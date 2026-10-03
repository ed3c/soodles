"""Correction selection keeps the original authority and one fixed continuation."""
import copy
import hashlib
import os
import signal
import time
import json
import io
import subprocess
import sys
import urllib.error
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import issue_atom as atom
import issue_admission as native_admission
import issue_execution as native_execution
import supervisor_admission as native_supervisor
import test_issue_atom as atom_tests
import supervisor_admission as admission
import test_supervisor_authorization as authorization_tests
from test_admission_revision import RevisionFixture, ref


class CorrectionWorkerReaderTests(unittest.TestCase):
    def test_explicit_generic_entry_keeps_bound_reader_and_ignores_old_prompt(self):
        execution = atom.issue_execution
        envelope = {'repository': 'fixture/target', 'issue': 18,
                    'target_binding': {'fixture': 'fixed'}, 'execution': {}}
        entry = {'path': '/fixture/entry.json', 'sha256': 'e' * 64}
        with patch.object(execution, 'load_external_envelope', return_value=envelope), \
                patch.object(execution, 'fetch_issue', return_value={'number': 18}) as reader, \
                patch.object(execution, 'validate_issue', return_value=envelope), \
                patch.object(execution, 'revision_context', return_value=envelope) as revision, \
                patch.object(execution, 'context') as old_context:
            with self.assertRaisesRegex(atom.issue_admission.AdmissionRefusal, 'worker.session_id'):
                execution.worker('/fixture/envelope.json', 'd' * 64, '/fixture', [],
                    reader=reader, environ={}, entry_reference=entry)
        reader.assert_called_once_with('fixture/target', 18, binding=envelope)
        revision.assert_called_once_with(envelope, entry, 'd' * 64)
        old_context.assert_not_called()


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

    def test_tri_base_prior_keeps_old_claim_and_rejects_scope_change(self):
        f = self.f
        f.git('commit', '--allow-empty', '-m', 'New provider target')
        target = f.git('rev-parse', 'HEAD')
        f.git('reset', '--hard', f.base)
        child = {**self.authorization, 'base_head': target,
            'issue': {**self.authorization['issue'], 'body': atom.correction_base_body(
                self.authorization, self.authorization['issue']['body'], target,
                self.authorization['prior_publication']['head'])}}
        self.assertEqual(len({f.base, f.target, target}), 3)
        before = self.paths['state'].read_bytes()
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'):
            result = atom.verify_prior_atom(child)
            self.assertEqual(result['prior_envelope_sha256'], self.state['envelope_sha256'])
            with self.assertRaisesRegex(atom.AtomRefusal, 'amendment.prior_scope'):
                atom.verify_prior_atom({**child, 'issue': {**child['issue'], 'body': child['issue']['body'] + 'Other task'}})
        self.assertEqual(self.paths['state'].read_bytes(), before)
        self.assertEqual(f.git('rev-parse', 'HEAD'), f.base)

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

    def postwrite_fixture(self):
        p = self.prior
        self.state['phase'] = 'landing'
        effective, selected_paths = atom.scope_projection(self.f.auth, self.state, p.paths)
        claim = atom.read_json(p.paths['claim'], 'claim')
        publication = self.state['publication']
        atom.save_json(p.paths['landing'], {'phase': 'awaiting_reconcile',
            'writes_offered': ['merge', 'close'], 'merge_sha': claim['head'], 'issue_closed_at': 'fixture',
            'claim': {**{key: claim[key] for key in ('repository', 'head', 'tree', 'base_head')},
                'issue': 18, 'pr': publication['pr']['number'], 'publication_branch': publication['branch'],
                'worktree': claim['worktree_name'], 'control_root': str(self.f.root),
                'execution_envelope': {'path': str(selected_paths['envelope']),
                                       'sha256': self.state['envelope_sha256']}}})
        p.snapshot['state']['mode'] = 'supervised'
        p.snapshot['state']['orders']['schedule'] = {'order_id': 'schedule', 'status': 'active',
            'stages': [{'stage_index': 0, 'task_key': 'schedule', 'skill': 'schedule',
                'provider': 'codex', 'model': 'fixture', 'runtime': 'process', 'prompt': '',
                'status': 'pending', 'attempts': []}]}
        atom.save_json(p.snapshot_path, p.snapshot)
        atom.save_json(p.paths['state'], self.state)
        return effective, selected_paths

    def test_postwrite_resume_accepts_exact_parked_supervised_owner_without_effects(self):
        import fcntl
        self.postwrite_fixture()
        before = copy.deepcopy(self.state)
        original = atom.subprocess.run
        def read_process(command, *args, **kwargs):
            if command[0] == 'ps':
                return subprocess.CompletedProcess(command, 0,
                    ' '.join(self.state['noodle_start']['process_argv']) + '\n', '')
            return original(command, *args, **kwargs)
        with (self.runtime / 'noodle.lock').open('a+b') as native, \
                patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom.subprocess, 'run', side_effect=read_process), \
                patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError), \
                patch.object(atom, 'ensure_noodle') as start, patch.object(atom, 'finish_host') as stop:
            fcntl.flock(native, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
            start.assert_not_called()
            stop.assert_not_called()
        saved = atom.read_json(self.prior.paths['state'], 'state')
        self.assertEqual(saved.pop('lifecycle_resume'), {'from': None, 'to': self.spec,
            'authorization_sha256': self.digest})
        self.assertEqual(saved, before)
        self.assertEqual(result['status'], 'resumed')
        self.assertEqual(result['next']['argv'], atom.same_command(self.source))

    def test_postwrite_resume_rejects_foreign_process_before_selecting_source(self):
        import fcntl
        self.postwrite_fixture()
        original = atom.subprocess.run
        def read_process(command, *args, **kwargs):
            if command[0] == 'ps':
                return subprocess.CompletedProcess(command, 0, 'foreign-process\n', '')
            return original(command, *args, **kwargs)
        before = self.prior.paths['state'].read_bytes()
        with (self.runtime / 'noodle.lock').open('a+b') as native, \
                patch.object(atom, 'validate_authorization', return_value=(self.f.auth, self.digest)), \
                patch.object(atom.subprocess, 'run', side_effect=read_process), \
                patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError):
            fcntl.flock(native, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(atom.AtomRefusal, 'amendment.prior_loop.identity'):
                atom.resume(self.source, self.descriptor, ref(self.descriptor)['sha256'],
                    environ={'SOODLES_AUTHORIZATION_SHA256': self.digest})
        self.assertEqual(self.prior.paths['state'].read_bytes(), before)

    def test_postwrite_custody_rejects_active_writer_config_and_foreign_control(self):
        self.postwrite_fixture()
        p = self.prior
        with patch.object(atom.issue_execution.os, 'kill', side_effect=ProcessLookupError):
            p.stage['attempts'][-1]['status'] = 'running'
            atom.save_json(p.snapshot_path, p.snapshot)
            with self.assertRaisesRegex(atom.AtomRefusal, 'noodle.order.attempt'):
                atom.postwrite_parked_custody(self.f.auth, p.paths, self.state)
            p.stage['attempts'][-1]['status'] = 'completed'
            atom.save_json(p.snapshot_path, p.snapshot)
            config = self.f.root / '.noodle.toml'
            raw = config.read_bytes()
            config.write_text('foreign = true\n')
            with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle.resume.prepared'):
                atom.postwrite_parked_custody(self.f.auth, p.paths, self.state)
            config.write_bytes(raw)
            with (self.runtime / 'control-ack.ndjson').open('a') as stream:
                stream.write('{"id":"foreign","action":"mode","status":"ok"}\n')
            with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle.resume.controls'):
                atom.postwrite_parked_custody(self.f.auth, p.paths, self.state)

    def test_prior_host_restored_readback_completes_missing_or_offered_child_receipt(self):
        p = self.prior
        child = {**p.authorization, 'host_config_sha256': None}
        child_paths = atom.artifact_paths(self.f.directory / 'child.json')
        (self.f.root / '.noodle.toml').unlink()
        original = p.paths['state'].read_bytes()
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom.issue_execution, '_absent_process'), \
                patch.object(atom, 'observe_prior_loop', return_value='restored'), \
                patch.object(atom, 'finish_host') as finish:
            intent = {'prior_authorization_sha256': child['prior_atom']['sha256'],
                      'order_id': self.f.selection['order_id'], 'status': 'offered'}
            for checkpoint in ({}, {'prior_host_recovery': intent}):
                self.assertTrue(atom.recover_prior_host(child, child_paths, checkpoint))
                self.assertEqual(checkpoint['prior_host_recovery'], {**intent, 'status': 'restored'})
            finish.assert_not_called()
        self.assertEqual(p.paths['state'].read_bytes(), original)

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

    def test_created_issue_number_preserves_original_authorization_marker(self):
        original = copy.deepcopy(self.f.auth)
        original['issue'].pop('number', None)
        observed = {}
        def prior(candidate):
            observed.update(candidate)
            raise atom.AtomRefusal('fixture.prior', 'captured')
        before = self.source.read_bytes()
        with patch.object(atom, 'scope_packet', return_value={'selection': {'schema': 2}}), \
                patch.object(atom, 'validate_correction_lineage'), \
                patch.object(atom, 'scope_projection', return_value=(original, self.prior.paths)), \
                patch.object(atom, 'verify_prior_atom', side_effect=prior):
            with self.assertRaisesRegex(atom.AtomRefusal, 'fixture.prior'):
                atom.prelanding_lifecycle(self.source, original, self.state, self.prior.paths)
        self.assertEqual(observed['issue']['number'], self.state['issue']['number'])
        self.assertEqual(observed['issue']['body'], atom.authorized_issue_body(original, self.digest))
        self.assertIn(atom.marker(self.digest), observed['issue']['body'])
        self.assertNotIn('number', original['issue'])
        self.assertEqual(self.source.read_bytes(), before)

    def test_typed_correction_ack_prefix_and_complete_tail_are_required(self):
        _, selected_paths = atom.scope_projection(self.f.auth, self.state, self.prior.paths)
        authorization = {**self.f.auth, 'prior_atom': {'path': str(self.source), 'sha256': self.digest}}
        state = {'correction_ack_prefix': '{"id":"parent","status":"ok"}\n'}
        commands = {name: {'id': name, 'action': action} for name, action in (
            ('correction_review', 'request-changes'), ('correction_edit', 'edit-item'),
            ('correction_requeue', 'requeue'), ('correction_release', 'mode'))}
        state.update(commands)
        path = self.runtime / 'control-ack.ndjson'
        tail = ''.join(json.dumps({**command, 'status': 'ok'}) + '\n' for command in commands.values())
        for raw, field in ((tail, 'lifecycle.resume.control_history'),
                (state['correction_ack_prefix'] + tail + '{"id":"foreign","status":"ok"}\n',
                 'lifecycle.resume.controls')):
            path.write_text(raw)
            with self.assertRaisesRegex(atom.AtomRefusal, field):
                atom.completed_control_readback(authorization, state, selected_paths)
        raw = state['correction_ack_prefix'] + tail
        path.write_text(raw)
        atom.completed_control_readback(authorization, state, selected_paths)
        self.assertEqual(path.read_text(), raw)

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
        self.prior_validator = atom.verify_prior_atom
        owner_patch = patch.object(atom, 'verify_prior_atom', return_value={'order_id': 'original'})
        self.owner = owner_patch.start()
        self.addCleanup(owner_patch.stop)

    def prepare(self, *, provider=None, output=None):
        return admission.correction(str(self.source), self.digest, str(output or self.output),
                                    provider=self.provider if provider is None else provider)

    def test_descendant_correction_requires_parent_selected_native_capability(self):
        root = self.fixture.fixture.root
        source_head = self.auth['base_head']
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'provider base advance'],
                       cwd=root, check=True, capture_output=True)
        target = atom._git(root, 'rev-parse', 'HEAD')
        subprocess.run(['git', 'reset', '--hard', source_head], cwd=root,
                       check=True, capture_output=True)
        self.publication['head'] = source_head
        self.publication['tree'] = atom._git(root, 'rev-parse', source_head + '^{tree}')
        self.provider.pull.return_value['head']['sha'] = source_head
        self.provider.branch.return_value['object']['sha'] = source_head
        self.run['head_sha'] = self.job['head_sha'] = source_head
        self.provider.base_head.return_value = target
        atom.save_json(self.paths['state'], self.state)
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            self.prepare()
        self.assertEqual(caught.exception.invalid['field'], 'correction.base.native')
        self.assertFalse(self.output.exists())
        self.assertEqual(atom._git(root, 'rev-parse', 'HEAD'), source_head)
        self.provider.update_issue_body.assert_not_called()

    def test_typed_release_rechecks_fixed_base_before_offer_then_reads_ack(self):
        authorization = {**self.auth, 'issue': {key: self.issue[key] for key in ('number', 'title', 'body')},
                         'prior_publication': self.publication}
        order_id = 'fixture-order'
        attempts = [{'status': 'failed', 'session_id': 'prior', 'attempt_id': 'prior-attempt'}]
        binding = {'repository': self.auth['repository'], 'issue': 131, 'body_sha256': 'a' * 64,
            'body_updated_at': None, 'contract': atom.issue_admission.parse_contract(self.issue['body']),
            'issue_body': self.issue['body'], 'execution': {'task': self.auth['task']},
            'revision_entry': {'reference': ref(self.source), 'context': {'prior_attempts': attempts}}}
        prompt = json.dumps(atom.issue_execution.projection(binding, 'b' * 64, 'supervised'), sort_keys=True)
        prefix = 'soodles-correction-' + self.digest[:24]
        commands = {'correction_edit': {'id': prefix + '-edit', 'action': 'edit-item', 'order_id': order_id, 'prompt': prompt},
                    'correction_requeue': {'id': prefix + '-requeue', 'action': 'requeue', 'order_id': order_id}}
        checkpoint = {'authorization_sha256': self.digest, 'envelope_sha256': 'b' * 64, **commands}
        stage = {'status': 'pending', 'prompt': prompt, 'attempts': attempts}
        owner = {'state': {'orders': {order_id: {'stages': [stage]}}, 'pending_reviews': {}, 'mode': 'manual', 'mode_epoch': 1}}
        prior = {'order_id': order_id, 'worktree_path': str(self.fixture.fixture.root), 'stage': stage}
        runtime = self.fixture.fixture.root / '.noodle'
        runtime.mkdir(exist_ok=True)
        acks = runtime / 'control-ack.ndjson'
        acks.write_text(''.join(json.dumps({**command, 'status': 'ok'}) + '\n' for command in commands.values()))
        self.provider.base_head.return_value = 'f' * 40
        with patch.object(atom.issue_execution, 'validate_revision_custody'):
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.advance_typed_correction(authorization, self.paths, checkpoint, binding, owner, prior, self.provider)
            self.assertEqual(caught.exception.invalid['field'], 'amendment.prior_base')
            self.assertEqual(caught.exception.invalid['value']['observed_base'], 'f' * 40)
            self.assertNotIn('correction_release', checkpoint)
            self.assertFalse((runtime / 'control.ndjson').exists())
            self.provider.base_head.return_value = self.auth['base_head']
            result = atom.advance_typed_correction(authorization, self.paths, checkpoint, binding, owner, prior, self.provider)
            self.assertEqual(result['action'], 'correction_release_pending')
            with acks.open('a') as stream:
                stream.write(json.dumps({**checkpoint['correction_release'], 'status': 'ok'}) + '\n')
            (runtime / 'control.ndjson').write_text('')
            owner['state'].update(mode='supervised', mode_epoch=2)
            self.provider.base_head.reset_mock()
            self.provider.base_head.return_value = 'e' * 40
            self.assertEqual(atom.advance_typed_correction(authorization, self.paths, checkpoint, binding, owner, prior, self.provider)['action'], 'correction_released')
            self.provider.base_head.assert_not_called()

    def test_tri_base_preparation_readmission_and_sealed_entry_preserve_old_generation(self):
        root = self.fixture.fixture.root
        outer = self.fixture.fixture.outer
        source_head = self.auth['base_head']
        self.issue.update(url='https://api.github.com/repos/ed3c/soodles/issues/131',
                          updated_at='2026-10-04T00:00:00Z')
        env = {admission.TOKEN_COMMAND_ENV: 'fixture-unused-credential'}
        original_bundle = outer / 'original-bundle'
        admission.prepare(self.issue, {**self.auth['carrier'], 'noodle': self.auth['noodle']},
                          root, original_bundle, task=self.auth['task'], environ=env)
        original = atom.read_json(original_bundle / 'envelope.json', 'original')
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'Prior scope base'], cwd=root, check=True, capture_output=True)
        prior_base = atom._git(root, 'rev-parse', 'HEAD')
        worktree = root / '.worktrees' / original['execution']['worktree']
        subprocess.run(['git', 'worktree', 'add', '-b', worktree.name, str(worktree), prior_base], cwd=root, check=True, capture_output=True)
        (worktree / 'allowed.py').write_text('retained candidate\n')
        subprocess.run(['git', 'add', '.'], cwd=worktree, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Published candidate'], cwd=worktree, check=True, capture_output=True)
        head = atom._git(worktree, 'rev-parse', 'HEAD')
        self.publication.update(head=head, tree=atom._git(worktree, 'rev-parse', 'HEAD^{tree}'))
        runtime_root = Path(atom.__file__).parent
        hashes = {name: atom.digest_file(runtime_root / name) for name in atom.LIFECYCLE_FILES}
        runtime = {'path': str(runtime_root / 'issue-atom'), 'sha256': hashes['issue-atom'],
                   'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode())}
        accepted = outer / 'accepted.json'
        atom.save_json(accepted, {'schema': 1, 'issue': 106, 'accepted_at': 'fixture',
            'binary': self.auth['noodle'], 'acceptance': ref(self.source), 'interface': ref(self.source)})
        readback = outer / 'scope-provider.json'
        atom.save_json(readback, {'repository': {'full_name': self.auth['repository'], 'default_branch': 'main'},
            'branch': {'name': 'main', 'commit': {'sha': prior_base}}})
        selection = {'schema': 2, 'type': 'base_advance', 'reason': 'Prior admitted base.',
            'evidence': ref(self.source), 'lifecycle_owner': runtime, 'candidate_head': head,
            'candidate_tree': self.publication['tree'], 'original_envelope': ref(original_bundle / 'envelope.json'),
            'order_id': original['execution']['order_id'], 'stage_index': 0, 'terminal_session': 'older-session',
            'before_contract': atom.issue_admission.parse_contract(self.auth['issue']['body']),
            'target_base': prior_base, 'references': [], 'provider_readback': ref(readback), 'native_acceptance': ref(accepted)}
        scope_output = outer / 'scope'
        scope_output.mkdir()
        packet = scope_output / 'scope-selection.json'
        atom.save_json(packet, {'schema': 1, 'authorization': ref(self.source), 'selection': selection, 'output': str(scope_output)})
        selection = atom.read_json(packet, 'selected scope')['selection']
        self.issue['body'] = atom.revision_body({**self.auth, 'issue': self.issue}, selection)
        prior_envelope = {**original, 'body_sha256': atom.digest_bytes(self.issue['body'].encode()), 'base_head': prior_base}
        prior_envelope_path = scope_output / 'admission/envelope.json'
        prior_envelope_path.parent.mkdir()
        atom.save_json(prior_envelope_path, prior_envelope)
        atom.save_json(prior_envelope_path.parent / 'prepared.json', {'envelope_sha256': atom.digest_file(prior_envelope_path)})
        self.state.update(lifecycle_resume={'from': None, 'to': runtime, 'authorization_sha256': self.digest},
            envelope_sha256=atom.digest_file(prior_envelope_path), scope_amendment={
            'selection': ref(packet), 'prepared': ref(prior_envelope_path.parent / 'prepared.json'), 'status': 'released'})
        atom.save_json(self.paths['state'], self.state)
        self.provider.pull.return_value['head']['sha'] = head
        self.provider.branch.return_value['object']['sha'] = head
        self.run['head_sha'] = self.job['head_sha'] = head
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'New provider base'], cwd=root, check=True, capture_output=True)
        target = atom._git(root, 'rev-parse', 'HEAD')
        subprocess.run(['git', 'reset', '--hard', source_head], cwd=root, check=True, capture_output=True)
        self.provider.base_head.return_value = target
        prepared = self.prepare()
        child_path = Path(prepared['authorization']['path'])
        child = atom.read_json(child_path, 'child')
        self.assertEqual(len({source_head, prior_base, target}), 3)
        self.assertEqual(child['base_head'], target)
        self.assertEqual(child['lifecycle_owner'], runtime)
        child_paths = atom.artifact_paths(child_path)
        child_paths['directory'].mkdir()
        child_state = {'phase': 'issue', 'writes': {}, 'issue': None, 'publication': None,
            'prior_host_recovery': {'status': 'restored'}}
        self.provider.update_issue_body.side_effect = atom.MutationUnknown('lost Issue PATCH response')
        for _ in range(2):
            with self.assertRaises(atom.AtomRefusal) as caught:
                atom.readmit_issue_base(self.provider, child, child_state, child_paths)
            self.assertEqual(caught.exception.invalid['field'], 'readmission.issue.outcome')
        self.issue['body'] = child['issue']['body']
        atom.readmit_issue_base(self.provider, child, child_state, child_paths)
        self.provider.update_issue_body.assert_called_once()
        self.assertEqual(child_state['writes']['issue_base'], atom.correction_base_intent(child))
        order_id = original['execution']['order_id']
        attempt = {'status': 'completed', 'session_id': 'published-session', 'attempt_id': 'attempt-published', 'worktree_name': worktree.name}
        stage = {'status': 'review', 'attempts': [attempt]}
        review = {'order_id': order_id, 'stage_index': 0, 'session_id': 'published-session',
                  'worktree_name': worktree.name, 'worktree_path': str(worktree)}
        events = root / '.noodle/sessions/published-session/events.ndjson'
        events.parent.mkdir(parents=True)
        events.write_text(json.dumps({'type': 'stage_message', 'session_id': 'published-session',
            'payload': {'order_id': order_id, 'stage_index': 0, 'outcome': 'completed', 'blocking': False}}) + '\n')
        atom.save_json(root / '.noodle/state.snapshot.json', {'state': {'orders': {order_id: {'status': 'active', 'stages': [stage]}},
            'pending_reviews': {order_id: review}}, 'effect_ledger': []})
        self.owner.return_value = {'prior_loop_status': 'restored', 'order_id': order_id,
            'worktree': worktree.name, 'worktree_path': str(worktree)}
        envelope, digest = atom.create_envelope(child, self.issue, self.issue['body'], child_paths['envelope'],
                                               environ=env, authorization_reference=ref(child_path))
        entry_path = child_paths['envelope'].parent / 'revision-entry.json'
        binding = atom.issue_execution.revision_context(atom.issue_admission.validate_issue(self.issue, envelope), ref(entry_path), digest)
        self.assertEqual(binding['revision_entry']['context']['kind'], 'ci_correction')
        self.assertEqual(envelope['execution']['source_head'], head)
        atom.issue_execution.validate_worktree(worktree, binding)
        self.assertEqual(atom._git(root, 'rev-parse', 'HEAD'), source_head)
        # A retained previous prompt cannot select the next envelope's entry.
        snapshot = atom.read_json(root / '.noodle/state.snapshot.json', 'snapshot')
        snapshot['state']['orders'][order_id]['stages'][0]['prompt'] = json.dumps({'revision_context': ref(original_bundle / 'envelope.json')})
        atom.save_json(root / '.noodle/state.snapshot.json', snapshot)
        with self.assertRaises(atom.issue_admission.AdmissionRefusal) as caught:
            atom.issue_execution.worker(child_paths['envelope'], digest, worktree, [],
                reader=lambda *_: self.issue, environ={}, entry_reference=ref(entry_path))
        self.assertEqual(caught.exception.invalid['field'], 'worker.session_id')
        original_entry = atom.read_json(entry_path, 'entry')
        controls = [({**envelope, 'execution': {**envelope['execution'], 'source_head': source_head}}, original_entry, 'revision.entry.instructions'),
                    (envelope, {**original_entry, 'prior_attempts': []}, 'correction.entry.terminal'),
                    (envelope, {**original_entry, 'native_acceptance': ref(self.source)}, 'revision.native.acceptance'),
                    (envelope, {**original_entry, 'candidate_head': source_head}, 'correction.entry.identity')]
        for changed_envelope, changed_entry, field in controls:
            with self.subTest(field=field), self.assertRaises(atom.issue_admission.AdmissionRefusal) as caught:
                atom.issue_execution.validate_revision_entry(changed_envelope, changed_entry, digest)
            self.assertEqual(caught.exception.invalid['field'], field)
        # A later failed CI keeps this child's sealed entry and every previous edge.
        subprocess.run(['git', 'merge', '--no-edit', target], cwd=worktree, check=True, capture_output=True)
        successor_head = atom._git(worktree, 'rev-parse', 'HEAD')
        successor_publication = {**self.publication, 'head': successor_head,
                                 'tree': atom._git(worktree, 'rev-parse', 'HEAD^{tree}')}
        child_state.update(authorization_sha256=ref(child_path)['sha256'], phase='ci',
            issue={'number': 131}, publication=successor_publication, envelope_sha256=digest,
            admission_sha256=atom.digest_file(child_paths['envelope'].parent / 'prepared.json'))
        atom.save_json(child_paths['state'], child_state)
        next_stage = {'status': 'review', 'skill': 'execute', 'provider': 'codex',
            'model': child['carrier']['codex']['model'],
            'prompt': json.dumps(atom.issue_execution.projection(binding, digest, 'supervised')),
            'attempts': [*original_entry['prior_attempts'], {**attempt, 'session_id': 'next-session', 'attempt_id': 'attempt-next'}]}
        snapshot['state']['orders'][order_id]['stages'] = [next_stage]
        snapshot['state']['pending_reviews'][order_id] = {**review, 'session_id': 'next-session',
            **{key: next_stage.get(key) for key in ('task_key', 'skill', 'provider', 'model', 'runtime', 'prompt')}}
        atom.save_json(root / '.noodle/state.snapshot.json', snapshot)
        atom.save_json(child_paths['claim'], {'repository': child['repository'], 'subject': child['repository'] + '#131',
            'head': successor_head, 'tree': successor_publication['tree'], 'base_head': target,
            'order_id': order_id, 'worktree_name': worktree.name, 'worktree_path': str(worktree), 'session_id': 'next-session'})
        next_authorization = {**child, 'prior_atom': ref(child_path), 'prior_publication': successor_publication}
        with patch.object(atom.issue_execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'):
            self.assertEqual(self.prior_validator(next_authorization)['prior_envelope_sha256'], digest)
            changed = copy.deepcopy(snapshot)
            changed['state']['orders'][order_id]['stages'][0]['attempts'] = next_stage['attempts'][-1:]
            atom.save_json(root / '.noodle/state.snapshot.json', changed)
            with self.assertRaises(atom.AtomRefusal) as caught:
                self.prior_validator(next_authorization)
            self.assertEqual(caught.exception.invalid['field'], 'amendment.prior_revision.attempts')
            atom.save_json(root / '.noodle/state.snapshot.json', snapshot)
        self.assertEqual(atom.validate_correction_lineage(child, ref(child_path), child_state), 1)
        child_state['writes']['issue_base']['status'] = 'offered'
        with self.assertRaises(atom.AtomRefusal) as caught:
            atom.validate_correction_lineage(child, ref(child_path), child_state)
        self.assertEqual(caught.exception.invalid['field'], 'correction.lineage.effects')

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



def native_ref(path):
    return {'path': str(path), 'sha256': atom.digest_file(path)}


def native_save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
    return path


class NativeFailedProvider:
    def __init__(self, authorization):
        self.authorization = authorization
        self.head = authorization['prior_publication']['head']
        self.workflow = authorization['workflow']
        self.run = {'id': 19, 'run_attempt': 1, 'head_sha': self.head,
                    'event': 'pull_request', 'path': self.workflow['path'],
                    'status': 'completed', 'conclusion': 'failure'}
        self.job = {'id': 23, 'run_id': 19, 'run_attempt': 1, 'head_sha': self.head,
                    'name': self.workflow['job'], 'status': 'completed', 'conclusion': 'failure',
                    'steps': [{'name': self.workflow['step'], 'status': 'completed', 'conclusion': 'failure'}]}

    def repository_info(self):
        return {'full_name': self.authorization['repository'], 'default_branch': 'main'}

    def base_head(self, branch):
        assert branch == 'main'
        return self.authorization['base_head']

    def pull(self, number):
        prior = self.authorization['prior_publication']
        assert number == prior['pr']['number']
        return {'number': number, 'state': 'open', 'merged': False,
                'head': {'ref': prior['branch'], 'sha': self.head}, 'base': {'ref': 'main'},
                'body': 'Refs ' + self.authorization['repository'] + '#' + str(self.authorization['issue']['number'])}

    def branch(self, branch):
        assert branch == self.authorization['prior_publication']['branch']
        return {'object': {'sha': self.head}}

    def workflow_runs(self, head):
        assert head == self.head
        return {'workflow_runs': [self.run]}

    def jobs(self, run_id):
        assert run_id == self.run['id']
        return {'jobs': [self.job]}

    def job_log(self, job_id):
        return {'job_id': job_id, 'raw': b'disposable exact-head failure\n', 'gap': None}


def native_ci_correction(root, project, wt, original_bundle, selected, issue, carrier, env):
    runtime = project / '.noodle'
    process = None
    started = time.monotonic()

    def command(argv, cwd=project):
        before = time.monotonic()
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        with (root / 'ci-commands.ndjson').open('a') as stream:
            stream.write(json.dumps({'argv': list(map(str, argv)), 'cwd': str(cwd), 'exit': result.returncode,
                                    'stdout': result.stdout, 'stderr': result.stderr,
                                    'elapsed_seconds': time.monotonic() - before}) + '\n')
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout.strip()

    def git(*args, cwd=project):
        return command(['git', *args], cwd)

    def snapshot():
        return json.loads((runtime / 'state.snapshot.json').read_text())['state']

    def wait(predicate, label):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            value = predicate()
            if value:
                return value
            if process is not None and process.poll() is not None:
                raise AssertionError('native owner exited: ' + (root / 'ci-daemon.stderr').read_text())
            time.sleep(.05)
        raise AssertionError('timeout: ' + label)

    original = json.loads((original_bundle / 'envelope.json').read_text())
    order = original['execution']['order_id']
    old_stage = copy.deepcopy(snapshot()['orders'][order]['stages'][0])
    retained_head = git('rev-parse', 'HEAD', cwd=wt)
    retained_tree = git('rev-parse', 'HEAD^{tree}', cwd=wt)
    assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=wt) == ''
    terminal = native_execution.blocked_outcome(original, native_execution.read_owner(original), completed=True)
    assert terminal['message']['outcome'] == 'completed'
    target = git('commit-tree', original['base_head'] + '^{tree}', '-p', original['base_head'],
                 '-m', 'Advance disposable provider base independently')
    git('update-ref', 'refs/remotes/origin/main', target)
    accepted = Path(env['FIXTURE_NATIVE_ACCEPTED'])
    parent_path = root / 'parent-authorization.json'
    parent_paths = atom.artifact_paths(parent_path)
    native_save(parent_paths['envelope'], original)
    parent = {'schema_version': 3, 'control_root': str(project), 'repository': original['repository'],
              'base_head': original['base_head'], 'task': original['execution']['task'], 'issue': issue,
              'noodle': carrier['noodle'], 'carrier': {k: v for k, v in carrier.items() if k != 'noodle'},
              'instruction_pins': [{'path': '.agents/skills/execute/SKILL.md',
                                    'sha256': atom.digest_file(project / '.agents/skills/execute/SKILL.md')}]}
    native_save(parent_path, parent)
    publication = {'head': retained_head, 'tree': retained_tree, 'branch': wt.name, 'pr': {'number': 41}}
    packet = native_save(root / 'selected-scope-fixture.json',
                  {'selection': {'schema': 2, 'native_acceptance': native_ref(accepted)}, 'output': str(parent_paths['directory'])})
    parent_state = {'authorization_sha256': native_ref(parent_path)['sha256'], 'publication': publication,
                    'envelope_sha256': native_ref(parent_paths['envelope'])['sha256'],
                    'scope_amendment': {'selection': native_ref(packet)}}
    native_save(parent_paths['state'], parent_state)
    child = {**parent, 'prior_atom': native_ref(parent_path), 'prior_publication': publication,
             'base_head': target, 'lifecycle_owner': {'fixture': 'selected runtime'},
             'workflow': {'path': '.github/workflows/runtime.yml', 'job': 'runtime', 'step': 'Accept runtime'}}
    new_body = atom.correction_base_body(parent, issue['body'], target, retained_head)
    issue = {**issue, 'body': new_body, 'updated_at': '2026-10-04T00:00:00Z'}
    child['issue'] = issue
    provider = NativeFailedProvider(child)
    failure, raw = atom.failed_ci_context(provider, child, provider.run, {'jobs': [provider.job]}, root / 'failed-job.log')
    (root / 'failed-job.log').write_bytes(raw)
    child['failure_context'] = failure
    child_path = native_save(root / 'child-authorization.json', child)
    paths = atom.artifact_paths(child_path)
    (root / 'issue-readback.json').write_text(json.dumps(issue))
    code = root / 'fixture-code'
    code.mkdir()
    source = Path(atom.__file__).resolve().parent
    for name in ('test_admission_revision.py', 'test_issue_admission.py'):
        (code / name).write_bytes((source / 'tests' / name).read_bytes())
    env['PYTHONPATH'] = str(code) + os.pathsep + str(source)
    prior = {'prior_loop_status': 'restored', 'order_id': order}
    with patch.object(atom, 'verify_prior_atom', return_value=prior), \
            patch.object(atom, 'correction_revision_source', return_value=(parent, parent_state, parent_paths, native_ref(accepted))), \
            patch.object(atom, 'validate_lifecycle_owner', return_value=selected / 'issue-atom'):
        envelope, digest = atom.create_envelope(child, issue, new_body, paths['envelope'],
                                                environ=env, authorization_reference=native_ref(child_path))
    bundle = paths['envelope'].parent
    prepared = json.loads((bundle / 'prepared.json').read_text())
    entry = json.loads((bundle / 'revision-entry.json').read_text())
    assert entry['kind'] == 'ci_correction' and entry['native_acceptance'] == native_ref(accepted)
    assert entry['old_base'] == original['base_head'] and entry['target_base'] == target
    assert envelope['execution']['source_head'] == retained_head
    (project / '.noodle.toml').write_bytes((bundle / 'noodle.toml').read_bytes())
    env['SOODLES_ADMISSION_LAUNCHER'] = str(bundle / 'launcher')
    before = (root / 'sentinel.ndjson').read_bytes()
    state = {'authorization_sha256': native_ref(child_path)['sha256'], 'envelope_sha256': digest,
             'admission_sha256': atom.digest_file(bundle / 'prepared.json'),
             'correction_ack_prefix': (runtime / 'control-ack.ndjson').read_text(),
             'correction_prior': {'order_id': order, 'worktree': wt.name, 'worktree_path': str(wt), 'stage': old_stage}}
    stdout = (root / 'ci-daemon.stdout').open('w')
    stderr = (root / 'ci-daemon.stderr').open('w')
    try:
        process = subprocess.Popen(prepared['next']['argv'], env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        state['noodle_start'] = {'status': 'started', 'pid': process.pid, 'argv': prepared['next']['argv'],
            'process_argv': prepared['process_argv'], 'config_sha256': atom.digest_file(bundle / 'noodle.toml')}
        native_save(paths['state'], state)
        native_save(root / 'ci-daemon-launch.json', {'argv': prepared['next']['argv'], 'pid': process.pid})
        wait(lambda: command(['ps', '-p', str(process.pid), '-o', 'command=']) == ' '.join(prepared['process_argv']), 'native exec')
        wait(lambda: (runtime / 'status.json').exists(), 'native status')
        time.sleep(.2)
        for index in range(30):
            before_call = time.monotonic()
            result = atom.advance_correction(child, paths, state, provider)
            native_save(root / ('owner-' + str(index) + '.json'), {'result': result, 'state': copy.deepcopy(state),
                 'native': snapshot(), 'elapsed_seconds': time.monotonic() - before_call})
            if result['action'] == 'correction_released':
                break
            if result['action'] != 'correction_release_pending':
                assert (root / 'sentinel.ndjson').read_bytes() == before
            key = {'correction_review_pending': 'correction_review', 'correction_edit_pending': 'correction_edit',
                   'correction_requeue_pending': 'correction_requeue', 'correction_release_pending': 'correction_release'}[result['action']]
            control = state[key]
            wait(lambda: any(json.loads(line).get('id') == control['id'] for line in
                             (runtime / 'control-ack.ndjson').read_text().splitlines()), 'native ' + control['action'])
        else:
            raise AssertionError('owner did not release')
        wait(lambda: (root / 'revision-outcome.json').exists(), 'sentinel completed outcome')
        outcome = json.loads((root / 'revision-outcome.json').read_text())
        assert outcome['returncode'] == 0, outcome
        wait(lambda: snapshot()['orders'][order]['stages'][0]['status'] == 'review', 'successor review')
        final = snapshot()['orders'][order]['stages'][0]
        launches = [json.loads(line) for line in (root / 'sentinel.ndjson').read_text().splitlines()]
        assert len(launches) == len(before.splitlines()) + 1
        assert launches[-1]['cwd'] == str(wt)
        assert len(final['attempts']) == len(old_stage['attempts']) + 1
        assert final['attempts'][:-1] == entry['prior_attempts']
        assert final.get('extra', {}).get('interrupted_execution_history', []) == []
        assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=wt) == ''
        git('merge-base', '--is-ancestor', target, 'HEAD', cwd=wt)
        assert atom.digest_file(terminal['source']['path']) == terminal['source']['sha256']
        controls = [json.loads(line) for line in (runtime / 'control-ack.ndjson').read_text()[len(state['correction_ack_prefix']):].splitlines()]
        assert [value['action'] for value in controls] == ['request-changes', 'edit-item', 'requeue', 'mode']
        native_save(root / 'ci-final-snapshot.json', snapshot())
        return {'status': 'passed', 'owner_entry': 'issue_atom.advance_correction', 'successor_count': 1,
                'same_order': order, 'same_worktree': str(wt), 'prior_attempts_preserved': True,
                'interruption_history_count': 0, 'retained_head': retained_head, 'target_base': target,
                'final_head': git('rev-parse', 'HEAD', cwd=wt), 'elapsed_seconds': time.monotonic() - started,
                'model_calls': 0, 'live_provider_calls': 0, 'scope': 'producer and held owner to native continuation',
                'setup_stubs': ['verify_prior_atom', 'correction_revision_source', 'validate_lifecycle_owner'],
                'unknown': ['Agent engineering semantics', 'live CI', 'landing', 'complete admission lifecycle'],
                'source_hashes': {name: atom.digest_file(source / name) for name in
                                  ('issue_atom.py', 'issue_admission.py', 'issue_execution.py', 'supervisor_admission.py',
                                   'tests/test_correction_preparation.py')}}
    finally:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stdout.close()
        stderr.close()
        native_save(root / 'ci-cleanup.json', {'daemon_pid': process.pid if process else None,
                                      'daemon_returncode': process.returncode if process else None})


