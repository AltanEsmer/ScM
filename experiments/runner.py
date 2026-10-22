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

_grader = importlib.util.spec_from_file_location('calibration_grading', Path(__file__).resolve().parents[1] / 'grading.py')
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
    phase = protocol.get('phase')
    valid_shape = (phase == 'composite_calibration' and len(task_ids) == 6 and protocol['variants'] == ['B0'] and protocol['repetitions'] == 5
                   or phase == 'pilot3' and 6 <= len(task_ids) <= 12 and protocol['variants'] == ['A', 'B', 'C'] and protocol['repetitions'] == 10)
    if (not isinstance(task_ids, list) or not valid_shape or type(protocol['repetitions']) is not int
            or any(not isinstance(task, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', task) for task in task_ids)
            or len(set(task_ids)) != len(task_ids)):
        raise ValueError('protocol and schedule dimensions differ')
    if not isinstance(protocol.get('selection_rule'), str) or not protocol['selection_rule'].strip():
        raise ValueError('protocol must state the selection_rule')
    expected = set(itertools.product(task_ids, protocol['variants'], range(1, protocol['repetitions'] + 1)))
    if len(result) != len(expected) or {(t.task, t.variant, t.repeat) for t in result} != expected:
        raise ValueError('schedule must contain each Cartesian trial exactly once')
    tasks = load(root / 'tasks.json')
    if len(tasks) != len(task_ids) or {task['id'] for task in tasks} != {trial.task for trial in result}:
        raise ValueError('task table must contain exactly the scheduled tasks')
    for task in tasks:
        if task.get('function') != task['id'] or not isinstance(task.get('cases'), list) or not task['cases']:
            raise ValueError('invalid task function or cases')
    families = {}
    for task in tasks:
        family = task.get('family')
        if family not in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6'] or protocol['families'].get(task['id']) != family:
            raise ValueError('invalid family mapping')
        families[family] = families.get(family, 0) + 1
        if task.get('role') != ('development' if phase == 'composite_calibration' else 'heldout'):
            raise ValueError('invalid task role')
    if (phase == 'composite_calibration' and sorted(families.values()) != [1]*6
            or phase == 'pilot3' and (len(families) < 3 or set(families.values()) != {2})):
        raise ValueError('invalid family dimensions')
    for trial in result:
        if not (root / trial.prompt_file).is_file():
            raise ValueError('missing scheduled prompt')
    protocol = load(root / 'protocol.json')
    if protocol['requested_model'] != 'gpt-6.1-sol' or protocol['requested_reasoning'] != 'medium':
        raise ValueError('protocol must request gpt-6.1-sol with medium reasoning')
    if type(protocol['timeout_seconds']) not in (int, float) or protocol['timeout_seconds'] != 4:
        raise ValueError('protocol timeout must be finite and positive')
    if protocol['fork_turns'] != 'none' or protocol['collection_backend'] != 'collaboration.spawn_agent':
        raise ValueError('protocol must use fresh native agents')
    if not re.fullmatch(r'[\w./:-]+@sha256:[0-9a-f]{64}', protocol['docker_image']):
        raise ValueError('Docker image must be digest-pinned')
    return result


def inputs(root):
    root = root.resolve()
    names = load(root / 'protocol.json')['frozen_files']
    if not isinstance(names, list) or not names or len(set(names)) != len(names):
        raise ValueError('invalid frozen_files')
    repo = Path(__file__).resolve().parents[1]
    cal = repo / 'calibration/round2'
    pilot = repo / 'pilots/pilot3'
    allowed = {repo / 'grading.py', repo / 'experiments/runner.py', pilot / 'run.py'}
    allowed |= {cal / name for name in ['build_pool.py', 'select_pilot3.py', 'run.py', 'tasks.json', 'heldout.json', 'canonical-clauses.json', 'protocol.json', 'trials.json', 'manifest.json', 'failure-validation.json', 'results/trials.csv']}
    allowed |= {cal / f'pool/family{i}.py' for i in range(1, 7)}
    allowed |= set((cal / 'tests').glob('*.py'))
    allowed |= {pilot / name for name in ['selection.json', 'planned-trials.json', 'tasks.json', 'protocol.json', 'trials.json']}
    heldout = load(cal / 'heldout.json')
    development = load(cal / 'tasks.json')
    if len(heldout) != 12 or len(development) != 6:
        raise ValueError('complete pool required')
    for family in [f'F{i}' for i in range(1, 7)]:
        if sum(t.get('family') == family for t in heldout) != 2 or sum(t.get('family') == family for t in development) != 1:
            raise ValueError('complete pool family mapping required')
    canonical = load(cal / 'canonical-clauses.json')
    for task in development + heldout:
        if (task.get('role') != ('development' if task in development else 'heldout')
                or not isinstance(task.get('reference'), str) or not task['reference'].strip()
                or not isinstance(task.get('clauses'), list) or not task['clauses']
                or canonical.get(task['id']) != task['clauses']
                or any(not isinstance(c, str) or not c or '\n' in c or '\r' in c for c in task['clauses'])
                or not isinstance(task.get('cases'), list) or not task['cases']
                or any(not isinstance(c, list) or len(c) != 2 for c in task['cases'])):
            raise ValueError('invalid complete pool types')
    allowed |= {cal / f"prompts/{t['id']}_B0.txt" for t in development}
    allowed |= {pilot / f"prompts/{t['id']}_{v}.txt" for t in heldout for v in 'ABC'}
    result = {}
    for name in names:
        if not isinstance(name, str) or Path(name).is_absolute():
            raise ValueError('frozen paths must be relative')
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) and path not in allowed:
            raise ValueError('untrusted cross-root frozen path: ' + str(path))
        if path.name == 'manifest.json' and path.parent == root:
            raise ValueError('manifest cannot hash itself')
        result[name] = sha(path)
    mandatory = {repo / 'grading.py', repo / 'experiments/runner.py', cal / 'build_pool.py', cal / 'select_pilot3.py', cal / 'run.py', pilot / 'run.py'}
    mandatory |= {cal / f'pool/family{i}.py' for i in range(1, 7)}
    mandatory |= set((cal / 'tests').glob('*.py'))
    mandatory |= {cal / name for name in ['tasks.json', 'heldout.json', 'canonical-clauses.json', 'protocol.json', 'trials.json']}
    mandatory |= {pilot / 'planned-trials.json'}
    mandatory |= {cal / f"prompts/{t['id']}_B0.txt" for t in development}
    mandatory |= {pilot / f"prompts/{t['id']}_{v}.txt" for t in heldout for v in 'ABC'}
    mandatory |= {root / name for name in ['protocol.json', 'trials.json', 'tasks.json', 'run.py']}
    if load(root / 'protocol.json')['phase'] == 'pilot3':
        mandatory |= {cal / 'manifest.json', cal / 'results/trials.csv', pilot / 'selection.json'}
        selection = load(pilot / 'selection.json')
        if (selection.get('source_csv_sha256') != sha(cal / 'results/trials.csv')
                or selection.get('source_calibration_manifest_sha256') != sha(cal / 'manifest.json')
                or selection.get('validation_sha256') != (sha(cal / 'failure-validation.json') if (cal / 'failure-validation.json').exists() else None)):
            raise ValueError('selection source hashes differ')
        if selection.get('gate_satisfied') is not True:
            raise ValueError('pilot gate not satisfied')
        if selection.get('validation_sha256') is not None:
            mandatory.add(cal / 'failure-validation.json')
    if not mandatory <= {(root / name).resolve() for name in names}:
        raise ValueError('missing required frozen input')
    return result


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
    records = verify(root)
    missing = [i for i, record in enumerate(records, 1) if record.status == 'missing']
    if not ordinals or ordinals != missing[:len(ordinals)]:
        raise ValueError('start must follow the next scheduled prefix')
    if sum(record.status == 'interrupted' for record in records) + len(ordinals) > 3:
        raise ValueError('at most three trials may be in flight')
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
    events = []
    dispatched_ordinals = []
    dispatch_times = []
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
            dispatched_ordinals.append(ordinal)
            dispatch_times.append(timestamp(dispatch['dispatch_observed_utc']))
            events.append((timestamp(dispatch['dispatch_observed_utc']), 1))
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
        events.append((timestamp(evidence['completion_observed_utc']), -1))
        verified.append(Record(trial, 'collected', session))
    if dispatched_ordinals != list(range(1, len(dispatched_ordinals) + 1)) or dispatch_times != sorted(dispatch_times):
        raise ValueError('dispatch history does not follow schedule prefix')
    active = 0
    for _, delta in sorted(events):
        active += delta
        if active > 3 or active < 0:
            raise ValueError('dispatch history violates three-in-flight limit')
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
    if len(rows) != len(records) or len({r['trial_id'] for r in rows}) != len(rows) or {r['trial_id'] for r in rows} != {r.trial.trial_id for r in records}:
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
    lines = ['# ' + protocol['phase'], '', '| Task | Variant | Collected | Evaluated | Pass | Pass rate | Candidate failure counts | Infrastructure | Not evaluated | Missing/interrupted | Classification |', '| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |']
    rates = {}
    complete = True
    for task in protocol['tasks']:
        for variant in protocol['variants']:
            group = [row for row in rows if row['task'] == task and row['variant'] == variant]
            passed = sum(row['status'] == 'pass' for row in group)
            evaluated = sum(row['status'] in failures | {'pass'} for row in group)
            classification = 'incomplete'
            if evaluated == protocol['repetitions']:
                classification = ('ceiling' if passed == 5 else 'floor' if passed == 0 else 'mixed_pending_validation') if protocol['phase'] == 'composite_calibration' else 'complete'
                rates[task, variant] = passed / evaluated
            else:
                complete = False
            counts = {status: sum(row['status'] == status for row in group) for status in statuses}
            missing = counts['missing'] + counts['interrupted']
            rate = f'{100 * passed / evaluated:.1f}%' if evaluated else 'NA'
            failed = ', '.join(f'{status}={counts[status]}' for status in sorted(failures))
            lines.append(f"| {task} | {variant} | {len(group) - missing} | {evaluated} | {passed} | {rate} | {failed} | {counts['infrastructure_error']} | {counts['not_evaluated']} | {missing} | {classification} |")
    if protocol['phase'] == 'pilot3':
        if complete:
            for variant in ['B', 'C']:
                difference = sum(rates[t, variant] - rates[t, 'A'] for t in protocol['tasks']) / len(protocol['tasks'])
                lines.append(f'Equal-task averaged {variant}-A: {100 * difference:+.2f} percentage points')
        else:
            lines.append('Primary analysis incomplete.')
    lines += ['', 'Requested model metadata is not provider-confirmed. First final messages are retained as raw bytes.', 'Infrastructure, missing and not-evaluated trials are incomplete. Candidate execution errors count as functional failures.']
    (root / 'results/report.md').write_text('\n'.join(lines) + '\n')
    return rows


def main(root=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'verify', 'grade', 'report', 'self-test', 'start', 'attach', 'record'))
    parser.add_argument('arguments', nargs='*')
    parser.add_argument('--root', default='.')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    root = Path(root) if root is not None else Path(args.root).resolve()
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
            return subprocess.call([sys.executable, '-m', 'unittest', 'discover', '-s', str(Path(__file__).resolve().parents[1] / 'calibration/round2/tests'), '-v'], cwd=Path(__file__).resolve().parents[1])
        else:
            {'freeze': freeze, 'grade': grade, 'report': report}[args.command](root)
            print(args.command + ' complete')
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
