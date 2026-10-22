import copy
import json
import unittest

import grading
from calibration.round2.pool import family1


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def domain(name, data):
    if name == 'inventory_transfer_cost':
        assert set(data) == {'n','days','supply','demand','carry_capacity','storage_cost','transfers'}
        n, days = data['n'], data['days']
        assert integer(n,1,2) and integer(days,1,3)
        for field, rows, low, high in [('supply',days,0,2),('demand',days,0,2),('carry_capacity',days-1,0,2),('storage_cost',days-1,-3,3)]:
            assert type(data[field]) is list and len(data[field]) == rows
            assert all(type(row) is list and len(row) == n and all(integer(x,low,high) for x in row) for row in data[field])
        assert type(data['transfers']) is list and len(data['transfers']) <= 3
        for edge in data['transfers']:
            assert type(edge) is list and len(edge) == 5
            assert all(integer(x,lo,hi) for x,lo,hi in zip(edge,[0,0,0,0,-3],[days-1,n-1,n-1,2,3]))
    else:
        assert set(data) == ({'n','arcs','versions'} if name == 'versioned_circulation_costs' else {'n','arcs'})
        assert integer(data['n'],1,4)
        assert type(data['arcs']) is list and len(data['arcs']) <= 6
        for edge in data['arcs']:
            assert type(edge) is list and len(edge) == 5
            u,v,low,high,cost = edge
            assert integer(u,0,data['n']-1) and integer(v,0,data['n']-1)
            assert integer(low,0,2) and integer(high,low,2) and integer(cost,-5,5)
        if 'versions' in data:
            assert type(data['versions']) is list and len(data['versions']) <= 8
            for j, change in enumerate(data['versions']):
                assert type(change) is list and len(change) == 5
                parent,i,low,high,cost = change
                assert integer(parent,0,j) and integer(i,0,len(data['arcs'])-1)
                assert integer(low,0,2) and integer(high,low,2) and integer(cost,-5,5)


def observations(task, function):
    rows = []
    for arg, expected in task['cases']:
        argument = copy.deepcopy(arg)
        actual = function(argument)
        rows.append(dict(actual=grading.typed(actual), input_after=grading.typed(argument),same_object=actual is argument))
    return json.dumps({'results':rows})


class NetworkContracts(unittest.TestCase):
    def test_domain_fresh_reference_oracle_and_transport(self):
        for task in family1.make_tasks():
            self.assertTrue(15 <= len(task['cases']) <= 25)
            for argument, expected in task['cases']:
                domain(task['function'],argument)
                before = copy.deepcopy(argument)
                namespace = {}
                exec(task['reference'],namespace)
                actual = namespace[task['function']](argument)
                self.assertTrue(grading.exact(actual, expected),task['id'])
                self.assertTrue(grading.exact(expected,family1.oracle(task['function'],argument)))
                self.assertEqual(argument,before)
            namespace = {}
            exec(task['reference'],namespace)
            output = observations(task,namespace[task['function']])
            self.assertLess(len(output.encode()),40000)
            self.assertEqual(grading.score(task,output)[:2],('pass',len(task['cases'])))

    def test_worked_literals(self):
        tasks = {t['id']:t for t in family1.make_tasks()}
        self.assertEqual(tasks['versioned_circulation_costs']['cases'][1][1],[-4,None,-4,0,-4])
        self.assertEqual(tasks['inventory_transfer_cost']['cases'][1][1],6)
        self.assertIsNone(tasks['inventory_transfer_cost']['cases'][2][1])
        self.assertEqual(tasks['inventory_transfer_cost']['cases'][3][1],-1)
        self.assertEqual(tasks['inventory_transfer_cost']['cases'][4][1],-4)
        self.assertEqual(tasks['single_failure_costs']['cases'][1][1],[None,None])

    def test_semantic_mutants_are_rejected(self):
        tasks = family1.make_tasks()
        version, inventory, failure = tasks
        mutants = [
            (version,version['reference'].replace('snapshots[parent]','snapshots[-1]')),
            (version,version['reference'].replace('range(low, high + 1)','range(0, high + 1)')),
            (version,version['reference'].replace('value + flow * cost','value + flow * max(cost, 0)')),
            (failure,failure['reference'].replace("edges[disabled][2:4] = [0, 0]","edges[disabled][3] = edges[disabled][2]")),
            (inventory,inventory['reference'].replace("data['storage_cost'][day][place]","0")),
            (inventory,inventory['reference'].replace("target = [data['supply'][d][p] - data['demand'][d][p]","target = [data['demand'][d][p] - data['supply'][d][p]")),
        ]
        for task, source in mutants:
            namespace = {};exec(source,namespace)
            self.assertEqual(grading.score(task,observations(task,namespace[task['function']]))[0],'fail')


if __name__ == '__main__':
    unittest.main()
