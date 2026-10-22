import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit_run',HERE/'run.py')
run=importlib.util.module_from_spec(spec); spec.loader.exec_module(run)


class AuditTests(unittest.TestCase):
    def test_generator_contracts_and_oracles(self):
        for module in run.modules():
            self.assertTrue(module.verify_oracles())
            for family in range(1,7):
                generate=getattr(module,f'generate_f{family}',None)
                if generate is None: continue
                first=generate(); self.assertEqual(first,generate())
                self.assertGreaterEqual(len(first),100)
                for case in first:
                    original=copy.deepcopy(case['argument'])
                    getattr(module,f'validate_f{family}')(case['argument'])
                    self.assertEqual(getattr(module,f'oracle_f{family}')(case['argument']),case['expected'])
                    self.assertEqual(case['argument'],original)
                self.assertEqual(sum(len(b) for b in run.batches(first)),len(first))

    def test_protocol_output_limit(self):
        huge=dict(id='large',category='test',argument={'x':'a'*50000},expected=0)
        with self.assertRaisesRegex(ValueError,'output'):
            list(run.batches([huge]))

    def test_preservation(self):
        paths=run.subprocess.check_output(['git','ls-tree','-r','--name-only',run.BASE],cwd=run.ROOT,text=True).splitlines()
        protected={p:run.hashlib.sha256(run.subprocess.check_output(['git','show',run.BASE+':'+p],cwd=run.ROOT)).hexdigest() for p in paths if p!='README.md' and not p.startswith('docs/')}
        for path,expected in protected.items():
            if path=='grading.py' or path.startswith(('calibration/','pilots/','experiments/')):
                self.assertEqual(run.digest(run.ROOT/path),expected,path)

    def test_sandbox_boundary(self):
        task=dict(id='f',function='f')
        case=dict(id='case',category='test',argument={'x':1},expected=2)
        with patch.object(run.grading,'evaluate',return_value=('pass',1,'')) as sandbox:
            record=run.execute(task,[case],'candidate source',{'image':'pinned','timeout_seconds':4})
        self.assertEqual(record['status'],'pass')
        self.assertEqual(sandbox.call_args.args[1:3],('candidate source','pinned'))
        self.assertEqual(sandbox.call_args.kwargs,{'timeout':4})

    def test_write_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'record.json'
            run.write(path,{'first':1})
            with self.assertRaises(FileExistsError): run.write(path,{'second':2})
            self.assertEqual(json.loads(path.read_text()),{'first':1})

    def test_hash_mismatch_aborts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'frozen').mkdir()
            (root/'source.py').write_text('changed')
            run.write(root/'frozen/manifest.json',{'source_sha256':{'source.py':'incorrect'},'original_sha256':{},'answers_sha256':{}})
            with patch.object(run,'HERE',root),patch.object(run,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'provenance changed'):
                    run.verify_frozen()

    def test_failure_isolates_every_case(self):
        cases=[dict(id=f'F5-{i}',category='test',argument={'x':i},expected=i) for i in range(2)]
        task=dict(id='task',family='F5',function='task',cases=cases)
        manifest={'batch_size':8}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'calibration/round2').mkdir(parents=True)
            run.write(root/'calibration/round2/tasks.json',[dict(id='task',reference='reference')])
            def result(task,batch,answer,manifest):
                return dict(status='fail',passed=0,total=len(batch),detail='',elapsed_seconds=0,case_ids=[c['id'] for c in batch])
            with patch.object(run,'ROOT',root),patch.object(run,'verify_frozen',return_value=(manifest,[task])),patch.object(run,'digest',return_value='sha'),patch.object(run,'execute',side_effect=result) as execute:
                run.run('preflight',root/'results')
                self.assertEqual(execute.call_count,3)
            self.assertEqual(len(list((root/'results').glob('reference-*.json'))),2)
            self.assertFalse(json.loads((root/'results/summary.json').read_text())['all_pass'])

    def test_invalid_family56(self):
        module=run.modules()[2]
        for family in [5,6]:
            arg=getattr(module,f'generate_f{family}')()[0]['argument']
            bad=copy.deepcopy(arg);bad['extra']=0
            with self.assertRaises(ValueError): getattr(module,f'validate_f{family}')(bad)
            bad=copy.deepcopy(arg);bad['state']=True
            with self.assertRaises(ValueError): getattr(module,f'validate_f{family}')(bad)
        a=module.generate_f6()[0]['argument'];a['alphabet']=['aa']
        with self.assertRaises(ValueError):module.validate_f6(a)


if __name__=='__main__': unittest.main()
