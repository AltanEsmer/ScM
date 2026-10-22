import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('hard_validation', Path(__file__).resolve().parents[1] / 'source/validate_hard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = module.validate

class HardValidationTests(unittest.TestCase):
    def test_statement_conforming_cases(self):
        samples = [(152, '1 1\n1 1 5', '5'), (339, '3\n1 2 3', '33'),
                   (466, '2 2\n1 2\n1 2 3\n2 2 1', '1'),
                   (581, '1\n2\n1 2\n3 5', '5'),
                   (778, '1\n01\n10\n2\n1 2\n2 1', '01'),
                   (979, '1\n3 1 1\n010\n1 3', '5'), (799, '2 6\n-5 9', '1 2 0')]
        for row, stdin, expected in samples:
            with self.subTest(row=row):
                validate(row, stdin, expected)

    def test_rejects_statement_domain_or_output_shape_violations(self):
        defects = [(152, '1 1\n1 2 5', '5'), (339, '3\n1 1 3', '50'),
                   (466, '2 1\n1 2\n2 3 1', '1'),
                   (581, '1\n3\n1 2\n2 1\n3 5 7', '12'),
                   (778, '1\n01\n10\n1\n1 3', '1'),
                   (979, '1\n3 1 1\n01\n1 3', '5'),
                   (979, '1\n3 1 1\n010\n1 3', '5 5'), (799, '2 6\n-5 9', '1 1 0')]
        for row, stdin, expected in defects:
            with self.subTest(row=row), self.assertRaises(ValueError):
                validate(row, stdin, expected)

if __name__ == '__main__':
    unittest.main()
