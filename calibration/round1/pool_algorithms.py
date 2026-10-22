"""Deterministic hard algorithm contracts, with no candidate collection.

Domains are explicitly bounded in the prompts. Ground truth uses exhaustive
flow-vector enumeration and incoming-edge tree enumeration for small graphs;
edit-script BFS for short strings; literals and planted optima for large graphs.
Additional medium edit cases use the unrestricted distance reference, checked
against the independent BFS on the small domain. Large planted distance cases
have disjoint alphabets (length lower bound), equal strings, or adjacent swaps
with unique symbols (a matching edit lower bound). References are standalone
stdlib source; running untrusted candidates belongs to the root sandbox runner.
"""
import inspect
import itertools
import pathlib
import random
from collections import deque


def distance(arg):
    a, b = arg['a'], arg['b']
    n, m = len(a), len(b)
    big = n + m
    d = [[0] * (m + 2) for _ in range(n + 2)]
    d[0][0] = big
    for i in range(n + 1):
        d[i + 1][0], d[i + 1][1] = big, i
    for j in range(m + 1):
        d[0][j + 1], d[1][j + 1] = big, j
    last = {}
    for i in range(1, n + 1):
        match = 0
        for j in range(1, m + 1):
            i1, j1 = last.get(b[j - 1], 0), match
            cost = 1
            if a[i - 1] == b[j - 1]:
                cost, match = 0, j
            d[i + 1][j + 1] = min(d[i][j] + cost, d[i + 1][j] + 1,
                                     d[i][j + 1] + 1,
                                     d[i1][j1] + i - i1 - 1 + 1 + j - j1 - 1)
        last[a[i - 1]] = i
    return d[n + 1][m + 1]


def circulation(arg):
    n = arg['n']
    arcs = arg['arcs']
    # First obtain any feasible bounded circulation via an auxiliary max flow.
    edges = []
    adjacency = [[] for _ in range(n + 2)]

    def add(u, v, cap, cost):
        k = len(edges)
        edges.extend([[u, v, cap, cost], [v, u, 0, -cost]])
        adjacency[u].append(k)
        adjacency[v].append(k ^ 1)
        return k

    balance = [0] * n
    original = []
    answer = 0
    for u, v, lo, hi, cost in arcs:
        original.append(add(u, v, hi - lo, cost))
        balance[u] -= lo
        balance[v] += lo
        answer += lo * cost
    required = 0
    for v, amount in enumerate(balance):
        if amount > 0:
            add(n, v, amount, 0)
            required += amount
        elif amount < 0:
            add(v, n + 1, -amount, 0)
    sent = 0
    while sent < required:
        parent = [-1] * (n + 2)
        parent[n] = -2
        queue = [n]
        for u in queue:
            for k in adjacency[u]:
                _, v, cap, _ = edges[k]
                if cap and parent[v] == -1:
                    parent[v] = k
                    queue.append(v)
            if parent[n + 1] != -1:
                break
        if parent[n + 1] == -1:
            return None
        amount = required - sent
        v = n + 1
        while v != n:
            k = parent[v]
            amount = min(amount, edges[k][2])
            v = edges[k][0]
        v = n + 1
        while v != n:
            k = parent[v]
            edges[k][2] -= amount
            edges[k ^ 1][2] += amount
            answer += amount * edges[k][3]
            v = edges[k][0]
        sent += amount
    # A feasible circulation is optimal iff its residual graph has no negative cycle.
    residual = [k for k, (u, v, _, _) in enumerate(edges) if u < n and v < n]
    while True:
        dist, parent = [0] * n, [-1] * n
        changed = -1
        for _ in range(n):
            changed = -1
            for k in residual:
                u, v, cap, cost = edges[k]
                if cap and dist[v] > dist[u] + cost:
                    dist[v], parent[v], changed = dist[u] + cost, k, v
            if changed == -1:
                break
        if changed == -1:
            return answer
        v = changed
        for _ in range(n):
            v = edges[parent[v]][0]
        start, cycle = v, []
        while True:
            k = parent[v]
            cycle.append(k)
            v = edges[k][0]
            if v == start:
                break
        amount = min(edges[k][2] for k in cycle)
        for k in cycle:
            edges[k][2] -= amount
            edges[k ^ 1][2] += amount
            answer += amount * edges[k][3]


def arborescence(arg):
    n, root = arg['n'], arg['root']
    edges = [tuple(e) for e in arg['edges']]
    total = 0
    while True:
        incoming = [float('inf')] * n
        predecessor = [-1] * n
        for u, v, cost in edges:
            if u != v and v != root and cost < incoming[v]:
                incoming[v], predecessor[v] = cost, u
        incoming[root] = 0
        if any(x == float('inf') for x in incoming):
            return None
        total += sum(incoming)
        group, seen = [-1] * n, [-1] * n
        count = 0
        for v in range(n):
            u = v
            while seen[u] != v and group[u] == -1 and u != root:
                seen[u] = v
                u = predecessor[u]
            if u != root and group[u] == -1:
                w = predecessor[u]
                group[u] = count
                while w != u:
                    group[w] = count
                    w = predecessor[w]
                count += 1
        if count == 0:
            return total
        for v in range(n):
            if group[v] == -1:
                group[v], count = count, count + 1
        edges = [(group[u], group[v], cost - incoming[v])
                 for u, v, cost in edges if group[u] != group[v]]
        root, n = group[root], count


