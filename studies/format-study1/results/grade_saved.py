#!/usr/bin/env python3
"""Grade a closed, fully recorded collection without modifying frozen artifacts."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def create_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


@dataclass(frozen=True)
class SavedTrial:
    scheduled: dict
    result: dict
    binding: dict


def checked_file(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Unsafe artifact path')
    return path


def closed_collection(root, verify):
    verify(root)
    manifest_path = root / 'manifest.json'
    manifest = read_json(manifest_path)
    if manifest.get('status') != 'FROZEN_NOT_RUN':
        raise ValueError('Frozen manifest required')
    freeze_hash = sha_bytes(manifest_path.read_bytes())
    image_id = read_json(root / 'isolation/offline-evidence.json')['image_id']
    trials = read_json(root / 'trials.json')
    if len(trials) != 72 or len({row['trial_id'] for row in trials}) != 72:
        raise ValueError('Exactly 72 distinct scheduled trials required')
    paths = []
    for trial in trials:
        folder = checked_file(root, 'runs/' + trial['trial_id'])
        paths.append((trial, folder / 'dispatch.json', folder / 'result.json'))
    if any(not dispatch.is_file() or not result.is_file() for _, dispatch, result in paths):
        raise ValueError('Collection is not closed: all 72 dispatch and result files required')
    saved = []
    identities = set()
    for trial, dispatch_path, result_path in paths:
        dispatch = read_json(dispatch_path)
        result = read_json(result_path)
        if dispatch.get('status') != 'attempted_no_retry' or result.get('status') != 'generated':
            raise ValueError('Collection contains failed or ambiguous generation')
        prompt_hash = manifest['sha256'][trial['prompt']]
        for record in (dispatch, result):
            for field, expected in {'trial_id': trial['trial_id'], 'freeze_sha256': freeze_hash,
                                    'prompt_sha256': prompt_hash, 'requested_model': 'gpt-6.1-sol',
                                    'effort': 'medium'}.items():
                if record.get(field) != expected:
                    raise ValueError(f'Generation metadata mismatch: {field}')
        if (result.get('reported_model') != 'gpt-6.1-sol' or result.get('tools') != []
                or not isinstance(result.get('answer'), str)
                or not isinstance(result.get('thread_id'), str) or not result['thread_id']
                or not result.get('completed_at_utc')):
            raise ValueError('Invalid saved generation identity or answer')
        if result['thread_id'] in identities:
            raise ValueError('Generation thread reused')
        identities.add(result['thread_id'])
        sources = {p.name: sha_bytes(p.read_bytes()) for p in (root / 'isolation').iterdir()
                   if p.suffix in ('.mjs', '.py') or p.name == 'Dockerfile'}
        if (dispatch.get('image_id') != image_id or result.get('image_id') != image_id
                or dispatch.get('source_sha256') != sources or result.get('source_sha256') != sources):
            raise ValueError('Generation image/source binding mismatch')
        binding = {'trial_id': trial['trial_id'], 'task_id': trial['task_id'],
                   'variant': trial['variant'], 'repetition': trial['repetition'],
                   'freeze_sha256': freeze_hash, 'prompt_sha256': prompt_hash,
                   'answer_sha256': sha_bytes(result['answer'].encode('utf-8')),
                   'dispatch_sha256': sha_bytes(dispatch_path.read_bytes()),
                   'generation_sha256': sha_bytes(result_path.read_bytes()),
                   'requested_model': result['requested_model'], 'reported_model': result['reported_model'],
                   'effort': result['effort'], 'thread_id': result['thread_id'],
                   'image_id': result['image_id'], 'source_sha256': sources,
                   'grader_sha256': sha_bytes((root / 'grader.py').read_bytes())}
        saved.append(SavedTrial(trial, result, binding))
    return saved


def run(root=STUDY):
    from prepare import verify, tasks
    from grader import grade
    saved = closed_collection(root, verify)
    selected = {task['id']: task for task in tasks(root)}
    outcomes = []
    for trial in saved:
        task = selected[trial.scheduled['task_id']]
        path = root / 'results' / 'trials' / (trial.scheduled['trial_id'] + '.json')
        attempt = path.with_suffix('.attempt.json')
        if path.exists():
            outcome = read_json(path)
            if any(outcome.get(key) != value for key, value in trial.binding.items()):
                raise ValueError('Existing grade belongs to different saved artifacts')
        else:
            create_json(attempt, {**trial.binding, 'status': 'grading_attempted_no_retry',
                                 'started_at_utc': datetime.now(timezone.utc).isoformat()})
            report = grade(trial.result['answer'], task, workers=3)
            for index, case in enumerate(report['cases']):
                case.update(evaluation_case_index=index,
                            source_case_index=task['evaluation_case_indices'][index],
                            input_sha256=sha_bytes(task['input_output']['inputs'][index].encode('utf-8')),
                            expected_sha256=sha_bytes(task['input_output']['outputs'][index].encode('utf-8')))
            outcome = {**report, **trial.binding,
                       'completed_at_utc': datetime.now(timezone.utc).isoformat()}
            create_json(path, outcome)
        if (outcome.get('task_id') != task['id']
                or outcome.get('total') != len(task['input_output']['inputs'])
                or len(outcome.get('cases', [])) != outcome['total']):
            raise ValueError('Malformed saved grade coverage')
        for index, case in enumerate(outcome['cases']):
            expected = {'evaluation_case_index': index,
                        'source_case_index': task['evaluation_case_indices'][index],
                        'input_sha256': sha_bytes(task['input_output']['inputs'][index].encode('utf-8')),
                        'expected_sha256': sha_bytes(task['input_output']['outputs'][index].encode('utf-8'))}
            if any(case.get(key) != value for key, value in expected.items()):
                raise ValueError('Saved grade case binding mismatch')
        outcomes.append(outcome)
        print(json.dumps({'trial_id': trial.scheduled['trial_id'], 'passed': outcome['passed'],
                          'total': outcome['total'], 'all_pass': outcome['all_pass']}), flush=True)
    output = root / 'results' / 'outcomes.json'
    if output.exists():
        if read_json(output) != outcomes:
            raise ValueError('Existing outcomes differ; refusing overwrite')
    else:
        create_json(output, outcomes)
    return outcomes


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
