"""Bounded finite-state text contracts and standalone references."""
import random

VALIDATOR = [
    'The function takes one dictionary a and must not mutate it. Integer fields contain exact integers, not booleans. alphabet is a list of 1..3 distinct strings, each exactly one Unicode code point. All text strings contain only characters in alphabet. String lengths count Unicode code points.',
    'delta is a rectangular list of 1..5 rows and len(alphabet) columns containing state indices 0..len(delta)-1. state is an initial state index. accept is a list of distinct state indices, possibly empty. An output is accepted when starting at state and replacing q with delta[q][alphabet.index(c)] for each output character c leaves q in accept. The empty output is tested at state.',
    'max_output is an integer 0..12. Only outputs of length at most max_output are permitted.'
]
SCRIPT = [
    'The exact keys are alphabet, delta, state, accept, max_output, text, mode, next_mode, cost, max_ops. text has length 0..12. next_mode is a list of 1..4 rows of three mode indices. cost has the same dimensions with each entry an integer 1..20. mode is an initial mode index. max_ops is an integer 0..24.',
    'A script reads text once from left to right and emits its output from left to right. Operation index 0 inserts any one alphabet character without consuming input. Operation index 1 deletes the next input character and emits nothing. Operation index 2 consumes the next input character and emits any one alphabet character, including the identical character. Delete and substitute require an unconsumed input character. There is no free copy operation.',
    'Each operation at mode m adds cost[m][operation] and then sets the mode to next_mode[m][operation]. Character choice does not affect this mode update or cost. The initial cost is zero. A successful script consumes all of text, emits an accepted output, and uses at most max_ops operations. It may continue inserting after consuming all input. The empty script is allowed. No acceptance condition is imposed on the final edit mode.'
]
EDIT_SOURCE = '''def FUNCTION(a):
    # Each layer contains all prefixes of a fixed operation count.
    layer = {(0,0,a['state'],a['mode']):(0,1)}
    best = None; count = 0
    for step in range(a['max_ops']+1):
        following = {}
        for (i,length,q,m),(value,ways) in layer.items():
            if i == len(a['text']) and q in a['accept']:
                if best is None or value < best: best,count = value,ways
                elif value == best: count = (count+ways)%1000000007
            if step == a['max_ops']: continue
            for op in range(3):
                if op != 0 and i == len(a['text']): continue
                emissions = [None] if op == 1 else range(len(a['alphabet']))
                for c in emissions:
                    size = length+(c is not None)
                    if size > a['max_output']: continue
                    target = (i+(op!=0),size,q if c is None else a['delta'][q][c],a['next_mode'][m][op])
                    candidate = value+a['cost'][m][op]
                    old = following.get(target)
                    if old is None or candidate < old[0]: following[target] = (candidate,ways)
                    elif candidate == old[0]: following[target] = (candidate,(old[1]+ways)%1000000007)
        layer = following
    RETURN
'''
JOINT_SOURCE = '''def joint_text_repair_cost(a):
    # Advance both input positions, sharing every emitted output character.
    n=len(a['left']); m=len(a['right']); limit=a['max_output']
    table = {(0,0,0,a['state']):0}
    best=None
    for length in range(limit+1):
        for i in range(n+1):
            for j in range(m+1):
                for q in range(len(a['delta'])):
                    key=(length,i,j,q)
                    if key not in table: continue
                    value=table[key]
                    if i==n and j==m and q in a['accept']:
                        best=value if best is None else min(best,value)
                    moves=[]
                    if i<n: moves.append(((length,i+1,j,q),1))
                    if j<m: moves.append(((length,i,j+1,q),1))
                    if length<limit:
                        for c,char in enumerate(a['alphabet']):
                            for di in range(2 if i<n else 1):
                                for dj in range(2 if j<m else 1):
                                    cost=(int(a['left'][i]!=char) if di else 1)+(int(a['right'][j]!=char) if dj else 1)
                                    moves.append(((length+1,i+di,j+dj,a['delta'][q][c]),cost))
                    for target,price in moves:
                        candidate=value+price
                        if candidate<table.get(target,10**9): table[target]=candidate
    return best
'''


