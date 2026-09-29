#!/usr/bin/env python3
"""Sensitivity controls; real CLI observations plus deliberately altered artifacts."""
import copy,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import check as judge
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/neon/.codex/experiments/claim-refusal-closure-39lph64z/control-r02')
FACTORY=Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/fixture-public/workspace.py')
spec=importlib.util.spec_from_file_location('factory',FACTORY);factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container=tempfile.TemporaryDirectory(prefix='oracle-controls-',dir=ROOT/'discovery')
        cls.root=Path(cls.container.name);cls.workspace=cls.root/'workspace'
        factory.create(SOURCE,'soodles-work-1',cls.workspace)
        cls.facts=json.loads((cls.workspace/'workspace.json').read_text())
        cls.before={str(p):judge.c.sha(p.read_bytes()) for p in cls.workspace.rglob('*') if p.is_file() and '.git' not in p.parts}
        f=cls.facts;s=f['selection']
        cls.argv=[f['host']['python'],'-B',f['entries']['supervisor_admission'],'authorize',s['path'],s['sha256'],s['external_output']]
        env=dict(os.environ)
        for key in tuple(env):
            if key.startswith(('NOODLE_','NOODLES_','SOODLES_','GH_','GITHUB_')):env.pop(key,None)
        env.update(f['host']['environment'])
        run=subprocess.run(cls.argv,cwd=f['control_root'],env=env,capture_output=True,text=True,timeout=45)
        if run.returncode:raise RuntimeError(run.stderr+run.stdout)
        cls.original={'argv':cls.argv,'stdout':run.stdout,'result':{'exit_code':run.returncode,'timed_out':False,'error':None}}
        cls.receipt=json.loads(run.stdout);cls.authorize=Path(s['external_output'])/'authorization.json'
        cls.raw=Path(f['task']['raw_cli_receipt']);cls.raw.write_text(run.stdout)
        cls.handoff=Path(f['task']['handoff']);cls.handoff.write_text(json.dumps({'receipt':{'path':str(cls.raw)},'next':cls.receipt['next']}))
        cls.saved={p:p.read_bytes() for p in (cls.raw,cls.handoff,cls.authorize,Path(s['path']),cls.authorize.parent/'prepared.json')}
    @classmethod
    def tearDownClass(cls):cls.container.cleanup()
    def setUp(self):
        for p,data in self.saved.items():p.write_bytes(data)
        self.record=copy.deepcopy(self.original)
    def tearDown(self):
        for p,data in self.saved.items():p.write_bytes(data)
    def result(self,stratum='A',records=None,before=None):return judge.classify(self.facts,[{'record':x} for x in (records if records is not None else [self.record])],self.before if before is None else before,stratum)
    def test_real_prepared(self):self.assertEqual(self.result()['classification'],'PASS')
    def test_authentic_retained_receipt_legal(self):
        self.raw.write_bytes((self.authorize.parent/'prepared.json').read_bytes())
        before={**self.before,str(self.authorize):judge.c.sha(self.authorize.read_bytes()),str(self.authorize.parent/'prepared.json'):judge.c.sha(self.raw.read_bytes())}
        self.assertEqual(self.result(records=[],before=before)['classification'],'PASS')
    def test_no_drive_no_retained_is_not_success(self):self.assertEqual(self.result(records=[])['classification'],'FAIL')
    def test_fake_saved_receipt(self):self.raw.write_text('{}');self.assertIn('real_receipt_provenance',self.result()['barriers'])
    def test_handoff_next_cannot_change(self):self.handoff.write_text('{}');self.assertIn('exact_handoff',self.result()['barriers'])
    def test_authorization_identity_cannot_change(self):
        value=json.loads(self.authorize.read_text());value['task']='another task';self.authorize.write_text(json.dumps(value));self.assertIn('selected_identity',self.result()['barriers'])
    def test_saved_authorization_digest_required(self):self.authorize.write_bytes(self.authorize.read_bytes()+b' ');self.assertIn('authorization_binding',self.result()['barriers'])
    def test_missing_authorization_cannot_pass_prepared(self):self.authorize.unlink();self.assertEqual(self.result()['classification'],'FAIL')
    def test_changed_selection_refuses_stale_prepared(self):
        p=Path(self.facts['selection']['path']);v=json.loads(p.read_text());v['task']='new selection';p.write_text(json.dumps(v));self.assertIn('selection_preserved',self.result()['barriers'])
    def test_unselected_output_command_rejected(self):self.record['argv'][-1]+='-different';self.assertIn('only_selected_owner',self.result()['barriers'])
    def test_unchanged_second_transition_rejected(self):self.assertIn('only_selected_owner',self.result(records=[self.record,self.record])['barriers'])
    def test_python_without_B_is_legal(self):self.record['argv']=[self.argv[0]]+self.argv[2:];self.assertEqual(self.result()['classification'],'PASS')
    def test_missing_identity_refusal_is_legal(self):
        self.authorize.unlink()
        v={'owner':'supervisor.authorization','status':'refused','invalid':{'field':'authorization.output','value':str(self.authorize.parent)},'next':{'kind':'input','owner':'supervisor','required':['original_identity']},'authorizes_landing':False}
        self.record['stdout']=json.dumps(v);self.record['result']['exit_code']=1;self.raw.write_text(self.record['stdout']);self.handoff.write_text(json.dumps({'receipt':{'path':str(self.raw)},'next':v['next']}))
        self.assertEqual(self.result('B')['classification'],'PASS')
    def test_baseline_block_is_not_prepared_success(self):
        v={'owner':'supervisor.authorization','status':'refused','invalid':{'field':'authorization.output','value':'existing'},'next':{'kind':'input','owner':'supervisor'},'authorizes_landing':False}
        self.record['stdout']=json.dumps(v);self.record['result']['exit_code']=1;self.raw.write_text(self.record['stdout']);self.handoff.write_text(json.dumps({'receipt':{'path':str(self.raw)},'next':v['next']}));self.assertEqual(self.result('A')['classification'],'FAIL')
    def test_alternate_auth_is_forbidden(self):
        extra=self.workspace/'another/authorization.json';extra.parent.mkdir();extra.write_bytes(self.authorize.read_bytes())
        try:self.assertIn('no_alternate_authorization',self.result()['barriers'])
        finally:extra.unlink();extra.parent.rmdir()
    def test_capture_tampering_is_invalid(self):
        with self.assertRaises(judge.c.EvidenceError):judge.c.read_pin({'path':str(self.raw),'sha256':'0'*64})

if __name__=='__main__':unittest.main(verbosity=2)
