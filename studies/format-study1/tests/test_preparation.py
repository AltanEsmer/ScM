import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import prepare
import grader
import analyze

class PreparationTests(unittest.TestCase):
    def test_format_changes_only_instruction_structure(self):
        question = 'A < B & C\n\nExample:\n  1 2\n'
        for variant in 'ABC':
            rendered = prepare.prompt(question, variant)
            self.assertEqual(prepare.recover_question(rendered, variant), question)
            instructions = rendered.split('\n\n<problem>\n', 1)[0]
            if variant == 'A':
                clauses = instructions.split('\n\n')
            elif variant == 'B':
                clauses = [line.split('. ', 1)[1] for line in instructions.splitlines()]
            else:
                clauses = [node.text for node in ET.fromstring(instructions)]
            self.assertEqual(clauses, list(prepare.CLAUSES))

    def test_all_selected_questions_round_trip(self):
        selected = sorted((ROOT / 'source/selected').glob('*/task.json'))
        self.assertEqual(len(selected), 12)
        for path in selected:
            question = json.loads(path.read_text())['question']
            for variant in 'ABC':
                with self.subTest(task=path.parent.name, variant=variant):
                    self.assertEqual(prepare.recover_question(prepare.prompt(question, variant), variant), question)

    def test_curated_cases_preserve_all_valid_original_values(self):
        original = {'id': 'sample', 'input_output': {'inputs': [str(i) for i in range(14)],
                                                     'outputs': [f'answer-{i}' for i in range(14)]}}
        before = copy.deepcopy(original)
        valid = [i for i in range(14) if i not in (1, 13)]
        hashes = {'validate_selected.py': 'validator-a', 'validate_hard.py': 'validator-b'}
        evaluation = {'task_id': 'sample', 'source_task_sha256': 'source-hash',
                      'validator_sha256': hashes, 'case_indices': valid,
                      'inputs': [original['input_output']['inputs'][i] for i in valid],
                      'outputs': [original['input_output']['outputs'][i] for i in valid],
                      'excluded': [{'case_index': i, 'reason': 'statement violation',
                                    'input_sha256': hashlib.sha256(str(i).encode()).hexdigest(),
                                    'expected_sha256': hashlib.sha256(f'answer-{i}'.encode()).hexdigest()} for i in (1, 13)]}
        def validator(stdin, expected):
            if stdin in ('1', '13'):
                raise ValueError('statement violation')
        curated = prepare.validate_subset(original, evaluation, 'source-hash', hashes, validator)
        self.assertEqual(original, before)
        self.assertEqual(curated['inputs'], [str(i) for i in valid])
        changed = copy.deepcopy(evaluation)
        changed['outputs'][0] = 'repaired-answer'
        with self.assertRaises(ValueError):
            prepare.validate_subset(original, changed, 'source-hash', hashes, validator)
        pruned = copy.deepcopy(evaluation)
        for key in ('case_indices', 'inputs', 'outputs'):
            pruned[key] = pruned[key][1:]
        with self.assertRaises(ValueError):
            prepare.validate_subset(original, pruned, 'source-hash', hashes, validator)
        with self.assertRaises(ValueError):
            prepare.validate_subset(original, evaluation, 'changed-source', hashes, validator)

    def test_schedule_is_balanced_and_deterministic(self):
        ids = [f'task-{i}' for i in range(12)]
        trials = prepare.schedule(ids)
        self.assertEqual(trials, prepare.schedule(list(reversed(ids))))
        self.assertEqual(len(trials), 72)
        self.assertEqual(len({r['trial_id'] for r in trials}), 72)
        self.assertTrue(all(r['status'] == 'NOT_RUN' for r in trials))
        self.assertEqual(set(collections.Counter((r['variant'], r['position']) for r in trials).values()), {8})
        for block in range(1, 25):
            self.assertEqual({r['variant'] for r in trials if r['block'] == block}, set('ABC'))

    def test_analysis_pairs_tasks_and_marks_unavailable(self):
        trials = prepare.schedule([f'task-{i}' for i in range(12)])
        counts = {f'task-{i}': 1 for i in range(12)}
        outcomes = [{'trial_id': r['trial_id'], 'all_pass': r['variant'] == 'B',
                     'passed': int(r['variant'] == 'B'), 'total': 1,
                     'cases': [{'status': 'OK', 'passed': r['variant'] == 'B'}]} for r in trials]
        result = analyze.summarize(trials, outcomes, counts)
        self.assertEqual(result['mean_B_minus_A'], 1)
        self.assertEqual(result['mean_C_minus_A'], 0)
        missing = analyze.summarize(trials, outcomes[:-1], counts)
        self.assertFalse(missing['complete'])
        self.assertNotIn('mean_B_minus_A', missing)
        with self.assertRaises(ValueError):
            analyze.summarize(trials, outcomes[:-1] + outcomes[:1], counts)
        for corrupt in ({'cases': []}, {'total': 2},
                        {'cases': [{'status': 'INFRASTRUCTURE_ERROR', 'passed': False}], 'passed': 0, 'all_pass': False}):
            broken = [dict(r) for r in outcomes]
            broken[0].update(corrupt)
            report = analyze.summarize(trials, broken, counts)
            self.assertFalse(report['complete'])
            self.assertNotIn('mean_B_minus_A', report)
            self.assertEqual(len(report['unavailable']), 1)

    def test_partial_analysis_retains_observed_success_and_failure(self):
        trials = prepare.schedule([f'task-{i}' for i in range(12)])
        counts = {f'task-{i}': 1 for i in range(12)}
        trial = trials[0]
        def outcome(passed):
            return {'trial_id': trial['trial_id'], 'all_pass': passed, 'passed': int(passed),
                    'total': 1, 'cases': [{'status': 'OK', 'passed': passed}]}
        passing = analyze.summarize(trials, [outcome(True)], counts)
        failing = analyze.summarize(trials, [outcome(False)], counts)
        a = next(row for row in passing['per_task'] if row['task_id'] == trial['task_id'])['cells'][trial['variant']]
        b = next(row for row in failing['per_task'] if row['task_id'] == trial['task_id'])['cells'][trial['variant']]
        self.assertEqual((a['planned'], a['evaluable'], a['successes']), (2, 1, 1))
        self.assertEqual((b['planned'], b['evaluable'], b['successes']), (2, 1, 0))
        self.assertIsNone(a['mean'])
        self.assertIsNone(b['mean'])
        self.assertNotIn('mean_B_minus_A', passing)
        self.assertNotIn('mean_B_minus_A', failing)

    def test_outputs_reject_debug_and_wrong_tokens(self):
        self.assertTrue(grader.matches('1\t2\n', '1 2'))
        self.assertFalse(grader.matches('debug\n1 2', '1 2'))
        self.assertFalse(grader.matches('1.0 2', '1 2'))
        self.assertFalse(grader.matches('12', '1 2'))

    def test_verify_detects_tampering_and_extra_artifact(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            artifact = root / 'trials.json'
            artifact.write_text('[]')
            prepare.write_json(root / 'manifest.json', {'sha256': {'trials.json': prepare.digest(artifact)}})
            self.assertEqual(prepare.verify(root), 1)
            artifact.write_text('[1]')
            with self.assertRaises(ValueError):
                prepare.verify(root)
            artifact.write_text('[]')
            (root / 'extra.txt').write_text('extra')
            with self.assertRaises(ValueError):
                prepare.verify(root)

    def test_freeze_requires_validated_sources(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with patch.object(prepare, 'tasks', return_value=[]):
                prepare.write_json(root / 'reference-validation.json', {'status': 'FAIL', 'task_count': 12})
                with self.assertRaises(ValueError):
                    prepare.freeze(root)
            self.assertFalse((root / 'manifest.json').exists())

    def test_grader_compares_on_host(self):
        task = {'id': 'x', 'input_output': {'inputs': ['hello'], 'outputs': ['secret']}}
        with patch.object(grader, 'run_case', return_value={'status': 'OK', 'stdout': 'secret'}) as run:
            result = grader.grade('print(input())', task)
        run.assert_called_once_with('print(input())', 'hello')
        self.assertTrue(result['all_pass'])

if __name__ == '__main__':
    unittest.main()
