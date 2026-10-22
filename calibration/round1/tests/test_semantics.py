"""Independent semantic checks, output budget, and regressions."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('semantics', ROOT / 'calibration/round1/pool_semantics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('grading_semantics', ROOT / 'grading.py')
grading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grading)


def substitute(node, name, value):
    tag = node[0]
    if tag == 'var':
        return value if node[1] == name else node
    if tag in ('int', 'rec'):
        return node
    if tag == 'fn':
        return node if node[1] == name else ['fn', node[1], substitute(node[2], name, value)]
    if tag == 'let':
        return ['let', node[1], substitute(node[2], name, value), node[3] if node[1] == name else substitute(node[3], name, value)]
    if tag == 'letrec':
        bound, param, fnbody, body = node[1:]
        return ['letrec', bound, param, fnbody if name in (bound, param) else substitute(fnbody, name, value), body if name == bound else substitute(body, name, value)]
    return [tag] + [substitute(child, name, value) for child in node[1:]]


def substitution_eval(node):
    tag, *a = node
    if tag in ('int', 'fn', 'rec'):
        return node
    if tag in ('add', 'sub', 'mul'):
        x, y = substitution_eval(a[0])[1], substitution_eval(a[1])[1]
        return ['int', {'add': lambda: x + y, 'sub': lambda: x - y, 'mul': lambda: x * y}[tag]()]
    if tag == 'if0':
        return substitution_eval(a[1] if substitution_eval(a[0])[1] == 0 else a[2])
    if tag == 'let':
        return substitution_eval(substitute(a[2], a[0], substitution_eval(a[1])))
    if tag == 'letrec':
        return substitution_eval(substitute(a[3], a[0], ['rec'] + a[:3]))
    if tag == 'call':
        f, value = substitution_eval(a[0]), substitution_eval(a[1])
        if f[0] == 'rec':
            _, name, param, body = f
            body = substitute(body, name, f)
        else:
            _, param, body = f
        return substitution_eval(substitute(body, param, value))
    raise AssertionError(node)


class SemanticsTests(unittest.TestCase):
    def test_references_and_observation_budget(self):
        for task in m.make_tasks():
            self.assertTrue(25 <= len(task['cases']) <= 36)
            namespace = {}
            exec(task['reference'], namespace)
            observations = []
            for arg, expected in task['cases']:
                original = copy.deepcopy(arg)
                actual = namespace[task['function']](arg)
                self.assertEqual(actual, expected, (task['id'], arg))
                self.assertIs(type(actual), type(expected))
                self.assertEqual(arg, original)
                observations.append(dict(actual=grading.typed(actual), input_after=grading.typed(arg), same_object=actual is arg))
            self.assertLess(len(json.dumps(dict(results=observations)).encode()), 49152)

    def test_independent_oracles(self):
        tasks = {t['id']: t for t in m.make_tasks()}
        for arg, expected in tasks['eval_lexical']['cases']:
            self.assertEqual(substitution_eval(arg), ['int', expected])
        for arg, expected in tasks['min_resource_route']['cases']:
            if arg['budget'] <= 6:
                self.assertEqual(m.brute_route(arg), expected)
        for arg, expected in tasks['min_parse_cost']['cases'][10:]:
            self.assertEqual(m.acyclic_parse(arg), expected)

    def test_domain(self):
        for task in m.make_tasks():
            for arg, _ in task['cases']:
                if task['id'] == 'min_parse_cost':
                    self.assertTrue(1 <= arg['nonterminals'] <= 8)
                    self.assertLessEqual(len(arg['rules']), 30)
                    self.assertLessEqual(len(arg['text']), 24)
                    for lhs, rhs, cost in arg['rules']:
                        self.assertTrue(0 <= lhs < arg['nonterminals'])
                        self.assertTrue(0 <= cost <= 10)
                        self.assertLessEqual(len(rhs), 3)
                        for tag, value in rhs:
                            self.assertTrue(tag == 'N' and 0 <= value < arg['nonterminals'] or tag == 'T' and value in 'ab')
                elif task['id'] == 'eval_lexical':
                    def check(node):
                        tag = node[0]
                        if tag == 'int':
                            self.assertTrue(type(node[1]) is int and abs(node[1]) <= 10**9)
                            return 1
                        if tag == 'var':
                            self.assertTrue(node[1].isascii() and node[1].isalpha() and node[1].islower() and 1 <= len(node[1]) <= 8)
                            return 1
                        if tag in ('let', 'fn', 'letrec'):
                            names = node[1:3] if tag == 'letrec' else node[1:2]
                            for name in names:
                                self.assertTrue(name.isascii() and name.isalpha() and name.islower() and 1 <= len(name) <= 8)
                            if tag == 'letrec':
                                self.assertNotEqual(node[1], node[2])
                            children = node[3:] if tag == 'letrec' else node[2:]
                        else:
                            children = node[1:]
                        return 1 + sum(check(child) for child in children)
                    self.assertLessEqual(check(arg), 250)
                elif task['id'] == 'min_resource_route':
                    self.assertTrue(1 <= arg['n'] <= 16)
                    self.assertLessEqual(len(arg['edges']), 60)
                    self.assertTrue(0 <= arg['budget'] <= 80)
                    self.assertEqual(arg['required'], sorted(set(arg['required'])))
                    self.assertLessEqual(len(arg['required']), 5)
                    for u, v, resource, cost in arg['edges']:
                        self.assertTrue(0 <= u < arg['n'] and 0 <= v < arg['n'])
                        self.assertTrue(1 <= resource <= 8 and -10 <= cost <= 20)

    def test_actual_mutants(self):
        tasks = {t['id']: t for t in m.make_tasks()}
        mutations = [
            ('min_parse_cost', 'total = cost', 'total = 0'),
            ('min_parse_cost', "cuts = [()] if left == right else []", 'cuts = []'),
            ('min_resource_route', 'answer = cost if answer is None else min(answer, cost)', 'return cost'),
            ('min_resource_route', 'value = cost + price', 'value = cost + max(0, price)'),
            ('eval_lexical', 'return args[0], args[1], env', 'return args[0], args[1], {}'),
            ('eval_lexical', "dict(captured, **{param: value})", "dict(env, **{param: value})"),
            ('eval_lexical', "dict(captured, **{param: value})", "{param: value, **captured}"),
        ]
        for name, before, after in mutations:
            task = tasks[name]
            self.assertIn(before, task['reference'])
            namespace = {}
            exec(task['reference'].replace(before, after), namespace)
            killed = False
            for arg, expected in task['cases']:
                try:
                    killed = namespace[name](copy.deepcopy(arg)) != expected
                except Exception:
                    killed = True
                if killed:
                    break
            self.assertTrue(killed, (name, before))

    def test_mutant_regressions(self):
        tasks = {t['id']: t['cases'] for t in m.make_tasks()}
        # Unit/nullable rules, occurrence costs, duplicate alternatives.
        self.assertEqual([expected for _, expected in tasks['min_parse_cost'][:7]], [None, 3, None, 4, 2, 11, 8])
        # Early goal stopping, ignoring budget, and forbidding repeated edges fail these.
        self.assertEqual([expected for _, expected in tasks['min_resource_route'][:6]], [0, None, -160, 9, 7, -3])
        # Dynamic scope, eager if0, and broken self capture have distinct witnesses.
        self.assertEqual(tasks['eval_lexical'][0][1], -10)
        self.assertEqual(tasks['eval_lexical'][27][1], 17)
        self.assertEqual(tasks['eval_lexical'][25][1], 8)


if __name__ == '__main__':
    unittest.main()
