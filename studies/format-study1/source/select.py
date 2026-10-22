import argparse, ast, collections, hashlib, json, pathlib, re, sys
import pyarrow.parquet as pq
parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=pathlib.Path, required=True)
parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
args = parser.parse_args()
ROOT = args.output_dir
ROOT.mkdir(parents=True, exist_ok=True)
SEED = 'scm-format-study1-external-v1'
rows = pq.read_table(args.dataset).to_pylist()
spj = {x['idx'] for x in map(json.loads, (ROOT / 'output_spj.jsonl').read_text().splitlines()) if x['special_judge']}
counts = collections.Counter()
eligible = []
exclusions = []
for i, row in enumerate(rows):
    counts['difficulty:' + row['difficulty']] += 1
    if 'hackerrank' in ((row.get('source') or '') + (row.get('url') or '')).lower():
        counts['unknown-license-hackerrank'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'unknown-license-hackerrank', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    try:
        io = json.loads(row['input_output'])
        solutions = json.loads(row['solutions'])
    except (TypeError, ValueError):
        counts['invalid-json'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'invalid-json', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    if i in spj or io.get('fn_name') or row.get('starter_code') or re.search(r'interactive|special judge|any (?:valid|correct)|absolute or relative error', row['question'], re.I):
        counts['non-exact-or-function'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'non-exact-or-function', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    ins, outs = io.get('inputs', []), io.get('outputs', [])
    if len(ins) < 10 or len(ins) != len(outs) or not all(isinstance(v, str) for v in ins + outs):
        counts['tests'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'tests', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    if any(re.search(r'(?<!\w)[+-]?(?:\d+\.\d*|\d*\.\d+|\d+[eE][+-]?\d+)', out) for out in outs):
        counts['float-output'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'float-output', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    seen = {}
    conflicts = []
    for case_index, (case_input, case_output) in enumerate(zip(ins, outs)):
        key = case_input.replace('\r\n', '\n').strip()
        normalized_output = ' '.join(case_output.split())
        if key in seen and seen[key][1] != normalized_output:
            conflicts.append({'first_case': seen[key][0], 'conflicting_case': case_index, 'input_sha256': hashlib.sha256(key.encode()).hexdigest(), 'first_output_sha256': hashlib.sha256(seen[key][1].encode()).hexdigest(), 'conflicting_output_sha256': hashlib.sha256(normalized_output.encode()).hexdigest()})
        else:
            seen[key] = (case_index, normalized_output)
    preparation_reason = None
    if '<image>' in row['question'].lower():
        preparation_reason = 'missing-image-placeholder-in-statement'
    elif conflicts:
        preparation_reason = 'duplicate-input-contradictory-expected-output'
    elif i == 78:
        preparation_reason = 'malformed-supplied-case-40-two-input-tests-three-output-lines'
    elif i == 44:
        preparation_reason = 'malformed-supplied-cases-83-and-86-two-input-tests-three-output-lines'
    elif i == 60:
        preparation_reason = 'malformed-supplied-case-61-disconnected-cyclic-graph-not-tree'
    elif i in {355,765}:
        preparation_reason = 'malformed-supplied-output-arity-does-not-match-declared-test-count'
    elif i == 778:
        preparation_reason = 'valid-input-case-94-semantically-incorrect-supplied-expected-output'
    if preparation_reason:
        counts[preparation_reason] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': preparation_reason, 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest(), 'conflict_witnesses': conflicts})
        continue
    usable = []
    for n, code in enumerate(solutions):
        try:
            tree = ast.parse(code)
        except (SyntaxError, TypeError):
            continue
        modules = {a.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for a in node.names}
        modules |= {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        forbidden = {'os','subprocess','socket','requests','urllib','pathlib','pickle','marshal','ctypes','multiprocessing'}
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        if modules <= sys.stdlib_module_names and not modules & forbidden and not calls & {'eval','exec','compile','__import__','open'}:
            usable.append((n, code))
            break
    if not usable:
        counts['no-static-python3-reference'] += 1
        exclusions.append({'row_index': i, 'external_id': row.get('url') or row.get('name') or f'taco-test-{i:04d}', 'reason': 'no-static-python3-reference', 'row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()})
        continue
    external_id = row.get('url') or row.get('name') or f'taco-test-{i:04d}'
    eligible.append({'id': external_id, 'row_index': i, 'difficulty': row['difficulty'], 'name': row['name'], 'source': row['source'], 'test_count': len(ins), 'solution_index': usable[0][0], 'reference_sha256': hashlib.sha256(usable[0][1].encode()).hexdigest(), 'rank': hashlib.sha256((SEED + '\0' + external_id).encode()).hexdigest()})
selected = []
for difficulty in ['MEDIUM', 'HARD']:
    candidates = sorted((x for x in eligible if x['difficulty'] == difficulty), key=lambda x: (x['rank'], x['id']))
    selected.extend(candidates[:6])
manifest = {'status': 'preliminary-static-selection-awaiting-container-reference-validation', 'dataset': 'BAAI/TACO', 'revision': 'd593ed0a2becbbc952230bb89be09189bf1056dc', 'split': 'test', 'shard_url': 'https://huggingface.co/datasets/BAAI/TACO/resolve/d593ed0a2becbbc952230bb89be09189bf1056dc/ALL/test-00000-of-00001.parquet', 'shard_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(), 'seed': SEED, 'selection_rule': 'External IDs sorted lexically for enumeration; rank sha256(seed + NUL + external_id), first six each MEDIUM and HARD after declared static filters. No model outcomes used.', 'eligibility_counts': dict(counts), 'excluded': exclusions, 'eligible_by_difficulty': dict(collections.Counter(x['difficulty'] for x in eligible)), 'selected': selected, 'eligible': sorted(eligible, key=lambda x: x['id']), 'files': {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ['output_spj.jsonl','LICENSE','README.upstream.md','README.github.md','LICENSE-CC-BY-4.0.txt']}}
(ROOT / 'selection.json').write_text(json.dumps(manifest, indent=2) + '\n')
for item in selected:
    row = rows[item['row_index']]
    target = ROOT / 'selected' / f"taco-test-{item['row_index']:04d}"
    target.mkdir(parents=True, exist_ok=True)
    (target / 'task.json').write_text(json.dumps({'id': f"taco-test-{item['row_index']:04d}", 'difficulty': item['difficulty'], 'metadata': item, 'question': row['question'], 'input_output': json.loads(row['input_output']), 'tags': row['tags'], 'time_limit': row['time_limit'], 'memory_limit': row['memory_limit']}, indent=2) + '\n')
    (target / 'reference.py').write_text(json.loads(row['solutions'])[item['solution_index']])
print(json.dumps({k:v for k,v in manifest.items() if k not in ['eligible','excluded','files']}, indent=2))
