#!/usr/bin/env python3
"""Prepare and prove isolation without contacting an inference provider."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import socket
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent
IMAGE = 'scm-format-isolation:0.157.1'


def docker(*args, check=True, timeout=120, input=None):
    result = subprocess.run(['docker', *args], text=True, capture_output=True, timeout=timeout, input=input)
    if check and result.returncode:
        raise RuntimeError(f'docker {args[0]} failed: {result.stderr[-1500:]} {result.stdout[-1500:]}')
    return result


def hardening():
    return ['--read-only', '--user', '65534:65534', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--pids-limit', '128',
            '--memory', '768m', '--cpus', '1', '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777']


def verify_image_sources(image_id):
    """Bind executed container modules to the reviewed host bytes, even without build."""
    names = ['client.mjs', 'relay.mjs', 'live_transport.mjs']
    script = (
        "const fs=require('node:fs'),crypto=require('node:crypto');"
        "const names=" + json.dumps(names) + ";"
        "console.log(JSON.stringify(Object.fromEntries(names.map(name=>"
        "[name,crypto.createHash('sha256').update(fs.readFileSync('/opt/isolation/'+name)).digest('hex')]))));"
    )
    actual = json.loads(docker('run', '--rm', '--network', 'none', *hardening(),
                              '--entrypoint', 'node', image_id, '-e', script).stdout)
    expected = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    if actual != expected:
        raise RuntimeError('IMAGE_SOURCE_MISMATCH: rebuild the reviewed isolation image')
    return actual


def offline_proof(build=True):
    if build:
        docker('build', '-t', IMAGE, str(ROOT), timeout=300)
    image = json.loads(docker('image', 'inspect', IMAGE).stdout)[0]
    image_sources = verify_image_sources(image['Id'])
    version = docker('run', '--rm', '--network', 'none', *hardening(),
                     '--entrypoint', 'codex', image['Id'], '--version').stdout.strip()
    if version != 'codex-cli 0.157.1':
        raise RuntimeError('unexpected pinned CLI version')
    suffix = uuid.uuid4().hex[:12]
    network, relay, client = [f'scm-isolation-{kind}-{suffix}' for kind in ['net', 'relay', 'client']]
    canaries = ['REFERENCE_'+suffix, 'TESTS_'+suffix, 'OLD_ANSWER_'+suffix]
    # Host canaries live outside every container mount, including the build context.
    with tempfile.TemporaryDirectory(prefix='scm-host-canaries-') as temp:
        for name, token in zip(['reference', 'tests', 'old-answers'], canaries):
            (Path(temp)/name).write_text(token)
        docker('network', 'create', '--internal', network)
        try:
            docker('run', '-d', '--name', relay, '--network', network, '--network-alias', 'relay',
                   *hardening(), '--entrypoint', 'node', image['Id'], '/opt/isolation/relay.mjs')
            for _ in range(50):
                if 'ready' in docker('logs', relay).stdout:
                    break
                time.sleep(.1)
            policy = docker('run', '--rm', '--network', 'none', *hardening(), '--entrypoint', 'node',
                            image['Id'], '/opt/isolation/relay.mjs', 'selftest')
            with socket.socket() as listener:
                listener.bind(('0.0.0.0', 0))
                listener.listen(1)
                host_port = listener.getsockname()[1]
                canary = docker('run', '--rm', '--network', network, *hardening(),
                                '-e', f'SCM_HOST_PROBE_PORT={host_port}', image['Id'], 'canary')
            canary_result = json.loads(canary.stdout.strip())
            docker('create', '--name', client, '--network', network, *hardening(), image['Id'])
            inspected = json.loads(docker('inspect', client).stdout)[0]
            assert inspected['Mounts'] == [], 'unexpected host mount'
            assert inspected['HostConfig']['ReadonlyRootfs'] is True
            assert inspected['Config']['User'] == '65534:65534'
            assert inspected['HostConfig']['CapDrop'] == ['ALL']
            assert inspected['HostConfig']['Privileged'] is False
            assert inspected['HostConfig']['NetworkMode'] == network
            topology = json.loads(docker('network', 'inspect', network).stdout)[0]
            assert topology['Internal'] is True
            result = docker('start', '-a', client, check=False, timeout=75)
            log = docker('logs', relay).stdout
            events = [json.loads(line) for line in log.splitlines() if line.strip()]
            captures = [e for e in events if e['kind']=='capture']
            rejected = [e for e in events if e['kind']=='rejected']
            if rejected or len(captures)!=1:
                raise RuntimeError(f'provider capture failed: rejected={rejected}, client={result.stdout[-2000:]}')
            capture = captures[0]
            combined = json.dumps(capture)
            assert all(token not in combined for token in canaries), 'host canary leaked'
            assert 'OFFLINE_ISOLATION_FIXTURE' in combined
            assert capture['body']['model']=='gpt-6.1-sol'
            assert capture['body']['reasoning']['effort']=='medium'
            client_events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
            final = [event for event in client_events if event.get('kind')=='client_result']
            if not final or not final[-1]['ok']:
                raise RuntimeError(f'client did not complete fixture: {result.stdout[-2000:]}')
            return {
                'status':'offline_isolation_verified_live_preflight_pending',
                'live_provider_requests':0, 'candidate_trials':0,
                'codex_version':version, 'image_id':image['Id'],
                'image_source_sha256':image_sources,
                'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in ROOT.iterdir() if p.suffix in ['.mjs','.py'] or p.name=='Dockerfile'},
                'container':{'host_mounts':[], 'internal_network':True,
                             'read_only_root':True,'uid':65534,'cap_drop':['ALL'],
                             'no_new_privileges':True},
                'canaries':{'outside_container_mounts':True,'not_in_request':True,
                            'runtime_probe':canary_result},
                'relay_policy':json.loads(policy.stdout),
                'provider_request':capture, 'client_events':client_events,
                'limitations':['Fixture response is not model generation.',
                    'No live ChatGPT provider authentication or model identity verified.',
                    'Docker daemon/host administrator remains trusted.'],
            }
        finally:
            for name in [client, relay]:
                docker('rm', '-f', name, check=False)
            docker('network', 'rm', network, check=False)


def source_hashes():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in ROOT.iterdir() if p.suffix in ['.mjs','.py'] or p.name=='Dockerfile'}


def verify_frozen():
    study = ROOT.parent
    manifest_path = study/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('status') != 'FROZEN_NOT_RUN' or not manifest.get('sha256'):
        raise RuntimeError('FROZEN_MANIFEST_REQUIRED')
    for relative, expected in manifest['sha256'].items():
        path = (study/relative).resolve()
        if not path.is_relative_to(study.resolve()) or path.is_symlink():
            raise RuntimeError('UNSAFE_FROZEN_PATH')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('FROZEN_ARTIFACT_CHANGED')
    return manifest, hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def verify_offline(image_id):
    image_sources = verify_image_sources(image_id)
    proof=json.loads((ROOT/'offline-evidence.json').read_text())
    if (proof.get('status')!='offline_isolation_verified_live_preflight_pending'
        or proof.get('source_sha256')!=source_hashes() or proof.get('image_id')!=image_id
        or proof.get('image_source_sha256')!=image_sources
        or proof.get('provider_request',{}).get('body',{}).get('tools')!=[]):
        raise RuntimeError('MATCHING_OFFLINE_PROOF_REQUIRED')


def run_live(prompt,image_id):
    # Only reached after explicit future CLI authorization and all artifact gates.
    auth_home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
    try:
        value=json.loads((auth_home/'auth.json').read_text())
        token=value['tokens']['access_token']; account=value['tokens']['account_id']
        if not isinstance(token,str) or not token or not isinstance(account,str) or not account:
            raise ValueError()
    except (OSError,ValueError,KeyError,TypeError):
        raise RuntimeError('LOGIN_REQUIRED: file-backed ChatGPT login is required') from None
    auth=json.dumps({'tokens':{'access_token':token,'account_id':account}})
    suffix=uuid.uuid4().hex[:12]
    network,relay,client=[f'scm-live-{kind}-{suffix}' for kind in ['net','relay','client']]
    relay_process=None
    docker('network','create','--internal',network)
    try:
        # Relay alone has external connectivity; only its memory receives credentials.
        docker('create','-i','--name',relay,'--network','bridge',*hardening(),
               '--entrypoint','node',image_id,'/opt/isolation/relay.mjs','live')
        docker('network','connect','--alias','relay',network,relay)
        relay_process=subprocess.Popen(['docker','start','-a','-i',relay],stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        relay_process.stdin.write(auth.encode()); relay_process.stdin.close()
        for _ in range(100):
            if 'ready' in docker('logs',relay).stdout:
                break
            if relay_process.poll() is not None:
                raise RuntimeError('RELAY_LOGIN_OR_START_FAILED')
            time.sleep(.1)
        else:
            raise RuntimeError('RELAY_START_TIMEOUT')
        docker('create','-i','--name',client,'--network',network,*hardening(),
               '-e','ISOLATION_MODE=live',image_id)
        inspected=json.loads(docker('inspect',client).stdout)[0]
        if inspected['Mounts'] or inspected['HostConfig']['NetworkMode']!=network:
            raise RuntimeError('ISOLATION_CONFIGURATION_FAILED')
        result=docker('start','-a','-i',client,check=False,timeout=150,input=prompt)
        events=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        final=next((event for event in reversed(events) if event.get('kind')=='client_result'),{})
        relay_events=[json.loads(line) for line in docker('logs',relay).stdout.splitlines() if line.startswith('{')]
        forwarded=[event for event in relay_events if event.get('kind')=='live_forwarded']
        if (not final.get('ok') or len(forwarded)!=1 or
            any(event.get('kind') in ['live_failed','rejected'] for event in relay_events)):
            raise RuntimeError('LIVE_TRANSPORT_OR_IDENTITY_FAILED_CLOSED')
        settings=next((event for event in events if event.get('kind')=='thread_settings'),{})
        return {'answer':final.get('answer',''),'thread_id':settings.get('thread_id'),
                'completed_at_utc':datetime.now(timezone.utc).isoformat(),
                'requested_model':'gpt-6.1-sol',
                'effort':'medium','reported_model':forwarded[0]['reported_model'],
                'identity_note':'Provider-reported identity; not independent model attestation.',
                'tools':[], 'image_id':image_id,'source_sha256':source_hashes()}
    finally:
        for name in [client,relay]:
            docker('rm','-f',name,check=False)
        docker('network','rm',network,check=False)
        if relay_process:
            relay_process.wait(timeout=10)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['offline-proof','live-preflight','generate'])
    parser.add_argument('--evidence',type=Path)
    parser.add_argument('--skip-build',action='store_true')
    parser.add_argument('--authorize-live',action='store_true',help='Explicit future authorization; sends an inference request.')
    parser.add_argument('--canary',type=Path)
    parser.add_argument('--trial-id')
    args=parser.parse_args()
    if args.command=='generate' and args.evidence:
        parser.error('generate writes create-only runs/TRIAL_ID/result.json; omit --evidence')
    if args.command=='offline-proof':
        result=offline_proof(not args.skip_build)
    else:
        if not args.authorize_live:
            parser.exit(2,'LIVE_PREFLIGHT_PENDING: --authorize-live is required; no authentication read or inference request was made.\n')
        image_id=json.loads(docker('image','inspect',IMAGE).stdout)[0]['Id']
        verify_offline(image_id)
        manifest,freeze_hash=verify_frozen()
        if args.evidence:
            evidence_path=args.evidence.resolve()
            if evidence_path.is_relative_to(ROOT.parent.resolve()) and not evidence_path.is_relative_to((ROOT.parent/'runs').resolve()):
                raise RuntimeError('EVIDENCE_MUST_NOT_OVERWRITE_FROZEN_ARTIFACTS')
            if evidence_path.exists():
                raise RuntimeError('EVIDENCE_ALREADY_EXISTS')
        if args.command=='live-preflight':
            if not args.evidence:
                parser.error('--evidence is required for live-preflight')
            args.evidence.parent.mkdir(parents=True,exist_ok=True)
            with args.evidence.with_suffix(args.evidence.suffix+'.attempt.json').open('x') as record:
                json.dump({'status':'canary_attempted','started_at_utc':datetime.now(timezone.utc).isoformat(),
                           'freeze_sha256':freeze_hash,'source_sha256':source_hashes(),'image_id':image_id},record)
            result=run_live('Return exactly SCM_LIVE_CANARY_OK and nothing else.',image_id)
            if result['answer'].strip()!='SCM_LIVE_CANARY_OK':
                raise RuntimeError('LIVE_CANARY_ANSWER_MISMATCH')
            result.update(status='live_canary_passed',freeze_sha256=freeze_hash)
        else:
            if not args.canary or not args.trial_id:
                parser.error('--canary and --trial-id are required for generate')
            canary=json.loads(args.canary.read_text())
            if (canary.get('status')!='live_canary_passed' or canary.get('freeze_sha256')!=freeze_hash
                or canary.get('image_id')!=image_id or canary.get('source_sha256')!=source_hashes()):
                raise RuntimeError('MATCHING_LIVE_CANARY_REQUIRED')
            trials=json.loads((ROOT.parent/'trials.json').read_text())
            trial=next((trial for trial in trials if trial['trial_id']==args.trial_id),None)
            if not trial:
                raise RuntimeError('UNKNOWN_FROZEN_TRIAL')
            relative=trial['prompt']
            path=(ROOT.parent/relative).resolve()
            if (relative not in manifest['sha256'] or not path.is_relative_to((ROOT.parent/'prompts').resolve())
                or path.suffix!='.txt'):
                raise RuntimeError('UNKNOWN_FROZEN_PROMPT')
            runs=ROOT.parent/'runs'
            for scheduled in trials:
                prior=runs/scheduled['trial_id']
                if not (prior/'dispatch.json').exists():
                    if scheduled['trial_id']!=args.trial_id:
                        raise RuntimeError('NOT_NEXT_SCHEDULED_TRIAL')
                    break
                if scheduled['trial_id']==args.trial_id:
                    raise RuntimeError('TRIAL_ALREADY_ATTEMPTED_NO_RETRY')
                if not (prior/'result.json').exists() or json.loads((prior/'result.json').read_text()).get('status')!='generated':
                    raise RuntimeError('PREVIOUS_ATTEMPT_AMBIGUOUS_OR_FAILED_STOP')
            run_dir=runs/args.trial_id
            run_dir.mkdir(parents=True,exist_ok=False)
            args.evidence=run_dir/'result.json'
            dispatch={'status':'attempted_no_retry','trial_id':args.trial_id,
                      'started_at_utc':datetime.now(timezone.utc).isoformat(),
                      'prompt_sha256':manifest['sha256'][relative],'freeze_sha256':freeze_hash,
                      'requested_model':'gpt-6.1-sol','effort':'medium',
                      'source_sha256':source_hashes(),'image_id':image_id}
            with (run_dir/'dispatch.json').open('x') as record:
                json.dump(dispatch,record,indent=2)
            try:
                result=run_live(path.read_text(),image_id)
            except Exception:
                with args.evidence.open('x') as record:
                    json.dump({**dispatch,'status':'interrupted_or_failed_do_not_retry'},record,indent=2)
                raise
            result.update(status='generated',trial_id=args.trial_id,prompt_sha256=manifest['sha256'][relative],freeze_sha256=freeze_hash)
    text=json.dumps(result,indent=2)+'\n'
    if args.evidence:
        args.evidence.parent.mkdir(parents=True,exist_ok=True)
        with args.evidence.open('w' if args.command=='offline-proof' else 'x') as record:
            record.write(text)
    print(text)

if __name__=='__main__':
    main()