def script_inputs():
    cases=[]
    def add(text, alphabet, delta, accept, maximum, ops, cost=None, transitions=None):
        cases.append(dict(text=text,alphabet=alphabet,delta=delta,state=0,accept=accept,max_output=maximum,max_ops=ops,mode=0,cost=cost or [[1,1,1]],next_mode=transitions or [[0,0,0]]))
    add('', ['a'], [[0]], [0], 0, 0)
    add('a',['a'],[[0]],[0],1,1)
    add('a',['a'],[[0]],[],1,3)
    add('a',['a'],[[1],[1]],[1],1,3,[[1,5,4],[9,1,1]],[[1,1,1],[1,1,1]])
    add('ab',['a','b'],[[1,0],[1,0]],[1],2,3)
    add('é',['é','🦊'],[[1,0],[0,1]],[1],2,3)
    add('', ['a'], [[1],[0]], [1], 2, 3)
    add('aa',['a'],[[0]],[0],0,1)
    rng=random.Random(6013)
    for _ in range(10):
        alphabet=['a','b']; states=rng.randint(1,3); modes=rng.randint(1,2)
        cases.append(dict(text=''.join(rng.choice(alphabet) for _ in range(rng.randrange(3))),alphabet=alphabet,delta=[[rng.randrange(states) for _ in alphabet] for _ in range(states)],state=rng.randrange(states),accept=[q for q in range(states) if rng.randrange(2)],max_output=rng.randrange(3),max_ops=rng.randrange(5),mode=rng.randrange(modes),cost=[[rng.randint(1,5) for _ in range(3)] for _ in range(modes)],next_mode=[[rng.randrange(modes) for _ in range(3)] for _ in range(modes)]))
    return cases


GOLDENS = {'constrained_edit_cost': [0, 1, None, 2, 2, 1, 1, None, None, None, None, 2, 5, None, 2, None, None, 3], 'optimal_edit_script_count': [1, 2, 0, 1, 4, 1, 1, 0, 0, 0, 0, 2, 5, 0, 1, 0, 0, 1], 'joint_text_repair_cost': [1, 0, None, 0, 2, 0, 1, 4, 3, None, None, 0, 1, None, 1, None, 1, 0]}


def make_tasks():
    tasks=[]
    for name,role,ending,clauses in [
        ('constrained_edit_cost','development','return best',['Return the minimum total cost among successful scripts as an integer, or None if there are none.']),
        ('optimal_edit_script_count','heldout','return count if best is not None else 0',['Return the number of successful scripts of globally minimum total cost, modulo 1000000007, as an integer. Return 0 if none exist. A script is its ordered sequence of operation indices and emitted characters (deletion has no emitted character). Different sequences count separately, even when their output, cost, consumed characters, or final mode coincide. The operation limit applies before minimizing cost; scripts of any length from zero through max_ops compete together.'])]:
        source=EDIT_SOURCE.replace('FUNCTION',name).replace('RETURN',ending)
        ns={};exec(source,ns)
        tasks.append(dict(id=name,function=name,family='F6',role=role,clauses=VALIDATOR+SCRIPT+clauses,cases=[[a,want] for a,want in zip(script_inputs(),GOLDENS[name])],reference=source))
    args=[]
    for index,a in enumerate(script_inputs()):
        args.append({k:a[k] for k in ['alphabet','delta','state','accept','max_output']})
        args[-1].update(left=a['text'],right=(''.join(reversed(a['text'])) if index%2 else a['alphabet'][-1]))
    ns={};exec(JOINT_SOURCE,ns)
    tasks.append(dict(id='joint_text_repair_cost',function='joint_text_repair_cost',family='F6',role='heldout',clauses=VALIDATOR+[
        'The exact keys are alphabet, delta, state, accept, max_output, left, right. left and right are strings of length 0..12.',
        'For strings x and y, their Levenshtein distance is the smallest number of unit-cost single-character insertions, deletions, and substitutions transforming x to y. Identical characters may be retained for zero cost. There are no edit modes or operation-count limits.',
        'Return the minimum of distance(left,output)+distance(right,output) over all permitted accepted outputs as an integer, or None if no permitted accepted output exists. Both distances use the same output, and each is minimized independently.'
    ],cases=[[a,want] for a,want in zip(args,GOLDENS['joint_text_repair_cost'])],reference=JOINT_SOURCE))
    for task in tasks:
        a=dict(alphabet=['a'], delta=[[0]], state=0, accept=[0], max_output=0)
        if task['function']=='joint_text_repair_cost':
            a.update(left='a'*12,right='a'*12); want=24
        else:
            a.update(text='a'*12,mode=0,next_mode=[[0,0,0]],cost=[[20,20,20]],max_ops=24)
            want=1 if task['function']=='optimal_edit_script_count' else 240
        task['cases'].append([a,want])
        if task['function']=='optimal_edit_script_count':
            task['cases'].append([
                dict(alphabet=['a','b','c'],delta=[[0,0,0]],state=0,accept=[0],max_output=12,
                     text='a'*12,mode=0,next_mode=[[1,0,0],[0,0,0]],cost=[[1,5,5],[4,4,4]],max_ops=24),
                521304104,
            ])
    return tasks
