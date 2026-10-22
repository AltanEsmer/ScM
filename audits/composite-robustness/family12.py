"""Fresh F1/F2 robustness cases; no frozen answers are used.

F1 enumerates every bounded integer arc flow and tests conservation directly.
Version lookup walks ancestor patches per arc rather than copying snapshots.
F2 memoizes exact-resource, target-span tree costs; positive rule resources
make recursive/nullable cycles finite. Verification independently uses balance
state DP for F1 and explicit leftmost sentential-form expansion for F2.
F1 has 160 fixed-seed cases (20 directed, 20 maximum-bound, 80 random,
40 metamorphic); F2 has 172 (32 directed, 20 maximum-bound, 80 random,
40 metamorphic). Metamorphisms rename vertices or swap terminals. F2 directed
cases include successful length-three/four trees at budgets five through seven,
ordered yields, and nullable/unary cost-versus-resource tradeoffs.
Goldens are hand-derived; small exhaustive crosschecks include empty graphs,
parallel arcs, self loops, negative cycles, nullable and recursive grammars.
Validators require exact JSON types and enforce every structural bound.
"""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import random


def _require(ok):
    if not ok:
        raise ValueError('argument violates task clauses')


def _int(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def validate_f1(arg):
    _require(type(arg) is dict and set(arg) == {'n', 'arcs', 'versions'})
    n, arcs, versions = arg['n'], arg['arcs'], arg['versions']
    _require(_int(n, 1, 4) and type(arcs) is list and len(arcs) <= 6)
    for e in arcs:
        _require(type(e) is list and len(e) == 5)
        u, v, lo, hi, c = e
        _require(_int(u, 0, n-1) and _int(v, 0, n-1) and
                 _int(lo, 0, 2) and _int(hi, lo, 2) and _int(c, -5, 5))
    _require(type(versions) is list and len(versions) <= 8 and (arcs or not versions))
    for j, e in enumerate(versions):
        _require(type(e) is list and len(e) == 5)
        parent, index, lo, hi, c = e
        _require(_int(parent, 0, j) and _int(index, 0, len(arcs)-1) and
                 _int(lo, 0, 2) and _int(hi, lo, 2) and _int(c, -5, 5))


def validate_f2(arg):
    _require(type(arg) is dict and set(arg) == {'n', 'start', 'rules', 'budget', 'text'})
    n = arg['n']
    _require(_int(n, 1, 3) and _int(arg['start'], 0, n-1))
    _require(_int(arg['budget'], 0, 7) and type(arg['text']) is str and
             len(arg['text']) <= 7 and set(arg['text']) <= set('ab'))
    _require(type(arg['rules']) is list and len(arg['rules']) <= 6)
    for rule in arg['rules']:
        _require(type(rule) is list and len(rule) == 4)
        lhs, rhs, resource, cost = rule
        _require(_int(lhs, 0, n-1) and _int(resource, 1, 3) and _int(cost, -5, 5))
        _require(type(rhs) is list and len(rhs) <= 2)
        _require(not rhs or (len(rhs) == 1 and type(rhs[0]) is str and rhs[0] in ('a', 'b'))
                 or all(_int(x, 0, n-1) for x in rhs))


def oracle_f1(arg):
    validate_f1(arg)
    answers = []
    for version in range(len(arg['versions']) + 1):
        edges = []
        for index, original in enumerate(arg['arcs']):
            edge = original[:]
            ancestor = version
            while ancestor:
                parent, changed, lo, hi, cost = arg['versions'][ancestor-1]
                if changed == index:
                    edge[2:] = [lo, hi, cost]
                    break
                ancestor = parent
            edges.append(edge)
        best = None
        for flows in product(*(range(e[2], e[3]+1) for e in edges)):
            balance = [0] * arg['n']
            cost = 0
            for f, (u, v, _, _, c) in zip(flows, edges):
                balance[u] -= f
                balance[v] += f
                cost += f*c
            if not any(balance) and (best is None or cost < best):
                best = cost
        answers.append(best)
    return answers


def oracle_f2(arg):
    validate_f2(arg)
    text = arg['text']

    @lru_cache(None)
    def tree(symbol, begin, end, resource):
        best = None
        for lhs, rhs, used, cost in arg['rules']:
            if lhs != symbol or used > resource:
                continue
            left = resource-used
            children = []
            if not rhs:
                if begin == end and left == 0:
                    children.append(0)
            elif type(rhs[0]) is str:
                if left == 0 and text[begin:end] == rhs[0]:
                    children.append(0)
            elif len(rhs) == 1:
                if left > 0:
                    children.append(tree(rhs[0], begin, end, left))
            else:
                for split in range(begin, end+1):
                    for first in range(1, left):
                        a = tree(rhs[0], begin, split, first)
                        b = tree(rhs[1], split, end, left-first)
                        if a is not None and b is not None:
                            children.append(a+b)
            for child in children:
                if child is not None and (best is None or child+cost < best):
                    best = child+cost
        return best

    values = [tree(arg['start'], 0, len(text), r) for r in range(1, arg['budget']+1)]
    return min((x for x in values if x is not None), default=None)


def _flow_dp(arg):
    snapshots = [deepcopy(arg['arcs'])]
    for parent, index, lo, hi, cost in arg['versions']:
        edges = deepcopy(snapshots[parent])
        edges[index][2:] = [lo, hi, cost]
        snapshots.append(edges)
    results = []
    for edges in snapshots:
        states = {(0,) * arg['n']: 0}
        for u, v, lo, hi, cost in edges:
            nxt = {}
            for balance, value in states.items():
                for f in range(lo, hi+1):
                    b = list(balance)
                    b[u] += f
                    b[v] -= f
                    key = tuple(b)
                    nxt[key] = min(nxt.get(key, float('inf')), value+f*cost)
            states = nxt
        results.append(states.get((0,) * arg['n']))
    return results


def _expand_f2(arg):
    # Enumerate derivations by leftmost expansion, without parsing spans.
    states = {((arg['start'],), 0): 0}
    best = None
    while states:
        nxt = {}
        for (form, spent), cost in states.items():
            index = next((i for i, x in enumerate(form) if type(x) is int), None)
            if index is None:
                if ''.join(form) == arg['text']:
                    best = cost if best is None else min(best, cost)
                continue
            if sum(type(x) is str for x in form) > len(arg['text']):
                continue
            prefix = ''.join(form[:index])
            if not arg['text'].startswith(prefix):
                continue
            for lhs, rhs, resource, value in arg['rules']:
                if lhs == form[index] and spent+resource <= arg['budget']:
                    new = form[:index]+tuple(rhs)+form[index+1:]
                    if sum(type(x) is int for x in new) > arg['budget']-spent-resource:
                        continue
                    key = (new, spent+resource)
                    nxt[key] = min(nxt.get(key, float('inf')), cost+value)
        states = nxt
    return best


def _case(family, cases, category, arg, oracle):
    cases.append({'id': f'{family}-{len(cases):03d}', 'category': category,
                  'argument': arg, 'expected': oracle(arg)})


def generate_f1():
    rng = random.Random(12001)
    cases = []
    bounds = [(a, b) for a in range(3) for b in range(a, 3)]
    for i in range(20):
        cost = i % 11-5
        arcs = ([[0, 1, 1, 2, cost], [1, 0, 0, 2, -2]] if i % 2 else
                [[0, 0, 0, 2, cost], [0, 1, 1, 1, 0]])
        versions = [[0, 1, 0, 0, 0], [1, 0, 0, 2, -5], [0, 0, 2, 2, 5],
                    [2, 1, 1, 2, -5]]
        if i == 0:
            arcs, versions = [], []
        _case('f1', cases, 'directed', {'n': 2, 'arcs': arcs, 'versions': versions}, oracle_f1)
    for i in range(100):
        maximum = i < 20
        n = 4 if maximum else rng.randint(1, 4)
        arcs = []
        for _ in range(6 if maximum else rng.randint(0, 6)):
            lo, hi = rng.choice(bounds)
            arcs.append([rng.randrange(n), rng.randrange(n), lo, hi, rng.randint(-5, 5)])
        versions = []
        for j in range((8 if maximum else rng.randint(0, 8)) if arcs else 0):
            lo, hi = rng.choice(bounds)
            versions.append([rng.randrange(j+1), rng.randrange(len(arcs)), lo, hi, rng.randint(-5, 5)])
        _case('f1', cases, 'maxbound' if maximum else 'random',
              {'n': n, 'arcs': arcs, 'versions': versions}, oracle_f1)
    for source in cases[20:60]:
        arg = deepcopy(source['argument'])
        permutation = list(reversed(range(arg['n'])))
        for e in arg['arcs']:
            e[0], e[1] = permutation[e[0]], permutation[e[1]]
        _case('f1', cases, 'metamorphic-vertex-renaming', arg, oracle_f1)
        assert cases[-1]['expected'] == source['expected']
    return cases


def generate_f2():
    rng = random.Random(12002)
    cases = []
    templates = [
        (1, 0, [], 7, ''),
        (1, 0, [[0, [], 1, -5]], 0, ''),
        (1, 0, [[0, [], 3, -5]], 3, ''),
        (1, 0, [[0, ['a'], 3, -5]], 2, 'a'),
        (1, 0, [[0, ['a'], 3, -5]], 3, 'a'),
        (1, 0, [[0, [0], 1, -3], [0, [], 1, 4]], 7, ''),
        (2, 0, [[0, [1], 1, -5], [1, [0], 1, -5], [1, [], 1, 2]], 7, ''),
        (1, 0, [[0, [0, 0], 1, -5], [0, [], 1, 1]], 7, ''),
        (1, 0, [[0, [0, 0], 1, -5], [0, [], 1, 1], [0, ['a'], 1, 2]], 7, 'a'),
        (1, 0, [[0, ['b'], 1, 5], [0, ['b'], 3, -5]], 2, 'b'),
        (1, 0, [[0, ['b'], 1, 5], [0, ['b'], 3, -5]], 3, 'b'),
        (1, 0, [[0, ['a'], 1, 2], [0, ['a'], 1, 2]], 7, 'a'),
        (3, 0, [[0, [1, 2], 1, 1], [1, ['a'], 1, 2], [2, ['b'], 1, 3]], 3, 'ab'),
        (3, 0, [[0, [1, 2], 1, 1], [1, ['a'], 1, 2], [2, ['b'], 1, 3]], 3, 'ba'),
        (3, 0, [[0, [1, 2], 1, 0], [1, [], 2, -4], [2, ['b'], 3, 2]], 6, 'b'),
        (3, 0, [[0, [1, 2], 1, 0], [1, ['a'], 3, 2], [2, [], 2, -4]], 6, 'a'),
        (2, 1, [[0, [], 1, -5], [1, ['b'], 2, 4]], 7, 'b'),
        (1, 0, [[0, [0], 1, -5]], 7, ''),
        (1, 0, [[0, [0, 0], 1, 0], [0, ['a'], 1, 1], [0, ['b'], 1, -1]], 7, 'abba'),
        (1, 0, [[0, ['a'], 1, -5]], 7, 'aaaaaaa'),
    ]
    branching = [[0, [0, 0], 1, -5], [0, ['a'], 1, 2], [0, ['b'], 1, 3]]
    for text, budget in [('aba', 5), ('abb', 6), ('baa', 7),
                         ('abab', 7), ('baab', 7), ('aabb', 7)]:
        templates.append((1, 0, deepcopy(branching), budget, text))
    ordered = [[0, [1, 2], 1, 0], [2, [2, 1], 1, -1],
               [1, ['a'], 1, 2], [2, ['b'], 1, 3]]
    templates.extend([(3, 0, deepcopy(ordered), 5, 'aba'),
                      (3, 0, deepcopy(ordered), 7, 'abaa')])
    unary = branching + [[0, [1], 1, -5], [1, ['a'], 1, 0]]
    templates.extend([(2, 0, deepcopy(unary), 5, 'aba'),
                      (2, 0, deepcopy(unary), 6, 'aba')])
    nullable = branching + [[0, [], 1, -5]]
    templates.extend([(1, 0, deepcopy(nullable), 5, 'aba'),
                      (1, 0, deepcopy(nullable), 7, 'aba')])
    for n, start, rules, budget, text in templates:
        arg = {'n': n, 'start': start, 'rules': rules, 'budget': budget, 'text': text}
        _case('f2', cases, 'directed', arg, oracle_f2)
    for i in range(100):
        maximum = i < 20
        n = 3 if maximum else rng.randint(1, 3)
        rhses = [[], ['a'], ['b']] + [[x] for x in range(n)] + [[x, y] for x in range(n) for y in range(n)]
        rules = [[rng.randrange(n), deepcopy(rng.choice(rhses)), rng.randint(1, 3), rng.randint(-5, 5)]
                 for _ in range(6 if maximum else rng.randint(0, 6))]
        arg = {'n': n, 'start': rng.randrange(n), 'rules': rules,
               'budget': 7 if maximum else rng.randint(0, 7),
               'text': ''.join(rng.choice('ab') for _ in range(7 if maximum else rng.randint(0, 7)))}
        if i % 2 == 0:
            terminal = rng.choice(['', 'a', 'b'])
            productive = [arg['start'], list(terminal), rng.randint(1, 3), rng.randint(-5, 5)]
            if rules:
                rules[-1] = productive
            else:
                rules.append(productive)
            arg['text'] = terminal
            arg['budget'] = 7 if maximum else rng.randint(productive[2], 7)
        _case('f2', cases, 'maxbound' if maximum else 'random', arg, oracle_f2)
    for source in cases[20:60]:
        arg = deepcopy(source['argument'])
        arg['text'] = arg['text'].translate(str.maketrans('ab', 'ba'))
        for rule in arg['rules']:
            if rule[1] and type(rule[1][0]) is str:
                rule[1][0] = rule[1][0].translate(str.maketrans('ab', 'ba'))
        _case('f2', cases, 'metamorphic-terminal-swap', arg, oracle_f2)
        assert cases[-1]['expected'] == source['expected']
    return cases


def verify_oracles():
    checked = {'f1': 0, 'f2': 0}
    gold1 = {'n': 2, 'arcs': [[0, 1, 1, 2, -4], [1, 0, 0, 2, 1]],
             'versions': [[0, 1, 0, 0, 1], [1, 0, 0, 0, -4], [0, 0, 1, 1, 5]]}
    assert oracle_f1(gold1) == [-6, None, 0, 6]
    gold2 = {'n': 1, 'start': 0, 'rules': [[0, [0], 2, -3], [0, [], 1, 2]], 'budget': 7, 'text': ''}
    assert oracle_f2(gold2) == -7
    assert oracle_f2(dict(gold2, budget=0)) is None
    assert oracle_f1({'n': 1, 'arcs': [[0, 0, 1, 2, -5]], 'versions': []}) == [-10]
    assert oracle_f2({'n': 1, 'start': 0, 'rules': [[0, [0, 0], 1, -5],
                       [0, [], 1, 1]], 'budget': 7, 'text': ''}) == -11
    deep = {'n': 1, 'start': 0, 'rules': [[0, [0, 0], 1, -5],
            [0, ['a'], 1, 2], [0, ['b'], 1, 3]], 'budget': 5, 'text': 'aba'}
    assert oracle_f2(deep) == -3
    assert oracle_f2(dict(deep, budget=4)) is None
    assert oracle_f2(dict(deep, budget=7, text='abab')) == -5
    assert oracle_f2(dict(deep, budget=6, text='abab')) is None
    assert oracle_f2(dict(deep, budget=7,
                         rules=deep['rules'] + [[0, [], 1, -5]])) == -13
    assert oracle_f2(dict(deep, budget=6, n=2,
                         rules=deep['rules'] + [[0, [1], 1, -5], [1, ['a'], 1, 0]])) == -10
    invalids = [
        (validate_f1, dict(gold1, n=True)),
        (validate_f1, dict(gold1, versions=[[1, 0, 0, 1, 0]])),
        (validate_f1, dict(gold1, arcs=[[0, 2, 0, 1, 0]])),
        (validate_f1, dict(gold1, arcs=[], versions=[[0, 0, 0, 0, 0]])),
        (validate_f1, dict(gold1, arcs=[[0, 0, 2, 1, 0]])),
        (validate_f1, dict(gold1, extra=0)),
        (validate_f2, dict(gold2, budget=True)),
        (validate_f2, dict(gold2, text='c')),
        (validate_f2, dict(gold2, rules=[[0, [True], 1, 0]])),
        (validate_f2, dict(gold2, rules=[[0, ['a', 'b'], 1, 0]])),
        (validate_f2, dict(gold2, rules=[[0, [], 0, 0]])),
        (validate_f2, dict(gold2, start=1)),
    ]
    for validator, arg in invalids:
        try:
            validator(arg)
        except ValueError:
            pass
        else:
            raise AssertionError('validator accepted invalid argument')
    for endpoints in product(range(2), repeat=4):
        for costs in product((-1, 0, 1), repeat=2):
            for bounds in product(((0, 0), (0, 1), (1, 1)), repeat=2):
                arg = {'n': 2, 'arcs': [[*endpoints[:2], *bounds[0], costs[0]],
                       [*endpoints[2:], *bounds[1], costs[1]]], 'versions': []}
                assert oracle_f1(arg) == _flow_dp(arg)
                checked['f1'] += 1
    possibilities = [[0, rhs, resource, cost] for rhs in ([], ['a'], ['b'], [0], [0, 0])
                     for resource in (1, 2) for cost in (-1, 1)]
    for rules in product(possibilities, repeat=2):
        for text in ('', 'a', 'b', 'aa', 'ab'):
            arg = {'n': 1, 'start': 0, 'rules': list(rules), 'budget': 4, 'text': text}
            assert oracle_f2(arg) == _expand_f2(arg)
            checked['f2'] += 1
    for family, generate, oracle, independent in (('f1', generate_f1, oracle_f1, _flow_dp),
                                                 ('f2', generate_f2, oracle_f2, _expand_f2)):
        for case in generate():
            arg = deepcopy(case['argument'])
            before = deepcopy(arg)
            assert oracle(arg) == independent(arg) == case['expected']
            assert arg == before
            checked[family] += 1
    return checked


if __name__ == '__main__':
    print(verify_oracles())
