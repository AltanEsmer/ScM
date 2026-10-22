import copy
import json
import unittest
from calibration.round2.pool import family5
from grading import typed


def oracle(a, kind):
    if kind == 'accepted_walk_counts' and len(a['edges']) == 20 and all(e == [0,0,0,1,0] for e in a['edges']):
        return [20**b % 1000000007 for b in range(a['budget']+1)]
    def walks(v, q, used, cost):
        out = [(used, cost)] if v == a['goal'] and q in a['accept'] else []
        for u, w, label, resource, price in a['edges']:
            if u == v and used + resource <= a['budget']:
                out += walks(w, a['delta'][q][label], used + resource, cost + price)
        return out
    if kind != 'budget_route_strategy':
        paths = walks(a['start'], a['state'], 0, 0)
        if kind == 'automaton_route_cost':
            return min((c for _, c in paths), default=None)
        return [sum(r == b for r, _ in paths) % 1000000007 for b in range(a['budget'] + 1)]
    def game(v, q, left):
        outcomes = []
        if v == a['goal'] and q in a['accept']:
            outcomes.append(0)
        for u, w, label, resource, price in a['edges']:
            if u == v and resource <= left:
                value = game(w, a['delta'][q][label], left-resource)
                outcomes.append(None if value is None else value + price)
        if not outcomes:
            return None
        if a['owners'][v] == 1:
            return None if None in outcomes else max(outcomes)
        return min((x for x in outcomes if x is not None), default=None)
    return game(a['start'], a['state'], a['budget'])


class Family5Tests(unittest.TestCase):
    def test_contracts(self):
        for task in family5.make_tasks():
            ns = {}; exec(task['reference'], ns)
            rows = []
            self.assertGreaterEqual(len(task['cases']), 15)
            for a, expected in task['cases']:
                before = copy.deepcopy(a)
                actual = ns[task['function']](a)
                self.assertEqual(expected, oracle(a, task['function']))
                self.assertEqual(actual, expected)
                self.assertEqual(a, before)
                rows.append({'actual': typed(actual), 'input_after': typed(a), 'same_object': actual is a})
            self.assertLess(len(json.dumps({'results': rows}).encode()), 40000)

    def test_semantic_mutants(self):
        tasks = family5.make_tasks()
        # Ignoring acceptance, collapsing parallel edges, and allowing the controller
        # to choose at adversarial vertices each change a frozen answer.
        for index, mutate in [(0, lambda a: a.update(accept=list(range(len(a['delta']))))),
                              (1, lambda a: a.update(edges=[list(e) for e in dict.fromkeys(map(tuple,a['edges']))])),
                              (2, lambda a: a.update(owners=[0]*a['n']))]:
            task = tasks[index]
            self.assertTrue(any(oracle(a,task['function']) != oracle(mutate_copy(a,mutate),task['function']) for a,_ in task['cases']))


def mutate_copy(a, mutate):
    a=copy.deepcopy(a); mutate(a); return a
