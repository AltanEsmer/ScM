import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import grading
import scm


class PilotTests(unittest.TestCase):
    def test_exact_nested_types(self):
        self.assertFalse(grading.exact([True], [1]))
        self.assertFalse(grading.exact({'a': True}, {'a': 1}))
        self.assertTrue(grading.exact({'a': [1]}, {'a': [1]}))

    def test_stdout_cannot_claim_pass(self):
        self.assertEqual(grading.score({'cases': [[[], []]], 'id': 'deduplicate'},
                                       '{"status":"pass"}')[0], 'invalid_output')
        self.assertEqual(grading.score({'cases': [[[], []]], 'id': 'deduplicate'},
                                       'not json')[0], 'invalid_output')

    def test_freeze_and_record_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for directory in ('experiment', 'prompts'):
                shutil.copytree(ROOT / directory, root / directory)
            for name in ('scm.py', 'grading.py'):
                shutil.copy(ROOT / name, root / name)
            scm.freeze(root)
            self.assertEqual(len(scm.verify(root)), 45)
            with self.assertRaises(ValueError):
                scm.verify(root, True)
            trial = scm.trials(root)[0]
            directory = root / 'records' / trial.trial_id
            directory.mkdir(parents=True)
            answer = b'def deduplicate(values): return []\n'
            (directory / 'answer.txt').write_bytes(answer)
            evidence = dict(trial_id=trial.trial_id, session_id='one', requested_model='gpt-6.1-sol',
                            requested_reasoning='medium', fork_turns='none',
                            dispatch_observed_utc='2026-10-22T10:00:00Z', completion_observed_utc='2026-10-22T10:01:00Z',
                            backend='collaboration.spawn_agent', observed_model=None, tool_trace_available=False,
                            prompt_sha256=scm.sha(root / trial.prompt_file), response_sha256=scm.sha(directory / 'answer.txt'),
                            capture_method='coordinator copied returned final message')
            (directory / 'evidence.json').write_text(json.dumps(evidence))
            self.assertEqual(scm.verify(root)[0].status, 'collected')
            second = scm.trials(root)[1]
            duplicate = root / 'records' / second.trial_id
            duplicate.mkdir()
            (duplicate / 'answer.txt').write_bytes(answer)
            second_evidence = dict(evidence, trial_id=second.trial_id,
                                   prompt_sha256=scm.sha(root / second.prompt_file))
            (duplicate / 'evidence.json').write_text(json.dumps(second_evidence))
            with self.assertRaisesRegex(ValueError, 'duplicate session'):
                scm.verify(root)
            shutil.rmtree(duplicate)
            (directory / 'evidence.json').unlink()
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                scm.verify(root)
            (directory / 'evidence.json').write_text(json.dumps(evidence))
            prompt = root / trial.prompt_file
            original_prompt = prompt.read_bytes()
            prompt.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'frozen inputs'):
                scm.verify(root)
            prompt.write_bytes(original_prompt)
            (directory / 'answer.txt').write_text('altered')
            with self.assertRaises(ValueError):
                scm.verify(root)

    def test_duplicate_schedule_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            shutil.copytree(ROOT / 'experiment', root / 'experiment')
            data = json.loads((root / 'experiment/trials.json').read_text())
            data[-1] = data[0]
            (root / 'experiment/trials.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                scm.trials(root)


class DockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = json.loads((ROOT / 'experiment/tasks.json').read_text())
        cls.image = json.loads((ROOT / 'experiment/protocol.json').read_text())['docker_image']

    def check_code(self, task, code, expected):
        status, _, _ = grading.evaluate(task, code, self.image)
        self.assertEqual(status, expected)

    def test_references(self):
        for task in self.tasks:
            with self.subTest(task=task['id']):
                self.check_code(task, task['reference'], 'pass')

    def test_mutants(self):
        mutants = [
            (0, 'def deduplicate(values): return sorted(set(values))'),
            (0, 'def deduplicate(values): return tuple(dict.fromkeys(values))'),
            (1, self.tasks[1]['reference'].replace('return out', 'return [tuple(x) for x in out]')),
            (0, 'def deduplicate(values): return values'),
            (0, 'def deduplicate(values):\n values[:] = list(dict.fromkeys(values))\n return values[:]'),
            (1, self.tasks[1]['reference'].replace('a <=', 'a <')),
            (1, self.tasks[1]['reference'].replace('sorted(intervals)', 'intervals')),
            (1, 'def merge_intervals(intervals):\n intervals.sort()\n return intervals'),
            (2, self.tasks[2]['reference'].replace('text.lower()', 'text')),
            (2, self.tasks[2]['reference'].replace('[a-z]+', r'\w+')),
            (0, 'def deduplicate(values): return [True if x == 1 else x for x in dict.fromkeys(values)]'),
        ]
        for i, code in mutants:
            with self.subTest(code=code):
                self.check_code(self.tasks[i], code, 'fail')

    def test_forged_results_and_exit_codes(self):
        task = self.tasks[0]
        forged = {'results': [{'actual': grading.typed(expected), 'input_after': grading.typed(argument),
                               'same_object': False} for argument, expected in task['cases']]}
        self.check_code(task, 'print(' + repr(json.dumps(forged)) + ')\nraise SystemExit(0)', 'runtime_error')

    def test_exit_codes_remain_candidate_failures(self):
        for code in ('raise SystemExit(125)', 'import os\nos._exit(125)'):
            with self.subTest(code=code):
                self.check_code(self.tasks[0], code, 'runtime_error')

    def test_unavailable_image_is_infrastructure_error(self):
        status, _, _ = grading.evaluate(self.tasks[0], self.tasks[0]['reference'], 'python@sha256:' + '0' * 64)
        self.assertEqual(status, 'infrastructure_error')

    def test_named_builtin_subclass_rejected(self):
        self.check_code(self.tasks[0], 'import builtins\nclass int(builtins.int): pass\ndef deduplicate(values): return [int(x) for x in dict.fromkeys(values)]', 'runtime_error')

    def test_errors_and_isolation(self):
        task = self.tasks[0]
        self.check_code(task, 'this is not python!', 'syntax_error')
        self.check_code(task, 'print(\'{"status":"pass"}\')\nraise SystemExit', 'runtime_error')
        self.check_code(task, 'while True: pass', 'timeout')
        self.check_code(task, 'print("x" * 200000)', 'output_limit')
        self.check_code(task, 'open("/tmp/denied", "w").write("x")', 'runtime_error')
        self.check_code(task, 'import socket\nsocket.create_connection(("1.1.1.1", 53), 1)', 'runtime_error')
        names = subprocess.check_output(['docker', 'ps', '-a', '--filter', 'name=scm-', '--format', '{{.Names}}'], text=True)
        self.assertEqual(names.strip(), '')
