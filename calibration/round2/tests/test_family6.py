import copy
from collections import Counter
import itertools
import json
import unittest
from calibration.round2.pool import family6
from grading import typed


def cost_spectrum(a):
    """Count every operation path at every cost, without shortest-path pruning."""
    layer={(0,0,a['state'],a['mode'],0):1}
    totals=Counter()
    for step in range(a['max_ops']+1):
        following=Counter()
        for (i,length,q,mode,spent),ways in layer.items():
            if i==len(a['text']) and q in a['accept']:
                totals[spent]+=ways
            if step==a['max_ops']:
                continue
            for op in range(3):
                if op!=0 and i==len(a['text']):
                    continue
                for char in ([None] if op==1 else a['alphabet']):
                    size=length+(char is not None)
                    if size>a['max_output']:
                        continue
                    state=q if char is None else a['delta'][q][a['alphabet'].index(char)]
                    following[(i+(op!=0),size,state,a['next_mode'][mode][op],spent+a['cost'][mode][op])]+=ways
        layer=following
    return totals


def distance(s,t):
    if not s: return len(t)
    if not t: return len(s)
    return min(1+distance(s[1:],t),1+distance(s,t[1:]),(s[0]!=t[0])+distance(s[1:],t[1:]))


def oracle(a, name):
    def accepted(s):
        q=a['state']
        for c in s:q=a['delta'][q][a['alphabet'].index(c)]
        return q in a['accept']
    if name=='joint_text_repair_cost':
        return min((distance(a['left'],''.join(t))+distance(a['right'],''.join(t)) for k in range(a['max_output']+1) for t in itertools.product(a['alphabet'],repeat=k) if accepted(t)),default=None)
    if a['max_ops']>6:
        totals=cost_spectrum(a)
        best=min(totals,default=None)
        return (totals[best]%1000000007 if best is not None else 0) if name=='optimal_edit_script_count' else best
    # Enumerate scripts directly, retaining every operation identity and prefix.
    values=[]
    def visit(i,out,mode,cost,steps):
        if i==len(a['text']) and accepted(out):values.append(cost)
        if steps==a['max_ops']:return
        for op in range(3):
            if op!=0 and i==len(a['text']):continue
            emissions=[''] if op==1 else a['alphabet']
            for c in emissions:
                if len(out)+len(c)>a['max_output']:continue
                visit(i+(op!=0),out+c,a['next_mode'][mode][op],cost+a['cost'][mode][op],steps+1)
    visit(0,'',a['mode'],0,0)
    best=min(values,default=None)
    return sum(v==best for v in values)%1000000007 if name=='optimal_edit_script_count' else best


class Family6Tests(unittest.TestCase):
    def test_modular_count_golden_and_candidate_mutant(self):
        task=family6.make_tasks()[1]
        arg,want=task['cases'][-1]
        totals=cost_spectrum(arg)
        self.assertEqual(min(totals),60)
        self.assertEqual(totals[60],2026521318286)
        self.assertEqual(want,521304104)
        source=task['reference'].replace('%1000000007','')
        ns={};exec(source,ns)
        self.assertTrue(any(ns[task['function']](copy.deepcopy(a))!=expected for a,expected in task['cases']))

    def test_cost_spectrum_agrees_with_small_script_enumeration(self):
        for arg in family6.script_inputs():
            totals=cost_spectrum(arg)
            best=min(totals,default=None)
            self.assertEqual(best,oracle(arg,'constrained_edit_cost'))
            self.assertEqual(totals[best]%1000000007 if best is not None else 0,
                             oracle(arg,'optimal_edit_script_count'))

    def test_contracts(self):
        for task in family6.make_tasks():
            ns={};exec(task['reference'],ns);rows=[]
            self.assertGreaterEqual(len(task['cases']),15)
            for a,want in task['cases']:
                before=copy.deepcopy(a); got=ns[task['function']](a)
                self.assertEqual(want,oracle(a,task['function']))
                self.assertEqual(got,want);self.assertEqual(a,before)
                rows.append(dict(actual=typed(got),input_after=typed(a),same_object=got is a))
            self.assertLess(len(json.dumps(dict(results=rows)).encode()),40000)

    def test_semantic_mutants(self):
        for task in family6.make_tasks():
            def mutate(a):
                a=copy.deepcopy(a)
                if task['function']=='joint_text_repair_cost':a['right']=a['left']
                elif task['function']=='optimal_edit_script_count':a['max_ops']=0
                else:a['next_mode']=[[0,0,0] for _ in a['next_mode']]
                return a
            self.assertTrue(any(oracle(a,task['function'])!=oracle(mutate(a),task['function']) for a,_ in task['cases']))
