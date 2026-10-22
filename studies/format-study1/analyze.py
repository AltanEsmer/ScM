"""Descriptive paired summaries with explicit unavailable observations."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVALUABLE_STATUSES = {'OK', 'TIMEOUT', 'OUTPUT_LIMIT', 'INVALID_UTF8', 'EXECUTION_ERROR'}

def evaluable(outcome, expected_cases):
    cases = outcome.get('cases')
    if not isinstance(cases, list) or len(cases) != expected_cases or outcome.get('total') != expected_cases:
        return None, 'MISSING_OR_MALFORMED_CASE_COVERAGE'
    for case in cases:
        if case.get('status') not in EVALUABLE_STATUSES:
            return None, 'INFRASTRUCTURE_OR_UNKNOWN_CASE_STATUS'
        if type(case.get('passed')) is not bool or (case['passed'] and case['status'] != 'OK'):
            return None, 'MALFORMED_CASE_RESULT'
    passed = sum(case['passed'] for case in cases)
    all_pass = passed == expected_cases
    if outcome.get('passed') != passed or type(outcome.get('all_pass')) is not bool or outcome['all_pass'] != all_pass:
        return None, 'INCONSISTENT_AGGREGATE'
    return all_pass, None

def summarize(trials, outcomes, case_counts):
    expected = {r['trial_id']: r for r in trials}
    if len(expected) != 72 or len(trials) != 72:
        raise ValueError('Exactly 72 distinct scheduled trials required')
    indexed = {r['trial_id']: r for r in outcomes}
    if len(indexed) != len(outcomes) or not set(indexed) <= set(expected):
        raise ValueError('Unknown or duplicate outcome trial IDs')
    task_ids = sorted({r['task_id'] for r in trials})
    if set(case_counts) != set(task_ids) or any(type(n) is not int or n < 1 for n in case_counts.values()):
        raise ValueError('Frozen positive case counts required for every task')
    rows = []
    unavailable = []
    for task in task_ids:
        cells = {}
        for variant in 'ABC':
            values = []
            missing = []
            planned = 0
            for trial in trials:
                if trial['task_id'] != task or trial['variant'] != variant:
                    continue
                planned += 1
                outcome = indexed.get(trial['trial_id'])
                value, reason = (None, 'MISSING_OUTCOME') if outcome is None else evaluable(outcome, case_counts[task])
                if reason:
                    entry = {'trial_id': trial['trial_id'], 'reason': reason}
                    missing.append(entry)
                    unavailable.append(entry)
                else:
                    values.append(int(value))
            cells[variant] = {'planned': planned, 'evaluable': len(values), 'successes': sum(values), 'unavailable': missing,
                              'mean': sum(values) / 2 if len(values) == 2 and not missing else None}
        rows.append({'task_id': task, 'cells': cells})
    result = {'task_count': len(rows), 'scheduled_trials': 72, 'received_outcomes': len(outcomes),
              'complete': not unavailable, 'unavailable': unavailable, 'per_task': rows,
              'interpretation': 'Descriptive only; summary contrasts require all 72 evaluable trials. No significance or equivalence claim.'}
    if not unavailable:
        for row in rows:
            row['B_minus_A'] = row['cells']['B']['mean'] - row['cells']['A']['mean']
            row['C_minus_A'] = row['cells']['C']['mean'] - row['cells']['A']['mean']
        result['mean_B_minus_A'] = sum(r['B_minus_A'] for r in rows) / len(rows)
        result['mean_C_minus_A'] = sum(r['C_minus_A'] for r in rows) / len(rows)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('outcomes', type=Path)
    args = parser.parse_args()
    from prepare import verify, tasks
    verify(ROOT)
    counts = {r['id']: len(r['input_output']['inputs']) for r in tasks(ROOT)}
    print(json.dumps(summarize(json.loads((ROOT / 'trials.json').read_text()),
                               json.loads(args.outcomes.read_text()), counts), indent=2))
