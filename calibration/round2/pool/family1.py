"""Bounded network contracts and deterministic finite case sets."""
import itertools
import random
import textwrap

COMMON = '''def _opt(n, edges, target=None):
    target = tuple(target or [0] * n)
    states = {(0,) * n: 0}
    for u, v, low, high, cost in edges:
        nxt = {}
        for balance, value in states.items():
            for flow in range(low, high + 1):
                b = list(balance)
                b[u] += flow
                b[v] -= flow
                key = tuple(b)
                val = value + flow * cost
                if key not in nxt or val < nxt[key]:
                    nxt[key] = val
        states = nxt
    return states.get(target)
'''
VERSION = COMMON + '''
def versioned_circulation_costs(data):
    snapshots = [[list(e) for e in data['arcs']]]
    answers = [_opt(data['n'], snapshots[0])]
    for parent, index, low, high, cost in data['versions']:
        edges = [e[:] for e in snapshots[parent]]
        edges[index][2:] = [low, high, cost]
        snapshots.append(edges)
        answers.append(_opt(data['n'], edges))
    return answers
'''
FAILURE = COMMON + '''
def single_failure_costs(data):
    result = []
    for disabled in range(len(data['arcs'])):
        edges = [e[:] for e in data['arcs']]
        edges[disabled][2:4] = [0, 0]
        result.append(_opt(data['n'], edges))
    return result
'''
INVENTORY = COMMON + '''
def inventory_transfer_cost(data):
    n, days = data['n'], data['days']
    edges = []
    for day in range(days - 1):
        for place in range(n):
            edges.append([day*n+place, (day+1)*n+place, 0,
                          data['carry_capacity'][day][place], data['storage_cost'][day][place]])
    for day, u, v, cap, cost in data['transfers']:
        edges.append([day*n+u, day*n+v, 0, cap, cost])
    target = [data['supply'][d][p] - data['demand'][d][p]
              for d in range(days) for p in range(n)]
    return _opt(n * days, edges, target)
'''


def flow_oracle(n, edges, target=None):
    """Independent Cartesian flow assignment oracle, including self-loops."""
    target = target or [0] * n
    best = None
    for values in itertools.product(*(range(e[2], e[3] + 1) for e in edges)):
        outgoing = [sum(f for f, e in zip(values, edges) if e[0] == u) for u in range(n)]
        incoming = [sum(f for f, e in zip(values, edges) if e[1] == u) for u in range(n)]
        if [a-b for a, b in zip(outgoing, incoming)] == target:
            cost = sum(f * e[4] for f, e in zip(values, edges))
            best = cost if best is None else min(best, cost)
    return best


def oracle(name, data):
    if name == 'versioned_circulation_costs':
        result = []
        for version in range(len(data['versions']) + 1):
            edges = [e[:] for e in data['arcs']]
            lineage = []
            cursor = version
            while cursor:
                change = data['versions'][cursor - 1]
                lineage.append(change)
                cursor = change[0]
            for _, i, low, high, cost in reversed(lineage):
                edges[i] = edges[i][:2] + [low, high, cost]
            result.append(flow_oracle(data['n'], edges))
        return result
    if name == 'single_failure_costs':
        return [flow_oracle(data['n'], [e if i != j else e[:2]+[0, 0, e[4]]
                                      for i, e in enumerate(data['arcs'])])
                for j in range(len(data['arcs']))]
    n, days = data['n'], data['days']
    edges = [[d*n+p, (d+1)*n+p, 0, data['carry_capacity'][d][p], data['storage_cost'][d][p]]
             for d in range(days-1) for p in range(n)]
    edges += [[d*n+u, d*n+v, 0, cap, cost] for d, u, v, cap, cost in data['transfers']]
    return flow_oracle(n*days, edges, [s-t for ss, tt in zip(data['supply'], data['demand']) for s, t in zip(ss, tt)])


NETWORK_CLAUSES = [
    'The argument is a dictionary with exactly the specified keys; all numeric fields are integers, not booleans.',
    'The field n is between 1 and 4 and names vertices 0 through n-1; arcs is a list of zero through six lists [u, v, lower, upper, cost].',
    'Each arc has endpoints in 0 through n-1, 0 <= lower <= upper <= 2, and -5 <= cost <= 5; parallel arcs and self-loops are allowed and list positions identify distinct arcs.',
    'A feasible circulation assigns an integer flow to every arc between its inclusive lower and upper bounds, with total incoming flow equal to total outgoing flow at every vertex.',
    'Its total cost is the sum over arcs of flow times cost; the optimum is the minimum total cost among feasible circulations, or None if none exists.',
]


