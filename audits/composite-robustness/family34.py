"""Independent F3/F4 audit data, without candidate execution or saved answers.

F3 uses an explicit continuation machine with tagged cells, snapshots, and
closures. Validation checks every syntax node and lexical scope, then executes
only selected paths with fuel, integer, and store bounds. A separate recursive
interpreter cross-checks tiny exhaustive terms and hand-derived goldens.
F4 uses dynamic programming over ternary request states and Pareto (time,cost)
frontiers. Its independent small-instance check enumerates complete event
permutations and simulates each valid precedence order.
Each deterministic 160-case family combines directed semantic traps, literal
bounds, seeded structured random inputs, and semantics-preserving transforms.
All helpers are pure with respect to supplied arguments.
"""
from copy import deepcopy
from itertools import permutations, product
import random
import re


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _int(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def _keys(x, keys):
    return type(x) is dict and set(x) == set(keys.split())


def _name(x):
    return type(x) is str and re.fullmatch('[a-z]{1,8}', x) is not None


def _syntax_f3(arg):
    _require(_keys(arg, 'bindings program'), 'F3 keys')
    bindings = arg['bindings']
    _require(type(bindings) is list and len(bindings) <= 6, 'bindings')
    count = 0
    arities = {'var': 1, 'let': 3, 'fn': 2, 'call': 2, 'seq': 2,
               'if': 3, 'add': 2, 'sub': 2, 'ref': 1, 'get': 1,
               'set': 2, 'snap': 0, 'restore': 2}

    def walk(e, scope, depth):
        nonlocal count
        count += 1
        _require(count <= 100 and depth <= 18, 'syntax resource limit')
        if type(e) is int:
            _require(-20 <= e <= 20, 'literal bound')
            return
        _require(type(e) is list and bool(e) and type(e[0]) is str,
                 'expression type')
        op = e[0]
        _require(op in arities and len(e) == arities[op] + 1, 'form arity')
        if op == 'var':
            _require(_name(e[1]) and e[1] in scope, 'unbound name')
        elif op in ('let', 'fn'):
            _require(_name(e[1]), 'name')
            if op == 'let':
                walk(e[2], scope, depth + 1)
                walk(e[3], scope | {e[1]}, depth + 1)
            else:
                walk(e[2], scope | {e[1]}, depth + 1)
        else:
            for child in e[1:]:
                walk(child, scope, depth + 1)

    scope = set()
    for pair in bindings:
        _require(type(pair) is list and len(pair) == 2, 'binding pair')
        name, expr = pair
        _require(_name(name) and name not in scope, 'binding name')
        walk(expr, scope, 1)
        scope.add(name)
    walk(arg['program'], scope, 1)


def _machine_f3(arg):
    store, env, steps = [], {}, 0

    def integer(v):
        _require(_int(v, -10000, 10000), 'dynamic integer')
        return v

    def cell(v):
        _require(type(v) is tuple and v[0] == 'cell' and 0 <= v[1] < len(store),
                 'live cell required')
        return v[1]

    def run(expr, scope):
        nonlocal steps
        todo, values = [('eval', expr, scope)], []
        while todo:
            frame = todo.pop()
            kind = frame[0]
            if kind == 'eval':
                _, e, local = frame
                steps += 1
                _require(steps <= 300, 'evaluation fuel')
                if type(e) is int:
                    values.append(e)
                    continue
                op = e[0]
                if op == 'var':
                    values.append(local[e[1]])
                elif op == 'fn':
                    values.append(('closure', e[1], e[2], local.copy()))
                elif op == 'snap':
                    values.append(('snapshot', tuple(store)))
                elif op == 'let':
                    todo.extend([('let', e[1], e[3], local), ('eval', e[2], local)])
                elif op == 'if':
                    todo.extend([('if', e[2], e[3], local), ('eval', e[1], local)])
                elif op in ('ref', 'get'):
                    todo.extend([(op,), ('eval', e[1], local)])
                else:
                    todo.extend([('left', op, e[2], local), ('eval', e[1], local)])
            elif kind == 'let':
                local = dict(frame[3]); local[frame[1]] = values.pop()
                todo.append(('eval', frame[2], local))
            elif kind == 'if':
                condition = integer(values.pop())
                todo.append(('eval', frame[1] if condition else frame[2], frame[3]))
            elif kind == 'left':
                _, op, right, local = frame
                left = values.pop()
                if op == 'restore':
                    _require(type(left) is tuple and left[0] == 'snapshot', 'snapshot required')
                    store[:] = left[1]
                    todo.append(('eval', right, local))
                else:
                    todo.extend([('apply', op, left), ('eval', right, local)])
            elif kind == 'ref':
                value = integer(values.pop())
                _require(len(store) < 8, 'store bound')
                values.append(('cell', len(store))); store.append(value)
            elif kind == 'get':
                values.append(store[cell(values.pop())])
            elif kind == 'apply':
                _, op, left = frame
                right = values.pop()
                if op == 'call':
                    _require(type(left) is tuple and left[0] == 'closure', 'closure required')
                    local = dict(left[3]); local[left[1]] = right
                    todo.append(('eval', left[2], local))
                elif op == 'seq':
                    values.append(right)
                elif op == 'set':
                    value = integer(right)
                    store[cell(left)] = value
                    values.append(value)
                else:
                    a, b = integer(left), integer(right)
                    values.append(integer(a + b if op == 'add' else a - b))
        _require(len(values) == 1, 'machine result')
        return values[0]

    for name, expr in arg['bindings']:
        env[name] = run(expr, env)
    value = integer(run(arg['program'], env))
    return {'value': value, 'store': store}


def validate_f3(arg):
    """Reject any static or evaluated-path violation of the complete F3 contract."""
    _syntax_f3(arg)
    _machine_f3(arg)


def oracle_f3(arg):
    _syntax_f3(arg)
    return _machine_f3(arg)


def _recursive_f3(arg):
    """Small-input cross-check with lexical Python functions and boxed cell IDs."""
    store = []
    class Cell:
        def __init__(self, index): self.index = index
    class Snapshot:
        def __init__(self): self.cells = store.copy()
    def evaluate(e, env):
        if type(e) is int: return e
        op = e[0]
        if op == 'var': return env[e[1]]
        if op == 'let':
            value = evaluate(e[2], env)
            return evaluate(e[3], {**env, e[1]: value})
        if op == 'fn':
            captured = env.copy()
            return lambda value: evaluate(e[2], {**captured, e[1]: value})
        if op == 'if': return evaluate(e[2] if evaluate(e[1], env) else e[3], env)
        if op == 'snap': return Snapshot()
        if op == 'restore':
            snapshot = evaluate(e[1], env)
            store[:] = snapshot.cells
            return evaluate(e[2], env)
        if op == 'ref':
            value = evaluate(e[1], env)
            handle = Cell(len(store)); store.append(value)
            return handle
        if op == 'get': return store[evaluate(e[1], env).index]
        first = evaluate(e[1], env)
        second = evaluate(e[2], env)
        if op == 'call': return first(second)
        if op == 'seq': return second
        if op == 'set': store[first.index] = second; return second
        if op == 'add': return first + second
        return first - second
    env = {}
    for name, expr in arg['bindings']: env[name] = evaluate(expr, env)
    return {'value': evaluate(arg['program'], env), 'store': store}


def validate_f4(arg):
    _require(_keys(arg, 'time cost requests vehicle'), 'F4 keys')
    time, cost = arg['time'], arg['cost']
    _require(type(time) is list and 1 <= len(time) <= 9, 'matrix size')
    n = len(time)
    for matrix in (time, cost):
        _require(type(matrix) is list and len(matrix) == n, 'matrix shape')
        for i, row in enumerate(matrix):
            _require(type(row) is list and len(row) == n, 'matrix row')
            _require(all(_int(x, 0, 20) for x in row) and row[i] == 0, 'matrix entries')
    requests = arg['requests']
    _require(type(requests) is list and len(requests) <= 4, 'requests')
    for r in requests:
        _require(_keys(r, 'pick drop load pw dw ps ds'), 'request keys')
        _require(all(_int(r[k], 0, n - 1) for k in ('pick', 'drop')), 'request nodes')
        _require(_int(r['load'], 1, 3), 'request load')
        _require(all(_int(r[k], 0, 5) for k in ('ps', 'ds')), 'service duration')
        for k in ('pw', 'dw'):
            w = r[k]
            _require(type(w) is list and len(w) == 2 and all(_int(x, 0, 80) for x in w)
                     and w[0] <= w[1], 'service window')
    v = arg['vehicle']
    _require(_keys(v, 'start end capacity release deadline'), 'vehicle keys')
    _require(all(_int(v[k], 0, n - 1) for k in ('start', 'end')), 'vehicle nodes')
    _require(_int(v['capacity'], 1, 5), 'capacity')
    _require(_int(v['release'], 0, 100) and _int(v['deadline'], v['release'], 100), 'vehicle times')


def oracle_f4(arg):
    validate_f4(arg)
    reqs, v = arg['requests'], arg['vehicle']
    m = len(reqs)
    start = (0,) * m
    frontier = {(start, v['start']): [(v['release'], 0)]}
    for _ in range(2 * m):
        following = {}
        for (status, node), labels in frontier.items():
            load = sum(r['load'] for r, s in zip(reqs, status) if s == 1)
            for i, r in enumerate(reqs):
                if status[i] == 2 or (status[i] == 0 and load + r['load'] > v['capacity']):
                    continue
                pick = status[i] == 0
                target = r['pick' if pick else 'drop']
                early, late = r['pw' if pick else 'dw']
                duration = r['ps' if pick else 'ds']
                after = list(status); after[i] += 1
                key = (tuple(after), target)
                for t, money in labels:
                    service = max(t + arg['time'][node][target], early)
                    if service > late: continue
                    label = (service + duration, money + arg['cost'][node][target])
                    choices = following.setdefault(key, [])
                    if any(t0 <= label[0] and c0 <= label[1] for t0, c0 in choices): continue
                    choices[:] = [(t0, c0) for t0, c0 in choices
                                  if not (label[0] <= t0 and label[1] <= c0)]
                    choices.append(label)
        frontier = following
    costs = [money + arg['cost'][node][v['end']]
             for (_, node), labels in frontier.items() for t, money in labels
             if t + arg['time'][node][v['end']] <= v['deadline']]
    return min(costs, default=None)


def _permutation_f4(arg):
    v, requests = arg['vehicle'], arg['requests']
    best = None
    for order in permutations(range(2 * len(requests))):
        seen, node, now, load, money = set(), v['start'], v['release'], 0, 0
        for event in order:
            i, delivery = divmod(event, 2)
            if delivery and 2 * i not in seen: break
            r = requests[i]
            destination = r['drop' if delivery else 'pick']
            lo, hi = r['dw' if delivery else 'pw']
            now = max(now + arg['time'][node][destination], lo)
            load += (-1 if delivery else 1) * r['load']
            if now > hi or not 0 <= load <= v['capacity']: break
            now += r['ds' if delivery else 'ps']
            money += arg['cost'][node][destination]
            node = destination; seen.add(event)
        else:
            if now + arg['time'][node][v['end']] <= v['deadline']:
                total = money + arg['cost'][node][v['end']]
                best = total if best is None else min(best, total)
    return best


def _v(name): return ['var', name]


def _f3_templates():
    c = _v('c'); s = _v('s')
    return [
        ('literal', [], 0),
        ('lexical_capture', [['x', 7], ['f', ['fn', 'y', ['sub', _v('x'), _v('y')]]]],
         ['let', 'x', 19, ['call', _v('f'), 2]]),
        ('alias', [['c', ['ref', 2]], ['d', c]], ['seq', ['set', _v('d'), 8], ['get', c]]),
        ('snapshot_copy', [['c', ['ref', 2]], ['s', ['snap']]],
         ['seq', ['set', c, 9], ['restore', s, ['get', c]]]),
        ('reuse_id', [['c', ['ref', 1]], ['s', ['snap']], ['d', ['ref', 2]]],
         ['restore', s, ['seq', ['ref', 17], ['get', _v('d')]]]),
        ('snapshot_expression_effect', [['c', ['ref', 1]], ['s', ['snap']]],
         ['restore', ['seq', ['set', c, 20], s], ['get', c]]),
        ('set_left_first', [['c', ['ref', 1]], ['d', ['ref', 2]]],
         ['seq', ['set', ['seq', ['set', c, 3], _v('d')], ['get', c]], ['get', _v('d')]]),
        ('argument_caller_scope', [['x', 3], ['f', ['fn', 'z', ['add', _v('x'), _v('z')]]]],
         ['let', 'x', 9, ['call', _v('f'), _v('x')]]),
        ('closure_alias', [['c', ['ref', 2]], ['f', ['fn', 'x', ['get', c]]]],
         ['seq', ['set', c, 11], ['call', _v('f'), 0]]),
        ('lazy_true', [], ['if', -1, 5, ['get', 0]]),
        ('lazy_false', [], ['if', 0, ['call', 0, 0], 6]),
        ('nested_restore', [['c', ['ref', 1]], ['s', ['snap']]],
         ['let', 't', ['seq', ['set', c, 7], ['snap']],
          ['restore', s, ['restore', _v('t'), ['get', c]]]]),
        ('unreachable_allocation', [], ['seq', ['ref', 8], 2]),
        ('call_left_first', [['c', ['ref', 0]]],
         ['call', ['seq', ['set', c, 4], ['fn', 'x', _v('x')]], ['get', c]]),
        ('higher_order', [], ['call', ['call', ['fn', 'x', ['fn', 'y', ['sub', _v('x'), _v('y')]]], 9], 4]),
        ('arithmetic_order', [['c', ['ref', 0]]], ['sub', ['set', c, 9], ['set', c, 2]]),
        ('restore_persists', [['s', ['snap']]], ['seq', ['ref', 3], ['restore', s, 8]]),
        ('parameter_shadow', [['x', 8]], ['call', ['fn', 'x', _v('x')], -2]),
        ('snapshot_argument', [['c', ['ref', 3]]],
         ['call', ['fn', 's', ['seq', ['set', c, 9], ['restore', s, ['get', c]]]], ['snap']]),
        ('restore_rhs_reuses_handle', [['c', ['ref', 2]], ['s', ['snap']], ['d', ['ref', 3]]],
         ['set', _v('d'), ['restore', s, ['seq', ['ref', 9], 7]]]),
    ]


def generate_f3():
    rng = random.Random(3403)
    result = []
    def add(category, arg):
        validate_f3(arg)
        result.append({'id': f'F3-{len(result):03d}', 'category': category,
                       'argument': deepcopy(arg), 'expected': oracle_f3(arg)})
    for category, bindings, program in _f3_templates():
        add('directed/' + category, {'bindings': bindings, 'program': program})
    for depth in (1, 8, 17):
        program = 0
        for _ in range(depth): program = ['add', 0, program]
        add('boundary/depth', {'bindings': [], 'program': program})
    add('boundary/eight_cells', {'bindings': [[c, ['ref', i]] for i,c in enumerate('abcdef')],
                               'program': ['seq', ['ref', 20], ['seq', ['ref', -20], 0]]})
    # A balanced full binary tree supplies 99 nodes without violating depth.
    leaves = [0] * 50
    while len(leaves) > 1:
        leaves = [['add', *leaves[i:i+2]] if i+1 < len(leaves) else leaves[i]
                  for i in range(0, len(leaves), 2)]
    add('boundary/ninety_nine_nodes', {'bindings': [], 'program': leaves[0]})
    add('boundary/one_hundred_nodes', {'bindings': [['z', 0]], 'program': deepcopy(leaves[0])})
    bindings = [['a', ['fn', 'x', ['add', _v('x'), _v('x')]]]]
    for previous, name in zip('abcd', 'bcde'):
        invocation = ['call', _v(previous), _v('x')]
        bindings.append([name, ['fn', 'x', ['seq', deepcopy(invocation), invocation]]])
    bindings.append(['z', 0])
    program = ['call', _v('a'), 0]
    for name in 'bcde':
        program = ['seq', ['call', _v(name), 0], program]
    add('boundary/three_hundred_evaluations', {'bindings': bindings, 'program': program})
    bindings = [['x', 20]]
    for previous, name in zip('xabcd', 'abcde'):
        bindings.append([name, ['add', _v(previous), _v(previous)]])
    terms = [_v('e') for _ in range(15)] + [_v('d'), _v('b')]
    while len(terms) > 1:
        terms = [['add', *terms[i:i+2]] if i+1 < len(terms) else terms[i]
                 for i in range(0, len(terms), 2)]
    add('boundary/positive_ten_thousand', {'bindings': bindings, 'program': terms[0]})
    add('boundary/negative_ten_thousand', {'bindings': deepcopy(bindings), 'program': ['sub', 0, terms[0]]})
    for i in range(91):
        x, y, z = [rng.randint(-20, 20) for _ in range(3)]
        kind = i % 5
        if kind == 0:
            arg = {'bindings': [['c', ['ref', x]], ['s', ['snap']]],
                   'program': ['seq', ['set', _v('c'), y], ['restore', _v('s'), ['add', ['get', _v('c')], z]]]}
        elif kind == 1:
            arg = {'bindings': [['x', x], ['f', ['fn', 'y', ['sub', _v('x'), _v('y')]]]],
                   'program': ['let', 'x', z, ['call', _v('f'), y]]}
        elif kind == 2:
            arg = {'bindings': [['c', ['ref', x]]], 'program':
                   ['if', y, ['add', ['set', _v('c'), z], ['get', _v('c')]], ['get', _v('c')]]}
        elif kind == 3:
            arg = {'bindings': [['c', ['ref', x]], ['s', ['snap']], ['d', ['ref', y]]],
                   'program': ['restore', _v('s'), ['let', 'e', ['ref', z], ['sub', ['get', _v('d')], ['get', _v('c')]]]]}
        else:
            arg = {'bindings': [], 'program': ['call', ['fn', 'x', ['call', ['fn', 'y', ['add', _v('x'), _v('y')]], y]], x]}
        add('seeded/' + str(kind), arg)
    bases = deepcopy(result[:20] + [c for c in result if c['category'].startswith('seeded/')][:20])
    for case in bases:
        arg = deepcopy(case['argument'])
        arg['program'] = ['seq', 0, arg['program']]
        add('metamorphic/pure_prefix', arg)
        assert result[-1]['expected'] == case['expected']
    return result


def _route_arg(n=3):
    return {'time': [[0 if i == j else 1 for j in range(n)] for i in range(n)],
            'cost': [[0 if i == j else 2 for j in range(n)] for i in range(n)],
            'requests': [], 'vehicle': {'start': 0, 'end': n-1, 'capacity': 3, 'release': 0, 'deadline': 100}}


def _request(pick=0, drop=1, load=1, pw=None, dw=None, ps=0, ds=0):
    return dict(pick=pick, drop=drop, load=load, pw=[0,80] if pw is None else pw,
                dw=[0,80] if dw is None else dw, ps=ps, ds=ds)


def generate_f4():
    rng = random.Random(3404)
    result = []
    def add(category, arg):
        validate_f4(arg)
        result.append({'id': f'F4-{len(result):03d}', 'category': category,
                       'argument': deepcopy(arg), 'expected': oracle_f4(arg)})
    a = _route_arg(); add('directed/empty_direct', a)
    a['vehicle']['deadline'] = 0; add('directed/empty_infeasible', a)
    directed = ('over_capacity', 'wait_exact_window', 'pickup_service_misses_delivery',
                'pickup_service_boundary', 'delivery_service_misses_finish',
                'delivery_service_finish_boundary', 'coincident_precedence',
                'duplicate_occurrences', 'capacity_requires_interleave',
                'slow_free_leg', 'fast_expensive_leg', 'late_release_exact_windows',
                'directed_endpoints', 'coincident_all_events', 'asymmetric_cost',
                'tight_event_order', 'window_eighty', 'zero_time_zero_cost')
    for i in range(18):
        a = _route_arg()
        r = _request(0, 1)
        a['requests'] = [r]
        if i == 0: r['load'] = 3; a['vehicle']['capacity'] = 2
        elif i == 1: r['pw'] = [20,20]; r['dw'] = [21,21]
        elif i == 2: r['ps'] = 5; r['dw'] = [0,5]
        elif i == 3: r['ps'] = 5; r['dw'] = [6,6]
        elif i == 4: r['ds'] = 5; a['vehicle']['deadline'] = 6
        elif i == 5: r['ds'] = 5; a['vehicle']['deadline'] = 7
        elif i == 6: r['pick'] = r['drop'] = 0; r['pw'] = [2,2]; r['dw'] = [0,1]
        elif i == 7: a['requests'] = [deepcopy(r), deepcopy(r)]
        elif i == 8: a['requests'] = [_request(0,1,2), _request(0,1,2)]; a['vehicle']['capacity'] = 2
        elif i == 9: a['time'][0][1] = 20; a['cost'][0][1] = 0
        elif i == 10: a['time'][0][1] = 0; a['cost'][0][1] = 20
        elif i == 11: a['vehicle']['release'] = 80; r['pw'] = r['dw'] = [80,80]; a['time'] = [[0]*3 for _ in range(3)]
        elif i == 12: a['vehicle']['start'] = 2; a['vehicle']['end'] = 0
        elif i == 13: r['pick'] = r['drop'] = 0; a['vehicle']['end'] = 0
        elif i == 14: a['requests'] = [_request(0,1), _request(1,0)]; a['cost'][1][0] = 20
        elif i == 15: a['requests'] = [_request(0,2,pw=[0,0],dw=[2,2]), _request(1,2,pw=[1,1],dw=[2,2])]
        elif i == 16: r['pw'] = [80,80]; r['dw'] = [80,80]
        else: a['time'] = [[0]*3 for _ in range(3)]; a['cost'] = [[0]*3 for _ in range(3)]
        add('directed/' + directed[i], a)
    for n in (1,9):
        for capacity in (1,5):
            a = _route_arg(n)
            a['requests'] = [_request(i%n, (i+1)%n, 3 if capacity==5 else 1, ps=5, ds=5) for i in range(4)]
            a['vehicle']['capacity'] = capacity
            add('boundary/nodes_requests_service', a)
    a = _route_arg(3)
    a['vehicle'].update(start=0, end=1, deadline=2)
    a['time'] = [[0,20,1],[1,0,1],[1,1,0]]
    a['cost'] = [[0,20,0],[0,0,0],[0,0,0]]
    add('directed/no_extra_waypoint_empty', a)
    a['requests'] = [_request(1,1)]
    add('directed/no_extra_waypoint_events', a)
    for i in range(94):
        n = rng.randint(1,9); a = _route_arg(n)
        for key in ('time','cost'):
            a[key] = [[0 if u==v else rng.randint(0,20) for v in range(n)] for u in range(n)]
        a['vehicle'] = {'start': rng.randrange(n), 'end': rng.randrange(n), 'capacity': rng.randint(1,5),
                        'release': rng.randint(0,15), 'deadline': rng.randint(40,100)}
        for _ in range(i%5):
            early = rng.randint(0,40); late = rng.randint(early,80)
            de = rng.randint(0,40); dl = rng.randint(de,80)
            a['requests'].append(_request(rng.randrange(n),rng.randrange(n),rng.randint(1,3),
                                          [early,late],[de,dl],rng.randint(0,5),rng.randint(0,5)))
        add('seeded/directed_matrices', a)
    for case in deepcopy(result[:40]):
        a = deepcopy(case['argument']); n = len(a['time']); p = list(reversed(range(n)))
        for key in ('time','cost'):
            old = a[key]; a[key] = [[old[p[u]][p[v]] for v in range(n)] for u in range(n)]
        for r in a['requests']:
            r['pick'] = p[r['pick']]; r['drop'] = p[r['drop']]
        for key in ('start','end'): a['vehicle'][key] = p[a['vehicle'][key]]
        a['requests'].reverse()
        add('metamorphic/node_request_permutation', a)
        assert result[-1]['expected'] == case['expected']
    return result


def verify_oracles():
    """Rerunnable hand goldens, exhaustive tiny crosschecks, and rejection checks."""
    counts = {'f3_goldens': 0, 'f3_crosschecks': 0, 'f4_goldens': 0, 'f4_crosschecks': 0,
              'invalid_rejections': 0}
    gold = [({'bindings': [], 'program': ['sub', 7, 2]}, {'value': 5, 'store': []}),
            ({'bindings': [['c',['ref',2]],['s',['snap']],['d',['ref',3]]],
              'program': ['restore',_v('s'),['seq',['ref',17],['get',_v('d')]]]},
             {'value':17,'store':[2,17]})]
    for a, expected in gold:
        assert oracle_f3(a) == expected == _recursive_f3(a)
        counts['f3_goldens'] += 1
    for x,y,op in product(range(-2,3), range(-2,3), ('add','sub')):
        expressions = [[op,x,y], ['let','x',x,[op,_v('x'),y]],
                       ['call',['fn','x',[op,_v('x'),y]],x],
                       ['let','c',['ref',x],['seq',['set',_v('c'),y],['get',_v('c')]]]]
        for e in expressions:
            a = {'bindings': [], 'program': e}
            assert oracle_f3(a) == _recursive_f3(a)
            counts['f3_crosschecks'] += 1
    for a in generate_f3():
        assert a['expected'] == _recursive_f3(a['argument'])
        counts['f3_crosschecks'] += 1
    a = _route_arg(); assert oracle_f4(a) == 2; counts['f4_goldens'] += 1
    a['requests'] = [_request(0,1)]; assert oracle_f4(a) == 4; counts['f4_goldens'] += 1
    a['vehicle']['deadline'] = 1; assert oracle_f4(a) is None; counts['f4_goldens'] += 1
    for travel, money, cap, duplicate in product(range(3), range(3), (1,2), (False,True)):
        a = _route_arg(2)
        a['time'] = [[0,travel],[2-travel,0]]; a['cost'] = [[0,money],[2-money,0]]
        a['vehicle'].update(capacity=cap, deadline=4)
        a['requests'] = [_request(0,1,pw=[0,1],dw=[0,3],ps=1)]
        if duplicate: a['requests'].append(deepcopy(a['requests'][0]))
        assert oracle_f4(a) == _permutation_f4(a)
        counts['f4_crosschecks'] += 1
    for case in generate_f4():
        assert case['expected'] == _permutation_f4(case['argument'])
        counts['f4_crosschecks'] += 1
    invalid = [({'bindings':[],'program':True},validate_f3),
               ({'bindings':[],'program':['if',0,21,0]},validate_f3),
               ({'bindings':[],'program':['fn','x',_v('y')]},validate_f3),
               ({'bindings':[],'program':['get',0]},validate_f3),
               ({'bindings':[],'program':['call',0,1]},validate_f3),
               ({'bindings':[],'program':['restore',0,1]},validate_f3),
               ({'bindings':[],'program':['ref',0]},validate_f3)]
    baseline = generate_f3()
    for category in ('boundary/one_hundred_nodes', 'boundary/depth',
                     'boundary/three_hundred_evaluations', 'boundary/positive_ten_thousand'):
        candidates = [c for c in baseline if c['category'] == category]
        a = deepcopy(candidates[-1]['argument'])
        a['program'] = ['add', a['program'], 1]
        invalid.append((a, validate_f3))
    a = {'bindings': [[name, ['ref', 0]] for name in 'abcdef'],
         'program': ['seq', ['ref', 0], ['seq', ['ref', 0], ['seq', ['ref', 0], 0]]]}
    invalid.append((a, validate_f3))
    for e in (['add', ['snap'], 0], ['if', ['snap'], 0, 0],
              ['ref', ['snap']], ['set', ['ref', 0], ['snap']],
              ['let', 's', ['snap'], ['let', 'c', ['ref', 0],
               ['restore', _v('s'), ['get', _v('c')]]]],
              ['if', 0, _v('missing'), 0], ['let', 'X', 0, 0]):
        invalid.append(({'bindings': [], 'program': e}, validate_f3))
    a = _route_arg(); a['vehicle']['capacity'] = True; invalid.append((a,validate_f4))
    a = _route_arg(); a['time'][0][0] = 1; invalid.append((a,validate_f4))
    for a, validator in invalid:
        try: validator(a)
        except ValueError: counts['invalid_rejections'] += 1
        else: raise AssertionError(('accepted invalid input',a))
    return counts


if __name__ == '__main__':
    print(verify_oracles())
    print({'F3': len(generate_f3()), 'F4': len(generate_f4())})
