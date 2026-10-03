"""Typed revision controls use disposable Git objects and original owner readbacks."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import issue_admission as admission
import issue_atom as atom
import issue_execution as execution
import supervisor_admission as supervisor
from test_issue_admission import issue_fixture


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def body(contract):
    return 'Retain original task.\n<!-- soodles:execution-v1 -->\n```json\n' + json.dumps(contract) + '\n```\n<!-- /soodles:execution-v1 -->\n'


class RevisionFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.root = self.directory / 'control'
        self.root.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('remote', 'add', 'origin', 'https://github.com/ed3c/soodles.git')
        (self.root / '.gitignore').write_text('.noodle/\n.worktrees/\n')
        for name in ('allowed.py', 'reference.md', 'AGENTS.md'):
            (self.root / name).write_text('original ' + name + '\n')
        for name in supervisor.BUNDLE_PATHS + ('.agents/skills/execute/SKILL.md', '.agents/skills/schedule/SKILL.md'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((Path(__file__).resolve().parents[1] / name).read_bytes())
        self.base = self.commit()
        (self.root / 'base-only.txt').write_text('provider advance\n')
        self.target = self.commit()
        self.issue, self.envelope = issue_fixture()
        self.contract = admission.parse_contract(self.issue['body'])
        self.contract.update(schema=3, base_head=self.base,
            write_paths=['allowed.py', 'manifest.json', 'reference.md'],
            required_paths=['allowed.py', 'manifest.json', 'reference.md'], evidence_manifest='manifest.json',
            frozen_paths=[{'path': 'reference.md', 'revision': 'base', 'sha256': sha(self.root / 'reference.md')}])
        self.issue.update(body=body(self.contract), title='Original')
        order = admission.scoped_order_id(18, self.root)
        self.wt = self.root / '.worktrees' / (order + '-0-execute')
        self.git('worktree', 'add', '-b', self.wt.name, self.wt, self.base)
        (self.wt / 'allowed.py').write_text('retained candidate\n')
        self.candidate = self.commit(self.wt)
        self.tree = self.git('rev-parse', 'HEAD^{tree}', cwd=self.wt)
        self.envelope.update(schema=2, base_head=self.base, write_paths=self.contract['write_paths'],
                             body_sha256=admission.body_digest(self.issue['body']))
        self.envelope['execution'].update(control_root=str(self.root), order_id=order, worktree=self.wt.name,
            source_head=self.base, instruction_context=admission.resolve_instruction_context(self.root, self.base,
                [{'path': 'AGENTS.md', 'sha256': sha(self.root / 'AGENTS.md')}]))
        self.envelope['execution']['carrier'] = {'noodle': ref(self.root / 'allowed.py'), 'codex': {'model': 'fixture', 'argv': ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture']}}
        self.original = self.save('original-envelope.json', self.envelope)
        self.auth = {'control_root': str(self.root), 'repository': 'ed3c/soodles',
                     'base_head': self.base, 'task': self.envelope['execution']['task'],
                     'issue': self.issue, 'carrier': {k:v for k,v in self.envelope['execution']['carrier'].items() if k != 'noodle'},
                     'noodle': self.envelope['execution']['carrier']['noodle']}
        native = self.save('accepted.json', {'schema': 1, 'issue': 106, 'accepted_at': 'fixture',
            'binary': ref(self.original), 'acceptance': ref(self.original), 'interface': ref(self.original)})
        provider = self.save('provider.json', {'repository': {'full_name': 'ed3c/soodles', 'default_branch': 'main'},
                                             'branch': {'name': 'main', 'commit': {'sha': self.target}}})
        self.selection = {'schema': 2, 'type': 'base_advance', 'reason': 'Integrate exact provider base.',
            'evidence': ref(self.original), 'lifecycle_owner': {}, 'candidate_head': self.candidate,
            'candidate_tree': self.tree, 'original_envelope': ref(self.original), 'order_id': order,
            'stage_index': 0, 'terminal_session': 'original-session', 'before_contract': self.contract,
            'target_base': self.target, 'references': [], 'provider_readback': ref(provider),
            'native_acceptance': ref(native)}

    def git(self, *args, cwd=None):
        return subprocess.check_output(['git', *map(str, args)], cwd=cwd or self.root,
                                       text=True, stderr=subprocess.PIPE).strip()

    def commit(self, cwd=None):
        self.git('add', '.', cwd=cwd)
        self.git('commit', '--allow-empty', '-m', 'Preserve exact fixture subject', cwd=cwd)
        return self.git('rev-parse', 'HEAD', cwd=cwd)

    def save(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value))
        return path

    def released_scope(self, original_path, authorization=None, selection=None, index=0):
        authorization = authorization or self.auth
        selection = selection or self.selection
        selected = {**selection, 'before_contract': admission.parse_contract(authorization['issue']['body'])}
        provider = self.save(f'provider-{index}.json', {'repository': {
            'full_name': 'ed3c/soodles', 'default_branch': 'main'},
            'branch': {'name': 'main', 'commit': {'sha': selected['target_base']}}})
        selected['provider_readback'] = ref(provider)
        after_body = atom.revision_body(authorization, selected)
        packet = self.save(f'history-{index}.json', {'schema': 1, 'authorization': ref(original_path),
            'selection': selected, 'output': str(self.directory)})
        packet_ref = ref(packet)
        prepared = self.save(f'prepared-{index}.json', {'envelope_sha256': sha(self.original)})
        controls = {name: {'id': 'soodles-scope-' + packet_ref['sha256'][:24] + '-' + name, 'action': action}
            for name, action in (('scope_request', 'request-changes'), ('scope_edit', 'edit-item'),
                                 ('scope_requeue', 'requeue'), ('scope_release', 'mode'))}
        return {'amendment': {'selection': packet_ref, 'status': 'released', 'prepared': ref(prepared)},
            'issue_write': {'status': 'observed', 'selection_sha256': packet_ref['sha256'],
                'previous_body_sha256': admission.body_digest(authorization['issue']['body']),
                'body_sha256': admission.body_digest(after_body)}, 'controls': controls,
            'acks': [{**command, 'status': 'ok'} for command in controls.values()]}

    def custody(self, entry):
        directory = self.root / '.noodle/sessions/original-session'
        directory.mkdir(parents=True, exist_ok=True)
        child = subprocess.Popen(['true'])
        child.wait()
        files = {'spawn.json': {'session_id': 'original-session', 'worktree_path': str(self.wt), 'retry_count': 0},
                 'process.json': {'session_id': 'original-session', 'pid': child.pid},
                 'events.ndjson': {'terminal': 'completed'}, 'prompt.txt': {'prompt': 'original'}}
        for name, value in files.items():
            (directory / name).write_text(json.dumps(value))
        return {'reason': entry['prior_attempts'][-1]['error'], 'session_id': 'original-session',
                'attempt_id': 'attempt-0', 'attempt': len(entry['prior_attempts']) - 1,
                'candidate_head': self.candidate, 'branch': self.wt.name,
                'worktree_name': self.wt.name, 'worktree_path': str(self.wt),
                'session_sha256': {name: sha(directory / name) for name in files}}

    def review(self, stage):
        return {'order_id': self.selection['order_id'], 'stage_index': 0, 'session_id': 'original-session',
                'worktree_name': self.wt.name, 'worktree_path': str(self.wt), 'plan': [], 'reason': 'completed',
                **{key: stage.get(key) for key in ('task_key', 'skill', 'provider', 'model', 'runtime', 'prompt')}}

    def criteria(self, advance=False):
        return {**self.selection, 'type': 'criteria_correction',
                'target_base': self.target if advance else self.base,
                'references': [{'path': 'reference.md', 'required': False, 'frozen': None},
                    {'path': 'allowed.py', 'required': True,
                     'frozen': {'revision': 'base', 'source_head': self.target if advance else self.base}}]}

    def entry(self):
        issue = {**self.issue, 'body': atom.revision_body(self.auth, self.selection)}
        envelope = {**self.envelope, 'base_head': self.target, 'body_sha256': admission.body_digest(issue['body'])}
        envelope = copy.deepcopy(envelope)
        envelope['execution']['carrier']['noodle'] = admission.load_revision_native(self.selection["native_acceptance"], self.root)
        path = self.save('effective-envelope.json', envelope)
        events = self.save('events.json', {'original': 'completed'})
        terminal = {'session_id': 'original-session', 'attempt_id': 'attempt-0', 'source': ref(events),
                    'message': {'outcome': 'completed', 'blocking': False}}
        entry = {'schema': 1, 'kind': 'base_advance', 'original_envelope': ref(self.original),
            'envelope_sha256': sha(path), 'selection_sha256': 'a' * 64,
            'candidate_head': self.candidate, 'candidate_tree': self.tree,
            'old_base': self.base, 'target_base': self.target, 'terminal': terminal,
            'native_acceptance': self.selection['native_acceptance'], 'prior_attempts': [],
            **{key: self.envelope['execution'][key] for key in ('order_id', 'stage_index', 'worktree')}}
        entry_path = self.save('revision-entry.json', entry)
        binding = execution.revision_context(admission.validate_issue(issue, envelope), ref(entry_path), sha(path))
        return issue, envelope, binding, entry_path


class AdmissionRevisionTests(unittest.TestCase):
    def setUp(self):
        self.f = RevisionFixture()
        self.addCleanup(self.f.temp.cleanup)

    def continuation_fixture(self):
        f = self.f
        issue, envelope, binding, entry_path = f.entry()
        entry = binding['revision_entry']['context']
        attempt = {'attempt_id': 'attempt-0', 'session_id': 'original-session', 'status': 'failed',
                   'worktree_name': f.wt.name, 'error': 'changes requested: exact target'}
        entry['prior_attempts'] = [attempt]
        entry_path.write_text(json.dumps(entry))
        binding['revision_entry']['reference'] = ref(entry_path)
        stage = {'task_key': 'execute', 'skill': 'execute', 'provider': 'codex', 'model': 'fixture',
                 'runtime': 'process', 'prompt': 'original prompt', 'attempts': [attempt], 'status': 'failed'}
        custody = f.custody(entry)
        stage['extra'] = {'request_changes_recovery': custody}
        review = f.review(stage)
        order_id = entry['order_id']
        owner = {'state': {'orders': {order_id: {'status': 'failed', 'plan': [], 'stages': [stage]}},
                           'pending_reviews': {order_id: review}}}
        amendment = {'native_review': copy.deepcopy(review), 'session_sha256': copy.deepcopy(custody['session_sha256']),
                     'restart_offered': True, 'ack_prefix': ''}
        state = {'scope_amendment': amendment, 'scope_request': {'id': 'request', 'action': 'request-changes'}}
        return issue, envelope, binding, owner, state

    def test_continuation_distinguishes_failed_edited_and_pending_without_new_attempt(self):
        f = self.f
        _, _, binding, owner, state = self.continuation_fixture()
        amendment = state['scope_amendment']
        order_id = binding['execution']['order_id']
        stage = owner['state']['orders'][order_id]['stages'][0]
        before = copy.deepcopy(stage['attempts'])
        observe = lambda: atom.scope_continuation_readback(binding, owner, amendment, state, 'new prompt')
        self.assertEqual(observe()['position'], 'failed')
        state['scope_edit'] = {'id': 'edit'}
        stage['prompt'] = 'new prompt'
        owner['state']['pending_reviews'][order_id]['prompt'] = 'new prompt'
        self.assertEqual(observe()['position'], 'edited')
        state['scope_requeue'] = {'id': 'requeue'}
        receipt = {'binding': stage['extra']['request_changes_recovery'],
                   'review': owner['state']['pending_reviews'].pop(order_id)}
        stage['extra'] = {'request_changes_requeued': receipt}
        stage['status'] = 'pending'
        owner['state']['orders'][order_id]['status'] = 'active'
        self.assertEqual(observe()['position'], 'pending')
        self.assertEqual(stage['attempts'], before)
        for key in ('reason', 'branch', 'session_id', 'candidate_head', 'attempt_id', 'attempt'):
            original = receipt['binding'][key]
            receipt['binding'][key] = 'foreign'
            with self.subTest(key=key), self.assertRaises(admission.AdmissionRefusal):
                observe()
            receipt['binding'][key] = original
        receipt['review']['reason'] = 'explicit rejection'
        with self.assertRaisesRegex(atom.AtomRefusal, 'scope.continuation.custody'):
            observe()

    def test_continuation_rejects_changed_candidate_session_history_and_released_state(self):
        f = self.f
        _, _, binding, owner, state = self.continuation_fixture()
        amendment = state['scope_amendment']
        observe = lambda: atom.scope_continuation_readback(binding, owner, amendment, state, 'new prompt')
        for name in ('spawn.json', 'prompt.txt', 'events.ndjson', 'process.json'):
            path = f.root / '.noodle/sessions/original-session' / name
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(file=name), self.assertRaises(admission.AdmissionRefusal):
                observe()
            path.write_bytes(original)
        (f.wt / 'dirty.txt').write_text('dirty')
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'worker.git.residue'):
            observe()
        (f.wt / 'dirty.txt').unlink()
        state['scope_release'] = {'id': 'release'}
        with self.assertRaisesRegex(atom.AtomRefusal, 'scope.continuation.lineage'):
            observe()
        del state['scope_release']
        amendment.pop('native_review')
        with self.assertRaisesRegex(atom.AtomRefusal, 'scope.continuation.history'):
            observe()

    def test_control_readback_retains_intents_and_rejects_foreign_or_rejected_ack(self):
        f = self.f
        runtime = f.root / '.noodle'
        runtime.mkdir()
        state = {'scope_amendment': {'ack_prefix': ''},
                 'scope_request': {'id': 'request', 'action': 'request-changes'}}
        commands = {'scope_request': state['scope_request']}
        mailbox = runtime / 'control.ndjson'
        mailbox.write_text(json.dumps(commands['scope_request']) + '\n')
        before = mailbox.read_bytes()
        result = atom.scope_control_readback(f.auth, state, commands)
        self.assertEqual(result, {'acks': [], 'pending': [commands['scope_request']]})
        self.assertEqual(mailbox.read_bytes(), before)
        for ack in ({'id': 'foreign', 'action': 'request-changes', 'status': 'ok'},
                    {'id': 'request', 'action': 'request-changes', 'status': 'error'}):
            (runtime / 'control-ack.ndjson').write_text(json.dumps(ack) + '\n')
            with self.subTest(ack=ack), self.assertRaisesRegex(atom.AtomRefusal, 'scope.control.foreign'):
                atom.scope_control_readback(f.auth, state, commands)

    def test_held_continuation_persists_one_start_before_unknown_spawn_and_never_retries(self):
        f = self.f
        issue, envelope, binding, owner, state = self.continuation_fixture()
        amendment = state['scope_amendment']
        bundle = f.directory / 'owner/admission'
        bundle.mkdir(parents=True)
        envelope_path = bundle / 'envelope.json'
        envelope_path.write_text(json.dumps(envelope))
        (bundle / 'revision-entry.json').write_text(json.dumps(binding['revision_entry']['context']))
        (bundle / 'noodle.toml').write_text('mode = "supervised"\n')
        (f.root / '.noodle.toml').write_bytes((bundle / 'noodle.toml').read_bytes())
        with (f.root / '.git/info/exclude').open('a') as stream:
            stream.write('\n.noodle.toml\n')
        launcher = bundle / 'start'
        launcher.write_text('fixture start')
        auth = {**f.auth, 'noodle': envelope['execution']['carrier']['noodle']}
        process_argv = [auth['noodle']['path'], '--project-dir', str(f.root), 'start', '--mode', 'manual']
        prepared = {'next': {'argv': [str(launcher)]}, 'start': str(launcher), 'start_sha256': sha(launcher),
                    'process_argv': process_argv}
        (bundle / 'prepared.json').write_text(json.dumps(prepared))
        child = subprocess.Popen(['true']); child.wait()
        prior = {'status': 'started', 'pid': child.pid, 'argv': [str(launcher)], 'process_argv': process_argv,
                 'config_sha256': sha(bundle / 'noodle.toml'), 'original_config': None}
        state.update(noodle_start=prior, admission_sha256=sha(bundle / 'prepared.json'), envelope_sha256=sha(envelope_path))
        amendment.update(prepared=ref(bundle / 'prepared.json'), preparation={'issue': issue})
        runtime = f.root / '.noodle'
        (runtime / 'noodle.lock').touch()
        (runtime / 'state.snapshot.json').write_text(json.dumps(owner))
        command = state['scope_request']
        ack = {**command, 'status': 'ok'}
        (runtime / 'control-ack.ndjson').write_text(json.dumps(ack) + '\n')
        prompt = json.dumps(execution.projection(binding, state['envelope_sha256'], 'supervised'), sort_keys=True)
        observation = atom.scope_continuation_readback(binding, owner, amendment, state, prompt)
        observation['controls'] = {'acks': [ack], 'pending': []}
        paths = {'state': f.directory / 'checkpoint.json', 'envelope': envelope_path, 'directory': f.directory}
        real_popen = subprocess.Popen
        offers = []
        def popen(argv, *args, **kwargs):
            if argv == [str(launcher)]:
                offers.append(argv)
                raise OSError('lost replacement spawn response')
            return real_popen(argv, *args, **kwargs)
        with patch.object(execution, 'read_owner', return_value=owner), patch.object(subprocess, 'Popen', side_effect=popen):
            with self.assertRaisesRegex(atom.AtomRefusal, 'scope.continuation.start'):
                atom.ensure_noodle(auth, paths, state, {'action': 'scope_continuation'}, {}, scope_continuation=observation)
            saved = json.loads(paths['state'].read_text())
            self.assertEqual(saved['noodle_start']['status'], 'offered')
            self.assertEqual(saved['scope_amendment']['continuation_restart']['prior_start'], prior)
            self.assertEqual(saved['scope_amendment']['ack_prefix'], '')
            self.assertEqual(saved['scope_request'], command)
            with self.assertRaisesRegex(atom.AtomRefusal, 'scope.continuation.restart'):
                atom.ensure_noodle(auth, paths, state, {'action': 'scope_continuation'}, {}, scope_continuation=observation)
            self.assertEqual(len(offers), 1)

    def test_base_criteria_and_combined_preserve_every_other_requirement(self):
        f = self.f
        for selection in (f.selection, f.criteria(), f.criteria(True)):
            with self.subTest(kind=selection['type'], target=selection['target_base']):
                changed = atom.revision_body(f.auth, selection)
                result = admission.parse_contract(changed)
                for key in set(f.contract) - {'base_head', 'required_paths', 'frozen_paths'}:
                    self.assertEqual(result[key], f.contract[key])
                self.assertEqual(result['base_head'], selection['target_base'])
                self.assertTrue(changed.startswith('Retain original task.\n'))
                self.assertIn('manifest.json', result['required_paths'])
                self.assertIn('allowed.py', result['required_paths'])
                if selection['type'] == 'criteria_correction':
                    self.assertNotIn('reference.md', result['required_paths'])
                    self.assertEqual(result['frozen_paths'], [{'path': 'allowed.py', 'revision': 'base',
                        'sha256': hashlib.sha256(admission.git_bytes(f.root, selection['target_base'], 'allowed.py')).hexdigest()}])

    def test_unselected_contract_and_reference_changes_refuse(self):
        f = self.f
        for field in ('acceptance', 'write_paths', 'owner', 'behavior', 'source'):
            selected = copy.deepcopy(f.selection)
            selected['before_contract'][field] = 'replaced'
            with self.subTest(field=field), self.assertRaisesRegex(atom.AtomRefusal, 'revision.before_contract'):
                atom.revision_body(f.auth, selected)
        for change in ({'path': 'outside.py', 'required': True, 'frozen': None},
                       {'path': 'manifest.json', 'required': False, 'frozen': None},
                       {'path': 'allowed.py', 'required': True, 'frozen': {'revision': 'head', 'source_head': f.candidate}}):
            with self.subTest(change=change), self.assertRaises(atom.AtomRefusal):
                atom.revision_body(f.auth, {**f.criteria(), 'references': [change]})
        with self.assertRaisesRegex(atom.AtomRefusal, 'revision.base_only'):
            atom.revision_body(f.auth, {**f.selection, 'references': f.criteria()['references']})

    def test_non_descendant_and_wrong_base_pin_refuse(self):
        f = self.f
        with self.assertRaisesRegex(atom.AtomRefusal, 'revision.ancestry'):
            atom.revision_body(f.auth, {**f.selection, 'target_base': 'f' * 40})
        contract = copy.deepcopy(f.contract)
        contract['frozen_paths'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(atom.AtomRefusal, 'revision.original_pin'):
            atom.revision_body({**f.auth, 'issue': {**f.issue, 'body': body(contract)}},
                               {**f.selection, 'before_contract': contract})

    def test_provider_requires_exact_repository_default_branch_and_fresh_target(self):
        f = self.f
        provider = Mock()
        provider.repository_info.return_value = {'full_name': 'ed3c/soodles', 'default_branch': 'main'}
        provider.branch_info.return_value = {'name': 'main', 'commit': {'sha': f.target}}
        atom.revision_provider(f.auth, f.selection, provider)
        provider.branch_info.return_value = {'name': 'main', 'commit': {'sha': f.candidate}}
        with self.assertRaisesRegex(atom.AtomRefusal, 'revision.provider.advanced'):
            atom.revision_provider(f.auth, f.selection, provider)

    def test_revision_history_replays_exact_bodies_and_preserves_raw_authorization(self):
        f = self.f
        original = copy.deepcopy(f.auth)
        original['issue'].pop('number')
        original_path = f.save('authorization.json', original)
        state = {'authorization_sha256': sha(original_path), 'issue': {'number': 18}, 'scope_history': []}
        effective = atom.scope_history_authority(original, state)
        self.assertIn(atom.marker(sha(original_path)), effective['issue']['body'])
        with patch.object(atom, 'validate_lifecycle_owner'):
            for index, selected in enumerate((f.criteria(), f.selection)):
                entry = f.released_scope(original_path, effective, selected, index)
                after_body = atom.revision_body(effective, json.loads(Path(entry['amendment']['selection']['path']).read_text())['selection'])
                state['scope_history'].append(entry)
                effective = atom.scope_history_authority(original, state)
                self.assertEqual(effective['issue']['body'], after_body)
            self.assertEqual(effective['base_head'], f.target)
            self.assertEqual(effective['task'], original['task'])
            self.assertNotIn('reference.md', admission.parse_contract(effective['issue']['body'])['required_paths'])
            self.assertEqual(json.loads(original_path.read_text()), original)
            for field in ('issue_write', 'acks'):
                changed = copy.deepcopy(state)
                if field == 'acks':
                    changed['scope_history'][0]['acks'].pop()
                else:
                    changed['scope_history'][0]['issue_write']['previous_body_sha256'] = '0' * 64
                with self.subTest(field=field), self.assertRaises(atom.AtomRefusal):
                    atom.scope_history_authority(original, changed)

    def test_duplicate_adoption_reads_same_checkpoint_without_second_custody(self):
        f = self.f
        authorization_path = f.save('authorization.json', f.auth)
        digest = sha(authorization_path)
        output = f.directory / 'adopted'
        output.mkdir()
        packet_path = output / 'scope-selection.json'
        packet_path.write_text(json.dumps({'schema': 1, 'authorization': ref(authorization_path),
            'selection': f.selection, 'output': str(output)}))
        paths = atom.artifact_paths(authorization_path)
        state = {'authorization_sha256': digest, 'issue': {'number': 18}, 'writes': {}}
        paths['state'].write_text(json.dumps(state))
        paths['envelope'].parent.mkdir(parents=True)
        paths['envelope'].write_text(json.dumps(f.envelope))
        (f.root / '.noodle').mkdir()
        stage = {'status': 'review', 'attempts': []}
        custody = {'stage': stage, 'envelope': ref(paths['envelope'])}
        with patch.object(atom, 'validate_authorization', return_value=(f.auth, digest)), \
                patch.object(atom, 'validate_lifecycle_owner'), \
                patch.object(atom, 'scope_custody', return_value=custody) as capture, \
                patch.object(atom, 'resumed_lifecycle', return_value={}), \
                patch.object(atom, 'repair_controller'), \
                patch.object(execution, 'read_owner', return_value={'state': {'orders': {
                    f.selection['order_id']: {'stages': [stage]}}}}):
            first = atom.adopt_scope_amendment(authorization_path, packet_path, sha(packet_path))
            saved = paths['state'].read_bytes()
            self.assertEqual(atom.adopt_scope_amendment(authorization_path, packet_path, sha(packet_path)), first)
            self.assertEqual(paths['state'].read_bytes(), saved)
            capture.assert_called_once()

    def test_sealed_entry_preserves_instructions_and_limits_preintegration_exception(self):
        f = self.f
        issue, envelope, binding, path = f.entry()
        projected = execution.projection(binding, sha(f.directory / 'effective-envelope.json'), 'supervised')
        self.assertEqual(projected['issue_body'], issue['body'])
        self.assertEqual(admission.parse_contract(projected['issue_body']), projected['contract'])
        self.assertEqual(projected['admission_revision']['candidate_head'], f.candidate)
        self.assertEqual(projected['revision_context'], ref(path))
        self.assertEqual(envelope['execution']['instruction_context'], f.envelope['execution']['instruction_context'])
        self.assertEqual(envelope['execution']['source_head'], f.base)
        execution.validate_worktree(f.wt, binding)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'worker.git.head'):
            execution.validate_worktree(f.wt, envelope)
        (f.wt / 'dirty.txt').write_text('dirty')
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'worker.git.residue'):
            execution.validate_worktree(f.wt, binding)
        (f.wt / 'dirty.txt').unlink()
        for field, value in (('candidate_tree', '0' * 40), ('candidate_head', f.base), ('old_base', f.target)):
            altered = copy.deepcopy(binding)
            altered['revision_entry']['context'][field] = value
            with self.subTest(field=field), self.assertRaises(admission.AdmissionRefusal):
                execution.validate_worktree(f.wt, altered)
        changed = copy.deepcopy(envelope)
        changed['execution']['task'] += ' substitute'
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'revision.entry.instructions'):
            execution.revision_context(changed, ref(path), binding['revision_entry']['context']['envelope_sha256'])

    def test_successor_requires_exact_attempt_history_and_native_custody(self):
        f = self.f
        _, _, binding, _ = f.entry()
        entry = binding['revision_entry']['context']
        prior = {'session_id': 'original-session', 'attempt_id': 'attempt-0', 'status': 'failed', 'error': 'changes requested: exact target'}
        entry['prior_attempts'] = [prior]
        current = {'session_id': 'successor-session', 'attempt_id': 'attempt-1', 'status': 'running'}
        stage = {'attempts': [prior, current]}
        custody = f.custody(entry)
        stage['extra'] = {'request_changes_requeued': {'binding': custody, 'review': f.review(stage)}}
        execution.validate_revision_successor(binding, stage, 'successor-session', f.wt)
        for key in custody:
            changed = copy.deepcopy(stage)
            changed['extra']['request_changes_requeued']['binding'][key] = 'foreign'
            with self.subTest(custody=key), self.assertRaisesRegex(admission.AdmissionRefusal, 'revision.entry.custody'):
                execution.validate_revision_successor(binding, changed, 'successor-session', f.wt)
        for index, key in ((0, 'session_id'), (1, 'session_id'), (0, 'attempt_id')):
            changed = copy.deepcopy(stage)
            changed['attempts'][index][key] = 'foreign'
            with self.subTest(index=index, key=key), self.assertRaisesRegex(admission.AdmissionRefusal, 'revision.entry.successor'):
                execution.validate_revision_successor(binding, changed, 'successor-session', f.wt)
        changed = copy.deepcopy(stage)
        changed['attempts'][-1]['attempt_id'] = 'attempt-0'
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'revision.entry.successor'):
            execution.validate_revision_successor(binding, changed, 'successor-session', f.wt)

    def test_custody_uses_original_envelope_carrier_and_exact_selected_identity(self):
        f = self.f
        binding = {**f.envelope, 'contract': f.contract, 'issue_body': f.issue['body']}
        stage = {'status': 'review', 'attempts': [],
                 'prompt': json.dumps(execution.projection(binding, sha(f.original), 'supervised'))}
        owner = {'state': {'orders': {f.selection['order_id']: {'stages': [stage]}}}}
        terminal = {'session_id': 'original-session', 'message': {'outcome': 'completed', 'blocking': False}}
        state = {'phase': 'execution', 'issue': {'number': 18}, 'envelope_sha256': sha(f.original),
                 'authorization_sha256': 'a' * 64, 'admission_sha256': 'b' * 64, 'noodle_start': {'status': 'started'}}
        paths = {key: f.directory / key for key in ('landing', 'claim', 'acceptance')}
        paths['envelope'] = f.original
        stale = {**f.auth, 'noodle': {'path': '/prior/bootstrap/noodle', 'sha256': 'c' * 64}}
        def stopped(authorization, checkpoint):
            self.assertEqual(authorization['noodle'], f.envelope['execution']['carrier']['noodle'])
            return 'stopped'
        with patch.object(execution, 'read_owner', return_value=owner), \
                patch.object(execution, 'blocked_outcome', return_value=terminal), \
                patch.object(execution, 'quiescent_order'), \
                patch.object(atom, 'observe_prior_loop', side_effect=stopped):
            result = atom.scope_custody(stale, state, paths, f.selection)
            self.assertEqual(result['blocked']['message']['outcome'], 'completed')
            for key in ('order_id', 'terminal_session', 'candidate_tree'):
                with self.subTest(key=key), self.assertRaisesRegex(atom.AtomRefusal, 'revision.custody'):
                    atom.scope_custody(stale, state, paths, {**f.selection, key: 'foreign'})
            with self.assertRaisesRegex(atom.AtomRefusal, 'scope.original_binding'):
                atom.scope_custody({**stale, 'repository': 'foreign/repository'}, state, paths, f.selection)
            with self.assertRaisesRegex(atom.AtomRefusal, 'scope.writes'):
                atom.scope_custody(stale, {**state, 'writes': {'issue_scope': {'status': 'offered'}}}, paths, f.selection)

    def test_completed_terminal_is_not_relabelled_blocked(self):
        from test_scope_amendment import ScopeAmendmentTests
        fixture = ScopeAmendmentTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        owner, events, event = fixture.blocked_fixture()
        event['payload'].update(outcome='completed', blocking=False)
        events.write_text(json.dumps(event) + '\n')
        self.assertIsNone(execution.blocked_outcome(fixture.envelope, owner))
        receipt = execution.blocked_outcome(fixture.envelope, owner, completed=True)
        self.assertEqual(receipt['message']['outcome'], 'completed')
        self.assertFalse(receipt['message']['blocking'])
        event['payload']['blocking'] = True
        events.write_text(json.dumps(event) + '\n')
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'blocked.blocking'):
            execution.blocked_outcome(fixture.envelope, owner, completed=True)

    def test_producer_seals_entry_and_readback_rejects_changed_bytes(self):
        f = self.f
        issue, envelope, binding, path = f.entry()
        entry = json.loads(path.read_text())
        entry.pop('envelope_sha256')
        selected = f.directory / 'selected-runtime'
        selected.mkdir()
        for name in supervisor.BUNDLE_PATHS:
            (selected / name).write_bytes((Path(__file__).resolve().parents[1] / name).read_bytes())
        output = f.directory / 'new-admission'
        carrier = copy.deepcopy(envelope['execution']['carrier'])
        carrier['codex']['argv'] = ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture']
        # The carrier is separately checked by the real native fixture.
        with patch.object(supervisor, 'validate_carrier'):
            result = supervisor.prepare(issue, carrier, f.root, output,
                environ={'NOODLES_TOKEN_COMMAND': 'printf fixture'}, wire_host=True,
                correction=True, runtime_root=selected, revision_entry=entry)
            self.assertEqual(json.loads((output / 'envelope.json').read_text())['execution']['source_head'], f.base)
            self.assertIn('revision-entry.json', (output / 'provider/codex').read_text())
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertIn({'path': 'revision-entry.json', 'sha256': sha(output / 'revision-entry.json')}, manifest['runtime'])
            again = supervisor.prepare(issue, carrier, f.root, output, environ={}, wire_host=True,
                correction=True, runtime_root=selected, revision_entry=entry, readback=True)
            self.assertEqual(result, again)
            (output / 'revision-entry.json').write_text('{}')
            with self.assertRaisesRegex(admission.AdmissionRefusal, 'scope.prepared.component'):
                supervisor.prepare(issue, carrier, f.root, output, environ={}, wire_host=True,
                    correction=True, runtime_root=selected, revision_entry=entry, readback=True)


    def test_revision_owner_reads_each_intent_without_repeating_effects(self):
        f = self.f
        selection = f.selection
        original = f.envelope
        terminal_path = f.save('terminal-events.json', {'completed': True})
        terminal = {'session_id': 'original-session', 'attempt_id': 'attempt-0',
                    'source': ref(terminal_path), 'message': {'outcome': 'completed', 'blocking': False}}
        attempt = {'attempt_id': 'attempt-0', 'session_id': 'original-session', 'status': 'completed', 'worktree_name': f.wt.name}
        stage = {'task_key': 'execute', 'skill': 'execute', 'provider': 'codex', 'model': 'fixture', 'runtime': 'process',
                 'status': 'review', 'attempts': [attempt], 'prompt': '{}'}
        order = selection['order_id']
        owner = {'state': {'orders': {order: {'stages': [copy.deepcopy(stage)], 'status': 'active', 'plan': []}}, 'pending_reviews': {order: f.review(stage)},
                           'mode': 'manual', 'mode_epoch': 1}}
        expected_attempts = [{**attempt, 'status': 'failed', 'error': 'changes requested: ' + selection['reason']}]
        custody = f.custody({'prior_attempts': expected_attempts})
        runtime = f.root / '.noodle'
        runtime.mkdir(exist_ok=True)
        (runtime / 'control-ack.ndjson').write_text('')
        output = f.directory / 'amendment'
        output.mkdir()
        selected = f.directory / 'selected-runtime'
        selected.mkdir()
        for name in supervisor.BUNDLE_PATHS:
            (selected / name).write_bytes((Path(__file__).resolve().parents[1] / name).read_bytes())
        selection['lifecycle_owner'] = {'path': str(selected / 'issue-atom')}
        packet = {'selection': selection, 'output': str(output)}
        effective = {**f.auth, 'base_head': f.target, 'noodle': admission.load_revision_native(selection['native_acceptance'], f.root),
                     'issue': {**f.issue, 'body': atom.revision_body(f.auth, selection)}}
        paths = {'state': f.directory / 'checkpoint.json', 'envelope': f.original}
        state = {'phase': 'execution', 'issue': {'number': 18}, 'publication': None, 'writes': {},
                 'noodle_start': {'prior': True}, 'repair': {'history': ['retained']},
                 'scope_amendment': {'selection': {'sha256': 'a' * 64}, 'prior': {
                     'envelope': ref(f.original), 'stage': stage, 'blocked': terminal, 'noodle_start': {'prior': True}}}}
        before_authority = copy.deepcopy(f.auth)
        provider = Mock()
        current_issue = copy.deepcopy(f.issue)
        provider.issue.side_effect = lambda _: copy.deepcopy(current_issue)
        provider.repository_info.return_value = {'full_name': 'ed3c/soodles', 'default_branch': 'main'}
        provider.branch_info.return_value = {'name': 'main', 'commit': {'sha': f.target}}
        def update(number, value):
            self.assertEqual(number, 18)
            current_issue['body'] = value
            raise atom.MutationUnknown('response lost after exact Issue patch')
        provider.update_issue_body.side_effect = update
        def project(*args):
            return effective, {**paths, 'envelope': output / 'admission/envelope.json'}
        def start(*args, **kwargs):
            state['scope_amendment'].update(restart_offered=True, ack_prefix='')
            state['noodle_start'] = {'status': 'started', 'config_sha256': 'fixture'}
            return {'action': 'running'}
        from contextlib import ExitStack
        with ExitStack() as stack:
            for target, name, value in (
                (atom, 'scope_packet', {'return_value': packet}),
                (atom, 'scope_projection', {'side_effect': project}),
                (atom, 'resumed_lifecycle', {'return_value': {'lifecycle_owner': selection['lifecycle_owner']}}),
                (atom, 'validate_lifecycle_owner', {'return_value': selected / 'issue-atom'}),
                (atom, 'observe_prior_loop', {'side_effect': lambda a,s: 'running' if s['noodle_start'].get('status') == 'started' else 'stopped'}),
                (execution, 'read_owner', {'return_value': owner}),
                (execution, 'blocked_outcome', {'return_value': terminal}),
                (supervisor, 'validate_carrier', {}),
                (atom, 'ensure_noodle', {'side_effect': start}),
                (atom, 'host_config_identity', {'return_value': 'fixture'}),
                (atom, 'noodle_process_argv', {'return_value': ['native', '--mode', 'manual']})):
                stack.enter_context(patch.object(target, name, **value))
            advance = lambda: atom.advance_scope_amendment(f.auth, paths, state, provider, {'NOODLES_TOKEN_COMMAND': 'printf fixture'})
            self.assertEqual(advance()['action'], 'scope_issue_readback_pending')
            self.assertEqual(state['writes']['issue_scope']['before_body'], f.issue['body'])
            self.assertEqual(advance()['action'], 'scope_admission_prepared')
            self.assertEqual(advance()['action'], 'running')
            for action in ('request-changes', 'edit-item', 'requeue', 'mode'):
                result = advance()
                self.assertTrue(result['action'].endswith('pending'), result)
                mailbox = runtime / 'control.ndjson'
                raw = mailbox.read_bytes()
                self.assertEqual(advance(), result)
                self.assertEqual(mailbox.read_bytes(), raw)
                command = json.loads(raw)
                self.assertEqual(command['action'], action)
                current = owner['state']['orders'][order]['stages'][0]
                if action == 'request-changes':
                    current.update(status='failed', attempts=[{**attempt, 'status': 'failed', 'error': 'changes requested: ' + selection['reason']}],
                        extra={'request_changes_recovery': custody})
                    owner['state']['orders'][order]['status'] = 'failed'
                elif action == 'edit-item':
                    current['prompt'] = command['prompt']
                    owner['state']['pending_reviews'][order]['prompt'] = command['prompt']
                elif action == 'requeue':
                    current['status'] = 'pending'
                    current['extra'] = {'request_changes_requeued': {'binding': custody, 'review': copy.deepcopy(owner['state']['pending_reviews'][order])}}
                    owner['state']['orders'][order]['status'] = 'active'
                    owner['state']['pending_reviews'] = {}
                else:
                    owner['state'].update(mode='supervised', mode_epoch=2)
                mailbox.write_text('')
                with (runtime / 'control-ack.ndjson').open('a') as stream:
                    stream.write(json.dumps({'id': command['id'], 'action': action, 'status': 'ok'}) + '\n')
            self.assertEqual(advance()['action'], 'scope_released')
        provider.update_issue_body.assert_called_once()
        self.assertEqual(f.auth, before_authority)
        self.assertEqual(state['repair'], {'history': ['retained']})
        self.assertEqual(state['scope_amendment']['prior']['blocked']['message']['outcome'], 'completed')


def native_successor(root):
    import os
    import sys
    bundle = Path(os.environ['SOODLES_ADMISSION_LAUNCHER']).parent
    entry = json.loads((bundle / 'revision-entry.json').read_text())
    git = lambda *args: subprocess.check_output(['git', *args], text=True, stderr=subprocess.PIPE).strip()
    observed = {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                'residue': git('status', '--porcelain=v1', '--untracked-files=all'),
                'session': os.environ['NOODLE_SESSION_ID'], 'entry': entry}
    (root / 'revision-successor.json').write_text(json.dumps(observed))
    assert observed['head'] == entry['candidate_head'] and observed['tree'] == entry['candidate_tree']
    assert observed['residue'] == ''
    git('merge', '--no-edit', entry['target_base'])
    result = subprocess.run([str(bundle / 'launcher'), 'stage-outcome', 'completed',
        'Integrated the exact target in the original disposable candidate.'], capture_output=True, text=True, timeout=30)
    (root / 'revision-outcome.json').write_text(json.dumps({'returncode': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr}))
    assert result.returncode == 0, result.stdout + result.stderr
    print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 0, 'output_tokens': 0}}), flush=True)


def native_review_continuation(root, project, wt, original_bundle, selected, issue, carrier, env):
    import fcntl
    import os
    import signal
    import time
    runtime = project / '.noodle'
    binary = carrier['noodle']['path']
    log = root / 'revision-commands.ndjson'
    process = None
    def git(*args, cwd=project):
        return subprocess.check_output(['git', *map(str, args)], cwd=cwd, env=env, text=True, stderr=subprocess.PIPE).strip()
    def snapshot():
        return json.loads((runtime / 'state.snapshot.json').read_text())['state']
    def wait(predicate, label):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            if process is not None and process.poll() is not None:
                raise AssertionError('revision loop exited: ' + (root / 'revision-daemon.stderr').read_text())
            time.sleep(.05)
        raise AssertionError('timeout: ' + label)
    def control(command):
        with (runtime / 'control.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with (runtime / 'control.ndjson').open('a') as stream:
                stream.write(json.dumps(command) + '\n')
        def ack():
            path = runtime / 'control-ack.ndjson'
            return next((json.loads(line) for line in path.read_text().splitlines()
                         if json.loads(line).get('id') == command['id']), None) if path.exists() else None
        result = wait(ack, command['id'])
        with log.open('a') as stream:
            stream.write(json.dumps({'command': command, 'ack': result, 'state': snapshot()}) + '\n')
        assert result['status'] == 'ok', result
    original = json.loads((original_bundle / 'envelope.json').read_text())
    order = original['execution']['order_id']
    old_stage = copy.deepcopy(snapshot()['orders'][order]['stages'][0])
    terminal = execution.blocked_outcome(original, execution.read_owner(original), completed=True)
    assert terminal['message']['outcome'] == 'completed' and terminal['message']['blocking'] is False
    retained_head = git('rev-parse', 'HEAD', cwd=wt)
    retained_tree = git('rev-parse', 'HEAD^{tree}', cwd=wt)
    assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=wt) == ''
    (project / 'target.txt').write_text('exact new base\n')
    git('add', 'target.txt'); git('commit', '-m', 'Advance disposable provider base')
    target = git('rev-parse', 'HEAD')
    git('update-ref', 'refs/remotes/origin/main', target)
    accepted_path = Path(env['FIXTURE_NATIVE_ACCEPTED'])
    accepted = json.loads(accepted_path.read_text())
    assert accepted['binary'] == carrier['noodle']
    reason = 'Integrate selected disposable target.'
    attempts = old_stage['attempts']
    entry = {'schema': 1, 'kind': 'base_advance', 'original_envelope': ref(original_bundle / 'envelope.json'),
        'selection_sha256': 'd' * 64, 'candidate_head': retained_head, 'candidate_tree': retained_tree,
        'old_base': original['base_head'], 'target_base': target, 'terminal': terminal,
        'native_acceptance': ref(accepted_path),
        'prior_attempts': [*attempts[:-1], {**attempts[-1], 'status': 'failed', 'error': 'changes requested: ' + reason}],
        **{key: original['execution'][key] for key in ('order_id', 'stage_index', 'worktree')}}
    contract = admission.parse_contract(issue['body'])
    contract['base_head'] = target
    for pin in contract['frozen_paths']:
        if pin['revision'] == 'base':
            pin['sha256'] = hashlib.sha256(admission.git_bytes(project, target, pin['path'])).hexdigest()
    issue = {**issue, 'body': body(contract), 'updated_at': '2026-10-03T01:00:00Z'}
    (root / 'issue-readback.json').write_text(json.dumps(issue))
    code = root / 'fixture-code'
    code.mkdir()
    source = Path(__file__).resolve().parents[1]
    for name in ('test_admission_revision.py', 'test_issue_admission.py'):
        (code / name).write_bytes((source / 'tests' / name).read_bytes())
    # The process spy imports current control helpers, never a model or provider client.
    env['PYTHONPATH'] = str(code) + os.pathsep + str(source)
    bundle = root / 'revision-bundle'
    receipt = supervisor.prepare(issue, carrier, project, bundle, environ=env, wire_host=True,
        correction=True, runtime_root=selected, revision_entry=entry)
    new_envelope = json.loads((bundle / 'envelope.json').read_text())
    assert new_envelope['execution']['source_head'] == original['execution']['source_head']
    assert new_envelope['execution']['instruction_context'] == original['execution']['instruction_context']
    binding = execution.revision_context(admission.validate_issue(issue, new_envelope),
                                        ref(bundle / 'revision-entry.json'), sha(bundle / 'envelope.json'))
    (project / '.noodle.toml').write_bytes((bundle / 'noodle.toml').read_bytes())
    env['SOODLES_ADMISSION_LAUNCHER'] = str(bundle / 'launcher')
    stdout = (root / 'revision-daemon.stdout').open('w')
    stderr = (root / 'revision-daemon.stderr').open('w')
    before = (root / 'sentinel.ndjson').read_bytes()
    try:
        process = subprocess.Popen(receipt['next']['argv'], env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        wait(lambda: (runtime / 'status.json').exists(), 'held native loop')
        control({'id': 'revision-request', 'action': 'request-changes', 'order_id': order, 'prompt': reason})
        stage = snapshot()['orders'][order]['stages'][0]
        assert stage['attempts'] == entry['prior_attempts'], (stage['attempts'], entry['prior_attempts'])
        assert 'interrupted_execution' not in stage['extra']
        assert len(stage['extra']['interrupted_execution_history']) == 1
        assert stage['extra']['request_changes_recovery']['candidate_head'] == retained_head
        assert (root / 'sentinel.ndjson').read_bytes() == before
        prompt = json.dumps(execution.projection(binding, sha(bundle / 'envelope.json'), 'supervised'), sort_keys=True)
        control({'id': 'revision-edit', 'action': 'edit-item', 'order_id': order, 'prompt': prompt})
        control({'id': 'revision-requeue', 'action': 'requeue', 'order_id': order})
        assert snapshot()['orders'][order]['stages'][0]['status'] == 'pending'
        assert (root / 'sentinel.ndjson').read_bytes() == before
        control({'id': 'revision-release', 'action': 'mode', 'value': 'supervised'})
        wait(lambda: (root / 'revision-outcome.json').exists(), 'revision completed outcome')
        outcome = json.loads((root / 'revision-outcome.json').read_text())
        assert outcome['returncode'] == 0, outcome
        control({'id': 'revision-hold', 'action': 'mode', 'value': 'manual'})
        wait(lambda: snapshot()['orders'][order]['stages'][0]['status'] == 'review', 'successor terminal')
        stage = snapshot()['orders'][order]['stages'][0]
        assert len(stage['extra']['interrupted_execution_history']) == 1
        assert len(stage['attempts']) == len(attempts) + 1
        assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=wt) == ''
        git('merge-base', '--is-ancestor', target, 'HEAD', cwd=wt)
        assert sha(terminal['source']['path']) == terminal['source']['sha256']
        return {'status': 'passed', 'retained_head': retained_head, 'target_base': target,
                'final_head': git('rev-parse', 'HEAD', cwd=wt), 'interruption_history_count': 1,
                'pre_release_dispatches': 0, 'successor_count': 1, 'dirty_exception': False,
                'original_instruction_context_preserved': True}
    finally:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
        stdout.close(); stderr.close()


def run_native(accepted_path, output):
    import os
    from test_interruption_recovery import native_control
    accepted = json.loads(Path(accepted_path).read_text())
    for key in ('binary', 'acceptance', 'interface'):
        assert sha(accepted[key]['path']) == accepted[key]['sha256']
    with patch.dict(os.environ, {'FIXTURE_NATIVE_ACCEPTED': str(Path(accepted_path).resolve())}):
        return native_control(output, accepted['binary']['path'], accepted['binary']['sha256'],
                              adapter=True, completed_review=native_review_continuation)


def external_reader_control(reader_path, expected_sha256, output):
    import sys
    reader = Path(reader_path).resolve()
    assert sha(reader) == expected_sha256
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    f = RevisionFixture()
    results = {}
    try:
        selected = f.criteria(True)
        issue = {**f.issue, 'body': atom.revision_body(f.auth, selected)}
        envelope = {**f.envelope, 'base_head': f.target, 'body_sha256': admission.body_digest(issue['body'])}
        script = '''import json,sys
sys.path.insert(0,sys.argv[1])
import issue_admission as judge
v=json.load(open(sys.argv[2]))
try:
 b=judge.validate_issue(v['issue'],v['envelope'])
 r=judge.verify_candidate(v['root'],b['base_head'],v['head'],v['issue'])
 print(json.dumps({'status':'accepted','result':r,'source_head':b['execution']['source_head'],'instruction_context':b['execution']['instruction_context']}))
except judge.AdmissionRefusal as e:
 print(json.dumps({'status':'refused','invalid':e.invalid}))
'''
        def check(name, expected):
            subject = {'issue': issue, 'envelope': envelope, 'root': str(f.wt), 'head': f.git('rev-parse', 'HEAD', cwd=f.wt)}
            path = output / (name + '-input.json')
            path.write_text(json.dumps(subject))
            result = subprocess.run([sys.executable, '-B', '-c', script, str(reader.parent), str(path)],
                                    capture_output=True, text=True, cwd=output, timeout=30)
            (output / (name + '-process.json')).write_text(json.dumps({'argv': result.args, 'returncode': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}))
            assert result.returncode == 0, result.stderr
            results[name] = json.loads(result.stdout)
            assert results[name]['status'] == expected, results[name]
        check('unintegrated_target', 'refused')
        f.git('merge', '--no-edit', f.target, cwd=f.wt)
        manifest = {'schema': 1, 'issue': {'repository': 'ed3c/soodles', 'number': 18},
            'instructions': [{'path': 'allowed.py',
                'baseline_sha256': hashlib.sha256(admission.git_bytes(f.root, f.target, 'allowed.py')).hexdigest(),
                'treatment_sha256': sha(f.wt / 'allowed.py')}], 'artifacts': [],
            'owner': {'name': 'Soodles Issue admission', 'tool': 'issue_admission.validate_delivery_paths',
                      'authorization': 'ed3c/soodles#18'}, 'authorizes_landing': False}
        (f.wt / 'manifest.json').write_text(json.dumps(manifest))
        positive = f.commit(f.wt)
        check('integrated_original_instructions', 'accepted')
        assert results['integrated_original_instructions']['source_head'] == f.base
        assert results['integrated_original_instructions']['instruction_context'] == f.envelope['execution']['instruction_context']
        (f.wt / 'manifest.json').unlink(); f.commit(f.wt)
        check('missing_manifest', 'refused')
        manifest['instructions'][0]['treatment_sha256'] = '0' * 64
        (f.wt / 'manifest.json').write_text(json.dumps(manifest)); f.commit(f.wt)
        check('wrong_digest', 'refused')
        envelope = copy.deepcopy(envelope)
        envelope['execution']['source_head'] = positive
        check('replaced_instruction_source', 'refused')
        (output / 'results.json').write_text(json.dumps({'reader': ref(reader), 'cases': results,
            'authorizes_landing': False, 'scope': 'Fixed external reader on disposable objects; no live effects.'}, indent=2))
        return results
    finally:
        f.temp.cleanup()
