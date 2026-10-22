import argparse
import hashlib
import json
import math
import pathlib


def validate_medium(row, text, expected):
    tokens = text.split()
    position = 0

    def take():
        nonlocal position
        if position >= len(tokens):
            raise ValueError('input ended before declared structure')
        token = tokens[position]
        position += 1
        return token

    def integer(low, high):
        value = int(take())
        if not low <= value <= high:
            raise ValueError(f'input value {value} outside [{low}, {high}]')
        return value

    outputs = expected.split()
    if row == 760:
        n = integer(3, 100000)
        for _ in range(n):
            integer(1, 10**9)
        if len(outputs) != 1 or not 1 <= int(outputs[0]) <= math.comb(n, 3):
            raise ValueError('expected triple count outside declared domain')
    elif row == 402:
        n = integer(2, 100000)
        integer(1, n)
        for _ in range(n):
            integer(0, 1)
        parents = list(range(n))

        def find(x):
            while parents[x] != x:
                parents[x] = parents[parents[x]]
                x = parents[x]
            return x

        for _ in range(n - 1):
            u, v = integer(1, n) - 1, integer(1, n) - 1
            a, b = find(u), find(v)
            if a == b:
                raise ValueError('declared tree has cycle or duplicate edge')
            parents[a] = b
        if len({find(i) for i in range(n)}) != 1:
            raise ValueError('declared tree disconnected')
        if len(outputs) != 1 or not 0 <= int(outputs[0]) <= n - 1:
            raise ValueError('expected restaurant count outside declared domain')
    elif row == 472:
        n = integer(1, 100)
        if n % 2 != 1:
            raise ValueError('chess piece side must be odd')
        for _ in range(4 * n):
            bits = take()
            if len(bits) != n or set(bits) - {'0', '1'}:
                raise ValueError('chess piece row not n binary digits')
        if len(outputs) != 1 or not 0 <= int(outputs[0]) <= 4 * n * n:
            raise ValueError('expected recolor count outside declared domain')
    elif row == 74:
        n = integer(1, 300000)
        added = set()
        add_count = remove_count = stack_size = 0
        for _ in range(2 * n):
            action = take()
            if action == 'add':
                value = integer(1, n)
                if value in added:
                    raise ValueError('box added more than once')
                added.add(value)
                add_count += 1
                stack_size += 1
            elif action == 'remove':
                remove_count += 1
                stack_size -= 1
                if stack_size < 0 or remove_count not in added:
                    raise ValueError('box removed before it was added')
            else:
                raise ValueError('unknown stack command')
        if add_count != n or remove_count != n:
            raise ValueError('command counts do not equal n')
        if len(outputs) != 1 or not 0 <= int(outputs[0]) <= n:
            raise ValueError('expected reorder count outside declared domain')
    elif row == 250:
        n = integer(1, 100000)
        for _ in range(n):
            integer(1, 10**9)
        if len(outputs) != n or any(int(value) < 1 for value in outputs):
            raise ValueError('expected one positive integer per input number')
    elif row == 320:
        n = integer(1, 10**6)
        for _ in range(n):
            integer(0, 10**6)
        if len(outputs) != 1 or not 1 <= int(outputs[0]) <= n:
            raise ValueError('expected lifting step count outside declared domain')
    else:
        raise ValueError(f'no reviewed input contract for MEDIUM row {row}')
    if position != len(tokens):
        raise ValueError('unconsumed input after declared structure')


def run(root, export=False):
    from validate_hard import validate as validate_hard
    selection = json.loads((root / 'selection.json').read_text())
    results = []
    index_map = {}
    validator_hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ['validate_selected.py', 'validate_hard.py']}
    for item in selection['selected']:
        row = item['row_index']
        task_file = root / 'selected' / f'taco-test-{row:04d}' / 'task.json'
        task = json.loads(task_file.read_text())
        failures = []
        tests = task['input_output']
        for index, (case_input, case_expected) in enumerate(zip(tests['inputs'], tests['outputs'])):
            try:
                if item['difficulty'] == 'MEDIUM':
                    validate_medium(row, case_input, case_expected)
                else:
                    validate_hard(row, case_input, case_expected)
            except (ValueError, AssertionError, IndexError, StopIteration) as error:
                failures.append({'case_index': index, 'reason': str(error), 'input_sha256': hashlib.sha256(case_input.encode()).hexdigest(), 'expected_sha256': hashlib.sha256(case_expected.encode()).hexdigest(), 'original_case_sha256': hashlib.sha256(json.dumps({'input': case_input, 'expected': case_expected}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        excluded_indices = {item['case_index'] for item in failures}
        retained = [index for index in range(len(tests['inputs'])) if index not in excluded_indices]
        evaluation = {'task_id': task['id'], 'source_task_sha256': hashlib.sha256(task_file.read_bytes()).hexdigest(), 'validator_sha256': validator_hashes, 'case_indices': retained, 'inputs': [tests['inputs'][index] for index in retained], 'outputs': [tests['outputs'][index] for index in retained], 'excluded': failures}
        evaluation_path = task_file.parent / 'evaluation-cases.json'
        if export:
            evaluation_path.write_text(json.dumps(evaluation, indent=2) + '\n')
        evaluation_sha256 = hashlib.sha256((json.dumps(evaluation, indent=2) + '\n').encode()).hexdigest()
        index_map[task['id']] = {'case_indices': retained, 'source_task_sha256': evaluation['source_task_sha256'], 'evaluation_cases_sha256': evaluation_sha256}
        results.append({'raw_case_count': len(tests['inputs']), 'curated_case_count': len(retained), 'excluded_case_count': len(failures), 'curated_passed': len(retained) >= 10, 'evaluation_cases_sha256': evaluation_sha256, 'task_id': task['id'], 'row_index': row, 'case_count': len(tests['inputs']), 'task_sha256': hashlib.sha256(task_file.read_bytes()).hexdigest(), 'passed': not failures, 'failures': failures})
    report = {'stage': 'READY_FOR_CURATED_PREFLIGHT' if all(item['curated_passed'] for item in results) else 'CURATION_FAILED', 'raw_all_passed': all(item['passed'] for item in results), 'curated_all_passed': all(item['curated_passed'] for item in results), 'validator_sha256': validator_hashes, 'raw_case_count': sum(item['raw_case_count'] for item in results), 'curated_case_count': sum(item['curated_case_count'] for item in results), 'excluded_case_count': sum(item['excluded_case_count'] for item in results), 'method': 'Task-specific statement input/domain and expected-shape checks. No answer computation or reference execution.', 'all_passed': all(item['passed'] for item in results), 'tasks': results}
    (root / 'structural-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    if export:
        (root / 'evaluation-index-map.json').write_text(json.dumps(index_map, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report['curated_all_passed'] if export else report['raw_all_passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    raise SystemExit(0 if run(args.source, args.export) else 1)
