"""Frozen-candidate material for lexical closures and persistent stores."""

REFERENCE = r'''
def _evaluate(e, env, store):
    if type(e) is int:
        return e
    op, *a = e
    if op == 'var':
        return env[a[0]]
    if op == 'let':
        value = _evaluate(a[1], env, store)
        return _evaluate(a[2], dict(env, **{a[0]: value}), store)
    if op == 'fn':
        return ('closure', a[0], a[1], env.copy())
    if op == 'call':
        f = _evaluate(a[0], env, store)
        x = _evaluate(a[1], env, store)
        return _evaluate(f[2], dict(f[3], **{f[1]: x}), store)
    if op == 'seq':
        _evaluate(a[0], env, store)
        return _evaluate(a[1], env, store)
    if op == 'if':
        return _evaluate(a[1] if _evaluate(a[0], env, store) != 0 else a[2], env, store)
    if op == 'snap':
        return ('snapshot', tuple(store))
    if op == 'restore':
        snapshot = _evaluate(a[0], env, store)
        store[:] = snapshot[1]
        return _evaluate(a[1], env, store)
    if op == 'ref':
        value = _evaluate(a[0], env, store)
        index = len(store)
        store.append(value)
        return ('cell', index)
    if op == 'get':
        return store[_evaluate(a[0], env, store)[1]]
    if op == 'set':
        cell = _evaluate(a[0], env, store)
        value = _evaluate(a[1], env, store)
        store[cell[1]] = value
        return value
    left = _evaluate(a[0], env, store)
    right = _evaluate(a[1], env, store)
    return left + right if op == 'add' else left - right

def _initial(bindings):
    env, store = {}, []
    for name, expression in bindings:
        env[name] = _evaluate(expression, env, store)
    return env, store

def store_program_result(arg):
    env, store = _initial(arg['bindings'])
    value = _evaluate(arg['program'], env, store)
    return {'value': value, 'store': store}

def forked_store_observations(arg):
    env, initial = _initial(arg['bindings'])
    stores, results = [], []
    for branch in arg['branches']:
        store = (initial if branch['from'] == -1 else stores[branch['from']]).copy()
        value = _evaluate(branch['program'], env, store)
        stores.append(store)
        results.append({'value': value, 'store': store.copy()})
    return results

def bounded_store_equivalence(arg):
    different = []
    for x in arg['domain']:
        observations = []
        for program in (arg['left'], arg['right']):
            store = []
            observations.append((_evaluate(program, {'x': x}, store), store))
        if observations[0] != observations[1]:
            different.append(x)
    return {'equivalent': not different, 'different_inputs': different}
'''

LANGUAGE = [
    "Use exact built-in JSON types; integers exclude booleans. Expressions are integers or the arrays specified here. Names are nonempty lowercase ASCII strings of at most 8 letters. All evaluation is deterministic, left to right, and must preserve the input argument.",
    "Expression forms are ['var',name], ['let',name,value,body], ['fn',parameter,body], ['call',function,argument], ['seq',first,second], ['if',condition,then,else], ['add',left,right], ['sub',left,right], ['ref',value], ['get',cell], ['set',cell,value], ['snap'], and ['restore',snapshot,body]. No other forms occur. Integer literals are between -20 and 20.",
    "A let evaluates value in the current environment, then body with that name bound to the resulting value. A function captures a copy of its current lexical name bindings. A call evaluates function then argument in the caller environment, then evaluates the captured body in its captured environment extended by its parameter. There is no recursion binding. A seq discards its first value. An if evaluates only the selected arm: then when its integer condition is nonzero, otherwise else. Add and sub operate on integers.",
    "The store starts as an empty ordered list of integer cells. Ref evaluates its integer argument, appends a cell, and returns a cell handle with ID equal to the previous store length. Get reads a handle's cell; set evaluates handle then integer value, overwrites that cell, and returns the assigned integer. Handles alias by integer ID, including across captured environments. All allocated cells, even unreachable cells, are observable in ascending ID order.",
    "Snap returns an immutable copy of the current entire store, without allocation. Restore first evaluates its snapshot expression, replaces the entire current store by that snapshot, then evaluates body in the same lexical environment. Restoring also resets the next allocation ID to the restored length. A preexisting handle denotes its numeric ID in the restored store; using it is valid only if that ID exists at access time. A later allocation may reuse a discarded ID. Closures and snapshots retain captured bindings or store contents independently of subsequent changes.",
    "All supplied expressions are well scoped, terminate, and are dynamically well typed on every evaluated path: arithmetic and conditions use integers; ref and set store integers only; call uses a closure; restore uses a snapshot; get and set use existing cell IDs. Every final program result is an integer. Each argument contains at most 100 expression nodes in total (including unevaluated function bodies), nesting at most 18, at most 300 evaluated expression nodes per program run, at most 8 cells in any store, and all intermediate integers have absolute value at most 10000. No invalid-input behavior is required."
]


