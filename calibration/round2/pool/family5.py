"""Finite resource walks and games; no collection is performed here."""
import random

COMMON = [
    'The function takes one dictionary a and must not mutate it. All numbers are exact integers (not booleans). Keys are n, edges, start, goal, state, delta, accept, budget; budget_route_strategy additionally has owners. There are no other keys.',
    'n is 1..8. start and goal are vertex indices 0..n-1. delta is a rectangular list with 1..5 rows and 1..3 columns, each entry a state index 0..len(delta)-1; state is an initial state index. accept is a list of distinct state indices, possibly empty.',
    'edges is a list of 0..20 lists [source, destination, label, resource, cost]. Vertices are in 0..n-1, label is a column index in delta, resource is 1..8, cost is -20..20. budget is 0..24. Parallel entries, self loops, and repeated entries are legal.',
    'A walk starts at start in state with resource use zero and cost zero. Taking an edge at the current vertex adds its resource and cost, moves to its destination, and replaces state q by delta[q][label]. Total resource may not exceed budget. An accepted ending has vertex goal and state in accept. The empty walk is allowed. Reaching an accepted ending does not prevent taking further edges.'
]
SOURCE = '''from functools import lru_cache

def FUNCTION(a):
    n = a['n']; budget = a['budget']; accept = set(a['accept'])
    outgoing = [[] for _ in range(n)]
    for u,v,label,r,c in a['edges']:
        outgoing[u].append((v,label,r,c))
    KIND
'''
COST = '''@lru_cache(None)
    def solve(v,q,left):
        values = [0] if v == a['goal'] and q in accept else []
        for w,label,r,c in outgoing[v]:
            if r <= left:
                sub = solve(w,a['delta'][q][label],left-r)
                if sub is not None: values.append(c+sub)
        return min(values,default=None)
    return solve(a['start'],a['state'],budget)'''
COUNT = '''dp = [[[0]*len(a['delta']) for _ in range(n)] for _ in range(budget+1)]
    dp[0][a['start']][a['state']] = 1
    result = []
    for used in range(budget+1):
        result.append(sum(dp[used][a['goal']][q] for q in accept)%1000000007)
        for v in range(n):
            for q,value in enumerate(dp[used][v]):
                for w,label,r,c in outgoing[v]:
                    if used+r <= budget:
                        target = a['delta'][q][label]
                        dp[used+r][w][target] = (dp[used+r][w][target]+value)%1000000007
    return result'''
GAME = '''@lru_cache(None)
    def solve(v,q,left):
        values = [0] if v == a['goal'] and q in accept else []
        for w,label,r,c in outgoing[v]:
            if r <= left:
                sub = solve(w,a['delta'][q][label],left-r)
                values.append(None if sub is None else c+sub)
        if a['owners'][v] == 1:
            return None if not values or None in values else max(values)
        return min((x for x in values if x is not None),default=None)
    return solve(a['start'],a['state'],budget)'''


def inputs():
    cases = [
        dict(n=1,edges=[],start=0,goal=0,state=0,delta=[[0]],accept=[0],budget=0),
        dict(n=1,edges=[],start=0,goal=0,state=0,delta=[[0]],accept=[],budget=2),
        dict(n=2,edges=[[0,1,0,1,3],[0,1,0,1,3]],start=0,goal=1,state=0,delta=[[0]],accept=[0],budget=1),
        dict(n=2,edges=[[0,1,0,1,3],[0,0,0,1,-5]],start=0,goal=1,state=0,delta=[[0]],accept=[0],budget=3),
        dict(n=1,edges=[[0,0,0,1,-2]],start=0,goal=0,state=0,delta=[[1],[0]],accept=[1],budget=4),
        dict(n=2,edges=[[0,1,0,1,2],[0,0,0,1,9]],start=0,goal=1,state=0,delta=[[0]],accept=[0],budget=1),
    ]
    rng=random.Random(5137)
    for _ in range(12):
        n=rng.randint(1,3); states=rng.randint(1,3)
        cases.append(dict(n=n, edges=[[rng.randrange(n),rng.randrange(n),rng.randrange(2),rng.randint(1,3),rng.randint(-5,5)] for _ in range(rng.randint(1,5))],start=rng.randrange(n),goal=rng.randrange(n),state=rng.randrange(states),delta=[[rng.randrange(states) for _ in range(2)] for _ in range(states)],accept=[q for q in range(states) if rng.randrange(2)],budget=rng.randrange(7)))
    return cases


