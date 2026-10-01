"""Push process evidence and bounded same-owner continuation, without live GitHub."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

import candidate_publication as publication
import issue_atom as atom


class PublisherReceiptTests(unittest.TestCase):
    def test_receipt_precedes_spawn_and_redacts_credentials(self):
        token = 'private-test-token'
        encoded = base64.b64encode(('x-access-token:' + token).encode()).decode()
        records = []
        provider = Mock(token=token, repository='ed3c/soodles')
        def execute(argv, **kwargs):
            self.assertEqual(records[0]['process'], 'started')
            self.assertEqual(argv[-2], 'https://github.com/ed3c/soodles.git')
            self.assertNotIn(token, ' '.join(argv))
            self.assertNotIn('GIT_TRACE', kwargs['env'])
            self.assertEqual(kwargs['env']['GIT_CONFIG_VALUE_0'], 'Authorization: Basic ' + encoded)
            self.assertEqual(kwargs['env']['GIT_CONFIG_KEY_2'], 'core.askPass')
            self.assertEqual(kwargs['env']['GIT_CONFIG_VALUE_2'], '')
            return subprocess.CompletedProcess(argv, 1, token + '\n', 'Authorization: Basic ' + encoded)
        with patch.dict('os.environ', {'GIT_TRACE': '1', 'GIT_CONFIG_VALUE_19': token}), \
                patch.object(publication.subprocess, 'run', side_effect=execute):
            receipt = atom.authenticated_push(provider, record=records.append)(
                Path.cwd(), 'push', '--porcelain', '--force-with-lease=refs/heads/x:old',
                'origin', 'new:refs/heads/x')
        self.assertEqual(receipt['process'], 'completed')
        self.assertEqual(receipt['exit_status'], 1)
        self.assertNotIn(token, json.dumps(records))
        self.assertNotIn(encoded, json.dumps(records))
        self.assertEqual(len(records), 2)

    def test_only_complete_exact_single_ref_rejection_proves_no_update(self):
        receipt = {'process': 'completed', 'exit_status': 1, 'argv': ['git', 'push', 'new:refs/heads/x'],
                   'stdout': '!\tnew:refs/heads/x\t[remote rejected] (policy)\n'}
        self.assertEqual(publication.push_disposition(receipt), 'rejected')
        for changed in ({'exit_status': 0}, {'exit_status': -9}, {'process': 'timed_out'},
                        {'stdout': '!\tnew:refs/heads/other\t[rejected] (policy)\n'},
                        {'stdout': '!\tnew:refs/heads/x\t[remote failure] (lost)\n'},
                        {'stdout': receipt['stdout'] * 2}, {'stdout': 'connection lost'}):
            with self.subTest(changed=changed):
                self.assertEqual(publication.push_disposition({**receipt, **changed}), 'unknown')

    def test_timeout_and_spawn_failure_leave_diagnostic_receipts(self):
        for error, expected in ((subprocess.TimeoutExpired(['git'], 30, output=b'partial', stderr=b'lost'), 'timed_out'),
                                (FileNotFoundError(2, 'Git missing'), 'not_started')):
            records = []
            with self.subTest(error=error), patch.object(publication.subprocess, 'run', side_effect=error):
                receipt = publication.run_push(Path.cwd(), ['git', 'push'], record=records.append)
            self.assertEqual(receipt['process'], expected)
            self.assertIsNone(receipt['exit_status'])
            self.assertEqual(records[0]['process'], 'started')
            self.assertEqual(records[-1], receipt)
            self.assertEqual(publication.push_disposition(receipt), 'unknown')

    def test_interruption_persists_unknown_result_and_propagates(self):
        for error in (KeyboardInterrupt(), SystemExit(1)):
            records = []
            with self.subTest(error=error), patch.object(publication.subprocess, 'run', side_effect=error):
                with self.assertRaises(type(error)):
                    publication.run_push(Path.cwd(), ['git', 'push'], record=records.append)
            self.assertEqual([r['process'] for r in records], ['started', 'interrupted'])
            self.assertIsNotNone(records[-1]['seconds'])
            self.assertEqual(publication.push_disposition(records[-1]), 'unknown')

    def fixture(self):
        import test_candidate_publication
        fixture = test_candidate_publication.CandidatePublicationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        prior, acceptance, claim = fixture.amended_candidate()
        fixture.provider.repository = 'ed3c/soodles'
        fixture.provider.token = 'test-token'
        paths = {'state': fixture.root.parent / 'push-state.json'}
        state = {'writes': {}}
        return fixture, prior, acceptance, claim, paths, state

    def test_rejected_offer_persists_then_corrected_capability_can_continue_same_pr_once(self):
        f, prior, acceptance, claim, paths, state = self.fixture()
        auth = {'prior_publication': prior}
        original_run = subprocess.run
        attempts = []
        capability_fixed = False
        def execute(argv, **kwargs):
            if argv[:2] != ['git', 'push']:
                return original_run(argv, **kwargs)
            attempts.append(argv)
            saved = json.loads(paths['state'].read_text())
            self.assertEqual(saved['publication_push_receipts'][-1]['process'], 'started')
            self.assertEqual(saved['writes']['candidate_amendment']['old_head'], prior['head'])
            if not capability_fixed:
                return subprocess.CompletedProcess(argv, 1, '!\t' + argv[-1] + '\t[remote rejected] (capability)\n', 'rejected')
            from test_candidate_publication import exact_pull
            f.provider.ref = claim['head']
            f.provider.pull_value = exact_pull(prior['pr']['number'], prior['branch'], claim['head'], 'main', 'Refs ed3c/soodles#128')
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch.object(publication.subprocess, 'run', side_effect=execute):
            with self.assertRaisesRegex(publication.PublicationRefusal, 'github.push.rejected'):
                atom.publish_candidate(auth, state, paths, claim, acceptance, f.provider)
            self.assertEqual(len(state['publication_push_receipts']), 1)
            capability_fixed = True  # Supervisor corrects the named capability before re-entry.
            state = json.loads(paths['state'].read_text())
            result = atom.publish_candidate(auth, state, paths, claim, acceptance, f.provider)
            self.assertEqual(result['pr'], prior['pr'])
            atom.publish_candidate(auth, state, paths, claim, acceptance, f.provider)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0], attempts[1])
        self.assertEqual(len(state['publication_push_receipts']), 2)

    def test_unknown_legacy_offer_or_timeout_never_reoffers(self):
        f, prior, acceptance, claim, paths, state = self.fixture()
        auth = {'prior_publication': prior}
        intent = {'old_head': prior['head'], 'new_head': claim['head'], 'pr': prior['pr']['number'], 'status': 'offered'}
        state['writes']['candidate_amendment'] = intent
        with patch.object(atom, 'authenticated_push', return_value=Mock(side_effect=AssertionError('replay'))):
            for receipts in ([], [{'process': 'timed_out'}], [{'process': 'started'}]):
                state['publication_push_receipts'] = receipts
                with self.assertRaisesRegex(publication.PublicationRefusal, 'github.branch.outcome'):
                    atom.publish_candidate(auth, state, paths, claim, acceptance, f.provider)

    def test_repeated_rejections_stop_at_two_and_preserve_both_receipts(self):
        f, prior, acceptance, claim, paths, state = self.fixture()
        original_run = subprocess.run
        attempts = []
        def execute(argv, **kwargs):
            if argv[:2] != ['git', 'push']:
                return original_run(argv, **kwargs)
            attempts.append(argv)
            return subprocess.CompletedProcess(argv, 1, '!\t' + argv[-1] + '\t[rejected] (denied)\n', '')
        with patch.object(publication.subprocess, 'run', side_effect=execute):
            for _ in range(3):
                with self.assertRaises(publication.PublicationRefusal):
                    atom.publish_candidate({'prior_publication': prior}, state, paths, claim, acceptance, f.provider)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(len(state['publication_push_receipts']), 2)

    def test_rejection_for_different_worktree_ref_or_lease_cannot_reoffer(self):
        f, prior, acceptance, claim, paths, state = self.fixture()
        original_run = subprocess.run
        def execute(argv, **kwargs):
            if argv[:2] != ['git', 'push']:
                return original_run(argv, **kwargs)
            return subprocess.CompletedProcess(argv, 1, '!\t' + argv[-1] + '\t[rejected] (denied)\n', '')
        with patch.object(publication.subprocess, 'run', side_effect=execute):
            with self.assertRaises(publication.PublicationRefusal):
                atom.publish_candidate({'prior_publication': prior}, state, paths, claim, acceptance, f.provider)
        original = copy.deepcopy(state)
        for field in ('cwd', 'lease', 'ref'):
            state = copy.deepcopy(original)
            receipt = state['publication_push_receipts'][0]
            if field == 'cwd':
                receipt['cwd'] += '-foreign'
            elif field == 'lease':
                receipt['argv'][3] += '0'
            else:
                receipt['argv'][-1] += '-foreign'
                receipt['stdout'] = '!\t' + receipt['argv'][-1] + '\t[rejected] (denied)\n'
            with self.subTest(field=field), patch.object(atom, 'authenticated_push',
                    return_value=Mock(side_effect=AssertionError('foreign receipt replay'))):
                with self.assertRaises(publication.PublicationRefusal):
                    atom.publish_candidate({'prior_publication': prior}, state, paths, claim, acceptance, f.provider)
