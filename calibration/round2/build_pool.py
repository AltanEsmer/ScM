"""Build immutable development and held-out inputs before calibration collection."""
import html
import importlib.util
import json
import os
from pathlib import Path
import random
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PILOT = REPO / 'pilots/pilot3'
ENDING = 'Return only Python 3.12 code using the standard library. Define the requested function. Do not include Markdown fences, explanations, tests, or executable input/output code.'
OPENING = 'Implement the Python function {name} taking one argument.'


def inventory():
    tasks = []
    for number in range(1, 7):
        spec = importlib.util.spec_from_file_location(f'pool_family{number}', ROOT / f'pool/family{number}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        group = module.make_tasks()
        if len(group) != 3 or any(t.get('family') != f'F{number}' for t in group):
            raise ValueError('each family must supply three tasks')
        if sorted(t.get('role', '') for t in group) != ['development', 'heldout', 'heldout']:
            raise ValueError('each family requires one development and two heldout tasks')
        tasks.extend(group)
    if len({t['id'] for t in tasks}) != 18:
        raise ValueError('task IDs must be unique')
    for task in tasks:
        if (task['function'] != task['id'] or not isinstance(task['reference'], str) or not task['reference'].strip()
                or not isinstance(task['cases'], list) or not task['cases']
                or any(not isinstance(c, list) or len(c) != 2 for c in task['cases'])
                or not isinstance(task['clauses'], list) or not task['clauses']
                or any(not isinstance(c, str) or not c or '\n' in c or '\r' in c for c in task['clauses'])):
            raise ValueError('invalid task shape')
    return tasks


def render(task, variant):
    clauses = task['clauses']
    if variant in ['A', 'B0']:
        body = '\n'.join(clauses)
    elif variant == 'B':
        body = '\n'.join('- ' + c for c in clauses)
    elif variant == 'C':
        body = '<requirements>\n' + '\n'.join('<clause>' + html.escape(c, quote=True) + '</clause>' for c in clauses) + '\n</requirements>'
    else:
        raise ValueError('unknown variant')
    result = OPENING.format(name=task['function']) + '\n\n' + body + '\n\n' + ENDING + '\n'
    if decode(result, variant) != clauses:
        raise ValueError('prompt clauses differ')
    return result


def decode(prompt, variant):
    body = prompt.split('\n\n', 1)[1].rsplit('\n\n', 1)[0]
    if variant in ['A', 'B0']:
        return body.splitlines()
    if variant == 'B':
        if any(not line.startswith('- ') for line in body.splitlines()):
            raise ValueError('invalid list')
        return [line[2:] for line in body.splitlines()]
    return [node.text or '' for node in ET.fromstring(body)]


def trial(task, variant, repeat):
    return dict(trial_id=f'{task}_{variant}_{repeat:02d}', task=task, variant=variant, repeat=repeat, prompt_file=f'prompts/{task}_{variant}.txt')


def pilot_schedule(tasks):
    rng = random.Random(20261026)
    blocks = []
    for task in tasks:
        rotations = [i % 3 for i in range(10)]
        rng.shuffle(rotations)
        base = list('ABC')
        rng.shuffle(base)
        for repeat, rotation in enumerate(rotations, 1):
            variants = base[rotation:] + base[:rotation]
            blocks.append([trial(task['id'], v, repeat) for v in variants])
    rng.shuffle(blocks)
    return [row for block in blocks for row in block]


def frozen_files(root, extra=()):
    root = root.resolve()
    files = [REPO / 'experiments/runner.py', REPO / 'grading.py', ROOT / 'build_pool.py', ROOT / 'select_pilot3.py', ROOT / 'run.py', PILOT / 'run.py']
    files += sorted((ROOT / 'pool').glob('family*.py')) + sorted((ROOT / 'tests').glob('*.py'))
    files += [ROOT / name for name in ['tasks.json', 'heldout.json', 'canonical-clauses.json', 'protocol.json', 'trials.json']]
    files += sorted((ROOT / 'prompts').glob('*.txt')) + sorted((PILOT / 'prompts').glob('*.txt'))
    files += [PILOT / 'planned-trials.json']
    files += [root / name for name in ['tasks.json', 'protocol.json', 'trials.json', 'run.py']]
    files += list(extra)
    return sorted({os.path.relpath(path.resolve(), root) for path in files})


def protocol(tasks, phase, root, extra=()):
    prior = json.loads((REPO / 'calibration/round1/protocol.json').read_text())
    prior.update(id=phase+'-2026-10-22', phase=phase, tasks=[t['id'] for t in tasks],
                 families={t['id']: t['family'] for t in tasks}, variants=['B0'] if phase == 'composite_calibration' else list('ABC'),
                 repetitions=5 if phase == 'composite_calibration' else 10, seed=20261026,
                 selection_rule='All five evaluated; one to four all-case passes and at least one independently validated semantic failure. Invalid families excluded. At least three eligible families required; include both heldout tasks of every eligible family.',
                 analysis='Calibration screens families only. Pilot3 reports per-cell counts and equal-task averaged B-A and C-A only when every cell has ten evaluated responses.',
                 order='Precomputed order; at most three in flight.', frozen_files=frozen_files(root, extra))
    return prior


def write_outputs(outputs):
    protected = any((root / 'manifest.json').exists() or any((root / directory).exists() and any((root / directory).iterdir()) for directory in ['records', 'dispatch']) for root in [ROOT, PILOT])
    if protected:
        spec = importlib.util.spec_from_file_location('build_verify_runner', REPO / 'experiments/runner.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        for root in [ROOT, PILOT]:
            if (root / 'manifest.json').exists():
                runner.verify(root)
        if any(not path.exists() or path.read_text() != text for path, text in outputs.items()):
            raise ValueError('cannot rebuild changed inputs after freeze or collection')
        return
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def build():
    tasks = inventory()
    development = [t for t in tasks if t['role'] == 'development']
    heldout = [t for t in tasks if t['role'] == 'heldout']
    outputs = {ROOT / 'tasks.json': encoded(development), ROOT / 'heldout.json': encoded(heldout),
               ROOT / 'canonical-clauses.json': encoded({t['id']: t['clauses'] for t in tasks}),
               PILOT / 'planned-trials.json': encoded(pilot_schedule(heldout))}
    for task in tasks:
        for variant in (['B0'] if task['role'] == 'development' else list('ABC')):
            root = ROOT if variant == 'B0' else PILOT
            outputs[root / f"prompts/{task['id']}_{variant}.txt"] = render(task, variant)
    rows = [trial(t['id'], 'B0', r) for t in development for r in range(1, 6)]
    random.Random(20261026).shuffle(rows)
    outputs[ROOT / 'trials.json'] = encoded(rows)
    data = protocol(development, 'composite_calibration', ROOT)
    data['frozen_files'] = sorted(set(data['frozen_files']) | {os.path.relpath(p, ROOT) for p in outputs})
    outputs[ROOT / 'protocol.json'] = encoded(data)
    write_outputs(outputs)
    return tasks


if __name__ == '__main__':
    build()
    print('Built six development and twelve heldout tasks; all prompts and planned trials.')
