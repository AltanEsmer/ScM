"""Behavioral contracts; exhaustive oracles deliberately differ from references."""
import importlib.util
import itertools
import json
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / 'pool_algorithms.py'
ROOT_GRADING = PATH.parents[2] / 'grading.py'


def load():
    spec = importlib.util.spec_from_file_location('pool_algorithms', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AlgorithmTests(unittest.TestCase):
    def test_task_contracts(self):
        tasks = load().make_tasks()
        self.assertEqual({t['id'] for t in tasks}, {'damerau_distance', 'min_cost_circulation', 'minimum_arborescence'})
        for task in tasks:
            self.assertTrue(25 <= len(task['cases']) <= 40)
            self.assertLess(len(json.dumps(task['cases']).encode()), 64000)
            namespace = {}
            exec(task['reference'], namespace)
            for argument, expected in task['cases']:
                before = json.dumps(argument, sort_keys=True)
                self.assertEqual(namespace[task['function']](argument), expected, (task['id'], argument))
                self.assertEqual(json.dumps(argument, sort_keys=True), before)

    def test_full_typed_observation_budget(self):
        # Match the root runner's full observation, including typed inputs.
        # Raw case JSON substantially understates its serialized size.
        spec = importlib.util.spec_from_file_location('rootgrading', ROOT_GRADING)
        rootgrading = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rootgrading)
        for task in load().make_tasks():
            observation = {'results': [
                {'actual': rootgrading.typed(expected),
                 'input_after': rootgrading.typed(arg), 'same_object': False}
                for arg, expected in task['cases']]}
            size = len(json.dumps(observation).encode('utf-8'))
            self.assertLessEqual(size, 48000, (task['id'], size))

    def test_unrestricted_transpositions(self):
        m = load()
        self.assertEqual(m.distance({'a': 'CA', 'b': 'ABC'}), 2)
        self.assertEqual(m.distance({'a': 'ABC', 'b': 'CA'}), 2)

    def test_exhaustive_flow_oracle(self):
        m = load()
        for costs in itertools.product((-2, 0, 3), repeat=3):
            arg = {'n': 2, 'arcs': [[0, 1, 0, 2, costs[0]], [1, 0, 1, 2, costs[1]], [0, 0, 0, 2, costs[2]]]}
            self.assertEqual(m.circulation(arg), m.brute_flow(arg))

    def test_exhaustive_tree_oracle(self):
        m = load()
        for costs in itertools.product((-3, 1), repeat=6):
            edges = [[u, v, costs[i]] for i, (u, v) in enumerate(itertools.permutations(range(3), 2))]
            arg = {'n': 3, 'root': 0, 'edges': edges}
            self.assertEqual(m.arborescence(arg), m.brute_tree(arg))

    def test_dataset_kills_common_wrong_contracts(self):
        tasks = {t['id']: t for t in load().make_tasks()}

        def osa(arg):
            a, b = arg['a'], arg['b']
            d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
            for i in range(len(a) + 1):
                d[i][0] = i
            for j in range(len(b) + 1):
                d[0][j] = j
            for i in range(1, len(a) + 1):
                for j in range(1, len(b) + 1):
                    d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (a[i-1] != b[j-1]))
                    if i > 1 and j > 1 and a[i-1] == b[j-2] and a[i-2] == b[j-1]:
                        d[i][j] = min(d[i][j], d[i-2][j-2] + 1)
            return d[-1][-1]

        def greedy_incoming(arg):
            total = 0
            for v in range(arg['n']):
                if v == arg['root']:
                    continue
                costs = [c for u, w, c in arg['edges'] if w == v and u != v]
                if not costs:
                    return None
                total += min(costs)
            return total

        def ignores_lower_bounds(arg):
            relaxed = {'n': arg['n'], 'arcs': [[u, v, 0, hi, c] for u, v, lo, hi, c in arg['arcs']]}
            return load().circulation(relaxed)

        mutants = [('damerau_distance', osa),
                   ('minimum_arborescence', greedy_incoming),
                   ('min_cost_circulation', ignores_lower_bounds),
                   ('min_cost_circulation', lambda arg: 0)]
        for task_id, mutant in mutants:
            self.assertTrue(any(mutant(arg) != expected for arg, expected in tasks[task_id]['cases']), task_id)

    def test_documented_bounds(self):
        for task in load().make_tasks():
            for arg, _ in task['cases']:
                if task['id'] == 'damerau_distance':
                    self.assertLessEqual(max(len(arg['a']), len(arg['b'])), 180)
                elif task['id'] == 'min_cost_circulation':
                    self.assertTrue(1 <= arg['n'] <= 48)
                    self.assertLessEqual(len(arg['arcs']), 240)
                    for u, v, lo, hi, cost in arg['arcs']:
                        self.assertTrue(0 <= u < arg['n'] and 0 <= v < arg['n'])
                        self.assertTrue(0 <= lo <= hi <= 1000000 and -100 <= cost <= 100)
                else:
                    self.assertTrue(1 <= arg['n'] <= 100 and 0 <= arg['root'] < arg['n'])
                    self.assertLessEqual(len(arg['edges']), 500)
                    for u, v, cost in arg['edges']:
                        self.assertTrue(0 <= u < arg['n'] and 0 <= v < arg['n'])
                        self.assertTrue(-1000000 <= cost <= 1000000)

    def test_small_edit_oracle(self):
        m = load()
        words = ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']
        for a, b in itertools.product(words, repeat=2):
            self.assertEqual(m.distance({'a': a, 'b': b}), m.brute_distance(a, b))


if __name__ == '__main__':
    unittest.main()
