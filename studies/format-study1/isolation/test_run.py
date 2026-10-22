"""Fast checks for launch gates; the offline-proof command is the integration test."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LaunchGateTests(unittest.TestCase):
    def test_unvalidated_live_commands_exit_without_reading_credentials(self):
        launcher = Path(__file__).with_name('run.py')
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            auth = home / 'auth.json'
            auth.write_text('DO_NOT_READ_OR_MODIFY_AUTH_CANARY')
            for command in ['live-preflight', 'generate']:
                with self.subTest(command=command):
                    result = subprocess.run(
                        [sys.executable, str(launcher), command],
                        env={**os.environ, 'CODEX_HOME': directory},
                        text=True, capture_output=True, timeout=5,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn('LIVE_PREFLIGHT_PENDING', result.stderr)
                    self.assertNotIn('DO_NOT_READ_OR_MODIFY_AUTH_CANARY', result.stdout + result.stderr)
                    self.assertEqual(auth.read_text(), 'DO_NOT_READ_OR_MODIFY_AUTH_CANARY')
                    self.assertEqual(list(home.iterdir()), [auth])

class ImageBindingTests(unittest.TestCase):
    def test_stale_image_cannot_be_attested_with_current_source(self):
        import importlib.util
        import hashlib
        import json
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('image_binding_runner', Path(__file__).with_name('run.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = {name:hashlib.sha256((module.ROOT/name).read_bytes()).hexdigest()
                    for name in ['client.mjs', 'relay.mjs', 'live_transport.mjs']}
        with patch.object(module, 'docker') as fake:
            fake.return_value.stdout = json.dumps(expected)
            self.assertEqual(module.verify_image_sources('sha256:fixture'), expected)
            changed = dict(expected, **{'client.mjs':'stale'})
            fake.return_value.stdout = json.dumps(changed)
            with self.assertRaisesRegex(RuntimeError, 'IMAGE_SOURCE_MISMATCH'):
                module.verify_image_sources('sha256:fixture')


class FrozenDispatchTests(unittest.TestCase):
    def setUp(self):
        import importlib.util
        import hashlib
        import json
        from unittest.mock import patch
        self.json = json
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        study = Path(self.temp.name)
        self.study = study
        isolation = study/'isolation'
        isolation.mkdir()
        (study/'prompts').mkdir()
        (study/'prompts'/'A.txt').write_text('frozen prompt')
        trials=[{'trial_id':name,'prompt':'prompts/A.txt'} for name in ['first','second']]
        (study/'trials.json').write_text(json.dumps(trials))
        manifest={'status':'FROZEN_NOT_RUN','sha256':{
            name:hashlib.sha256((study/name).read_bytes()).hexdigest()
            for name in ['trials.json','prompts/A.txt']}}
        (study/'manifest.json').write_text(json.dumps(manifest))
        freeze=hashlib.sha256((study/'manifest.json').read_bytes()).hexdigest()
        self.canary=study.parent/(study.name+'-canary.json')
        self.addCleanup(lambda:self.canary.unlink(missing_ok=True))
        self.canary.write_text(json.dumps({'status':'live_canary_passed','freeze_sha256':freeze,
                                           'image_id':'sha256:fake','source_sha256':{'fake':'hash'}}))
        spec=importlib.util.spec_from_file_location('isolation_test_runner',Path(__file__).with_name('run.py'))
        self.module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.module.ROOT=isolation
        for name,value in [('docker',lambda *args,**kwargs:type('Result',(),{'stdout':'[{"Id":"sha256:fake"}]'})()),
                           ('verify_offline',lambda image:None),('source_hashes',lambda:{'fake':'hash'})]:
            patcher=patch.object(self.module,name,value);patcher.start();self.addCleanup(patcher.stop)
        self.live=patch.object(self.module,'run_live',return_value={'answer':'fixture'})
        self.mock_live=self.live.start();self.addCleanup(self.live.stop)

    def dispatch(self,trial):
        from unittest.mock import patch
        import io
        with patch.object(sys,'argv',['run.py','generate','--authorize-live','--canary',str(self.canary),'--trial-id',trial]),patch('sys.stdout',new_callable=io.StringIO):
            self.module.main()

    def test_schedule_reserves_before_dispatch_and_prevents_retry(self):
        with self.assertRaisesRegex(RuntimeError,'NOT_NEXT_SCHEDULED_TRIAL'):
            self.dispatch('second')
        self.mock_live.assert_not_called()
        def observed_dispatch(*args):
            self.assertTrue((self.study/'runs'/'first'/'dispatch.json').exists())
            return {'answer':'fixture'}
        self.mock_live.side_effect=observed_dispatch
        self.dispatch('first')
        with self.assertRaisesRegex(RuntimeError,'TRIAL_ALREADY_ATTEMPTED'):
            self.dispatch('first')
        self.assertEqual(self.mock_live.call_count,1)

    def test_failed_attempt_blocks_retry_and_following_trial(self):
        self.mock_live.side_effect=RuntimeError('synthetic provider failure')
        with self.assertRaises(RuntimeError):
            self.dispatch('first')
        with self.assertRaisesRegex(RuntimeError,'PREVIOUS_ATTEMPT_AMBIGUOUS_OR_FAILED'):
            self.dispatch('second')
        self.assertEqual(self.mock_live.call_count,1)

    def test_changed_frozen_prompt_blocks_before_dispatch(self):
        (self.study/'prompts'/'A.txt').write_text('modified')
        with self.assertRaisesRegex(RuntimeError,'FROZEN_ARTIFACT_CHANGED'):
            self.dispatch('first')
        self.mock_live.assert_not_called()


if __name__ == '__main__':
    unittest.main()