def make_tasks():
    rng = random.Random(12021)
    version_inputs = [
        {'n': 1, 'arcs': [], 'versions': []},
        {'n': 2, 'arcs': [[0,1,1,2,3],[1,0,0,2,-5]], 'versions': [[0,1,0,0,-5],[0,0,0,2,3],[1,0,0,0,3],[2,1,1,2,-5]]},
        {'n': 1, 'arcs': [[0,0,1,2,-3]], 'versions': [[0,0,0,2,4],[0,0,2,2,-5]]},
        {'n': 3, 'arcs': [[0,1,1,1,2]], 'versions': [[0,0,0,1,-2]]},
    ]
    failure_inputs = [
        {'n': 1, 'arcs': []},
        {'n': 2, 'arcs': [[0,1,1,2,3],[1,0,1,2,-5]]},
        {'n': 2, 'arcs': [[0,1,1,1,2],[0,1,0,2,-3],[1,0,1,2,0]]},
        {'n': 1, 'arcs': [[0,0,2,2,-5],[0,0,0,2,-3]]},
    ]
    for _ in range(16):
        n = rng.randint(1,4)
        edges = []
        for j in range(rng.randint(1,6)):
            low = rng.randint(0,1)
            edges.append([rng.randrange(n),rng.randrange(n),low,rng.randint(low,2),rng.randint(-5,5)])
        failure_inputs.append({'n': n, 'arcs': edges})
        versions = []
        for j in range(rng.randint(2,5)):
            low = rng.randint(0,1)
            versions.append([rng.randrange(j+1),rng.randrange(len(edges)),low,rng.randint(low,2),rng.randint(-5,5)])
        version_inputs.append({'n': n, 'arcs': edges, 'versions': versions})
    inventory_inputs = [
        {'n':1,'days':1,'supply':[[0]],'demand':[[0]],'carry_capacity':[],'storage_cost':[],'transfers':[]},
        {'n':1,'days':2,'supply':[[2],[0]],'demand':[[0],[2]],'carry_capacity':[[2]],'storage_cost':[[3]],'transfers':[]},
        {'n':1,'days':2,'supply':[[0],[1]],'demand':[[1],[0]],'carry_capacity':[[2]],'storage_cost':[[-2]],'transfers':[]},
        {'n':2,'days':2,'supply':[[1,0],[0,0]],'demand':[[0,0],[0,1]],'carry_capacity':[[1,1]],'storage_cost':[[3,-2]],'transfers':[[0,0,1,1,1],[1,0,1,1,2]]},
        {'n':2,'days':1,'supply':[[0,0]],'demand':[[0,0]],'carry_capacity':[],'storage_cost':[],'transfers':[[0,0,1,2,-3],[0,1,0,2,1]]},
    ]
    for _ in range(15):
        n, days = rng.randint(1,2), rng.randint(1,3)
        data = {'n':n,'days':days,
            'supply':[[rng.randint(0,2) for p in range(n)] for d in range(days)],
            'demand':[[rng.randint(0,2) for p in range(n)] for d in range(days)],
            'carry_capacity':[[rng.randint(0,2) for p in range(n)] for d in range(days-1)],
            'storage_cost':[[rng.randint(-3,3) for p in range(n)] for d in range(days-1)],
            'transfers':[[rng.randrange(days),rng.randrange(n),rng.randrange(n),rng.randint(0,2),rng.randint(-3,3)] for j in range(rng.randint(0,3))]}
        if _ < 8:
            data['supply'] = [[0]*n for d in range(days)]
            data['demand'] = [[0]*n for d in range(days)]
            if days > 1:
                place = rng.randrange(n)
                data['supply'][0][place] = 1
                data['demand'][-1][place] = 1
                for row in data['carry_capacity']:
                    row[place] = max(1, row[place])
        inventory_inputs.append(data)
    specs = [
        ('versioned_circulation_costs', 'development', VERSION, version_inputs, NETWORK_CLAUSES + [
            'The dictionary keys are n, arcs, and versions; versions is a list of zero through eight lists [parent, arc_index, lower, upper, cost].',
            'The original arcs define version 0; the entry at zero-based index j of versions defines version j+1 by copying version parent, where 0 <= parent <= j, and replacing only the bounds and cost of the indexed arc.',
            'Every arc_index is a valid position in arcs, and every replacement obeys the same bounds and cost restrictions as an original arc; versions is empty if arcs is empty.',
            'Return a new list of integers or None, containing the circulation optimum for version 0 and then each version in entry order; infeasible versions may have feasible descendants.',
            'Do not modify the argument or any nested object.']),
        ('inventory_transfer_cost','heldout',INVENTORY,inventory_inputs,[
            'The argument is a dictionary with exactly n, days, supply, demand, carry_capacity, storage_cost, and transfers; all numeric fields are integers, not booleans.',
            'There are n locations, with 1 <= n <= 2, and days dates numbered 0 through days-1, with 1 <= days <= 3.',
            'Supply and demand are days-by-n lists of integers from 0 through 2; every supply unit must be used and every demand unit must be satisfied at its specified location and date.',
            'Carry_capacity and storage_cost are (days-1)-by-n lists; each capacity is 0 through 2 and each cost is -3 through 3.',
            'A carry flow at location p from date d to date d+1 is an integer between zero and carry_capacity[d][p], and costs storage_cost[d][p] per unit.',
            'Transfers contains zero through three lists [date, u, v, capacity, cost], with valid date and location indices, capacity 0 through 2, and cost -3 through 3; duplicates and self-loops are allowed and each entry has its own capacity.',
            'A transfer sends an integer between zero and capacity units from u to v on its date at its cost per unit; incoming transfers may supply outgoing transfers on the same date, including circulations.',
            'At each location and date, supply plus incoming transfers plus carry from the preceding date must equal demand plus outgoing transfers plus carry to the following date; there is no initial or final inventory beyond these flows and no disposal.',
            'Return the minimum total carry and transfer cost as an integer, or None if the equalities cannot all be met.',
            'Do not modify the argument or any nested object.']),
        ('single_failure_costs','heldout',FAILURE,failure_inputs,NETWORK_CLAUSES + [
            'The dictionary keys are exactly n and arcs.',
            'For each position i in arcs, form a separate scenario from the original arcs by setting both bounds of arc i to zero, even if its original lower bound was positive; retain every other bound and cost.',
            'Return a new list of integers or None giving each separate scenario optimum in arc order; return an empty list when arcs is empty.',
            'Do not modify the argument or any nested object.'])]
    return [dict(id=name,function=name,family='F1',role=role,clauses=clauses,
                 cases=[[data,oracle(name,data)] for data in inputs],reference=textwrap.dedent(source))
            for name,role,source,inputs,clauses in specs]
