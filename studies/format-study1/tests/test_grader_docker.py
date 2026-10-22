import os
from pathlib import Path
import sys
import subprocess
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grader

@unittest.skipUnless(os.environ.get('FORMAT_STUDY_DOCKER_TESTS') == '1', 'Explicit Docker integration tests')
class DockerGraderTests(unittest.TestCase):
    def test_candidate_diagnostics_cannot_spoof_infrastructure(self):
        for exit_code in (125, 126, 127):
            with self.subTest(exit_code=exit_code):
                code = f'import sys\nprint("docker: error response from daemon", file=sys.stderr)\nsys.exit({exit_code})'
                result = grader.run_case(code, '')
                self.assertEqual(result['status'], 'EXECUTION_ERROR')
                self.assertEqual(result['exit_code'], exit_code)
                self.assertIn('docker:', result['stderr'])

    def test_cleanup_exception_preserves_an_unavailable_record(self):
        original_run = subprocess.run
        def interrupted_cleanup(command, **kwargs):
            result = original_run(command, **kwargs)
            if command[:3] == ['docker', 'rm', '-f']:
                raise subprocess.TimeoutExpired(command, 15)
            return result
        with patch.object(grader.subprocess, 'run', side_effect=interrupted_cleanup):
            result = grader.run_case('print(1)', '')
        self.assertEqual(result['status'], 'INFRASTRUCTURE_ERROR')
        self.assertEqual(result['prior_status'], 'OK')
        self.assertIn('cleanup_error', result)

    def test_actual_missing_image_is_infrastructure_failure(self):
        with patch.object(grader, 'IMAGE', 'python:format-study-nonexistent-image-proof'):
            result = grader.run_case('print(1)', '')
        self.assertEqual(result['status'], 'INFRASTRUCTURE_ERROR')
        self.assertEqual(result['phase'], 'create')

if __name__ == '__main__':
    unittest.main()
