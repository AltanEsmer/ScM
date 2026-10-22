"""One explicit sequential full-task retry after reference infrastructure failures."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from grader import grade
from prepare import ROOT, digest, tasks, write_json


def recover(root=ROOT):
    if (root / 'manifest.json').exists():
        raise ValueError('Frozen evidence cannot be changed')
    report_path = root / 'reference-validation.json'
    previous = json.loads(report_path.read_text())
    rows = {row['id']: row for row in tasks(root)}
    if previous.get('status') != 'FAIL' or previous.get('grader_sha256') != digest(root / 'grader.py'):
        raise ValueError('Only current-grader failed preflight may be recovered')
    for field, filename in (('task_sha256', 'task.json'), ('reference_sha256', 'reference.py'),
                            ('evaluation_sha256', 'evaluation-cases.json')):
        actual = {task_id: digest(root / 'source/selected' / task_id / filename) for task_id in rows}
        if previous.get(field) != actual:
            raise ValueError('Recovery requires unchanged source, reference, and evaluation artifacts')
    affected = []
    for result in previous['reports']:
        failures = [case for case in result['cases'] if not case['passed']]
        if failures:
            if any(case['status'] != 'INFRASTRUCTURE_ERROR' for case in failures):
                raise ValueError('Semantic or candidate execution failures cannot use infrastructure recovery')
            affected.append(result['task_id'])
    if not affected:
        raise ValueError('No infrastructure-only affected tasks')
    archive = root / 'reference-attempts' / 'attempt-1'
    archive.mkdir(parents=True, exist_ok=False)
    for name in ('reference-validation.json', 'reference-validation.partial.json', 'reference-validation.cases.jsonl'):
        shutil.copy2(root / name, archive / name)
    prior_hash = digest(archive / 'reference-validation.json')
    log_path = root / 'reference-recovery.cases.jsonl'
    log_path.touch(exist_ok=False)
    replacements = {}
    for task_id in affected:
        task = rows[task_id]
        def record_case(index, result):
            stdin = task['input_output']['inputs'][index]
            expected = task['input_output']['outputs'][index]
            entry = {'attempt': 2, 'task_id': task_id, 'evaluation_case_index': index,
                     'source_case_index': task['evaluation_case_indices'][index],
                     'input_sha256': hashlib.sha256(stdin.encode()).hexdigest(),
                     'expected_sha256': hashlib.sha256(expected.encode()).hexdigest(), 'result': result}
            with log_path.open('a') as stream:
                stream.write(json.dumps(entry) + '\n')
        source = root / 'source/selected' / task_id / 'reference.py'
        replacements[task_id] = grade(source.read_text(), task, workers=1, on_case=record_case)
        print(json.dumps({'task_id': task_id, 'passed': replacements[task_id]['passed'],
                          'total': replacements[task_id]['total'], 'attempt': 2}), flush=True)
        write_json(root / f'reference-attempts/{task_id}-attempt-2.json', replacements[task_id])
    report = dict(previous)
    report['reports'] = [replacements.get(result['task_id'], result) for result in previous['reports']]
    report['status'] = 'PASS' if all(result['all_pass'] for result in report['reports']) else 'FAIL'
    report['recovery'] = {'method': 'Single sequential full-task retry, only after infrastructure failures; no case pruning or source changes.',
                          'completed_utc': datetime.now(timezone.utc).isoformat(),
                          'affected_task_ids': affected, 'prior_report': 'reference-attempts/attempt-1/reference-validation.json',
                          'prior_report_sha256': prior_hash, 'recovery_log': str(log_path.relative_to(root)),
                          'recovery_log_sha256': digest(log_path),
                          'reports': {task_id: digest(root / f'reference-attempts/{task_id}-attempt-2.json') for task_id in affected}}
    write_json(report_path, report)
    write_json(root / 'reference-validation.partial.json', {'status': 'COMPLETE_WITH_EXPLICIT_RECOVERY',
                                                          'final_report': 'reference-validation.json'})
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    report = recover()
    print(json.dumps({'status': report['status'], 'recovery': report['recovery']}, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
