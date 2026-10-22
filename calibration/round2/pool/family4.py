"""Capacity, precedence, time-window and monetary-cost transport contracts."""
import itertools
import random

REFERENCE = r'''
def _route(arg, vehicle, indices):
    requests = arg['requests']
    best = None
    def visit(node, time, load, picked, done, cost):
        nonlocal best
        if len(done) == len(indices):
            if time + arg['time'][node][vehicle['end']] <= vehicle['deadline']:
                total = cost + arg['cost'][node][vehicle['end']]
                if best is None or total < best:
                    best = total
            return
        for i in indices:
            r = requests[i]
            if i in done:
                continue
            delivery = i in picked
            target = r['drop'] if delivery else r['pick']
            window = r['dw'] if delivery else r['pw']
            newload = load + (-r['load'] if delivery else r['load'])
            start = max(time + arg['time'][node][target], window[0])
            if newload > vehicle['capacity'] or start > window[1]:
                continue
            duration = r['ds'] if delivery else r['ps']
            visit(target, start + duration, newload, picked | {i},
                  done | {i} if delivery else done, cost + arg['cost'][node][target])
    visit(vehicle['start'], vehicle['release'], 0, set(), set(), 0)
    return best

def pickup_delivery_cost(arg):
    return _route(arg, arg['vehicle'], list(range(len(arg['requests']))))

def fleet_assignment_cost(arg):
    from itertools import product
    best = None
    vehicles = arg['vehicles']
    for assignment in product(range(len(vehicles)), repeat=len(arg['requests'])):
        total = 0
        for j, vehicle in enumerate(vehicles):
            cost = _route(arg, vehicle, [i for i, v in enumerate(assignment) if v == j])
            if cost is None:
                break
            total += cost
        else:
            if best is None or total < best:
                best = total
    return best

def reward_delivery_selection(arg):
    best = 0
    for mask in range(1 << len(arg['requests'])):
        indices = [i for i in range(len(arg['requests'])) if mask >> i & 1]
        cost = _route(arg, arg['vehicle'], indices)
        if cost is not None and cost <= arg['budget']:
            best = max(best, sum(arg['requests'][i]['reward'] for i in indices))
    return best
'''

COMMON = [
    "All values use exact built-in JSON types; integers exclude booleans. Preserve the input. Arg contains time, cost, requests and the additional fields stated below, with no others. Time and cost are square matrices of size N, 1 <= N <= 9; entries are integers from 0 to 20 with zero diagonals. Matrices are directed and need not satisfy a triangle inequality. Entries give direct travel duration and direct monetary cost; they are independent quantities.",
    "Requests is an ordered list of 0 to 4 distinct request occurrences (identical objects still count separately). Each request has pick and drop node indices in [0,N), load in [1,3], pw and dw as [earliest,latest] service-start windows with integer 0 <= earliest <= latest <= 80, and ps and ds as pickup and delivery service durations in [0,5]. Only the reward contract additionally has reward, an integer from 0 to 30. Pickup and delivery nodes may coincide, including with vehicle endpoints.",
    "Each vehicle object has exactly start, end (node indices), capacity (integer 1 to 5), release and deadline (integers with 0 <= release <= deadline <= 100). It starts empty at start at release, visits exactly one pickup and one delivery event for each request assigned to it, and finishes empty at end by deadline inclusive. Each pickup must precede its own delivery, even at identical nodes. No unassigned events, extra waypoint visits, request transfers, or split loads are allowed.",
    "For each event, travel directly from the previous node, then start service at the maximum of arrival time and its window earliest. Start must be at most window latest inclusive. Waiting is permitted and has no monetary cost. Service finishes after ps or ds time units; the next trip starts then. Load changes by +load at pickup and -load at delivery and must stay between zero and capacity inclusive. Finish time includes direct travel from the last event to end; an empty route travels directly from start to end. Extra waiting cannot improve feasibility and is allowed only if all these constraints remain satisfied.",
    "Route monetary cost is the sum of cost entries for every traveled leg, including the initial leg and the final leg to end, and excluding waiting and service durations. A correct return uses an integer optimum, or null exactly where specified. No invalid-input behavior is required."
]


def _oracle(arg, vehicle, indices):
    """Independent full event-permutation oracle, separate from reference DFS."""
    best = None
    events = [(i, delivery) for i in indices for delivery in (False, True)]
    for order in itertools.permutations(events):
        node, time, load, cost = vehicle['start'], vehicle['release'], 0, 0
        picked = set()
        for i, delivery in order:
            r = arg['requests'][i]
            if delivery and i not in picked:
                break
            target, window, service = (r['drop'], r['dw'], r['ds']) if delivery else (r['pick'], r['pw'], r['ps'])
            time = max(time + arg['time'][node][target], window[0])
            load += -r['load'] if delivery else r['load']
            if not 0 <= load <= vehicle['capacity'] or time > window[1]:
                break
            time += service
            cost += arg['cost'][node][target]
            node = target
            picked.add(i)
        else:
            if time + arg['time'][node][vehicle['end']] <= vehicle['deadline']:
                cost += arg['cost'][node][vehicle['end']]
                best = cost if best is None else min(best, cost)
    return best


