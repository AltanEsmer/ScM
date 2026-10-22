"""Independent product-graph oracles. F5 uses forward resource relaxation;
F6 uses positive-weight Dijkstra over consumed/emitted/state/mode/steps.
Fixed seeds cover boundary sizes, signed routes, Unicode, mode cycles, long
inputs, and alphabet/vertex relabeling pairs. Tiny exhaustive scripts crosscheck.
"""
import copy
import heapq
import itertools
import random


def integer(x, low, high):
    if type(x) is not int or not low <= x <= high:
        raise ValueError('integer outside contract')


def matrix(a, rows, cols, low, high):
    if type(a) is not list or not 1 <= len(a) <= rows:
        raise ValueError('matrix rows')
    for row in a:
        if type(row) is not list or len(row) != cols:
            raise ValueError('matrix columns')
        for x in row:
            integer(x, low, high)


def automaton(a, width):
    matrix(a['delta'], 5, width, 0, len(a['delta'])-1)
    integer(a['state'], 0, len(a['delta'])-1)
    if type(a['accept']) is not list or len(set(a['accept'])) != len(a['accept']):
        raise ValueError('accept states')
    for q in a['accept']:
        integer(q, 0, len(a['delta'])-1)


def validate_f5(a):
    if type(a) is not dict or set(a) != {'n','edges','start','goal','state','delta','accept','budget'}:
        raise ValueError('keys')
    integer(a['n'],1,8); integer(a['start'],0,a['n']-1); integer(a['goal'],0,a['n']-1)
    integer(a['budget'],0,24)
    if type(a['delta']) is not list or not a['delta'] or type(a['delta'][0]) is not list:
        raise ValueError('delta')
    width=len(a['delta'][0]); integer(width,1,3); automaton(a,width)
    if type(a['edges']) is not list or len(a['edges'])>20:
        raise ValueError('edges')
    for e in a['edges']:
        if type(e) is not list or len(e)!=5: raise ValueError('edge')
        for x,lo,hi in zip(e,[0,0,0,1,-20],[a['n']-1,a['n']-1,width-1,8,20]): integer(x,lo,hi)


def validate_f6(a):
    if type(a) is not dict or set(a) != {'alphabet','delta','state','accept','max_output','text','mode','next_mode','cost','max_ops'}:
        raise ValueError('keys')
    abc=a['alphabet']
    if type(abc) is not list or not 1<=len(abc)<=3 or any(type(c) is not str or len(c)!=1 for c in abc) or len(set(abc))!=len(abc): raise ValueError('alphabet')
    automaton(a,len(abc)); integer(a['max_output'],0,12); integer(a['max_ops'],0,24)
    if type(a['text']) is not str or len(a['text'])>12 or any(c not in abc for c in a['text']): raise ValueError('text')
    matrix(a['next_mode'],4,3,0,len(a['next_mode'])-1)
    if len(a['cost'])!=len(a['next_mode']): raise ValueError('cost rows')
    matrix(a['cost'],4,3,1,20); integer(a['mode'],0,len(a['next_mode'])-1)


def oracle_f5(a):
    layers=[{} for _ in range(a['budget']+1)]
    layers[0][a['start'],a['state']]=0
    answer=None
    for spent,layer in enumerate(layers):
        for (v,q),cost in list(layer.items()):
            if v==a['goal'] and q in a['accept']: answer=cost if answer is None else min(answer,cost)
            for u,w,label,res,price in a['edges']:
                if u==v and spent+res<=a['budget']:
                    dest=layers[spent+res]; key=(w,a['delta'][q][label]); value=cost+price
                    dest[key]=min(dest.get(key,value),value)
    return answer


def oracle_f6(a):
    initial=(0,0,a['state'],a['mode'],0)
    distance={initial:0}; queue=[(0,initial)]
    while queue:
        price,key=heapq.heappop(queue)
        if distance[key]!=price: continue
        i,size,q,m,steps=key
        if i==len(a['text']) and q in a['accept']: return price
        if steps==a['max_ops']: continue
        for op in range(3):
            if op and i==len(a['text']): continue
            if op!=1 and size==a['max_output']: continue
            for label in ([None] if op==1 else range(len(a['alphabet']))):
                target=(i+(op!=0),size+(op!=1),q if op==1 else a['delta'][q][label],a['next_mode'][m][op],steps+1)
                value=price+a['cost'][m][op]
                if value<distance.get(target,float('inf')):
                    distance[target]=value; heapq.heappush(queue,(value,target))
    return None


