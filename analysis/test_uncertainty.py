import json
import subprocess
import sys
import unittest
from pathlib import Path

from uncertainty import clopper_pearson


class IntervalTests(unittest.TestCase):
    def test_closed_form_edges(self):
        for n in (1, 3, 5, 50):
            self.assertAlmostEqual(clopper_pearson(0, n)[1], 1 - 0.025 ** (1 / n), places=12)
            self.assertEqual(clopper_pearson(0, n)[0], 0)
            self.assertAlmostEqual(clopper_pearson(n, n)[0], 0.025 ** (1 / n), places=12)
            self.assertEqual(clopper_pearson(n, n)[1], 1)

    def test_one_of_three_reference_values(self):
        low, high = clopper_pearson(1, 3)
        self.assertAlmostEqual(low, 0.0084037586596126, places=12)
        self.assertAlmostEqual(high, 0.9057006759497539, places=12)

    def test_complement_symmetry(self):
        for n in (3, 5, 20):
            for k in range(n + 1):
                low, high = clopper_pearson(k, n)
                other_low, other_high = clopper_pearson(n - k, n)
                self.assertAlmostEqual(low, 1 - other_high, places=12)
                self.assertAlmostEqual(high, 1 - other_low, places=12)

    def test_invalid_counts(self):
        for k, n in [(-1, 3), (4, 3), (0, 0), (0, -1), (1.0, 3), (1, 3.0), (True, 3), (0, False), ('1', 3)]:
            with self.subTest(k=k, n=n), self.assertRaises(ValueError):
                clopper_pearson(k, n)

    def test_cli_illustrations_and_assumptions(self):
        path = Path(__file__).with_name('uncertainty.py')
        result = subprocess.run([sys.executable, str(path)], check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual([(row['k'], row['n']) for row in data['illustrations']], [(0, 3), (1, 3), (2, 3), (3, 3), (5, 5)])
        self.assertIn('iid Bernoulli', data['assumptions'])
        self.assertIn('selection', data['limitations'])
        self.assertIn('90', data['limitations'])
