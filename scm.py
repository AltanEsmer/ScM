"""Frozen file-based pilot. Candidate code executes only through grading's Docker runner."""
import argparse
import csv
import hashlib
import itertools
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import grading


@dataclass(frozen=True)
class Trial:
    trial_id: str
    task: str
    variant: str
    repeat: int
    prompt_file: str


@dataclass(frozen=True)
class Record:
    trial: Trial
    status: str
    session_id: str | None = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def trials(root):
    rows = load(root / 'experiment/trials.json')
    result = []
    for row in rows:
        task, variant, repeat = row['task'], row['variant'], row['repeat']
        identity = f'{task}_{variant}_{repeat:02d}'
        if type(repeat) is not int or row['trial_id'] != identity or row['prompt_file'] != f'prompts/{task}_{variant}.txt':
            raise ValueError('invalid trial identity or prompt path')
        result.append(Trial(identity, task, variant, repeat, row['prompt_file']))
    expected = set(itertools.product(('deduplicate', 'merge_intervals', 'word_counts'), 'ABC', range(1, 6)))
    if len(result) != 45 or {(t.task, t.variant, t.repeat) for t in result} != expected:
        raise ValueError('schedule must contain each of 45 Cartesian trials exactly once')
    return result


def inputs(root):
    files = [root / 'scm.py', root / 'grading.py', *sorted((root / 'experiment').glob('*.json')),
             *sorted((root / 'prompts').glob('*.txt'))]
    if (root / 'scripts/capture.py').exists():
        files.append(root / 'scripts/capture.py')
    return {str(p.relative_to(root)): sha(p) for p in files}


def freeze(root):
    trials(root)
    manifest = root / 'manifest.json'
    current = {'schema': 1, 'hashes': inputs(root)}
    if manifest.exists():
        if load(manifest) != current:
            raise ValueError('frozen inputs changed')
        return
    if (root / 'records').exists() and any((root / 'records').iterdir()):
        raise ValueError('freeze must precede collection')
    with manifest.open('x') as file:
        json.dump(current, file, indent=2)
        file.write('\n')


def verify(root, require_complete=False):
    if load(root / 'manifest.json') != {'schema': 1, 'hashes': inputs(root)}:
        raise ValueError('frozen inputs changed')
    schedule = trials(root)
    protocol = load(root / 'experiment/protocol.json')
    records = root / 'records'
    if records.exists() and set(p.name for p in records.iterdir()) - {t.trial_id for t in schedule}:
        raise ValueError('unknown record')
    sessions = set()
    verified = []
    for trial in schedule:
        directory = records / trial.trial_id
        if not directory.exists():
            verified.append(Record(trial, 'missing'))
            continue
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
        times = []
        for key in ('dispatch_observed_utc', 'completion_observed_utc'):
            stamp = evidence.get(key)
            if not isinstance(stamp, str) or not re.search(r'(Z|\+00:00)$', stamp):
                raise ValueError('expected UTC observation timestamp')
            times.append(datetime.fromisoformat(stamp.replace('Z', '+00:00')))
        if times[1] < times[0]:
            raise ValueError('completion precedes dispatch')
        verified.append(Record(trial, 'collected', session))
    if require_complete and any(r.status == 'missing' for r in verified):
        raise ValueError('collection incomplete')
    return verified


def grade(root):
    records = verify(root)
    tasks = {t['id']: t for t in load(root / 'experiment/tasks.json')}
    image = load(root / 'experiment/protocol.json')['docker_image']
    rows = []
    infrastructure_error = None
    for record in records:
        trial = record.trial
        status, passed, detail = record.status, 0, ''
        if status == 'collected' and infrastructure_error is not None:
            status, detail = 'not_evaluated', 'Stopped after Docker infrastructure failure'
        elif status == 'collected':
            status, passed, detail = grading.evaluate(tasks[trial.task], (root / 'records' / trial.trial_id / 'answer.txt').read_text(), image)
        rows.append(dict(trial_id=trial.trial_id, task=trial.task, variant=trial.variant, repeat=trial.repeat,
                         session_id=record.session_id or '', status=status, passed=passed,
                         total=len(tasks[trial.task]['cases']), detail=detail,
                         requested_model='gpt-6.1-sol', requested_reasoning='medium', observed_model='',
                         response_sha256=sha(root / 'records' / trial.trial_id / 'answer.txt') if record.session_id else '',
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
    if len(rows) != 45 or {r['trial_id'] for r in rows} != {r.trial.trial_id for r in records}:
        raise ValueError('derived results have invalid schedule')
    schedule = {record.trial.trial_id: record for record in records}
    failures = {'fail', 'syntax_error', 'runtime_error', 'timeout', 'invalid_output', 'output_limit'}
    statuses = failures | {'pass', 'missing', 'infrastructure_error', 'not_evaluated'}
    for row in rows:
        record = schedule[row['trial_id']]
        trial = record.trial
        if (row['task'], row['variant'], row['repeat']) != (trial.task, trial.variant, str(trial.repeat)) or row['status'] not in statuses:
            raise ValueError('derived results have invalid identity or status')
        if (row['status'] == 'missing') != (record.status == 'missing') or row['session_id'] != (record.session_id or ''):
            raise ValueError('derived results do not match collection')
        path = root / 'records' / row['trial_id'] / 'answer.txt'
        if row['manifest_sha256'] != sha(root / 'manifest.json') or row['response_sha256'] != (sha(path) if path.exists() else ''):
            raise ValueError('derived results are stale; run grade')
    lines = ['# Prompt sensitivity pilot', '',
             '| Task | Variant | Collected | Evaluated | Pass | Failure | Infrastructure | Not evaluated | Missing |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for task, variant in itertools.product(('deduplicate', 'merge_intervals', 'word_counts'), 'ABC'):
        group = [r for r in rows if r['task'] == task and r['variant'] == variant]
        counts = {status: sum(r['status'] == status for r in group) for status in statuses}
        failed = sum(counts[status] for status in failures)
        evaluated = counts['pass'] + failed
        lines.append(f"| {task} | {variant} | {5 - counts['missing']} | {evaluated} | {counts['pass']} | {failed} | {counts['infrastructure_error']} | {counts['not_evaluated']} | {counts['missing']} |")
    lines += ['', 'Functional pass denominator is Evaluated. Missing, infrastructure failures, and not evaluated trials are excluded.',
              'Candidate execution errors count as functional failures. Collected includes infrastructure failures and not evaluated trials.',
              'Five repetitions per cell provide limited evidence. All-pass results do not establish wording invariance.',
              'Requested model and reasoning are not provider-confirmed metadata. Full tool traces are unavailable.',
              'Fresh no-history agents retain system instructions and filesystem/tool access.',
              'Host scoring compares returned observations. Deliberate candidate interpreter tampering can fabricate all observations.',
              'The threat model is ordinary generated code, not a fully malicious candidate.', '']
    (root / 'results/report.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'verify', 'grade', 'report', 'self-test'))
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        if args.command == 'verify':
            records = verify(root, args.require_complete)
            print(json.dumps({s: sum(r.status == s for r in records) for s in ('collected', 'missing')}))
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
