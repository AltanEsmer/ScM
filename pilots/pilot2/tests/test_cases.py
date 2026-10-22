import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot2_cases', ROOT / 'build_cases.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class CaseTests(unittest.TestCase):
    def test_literal_contracts(self):
        for task, cases in build.LITERALS.items():
            for argument, expected in cases:
                with self.subTest(task=task, argument=argument):
                    self.assertEqual(build.ORACLES[task](argument), expected)

    def test_references_and_no_mutation(self):
        for task in build.make_tasks():
            namespace = {}
            exec(task['reference'], namespace)
            for argument, expected in task['cases']:
                before = copy.deepcopy(argument)
                with self.subTest(task=task['id'], argument=argument):
                    self.assertEqual(namespace[task['function']](argument), expected)
                    self.assertEqual(argument, before)

    def test_generated_artifact_is_current(self):
        self.assertEqual(json.loads((ROOT / 'tasks.json').read_text()), build.make_tasks())

    def test_prompt_inventory_and_common_output_instruction(self):
        paths = list((ROOT / 'prompts').glob('*.txt'))
        self.assertEqual({path.name for path in paths},
                         {f'{task}_{variant}.txt' for task in build.ORACLES for variant in 'ABC'})
        endings = {path.read_text().split('\n\n')[-1] for path in paths}
        self.assertEqual(len(endings), 1)
        self.assertIn('Python 3.12', next(iter(endings)))
        for task in build.ORACLES:
            self.assertEqual((ROOT / 'prompts' / f'{task}_A.txt').read_text().split('\n\n')[0],
                             build.SPECS[task])

    def test_semantic_mutants_are_rejected(self):
        changes = {
            'select_jobs': [
                ('data[j][1] <= start or end <= data[j][0]',
                 'data[j][1] < start or end < data[j][0]'),
                ('len(state[1])', '-len(state[1])'),
                ('len(state[1]), state[1]', 'len(state[1]), tuple(-i for i in state[1])'),
            ],
            'match_path': [
                ("r'[\\s\\S]*'", "'[^/]*'"),
                ("r'[\\s\\S]*'", "'.*'"),
                ("'[^/]*'", "r'[\\s\\S]*'"),
                ("'[^/]'", "r'[\\s\\S]'"),
                ('re.fullmatch', 're.search'),
                ("j - i >= 2", "j - i == 2"),
            ],
            'best_itinerary': [
                ('departure < now', 'departure <= now'),
                ('arrival, len(route), route', 'len(route), arrival, route'),
                ('arrival, len(route), route', 'arrival, -len(route), route'),
                ('arrival, len(route), route', 'arrival, len(route), tuple(-i for i in route)'),
                ('else list(best[2])', 'else sorted(best[2])'),
            ],
        }
        cases = build.make_case_sets()
        for name, mutations in changes.items():
            for old, new in mutations:
                source = build.REFERENCES[name]
                self.assertIn(old, source)
                namespace = {}
                exec(source.replace(old, new), namespace)
                with self.subTest(task=name, mutation=(old, new)):
                    self.assertTrue(any(namespace[name](copy.deepcopy(arg)) != expected
                                        for arg, expected in cases[name]))

        def earliest_prefix(data):
            if data['start'] == data['goal']:
                return []
            arrivals = {data['start']: (data['time'], [])}
            for i in sorted(range(len(data['flights'])), key=lambda i: data['flights'][i][2]):
                origin, destination, departure, arrival = data['flights'][i]
                if origin in arrivals and arrivals[origin][0] <= departure:
                    candidate = (arrival, arrivals[origin][1] + [i])
                    if destination not in arrivals or candidate < arrivals[destination]:
                        arrivals[destination] = candidate
            return arrivals.get(data['goal'], (None, None))[1]

        arg, expected = build.LITERALS['best_itinerary'][6]
        self.assertNotEqual(earliest_prefix(arg), expected)

    def test_mutants_are_rejected(self):
        mutants = {
            'select_jobs': [lambda data: [], lambda data: list(range(len(data))),
                            lambda data: sorted(build.jobs_oracle(data), reverse=True)],
            'match_path': [lambda data: True, lambda data: False,
                           lambda data: __import__('fnmatch').fnmatchcase(data['text'], data['pattern'])],
            'best_itinerary': [lambda data: None, lambda data: [],
                               lambda data: next(([i] for i, f in enumerate(data['flights'])
                                   if f[0] == data['start'] and f[1] == data['goal'] and f[2] >= data['time']), None)],
        }
        for name, candidates in mutants.items():
            for mutant in candidates:
                self.assertTrue(any(mutant(copy.deepcopy(arg)) != expected
                                    for arg, expected in build.make_case_sets()[name]), name)


if __name__ == '__main__':
    unittest.main()
