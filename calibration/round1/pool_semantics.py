"""Bounded semantic contracts with literal and independent oracle ground truth."""
import inspect
import itertools
import pathlib
import random


def min_parse_cost(data):
    import itertools
    n = len(data['text'])
    chart = {}
    changed = True
    while changed:
        changed = False
        for width in range(n + 1):
            for left in range(n - width + 1):
                right = left + width
                for lhs, rhs, cost in data['rules']:
                    cuts = itertools.combinations_with_replacement(range(left, right + 1), max(0, len(rhs) - 1))
                    if not rhs:
                        cuts = [()] if left == right else []
                    for middle in cuts:
                        points = (left,) + middle + (right,)
                        total = cost
                        for index, (tag, value) in enumerate(rhs):
                            a, b = points[index:index + 2]
                            if tag == 'T':
                                part = 0 if b == a + 1 and data['text'][a:b] == value else None
                            else:
                                part = chart.get((value, a, b))
                            if part is None:
                                break
                            total += part
                        else:
                            key = (lhs, left, right)
                            if key not in chart or total < chart[key]:
                                chart[key] = total
                                changed = True
    return chart.get((data['start'], 0, n))


def min_resource_route(data):
    bits = {v: 1 << i for i, v in enumerate(data['required'])}
    full = (1 << len(bits)) - 1
    layers = [{} for _ in range(data['budget'] + 1)]
    layers[0][data['start'], bits.get(data['start'], 0)] = 0
    outgoing = [[] for _ in range(data['n'])]
    for u, v, resource, cost in data['edges']:
        outgoing[u].append((v, resource, cost))
    answer = None
    for used, layer in enumerate(layers):
        for (u, mask), cost in layer.items():
            if u == data['goal'] and mask == full:
                answer = cost if answer is None else min(answer, cost)
            for v, resource, price in outgoing[u]:
                if used + resource <= data['budget']:
                    target = layers[used + resource]
                    key = v, mask | bits.get(v, 0)
                    value = cost + price
                    if key not in target or value < target[key]:
                        target[key] = value
    return answer


def eval_lexical(data):
    def evaluate(node, env):
        tag, *args = node
        if tag == 'int':
            return args[0]
        if tag == 'var':
            return env[args[0]]
        if tag in ('add', 'sub', 'mul'):
            a = evaluate(args[0], env)
            b = evaluate(args[1], env)
            return a + b if tag == 'add' else a - b if tag == 'sub' else a * b
        if tag == 'if0':
            return evaluate(args[1] if evaluate(args[0], env) == 0 else args[2], env)
        if tag == 'let':
            value = evaluate(args[1], env)
            return evaluate(args[2], dict(env, **{args[0]: value}))
        if tag == 'fn':
            return args[0], args[1], env
        if tag == 'call':
            param, body, captured = evaluate(args[0], env)
            value = evaluate(args[1], env)
            return evaluate(body, dict(captured, **{param: value}))
        name, param, body, rest = args
        captured = dict(env)
        captured[name] = param, body, captured
        return evaluate(rest, captured)
    return evaluate(data, {})


def brute_route(data):
    # Enumerate walks, without merging states or using the reference's masks.
    answer = None
    stack = [(data['start'], 0, 0, frozenset([data['start']]))]
    while stack:
        u, used, price, visited = stack.pop()
        if u == data['goal'] and set(data['required']) <= visited:
            answer = price if answer is None else min(answer, price)
        for a, b, resource, cost in data['edges']:
            if a == u and used + resource <= data['budget']:
                stack.append((b, used + resource, price + cost, visited | {b}))
    return answer


def acyclic_parse(data):
    # Materialize all yields of an acyclic grammar, independently of spans.
    def yields(symbol):
        tag, value = symbol
        if tag == 'T':
            return [(value, 0)]
        output = []
        for lhs, rhs, cost in data['rules']:
            if lhs == value:
                for pieces in itertools.product(*(yields(s) for s in rhs)):
                    output.append((''.join(p[0] for p in pieces), cost + sum(p[1] for p in pieces)))
        return output
    matches = [cost for text, cost in yields(['N', data['start']]) if text == data['text']]
    return min(matches, default=None)


