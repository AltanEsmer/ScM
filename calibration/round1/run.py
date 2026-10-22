"""Isolated baseline task-pool calibration. Candidate code executes only through grading's Docker runner."""
import argparse
import csv
import hashlib
import itertools
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from typing import NamedTuple

_grader = importlib.util.spec_from_file_location('calibration_grading', Path(__file__).resolve().parents[2] / 'grading.py')
grading = importlib.util.module_from_spec(_grader)
_grader.loader.exec_module(grading)


class Trial(NamedTuple):
    trial_id: str
    task: str
    variant: str
    repeat: int
    prompt_file: str


class Record(NamedTuple):
    trial: Trial
    status: str
    session_id: str | None = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def trials(root):
    rows = load(root / 'trials.json')
    result = []
    for row in rows:
        task, variant, repeat = row['task'], row['variant'], row['repeat']
        if type(repeat) is not int:
            raise ValueError('invalid trial repeat')
        identity = f'{task}_{variant}_{repeat:02d}'
        if row['trial_id'] != identity or row['prompt_file'] != f'prompts/{task}_{variant}.txt':
            raise ValueError('invalid trial identity or prompt path')
        result.append(Trial(identity, task, variant, repeat, row['prompt_file']))
    protocol = load(root / 'protocol.json')
    task_ids = protocol['tasks']
    if (not isinstance(task_ids, list) or len(task_ids) != 6
            or any(not isinstance(task, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', task) for task in task_ids)
            or len(set(task_ids)) != 6 or protocol['variants'] != ['B0']
            or type(protocol['repetitions']) is not int or protocol['repetitions'] != 3):
        raise ValueError('protocol and schedule dimensions differ')
    if not isinstance(protocol.get('selection_rule'), str) or not protocol['selection_rule'].strip():
        raise ValueError('protocol must state the selection_rule')
    expected = set(itertools.product(task_ids, protocol['variants'], range(1, protocol['repetitions'] + 1)))
    if len(result) != len(expected) or {(t.task, t.variant, t.repeat) for t in result} != expected:
        raise ValueError('schedule must contain each of 18 Cartesian trials exactly once')
    tasks = load(root / 'tasks.json')
    if len(tasks) != len(task_ids) or {task['id'] for task in tasks} != {trial.task for trial in result}:
        raise ValueError('task table must contain exactly the six scheduled tasks')
    for task in tasks:
        if task.get('function') != task['id'] or not isinstance(task.get('cases'), list) or not task['cases']:
            raise ValueError('invalid task function or cases')
    for trial in result:
        if not (root / trial.prompt_file).is_file():
            raise ValueError('missing scheduled prompt')
    protocol = load(root / 'protocol.json')
    if protocol['requested_model'] != 'gpt-6.1-sol' or protocol['requested_reasoning'] != 'medium':
        raise ValueError('protocol must request gpt-6.1-sol with medium reasoning')
    if type(protocol['timeout_seconds']) not in (int, float) or not 0 < protocol['timeout_seconds'] < float('inf'):
        raise ValueError('protocol timeout must be finite and positive')
    if protocol['fork_turns'] != 'none' or protocol['collection_backend'] != 'collaboration.spawn_agent':
        raise ValueError('protocol must use fresh native agents')
    if not re.fullmatch(r'[\w./:-]+@sha256:[0-9a-f]{64}', protocol['docker_image']):
        raise ValueError('Docker image must be digest-pinned')
    return result


def inputs(root):
    names = ['../../grading.py', 'run.py', 'tasks.json', 'protocol.json', 'trials.json',
             'build_cases.py', 'pool_algorithms.py', 'pool_semantics.py']
    names += [str(path.relative_to(root)) for path in sorted((root / 'prompts').glob('*.txt'))]
    return {name: sha(root / name) for name in names}


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    if not isinstance(value, str) or not re.search(r'(Z|\+00:00)$', value):
        raise ValueError('expected UTC observation timestamp')
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def capture_root(root):
    return root / 'dispatch'


def ordinal_trial(root, ordinal):
    schedule = trials(root)
    if type(ordinal) is not int or not 1 <= ordinal <= len(schedule):
        raise ValueError(f'ordinal must be between 1 and {len(schedule)}')
    return schedule[ordinal - 1]


def start(root, ordinals):
    verify(root)
    selected = [ordinal_trial(root, number) for number in ordinals]
    if len(set(ordinals)) != len(ordinals):
        raise ValueError('duplicate ordinals')
    for trial in selected:
        if (capture_root(root) / trial.trial_id).exists() or (root / 'records' / trial.trial_id).exists():
            raise ValueError('trial already started')
    for number, trial in zip(ordinals, selected):
        directory = capture_root(root) / trial.trial_id
        directory.mkdir(parents=True, exist_ok=False)
        (directory / 'dispatch.json').write_text(json.dumps(dict(ordinal=number, trial_id=trial.trial_id,
            dispatch_observed_utc=now()), indent=2) + '\n')
        print(number, trial.trial_id)
        print((root / trial.prompt_file).read_text(), end='')


def attach(root, ordinal, session_id):
    records = verify(root)
    trial = ordinal_trial(root, ordinal)
    if not isinstance(session_id, str) or not session_id.strip() or any(r.session_id == session_id for r in records):
        raise ValueError('missing or duplicate session ID')
    directory = capture_root(root) / trial.trial_id
    if not (directory / 'dispatch.json').exists() or (root / 'records' / trial.trial_id).exists():
        raise ValueError('trial must be started and unrecorded')
    with (directory / 'session.json').open('x') as file:
        json.dump({'session_id': session_id}, file)


def record(root, ordinal, session_id, answer_file):
    records = verify(root)
    trial = ordinal_trial(root, ordinal)
    if not isinstance(session_id, str) or not session_id.strip() or any(r.session_id == session_id and r.trial != trial for r in records):
        raise ValueError('missing or duplicate session ID')
    capture = capture_root(root) / trial.trial_id
    dispatch = load(capture / 'dispatch.json')
    if (capture / 'session.json').exists() and load(capture / 'session.json')['session_id'] != session_id:
        raise ValueError('attached session ID differs')
    answer = Path(answer_file).read_bytes()
    protocol = load(root / 'protocol.json')
    directory = root / 'records' / trial.trial_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'answer.txt').write_bytes(answer)
    evidence = dict(trial_id=trial.trial_id, session_id=session_id,
        requested_model=protocol['requested_model'], requested_reasoning=protocol['requested_reasoning'],
        fork_turns='none', dispatch_observed_utc=dispatch['dispatch_observed_utc'],
        completion_observed_utc=now(), backend='collaboration.spawn_agent', observed_model=None,
        tool_trace_available=False, prompt_sha256=sha(root / trial.prompt_file),
        response_sha256=sha(directory / 'answer.txt'), capture_method='coordinator copied returned final message')
    with (directory / 'evidence.json').open('x') as file:
        json.dump(evidence, file, indent=2)
        file.write('\n')


def freeze(root):
    trials(root)
    manifest = root / 'manifest.json'
    current = {'schema': 1, 'hashes': inputs(root), 'frozen_observed_utc': now()}
    if manifest.exists():
        verify(root)
        return
    if any(path.exists() and any(path.iterdir()) for path in (root / 'records', capture_root(root))):
        raise ValueError('freeze must precede collection')
    with manifest.open('x') as file:
        json.dump(current, file, indent=2)
        file.write('\n')


def verify(root, require_complete=False):
    manifest = load(root / 'manifest.json')
    if manifest.get('schema') != 1 or manifest['hashes'] != inputs(root):
        raise ValueError('frozen inputs changed')
    schedule = trials(root)
    protocol = load(root / 'protocol.json')
    frozen = timestamp(manifest['frozen_observed_utc'])
    records = root / 'records'
    captures = capture_root(root)
    if captures.exists() and set(p.name for p in captures.iterdir()) - {t.trial_id for t in schedule}:
        raise ValueError('unknown capture')
    if records.exists() and set(p.name for p in records.iterdir()) - {t.trial_id for t in schedule}:
        raise ValueError('unknown record')
    sessions = set()
    verified = []
    for ordinal, trial in enumerate(schedule, 1):
        directory = records / trial.trial_id
        capture = captures / trial.trial_id
        dispatch = None
        attached = None
        if capture.exists():
            if not {'dispatch.json'} <= {p.name for p in capture.iterdir()} <= {'dispatch.json', 'session.json'}:
                raise ValueError('incomplete or unexpected capture files')
            dispatch = load(capture / 'dispatch.json')
            if dispatch['trial_id'] != trial.trial_id or type(dispatch['ordinal']) is not int or dispatch['ordinal'] != ordinal or timestamp(dispatch['dispatch_observed_utc']) < frozen:
                raise ValueError('invalid dispatch identity or timestamp')
            if (capture / 'session.json').exists():
                attached = load(capture / 'session.json')['session_id']
                if not isinstance(attached, str) or not attached.strip():
                    raise ValueError('missing session ID')
        if not directory.exists():
            if attached is not None:
                if not isinstance(attached, str) or not attached.strip() or attached in sessions:
                    raise ValueError('missing or duplicate session ID')
                sessions.add(attached)
            verified.append(Record(trial, 'interrupted' if dispatch else 'missing', attached))
            continue
        if dispatch is None:
            raise ValueError('record has no dispatch')
        if {p.name for p in directory.iterdir()} != {'answer.txt', 'evidence.json'}:
            raise ValueError(f'{trial.trial_id}: incomplete or unexpected record files')
        evidence = load(directory / 'evidence.json')
        checks = {'trial_id': trial.trial_id, 'requested_model': protocol['requested_model'],
                  'requested_reasoning': protocol['requested_reasoning'], 'fork_turns': 'none',
                  'backend': 'collaboration.spawn_agent', 'observed_model': None,
                  'tool_trace_available': False, 'prompt_sha256': sha(root / trial.prompt_file),
                  'response_sha256': sha(directory / 'answer.txt'),
                  'capture_method': 'coordinator copied returned final message'}
        if any(key not in evidence or type(evidence[key]) is not type(value) or evidence[key] != value for key, value in checks.items()):
            raise ValueError(f'{trial.trial_id}: evidence settings or hashes mismatch')
        session = evidence.get('session_id')
        if not isinstance(session, str) or not session.strip() or session in sessions:
            raise ValueError('missing or duplicate session ID')
        sessions.add(session)
        if attached is not None and attached != session:
            raise ValueError('attached session ID differs')
        if evidence['dispatch_observed_utc'] != dispatch['dispatch_observed_utc']:
            raise ValueError('dispatch observation differs')
        if timestamp(evidence['completion_observed_utc']) < timestamp(evidence['dispatch_observed_utc']):
            raise ValueError('completion precedes dispatch')
        verified.append(Record(trial, 'collected', session))
    if require_complete and any(r.status != 'collected' for r in verified):
        raise ValueError('collection incomplete')
    return verified


def grade(root):
    records = verify(root)
    tasks = {t['id']: t for t in load(root / 'tasks.json')}
    protocol = load(root / 'protocol.json')
    image = protocol['docker_image']
    rows = []
    infrastructure_error = None
    for record in records:
        trial = record.trial
        status, passed, detail = record.status, 0, ''
        if status == 'collected' and infrastructure_error is not None:
            status, detail = 'not_evaluated', 'Stopped after Docker infrastructure failure'
        elif status == 'collected':
            try:
                answer = (root / 'records' / trial.trial_id / 'answer.txt').read_text()
                status, passed, detail = grading.evaluate(tasks[trial.task], answer, image, timeout=protocol['timeout_seconds'])
            except UnicodeError as exc:
                status, detail = 'invalid_output', str(exc)
            except (OSError, subprocess.SubprocessError) as exc:
                status, detail = 'infrastructure_error', str(exc)
        rows.append(dict(trial_id=trial.trial_id, task=trial.task, variant=trial.variant, repeat=trial.repeat,
                         session_id=record.session_id or '', status=status, passed=passed,
                         total=len(tasks[trial.task]['cases']), detail=detail,
                         requested_model='gpt-6.1-sol', requested_reasoning='medium', observed_model='',
                         response_sha256=sha(root / 'records' / trial.trial_id / 'answer.txt') if record.status == 'collected' else '',
                         manifest_sha256=sha(root / 'manifest.json')))
        if status == 'infrastructure_error':
            infrastructure_error = detail
    results = root / 'results'
    results.mkdir(exist_ok=True)
    with (results / 'trials.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report(root)
    if infrastructure_error is not None:
        raise RuntimeError('Docker infrastructure failed: ' + infrastructure_error)


def report(root):
    records = verify(root)
    with (root / 'results/trials.csv').open(newline='') as file:
        rows = list(csv.DictReader(file))
    if len(rows) != len(records) or {r['trial_id'] for r in rows} != {r.trial.trial_id for r in records}:
        raise ValueError('derived results have invalid schedule')
    schedule = {record.trial.trial_id: record for record in records}
    failures = {'fail', 'syntax_error', 'runtime_error', 'timeout', 'invalid_output', 'output_limit'}
    statuses = failures | {'pass', 'missing', 'interrupted', 'infrastructure_error', 'not_evaluated'}
    for row in rows:
        record = schedule[row['trial_id']]
        trial = record.trial
        if (row['task'], row['variant'], row['repeat']) != (trial.task, trial.variant, str(trial.repeat)) or row['status'] not in statuses:
            raise ValueError('derived results have invalid identity or status')
        if (record.status != 'collected' and row['status'] != record.status) or (record.status == 'collected' and row['status'] in {'missing', 'interrupted'}) or row['session_id'] != (record.session_id or ''):
            raise ValueError('derived results do not match collection')
        path = root / 'records' / row['trial_id'] / 'answer.txt'
        if row['manifest_sha256'] != sha(root / 'manifest.json') or row['response_sha256'] != (sha(path) if path.exists() else ''):
            raise ValueError('derived results are stale; run grade')
    tasks = {task['id']: task for task in load(root / 'tasks.json')}
    for row in rows:
        total = len(tasks[row['task']]['cases'])
        if not re.fullmatch(r'0|[1-9][0-9]*', row['passed']) or row['total'] != str(total):
            raise ValueError('derived results have invalid counts')
        passed = int(row['passed'])
        if not 0 <= passed <= total or (row['status'] == 'pass' and passed != total) or (row['status'] in failures and passed == total):
            raise ValueError('derived results have invalid counts')
        if row['status'] not in failures | {'pass'} and passed != 0:
            raise ValueError('derived results have invalid counts')
        if row['requested_model'] != 'gpt-6.1-sol' or row['requested_reasoning'] != 'medium' or row['observed_model'] != '':
            raise ValueError('derived results have invalid model metadata')
    protocol = load(root / 'protocol.json')
    lines = ['# Baseline task-pool calibration round 1', '',
             '| Task | Variant | Collected | Evaluated | Pass | Failure | Infrastructure | Not evaluated | Missing | Classification |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for task in protocol['tasks']:
        group = [row for row in rows if row['task'] == task]
        counts = {status: sum(row['status'] == status for row in group) for status in statuses}
        failed = sum(counts[status] for status in failures)
        evaluated = counts['pass'] + failed
        classification = 'incomplete'
        if evaluated == protocol['repetitions']:
            classification = {0: 'floor', 1: 'eligible', 2: 'eligible', 3: 'ceiling'}[counts['pass']]
        lines.append(f"| {task} | B0 | {len(group) - counts['missing'] - counts['interrupted']} | {evaluated} | {counts['pass']} | {failed} | {counts['infrastructure_error']} | {counts['not_evaluated']} | {counts['missing'] + counts['interrupted']} | {classification} |")
    lines += ['', 'Baseline calibration only. This run does not compare prompt variants.',
              'Selection rule: ' + protocol['selection_rule'],
              'Eligible means one or two functional passes among three evaluated trials. Three passes is ceiling; zero passes is floor. Otherwise classification is incomplete.',
              'Functional pass denominator is Evaluated. Missing, infrastructure failures, and not evaluated trials are excluded.',
              'Candidate execution errors count as functional failures. Collected includes infrastructure failures and not evaluated trials.',
              'Interrupted dispatches are included in Missing. Three repetitions provide limited calibration evidence.',
              'Requested model and reasoning are not provider-confirmed metadata. Full tool traces are unavailable.',
              'Fresh no-history agents retain system instructions and filesystem/tool access.',
              'Host scoring compares returned observations. Deliberate candidate interpreter tampering can fabricate all observations.',
              'The threat model is ordinary generated code, not a fully malicious candidate.', '']
    (root / 'results/report.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'verify', 'grade', 'report', 'self-test', 'start', 'attach', 'record'))
    parser.add_argument('arguments', nargs='*')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        if args.command == 'verify':
            records = verify(root, args.require_complete)
            print(json.dumps({s: sum(r.status == s for r in records) for s in ('collected', 'missing', 'interrupted')}))
        elif args.command == 'start':
            if not args.arguments:
                raise ValueError('start requires ordinals')
            start(root, list(map(int, args.arguments)))
        elif args.command == 'attach':
            if len(args.arguments) != 2:
                raise ValueError('attach requires ordinal and session ID')
            attach(root, int(args.arguments[0]), args.arguments[1])
        elif args.command == 'record':
            if len(args.arguments) != 3:
                raise ValueError('record requires ordinal, session ID and answer file')
            record(root, int(args.arguments[0]), args.arguments[1], Path(args.arguments[2]))
        elif args.command == 'self-test':
            return subprocess.call([sys.executable, '-m', 'unittest', 'discover', '-s', str(root / 'tests'), '-v'], cwd=root)
        else:
            {'freeze': freeze, 'grade': grade, 'report': report}[args.command](root)
            print(args.command + ' complete')
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
