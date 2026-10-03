"""Correction selection keeps the original authority and one fixed continuation."""
import copy
import json
import io
import subprocess
import sys
import urllib.error
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom
import test_issue_atom as atom_tests
import supervisor_admission as admission
import test_supervisor_authorization as authorization_tests
from test_admission_revision import RevisionFixture, ref


class TypedRevisionPriorTests(unittest.TestCase):
    def setUp(self):
        f = self.f = RevisionFixture()
        self.addCleanup(f.temp.cleanup)
        source_root = Path(atom.__file__).parent
        hashes = {name: atom.digest_file(source_root / name) for name in atom.LIFECYCLE_FILES}
        f.selection['lifecycle_owner'] = {'path': str(source_root / 'issue-atom'),
            'sha256': hashes['issue-atom'], 'source_sha256': atom.digest_bytes(json.dumps(
                hashes, sort_keys=True, separators=(',', ':')).encode())}
        f.auth['landing_owner'] = {'path': str(f.directory / 'fixed-judge/soodles.py')}
        issue, envelope, _, entry_path = f.entry()
        source = f.save('authorization.json', f.auth)
        packet = f.save('selection.json', {'schema': 1, 'authorization': ref(source),
            'selection': f.selection, 'output': str(f.directory)})
        paths = atom.artifact_paths(source)
        paths['directory'].mkdir()
        bundle = f.directory / 'admission'
        bundle.mkdir()
        (bundle / 'envelope.json').write_text(json.dumps(envelope))
        prior_attempt = {'status': 'completed', 'session_id': 'original-session'}
        entry = json.loads(entry_path.read_text())
        entry.update(selection_sha256=ref(packet)['sha256'], prior_attempts=[{
            **prior_attempt, 'status': 'failed', 'error': 'changes requested: ' + f.selection['reason']}])
        self.entry_path = bundle / 'revision-entry.json'
        atom.save_json(self.entry_path, entry)
        prepared = bundle / 'prepared.json'
        atom.save_json(prepared, {'envelope_sha256': atom.digest_file(bundle / 'envelope.json')})
        f.git('merge', '--no-edit', f.target, cwd=f.wt)
        head = f.git('rev-parse', 'HEAD', cwd=f.wt)
        tree = f.git('rev-parse', 'HEAD^{tree}', cwd=f.wt)
        self.state = {'authorization_sha256': ref(source)['sha256'], 'phase': 'ci',
            'issue': {'number': 18}, 'publication': {'head': head, 'tree': tree},
            'envelope_sha256': atom.digest_file(bundle / 'envelope.json'),
            'admission_sha256': atom.digest_file(prepared), 'scope_amendment': {
                'selection': ref(packet), 'prepared': ref(prepared), 'status': 'released',
                'prior': {'stage': {'attempts': [prior_attempt]}, 'blocked': entry['terminal']}}}
        atom.save_json(paths['state'], self.state)
        _, current_paths = atom.scope_projection(f.auth, self.state, paths)
        paths['claim'] = current_paths['claim']
        effective = {**f.auth, 'base_head': f.target, 'issue': issue,
            'noodle': atom.issue_admission.load_revision_native(f.selection['native_acceptance'], f.root)}
        self.authorization = {**effective, 'prior_atom': ref(source),
                              'prior_publication': self.state['publication']}
        atom.save_json(paths['claim'], {'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#18',
            'head': head, 'tree': tree, 'base_head': f.target,
            'order_id': f.selection['order_id'], 'worktree_name': f.wt.name,
            'worktree_path': str(f.wt), 'session_id': 'successor'})
        binding = atom.issue_admission.validate_issue(issue, envelope)
        binding = atom.issue_execution.revision_context(binding, ref(self.entry_path), self.state['envelope_sha256'])
        self.prompt = atom.issue_execution.projection(binding, self.state['envelope_sha256'], 'supervised')
        self.stage = {'status': 'review', 'skill': 'execute', 'provider': 'codex', 'model': 'fixture',
            'prompt': json.dumps(self.prompt), 'attempts': [*entry['prior_attempts'],
                {'status': 'completed', 'session_id': 'successor'}]}
        self.snapshot = {'state': {'orders': {f.selection['order_id']: {
            'status': 'active', 'stages': [self.stage]}},
            'pending_reviews': {f.selection['order_id']: {}}}, 'effect_ledger': []}
        self.snapshot_path = f.root / '.noodle/state.snapshot.json'
        atom.save_json(self.snapshot_path, self.snapshot)
        self.paths = paths

    def test_prior_atom_accepts_complete_scope_selected_revision_projection(self):
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'):
            result = atom.verify_prior_atom(self.authorization)
        self.assertEqual(result['order_id'], self.f.selection['order_id'])
        self.assertEqual(result['prior_envelope_sha256'], self.state['envelope_sha256'])
        self.assertEqual(result['prior_loop_status'], 'stopped')

    def test_prior_atom_reads_current_claim_without_falling_back_to_retained_receipt(self):
        legacy = atom.artifact_paths(self.authorization['prior_atom']['path'])['claim']
        current = self.paths['claim']
        self.assertNotEqual(legacy, current)
        claim = atom.read_json(current, 'claim')
        atom.save_json(legacy, {**claim, 'head': self.f.candidate, 'tree': self.f.tree})
        retained = legacy.read_bytes()
        state = self.paths['state'].read_bytes()
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'):
            result = atom.verify_prior_atom(self.authorization)
            self.assertEqual(result['order_id'], self.f.selection['order_id'])
            self.assertEqual(legacy.read_bytes(), retained)
            current.unlink()
            with self.assertRaisesRegex(atom.AtomRefusal, 'amendment.prior_claim'):
                atom.verify_prior_atom(self.authorization)
        self.assertEqual(legacy.read_bytes(), retained)
        self.assertEqual(self.paths['state'].read_bytes(), state)

    def test_prior_atom_rejects_missing_foreign_or_changed_revision_reference(self):
        foreign = self.f.save('foreign-entry.json', json.loads(self.entry_path.read_text()))
        cases = (('missing', None), ('foreign', ref(foreign)),
                 ('digest', {**ref(self.entry_path), 'sha256': '0' * 64}))
        before = self.paths['state'].read_bytes()
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop') as observe:
            for name, reference in cases:
                prompt = copy.deepcopy(self.prompt)
                if reference is None:
                    del prompt['revision_context']
                else:
                    prompt['revision_context'] = reference
                self.stage['prompt'] = json.dumps(prompt)
                atom.save_json(self.snapshot_path, self.snapshot)
                with self.subTest(case=name), self.assertRaisesRegex(
                        atom.AtomRefusal, 'amendment.prior_revision.reference'):
                    atom.verify_prior_atom(self.authorization)
            self.stage['prompt'] = json.dumps(self.prompt)
            atom.save_json(self.snapshot_path, self.snapshot)
            self.entry_path.write_bytes(self.entry_path.read_bytes() + b' ')
            with self.assertRaisesRegex(atom.AtomRefusal, 'amendment.prior_revision.reference'):
                atom.verify_prior_atom(self.authorization)
            observe.assert_not_called()
        self.assertEqual(self.paths['state'].read_bytes(), before)

    def test_prior_atom_rejects_coherent_entry_tampering_and_prompt_drift(self):
        original = self.entry_path.read_bytes()
        entry = json.loads(original)
        changed_attempts = copy.deepcopy(entry['prior_attempts'])
        changed_attempts[-1]['error'] = 'different revision reason'
        cases = (('selection_sha256', '0' * 64), ('candidate_head', 'a' * 40),
                 ('prior_attempts', changed_attempts))
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop') as observe:
            for key, value in cases:
                changed = {**entry, key: value}
                atom.save_json(self.entry_path, changed)
                prompt = {**self.prompt, 'revision_context': ref(self.entry_path),
                          'admission_revision': changed}
                self.stage['prompt'] = json.dumps(prompt)
                atom.save_json(self.snapshot_path, self.snapshot)
                with self.subTest(field=key), self.assertRaisesRegex(
                        atom.AtomRefusal, 'amendment.prior_revision.selection'):
                    atom.verify_prior_atom(self.authorization)
            self.entry_path.write_bytes(original)
            for key, value in (('task', 'replacement task'), ('admission_revision', None)):
                self.stage['prompt'] = json.dumps({**self.prompt, key: value})
                atom.save_json(self.snapshot_path, self.snapshot)
                with self.subTest(field=key), self.assertRaisesRegex(
                        atom.AtomRefusal, 'amendment.prior_prompt'):
                    atom.verify_prior_atom(self.authorization)
            self.stage['prompt'] = json.dumps(self.prompt)
            self.stage['attempts'] = self.stage['attempts'][-1:]
            atom.save_json(self.snapshot_path, self.snapshot)
            with self.assertRaisesRegex(atom.AtomRefusal, 'amendment.prior_revision.attempts'):
                atom.verify_prior_atom(self.authorization)
            observe.assert_not_called()


