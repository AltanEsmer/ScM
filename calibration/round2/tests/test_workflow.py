import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

class Workflow(unittest.TestCase):
    def test_inventory_and_prompt_roundtrip(self):
        builder = module('builder', ROOT / 'calibration/round2/build_pool.py')
        tasks = builder.inventory()
        self.assertEqual(len(tasks), 18)
        self.assertEqual(sum(t['role'] == 'development' for t in tasks), 6)
        for task in tasks:
            for variant in ['B0', 'A', 'B', 'C']:
                self.assertEqual(builder.decode(builder.render(task, variant), variant), task['clauses'])
    def test_balanced_schedule(self):
        builder = module('builder', ROOT / 'calibration/round2/build_pool.py')
        tasks = [t for t in builder.inventory() if t['role'] == 'heldout']
        rows = builder.pilot_schedule(tasks)
        self.assertEqual(len(rows), 360)
        for task in tasks:
            for position in range(3):
                counts = [sum(r['variant'] == v for i,r in enumerate(rows) if r['task'] == task['id'] and i % 3 == position) for v in 'ABC']
                self.assertLessEqual(max(counts) - min(counts), 1)


class Gate(unittest.TestCase):
    def setUp(self):
        self.gate = module('gate', ROOT / 'calibration/round2/select_pilot3.py')
        self.tasks = [dict(id=f'd{i}', family=f'F{i}', cases=[[{}, 1]]) for i in range(1,7)]
    def evidence(self, count):
        rows = []
        review = {}
        for i in range(1,7):
            for r in range(5):
                identity = f'd{i}_{r}'
                rows.append(dict(trial_id=identity, task=f'd{i}', status='fail' if i <= count and r == 0 else 'pass'))
                if i <= count and r == 0:
                    review[identity] = dict(case_indices=[0], reviewed_valid=True, family_valid=True, rationale='Independent golden mismatch confirmed')
        return rows, review
    def test_gate_zero_to_two_reject_three_and_all_six_select(self):
        for count in range(7):
            rows, reviews = self.evidence(count)
            result = self.gate.decide(self.tasks, rows, reviews)
            self.assertEqual(result['gate_satisfied'], count >= 3)
            self.assertEqual(result['eligible_families'], [f'F{i}' for i in range(1,count+1)])
    def test_unvalidated_and_errors_only_do_not_qualify(self):
        rows, reviews = self.evidence(3)
        self.assertFalse(self.gate.decide(self.tasks, rows)['gate_satisfied'])
        for row in rows:
            if row['status'] == 'fail': row['status'] = 'runtime_error'
        self.assertFalse(self.gate.decide(self.tasks, rows)['gate_satisfied'])
        with self.assertRaises(ValueError): self.gate.decide(self.tasks, rows, reviews)
    def test_defect_invalidation_unknown_and_bad_case_rejected(self):
        rows, reviews = self.evidence(3)
        reviews['d1_0']['family_valid'] = False
        self.assertFalse(self.gate.decide(self.tasks, rows, reviews)['gate_satisfied'])
        reviews['unknown'] = reviews['d1_0']
        with self.assertRaises(ValueError): self.gate.decide(self.tasks, rows, reviews)
        del reviews['unknown']
        reviews['d1_0']['case_indices'] = [-1]
        with self.assertRaises(ValueError): self.gate.decide(self.tasks, rows, reviews)