def _task(name, role, clauses, cases):
    return dict(id=name, function=name, family='F3', role=role,
                clauses=clauses + LANGUAGE, cases=cases, reference=REFERENCE)


def make_tasks():
    dev, forks, equivalence = [], [], []
    for n in range(-4, 5):
        bindings = [['r', ['ref', n]], ['f', ['fn', 'a', ['add', ['get', ['var', 'r']], ['var', 'a']]]]]
        program = ['let', 's', ['snap'], ['seq', ['set', ['var', 'r'], n + 1], ['restore', ['var', 's'], ['call', ['var', 'f'], 2]]]]
        dev.append([{'bindings': bindings, 'program': program}, {'value': n + 2, 'store': [n]}])
        forks.append([{'bindings': bindings, 'branches': [
            {'from': -1, 'program': ['set', ['var', 'r'], n + 2]},
            {'from': -1, 'program': ['call', ['var', 'f'], 1]},
            {'from': 0, 'program': ['call', ['var', 'f'], 3]}]},
            [{'value': n + 2, 'store': [n + 2]}, {'value': n + 1, 'store': [n]}, {'value': n + 5, 'store': [n + 2]}]])
        equivalence.append([{'domain': [-2, 0, 2], 'left': ['add', ['var', 'x'], n], 'right': ['sub', ['var', 'x'], -n]}, {'equivalent': True, 'different_inputs': []}])
    # Literal interaction goldens, independently reasoned from the operational clauses.
    examples = [
        (['let','x',2,['let','f',['fn','a',['add',['var','x'],['var','a']]],['let','x',9,['call',['var','f'],1]]]], 3, []),
        (['let','r',['ref',1],['let','q',['var','r'],['seq',['set',['var','q'],7],['get',['var','r']]]]], 7, [7]),
        (['let','s',['snap'],['seq',['ref',8],['restore',['var','s'],['seq',['ref',3],4]]]], 4, [3]),
        (['if',0,['seq',['ref',9],1],2], 2, []),
        (['let','r',['ref',1],['let','s',['snap'],['seq',['set',['var','r'],8],['restore',['var','s'],['get',['var','r']]]]]],1,[1]),
        (['let','f',['call',['fn','x',['fn','y',['sub',['var','x'],['var','y']]]],7],['call',['var','f'],2]],5,[]),
        (['add',['seq',['ref',1],2],['seq',['ref',3],4]],6,[1,3]),
    ]
    for p, v, s in examples:
        dev.append([{'bindings': [], 'program': p}, {'value': v, 'store': s}])
        forks.append([{'bindings': [], 'branches': [{'from': -1, 'program': p}, {'from': -1, 'program': 0}]}, [{'value': v, 'store': s}, {'value': 0, 'store': []}]])
    pairs = [
        (['var','x'],0,[-2,2]),
        (['seq',['ref',1],0],0,[-2,0,2]),
        (['if',['var','x'],1,0],1,[0]),
        (['let','r',['ref',1],['seq',['set',['var','r'],2],0]],['seq',['ref',2],0],[]),
        (['let','s',['snap'],['seq',['ref',1],['restore',['var','s'],0]]],0,[]),
        (['seq',['ref',1],0],['seq',['ref',2],0],[-2,0,2]),
        (['call',['fn','a',['add',['var','a'],1]],['var','x']],['add',1,['var','x']],[]),
    ]
    for left,right,diff in pairs:
        equivalence.append([{'domain':[-2,0,2], 'left':left,'right':right}, {'equivalent':not diff,'different_inputs':diff}])
    dev.extend([
        [{'bindings': [], 'program': ['let','r',['ref',1],['let','s',['snap'],['let','q',['ref',2],['restore',['var','s'],['seq',['ref',9],['get',['var','q']]]]]]]}, {'value':9,'store':[1,9]}],
        [{'bindings': [], 'program': ['let','r',['ref',1],['add',['set',['var','r'],3],['get',['var','r']]]]}, {'value':6,'store':[3]}],
        [{'bindings': [['r',['ref',2]],['f',['fn','a',['set',['var','r'],['var','a']]]]],'program':['let','r',['ref',8],['call',['var','f'],4]]}, {'value':4,'store':[4,8]}],
    ])
    forks.extend([
        [{'bindings':[['r',['ref',0]]], 'branches':[{'from':-1,'program':['set',['var','r'],2]},{'from':0,'program':['set',['var','r'],5]},{'from':0,'program':['get',['var','r']]},{'from':1,'program':['get',['var','r']]}]}, [{'value':2,'store':[2]},{'value':5,'store':[5]},{'value':2,'store':[2]},{'value':5,'store':[5]}]],
        [{'bindings':[], 'branches':[]}, []],
        [{'bindings':[['r',['ref',1]],['s',['snap']]],'branches':[{'from':-1,'program':['set',['var','r'],8]},{'from':0,'program':['restore',['var','s'],['get',['var','r']]]}]}, [{'value':8,'store':[8]},{'value':1,'store':[1]}]],
    ])
    equivalence.extend([
        [{'domain':[], 'left':['var','x'], 'right':0}, {'equivalent':True,'different_inputs':[]}],
        [{'domain':[-1,0,1], 'left':['seq',['ref',['var','x']],0], 'right':['seq',['ref',0],0]}, {'equivalent':False,'different_inputs':[-1,1]}],
        [{'domain':[-1,0,1], 'left':['if',['var','x'],['seq',['ref',1],0],0], 'right':0}, {'equivalent':False,'different_inputs':[-1,1]}],
        [{'domain':[-1,0,1], 'left':['let','x',2,['let','f',['fn','a',['add',['var','x'],['var','a']]],['let','x',9,['call',['var','f'],1]]]], 'right':3}, {'equivalent':True,'different_inputs':[]}],
    ])
    return [
        _task('store_program_result','development',[
            "Implement store_program_result(arg). Arg has exactly bindings and program. Bindings is an ordered list of at most 6 [name,expression] pairs with distinct names, evaluated sequentially starting with empty environment and store; each binding sees earlier bindings. Program then runs in that environment and resulting store. Return exactly {'value': final integer, 'store': final list of integers}."],dev),
        _task('forked_store_observations','heldout',[
            "Implement forked_store_observations(arg). Arg has exactly bindings and branches. Bindings is an ordered list of at most 6 distinct [name,expression] pairs evaluated sequentially from empty environment and store, with each binding seeing earlier bindings. Preserve the resulting lexical environment for all branches.",
            "Branches is a list of 0 to 6 objects with exactly from and program. For branch index i, from is -1 or an integer in [0,i). Start that branch with a copy of the initial store when from is -1, otherwise a copy of the selected earlier branch's final store. Run its program in the initial lexical environment, independently of other branches. Return the ordered list of {'value': final integer, 'store': final integer list} observations. No branch changes the initial or earlier branch stores."],forks),
        _task('bounded_store_equivalence','heldout',[
            "Implement bounded_store_equivalence(arg). Arg has exactly left, right, and domain. Left and right are expressions. Domain is an ascending list of 0 to 7 distinct integers between -10 and 10. For each domain value x, independently run each program starting with an empty store and the single lexical binding x to that integer. Programs are equivalent at x exactly when both their final integer values and entire final ordered stores agree.",
            "Return exactly {'equivalent': boolean, 'different_inputs': list of integers}, where different_inputs contains all domain members at which the programs differ, in domain order, and equivalent is true exactly when that list is empty. Empty domains are equivalent."],equivalence)]