def generate_f5():
    rng=random.Random(516025); cases=[]
    def add(a,category):
        validate_f5(a); cases.append(dict(id=f'F5-{len(cases):03}',category=category,argument=a,expected=oracle_f5(a)))
    for budget in [0,1,7,8,23,24]:
        for accept in [[],[0]]:
            add(dict(n=1,edges=[[0,0,0,1,-20]],start=0,goal=0,state=0,delta=[[0]],accept=accept,budget=budget),'negative-loop-boundary')
    for j in range(74):
        n=8 if j%7==0 else rng.randint(1,8); q=5 if j%7==0 else rng.randint(1,5); k=rng.randint(1,3)
        a=dict(n=n,edges=[],start=rng.randrange(n),goal=rng.randrange(n),state=rng.randrange(q),delta=[[rng.randrange(q) for _ in range(k)] for _ in range(q)],accept=rng.sample(range(q),rng.randrange(q+1)),budget=24 if j%3==0 else rng.randrange(25))
        for _ in range(20 if j%7==0 else rng.randrange(21)):
            a['edges'].append([rng.randrange(n),rng.randrange(n),rng.randrange(k),rng.randint(1,8),rng.randint(-20,20)])
        add(a,'max-size' if j%7==0 else 'random-product-graph')
        b=copy.deepcopy(a); b['start']=n-1-b['start']; b['goal']=n-1-b['goal']
        for e in b['edges']: e[0]=n-1-e[0]; e[1]=n-1-e[1]
        add(b,'vertex-relabel-pair')
        assert cases[-1]['expected']==cases[-2]['expected']
    return cases


def generate_f6():
    rng=random.Random(616025); cases=[]
    def add(a,category):
        validate_f6(a); cases.append(dict(id=f'F6-{len(cases):03}',category=category,argument=a,expected=oracle_f6(a)))
    for length in [0,1,2,3,7,11,12]:
        for ops in [0,length,24]:
            add(dict(alphabet=['é'],delta=[[0]],state=0,accept=[0],max_output=12,text='é'*length,mode=0,next_mode=[[0,0,0]],cost=[[20,7,2]],max_ops=ops),'long-input-no-free-copy')
    for length in [0,3,12]:
        for maxout in [0,1,12]:
            for ops in [length,24]:
                add(dict(alphabet=['a','🦊'],delta=[[0,1],[1,0]],state=0,accept=[1],max_output=maxout,text='a'*length,mode=0,next_mode=[[1,1,1],[0,0,0]],cost=[[20,1,20],[1,20,1]],max_ops=ops),'directed-insert-tail-delete-mode-tradeoff')
    for j in range(70):
        abc=['a','é','🦊'][:rng.randint(1,3)]; q=5 if j%8==0 else rng.randint(1,5); modes=4 if j%8==0 else rng.randint(1,4)
        a=dict(alphabet=abc,delta=[[rng.randrange(q) for _ in abc] for _ in range(q)],state=rng.randrange(q),accept=rng.sample(range(q),rng.randrange(q+1)),max_output=12 if j%4==0 else rng.randrange(13),text=''.join(rng.choice(abc) for _ in range(12 if j%4==0 else rng.randrange(13))),mode=rng.randrange(modes),next_mode=[[rng.randrange(modes) for _ in range(3)] for _ in range(modes)],cost=[[rng.randint(1,20) for _ in range(3)] for _ in range(modes)],max_ops=24 if j%3==0 else rng.randrange(25))
        add(a,'max-size-mode-cycles' if j%4==0 else 'random-edit-regimes')
        b=copy.deepcopy(a); trans=dict(zip(abc,['λ','中','🐋'])); b['alphabet']=[trans[c] for c in abc]; b['text']=''.join(trans[c] for c in a['text'])
        add(b,'unicode-relabel-pair')
        assert cases[-1]['expected']==cases[-2]['expected']
    return cases


def verify_oracles():
    count=0
    for n in range(3):
        for maxout in range(3):
            for ops in range(5):
                a=dict(alphabet=['a','b'],delta=[[1,0],[0,1]],state=0,accept=[1],max_output=maxout,text='a'*n,mode=0,next_mode=[[1,0,1],[0,1,0]],cost=[[2,3,4],[5,1,2]],max_ops=ops)
                values=[]
                def scripts(i,out,q,m,steps,price):
                    if i==n and q==1: values.append(price)
                    if steps==ops: return
                    for op in range(3):
                        if op and i==n: continue
                        for c in ([None] if op==1 else [0,1]):
                            if out+(c is not None)>maxout: continue
                            scripts(i+(op!=0),out+(c is not None),q if c is None else a['delta'][q][c],a['next_mode'][m][op],steps+1,price+a['cost'][m][op])
                scripts(0,0,0,0,0,0)
                assert oracle_f6(a)==min(values,default=None)
                count+=1
    for budget in range(9):
        a=dict(n=1,edges=[[0,0,0,2,-3]],start=0,goal=0,state=0,delta=[[0]],accept=[0],budget=budget)
        assert oracle_f5(a)==-3*(budget//2); count+=1
    rng=random.Random(501)
    for trial in range(60):
        a=dict(n=2,edges=[[rng.randrange(2),rng.randrange(2),rng.randrange(2),rng.randint(1,2),rng.randint(-3,3)] for _ in range(4)],start=0,goal=trial%2,state=0,delta=[[1,0],[0,1]],accept=[trial%2],budget=trial%5)
        costs=[]
        def walks(v,q,spent,price):
            if v==a['goal'] and q in a['accept']: costs.append(price)
            for u,w,label,res,cost in a['edges']:
                if u==v and spent+res<=a['budget']: walks(w,a['delta'][q][label],spent+res,price+cost)
        walks(0,0,0,0)
        assert oracle_f5(a)==min(costs,default=None)
    return {'f5_closed_form_goldens':9,'f5_exhaustive_walks':60,'f6_exhaustive_scripts':count-9}