def brute_flow(arg):
    best = None
    for flows in itertools.product(*(range(e[2], e[3] + 1) for e in arg['arcs'])):
        balance, cost = [0] * arg['n'], 0
        for (u, v, _, _, c), f in zip(arg['arcs'], flows):
            balance[u] -= f
            balance[v] += f
            cost += c * f
        if not any(balance) and (best is None or cost < best):
            best = cost
    return best


def brute_tree(arg):
    vertices = [v for v in range(arg['n']) if v != arg['root']]
    options = [[e for e in arg['edges'] if e[1] == v and e[0] != v] for v in vertices]
    best = None
    for chosen in itertools.product(*options):
        reached = {arg['root']}
        while True:
            after = reached | {v for u, v, _ in chosen if u in reached}
            if after == reached:
                break
            reached = after
        if len(reached) == arg['n']:
            cost = sum(e[2] for e in chosen)
            if best is None or cost < best:
                best = cost
    return best


def brute_distance(a, b):
    if a == b:
        return 0
    alphabet = sorted(set(a + b))
    queue, seen = deque([(a, 0)]), {a}
    bound = max(len(a), len(b)) + 1
    while queue:
        word, depth = queue.popleft()
        candidates = set()
        for i in range(len(word)):
            candidates.add(word[:i] + word[i + 1:])
            for ch in alphabet:
                candidates.add(word[:i] + ch + word[i + 1:])
        for i in range(len(word) - 1):
            candidates.add(word[:i] + word[i + 1] + word[i] + word[i + 2:])
        if len(word) < bound:
            for i in range(len(word) + 1):
                for ch in alphabet:
                    candidates.add(word[:i] + ch + word[i:])
        if b in candidates:
            return depth + 1
        for word2 in candidates - seen:
            seen.add(word2)
            queue.append((word2, depth + 1))


def _source(function, name):
    return inspect.getsource(function).replace('def ' + function.__name__ + '(', 'def ' + name + '(', 1)


