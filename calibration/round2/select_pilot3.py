"""Validate calibration evidence and mechanically select the heldout pilot subset."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments import runner
import importlib.util
_spec = importlib.util.spec_from_file_location('composite_builder', Path(__file__).with_name('build_pool.py'))
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)
ROOT = Path(__file__).resolve().parent
PILOT = ROOT.parents[1] / 'pilots/pilot3'
FAILURES = {'fail', 'syntax_error', 'runtime_error', 'timeout', 'invalid_output', 'output_limit'}


def decide(tasks, rows, validation=None):
    """Pure gate over validated derived rows and independent case review evidence."""
    validation = {} if validation is None else validation
    if not isinstance(validation, dict):
        raise ValueError('validation must map trial IDs to reviews')
    by_id = {row['trial_id']: row for row in rows}
    task_map = {task['id']: task for task in tasks}
    invalid = set()
    validated = set()
    for trial_id, review in validation.items():
        if trial_id not in by_id or not isinstance(review, dict):
            raise ValueError('unknown validation trial')
        row = by_id[trial_id]
        task = task_map[row['task']]
        indices = review.get('case_indices')
        if (row['status'] != 'fail' or not isinstance(indices, list) or not indices
                or any(type(i) is not int or not 0 <= i < len(task['cases']) for i in indices)
                or len(set(indices)) != len(indices)
                or type(review.get('reviewed_valid')) is not bool
                or type(review.get('family_valid')) is not bool
                or not isinstance(review.get('rationale'), str) or not review['rationale'].strip()):
            raise ValueError('invalid semantic failure review')
        if not review['family_valid']:
            invalid.add(task['family'])
        if review['reviewed_valid'] and review['family_valid']:
            validated.add(task['family'])
    outcomes = []
    eligible = []
    for task in tasks:
        group = [r for r in rows if r['task'] == task['id']]
        counts = {status: sum(r['status'] == status for r in group) for status in sorted(FAILURES | {'pass', 'missing', 'interrupted', 'infrastructure_error', 'not_evaluated'})}
        evaluated = counts['pass'] + sum(counts[s] for s in FAILURES)
        mixed = evaluated == 5 and 1 <= counts['pass'] <= 4
        status = 'invalidated' if task['family'] in invalid else 'incomplete' if evaluated != 5 else 'ceiling' if counts['pass'] == 5 else 'floor' if counts['pass'] == 0 else 'eligible' if task['family'] in validated else 'mixed_pending_validation'
        if mixed and status == 'eligible':
            eligible.append(task['family'])
        outcomes.append(dict(family=task['family'], development_task=task['id'], counts=counts, evaluated=evaluated, status=status))
    return dict(families=outcomes, eligible_families=eligible, gate_satisfied=len(eligible) >= 3,
                status='ready_for_review' if len(eligible) >= 3 else 'not_run_insufficient_eligible_families')


def select(root=ROOT, pilot=PILOT):
    root, pilot = Path(root).resolve(), Path(pilot).resolve()
    runner.verify(root, require_complete=True)
    rows = runner.report(root)
    tasks = runner.load(root / 'tasks.json')
    validation_path = root / 'failure-validation.json'
    validation = runner.load(validation_path) if validation_path.exists() else None
    decision = decide(tasks, rows, validation)
    decision.update(source_csv_sha256=runner.sha(root / 'results/trials.csv'),
                    source_calibration_manifest_sha256=runner.sha(root / 'manifest.json'),
                    validation_sha256=runner.sha(validation_path) if validation_path.exists() else None)
    heldout = runner.load(root / 'heldout.json')
    chosen = [t for t in heldout if t['family'] in decision['eligible_families']]
    decision['eligible_task_ids'] = [t['id'] for t in chosen]
    outputs = {pilot / 'selection.json': builder.encoded(decision)}
    if decision['gate_satisfied']:
        rows = [r for r in runner.load(pilot / 'planned-trials.json') if r['task'] in decision['eligible_task_ids']]
        extra = [root / 'results/trials.csv', root / 'manifest.json', pilot / 'selection.json']
        if validation_path.exists(): extra.append(validation_path)
        outputs.update({pilot / 'tasks.json': builder.encoded(chosen), pilot / 'trials.json': builder.encoded(rows),
                        pilot / 'protocol.json': builder.encoded(builder.protocol(chosen, 'pilot3', pilot, extra))})
    locked = (pilot / 'manifest.json').exists() or any((pilot / d).exists() and any((pilot / d).iterdir()) for d in ['records', 'dispatch'])
    if locked:
        if any(not path.exists() or path.read_text() != text for path, text in outputs.items()):
            raise ValueError('selection cannot change after pilot freeze or collection')
    else:
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    return decision


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        print(json.dumps(select(), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
