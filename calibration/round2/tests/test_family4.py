"""Permutation goldens, precise bounds, transport observations and mutant checks."""
import copy
import json
import unittest

from calibration.round2.pool import family4
from grading import score, typed


def validate(arg, function):
    required={'time','cost','requests'} | ({'vehicles'} if function=='fleet_assignment_cost' else {'vehicle'}) | ({'budget'} if function=='reward_delivery_selection' else set())
    assert set(arg)==required
    n=len(arg['time']);assert 1<=n<=9
    def integer(x,lo,hi): assert type(x) is int and lo<=x<=hi
    for matrix in (arg['time'],arg['cost']):
        assert type(matrix) is list and len(matrix)==n
        for i,row in enumerate(matrix):
            assert type(row) is list and len(row)==n
            for value in row: integer(value,0,20)
            assert row[i]==0
    assert 0<=len(arg['requests'])<=4
    for r in arg['requests']:
        assert set(r)=={'pick','drop','load','pw','dw','ps','ds'} | ({'reward'} if function=='reward_delivery_selection' else set())
        for field in ('pick','drop'): integer(r[field],0,n-1)
        integer(r['load'],1,3)
        for field in ('pw','dw'):
            w=r[field];assert type(w) is list and len(w)==2
            integer(w[0],0,80);integer(w[1],w[0],80)
        for field in ('ps','ds'): integer(r[field],0,5)
        if 'reward' in r: integer(r['reward'],0,30)
    vehicles=arg.get('vehicles',[arg.get('vehicle')]);assert 1<=len(vehicles)<=3
    for v in vehicles:
        assert set(v)=={'start','end','capacity','release','deadline'}
        for field in ('start','end'): integer(v[field],0,n-1)
        integer(v['capacity'],1,5);integer(v['release'],0,100);integer(v['deadline'],v['release'],100)
    if 'budget' in arg: integer(arg['budget'],0,100)


class TransportContracts(unittest.TestCase):
    def test_independent_permutations_membership_types_and_budget(self):
        for task in family4.make_tasks():
            ns={};exec(task['reference'],ns);rows=[]
            self.assertTrue(15<=len(task['cases'])<=25)
            for arg,expected in task['cases']:
                original=copy.deepcopy(arg);validate(arg,task['function'])
                mode={'pickup_delivery_cost':'single','fleet_assignment_cost':'fleet','reward_delivery_selection':'reward'}[task['function']]
                self.assertEqual(typed(family4._expected(arg,mode)),typed(expected))
                actual=ns[task['function']](arg)
                self.assertEqual(typed(actual),typed(expected));self.assertEqual(arg,original)
                self.assertTrue(actual is None or type(actual) is int)
                rows.append(dict(actual=typed(actual),input_after=typed(arg),same_object=actual is arg))
            payload=json.dumps({'results':rows},allow_nan=False)+'\n'
            self.assertLess(len(payload.encode()),40000)
            self.assertEqual(score(task,payload)[0],'pass')

    def test_literal_boundaries(self):
        tasks=family4.make_tasks()
        self.assertEqual([e for _,e in tasks[0]['cases'][-4:]],[7,7,None,5])
        # Identical request occurrences all earn reward; omission remains optional.
        self.assertTrue(any(type(e) is int and e>0 for _,e in tasks[2]['cases']))
        self.assertTrue(any(e is None for _,e in tasks[0]['cases']))
        self.assertTrue(any(e is not None for _,e in tasks[1]['cases']))

    def test_semantic_mutants_are_killed(self):
        mutants=[
            ("max(time + arg['time'][node][target], window[0])","time + arg['time'][node][target]"),
            ("arg['time'][node][target]","arg['cost'][node][target]"),
            ("start + duration","start"),
            ("start > window[1]","start >= window[1]"),
            ("newload > vehicle['capacity']","newload >= vehicle['capacity']"),
            ("cost + arg['cost'][node][vehicle['end']]","cost"),
            ("time + arg['time'][node][vehicle['end']] <= vehicle['deadline']","time + arg['time'][node][vehicle['end']] < vehicle['deadline']"),
            ("vehicles = arg['vehicles']","vehicles = arg['vehicles'][:1]"),
            ("cost <= arg['budget']","cost < arg['budget']"),
            ("sum(arg['requests'][i]['reward'] for i in indices)","len(indices)"),
            ("for mask in range(1 << len(arg['requests'])):","for mask in [(1 << len(arg['requests'])) - 1]:"),
        ]
        tasks=family4.make_tasks()
        for old,new in mutants:
            self.assertIn(old,family4.REFERENCE)
            ns={};exec(family4.REFERENCE.replace(old,new),ns)
            killed=False
            for task in tasks:
                for arg,expected in task['cases']:
                    try: killed |= ns[task['function']](copy.deepcopy(arg))!=expected
                    except Exception: killed=True
            self.assertTrue(killed,(old,new))

if __name__=='__main__': unittest.main()