def make_tasks():
    rng = random.Random(320261022)
    edits = [[{'a': a, 'b': b}, value] for a, b, value in [
        ('', '', 0), ('', 'abc', 3), ('abc', '', 3), ('CA', 'ABC', 2),
        ('ABC', 'CA', 2), ('ab', 'ba', 1), ('aab', 'aba', 1),
        ('abcdef', 'abcfde', 2), ('é🙂', '🙂é', 1), ('e\u0301', 'é', 2),
        ('abca', 'acba', 1), ('same', 'same', 0)]]
    words = ['a', 'b', 'aa', 'ab', 'ba', 'bb', 'aba', 'bab']
    for _ in range(12):
        a, b = rng.choice(words), rng.choice(words)
        edits.append([{'a': a, 'b': b}, brute_distance(a, b)])
    for length in (80, 120, 180):
        edits.append([{'a': 'a' * length, 'b': 'b' * length}, length])
        edits.append([{'a': 'ab' * (length // 2), 'b': 'ab' * (length // 2)}, 0])
    unique = ''.join(chr(0x400 + i) for i in range(180))
    edits.append([{'a': unique, 'b': ''.join(unique[i + 1] + unique[i] for i in range(0, 180, 2))}, 90])
    for _ in range(3):
        a = ''.join(rng.choice('abcde') for _ in range(100))
        b = ''.join(rng.choice('abcde') for _ in range(95))
        edits.append([{'a': a, 'b': b}, distance({'a': a, 'b': b})])

    flows = []
    literals = [({'n': 1, 'arcs': []}, 0),
                ({'n': 1, 'arcs': [[0, 0, 2, 7, -3]]}, -21),
                ({'n': 2, 'arcs': [[0, 1, 1, 2, 0]]}, None),
                ({'n': 2, 'arcs': [[0, 1, 0, 4, -5], [1, 0, 0, 3, 2]]}, -9),
                ({'n': 3, 'arcs': [[1, 2, 0, 4, -3], [2, 1, 0, 4, 1]]}, -8),
                ({'n': 2, 'arcs': [[0, 1, 2, 2, 5], [1, 0, 2, 2, -1]]}, 8),
                ({'n': 2, 'arcs': [[0, 1, 0, 0, -100]]}, 0)]
    flows.extend([[a, e] for a, e in literals])
    for _ in range(20):
        n = rng.randrange(1, 5)
        arcs = []
        for _ in range(rng.randrange(1, 8)):
            lo = rng.randrange(2)
            arcs.append([rng.randrange(n), rng.randrange(n), lo, lo + rng.randrange(3), rng.randrange(-7, 8)])
        arg = {'n': n, 'arcs': arcs}
        flows.append([arg, brute_flow(arg)])
    # Independent planted optimum: disjoint directed rings have one common flow;
    # isolated forward arcs cannot carry circulation. Parallel rings share only vertices.
    for size, capacity in ((12, 999999), (18, 1000000), (30, 876543)):
        arcs, expected = [], 0
        for start in range(0, size, 3):
            costs = [-19, 4, 3]
            for i, cost in enumerate(costs):
                arcs.append([start + i, start + (i + 1) % 3, 1, capacity, cost])
            expected += capacity * sum(costs)
        for v in range(size):
            arcs.append([v, v, 0, capacity, -2])
            expected -= 2 * capacity
        flows.append([{'n': size, 'arcs': arcs}, expected])
    # Large acyclic graph: conservation forces every flow to zero.
    arcs = [[u, v, 0, 1000000, rng.randrange(-100, 101)] for u in range(30) for v in range(u + 1, 30)][:60]
    flows.append([{'n': 30, 'arcs': arcs}, 0])
    flows.append([{'n': 48, 'arcs': [[0, 1, 1, 1000000, -100]]}, None])

    # Potential certificate: every residual reduced cost at the planted flow is
    # nonnegative. Two overlapping saturated Hamiltonian cycles balance exactly;
    # every other arc is unused. Thus the planted cost is a global lower bound.
    for n in (18, 32, 48):
        potential = [rng.randrange(-15, 16) for _ in range(n)]
        arcs, expected = [], 0
        for capacity in (34567, 876543):
            order = list(range(n))
            rng.shuffle(order)
            for i, u in enumerate(order):
                v = order[(i + 1) % n]
                cost = potential[v] - potential[u] - rng.randrange(1, 21)
                arcs.append([u, v, rng.randrange(3), capacity, cost])
                expected += capacity * cost
        for _ in range(16):
            u, v = rng.randrange(n), rng.randrange(n)
            cost = potential[v] - potential[u] + rng.randrange(1, 21)
            arcs.append([u, v, 0, 1000000, cost])
        flows.append([{'n': n, 'arcs': arcs}, expected])

    trees = [[{'n': 1, 'root': 0, 'edges': [[0, 0, -99]]}, 0],
             [{'n': 3, 'root': 0, 'edges': [[1, 2, -4], [2, 1, -4]]}, None],
             [{'n': 3, 'root': 0, 'edges': [[0, 1, 5], [0, 2, 7], [1, 2, -4], [2, 1, -3]]}, 1],
             [{'n': 2, 'root': 1, 'edges': [[1, 0, 8], [1, 0, -2], [0, 0, -100], [0, 1, -100]]}, -2]]
    for _ in range(23):
        n = rng.randrange(2, 6)
        arg = {'n': n, 'root': rng.randrange(n), 'edges': [[rng.randrange(n), rng.randrange(n), rng.randrange(-20, 21)] for _ in range(rng.randrange(2, 13))]}
        trees.append([arg, brute_tree(arg)])
    # Connected moderate graphs checked by complete incoming-edge enumeration.
    for _ in range(4):
        n, root = 7, rng.randrange(7)
        edges = [[root, v, rng.randrange(-5, 25)] for v in range(n) if v != root]
        for v in range(n):
            if v != root:
                edges.extend([[rng.randrange(n), v, rng.randrange(-20, 6)] for _ in range(2)])
        arg = {'n': n, 'root': root, 'edges': edges}
        trees.append([arg, brute_tree(arg)])
    # An incoming-edge lower bound is attained by the planted outward star.
    for n in (30, 60, 100):
        root = n - 1
        edges, expected = [], 0
        for v in range(n - 1):
            cost = -1000 + v
            edges.append([root, v, cost])
            expected += cost
            if v % 10 == 0:
                edges.append([v, v, -1000000])
        for _ in range(20):
            edges.append([rng.randrange(n), rng.randrange(n), rng.randrange(1, 10001)])
        trees.append([{'n': n, 'root': root, 'edges': edges}, expected])
    # Strongly connected non-root cycle requires one paid entry; all other edges cost -7.
    for n in (40, 80):
        edges = [[v, 1 + v % (n - 1), -7] for v in range(1, n)]
        edges += [[0, v, 30 + v] for v in range(1, n)]
        trees.append([{'n': n, 'root': 0, 'edges': edges}, 31 - 7 * (n - 2)])
    result = []
    for name, function, cases in [('damerau_distance', distance, edits), ('min_cost_circulation', circulation, flows), ('minimum_arborescence', arborescence, trees)]:
        spec = (pathlib.Path(__file__).parent / 'prompts' / (name + '_B0.txt')).read_text()
        result.append({'id': name, 'function': name, 'spec': spec, 'cases': cases, 'reference': _source(function, name)})
    return result
