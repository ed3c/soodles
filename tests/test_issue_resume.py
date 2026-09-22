"""Resume must preserve predecessor truth and existing admission effects."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

import issue_admission
import issue_execution
import test_issue_execution


class IssueResumeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_issue_execution.IssueExecutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.archived_completion()
        f.git('worktree', 'remove', str(f.worktree))
        f.git('branch', '-D', f.envelope['execution']['worktree'])
        self.checkpoint = f.directory / 'A-checkpoint.json'
        self.state = {'schema': 2, 'phase': 'resolved', 'classification': 'RESOLVED',
            'claim': {'repository': 'ed3c/soodles', 'issue': 18, 'pr': 19,
                'head': f.envelope['base_head'], 'tree': f.git('rev-parse', 'HEAD^{tree}'),
                'base_head': f.envelope['base_head'], 'run_id': 1, 'run_attempt': 1,
                'worktree': f.envelope['execution']['worktree'], 'control_root': str(f.root),
                'verifier_sha256': 'f' * 64,
                'execution_envelope': {'path': str(f.path), 'sha256': f.pin}},
            'local': {'removed_worktree': f.envelope['execution']['worktree'],
                      'worktree_owner': 'Noodle', 'cleanup_mode': 'noodle'}}
        self.save()
        self.envelope = copy.deepcopy(f.envelope)
        self.envelope['issue'] = 20
        self.envelope['execution'].update(order_id='soodles-20', worktree='soodles-20-0-execute')
        self.path = f.directory / 'B-envelope.json'
        self.path.write_text(json.dumps(self.envelope))
        self.pin = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.issue = copy.deepcopy(f.issue)
        self.issue.update(number=20, url='https://api.github.com/repos/ed3c/soodles/issues/20',
                          html_url='https://github.com/ed3c/soodles/issues/20')
        self.mailbox = f.runtime / 'orders-next.json'

    def save(self):
        self.checkpoint.write_text(json.dumps(self.state))

    def resume(self):
        return issue_execution.resume(self.checkpoint, self.path, self.pin,
                                      self.fixture.root, reader=lambda _repository, _number: self.issue)

    def refused(self, field):
        before = (self.fixture.runtime / 'state.snapshot.json').read_bytes()
        with self.assertRaises(issue_admission.AdmissionRefusal) as raised:
            self.resume()
        self.assertEqual(raised.exception.invalid['field'], field)
        self.assertFalse(self.mailbox.exists())
        self.assertEqual(before, (self.fixture.runtime / 'state.snapshot.json').read_bytes())

    def test_pending_and_retained_owner_readback_do_not_republish(self):
        self.assertTrue(self.resume()['published'])
        before = self.mailbox.read_bytes(), self.mailbox.stat().st_ino, self.mailbox.stat().st_mtime_ns
        pending = self.resume()
        self.assertFalse(pending['published'])
        self.assertEqual(pending['next']['operation'], 'resume')
        self.assertEqual(before, (self.mailbox.read_bytes(), self.mailbox.stat().st_ino, self.mailbox.stat().st_mtime_ns))
        self.fixture.snapshot['effect_ledger'].append({'effect_id': 'B-dispatch',
            'effect': {'type': 'dispatch', 'payload': {'order_id': 'soodles-20'}}})
        self.fixture.save_owner()
        self.mailbox.unlink()
        retained = self.resume()
        self.assertEqual(retained['action'], 'previously_admitted')
        self.assertFalse(retained['published'])
        self.assertFalse(self.mailbox.exists())

    def test_unresolved_and_foreign_predecessor_refuse_before_publication(self):
        self.state['phase'] = 'reconciling'
        self.save()
        self.refused('resume.predecessor')
        self.state['phase'] = 'resolved'
        self.state['claim']['control_root'] = '/foreign'
        self.save()
        self.refused('resume.control_root')

    def test_cleanup_path_symlink_and_branch_residue_refuse(self):
        f = self.fixture
        f.worktree.symlink_to('/missing-target')
        self.refused('resume.cleanup.path')
        f.worktree.unlink()
        f.git('branch', f.envelope['execution']['worktree'])
        self.refused('resume.cleanup.branch')

    def test_registration_residue_refuses_even_without_path_or_branch(self):
        f = self.fixture
        f.git('worktree', 'add', '--detach', str(f.worktree))
        import shutil
        shutil.rmtree(f.worktree)
        self.refused('resume.cleanup.registration')

    def test_missing_original_completion_and_same_successor_refuse(self):
        self.fixture.snapshot['effect_ledger'] = []
        self.fixture.save_owner()
        with self.assertRaises(issue_admission.AdmissionRefusal):
            self.resume()
        self.assertFalse(self.mailbox.exists())
        self.path, self.pin = self.fixture.path, self.fixture.pin
        self.refused('resume.successor_identity')

    def test_conflicting_mailbox_and_stale_provider_preserve_effects(self):
        self.mailbox.write_text('{"orders": []}')
        before = self.mailbox.read_bytes(), self.mailbox.stat().st_ino
        with self.assertRaises(issue_admission.AdmissionRefusal):
            self.resume()
        self.assertEqual(before, (self.mailbox.read_bytes(), self.mailbox.stat().st_ino))
        self.mailbox.unlink()
        self.issue['body'] += '\nchanged'
        with self.assertRaises(issue_admission.AdmissionRefusal):
            self.resume()
        self.assertFalse(self.mailbox.exists())

    def test_current_owner_and_malformed_checkpoint_preserve_effects(self):
        self.fixture.snapshot['state']['orders']['soodles-20'] = {'stages': [{'attempts': [{'status': 'running'}]}]}
        self.fixture.save_owner()
        self.assertEqual(self.resume()['action'], 'owned')
        self.assertFalse(self.mailbox.exists())
        self.checkpoint.write_text('not json')
        self.refused('resume.checkpoint')


class ResumeEvidenceTests(unittest.TestCase):
    def test_frozen_evidence_discriminates_and_preserves_claim_scope(self):
        import importlib.util
        directory = Path(__file__).resolve().parents[1] / 'docs/experiments/interruption-resume'
        spec = importlib.util.spec_from_file_location('resume_evidence', directory / 'observer.py')
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
        result = observer.verify(directory)
        self.assertEqual(result['classification'], 'VERIFIED')
        self.assertFalse(result['authorizes_landing'])