GOLDENS = {'automaton_route_cost': [0, None, 3, -7, -6, 2, None, None, None, None, 0, None, None, -1, -3, -2, None, None], 'accepted_walk_counts': [[1], [0, 0, 0], [0, 2], [0, 1, 1, 1], [0, 1, 0, 1, 0], [0, 1], [0, 0, 0], [0, 0, 0, 0], [0], [0, 0, 0, 0, 0, 0], [1], [0, 0, 0, 0, 0], [0, 0, 0], [1, 0, 1, 1], [0, 0, 1], [1, 1, 2, 5], [0], [0, 0, 0, 0, 0, 0, 0]], 'budget_route_strategy': [0, None, 3, None, -6, None, None, None, None, None, 0, None, None, 1, -3, 15, None, None]}


def make_tasks():
    specs = [
        ('automaton_route_cost','development',COST,['Return the minimum cost of any accepted walk using at most budget resource, as an integer, or None if no accepted walk exists.']),
        ('accepted_walk_counts','heldout',COUNT,['Return a list of budget+1 integers. Entry b is the number of accepted walks with total resource exactly b, modulo 1000000007. Walks are distinguished by their ordered sequence of indices in edges, so repeated equal entries are distinct choices. Edge costs do not affect counts.']),
        ('budget_route_strategy','heldout',GAME,[
            'owners is a list of n integers, each 0 or 1. At a vertex owned by 0 the minimizing player chooses an action; at a vertex owned by 1 the adversary chooses an action. Both observe the complete history. Legal actions are taking any outgoing edge whose resource fits the remaining budget, and stopping if and only if the current ending is accepted. Stopping ends successfully with no additional cost. There is no stop action elsewhere.',
            'If there are no legal actions play ends unsuccessfully. All plays are finite because every edge spends positive resource. A strategy guarantees success only if every adversarial choice leads to successful stopping. Return None if the minimizing player has no strategy guaranteeing success; otherwise return the least possible worst-case total cost among its success-guaranteeing strategies, as an integer. At an adversarial accepted ending the adversary may choose an edge instead of stopping.'
        ])]
    tasks=[]
    for name,role,body,extra in specs:
        source=SOURCE.replace('FUNCTION',name).replace('KIND',body)
        ns={};exec(source,ns)
        args=inputs()
        if name=='budget_route_strategy':
            for i,a in enumerate(args): a['owners']=[(i+v)%2 for v in range(a['n'])]
            args[5]['owners']=[1,0]
        tasks.append(dict(id=name,function=name,family='F5',role=role,clauses=COMMON+extra,cases=[[a,want] for a,want in zip(args,GOLDENS[name])],reference=source))
    # Boundary cases have closed-form independent expectations.
    for task in tasks:
        a = dict(n=8, edges=[[0,7,0,8,-20]], start=0, goal=7, state=0,
                 delta=[[4,0,0],[0,0,0],[0,0,0],[0,0,0],[4,4,4]], accept=[4], budget=24)
        if task['function']=='budget_route_strategy': a['owners']=[0]*8
        want = [0]*25 if task['function']=='accepted_walk_counts' else -20
        if isinstance(want,list): want[8]=1
        task['cases'].append([a,want])
    a=dict(n=1,edges=[[0,0,0,1,0] for _ in range(20)],start=0,goal=0,state=0,delta=[[0]],accept=[0],budget=8)
    tasks[1]['cases'].append([a,[pow(20,b,1000000007) for b in range(9)]])
    return tasks