class CIPrelandingResumeTests(unittest.TestCase):
    def setUp(self):
        prior = self.prior = TypedRevisionPriorTests()
        prior.setUp()
        self.addCleanup(prior.doCleanups)
        f = self.f = prior.f
        self.source = Path(prior.authorization['prior_atom']['path'])
        self.digest = ref(self.source)['sha256']
        self.state = prior.state
        self.state['schema_version'] = 1
        publication = self.state['publication']
        publication.update(owner='soodles.candidate-publication', status='created',
            repository='ed3c/soodles', subject='ed3c/soodles#18',
            branch='soodles/issue-18-' + publication['head'][:12],
            pr={'number': 19, 'url': 'https://github.com/ed3c/soodles/pull/19'},
            next=None, authorizes_landing=False)
        self.state['writes'] = {'issue_create': {'status': 'offered'},
            'publication_branch_push': {'head': publication['head'], 'status': 'offered'},
            'publication_pr_create': {'head': publication['head'], 'status': 'offered'}}
        runtime = self.runtime = f.root / '.noodle'
        for attempt in prior.stage['attempts']:
            attempt.update(attempt_id=attempt['session_id'] + '-attempt', worktree_name=f.wt.name)
            directory = runtime / 'sessions' / attempt['session_id']
            directory.mkdir(parents=True)
            atom.save_json(directory / 'process.json', {'session_id': attempt['session_id'], 'pid': 424242})
            (directory / 'events.ndjson').write_text(json.dumps({'type': 'stage_message',
                'session_id': attempt['session_id'], 'payload': {'order_id': f.selection['order_id'],
                    'stage_index': 0, 'outcome': 'completed', 'blocking': False}}) + '\n')
        # Preserve the producer's original attempt fields in both retained inputs.
        entry = json.loads(prior.entry_path.read_text())
        entry['prior_attempts'] = copy.deepcopy(prior.stage['attempts'][:-1])
        atom.save_json(prior.entry_path, entry)
        original_attempt = self.state['scope_amendment']['prior']['stage']['attempts'][0]
        original_attempt.update(attempt_id='original-session-attempt', worktree_name=f.wt.name)
        prior.prompt.update(revision_context=ref(prior.entry_path), admission_revision=entry)
        prior.stage['prompt'] = json.dumps(prior.prompt)
        prior.snapshot['state']['pending_reviews'][f.selection['order_id']] = {
            'order_id': f.selection['order_id'], 'stage_index': 0, 'session_id': 'successor',
            'worktree_name': f.wt.name, 'worktree_path': str(f.wt)}
        atom.save_json(prior.snapshot_path, prior.snapshot)
        claim = atom.read_json(prior.paths['claim'], 'claim')
        claim.update(schema_version=1, owner='Noodle', stage_index=0, attempt_id='successor-attempt',
            branch=f.wt.name, base_branch='main', push_remote='origin',
            remote_url='https://github.com/ed3c/soodles.git', authorizes_provider_write=False,
            authorizes_landing=False, evidence={'canonical_snapshot_sha256': ref(prior.snapshot_path)['sha256'],
                'session_events_sha256': ref(runtime / 'sessions/successor/events.ndjson')['sha256']})
        atom.save_json(prior.paths['claim'], claim)
        self.state['publication_source'] = {'claim_sha256': atom.atom_repair.digest(claim),
            'value': publication, 'sha256': atom.atom_repair.digest(publication)}
        bundle = prior.entry_path.parent
        (bundle / 'noodle.toml').write_text('mode = "supervised"\n')
        (f.root / '.noodle.toml').write_bytes((bundle / 'noodle.toml').read_bytes())
        (bundle / 'start-noodle').write_text('fixture selected start\n')
        argv = [prior.authorization['noodle']['path'], '--project-dir', str(f.root), 'start', '--mode', 'manual']
        self.state['noodle_start'] = {'status': 'started', 'pid': 434343, 'process_argv': argv,
            'argv': [str(bundle / 'start-noodle')], 'config_sha256': ref(bundle / 'noodle.toml')['sha256']}
        prepared = {'envelope_sha256': self.state['envelope_sha256'], 'process_argv': argv,
            'start': str(bundle / 'start-noodle'), 'start_sha256': ref(bundle / 'start-noodle')['sha256'],
            'next': {'argv': [str(bundle / 'start-noodle')]}}
        atom.save_json(bundle / 'prepared.json', prepared)
        self.state['admission_sha256'] = ref(bundle / 'prepared.json')['sha256']
        self.state['scope_amendment']['prepared'] = ref(bundle / 'prepared.json')
        self.state['scope_amendment']['ack_prefix'] = '{"id":"retained-history","status":"ok"}\n'
        commands = {name: {'id': 'soodles-scope-' + self.state['scope_amendment']['selection']['sha256'][:24] + '-' + name,
                          'action': action} for name, action in (
            ('scope_request', 'request-changes'), ('scope_edit', 'edit-item'),
            ('scope_requeue', 'requeue'), ('scope_release', 'mode'))}
        self.state.update(commands)
        (runtime / 'control-ack.ndjson').write_text(self.state['scope_amendment']['ack_prefix'] + ''.join(
            json.dumps({**command, 'status': 'ok'}) + '\n' for command in commands.values()))
        atom.save_json(prior.paths['state'], self.state)
        self.spec = f.selection['lifecycle_owner']
        self.descriptor = f.save('runtime-selection.json', self.spec)

    def test_resume_selects_ci_runtime_without_changing_parked_review_or_effects(self):
        p = self.prior
        before = copy.deepcopy(self.state)
        auth_bytes, owner_bytes = self.source.read_bytes(), p.snapshot_path.read_bytes()
        with patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom, 'observe_prior_loop', return_value='running'), \
                patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError), \
                patch.object(atom, 'ensure_noodle') as start, \
                patch.object(atom, 'finish_host') as stop:
            result = atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
            once = p.paths['state'].read_bytes()
            controller = atom.repair_controller(self.f.auth, atom.read_json(p.paths['state'], 'state'),
                p.paths, authorization_path=self.source)
            self.assertEqual(controller.disabled, 'scope_amendment_preserves_original_repair_authority')
            self.assertEqual(p.paths['state'].read_bytes(), once)
            atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
            start.assert_not_called()
            stop.assert_not_called()
        after = atom.read_json(p.paths['state'], 'state')
        self.assertEqual(after.pop('lifecycle_resume'), {'from': None, 'to': self.spec,
                         'authorization_sha256': self.digest})
        self.assertEqual(after, before)
        self.assertEqual(p.paths['state'].read_bytes(), once)
        self.assertEqual(self.source.read_bytes(), auth_bytes)
        self.assertEqual(p.snapshot_path.read_bytes(), owner_bytes)
        self.assertEqual(result['next']['argv'], atom.same_command(self.source))

    def test_resume_accepts_stopped_published_owner_with_same_custody(self):
        with patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'), \
                patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError):
            result = atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
        self.assertEqual(result['status'], 'resumed')
        self.assertEqual(atom.read_json(self.prior.paths['state'], 'state')['noodle_start'],
                         self.state['noodle_start'])

    def test_resume_refuses_unscoped_or_schema_one_ci_without_selection(self):
        original = copy.deepcopy(self.state)
        packet_path = Path(original['scope_amendment']['selection']['path'])
        packet = atom.read_json(packet_path, 'scope.packet')
        packet['selection'] = {'schema': 1, 'added_write_paths': ['test_manager.py'],
            **{key: self.f.selection[key] for key in
               ('reason', 'evidence', 'lifecycle_owner', 'candidate_head')}}
        legacy = self.f.save('schema-one-selection.json', packet)
        auth_bytes = self.source.read_bytes()
        owner_bytes = self.prior.snapshot_path.read_bytes()
        with patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom, 'verify_prior_atom') as prior, \
                patch.object(atom, 'ensure_noodle') as start, patch.object(atom, 'finish_host') as stop:
            for case in ('unscoped', 'schema_one'):
                state = copy.deepcopy(original)
                if case == 'unscoped':
                    del state['scope_amendment']
                else:
                    state['scope_amendment']['selection'] = ref(legacy)
                atom.save_json(self.prior.paths['state'], state)
                before = self.prior.paths['state'].read_bytes()
                with self.subTest(case=case), self.assertRaises(atom.AtomRefusal) as raised:
                    atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                        environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
                self.assertEqual(raised.exception.invalid['field'], 'lifecycle.resume.scope')
                self.assertEqual(self.prior.paths['state'].read_bytes(), before)
                self.assertNotIn('lifecycle_resume', atom.read_json(self.prior.paths['state'], 'state'))
            prior.assert_not_called()
            start.assert_not_called()
            stop.assert_not_called()
        self.assertEqual(self.source.read_bytes(), auth_bytes)
        self.assertEqual(self.prior.snapshot_path.read_bytes(), owner_bytes)

    def test_resume_refuses_changed_custody_and_unknown_effects_without_selection(self):
        p = self.prior
        original_state = copy.deepcopy(self.state)
        original_owner = copy.deepcopy(p.snapshot)
        claim_bytes = p.paths['claim'].read_bytes()
        config = self.f.root / '.noodle.toml'
        config_bytes = config.read_bytes()
        ack_bytes = (self.runtime / 'control-ack.ndjson').read_bytes()
        correction = p.paths['directory'] / 'correction'
        transient = [self.runtime / name for name in ('control.ndjson', 'control-ack.ndjson', 'orders-next.json')]
        cases = {'publication_source': 'lifecycle.resume.publication', 'unknown_write': 'correction.lineage.effects',
            'unknown_push': 'lifecycle.resume.push', 'foreign_review': 'base_recovery.review.identity',
            'live_writer': 'takeover.prior_writer', 'task': 'amendment.prior_prompt',
            'claim': 'amendment.prior_claim', 'config': 'lifecycle.resume.prepared',
            'pending_control': 'lifecycle.resume.mailbox', 'missing_ack': 'lifecycle.resume.controls',
            'foreign_ack': 'lifecycle.resume.controls', 'ack_prefix': 'lifecycle.resume.control_history',
            'proposal': 'lifecycle.resume.mailbox', 'landing': 'correction.lineage.state',
            'correction': 'lifecycle.resume.correction', 'live_session': 'takeover.process_alive'}
        with patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom, 'observe_prior_loop', return_value='running'), \
                patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError) as process, \
                patch.object(atom, 'ensure_noodle') as start, patch.object(atom, 'finish_host') as stop:
            for case in cases:
                state = copy.deepcopy(original_state)
                owner = copy.deepcopy(original_owner)
                stage = owner['state']['orders'][self.f.selection['order_id']]['stages'][0]
                if case == 'publication_source':
                    state['publication_source']['sha256'] = '0' * 64
                elif case == 'unknown_write':
                    state['writes']['unknown'] = {'status': 'offered'}
                elif case == 'unknown_push':
                    state['publication_push_receipts'] = [{'process': 'started'}]
                elif case == 'foreign_review':
                    owner['state']['pending_reviews'][self.f.selection['order_id']]['session_id'] = 'foreign'
                elif case == 'live_writer':
                    stage['attempts'][-1]['status'] = 'running'
                elif case == 'task':
                    prompt = json.loads(stage['prompt'])
                    stage['prompt'] = json.dumps({**prompt, 'task': 'replacement task'})
                elif case == 'claim':
                    claim = json.loads(claim_bytes)
                    atom.save_json(p.paths['claim'], {**claim, 'head': '0' * 40})
                elif case == 'config':
                    config.write_text('changed')
                elif case == 'pending_control':
                    transient[0].write_text('{"id":"foreign","action":"mode"}\n')
                elif case == 'missing_ack':
                    state['scope_release'] = {'id': 'release', 'action': 'mode'}
                elif case == 'foreign_ack':
                    transient[1].write_bytes(ack_bytes + b'{"id":"foreign","action":"mode","status":"ok"}\n')
                elif case == 'ack_prefix':
                    state['scope_amendment']['ack_prefix'] = 'changed prefix\n'
                elif case == 'proposal':
                    transient[2].write_text('{"orders": []}')
                elif case == 'landing':
                    atom.save_json(p.paths['landing'], {})
                elif case == 'correction':
                    correction.mkdir()
                elif case == 'live_session':
                    process.side_effect = None
                atom.save_json(p.snapshot_path, owner)
                atom.save_json(p.paths['state'], state)
                before = p.paths['state'].read_bytes()
                with self.subTest(case=case), self.assertRaises((atom.AtomRefusal, atom.issue_admission.AdmissionRefusal)) as raised:
                    atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                        environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
                self.assertEqual(raised.exception.invalid['field'], cases[case], case)
                self.assertEqual(p.paths['state'].read_bytes(), before, case)
                process.side_effect = ProcessLookupError
                p.paths['claim'].write_bytes(claim_bytes)
                config.write_bytes(config_bytes)
                for path in transient + [p.paths['landing']]:
                    path.unlink(missing_ok=True)
                (self.runtime / 'control-ack.ndjson').write_bytes(ack_bytes)
                if correction.exists():
                    correction.rmdir()
            start.assert_not_called()
            stop.assert_not_called()


