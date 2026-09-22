"""Frozen supervisor controls; candidate modules are subjects, not the judge."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(sys.argv.pop(1)).resolve()))
atom = importlib.import_module('issue_atom')

class ContinuationControls(unittest.TestCase):
    def test_native_prepublication_uses_native_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = {'scope':'native publication readiness','authorizes_landing':False}
            with patch('soodles.acceptance_verify', side_effect=AssertionError('Linux pre-publication dependency')), \
                 patch.object(atom.candidate_publication, 'native_readiness', return_value=receipt, create=True):
                value = atom._accept({'noodle':{'path':'/fixture/noodle','sha256':'a'*64}},
                                     {'worktree_path':str(root)}, root/'readiness.json')
            self.assertEqual(value, receipt)

    def test_queued_ci_is_wait_not_missing_job_refusal(self):
        class Provider:
            def workflow_runs(self, head):
                return {'workflow_runs':[{'id':1,'head_sha':head,'event':'pull_request',
                    'path':'.github/workflows/runtime.yml','status':'queued'}]}
            def jobs(self, run):
                return {'jobs':[]}
        auth={'workflow':{'path':'.github/workflows/runtime.yml','job':'runtime-evidence','step':'Canonical'}}
        run, jobs = atom.select_run(Provider(), auth, 'b'*40)
        self.assertEqual(run['status'], 'queued')

    def test_failed_ci_stays_refusal(self):
        class Provider:
            def workflow_runs(self, head):
                return {'workflow_runs':[{'id':1,'head_sha':head,'event':'pull_request',
                    'path':'.github/workflows/runtime.yml','status':'completed','conclusion':'failure'}]}
            def jobs(self, run):
                return {'jobs':[{'name':'runtime-evidence','status':'completed','conclusion':'failure',
                    'steps':[{'name':'Canonical','conclusion':'failure'}]}]}
        auth={'workflow':{'path':'.github/workflows/runtime.yml','job':'runtime-evidence','step':'Canonical'}}
        with self.assertRaises(atom.AtomRefusal):
            atom.select_run(Provider(), auth, 'b'*40)

    def test_same_entry_continues_normal_wait(self):
        pending={'status':'pending','waiting_on':'GitHub Actions','next':{'argv':['same']}}
        resolved={'status':'resolved','next':None}
        with patch.object(atom, 'run', side_effect=[pending,resolved]) as run:
            value=atom.drive('/fixture/authorization.json', timeout=5, interval=0, sleep=lambda _:None)
        self.assertEqual(value, resolved)
        self.assertEqual(run.call_count, 2)

    def test_unknown_write_refusal_is_not_retried(self):
        error=atom.AtomRefusal('github.issue.outcome','unknown','fresh_provider_issue_readback_without_retry')
        with patch.object(atom, 'run', side_effect=error) as run:
            with self.assertRaises(atom.AtomRefusal):
                atom.drive('/fixture/authorization.json', timeout=5, interval=0, sleep=lambda _:None)
        self.assertEqual(run.call_count, 1)

if __name__=='__main__':
    unittest.main()
