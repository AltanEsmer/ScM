import json
import pathlib
import unittest

from validate_selected import validate_medium
from validate_hard import validate as validate_hard


POSITIVE = {
    760: ('3\n1 1 1\n', '1\n'),
    402: ('2 1\n0 0\n1 2\n', '1\n'),
    472: ('1\n0\n0\n0\n0\n', '2\n'),
    74: ('1\nadd 1\nremove\n', '0\n'),
    250: ('1\n1\n', '1\n'),
    320: ('1\n0\n', '1\n'),
    152: ('1 1\n1 1 1\n', '1\n'),
    339: ('1\n1\n', '1\n'),
    466: ('1 1\n1\n2 1 1\n', '1\n'),
    581: ('1\n2\n1 2\n1 1\n', '1\n'),
    778: ('1\n0\n0\n1\n1 1\n', '0\n'),
    979: ('1\n1 1 1\n0\n1 1\n', '1\n'),
    799: ('1 0\n1\n', '1 0\n'),
}
NEGATIVE = {
    760: '2\n1 1\n',
    402: '2 1\n0 0\n1 1\n',
    472: '2\n00\n00\n00\n00\n00\n00\n00\n00\n',
    74: '1\nremove\nadd 1\n',
    250: '1\n-1\n',
    320: '1\n-1\n',
    152: '1 1\n0 1 1\n',
    339: '2\n1 1\n',
    466: '1 1\n1\n0 1 1\n',
    581: '1\n1\n1\n',
    778: '1\n0\n0\n1\n2 1\n',
    979: '1\n1 1 1\n00\n1 1\n',
    799: '1 0\n1000000001\n',
}
MEDIUM = {760, 402, 472, 74, 250, 320}


def validate(row, text, output):
    (validate_medium if row in MEDIUM else validate_hard)(row, text, output)


class StatementValidatorsTest(unittest.TestCase):
    def test_all_contracts_accept_valid_minimal_examples(self):
        for row, (text, output) in POSITIVE.items():
            with self.subTest(row=row):
                validate(row, text, output)

    def test_all_contracts_reject_specific_domain_violations(self):
        for row, text in NEGATIVE.items():
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    validate(row, text, POSITIVE[row][1])

    def test_all_contracts_reject_undeclared_input_and_output(self):
        for row, (text, output) in POSITIVE.items():
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    validate(row, text + ' 0', output)
                with self.assertRaises(ValueError):
                    validate(row, text, output + ' 0')

    def test_curated_cases_are_exact_original_subset(self):
        root = pathlib.Path(__file__).resolve().parent
        selection = json.loads((root / 'selection.json').read_text())
        total = excluded_total = 0
        for item in selection['selected']:
            folder = root / 'selected' / f"taco-test-{item['row_index']:04d}"
            original = json.loads((folder / 'task.json').read_text())['input_output']
            curated = json.loads((folder / 'evaluation-cases.json').read_text())
            indices = curated['case_indices']
            excluded = {entry['case_index'] for entry in curated['excluded']}
            self.assertEqual(indices, sorted(set(indices)))
            self.assertGreaterEqual(len(indices), 10)
            self.assertFalse(set(indices) & excluded)
            self.assertEqual(set(indices) | excluded, set(range(len(original['inputs']))))
            for index, text, output in zip(indices, curated['inputs'], curated['outputs']):
                self.assertEqual(text, original['inputs'][index])
                self.assertEqual(output, original['outputs'][index])
                validate(item['row_index'], text, output)
            total += len(indices)
            excluded_total += len(excluded)
        self.assertEqual(total, 2178)
        self.assertEqual(excluded_total, 161)


if __name__ == '__main__':
    unittest.main()
