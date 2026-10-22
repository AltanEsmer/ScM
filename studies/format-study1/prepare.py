"""Build and verify preparation artifacts; never invoke a model."""
import argparse
import hashlib
import itertools
import importlib.util
import json
from pathlib import Path
import random
import subprocess
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SEED = 20261022
CLAUSES = (
    'Solve the programming problem below.',
    'Use Python 3.12 and only the Python standard library.',
    'Read input from standard input and write the required output to standard output.',
    'Return only runnable Python source code, without Markdown fences or explanation.',
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def prompt(question, variant):
    if variant == 'A':
        instructions = '\n\n'.join(CLAUSES)
    elif variant == 'B':
        instructions = '\n'.join(f'{i}. {clause}' for i, clause in enumerate(CLAUSES, 1))
    elif variant == 'C':
        instructions = '<instructions>\n' + '\n'.join(f'<instruction>{escape(c)}</instruction>' for c in CLAUSES) + '\n</instructions>'
    else:
        raise ValueError(variant)
    paragraphs = question.split('\n\n')
    if variant == 'A':
        problem = question
    elif variant == 'B':
        problem = '\n\n'.join(f'{i}. ' + text.replace('\n', '\n   ') for i, text in enumerate(paragraphs, 1))
    else:
        problem = '\n'.join('<paragraph>' + escape(text) + '</paragraph>' for text in paragraphs)
    return instructions + '\n\n<problem>\n' + problem + '\n</problem>\n'

def recover_question(rendered, variant):
    problem = rendered.split('\n\n<problem>\n', 1)[1].removesuffix('\n</problem>\n')
    if variant == 'A':
        return problem
    if variant == 'B':
        return '\n\n'.join(block.split('. ', 1)[1].replace('\n   ', '\n') for block in problem.split('\n\n'))
    return '\n\n'.join(node.text or '' for node in ET.fromstring('<problem>' + problem + '</problem>'))

def schedule(task_ids):
    rng = random.Random(SEED)
    blocks = [(task, rep) for task in sorted(task_ids) for rep in (1, 2)]
    rng.shuffle(blocks)
    orders = list(itertools.permutations('ABC')) * 4
    rng.shuffle(orders)
    return [dict(trial_id=f'{task}-r{rep}-{variant}', task_id=task, repetition=rep,
                 block=block, position=position, variant=variant,
                 prompt=f'prompts/{task}/{variant}.txt', status='NOT_RUN')
            for block, ((task, rep), order) in enumerate(zip(blocks, orders), 1)
            for position, variant in enumerate(order, 1)]

def validate_subset(row, evaluation, source_hash, validator_hashes, validate_case):
    original = row['input_output']
    indices = evaluation['case_indices']
    if (evaluation.get('task_id') != row['id'] or evaluation.get('source_task_sha256') != source_hash
            or evaluation.get('validator_sha256') != validator_hashes):
        raise ValueError('Curated fixtures do not match original source or validators')
    if (len(indices) < 10 or any(type(i) is not int for i in indices)
            or indices != sorted(set(indices)) or any(i < 0 or i >= len(original['inputs']) for i in indices)):
        raise ValueError('Invalid curated case index set')
    if (evaluation.get('inputs') != [original['inputs'][i] for i in indices]
            or evaluation.get('outputs') != [original['outputs'][i] for i in indices]):
        raise ValueError('Curated inputs or expected outputs differ from original cases')
    valid = []
    for index, (stdin, expected) in enumerate(zip(original['inputs'], original['outputs'])):
        try:
            validate_case(stdin, expected)
        except (ValueError, AssertionError, IndexError, StopIteration):
            continue
        valid.append(index)
    if indices != valid:
        raise ValueError('Curated set must contain every and only statement-validator-passing case')
    exclusions = evaluation.get('excluded', [])
    excluded_indices = [entry['case_index'] for entry in exclusions]
    if sorted(excluded_indices) != sorted(set(range(len(original['inputs']))) - set(indices)):
        raise ValueError('Every excluded original case must be recorded exactly once')
    for entry in exclusions:
        index = entry['case_index']
        if (not entry.get('reason')
                or entry['input_sha256'] != hashlib.sha256(original['inputs'][index].encode()).hexdigest()
                or entry['expected_sha256'] != hashlib.sha256(original['outputs'][index].encode()).hexdigest()):
            raise ValueError('Excluded case evidence differs from original source')
    return {'inputs': list(evaluation['inputs']), 'outputs': list(evaluation['outputs'])}

def load_task(path, root):
    row = json.loads(path.read_text(encoding='utf-8'))
    evaluation_path = path.parent / 'evaluation-cases.json'
    evaluation = json.loads(evaluation_path.read_text(encoding='utf-8'))
    modules = {}
    validator_hashes = {}
    for filename in ('validate_selected.py', 'validate_hard.py'):
        source = root / 'source' / filename
        validator_hashes[filename] = digest(source)
        spec = importlib.util.spec_from_file_location('study_' + filename[:-3], source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[filename] = module
    index = row['metadata']['row_index']
    validator = modules['validate_hard.py'].validate if row['difficulty'] == 'HARD' else modules['validate_selected.py'].validate_medium
    curated = validate_subset(row, evaluation, digest(path), validator_hashes,
                              lambda stdin, expected: validator(index, stdin, expected))
    row['source_test_count'] = len(row['input_output']['inputs'])
    row['evaluation_case_indices'] = list(evaluation['case_indices'])
    row['input_output'] = curated
    return row

def tasks(root):
    paths = sorted((root / 'source/selected').glob('*/task.json'))
    rows = [load_task(p, root) for p in paths]
    if len(rows) != 12 or len({r['id'] for r in rows}) != 12:
        raise ValueError('Exactly 12 distinct selected tasks are required')
    if sorted(r['difficulty'] for r in rows) != ['HARD'] * 6 + ['MEDIUM'] * 6:
        raise ValueError('Expected six HARD and six MEDIUM tasks')
    for path, row in zip(paths, rows):
        io = row['input_output']
        if len(io['inputs']) < 10 or len(io['inputs']) != len(io['outputs']):
            raise ValueError(f'Invalid test cases: {path}')
        if not all(isinstance(x, str) for x in io['inputs'] + io['outputs']):
            raise ValueError('Cases must use strings')
        if not (path.parent / 'reference.py').is_file():
            raise ValueError(f'Missing reference: {path}')
    return rows

def build(root=ROOT):
    if (root / 'manifest.json').exists():
        raise ValueError('Frozen study cannot be rebuilt; preserve its artifacts')
    rows = tasks(root)
    selected_ids = {row['id'] for row in rows}
    prompts = root / 'prompts'
    if prompts.exists():
        for folder in prompts.iterdir():
            if folder.is_dir() and folder.name not in selected_ids:
                if any(p.name not in ('A.txt', 'B.txt', 'C.txt') or not p.is_file() for p in folder.iterdir()):
                    raise ValueError('Unexpected files in obsolete generated prompt directory')
                for path in folder.iterdir():
                    path.unlink()
                folder.rmdir()
    for row in rows:
        folder = root / 'prompts' / row['id']
        folder.mkdir(parents=True, exist_ok=True)
        for variant in 'ABC':
            (folder / f'{variant}.txt').write_text(prompt(row['question'], variant), encoding='utf-8')
    write_json(root / 'trials.json', schedule([r['id'] for r in rows]))
    write_json(root / 'prompt-contract.json', {'status': 'PRESPECIFIED', 'seed': SEED, 'clauses': CLAUSES,
        'problem_partition': 'question.split(\"\\n\\n\"); exact reconstruction with blank-line join',
        'variants': {'A': 'prose instructions and source paragraphs', 'B': 'numbered instruction and problem paragraphs', 'C': 'XML instruction and problem paragraph elements'},
        'model': 'gpt-6.1-sol', 'reasoning_effort': 'medium',
        'primary_outcome': 'all curated frozen cases pass', 'evaluation_scope': 'Statement-validator-passing supplied cases; originals retained; not an official TACO score', 'comparison': 'whitespace-separated tokens, exact string equality',
        'analysis': 'Average repetitions within each task; report per-task B-A and C-A and their means; descriptive only.'})

def artifact_paths(root):
    return sorted(p for p in root.rglob('*') if p.is_file()
                  and p not in (root / 'manifest.json', root / 'verification.md', root / 'README.md')
                  and '__pycache__' not in p.parts and p.suffix != '.pyc'
                  and not any(x in p.parts for x in ('results', 'runs')))

def freeze(root=ROOT):
    if (root / 'manifest.json').exists():
        raise ValueError('Manifest already exists')
    rows = tasks(root)
    report = json.loads((root / 'reference-validation.json').read_text())
    if report.get('status') != 'PASS' or report.get('task_count') != 12:
        raise ValueError('Successful reference validation is required')
    evidence_path = root / 'isolation/offline-evidence.json'
    evidence = json.loads(evidence_path.read_text())
    if (evidence.get('status') != 'offline_isolation_verified_live_preflight_pending'
            or evidence.get('live_provider_requests') != 0 or evidence.get('candidate_trials') != 0
            or not evidence.get('image_id')):
        raise ValueError('Passing offline isolation evidence with zero candidate calls required')
    contract = json.loads((root / 'prompt-contract.json').read_text())
    body = evidence.get('provider_request', {}).get('body', {})
    if (contract.get('model') != 'gpt-6.1-sol' or contract.get('reasoning_effort') != 'medium'
            or contract.get('seed') != SEED or contract.get('clauses') != list(CLAUSES)
            or body.get('model') != contract['model'] or body.get('reasoning', {}).get('effort') != contract['reasoning_effort']
            or body.get('tools') != []):
        raise ValueError('Prompt contract or offline captured model settings differ')
    isolation_sources = {p.name: digest(p) for p in (root / 'isolation').iterdir()
                         if p.suffix in ('.py', '.mjs') or p.name == 'Dockerfile'}
    if evidence.get('image_source_sha256') != {name:isolation_sources[name] for name in ('client.mjs', 'relay.mjs', 'live_transport.mjs')}:
        raise ValueError('Offline proof does not bind executed image modules to current sources')
    if evidence.get('source_sha256') != isolation_sources:
        raise ValueError('Offline isolation source coverage changed')
    image = subprocess.run(['docker', 'image', 'inspect', evidence['image_id'], '--format', '{{.Id}}'],
                           capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    if image != evidence['image_id']:
        raise ValueError('Offline isolation image is unavailable or differs')
    for relative, expected_hash in evidence.get('source_sha256', {}).items():
        path = root / 'isolation' / relative
        if not path.resolve().is_relative_to((root / 'isolation').resolve()) or digest(path) != expected_hash:
            raise ValueError('Offline isolation evidence does not match its source files')
    if not evidence.get('source_sha256'):
        raise ValueError('Offline source hashes required')
    if (root / 'runs').exists() and any((root / 'runs').iterdir()):
        raise ValueError('Candidate collection must not have started before freezing')
    expected = {r['id']: digest(root / 'source/selected' / r['id'] / 'task.json') for r in rows}
    refs = {r['id']: digest(root / 'source/selected' / r['id'] / 'reference.py') for r in rows}
    evaluations = {r['id']: digest(root / 'source/selected' / r['id'] / 'evaluation-cases.json') for r in rows}
    if report.get('grader_sha256') != digest(root / 'grader.py'):
        raise ValueError('Reference evidence uses a different grader')
    if report.get('task_sha256') != expected or report.get('reference_sha256') != refs or report.get('evaluation_sha256') != evaluations:
        raise ValueError('Reference validation does not match current source')
    structural = json.loads((root / 'source/structural-validation.json').read_text())
    structural_rows = {r['task_id']: r for r in structural.get('tasks', [])}
    if structural.get('curated_all_passed') is not True or set(structural_rows) != set(expected):
        raise ValueError('All selected fixtures must pass statement-derived structural validation')
    if any(structural_rows[task_id].get('task_sha256') != sha for task_id, sha in expected.items()):
        raise ValueError('Structural validation does not match selected source hashes')
    reports = {r['task_id']: r for r in report.get('reports', [])}
    if set(reports) != set(expected):
        raise ValueError('Reference report task coverage differs')
    for row in rows:
        result = reports[row['id']]
        count = len(row['input_output']['inputs'])
        if (result.get('total') != count or result.get('passed') != count
                or result.get('all_pass') is not True or len(result.get('cases', [])) != count
                or any(c.get('status') != 'OK' or c.get('passed') is not True for c in result['cases'])):
            raise ValueError('Reference cases do not all pass')
    if json.loads((root / 'trials.json').read_text()) != schedule([r['id'] for r in rows]):
        raise ValueError('Schedule differs from prespecified schedule')
    for row in rows:
        for v in 'ABC':
            if (root / 'prompts' / row['id'] / f'{v}.txt').read_text() != prompt(row['question'], v):
                raise ValueError('Prompt differs from canonical rendering')
    write_json(root / 'manifest.json', {'schema_version': 1, 'status': 'FROZEN_NOT_RUN',
        'sha256': {str(p.relative_to(root)): digest(p) for p in artifact_paths(root)}})

def verify(root=ROOT):
    manifest = json.loads((root / 'manifest.json').read_text())
    actual = {str(p.relative_to(root)): digest(p) for p in artifact_paths(root)}
    if actual != manifest['sha256']:
        raise ValueError('Frozen artifact set or content changed')
    return len(actual)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'freeze', 'verify'])
    args = parser.parse_args()
    result = globals()[args.command]()
    print(json.dumps({'command': args.command, 'status': 'PASS', 'artifacts': result}))