def _expected(arg, mode):
    n = len(arg['requests'])
    if mode == 'single':
        return _oracle(arg, arg['vehicle'], range(n))
    if mode == 'reward':
        values = [0]
        for subset in itertools.chain.from_iterable(itertools.combinations(range(n), k) for k in range(n + 1)):
            cost = _oracle(arg, arg['vehicle'], subset)
            if cost is not None and cost <= arg['budget']:
                values.append(sum(arg['requests'][i]['reward'] for i in subset))
        return max(values)
    totals = []
    for assignment in itertools.product(range(len(arg['vehicles'])), repeat=n):
        costs = [_oracle(arg, v, [i for i in range(n) if assignment[i] == j]) for j, v in enumerate(arg['vehicles'])]
        if all(c is not None for c in costs):
            totals.append(sum(costs))
    return min(totals) if totals else None


def make_tasks():
    rng = random.Random(403)
    base = []
    # Deliberately tight deterministic schedules plus independent random matrices.
    for i in range(16):
        n = 3
        time = [[0 if a == b else rng.randint(1, 4) for b in range(n)] for a in range(n)]
        cost = [[0 if a == b else rng.randint(0, 8) for b in range(n)] for a in range(n)]
        requests = []
        for j in range(i % 3):
            requests.append(dict(pick=j, drop=(j + 1) % n, load=1 + (i + j) % 3,
                                 pw=[i % 4, 6 + i % 5], dw=[3, 9 + i % 9], ps=i % 3, ds=j))
        v = dict(start=0, end=2, capacity=1 + i % 5, release=i % 2, deadline=10 + i)
        base.append(dict(time=time, cost=cost, requests=requests, vehicle=v))
    # Boundary goldens: exact deadline, service-start latest, waiting, empty direct leg.
    base.extend([
        dict(time=[[0,2],[3,0]],cost=[[0,7],[4,0]],requests=[],vehicle=dict(start=0,end=1,capacity=1,release=1,deadline=3)),
        dict(time=[[0,1],[1,0]],cost=[[0,2],[5,0]],requests=[dict(pick=0,drop=1,load=1,pw=[5,5],dw=[8,8],ps=2,ds=1)],vehicle=dict(start=0,end=0,capacity=1,release=0,deadline=10)),
        dict(time=[[0]],cost=[[0]],requests=[dict(pick=0,drop=0,load=2,pw=[0,0],dw=[0,0],ps=0,ds=0)],vehicle=dict(start=0,end=0,capacity=1,release=0,deadline=0)),
        dict(time=[[0,1],[1,0]],cost=[[0,3],[2,0]],requests=[dict(pick=0,drop=1,load=1,pw=[0,2],dw=[1,3],ps=0,ds=0)]*4,vehicle=dict(start=0,end=0,capacity=4,release=0,deadline=4)),
    ])
    # Waiting at pickup forces delivery beyond its latest service-start time.
    base.insert(0, dict(time=[[0,1],[1,0]],cost=[[0,2],[3,0]],requests=[dict(pick=0,drop=1,load=1,pw=[5,5],dw=[0,3],ps=0,ds=0)],vehicle=dict(start=0,end=0,capacity=1,release=0,deadline=20)))
    base.insert(0, dict(time=[[0,1],[1,0]],cost=[[0,2],[3,0]],requests=[dict(pick=0,drop=1,load=1,pw=[0,0],dw=[1,2],ps=3,ds=0)],vehicle=dict(start=0,end=0,capacity=1,release=0,deadline=20)))
    single, fleet, reward = [], [], []
    import copy
    for i, b in enumerate(base):
        single.append([copy.deepcopy(b), _expected(b, 'single')])
        f = copy.deepcopy(b)
        vehicle = f.pop('vehicle')
        other = dict(vehicle, start=1 if len(b['time']) > 1 else 0, capacity=5, deadline=30)
        f['vehicles'] = [vehicle, other]
        fleet.append([f, _expected(f, 'fleet')])
        r = copy.deepcopy(b)
        r['budget'] = 5 if i == len(base) - 1 else i % 14
        for j, request in enumerate(r['requests']):
            request['reward'] = (i + j * 7) % 19
        reward.append([r, _expected(r, 'reward')])
    extra = [
        ("pickup_delivery_cost", "development", "Arg additionally has vehicle. Serve every request with that vehicle. Return the minimum feasible route monetary cost, or null if no feasible route exists.", single),
        ("fleet_assignment_cost", "heldout", "Arg additionally has vehicles, a list of 1 to 3 vehicle objects. Assign every request to exactly one vehicle and serve it entirely on that vehicle. Every vehicle, even one assigned no requests, must perform a feasible route from its start to end. Minimize the sum of all vehicle route costs. Return that integer minimum, or null if no assignment and schedule is feasible.", fleet),
        ("reward_delivery_selection", "heldout", "Arg additionally has vehicle and budget, an integer from 0 to 100. Each request also has reward. Choose any subset of requests and serve exactly that subset with the vehicle on a feasible route costing at most budget inclusive. Return the greatest total reward of served requests, an integer. If no subset has a feasible route within budget, return 0; zero is also the value of any feasible empty subset. Reward is earned only after both events complete. There is no secondary cost or request-count objective.", reward),
    ]
    return [dict(id=name,function=name,family='F4',role=role,clauses=["Implement " + name + "(arg). " + clause] + COMMON,cases=cases,reference=REFERENCE) for name,role,clause,cases in extra]