class CorrectionPreparationTests(unittest.TestCase):
    def setUp(self):
        fixture = authorization_tests.AuthorizationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        prepared = fixture.run_authorize()
        self.source = Path(prepared['authorization']['path'])
        self.digest = prepared['authorization']['sha256']
        self.auth = json.loads(self.source.read_text())
        self.paths = atom.artifact_paths(self.source)
        self.paths['directory'].mkdir()
        self.output = self.paths['directory'] / 'correction'
        self.publication = {
            'owner': 'soodles.candidate-publication', 'status': 'created',
            'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#131',
            'branch': 'soodles/issue-131-' + 'b' * 12,
            'head': 'b' * 40, 'tree': 'c' * 40,
            'pr': {'number': 41, 'url': 'https://github.com/ed3c/soodles/pull/41'},
            'next': None, 'authorizes_landing': False,
        }
        self.state = {
            'schema_version': 1, 'authorization_sha256': self.digest,
            'phase': 'ci', 'issue': {'number': 131}, 'publication': self.publication,
            'writes': {}, 'noodle_start': {
                'status': 'started', 'config_sha256': '1' * 64,
                'original_config': None, 'restored': True},
        }
        atom.save_json(self.paths['state'], self.state)
        self.issue = {
            'number': 131, 'title': self.auth['issue']['title'],
            'body': self.auth['issue']['body'].rstrip() + '\n\n' + atom.marker(self.digest) + '\n',
            'state': 'open', 'html_url': 'https://github.com/ed3c/soodles/issues/131',
        }
        self.provider = Mock()
        self.provider.issues.side_effect = lambda: [dict(self.issue)]
        self.provider.issue.side_effect = lambda _: dict(self.issue)
        self.provider.repository_info.return_value = {'full_name': 'ed3c/soodles', 'default_branch': 'main'}
        self.provider.base_head.return_value = self.auth['base_head']
        self.provider.pull.return_value = {
            'number': 41, 'state': 'open', 'merged': False,
            'head': {'ref': self.publication['branch'], 'sha': self.publication['head']},
            'base': {'ref': 'main'}, 'body': 'Refs ed3c/soodles#131',
        }
        self.provider.branch.return_value = {'object': {'sha': self.publication['head']}}
        self.run = {'id': 1, 'run_attempt': 1, 'head_sha': self.publication['head'], 'event': 'pull_request',
                    'path': self.auth['workflow']['path'], 'status': 'completed', 'conclusion': 'failure'}
        self.job = {'id': 10, 'run_id': 1, 'run_attempt': 1, 'head_sha': self.publication['head'], 'name': self.auth['workflow']['job'], 'status': 'completed', 'conclusion': 'failure',
                    'steps': [{'name': self.auth['workflow']['step'], 'status': 'completed',
                               'conclusion': 'failure'}]}
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}
        self.provider.job_log.side_effect = lambda job_id: {
            'job_id': job_id, 'raw': b'exact failure: assertion A\n', 'gap': None}
        owner_patch = patch.object(atom, 'verify_prior_atom', return_value={'order_id': 'original'})
        self.owner = owner_patch.start()
        self.addCleanup(owner_patch.stop)

    def prepare(self, *, provider=None, output=None):
        return admission.correction(str(self.source), self.digest, str(output or self.output),
                                    provider=self.provider if provider is None else provider)

    def test_prepares_same_issue_task_judge_carrier_and_fixed_continuation(self):
        original_auth = self.source.read_bytes()
        original_state = self.paths['state'].read_bytes()
        result = self.prepare()
        corrected = json.loads(Path(result['authorization']['path']).read_text())
        self.assertEqual(result['status'], 'prepared')
        self.assertEqual(result['next']['argv'],
                         [str(self.fixture.fixture.root / 'issue-atom'), 'run',
                          str(self.output / 'prepared/authorization.json')])
        self.assertEqual(result['next']['environment'],
                         {'SOODLES_AUTHORIZATION_SHA256': result['authorization']['sha256']})
        for key in ('task', 'base_head', 'control_root', 'carrier', 'noodle', 'landing_owner'):
            self.assertEqual(corrected[key], self.auth[key])
        self.assertEqual(corrected['issue'], {key: self.issue[key] for key in ('number', 'title', 'body')})
        self.assertEqual(atom.issue_admission.parse_contract(corrected['issue']['body']),
                         atom.issue_admission.parse_contract(self.auth['issue']['body']))
        self.assertEqual(corrected['prior_publication'], self.publication)
        self.assertEqual(corrected['prior_atom'], {'path': str(self.source), 'sha256': self.digest})
        self.owner.assert_called_once_with({k: v for k, v in corrected.items() if k != 'failure_context'})
        failure = corrected['failure_context']['data']
        self.assertEqual(failure['run'], self.run)
        self.assertEqual(failure['jobs'], {'jobs': [self.job]})
        log = failure['diagnostics'][0]['log']
        self.assertEqual(Path(log['path']).read_bytes(), b'exact failure: assertion A\n')
        self.assertEqual(log['bytes'], 27)
        self.assertNotIn('text', failure['diagnostics'][0])
        self.assertEqual(self.source.read_bytes(), original_auth)
        self.assertEqual(self.paths['state'].read_bytes(), original_state)
        self.assertFalse(result['authorizes_landing'])
        for operation in ('create_issue', 'update_issue_body', 'merge', 'close_issue'):
            getattr(self.provider, operation).assert_not_called()

    def test_revision_correction_preserves_effective_scope_and_original_lineage(self):
        body = self.issue['body'] + '\nRevision criteria apply to the successor.\n'
        original = self.source.read_bytes()
        with atom_tests.typed_revision_receipts(self.source, self.state,
                self.paths['directory'] / 'revision', body=body) as current:
            atom.save_json(self.paths['state'], self.state)
            atom.save_json(self.paths['claim'], {'head': 'retained'})
            atom.save_json(current['claim'], {'head': self.publication['head']})
            self.issue['body'] = body
            result = self.prepare()
            corrected = atom.read_json(result['authorization']['path'], 'fixture.authorization')
            self.assertEqual(corrected['issue']['body'], body)
            self.assertEqual(corrected['prior_atom'], {'path': str(self.source), 'sha256': self.digest})
            self.assertEqual(corrected['prior_publication'], self.publication)
            self.assertEqual(corrected['landing_owner'], self.auth['landing_owner'])
            self.assertEqual(self.owner.call_args.args[0]['issue']['body'], body)
            self.assertEqual(self.source.read_bytes(), original)
            self.assertEqual(atom.read_json(self.paths['claim'], 'fixture.retained'), {'head': 'retained'})

    def test_prepared_failure_reaches_envelope_and_writer_projection_as_data(self):
        head = self.auth['base_head']
        self.publication['head'] = head
        self.run['head_sha'] = self.job['head_sha'] = head
        self.provider.pull.return_value['head']['sha'] = head
        self.provider.branch.return_value['object']['sha'] = head
        atom.save_json(self.paths['state'], self.state)
        prepared = self.prepare()
        corrected = atom.read_json(prepared['authorization']['path'], 'fixture')
        root = Path(corrected['control_root'])
        name = atom.issue_admission.scoped_order_id(131, root) + '-0-execute'
        subprocess.run(['git', 'worktree', 'add', '-b', name, str(root / '.worktrees' / name), head],
                       cwd=root, check=True, capture_output=True)
        issue = {**self.issue, 'updated_at': '2026-10-02T00:00:00Z',
                 'url': 'https://api.github.com/repos/ed3c/soodles/issues/131'}
        paths = atom.artifact_paths(prepared['authorization']['path'])
        self.owner.return_value = {'prior_loop_status': 'restored'}
        envelope, digest = atom.create_envelope(corrected, issue, issue['body'], paths['envelope'],
                                                environ={'NOODLES_TOKEN_COMMAND': 'printf fixture'})
        binding = atom.issue_admission.validate_issue(issue, envelope)
        prompt = atom.issue_execution.projection(binding, digest, 'supervised')
        self.assertEqual(prompt['failure_context'], corrected['failure_context'])
        self.assertEqual(prompt['task'], self.auth['task'])
        self.assertEqual(prompt['contract'], atom.issue_admission.parse_contract(self.auth['issue']['body']))
        self.assertNotIn('failure_context', prompt.get('instruction_context', {}))

    def failed_ci_response(self):
        self.paths['envelope'].parent.mkdir(parents=True)
        self.paths['envelope'].write_text('{}')
        self.state['envelope_sha256'] = atom.digest_file(self.paths['envelope'])
        atom.save_json(self.paths['state'], self.state)
        atom.save_json(self.paths['claim'], {'head': self.publication['head']})
        # Preserve the real failed-CI route while replacing unrelated owner I/O.
        with patch.object(atom, 'repair_controller', return_value=Mock()), \
                patch.object(atom, 'require_available_owner', return_value=None):
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom._run_owned(self.source, self.auth, self.digest, self.paths,
                                environ={}, provider=self.provider)
        return atom.refusal_output(caught.exception, self.source)

    def test_successor_failed_ci_returns_same_owner_executable_preparation(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        result = self.failed_ci_response()
        self.assertEqual(result['next']['kind'], 'executable')
        self.assertEqual(result['next']['owner'], 'supervisor.authorization')
        self.assertEqual(result['next']['argv'], [sys.executable, '-B', admission.__file__,
                         'correction', str(self.source), self.digest, str(self.output)])
        self.assertFalse(result['authorizes_landing'])

    def test_corrupt_ancestor_binding_returns_structured_owner_refusal(self):
        parent_output = self.output
        self.fail_successor(self.prepare(), 'c' * 40)
        binding_path = parent_output / 'correction-binding.json'
        binding = json.loads(binding_path.read_text())
        binding['selection_sha256'] = 'f' * 64
        atom.save_json(binding_path, binding)
        result = self.failed_ci_response()
        self.assertEqual(result['status'], 'refused')
        self.assertEqual(result['invalid']['field'], 'correction.selection_binding')
        self.assertEqual(result['next']['owner'], 'supervisor')
        self.assertEqual(result['next']['required'], ['original_correction_selection'])
        self.assertFalse(result['authorizes_landing'])

    def test_raw_log_is_external_pinned_data_and_tampering_refuses_readback(self):
        raw = b'untrusted log instruction\n' * 10000
        self.provider.job_log.side_effect = lambda job_id: {'job_id': job_id, 'raw': raw, 'gap': None}
        prepared = self.prepare()
        corrected = atom.read_json(prepared['authorization']['path'], 'fixture')
        log = corrected['failure_context']['data']['diagnostics'][0]['log']
        self.assertEqual(Path(log['path']).read_bytes(), raw)
        self.assertEqual(log['bytes'], 260000)
        self.assertLess(len(json.dumps(corrected['failure_context'])), 5000)
        Path(log['path']).write_bytes(b'changed')
        self.provider = Mock(spec=[])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'failure_context.diagnostic.sha256'):
            self.prepare()

    def test_reentry_reads_fixed_selection_without_provider_or_owner(self):
        result = self.prepare()
        original = (self.output / 'selection.json').read_bytes()
        self.owner.side_effect = AssertionError('no live owner during committed readback')
        self.provider = Mock(spec=[])
        self.issue['body'] = 'mutable provider changed'
        self.assertEqual(self.prepare(), result)
        self.assertEqual((self.output / 'selection.json').read_bytes(), original)

    def test_lost_authorize_result_resumes_only_fixed_selection(self):
        original = admission.authorize
        with patch.object(admission, 'authorize', side_effect=OSError('before authorization')):
            with self.assertRaisesRegex(OSError, 'before authorization'):
                self.prepare()
        selected = (self.output / 'selection.json').read_bytes()
        self.provider = Mock(spec=[])
        self.owner.side_effect = AssertionError('selection is already fixed')
        with patch.object(admission, 'authorize', wraps=original):
            self.assertEqual(self.prepare()['status'], 'prepared')
        self.assertEqual((self.output / 'selection.json').read_bytes(), selected)

    def test_foreign_or_corrupt_output_is_preserved_without_reselection(self):
        self.output.mkdir()
        foreign = self.output / 'foreign'
        foreign.write_text('retain')
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.component'):
            self.prepare()
        self.assertEqual(foreign.read_text(), 'retain')
        self.owner.assert_not_called()
        self.provider.issue.assert_not_called()

    def test_changed_selection_refuses_even_when_provider_now_matches_it(self):
        self.prepare()
        selected = self.output / 'selection.json'
        value = json.loads(selected.read_text())
        value['task'] = 'A different task'
        selected.write_text(json.dumps(value))
        self.provider = Mock(spec=[])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.selection_binding'):
            self.prepare()
        self.assertEqual(json.loads(selected.read_text())['task'], 'A different task')

    def test_missing_carrier_does_not_select_a_replacement(self):
        Path(self.auth['noodle']['path']).unlink()
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.noodle') as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['required'], ['exact_noodle_binary'])
        self.assertFalse(self.output.exists())
        self.provider.issue.assert_not_called()

    def test_different_output_cannot_create_another_budget(self):
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.output'):
            self.prepare(output=self.output.with_name('another-correction'))
        self.assertFalse(self.output.exists())
        self.owner.assert_not_called()

    def fail_successor(self, prepared, head):
        self.source = Path(prepared['authorization']['path'])
        self.digest = prepared['authorization']['sha256']
        self.auth = json.loads(self.source.read_text())
        self.paths = atom.artifact_paths(self.source)
        self.paths['directory'].mkdir()
        self.output = self.paths['directory'] / 'correction'
        self.publication = {**self.publication, 'status': 'amended', 'head': head}
        self.state = {**copy.deepcopy(self.state), 'authorization_sha256': self.digest,
                      'publication': self.publication}
        atom.save_json(self.paths['state'], self.state)
        self.provider.pull.return_value['head']['sha'] = head
        self.provider.branch.return_value['object']['sha'] = head
        self.run.update(id=self.run['id'] + 1, head_sha=head)
        self.job.update(id=self.job['id'] + 1, run_id=self.run['id'], head_sha=head)
        self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}
        self.provider.jobs.return_value = {'jobs': [self.job]}

    def test_three_distinct_corrections_keep_original_owner_then_require_reassessment(self):
        original = copy.deepcopy(self.auth)
        ledgers = []
        for head in ('c' * 40, 'd' * 40, 'e' * 40):
            self.state['repair'] = {'history': [{'status': 'confirmed', 'signal': 'stale_pr'}],
                                    'models': 1, 'started_at': 'original'}
            atom.save_json(self.paths['state'], self.state)
            ledgers.append((self.paths['state'], self.paths['state'].read_bytes()))
            prepared = self.prepare()
            self.assertEqual(self.prepare(), prepared)
            self.fail_successor(prepared, head)
            for key in ('task', 'base_head', 'control_root', 'carrier', 'noodle', 'landing_owner'):
                self.assertEqual(self.auth[key], original[key])
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.limit') as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['required'], ['reassess_cause_after_three_failed_corrections'])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.provider.job_log.call_count, 3)
        for path, raw in ledgers:
            self.assertEqual(path.read_bytes(), raw)

    def test_pending_third_correction_is_not_a_third_confirmed_failure(self):
        for head in ('c' * 40, 'd' * 40, 'e' * 40):
            self.fail_successor(self.prepare(), head)
        self.run['status'] = 'in_progress'
        self.run['conclusion'] = None
        for _ in range(2):
            with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior_runtime') as caught:
                self.prepare()
            self.assertNotIn('reassess_cause_after_three_failed_corrections', caught.exception.next['required'])
            self.assertFalse(self.output.exists())
        self.assertEqual(self.provider.job_log.call_count, 3)

    def test_repeated_failed_head_cannot_prepare_successor(self):
        self.fail_successor(self.prepare(), 'b' * 40)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.head'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_unknown_ancestor_effect_blocks_successor_without_provider_reads(self):
        ancestor_paths = self.paths
        self.fail_successor(self.prepare(), 'c' * 40)
        ancestor = atom.read_json(ancestor_paths['state'], 'fixture')
        ancestor['writes']['merge'] = {'status': 'offered'}
        atom.save_json(ancestor_paths['state'], ancestor)
        self.provider.reset_mock()
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.effects'):
            self.prepare()
        self.provider.issue.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_changed_task_judge_scope_and_parent_publication_refuse(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        original = copy.deepcopy(self.auth)
        for field in ('task', 'landing_owner', 'contract', 'prior_publication', 'failure_context'):
            with self.subTest(field=field):
                value = copy.deepcopy(original)
                if field == 'task':
                    value['task'] += ' changed scope'
                elif field == 'landing_owner':
                    value[field]['verifier_sha256'] = 'f' * 64
                elif field == 'contract':
                    contract = atom.issue_admission.parse_contract(value['issue']['body'])
                    changed = copy.deepcopy(contract)
                    changed['behavior'].append('unadmitted behavior')
                    value['issue']['body'] = value['issue']['body'].replace(
                        json.dumps(contract), json.dumps(changed))
                    self.assertNotEqual(value['issue']['body'], original['issue']['body'])
                elif field == 'prior_publication':
                    value[field]['pr']['number'] = 99
                else:
                    value[field]['data']['run']['head_sha'] = 'f' * 40
                    value[field]['sha256'] = atom.issue_admission.failure_digest(value[field]['data'])
                atom.save_json(self.source, value)
                digest = atom.digest_file(self.source)
                state = {**self.state, 'authorization_sha256': digest}
                with self.assertRaises((atom.AtomRefusal, admission.AdmissionRefusal)):
                    atom.validate_correction_lineage(value, {'path': str(self.source), 'sha256': digest}, state)
        atom.save_json(self.source, original)

    def test_legacy_external_predecessor_does_not_reset_history(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        del self.auth['failure_context']
        atom.save_json(self.source, self.auth)
        self.digest = atom.digest_file(self.source)
        self.state['authorization_sha256'] = self.digest
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.lineage.external'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_cyclic_or_broken_parent_reference_refuses(self):
        self.fail_successor(self.prepare(), 'c' * 40)
        self.auth['prior_atom'] = {'path': str(self.source), 'sha256': self.digest}
        atom.save_json(self.source, self.auth)
        self.digest = atom.digest_file(self.source)
        self.state['authorization_sha256'] = self.digest
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior_atom.sha256'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_missing_log_is_explicit_data_and_does_not_change_task(self):
        self.provider.job_log.return_value = None
        self.provider.job_log.side_effect = lambda job_id: {
            'job_id': job_id, 'raw': None, 'gap': 'log_http_status_404'}
        prepared = self.prepare()
        authorization = atom.read_json(prepared['authorization']['path'], 'fixture')
        self.assertEqual(authorization['task'], self.auth['task'])
        self.assertEqual(authorization['failure_context']['data']['diagnostics'][0]['gap'], 'log_http_status_404')
        self.assertEqual(self.prepare(), prepared)
        self.provider.job_log.assert_called_once_with(10)

    def test_wrong_run_job_or_diagnostic_identity_is_not_admitted(self):
        original_run, original_job = copy.deepcopy(self.run), copy.deepcopy(self.job)
        for field in ('run_attempt', 'job_run', 'job_attempt', 'job_head', 'log_job'):
            with self.subTest(field=field):
                if field == 'run_attempt':
                    self.run['run_attempt'] = 0
                elif field == 'job_run':
                    self.job['run_id'] = 999
                elif field == 'job_attempt':
                    self.job['run_attempt'] = 2
                elif field == 'job_head':
                    self.job['head_sha'] = 'f' * 40
                else:
                    self.provider.job_log.side_effect = lambda job_id: {
                        'job_id': 999, 'raw': b'changed', 'gap': None}
                with self.assertRaises(admission.AdmissionRefusal):
                    self.prepare()
                self.assertFalse(self.output.exists())
                self.run.clear()
                self.run.update(original_run)
                self.job.clear()
                self.job.update(original_job)

    def test_unresolved_original_effect_refuses_without_new_preparation(self):
        self.state['repair'] = {'history': [{'signal': 'stale_pr', 'status': 'intent'}]}
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'correction.repair_history'):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.provider.issue.assert_not_called()

    def test_unknown_original_owner_is_not_replaced(self):
        self.owner.side_effect = atom.AtomRefusal('amendment.prior_loop.group', 'present',
                                                'quiescent_noodle_owner', owner='Noodle')
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.prepare()
        self.assertEqual(caught.exception.next['owner'], 'Noodle')
        self.assertEqual(caught.exception.next['required'], ['quiescent_noodle_owner'])
        self.provider.issue.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_provider_base_drift_and_nonfailed_ci_leave_no_selection(self):
        for kind in ('base', 'head', 'running', 'success', 'cancelled', 'missing'):
            with self.subTest(kind=kind):
                base, pull = self.provider.base_head.return_value, copy.deepcopy(self.provider.pull.return_value)
                run, job = copy.deepcopy(self.run), copy.deepcopy(self.job)
                if kind == 'base':
                    self.provider.base_head.return_value = 'f' * 40
                elif kind == 'head':
                    self.provider.pull.return_value['head']['sha'] = 'f' * 40
                elif kind == 'running':
                    self.run['status'] = 'in_progress'
                elif kind == 'missing':
                    self.provider.workflow_runs.return_value = {'workflow_runs': []}
                else:
                    self.run['conclusion'] = self.job['conclusion'] = self.job['steps'][0]['conclusion'] = kind
                with self.assertRaises(admission.AdmissionRefusal):
                    self.prepare()
                self.assertFalse(self.output.exists())
                self.provider.base_head.return_value = base
                self.provider.pull.return_value = pull
                self.run.clear()
                self.run.update(run)
                self.job.clear()
                self.job.update(job)
                self.provider.workflow_runs.return_value = {'workflow_runs': [self.run]}

    def test_skipped_acceptance_after_exact_runtime_failure_is_supported(self):
        self.job['steps'][0]['conclusion'] = 'skipped'
        self.job['steps'].insert(0, {'name': 'Prepare runtime', 'status': 'completed', 'conclusion': 'failure'})
        self.assertEqual(self.prepare()['status'], 'prepared')

    def test_host_credential_supplier_requests_only_read_capabilities(self):
        with patch.object(atom.provider_credential, 'resolve_host_environment', return_value={'selected': 'host'}) as host, \
                patch.object(atom.provider_credential, 'supply_token', return_value='fixture-token') as token, \
                patch.object(atom, 'GitHubProvider', return_value=self.provider):
            result = admission.correction(str(self.source), self.digest, str(self.output), environ={})
        self.assertEqual(result['status'], 'prepared')
        host.assert_called_once_with(Path(self.auth['control_root']), environ={})
        token.assert_called_once_with(self.auth['repository'],
            {'contents': 'read', 'issues': 'read', 'pull_requests': 'read', 'actions': 'read'},
            environ={'selected': 'host'})


class DiagnosticTransportTests(unittest.TestCase):
    def response(self, url, code, raw=b'', headers=None):
        value = io.BytesIO(raw)
        value.url, value.code, value.headers = url, code, headers or {}
        return value

    def test_signed_redirect_receives_no_token_and_preserves_exact_log(self):
        provider = atom.GitHubProvider('ed3c/soodles', token='fixture-secret')
        url = provider.api + '/actions/jobs/10/logs'
        redirect = 'https://logs.example.invalid/signed?signature=opaque'
        opener = Mock()
        opener.open.side_effect = [self.response(url, 302, headers={'Location': redirect}),
                                  self.response(redirect, 200, b'raw failure\n')]
        with patch.object(atom.urllib.request, 'build_opener', return_value=opener) as build:
            result = provider.job_log(10)
        self.assertIsInstance(build.call_args.args[0], atom.candidate_publication.NoRedirect)
        requests = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(requests[0].get_header('Authorization'), 'Bearer fixture-secret')
        self.assertIsNone(requests[1].get_header('Authorization'))
        self.assertEqual(requests[1].full_url, redirect)
        self.assertEqual(result, {'job_id': 10, 'raw': b'raw failure\n', 'gap': None})

    def test_missing_or_unsafe_logs_are_explicit_gaps_without_redirect_effect(self):
        provider = atom.GitHubProvider('ed3c/soodles', token='fixture-secret')
        url = provider.api + '/actions/jobs/10/logs'
        for code, location, expected in ((404, None, 'log_http_status_404'),
                                        (302, 'http://unsafe.invalid', 'invalid_log_redirect')):
            with self.subTest(code=code):
                opener = Mock()
                opener.open.return_value = self.response(url, code, headers={'Location': location})
                with patch.object(atom.urllib.request, 'build_opener', return_value=opener):
                    result = provider.job_log(10)
                self.assertEqual(result['gap'], expected)
                self.assertIsNone(result['raw'])
                opener.open.assert_called_once()


if __name__ == '__main__':
    unittest.main()
