"""Original scope supplements preserve requirements and never replay unknown effects."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import issue_admission
import issue_atom as atom
import issue_execution
import supervisor_admission
from test_issue_admission import issue_fixture


class ScopeAmendmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.issue, self.envelope = issue_fixture()
        self.envelope['execution']['control_root'] = str(self.directory / 'control')
        self.body = self.issue['body'] + atom.marker('d' * 64) + '\n'

    def test_supplement_preserves_every_requirement_and_original_marker(self):
        changed = issue_admission.supplemented_body(self.body, ['test_manager.py'])
        before = issue_admission.parse_contract(self.body)
        after = issue_admission.parse_contract(changed)
        self.assertEqual(after, {**before, 'write_paths': sorted(before['write_paths'] + ['test_manager.py'])})
        self.assertTrue(changed.startswith('Free surrounding prose.\n'))
        self.assertTrue(changed.endswith(atom.marker('d' * 64) + '\n'))
        for added in ([], ['allowed.py'], ['../outside.py']):
            with self.subTest(added=added), self.assertRaises(issue_admission.AdmissionRefusal):
                issue_admission.supplemented_body(self.body, added)

    def test_standard_envelope_still_requires_exact_provider_scope(self):
        changed = issue_admission.supplemented_body(self.issue['body'], ['test_manager.py'])
        issue = {**self.issue, 'body': changed}
        envelope = {**self.envelope, 'body_sha256': issue_admission.body_digest(changed),
                    'write_paths': [*self.envelope['write_paths'], 'test_manager.py']}
        binding = issue_admission.validate_issue(issue, envelope)
        self.assertIn('test_manager.py', binding['write_paths'])
        self.assertFalse(binding['authorizes_landing'])
        with self.assertRaises(issue_admission.AdmissionRefusal):
            issue_admission.validate_issue(self.issue, envelope)

    def blocked_fixture(self):
        execution = self.envelope['execution']
        session = 'original-session'
        events = Path(execution['control_root']) / '.noodle/sessions' / session / 'events.ndjson'
        events.parent.mkdir(parents=True)
        event = {'type': 'stage_message', 'session_id': session, 'payload': {
            'order_id': execution['order_id'], 'stage_index': 0,
            'outcome': 'blocked', 'blocking': True, 'message': 'Missing admitted adapter.'}}
        events.write_text(json.dumps(event) + '\n')
        attempt = {'attempt_id': 'original-attempt', 'session_id': session,
                   'status': 'completed', 'worktree_name': execution['worktree']}
        review = {'order_id': execution['order_id'], 'stage_index': 0, 'session_id': session,
                  'worktree_name': execution['worktree'], 'worktree_path': str(
                      Path(execution['control_root']) / '.worktrees' / execution['worktree'])}
        owner = {'state': {'orders': {execution['order_id']: {'stages': [
            {'status': 'review', 'attempts': [attempt]}]}}, 'pending_reviews': {execution['order_id']: review}}}
        return owner, events, event

    def test_blocked_diagnostic_binds_review_session_event_and_original_message(self):
        owner, events, event = self.blocked_fixture()
        result = issue_execution.blocked_outcome(self.envelope, owner)
        self.assertEqual(result['message'], event['payload'])
        self.assertEqual(result['source'], {'path': str(events), 'sha256': atom.digest_file(events)})
        original = copy.deepcopy(owner)
        for field, value in (('session_id', 'foreign-session'), ('stage_index', 1),
                             ('worktree_name', 'foreign-worktree')):
            with self.subTest(field=field):
                owner = copy.deepcopy(original)
                owner['state']['pending_reviews'][self.envelope['execution']['order_id']][field] = value
                with self.assertRaisesRegex(issue_admission.AdmissionRefusal, 'blocked.review.identity'):
                    issue_execution.blocked_outcome(self.envelope, owner)
        event['session_id'] = 'foreign-session'
        events.write_text(json.dumps(event) + '\n')
        with self.assertRaisesRegex(issue_admission.AdmissionRefusal, 'blocked.identity'):
            issue_execution.blocked_outcome(self.envelope, original)

    def test_unknown_issue_write_stops_without_second_provider_effect(self):
        auth = {'control_root': self.envelope['execution']['control_root'], 'repository': 'ed3c/soodles',
                'issue': {'title': 'Original', 'body': self.issue['body']}}
        updated = issue_admission.supplemented_body(self.issue['body'], ['test_manager.py'])
        selected = {**auth, 'issue': {'title': 'Original', 'body': updated, 'number': 18}}
        stage = {'status': 'review', 'attempts': []}
        events = self.directory / 'blocked-events.ndjson'
        events.write_text('original blocked event\n')
        blocked = {'message': {'outcome': 'blocked'},
                   'source': {'path': str(events), 'sha256': atom.digest_file(events)}}
        state = {'phase': 'execution', 'publication': None, 'writes': {}, 'issue': {'number': 18},
                 'scope_amendment': {'selection': {'sha256': 'a' * 64}, 'prior': {
                     'envelope': {'path': '/original/envelope.json', 'sha256': 'b' * 64},
                     'noodle_start': {}, 'stage': stage, 'blocked': blocked}}}
        paths = {'state': self.directory / 'state.json'}
        provider = Mock()
        provider.issue.return_value = {**self.issue, 'title': 'Original'}
        provider.update_issue_body.side_effect = atom.MutationUnknown('lost response')
        packet = {'selection': {'candidate_head': 'c' * 40}, 'output': str(self.directory / 'output')}
        owner = {'state': {'orders': {self.envelope['execution']['order_id']: {'stages': [stage]}}}}
        with patch.object(atom, 'scope_packet', return_value=packet), \
                patch.object(atom, 'scope_projection', return_value=(selected, paths)), \
                patch.object(issue_admission, 'load_external_envelope', return_value=self.envelope), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'), \
                patch.object(issue_execution, 'read_owner', return_value=owner), \
                patch.object(issue_execution, 'blocked_outcome', return_value=blocked), \
                patch.object(issue_execution, 'validate_worktree'), \
                patch.object(supervisor_admission, 'prepare') as prepare:
            result = atom.advance_scope_amendment(auth, paths, state, provider, {})
            self.assertEqual(result['action'], 'scope_issue_readback_pending')
            saved = json.loads(paths['state'].read_text())
            self.assertEqual(saved['writes']['issue_scope']['status'], 'offered')
            with self.assertRaisesRegex(atom.AtomRefusal, 'scope.issue.outcome'):
                atom.advance_scope_amendment(auth, paths, state, provider, {})
            provider.update_issue_body.assert_called_once_with(18, updated)
            prepare.assert_not_called()
            self.assertIsNone(state['publication'])

    def test_control_reentry_observes_ack_without_appending_again(self):
        root = self.directory / 'control'
        runtime = root / '.noodle'
        runtime.mkdir(parents=True)
        state = {}
        paths = {'state': self.directory / 'state.json'}
        command = {'id': 'selected-edit', 'action': 'edit-item', 'order_id': 'original', 'prompt': 'fixed'}
        auth = {'control_root': str(root)}
        self.assertIsNone(atom.amendment_control(auth, paths, state, 'scope_edit', command))
        raw = (runtime / 'control.ndjson').read_bytes()
        self.assertIsNone(atom.amendment_control(auth, paths, state, 'scope_edit', command))
        self.assertEqual((runtime / 'control.ndjson').read_bytes(), raw)
        (runtime / 'control.ndjson').write_bytes(b'')
        ack = {'id': command['id'], 'action': command['action'], 'status': 'ok'}
        (runtime / 'control-ack.ndjson').write_text(json.dumps(ack) + '\n')
        self.assertEqual(atom.amendment_control(auth, paths, state, 'scope_edit', command), ack)
        self.assertEqual((runtime / 'control.ndjson').read_bytes(), b'')

    def test_correction_readback_starts_from_raw_authority_after_scope_projection(self):
        raw = {'repository': 'ed3c/soodles', 'control_root': str(self.directory / 'control'),
               'issue': {'title': 'Original', 'body': self.issue['body']}, 'task': 'Original task',
               'carrier': {}, 'noodle': {}, 'landing_owner': {'fixed': True},
               'lifecycle_owner': {'path': '/original/issue-atom'}}
        source = self.directory / 'authorization.json'
        source.write_text(json.dumps(raw))
        reference = {'path': str(source), 'sha256': atom.digest_file(source)}
        paths = atom.artifact_paths(source)
        state = {'scope_amendment': {'selection': 'fixture'}}
        atom.save_json(paths['state'], state)
        effective = {**raw, 'issue': {**raw['issue'], 'number': 18,
            'body': issue_admission.supplemented_body(raw['issue']['body'], ['test_manager.py'])}}
        current = {'path': '/selected/issue-atom'}
        already_selected = {**effective, 'lifecycle_owner': current}
        target = self.directory / 'correction'
        target.mkdir()
        selection = supervisor_admission._correction_selection(
            already_selected, reference, effective['issue'], {'head': 'a' * 40})
        atom.save_json(target / 'selection.json', selection)
        atom.save_json(target / 'correction-binding.json', {'schema': 1, 'prior_atom': reference,
            'output': str(target), 'selection_sha256': atom.digest_file(target / 'selection.json')})
        with patch.object(atom, 'resumed_lifecycle', return_value={**raw, 'lifecycle_owner': current}) as resumed, \
                patch.object(atom, 'scope_projection', return_value=(effective, paths)), \
                patch.object(supervisor_admission, 'authorize', return_value={'status': 'prepared'}):
            result = supervisor_admission._correction_readback(target, already_selected, reference)
        self.assertEqual(result['status'], 'prepared')
        resumed.assert_called_once_with(raw, state)
        self.assertEqual(json.loads(source.read_text()), raw)

    def test_scope_bundle_receipt_is_atomic_and_existing_bundle_readback_does_not_write(self):
        import test_issue_atom
        fixture = test_issue_atom.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        provider = test_issue_atom.Provider()
        fixture.ready_issue(provider)
        order_id = issue_admission.scoped_order_id(131, fixture.root)
        name = order_id + '-0-execute'
        subprocess.run(['git', 'worktree', 'add', '-b', name,
                        str(fixture.root / '.worktrees' / name), fixture.base],
                       cwd=fixture.root, check=True, capture_output=True)
        output = fixture.outer / 'scope-admission'
        args = (provider.value, {**fixture.authorization['carrier'], 'noodle': fixture.authorization['noodle']},
                fixture.root, output)
        options = {'task': fixture.authorization['task'], 'wire_host': True, 'correction': True,
                   'runtime_root': Path(atom.__file__).parent}
        receipt = supervisor_admission.prepare(*args, environ=fixture.env, **options)
        self.assertEqual(json.loads((output / 'prepared.json').read_text()), receipt)
        before = {str(path.relative_to(output)): path.read_bytes() for path in output.rglob('*') if path.is_file()}
        with patch.object(supervisor_admission.tempfile, 'mkdtemp', side_effect=AssertionError('unexpected write')):
            self.assertEqual(supervisor_admission.prepare(*args, environ={}, readback=True, **options), receipt)
            (output / 'runtime/issue_execution.py').write_text('changed source')
            with self.assertRaisesRegex(issue_admission.AdmissionRefusal, 'scope.prepared.component'):
                supervisor_admission.prepare(*args, environ={}, readback=True, **options)
        after = {str(path.relative_to(output)): path.read_bytes() for path in output.rglob('*') if path.is_file()}
        self.assertEqual({k: v for k, v in after.items() if k != 'runtime/issue_execution.py'},
                         {k: v for k, v in before.items() if k != 'runtime/issue_execution.py'})


    def test_archived_publication_selects_terminal_attempt_and_retains_failed_session(self):
        from test_issue_execution import IssueExecutionTests
        fixture = IssueExecutionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        directory = fixture.archived_completion()
        events = directory / "events.ndjson"
        event = json.loads(events.read_text())
        event["session_id"] = fixture.session
        events.write_text(json.dumps(event) + "\n")
        previous = fixture.runtime / "sessions" / "retained-failed-session"
        previous.mkdir()
        for name in ("spawn.json", "process.json"):
            value = json.loads((directory / name).read_text())
            value["session_id"] = previous.name
            (previous / name).write_text(json.dumps(value))
        old_dispatch = copy.deepcopy(fixture.snapshot["effect_ledger"][1])
        old_dispatch["effect_id"] = old_dispatch["effect"]["effect_id"] = "prior-dispatch"
        old_dispatch["effect"]["payload"]["attempt_id"] = "prior-failed-attempt"
        fixture.snapshot["effect_ledger"].append(old_dispatch)
        fixture.save_owner()
        publication = {"order_id": "soodles-18", "stage_index": 0,
            "worktree_name": fixture.envelope["execution"]["worktree"],
            "attempt_id": "soodles-18-0-attempt-0", "session_id": fixture.session}
        result = issue_execution.completed_original_order(fixture.envelope, fixture.snapshot, publication)
        self.assertEqual(result["quiescent_sessions"][0]["session_id"], fixture.session)
        self.assertEqual(result["retained_quiescent_sessions"][0]["session_id"], previous.name)
        self.assertEqual(result["dispatch_effect"], "event-2-effect-0")
        for key, value in (("attempt_id", "foreign-attempt"), ("session_id", "foreign-session")):
            with self.subTest(key=key), self.assertRaises(issue_admission.AdmissionRefusal):
                issue_execution.completed_original_order(fixture.envelope, fixture.snapshot, {**publication, key: value})


if __name__ == '__main__':
    unittest.main()
