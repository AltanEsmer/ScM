"""Freeze fixtures, sandbox-reference preflight, then explicitly approved grading.
No candidate is imported or evaluated by this host process.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
from datetime import datetime, timezone
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE="08130cac7739bddb10dcd3c884be1b6037a58d68"
sys.path.insert(0,str(ROOT))
import grading


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,data):
    with path.open('x') as stream:
        json.dump(data,stream,indent=2,ensure_ascii=False); stream.write('\n')


def modules():
    result=[]
    for name in ['family12','family34','family56']:
        spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); result.append(module)
    return result


def batches(cases,size=8):
    """Eight-case ceiling with a conservative typed-output byte bound."""
    batch=[]
    for case in cases:
        trial=batch+[case]
        bound=len(json.dumps({'results':[{'actual':grading.typed(c['expected']),'input_after':grading.typed(c['argument']),'same_object':False} for c in trial]},ensure_ascii=True).encode())
        if batch and (len(trial)>size or bound>48000):
            yield batch
            batch=[]
            trial=[case]
            bound=len(json.dumps({'results':[{'actual':grading.typed(case['expected']),'input_after':grading.typed(case['argument']),'same_object':False}]},ensure_ascii=True).encode())
        if bound>48000: raise ValueError('expected protocol output exceeds conservative bound')
        batch=trial
    if batch: yield batch


def freeze():
    destination=HERE/'frozen'
    if destination.exists(): raise FileExistsError('freeze already exists')
    tasks=json.loads((ROOT/'calibration/round2/tasks.json').read_text())
    generators=modules(); fixtures=[]; checks={}
    for module in generators:
        checks[module.__name__]=module.verify_oracles()
    for i,task in enumerate(tasks):
        module=generators[i//2]; family=task['family'].lower()
        generated=getattr(module,'generate_'+family)()
        seen=set(); cases=[]
        for case in generated:
            key=json.dumps(case['argument'],sort_keys=True)
            if key not in seen:
                seen.add(key); case['id']=task['family']+f'-{len(cases):03}'; cases.append(case)
        if len({c['id'] for c in cases})!=len(cases): raise ValueError('duplicate ids')
        for case in cases:
            if set(case)!={'id','category','argument','expected'}: raise ValueError('case shape')
            getattr(module,'validate_'+family)(case['argument'])
        list(batches(cases))
        fixtures.append(dict(id=task['id'],function=task['function'],family=task['family'],cases=cases))
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    protected={p:hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)).hexdigest() for p in paths if p not in ('README.md','docs/evidence-strength.md')}
    for p,h in protected.items():
        if digest(ROOT/p)!=h: raise ValueError('original changed '+p)
    answers=sorted((ROOT/'calibration/round2/records').glob('*/answer.txt'))
    if len(answers)!=30: raise ValueError('expected thirty saved answers')
    destination.mkdir()
    write(destination/'cases.json',fixtures)
    source={str(p.relative_to(ROOT)):digest(p) for p in sorted(HERE.rglob('*.py'))}
    source['grading.py']=digest(ROOT/'grading.py')
    summary={t['family']:{'cases':len(t['cases']),'unique_arguments':len({json.dumps(c['argument'],sort_keys=True) for c in t['cases']}),'categories':dict(collections.Counter(c['category'] for c in t['cases']))} for t in fixtures}
    manifest=dict(schema=1,base_commit=BASE,created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=source,cases_sha256=digest(destination/'cases.json'),original_sha256=protected,answers_sha256={str(p.relative_to(ROOT)):digest(p) for p in answers},oracle_checks=checks,coverage=summary,image=json.loads((ROOT/'calibration/round2/protocol.json').read_text())['docker_image'],timeout_seconds=4,batch_size=8,design_blinding='Generator authors did not read saved answer contents during suite construction. Parent previously inspected selected answers during diagnosis. Hashing reads bytes without interpreting source.')
    write(destination/'manifest.json',manifest)
    print(json.dumps(summary,indent=2))


def verify_frozen():
    manifest=json.loads((HERE/'frozen/manifest.json').read_text())
    for group in ['source_sha256','original_sha256','answers_sha256']:
        for p,h in manifest[group].items():
            if digest(ROOT/p)!=h: raise ValueError('frozen provenance changed '+p)
    if digest(HERE/'frozen/cases.json')!=manifest['cases_sha256']: raise ValueError('cases changed')
    return manifest,json.loads((HERE/'frozen/cases.json').read_text())


def execute(task,cases,answer,manifest):
    start=time.monotonic()
    status,passed,detail=grading.evaluate(dict(id=task['id'],function=task['function'],cases=[[c['argument'],c['expected']] for c in cases]),answer,manifest['image'],timeout=manifest['timeout_seconds'])
    return dict(status=status,passed=passed,total=len(cases),detail=detail,elapsed_seconds=round(time.monotonic()-start,6),case_ids=[c['id'] for c in cases])


def validate_completion(records,fixtures,mode):
    expected={}
    for task in fixtures:
        trials=['reference'] if mode=='preflight' else [task['id']+f'_B0_{i:02}' for i in range(1,6)]
        for trial in trials:
            expected[task['id'],trial]=[c['id'] for c in task['cases']]
    observed=collections.defaultdict(list)
    summaries={}
    for record in records:
        key=(record['task'],record['trial'])
        observed[key].extend(record['case_ids'])
        summary=summaries.setdefault(key,dict(task=key[0],trial=key[1],family=record['family'],passed=0,total=0,status_counts={}))
        summary['passed']+=record['passed']; summary['total']+=record['total']
        counts=summary['status_counts']; counts[record['status']]=counts.get(record['status'],0)+1
    if set(observed)!=set(expected): raise ValueError('incomplete or unexpected task/trial coverage')
    for key,ids in expected.items():
        if collections.Counter(observed[key])!=collections.Counter(ids): raise ValueError('missing or duplicate case coverage')
    return list(summaries.values())


def run(mode,destination,review_note=None,preflight_path=None):
    manifest,fixtures=verify_frozen()
    if mode=='grade':
        if not review_note: raise ValueError('grade requires suite review checkpoint via --review-note')
        if preflight_path is None: raise ValueError('--preflight path required')
        preflight=json.loads((preflight_path/'summary.json').read_text())
        if not preflight['all_pass'] or preflight['manifest_sha256']!=digest(HERE/'frozen/manifest.json') or preflight['batches_sha256']!=digest(preflight_path/'batches.jsonl'): raise ValueError('matching successful reference preflight required')
    destination.mkdir(parents=True,exist_ok=False)
    write(destination/'provenance.json',dict(mode=mode,review_note=review_note,created_utc=datetime.now(timezone.utc).isoformat(),preflight_path=str(preflight_path) if preflight_path else None,manifest_sha256=digest(HERE/'frozen/manifest.json')))
    references={t['id']:t['reference'] for t in json.loads((ROOT/'calibration/round2/tasks.json').read_text())}
    all_pass=True
    records=[]
    with (destination/'batches.jsonl').open('x') as log:
        for task in fixtures:
            answers=[('reference',references[task['id']])] if mode=='preflight' else [(p.parent.name,p.read_text()) for p in sorted((ROOT/'calibration/round2/records').glob(task['id']+'_B0_*/answer.txt'))]
            for trial,answer in answers:
                for index,batch in enumerate(batches(task['cases'],manifest['batch_size'])):
                    verify_frozen()
                    record=dict(task=task['id'],family=task['family'],trial=trial,batch=index,**execute(task,batch,answer,manifest))
                    log.write(json.dumps(record)+'\n');log.flush(); records.append(record)
                    if record['status']!='pass':
                        all_pass=False
                        for case in batch:
                            reproduction=execute(task,[case],answer,manifest)
                            write(destination/f'{trial}-{index}-{case["id"]}.json',dict(task=task['id'],trial=trial,case=case,reproduction=reproduction,batch_status=record['status'],interpretation='semantic counterexample' if reproduction['status']=='fail' else 'individual execution outcome; batch-only failures may be aggregate resource limits',actual_observation='Unavailable through grading.evaluate; no fabricated actual value.'))
    verify_frozen()
    trial_summaries=validate_completion(records,fixtures,mode)
    result=dict(all_pass=all_pass,trials=trial_summaries,family_trial_counts=dict(collections.Counter(t['family'] for t in trial_summaries)),batches_sha256=digest(destination/'batches.jsonl'),finished_utc=datetime.now(timezone.utc).isoformat(),manifest_sha256=digest(HERE/'frozen/manifest.json'))
    write(destination/'summary.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['freeze','verify','preflight','grade'])
    parser.add_argument('--output',type=Path); parser.add_argument('--review-note'); parser.add_argument('--preflight',type=Path)
    args=parser.parse_args()
    if args.mode=='freeze': freeze()
    elif args.mode=='verify': verify_frozen(); print('frozen provenance valid')
    else:
        if args.output is None: parser.error('--output required; existing directories are never overwritten')
        run(args.mode,args.output,args.review_note,args.preflight)
