import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare
import recover_references

class ReferenceRecoveryTests(unittest.TestCase):
    def fixture(self, root, failure_status='INFRASTRUCTURE_ERROR'):
        (root / 'grader.py').write_text('frozen grader fixture')
        folder = root / 'source/selected/task-a'
        folder.mkdir(parents=True)
        for name in ('task.json', 'reference.py', 'evaluation-cases.json'):
            (folder / name).write_text('{}')
        task = {'id': 'task-a', 'evaluation_case_indices': [7],
                'input_output': {'inputs': ['1'], 'outputs': ['2']}}
        report = {'status': 'FAIL', 'task_count': 1, 'grader_sha256': prepare.digest(root / 'grader.py'),
                  'reports': [{'task_id': 'task-a', 'all_pass': False, 'passed': 0, 'total': 1,
                               'cases': [{'status': failure_status, 'passed': False}]}]}
        for field, name in (('task_sha256', 'task.json'), ('reference_sha256', 'reference.py'),
                            ('evaluation_sha256', 'evaluation-cases.json')):
            report[field] = {'task-a': prepare.digest(folder / name)}
        prepare.write_json(root / 'reference-validation.json', report)
        prepare.write_json(root / 'reference-validation.partial.json', {'status': 'INCOMPLETE'})
        (root / 'reference-validation.cases.jsonl').write_text('preserved original attempt\n')
        return task

    def test_recovery_preserves_attempt_and_revalidates_full_task_sequentially(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            task = self.fixture(root)
            original = (root / 'reference-validation.json').read_bytes()
            def successful_grade(code, received, workers, on_case):
                self.assertEqual(workers, 1)
                self.assertEqual(received, task)
                case = {'status': 'OK', 'passed': True, 'stdout': '2'}
                on_case(0, case)
                return {'task_id': 'task-a', 'all_pass': True, 'passed': 1, 'total': 1, 'cases': [case]}
            with patch.object(recover_references, 'tasks', return_value=[task]), patch.object(recover_references, 'grade', side_effect=successful_grade):
                result = recover_references.recover(root)
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual((root / 'reference-attempts/attempt-1/reference-validation.json').read_bytes(), original)
            self.assertEqual(result['recovery']['affected_task_ids'], ['task-a'])
            self.assertEqual(json.loads((root / 'reference-recovery.cases.jsonl').read_text())['source_case_index'], 7)

    def test_recovery_refuses_semantic_failure(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            task = self.fixture(root, failure_status='OK')
            with patch.object(recover_references, 'tasks', return_value=[task]), self.assertRaises(ValueError):
                recover_references.recover(root)
            self.assertFalse((root / 'reference-attempts').exists())

if __name__ == '__main__':
    unittest.main()