def make_tasks():
    rng = random.Random(714209)
    parses = []
    def grammar(k, rules, text, expected, start=0):
        parses.append([dict(nonterminals=k, start=start, rules=rules, text=text), expected])
    N = lambda i: ['N', i]
    T = lambda c: ['T', c]
    grammar(1, [], '', None)
    grammar(1, [[0, [], 3]], '', 3)
    grammar(1, [[0, [N(0)], 0]], '', None)
    grammar(2, [[0, [N(1)], 0], [1, [N(0)], 0], [1, [], 4]], '', 4)
    grammar(1, [[0, [N(0)], 0], [0, [T('a')], 7], [0, [T('a')], 2]], 'a', 2)
    grammar(1, [[0, [N(0), N(0)], 1], [0, [T('a')], 2]], 'aaaa', 11)
    grammar(2, [[0, [N(1), T('a'), N(1)], 2], [1, [], 3]], 'a', 8)
    grammar(1, [[0, [T('a'), N(0), T('b')], 1], [0, [], 0]], 'aaaabbbb', 4)
    grammar(1, [[0, [T('a'), N(0)], 1], [0, [], 2]], 'a' * 24, 26)
    grammar(2, [[0, [N(1), N(1)], 0], [1, [], 5], [1, [T('b')], 1]], 'b', 6)
    for _ in range(18):
        rules = []
        for lhs in range(3):
            for _ in range(rng.randrange(1, 4)):
                rhs = [N(rng.randrange(lhs + 1, 3)) if lhs < 2 and rng.random() < .45 else T(rng.choice('ab')) for _ in range(rng.randrange(3))]
                rules.append([lhs, rhs, rng.randrange(11)])
        arg = dict(nonterminals=3, start=rng.randrange(3), rules=rules, text=''.join(rng.choices('ab', k=rng.randrange(5))))
        parses.append([arg, acyclic_parse(arg)])
    routes = []
    def route(n, edges, start, goal, budget, required, expected):
        routes.append([dict(n=n, edges=edges, start=start, goal=goal, budget=budget, required=required), expected])
    route(1, [], 0, 0, 0, [], 0)
    route(2, [], 0, 1, 0, [], None)
    route(1, [[0, 0, 1, -2]], 0, 0, 80, [0], -160)
    route(2, [[0, 1, 2, 4], [0, 1, 1, 9]], 0, 1, 1, [], 9)
    route(3, [[0, 2, 1, 0], [0, 1, 1, 5], [1, 2, 1, 2]], 0, 2, 2, [1], 7)
    route(2, [[0, 1, 1, 5], [1, 0, 1, -9]], 0, 1, 5, [0, 1], -3)
    route(3, [[0, 1, 1, -5], [1, 2, 1, 10], [0, 2, 2, 1]], 0, 2, 2, [], 1)
    route(16, [[i, i + 1, 1, 1] for i in range(15)], 0, 15, 15, [0, 3, 6, 9, 15], 15)
    for _ in range(20):
        n = rng.randrange(1, 5)
        arg = dict(n=n, edges=[[rng.randrange(n), rng.randrange(n), rng.randrange(1, 5), rng.randrange(-10, 21)] for _ in range(rng.randrange(9))], start=rng.randrange(n), goal=rng.randrange(n), budget=rng.randrange(7), required=sorted(rng.sample(range(n), rng.randrange(min(n, 3) + 1))))
        routes.append([arg, brute_route(arg)])
    lexical = []
    I = lambda x: ['int', x]
    V = lambda x: ['var', x]
    for a in (-7, 0, 2, 13):
        lexical.extend([
            [['let', 'x', I(a), ['let', 'f', ['fn', 'y', ['sub', V('x'), V('y')]], ['let', 'x', I(99), ['call', V('f'), I(3)]]]], a - 3],
            [['call', ['call', ['fn', 'x', ['fn', 'y', ['add', V('x'), V('y')]]], I(a)], I(8)], a + 8],
            [['let', 'x', I(a), ['let', 'x', ['add', V('x'), I(1)], V('x')]], a + 1],
            [['if0', I(a), I(11), ['mul', I(a), I(3)]], 11 if a == 0 else a * 3],
        ])
    for n in range(8):
        lexical.append([['letrec', 'sum', 'n', ['if0', V('n'), I(0), ['add', V('n'), ['call', V('sum'), ['sub', V('n'), I(1)]]]], ['call', V('sum'), I(n)]], n * (n + 1) // 2])
    lexical.extend([
        [['let', 'x', I(6), ['letrec', 'f', 'n', ['if0', V('n'), V('x'), ['call', V('f'), ['sub', V('n'), I(1)]]], ['let', 'x', I(100), ['call', V('f'), I(4)]]]], 6],
        [['letrec', 'f', 'n', ['if0', V('n'), I(8), ['call', V('f'), ['sub', V('n'), I(1)]]], ['let', 'g', V('f'), ['let', 'f', ['fn', 'x', I(99)], ['call', V('g'), I(3)]]]], 8],
        [['call', ['fn', 'f', ['call', V('f'), I(9)]], ['fn', 'x', ['mul', V('x'), V('x')]]], 81],
        [['letrec', 'f', 'n', ['call', V('f'), V('n')], ['if0', I(0), I(17), ['call', V('f'), I(0)]]], 17],
    ])
    lexical.append([['let', 'x', I(5), ['call', ['fn', 'x', V('x')], I(7)]], 7])
    # Seeded arithmetic/closure combinations have independently derived literals.
    for _ in range(4):
        a, b, c = (rng.randrange(-20, 21) for _ in range(3))
        lexical.append([['let', 'x', I(a), ['call', ['fn', 'y', ['sub', ['mul', V('x'), V('y')], I(c)]], I(b)]], a * b - c])
    result = []
    for function, cases in ((min_parse_cost, parses), (min_resource_route, routes), (eval_lexical, lexical)):
        name = function.__name__
        result.append(dict(id=name, function=name, cases=cases, reference=inspect.getsource(function), spec=(pathlib.Path(__file__).parent / 'prompts' / (name + '_B0.txt')).read_text()))
    return result
