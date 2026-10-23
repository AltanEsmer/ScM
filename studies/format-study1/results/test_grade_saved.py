"""Synthetic collection gates; no saved model answers or Docker are accessed."""
import json
from pathlib import Path
import tempfile
import unittest
from grade_saved import closed_collection, create_json, sha_bytes


class CollectionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'isolation').mkdir()
        create_json(self.root / 'isolation/offline-evidence.json', {'image_id': 'synthetic-image'})
        (self.root / 'grader.py').write_text('synthetic grader')
        self.trials = [{'trial_id': f'trial-{i}', 'task_id': 'task', 'variant': 'A',
                        'repetition': 1, 'prompt': 'prompt.txt'} for i in range(72)]
        create_json(self.root / 'trials.json', self.trials)
        create_json(self.root / 'manifest.json', {'status': 'FROZEN_NOT_RUN', 'sha256': {'prompt.txt': 'prompt-hash'}})
        self.freeze = sha_bytes((self.root / 'manifest.json').read_bytes())
        for trial in self.trials:
            shared = {'trial_id': trial['trial_id'], 'freeze_sha256': self.freeze,
                      'prompt_sha256': 'prompt-hash', 'requested_model': 'gpt-6.1-sol',
                      'effort': 'medium', 'image_id': 'synthetic-image', 'source_sha256': {}}
            folder = self.root / 'runs' / trial['trial_id']
            create_json(folder / 'dispatch.json', {**shared, 'status': 'attempted_no_retry'})
            create_json(folder / 'result.json', {**shared, 'status': 'generated', 'answer': 'print(42)\n',
                        'reported_model': 'gpt-6.1-sol', 'tools': [], 'thread_id': trial['trial_id'],
                        'completed_at_utc': '2026-10-23T00:00:00+00:00'})

    def change(self, field, value):
        path = self.root / 'runs/trial-0/result.json'
        result = json.loads(path.read_text())
        result[field] = value
        path.write_text(json.dumps(result))

    def test_complete_collection_binds_exact_saved_text(self):
        verified = []
        rows = closed_collection(self.root, lambda root: verified.append(root))
        self.assertEqual(verified, [self.root])
        self.assertEqual(len(rows), 72)
        self.assertEqual(rows[0].binding['answer_sha256'], sha_bytes(b'print(42)\n'))

    def test_missing_record_blocks_before_loading_answers(self):
        (self.root / 'runs/trial-71/result.json').unlink()
        (self.root / 'runs/trial-0/result.json').write_text('unreadable')
        with self.assertRaisesRegex(ValueError, 'not closed'):
            closed_collection(self.root, lambda root: None)

    def test_model_effort_freeze_and_tools_mismatches_block(self):
        for field, bad, original in [('reported_model', 'other', 'gpt-6.1-sol'),
                                     ('effort', 'low', 'medium'),
                                     ('freeze_sha256', 'changed', self.freeze),
                                     ('tools', ['shell'], [])]:
            with self.subTest(field=field):
                self.change(field, bad)
                with self.assertRaises(ValueError):
                    closed_collection(self.root, lambda root: None)
                self.change(field, original)

    def test_failed_generation_blocks(self):
        self.change('status', 'interrupted_or_failed_do_not_retry')
        with self.assertRaises(ValueError):
            closed_collection(self.root, lambda root: None)

    def test_thread_reuse_blocks(self):
        self.change('thread_id', 'trial-1')
        with self.assertRaisesRegex(ValueError, 'thread reused'):
            closed_collection(self.root, lambda root: None)

    def test_create_only_records(self):
        path = self.root / 'once.json'
        create_json(path, {'status': 'attempted'})
        with self.assertRaises(FileExistsError):
            create_json(path, {'status': 'retry'})


if __name__ == '__main__':
    unittest.main()
