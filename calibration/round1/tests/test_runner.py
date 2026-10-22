import importlib.util
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'run.py'


class RunnerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('calibration_runner', SOURCE)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.root = Path(self.temp.name) / 'calibration/round1'
        self.root.mkdir(parents=True)
        (self.root.parent.parent / 'grading.py').write_text('frozen grader\n')
        for name in ('run.py', 'build_cases.py', 'pool_algorithms.py', 'pool_semantics.py'):
            (self.root / name).write_text('frozen input\n')
        (self.root / 'prompts').mkdir()
        self.tasks = ['task_one', 'task_two', 'task_three', 'task_four', 'task_five', 'task_six']
        rows = []
        for task in self.tasks:
            for variant in ['B0']:
                prompt = f'prompts/{task}_{variant}.txt'
                (self.root / prompt).write_text(f'Exact {task} {variant}\n')
                rows.extend(dict(trial_id=f'{task}_{variant}_{repeat:02d}', task=task,
                                 variant=variant, repeat=repeat, prompt_file=prompt)
                            for repeat in range(1, 4))
        self.write('trials.json', rows)
        self.write('tasks.json', [dict(id=task, function=task, cases=[[[], []]]) for task in self.tasks])
        self.write('protocol.json', dict(requested_model='gpt-6.1-sol', requested_reasoning='medium',
                                         docker_image='python@sha256:' + 'a' * 64, fork_turns='none',
                                         collection_backend='collaboration.spawn_agent', timeout_seconds=4,
                                         tasks=self.tasks, variants=['B0'], repetitions=3, selection_rule='Select one or two passes among three evaluated trials'))

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def collect(self, ordinal, session):
        self.runner.start(self.root, [ordinal])
        answer = self.root / 'candidate.txt'
        answer.write_bytes(b'raw\r\nanswer\x00\n')
        self.runner.record(self.root, ordinal, session, answer)

    def test_freeze_required_and_inputs_cannot_change(self):
        with self.assertRaises((ValueError, OSError)):
            self.runner.start(self.root, [1])
        self.runner.freeze(self.root)
        self.assertEqual(len(self.runner.verify(self.root)), 18)
        (self.root.parent.parent / 'grading.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.runner.verify(self.root)

    def test_freeze_rejects_invalid_schedule_settings_and_missing_prompt(self):
        path = self.root / 'trials.json'
        schedule = json.loads(path.read_text())
        path.write_text(json.dumps(schedule[:-1] + [schedule[0]]))
        with self.assertRaisesRegex(ValueError, '18 Cartesian'):
            self.runner.freeze(self.root)
        path.write_text(json.dumps(schedule))
        protocol = json.loads((self.root / 'protocol.json').read_text())
        self.write('protocol.json', dict(protocol, requested_reasoning='low'))
        with self.assertRaisesRegex(ValueError, 'medium'):
            self.runner.freeze(self.root)
        self.write('protocol.json', protocol)
        (self.root / 'prompts/task_one_B0.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'prompt'):
            self.runner.freeze(self.root)

    def test_freeze_rejects_invalid_timeout_and_protocol_dimensions(self):
        protocol = json.loads((self.root / 'protocol.json').read_text())
        for timeout in (0, -1, True, float('inf'), float('nan')):
            self.write('protocol.json', dict(protocol, timeout_seconds=timeout))
            with self.assertRaisesRegex(ValueError, 'timeout'):
                self.runner.freeze(self.root)
        for change in ({'tasks': self.tasks[:2]}, {'variants': ['A', 'B']}, {'repetitions': 4}):
            self.write('protocol.json', dict(protocol, **change))
            with self.assertRaisesRegex(ValueError, 'dimensions'):
                self.runner.freeze(self.root)

    def test_freeze_is_idempotent_but_cannot_follow_capture(self):
        self.runner.freeze(self.root)
        frozen = (self.root / 'manifest.json').read_bytes()
        self.runner.freeze(self.root)
        self.assertEqual((self.root / 'manifest.json').read_bytes(), frozen)
        self.runner.start(self.root, [1])
        (self.root / 'manifest.json').unlink()
        with self.assertRaisesRegex(ValueError, 'precede'):
            self.runner.freeze(self.root)

    def test_attach_must_match_recorded_session(self):
        self.runner.freeze(self.root)
        self.runner.start(self.root, [1])
        self.runner.attach(self.root, 1, 'native-session')
        answer = self.root / 'candidate.txt'
        answer.write_bytes(b'answer')
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.runner.record(self.root, 1, 'different-session', answer)
        self.runner.record(self.root, 1, 'native-session', answer)
        self.assertEqual(self.runner.verify(self.root)[0].session_id, 'native-session')
        self.assertTrue((self.root / 'dispatch/task_one_B0_01/dispatch.json').is_file())
        self.assertTrue((self.root / 'dispatch/task_one_B0_01/session.json').is_file())

    def test_record_preserves_bytes_and_rejects_overwrite(self):
        self.runner.freeze(self.root)
        self.collect(1, 'session-1')
        directory = self.root / 'records/task_one_B0_01'
        self.assertEqual((directory / 'answer.txt').read_bytes(), b'raw\r\nanswer\x00\n')
        self.assertEqual(self.runner.verify(self.root)[0].status, 'collected')
        with self.assertRaises((ValueError, FileExistsError)):
            self.runner.record(self.root, 1, 'session-1', self.root / 'candidate.txt')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.runner.verify(self.root, True)

    def test_started_trial_is_interrupted_and_ordinals_are_bounded(self):
        self.runner.freeze(self.root)
        for ordinal in (0, -1, 19):
            with self.assertRaises(ValueError):
                self.runner.start(self.root, [ordinal])
        self.runner.start(self.root, [2])
        self.runner.attach(self.root, 2, 'native-session')
        records = self.runner.verify(self.root)
        self.assertEqual((records[0].status, records[1].status), ('missing', 'interrupted'))
        with self.assertRaises((ValueError, FileExistsError)):
            self.runner.start(self.root, [2])

    def test_evidence_and_unknown_records_are_rejected(self):
        self.runner.freeze(self.root)
        self.collect(1, 'session-1')
        evidence_path = self.root / 'records/task_one_B0_01/evidence.json'
        evidence = json.loads(evidence_path.read_text())
        evidence['completion_observed_utc'] = '2000-01-01T00:00:00+00:00'
        evidence_path.write_text(json.dumps(evidence))
        with self.assertRaises(ValueError):
            self.runner.verify(self.root)
        evidence['completion_observed_utc'] = self.runner.now()
        evidence_path.write_text(json.dumps(evidence))
        (self.root / 'records/unknown').mkdir()
        with self.assertRaisesRegex(ValueError, 'unknown'):
            self.runner.verify(self.root)

    def test_duplicate_sessions_are_rejected(self):
        self.runner.freeze(self.root)
        self.collect(1, 'same-session')
        self.runner.start(self.root, [2])
        with self.assertRaisesRegex(ValueError, 'session'):
            self.runner.record(self.root, 2, 'same-session', self.root / 'candidate.txt')

    def test_infrastructure_stops_grading_and_report_detects_stale_answers(self):
        self.runner.freeze(self.root)
        self.collect(1, 'session-1')
        self.collect(2, 'session-2')
        with patch.object(self.runner.grading, 'evaluate', return_value=('infrastructure_error', 0, 'offline')) as evaluate:
            with self.assertRaisesRegex(RuntimeError, 'infrastructure'):
                self.runner.grade(self.root)
            self.assertEqual(evaluate.call_count, 1)
            self.assertEqual(evaluate.call_args.kwargs, {'timeout': 4})
        import csv
        with (self.root / 'results/trials.csv').open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([r['status'] for r in rows[:3]], ['infrastructure_error', 'not_evaluated', 'missing'])
        report = (self.root / 'results/report.md').read_text()
        self.assertIn('| task_one | B0 | 2 | 0 | 0 | 0 | 1 | 1 | 1 | incomplete |', report)
        rows[0]['response_sha256'] = 'stale'
        with (self.root / 'results/trials.csv').open('w') as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.runner.report(self.root)

    def test_report_classifies_only_three_evaluated_trials(self):
        self.runner.freeze(self.root)
        for ordinal in range(1, 16):
            self.collect(ordinal, f'session-{ordinal}')
        outcomes = (['pass'] * 3 + ['fail'] * 3 + ['pass', 'fail', 'fail']
                    + ['pass', 'pass', 'timeout'] + ['pass', 'runtime_error', 'infrastructure_error'])
        results = [(status, 1 if status == 'pass' else 0, '') for status in outcomes]
        with patch.object(self.runner.grading, 'evaluate', side_effect=results):
            with self.assertRaises(RuntimeError):
                self.runner.grade(self.root)
        report = (self.root / 'results/report.md').read_text()
        for task, classification in zip(self.tasks, ['ceiling', 'floor', 'eligible', 'eligible', 'incomplete', 'incomplete']):
            row = next(line for line in report.splitlines() if line.startswith(f'| {task} |'))
            self.assertTrue(row.endswith(f'| {classification} |'), row)
        self.assertIn('does not compare prompt variants', report)

    def test_report_rejects_forged_pass_counts(self):
        self.runner.freeze(self.root)
        self.collect(1, 'session-1')
        with patch.object(self.runner.grading, 'evaluate', return_value=('pass', 1, '')):
            self.runner.grade(self.root)
        import csv
        path = self.root / 'results/trials.csv'
        with path.open() as file:
            rows = list(csv.DictReader(file))
        for passed, total in [('0', '1'), ('1.0', '1'), ('1', '2'), ('2', '1')]:
            rows[0].update(passed=passed, total=total)
            with path.open('w') as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, 'counts'):
                self.runner.report(self.root)

    def test_freeze_hashes_pool_modules_and_requires_selection_rule(self):
        protocol = json.loads((self.root / 'protocol.json').read_text())
        self.write('protocol.json', dict(protocol, selection_rule=''))
        with self.assertRaisesRegex(ValueError, 'selection_rule'):
            self.runner.freeze(self.root)
        self.write('protocol.json', protocol)
        self.runner.freeze(self.root)
        hashes = json.loads((self.root / 'manifest.json').read_text())['hashes']
        self.assertIn('pool_algorithms.py', hashes)
        self.assertIn('pool_semantics.py', hashes)
        self.assertNotIn('equivalence.md', hashes)
        (self.root / 'pool_semantics.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.runner.verify(self.root)

    def test_six_task_ids_must_be_unique_and_match_functions(self):
        protocol = json.loads((self.root / 'protocol.json').read_text())
        self.write('protocol.json', dict(protocol, tasks=[self.tasks[0]] * 6))
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            self.runner.freeze(self.root)
        self.write('protocol.json', protocol)
        tasks = json.loads((self.root / 'tasks.json').read_text())
        tasks[0]['function'] = 'different_function'
        self.write('tasks.json', tasks)
        with self.assertRaisesRegex(ValueError, 'function'):
            self.runner.freeze(self.root)


if __name__ == '__main__':
    unittest.main()