class Collection(unittest.TestCase):
    def setUp(self):
        import tempfile
        import shutil
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for relative in ['grading.py', 'experiments', 'calibration/round1/protocol.json', 'calibration/round2', 'pilots/pilot3']:
            source = ROOT / relative
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', 'records', 'dispatch', 'results', 'manifest.json'))
            else: shutil.copy2(source,target)
        self.runner = module('fixture_runner', self.repo / 'experiments/runner.py')
        self.root = self.repo / 'calibration/round2'
        self.runner.freeze(self.root)
    def collect(self, ordinal=1):
        from contextlib import redirect_stdout
        import io
        with redirect_stdout(io.StringIO()): self.runner.start(self.root,[ordinal])
        answer = self.repo / 'answer'
        answer.write_bytes(b'\xef\xbb\xbfdef solution(x):\r\n    return x\r\n')
        self.runner.attach(self.root, ordinal, f'session-{ordinal}')
        self.runner.record(self.root, ordinal, f'session-{ordinal}', answer)
        return self.runner.ordinal_trial(self.root,ordinal), answer.read_bytes()
    def test_first_bytes_no_overwrite_unique_sessions(self):
        trial, raw = self.collect()
        self.assertEqual((self.root / 'records' / trial.trial_id / 'answer.txt').read_bytes(), raw)
        with self.assertRaises((ValueError,FileExistsError)):
            self.runner.record(self.root,1,'session-1',self.repo/'answer')
        from contextlib import redirect_stdout
        import io
        with redirect_stdout(io.StringIO()): self.runner.start(self.root,[2])
        with self.assertRaises(ValueError): self.runner.attach(self.root,2,'session-1')
    def test_frozen_source_and_heldout_changes_rejected(self):
        (self.repo / 'pilots/pilot3/planned-trials.json').write_text('[]')
        with self.assertRaises(ValueError): self.runner.verify(self.root)
    def test_cartesian_duplicate_and_dimensions_rejected(self):
        path=self.root/'trials.json'
        rows=self.runner.load(path)
        rows[1]=rows[0]
        path.write_text(__import__('json').dumps(rows))
        with self.assertRaises(ValueError): self.runner.trials(self.root)
    def test_infrastructure_rows_and_stale_counts(self):
        from unittest.mock import patch
        self.collect(1)
        self.collect(2)
        with patch.object(self.runner.grading,'evaluate',side_effect=OSError('Docker unavailable')):
            with self.assertRaises(RuntimeError): self.runner.grade(self.root)
        rows=self.runner.report(self.root)
        self.assertEqual([r['status'] for r in rows[:3]],['infrastructure_error','not_evaluated','missing'])
        import csv
        path=self.root/'results/trials.csv'
        rows[0]['passed']='1'
        with path.open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        with self.assertRaises(ValueError): self.runner.report(self.root)

    def test_schedule_prefix_and_historical_concurrency(self):
        from contextlib import redirect_stdout
        import io
        import json
        with self.assertRaises(ValueError): self.runner.start(self.root,[2])
        with redirect_stdout(io.StringIO()): self.runner.start(self.root,[1,2,3])
        with self.assertRaises(ValueError): self.runner.start(self.root,[4])
        trial=self.runner.ordinal_trial(self.root,4)
        directory=self.root/'dispatch'/trial.trial_id
        directory.mkdir()
        (directory/'dispatch.json').write_text(json.dumps(dict(ordinal=4,trial_id=trial.trial_id,dispatch_observed_utc=self.runner.now())))
        with self.assertRaises(ValueError): self.runner.verify(self.root)

    def test_selection_subset_order_and_source_binding(self):
        from unittest.mock import patch
        import json
        for ordinal in range(1,31): self.collect(ordinal)
        seen = {}
        def evaluate(task, answer, image, timeout):
            family=task['family']
            seen[family]=seen.get(family,0)+1
            if family in ['F1','F2','F3'] and seen[family] == 1:
                return 'fail', 0, 'case 0 mismatch'
            return 'pass',len(task['cases']),''
        with patch.object(self.runner.grading,'evaluate',side_effect=evaluate):
            self.runner.grade(self.root)
        rows=self.runner.report(self.root)
        reviews={row['trial_id']:dict(case_indices=[0],reviewed_valid=True,family_valid=True,rationale='Literal mismatch verified independently') for row in rows if row['status']=='fail'}
        (self.root/'failure-validation.json').write_text(json.dumps(reviews))
        gate=module('fixture_gate',self.root/'select_pilot3.py')
        gate.runner=self.runner
        pilot=self.repo/'pilots/pilot3'
        result=gate.select(self.root,pilot)
        self.assertTrue(result['gate_satisfied'])
        self.assertEqual(len(self.runner.load(pilot/'tasks.json')),6)
        planned=self.runner.load(pilot/'planned-trials.json')
        expected=[r for r in planned if r['task'] in result['eligible_task_ids']]
        self.assertEqual(self.runner.load(pilot/'trials.json'),expected)
        self.assertEqual(len(self.runner.trials(pilot)),180)
        first=(pilot/'selection.json').read_bytes()
        gate.select(self.root,pilot)
        self.assertEqual((pilot/'selection.json').read_bytes(),first)
        self.runner.freeze(pilot)
        (self.root/'results/trials.csv').write_text('changed')
        with self.assertRaises(ValueError): self.runner.verify(pilot)

if __name__ == '__main__': unittest.main()
