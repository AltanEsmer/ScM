import copy
import json
import unittest

import grading
from calibration.round2.pool import family2


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def domain(name, data):
    assert set(data) == {'n','start','rules','budget','text'}
    n = data['n']
    assert integer(n,1,3) and integer(data['start'],0,n-1)
    assert integer(data['budget'],0,16 if name == 'bounded_derivation_count' else 7)
    assert type(data['text']) is str and len(data['text']) <= 7 and set(data['text']) <= set('ab')
    assert type(data['rules']) is list and len(data['rules']) <= 6
    for rule in data['rules']:
        assert type(rule) is list and len(rule) == 4
        lhs,rhs,resource,cost = rule
        assert integer(lhs,0,n-1) and integer(resource,1,3) and integer(cost,-5,5)
        assert type(rhs) is list and len(rhs) <= 2
        assert (not rhs or (len(rhs) == 1 and type(rhs[0]) is str and rhs[0] in ('a','b'))
                or all(integer(x,0,n-1) for x in rhs))


def observations(task, function):
    rows = []
    for arg, expected in task['cases']:
        argument = copy.deepcopy(arg)
        actual = function(argument)
        rows.append(dict(actual=grading.typed(actual),input_after=grading.typed(argument),same_object=actual is argument))
    return json.dumps({'results':rows})


class GrammarContracts(unittest.TestCase):
    def test_domain_fresh_reference_oracle_and_transport(self):
        for task in family2.make_tasks():
            self.assertTrue(15 <= len(task['cases']) <= 25)
            for argument,expected in task['cases']:
                domain(task['function'],argument)
                before = copy.deepcopy(argument)
                namespace = {};exec(task['reference'],namespace)
                actual = namespace[task['function']](argument)
                self.assertTrue(grading.exact(actual,expected),(task['id'],argument,actual,expected))
                if argument['budget'] <= 7:
                    self.assertTrue(grading.exact(expected,family2.oracle(task['function'],argument)))
                else:
                    self.assertEqual(expected,((5**16-1)//4) % 1000000007)
                self.assertEqual(argument,before)
            namespace = {};exec(task['reference'],namespace)
            output = observations(task,namespace[task['function']])
            self.assertLess(len(output.encode()),40000)
            self.assertEqual(grading.score(task,output)[:2],('pass',len(task['cases'])))

    def test_worked_literals(self):
        parse,count,edit = family2.make_tasks()
        self.assertEqual([parse['cases'][i][1] for i in (0,1,2,4,5,7,8,9)], [None,None,2,-3,-9,-3,-3,2])
        self.assertEqual(count['cases'][7][1],2)
        self.assertEqual(count['cases'][5][1],7)
        self.assertEqual(count['cases'][8][1],3)
        self.assertEqual(edit['cases'][10][1],2)
        self.assertEqual(edit['cases'][12][1],1)
        self.assertIsNone(edit['cases'][0][1])

    def test_semantic_mutants_are_rejected(self):
        parse,count,edit = family2.make_tasks()
        mutants = [
            (parse,parse['reference'].replace('range(1, budget + 1)','range(1, budget)')),
            (parse,parse['reference'].replace("values = [row[data['text']] for row in _chart(data) if data['text'] in row]", "values = [row[data['text']] for row in _chart(data)[-1:] if data['text'] in row]")),
            (count,count['reference'].replace("for lhs, rhs, resource, cost in data['rules']:","for lhs, rhs, resource, cost in [r for i,r in enumerate(data['rules']) if r not in data['rules'][:i]]:")),
            (count,count['reference'].replace(' % 1000000007','')),
            (edit,edit['reference'].replace("_distance(data['text'], word)","abs(len(data['text'])-len(word))")),
            (edit,edit['reference'].replace("default=None","default=0")),
        ]
        for task,source in mutants:
            namespace = {};exec(source,namespace)
            self.assertEqual(grading.score(task,observations(task,namespace[task['function']]))[0],'fail')


if __name__ == '__main__':
    unittest.main()