def native_completed_control(output, accepted):
    import fcntl
    import platform
    import sys
    from test_issue_admission import issue_fixture
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    project = root / 'project'
    runtime = project / '.noodle'
    binary = accepted['binary']['path']
    env = {k: v for k, v in os.environ.items() if not any(x in k.upper() for x in ('TOKEN', 'API_KEY', 'SECRET'))}
    env.update(NOODLE_NO_BROWSER='1', GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
    process = None

    def run(argv, cwd=None):
        start = time.monotonic()
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        with (root / 'setup-commands.ndjson').open('a') as stream:
            stream.write(json.dumps({'argv': list(map(str, argv)), 'cwd': str(cwd), 'exit': result.returncode,
                                    'stdout': result.stdout, 'stderr': result.stderr,
                                    'elapsed_seconds': time.monotonic() - start}) + '\n')
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout.strip()

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def wait(predicate, label):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if process is not None and process.poll() is not None:
                raise AssertionError('initial daemon exited')
            value = predicate()
            if value:
                return value
            time.sleep(.05)
        raise AssertionError('timeout: ' + label)

    try:
        run(['git', 'init', '-b', 'main', project])
        run(['git', 'config', 'user.name', 'Native Fixture'], project)
        run(['git', 'config', 'user.email', 'fixture@example.invalid'], project)
        source = Path(atom.__file__).resolve().parent
        for name in native_supervisor.BUNDLE_PATHS:
            write(project / name, (source / name).read_text())
        reader = "import json, os\nfrom pathlib import Path\ndef fetch_issue(repository, number):\n    return json.loads(Path(os.environ['FIXTURE_ISSUE_READBACK']).read_text())\n"
        write(project / 'github_reader.py', reader)
        write(project / '.gitignore', '.noodle/\n.worktrees/\n.noodle.toml\n')
        write(project / 'candidate.txt', 'candidate\n')
        write(project / 'new.txt', 'fixture evidence\n')
        for skill in ('execute', 'schedule'):
            write(project / '.agents/skills' / skill / 'SKILL.md',
                  f'---\nname: {skill}\ndescription: Local fixture only.\nschedule: Local fixture only.\n---\nRemain idle.\n')
        sentinel = root / 'fixture-bin/codex'
        write(sentinel, '#!' + sys.executable + '\n' + """
import json, os, pathlib, subprocess, sys
root = pathlib.Path(ROOT)
prompt = sys.stdin.read()
with (root / 'sentinel.ndjson').open('a') as stream:
    stream.write(json.dumps({'pid': os.getpid(), 'argv': sys.argv, 'cwd': os.getcwd(), 'prompt': prompt})+'\\n')
print(json.dumps({'type': 'thread.started', 'thread_id': 'fixture-'+str(os.getpid())}), flush=True)
bundle = pathlib.Path(os.environ['SOODLES_ADMISSION_LAUNCHER']).parent
if (bundle / 'revision-entry.json').exists():
    sys.path.insert(0, str(root / 'fixture-code'))
    from test_admission_revision import native_successor
    native_successor(root)
else:
    pathlib.Path('candidate.txt').write_text('completed candidate\\n')
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Keep disposable completed candidate'], check=True, capture_output=True)
    argv = [str(bundle / 'launcher'), 'stage-outcome', 'completed', 'Completed disposable candidate.']
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    (root / 'initial-outcome.json').write_text(json.dumps({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}))
    assert result.returncode == 0, result.stdout + result.stderr
    print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 0, 'output_tokens': 0}}), flush=True)
""".replace('ROOT', repr(str(root))))
        sentinel.chmod(0o755)
        backlog = root / 'backlog-sync'
        write(backlog, '#!/bin/sh\nexit 0\n'); backlog.chmod(0o755)
        write(project / '.noodle.toml', f'mode = "manual"\n[routing.defaults]\nprovider = "codex"\nmodel = "fixture"\n[agents.codex]\npath = {json.dumps(str(sentinel.parent))}\n[server]\nenabled = false\n[concurrency]\nmax_concurrency = 1\n[adapters.backlog.scripts]\nsync = {json.dumps(str(backlog))}\nadd = {json.dumps(str(backlog))}\ndone = {json.dumps(str(backlog))}\nedit = {json.dumps(str(backlog))}\n')
        run(['git', 'add', '.'], project); run(['git', 'commit', '-m', 'Keep minimal native fixture inputs'], project)
        run(['git', 'remote', 'add', 'origin', 'git@github.com:ed3c/soodles.git'], project)
        base = run(['git', 'rev-parse', 'HEAD'], project)
        run(['git', 'update-ref', 'refs/remotes/origin/main', base], project)
        run(['git', 'symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main'], project)
        issue, _ = issue_fixture()
        contract = native_admission.parse_contract(issue['body'])
        contract.update(schema=3, base_head=base, write_paths=['candidate.txt', 'new.txt'],
                        required_paths=['candidate.txt', 'new.txt'], evidence_manifest='new.txt',
                        frozen_paths=[{'path': 'candidate.txt', 'revision': 'base', 'sha256': atom.digest_file(project / 'candidate.txt')}])
        issue['body'] = '<!-- soodles:execution-v1 -->\n```json\n' + json.dumps(contract) + '\n```\n<!-- /soodles:execution-v1 -->'
        native_save(root / 'issue-readback.json', issue)
        env.update(FIXTURE_ISSUE_READBACK=str(root / 'issue-readback.json'), NOODLES_TOKEN_COMMAND='printf fixture-installation-token')
        carrier = {'platform': platform.system().lower() + '_' + platform.machine().lower(), 'noodle': accepted['binary'],
                   'codex': {**native_ref(sentinel), 'model': 'fixture', 'argv': ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture']}}
        selected = root / 'selected-runtime'; selected.mkdir()
        for name in native_supervisor.BUNDLE_PATHS:
            write(selected / name, reader if name == 'github_reader.py' else (source / name).read_text())
        bundle = root / 'original-bundle'
        prepared = native_supervisor.prepare(issue, carrier, project, bundle, environ=env, wire_host=True,
            task='Retain this disposable candidate and report one completed outcome.',
            instruction_pins=[{'path': '.agents/skills/execute/SKILL.md', 'sha256': atom.digest_file(project / '.agents/skills/execute/SKILL.md')}])
        original = json.loads((bundle / 'envelope.json').read_text())
        order = original['execution']['order_id']
        wt = project / '.worktrees' / original['execution']['worktree']
        prompt = json.dumps(native_execution.projection(native_admission.validate_issue(issue, original), atom.digest_file(bundle / 'envelope.json'), 'supervised'))
        stage = {'stage_index': 0, 'task_key': 'execute', 'status': 'pending', 'provider': 'codex', 'model': 'fixture',
                 'runtime': 'process', 'skill': 'execute', 'prompt': prompt, 'attempts': []}
        stamp = '2026-10-04T00:00:00Z'
        canonical = {'orders': {order: {'order_id': order, 'status': 'active', 'stages': [stage]}},
                     'pending_reviews': {}, 'mode': 'manual', 'schema_version': 1, 'last_event_id': '1'}
        native_save(runtime / 'state.snapshot.json', {'order_revision': 'a' * 32, 'state': canonical, 'effect_ledger': [], 'generated_at': stamp})
        native_save(runtime / 'orders.json', {'generated_at': stamp, 'orders': [{'id': order, 'status': 'active',
             'stages': [{k: v for k, v in stage.items() if k not in ('stage_index', 'attempts')}]}]})
        native_save(runtime / 'pending-review.json', [])
        (project / '.noodle.toml').write_bytes((bundle / 'noodle.toml').read_bytes())
        env['SOODLES_ADMISSION_LAUNCHER'] = str(bundle / 'launcher')
        stdout = (root / 'initial-daemon.stdout').open('w'); stderr = (root / 'initial-daemon.stderr').open('w')
        process = subprocess.Popen(prepared['next']['argv'], env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        native_save(root / 'initial-daemon-launch.json', {'argv': prepared['next']['argv'], 'pid': process.pid})
        wait(lambda: (runtime / 'status.json').exists(), 'initial status')
        with (runtime / 'control.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with (runtime / 'control.ndjson').open('a') as stream:
                stream.write(json.dumps({'id': 'fixture-initial-release', 'action': 'mode', 'value': 'supervised'}) + '\n')
        wait(lambda: (root / 'initial-outcome.json').exists(), 'initial completed outcome')
        wait(lambda: json.loads((runtime / 'state.snapshot.json').read_text())['state']['orders'][order]['stages'][0]['status'] == 'review', 'initial parked review')
        process.send_signal(signal.SIGTERM); process.wait(timeout=15)
        stdout.close(); stderr.close()
        result = native_ci_correction(root, project, wt, bundle, selected, issue, carrier, env)
        native_save(root / 'result.json', result)
        return result
    except Exception as error:
        import traceback
        native_save(root / 'failure.json', {'error': str(error), 'traceback': traceback.format_exc()})
        raise
    finally:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=15)
        launches = [json.loads(line) for line in (root / 'sentinel.ndjson').read_text().splitlines()] if (root / 'sentinel.ndjson').exists() else []
        pids = ([process.pid] if process else []) + [value['pid'] for value in launches]
        remaining = [pid for pid in pids if subprocess.run(['ps', '-p', str(pid), '-o', 'pid='], capture_output=True, text=True).stdout.strip()]
        native_save(root / 'process-readback.json', {'pids': pids, 'remaining': remaining})
        assert not remaining, remaining


def run_native_correction(accepted_path, output):
    accepted = json.loads(Path(accepted_path).read_text())
    for name in ('binary', 'acceptance', 'interface'):
        assert atom.digest_file(accepted[name]['path']) == accepted[name]['sha256']
    with patch.dict(os.environ, {'FIXTURE_NATIVE_ACCEPTED': str(Path(accepted_path).resolve())}):
        return native_completed_control(output, accepted)



if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--native":
        print(json.dumps(run_native_correction(sys.argv[2], sys.argv[3]), indent=2))
    else:
        unittest.main()
