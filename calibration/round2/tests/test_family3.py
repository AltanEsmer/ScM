"""Independent substitution semantics, domain membership and semantic mutants."""
import copy
import json
import unittest

from calibration.round2.pool import family3
from grading import score, typed


def substitute(e, name, value):
    if type(e) is not list:
        return e
    op, *a = e
    if op == 'var':
        return value if a[0] == name else e
    if op == 'fn':
        return e if a[0] == name else [op,a[0],substitute(a[1],name,value)]
    if op == 'let':
        return [op,a[0],substitute(a[1],name,value),a[2] if a[0] == name else substitute(a[2],name,value)]
    return [op] + [substitute(x,name,value) for x in a]


def oracle(e, store=()):
    """Closed terms reduce by value substitution; state is an immutable tuple."""
    if type(e) is not list:
        return e, store
    op,*a=e
    if op == 'fn': return ('fn',a[0],a[1]),store
    if op == 'snap': return ('snap',store),store
    if op == 'let':
        v,s=oracle(a[1],store)
        return oracle(substitute(a[2],a[0],v),s)
    if op == 'seq':
        _,s=oracle(a[0],store)
        return oracle(a[1],s)
    if op == 'if':
        v,s=oracle(a[0],store)
        return oracle(a[1] if v else a[2],s)
    v,s=oracle(a[0],store)
    if op == 'ref': return ('cell',len(s)),s+(v,)
    if op == 'get': return s[v[1]],s
    if op == 'restore': return oracle(a[1],v[1])
    w,s=oracle(a[1],s)
    if op == 'call': return oracle(substitute(v[2],v[1],w),s)
    if op == 'set': return w,s[:v[1]]+(w,)+s[v[1]+1:]
    return (v+w if op == 'add' else v-w),s


def initial(bindings):
    replacements=[];store=()
    for name,e in bindings:
        for n,v in replacements: e=substitute(e,n,v)
        v,store=oracle(e,store);replacements.append((name,v))
    return replacements,store


def observe(arg, function):
    if function == 'bounded_store_equivalence':
        diff=[x for x in arg['domain'] if oracle(substitute(arg['left'],'x',x)) != oracle(substitute(arg['right'],'x',x))]
        return dict(equivalent=not diff,different_inputs=diff)
    replacements,store=initial(arg['bindings'])
    def run(e,s):
        for name,value in replacements: e=substitute(e,name,value)
        v,s=oracle(e,s)
        assert type(v) is int and len(s)<=8 and all(type(x) is int for x in s)
        return dict(value=v,store=list(s))
    if function == 'store_program_result': return run(arg['program'],store)
    results=[]
    for branch in arg['branches']:
        results.append(run(branch['program'],store if branch['from']==-1 else tuple(results[branch['from']]['store'])))
    return results


def validate_expression(e, scope, depth=0):
    assert depth<=18
    if type(e) is int:
        assert -20<=e<=20
        return 1
    assert type(e) is list and e
    op,*a=e
    arities=dict(var=1,let=3,fn=2,call=2,seq=2,if_=3,add=2,sub=2,ref=1,get=1,set=2,snap=0,restore=2)
    assert len(a)==arities['if_' if op=='if' else op]
    if op in ('var','fn','let'):
        assert type(a[0]) is str and a[0].isascii() and a[0].isalpha() and a[0].islower() and len(a[0])<=8
    if op=='var':
        assert a[0] in scope
        return 1
    if op=='fn': return 1+validate_expression(a[1],scope|{a[0]},depth+1)
    if op=='let': return 1+validate_expression(a[1],scope,depth+1)+validate_expression(a[2],scope|{a[0]},depth+1)
    return 1+sum(validate_expression(x,scope,depth+1) for x in a)


class StoreContracts(unittest.TestCase):
    def test_cases_independent_oracle_types_preservation_and_budget(self):
        for task in family3.make_tasks():
            ns={};exec(task['reference'],ns);rows=[]
            self.assertTrue(15<=len(task['cases'])<=25)
            for arg,expected in task['cases']:
                original=copy.deepcopy(arg)
                if 'bindings' in arg:
                    scope=set();nodes=0
                    self.assertLessEqual(len(arg['bindings']),6)
                    for name,e in arg['bindings']:
                        self.assertNotIn(name,scope);nodes+=validate_expression(e,scope);scope.add(name)
                    if 'branches' in arg:
                        self.assertLessEqual(len(arg['branches']),6)
                        for i,b in enumerate(arg['branches']):
                            self.assertEqual(set(b),{'from','program'});self.assertTrue(-1<=b['from']<i)
                            nodes+=validate_expression(b['program'],scope)
                    else: nodes+=validate_expression(arg['program'],scope)
                else:
                    d=arg['domain'];self.assertEqual(d,sorted(set(d)));self.assertLessEqual(len(d),7)
                    self.assertTrue(all(type(x) is int and -10<=x<=10 for x in d))
                    nodes=sum(validate_expression(arg[k],{'x'}) for k in ('left','right'))
                self.assertLessEqual(nodes,100)
                self.assertEqual(typed(observe(arg,task['function'])),typed(expected))
                actual=ns[task['function']](arg)
                self.assertEqual(typed(actual),typed(expected));self.assertEqual(arg,original)
                rows.append(dict(actual=typed(actual),input_after=typed(arg),same_object=actual is arg))
            payload=json.dumps({'results':rows},allow_nan=False)+'\n'
            self.assertLess(len(payload.encode()),40000)
            self.assertEqual(score(task,payload)[0],'pass')

    def test_semantic_mutants_are_killed(self):
        mutants=[
            ("dict(f[3], **{f[1]: x})","dict(env, **{f[1]: x})"),
            ("('snapshot', tuple(store))","('snapshot', store)"),
            ("store[:] = snapshot[1]","store[:] = list(snapshot[1]) + store[len(snapshot[1]):]"),
            ("store[cell[1]] = value","store[cell[1]] = value + 1"),
            ("observations[0] != observations[1]","observations[0][0] != observations[1][0]"),
            ("initial if branch['from'] == -1 else stores[branch['from']]","initial"),
        ]
        for old,new in mutants:
            self.assertIn(old,family3.REFERENCE)
            ns={};exec(family3.REFERENCE.replace(old,new),ns)
            killed=False
            for task in family3.make_tasks():
                for a,e in task['cases']:
                    try: killed |= ns[task['function']](copy.deepcopy(a))!=e
                    except Exception: killed=True
            self.assertTrue(killed,(old,new))

    def test_every_task_rejects_dynamic_scoping(self):
        source=family3.REFERENCE.replace("dict(f[3], **{f[1]: x})", "dict(env, **{f[1]: x})")
        ns={};exec(source,ns)
        for task in family3.make_tasks():
            self.assertTrue(any(ns[task['function']](copy.deepcopy(arg))!=expected
                                for arg,expected in task['cases']),task['id'])

if __name__=='__main__': unittest.main()
