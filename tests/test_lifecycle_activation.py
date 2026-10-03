"""External lifecycle activation: selection is not candidate self-authorization."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import issue_atom as atom
import supervisor_admission as admission
import test_supervisor_authorization as authorization_tests


class LifecycleActivationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = authorization_tests.AuthorizationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.runtime = self.fixture.fixture.outer / 'selected-lifecycle'
        self.runtime.mkdir()
        expected_files = {"issue-atom", "soodles", "soodles.py", "issue_atom.py",
            "supervisor_admission.py", "issue_admission.py", "issue_execution.py",
            "candidate_publication.py", "provider_credential.py", "provider_transport.py",
            "repository_binding.py", "dependency_binding.py", "github_reader.py",
            "landing.py", "policy/runtime.lock.json", "atom_repair.py",
            "policy/repair-policy.json", "provider_readback.py", "system_context.py",
            "contracts/system-v1/routes.json", "contracts/system-v1/common.md",
            "contracts/system-v1/issue-atom.md", "contracts/system-v1/candidate.md",
            "contracts/system-v1/readback.md", "provider-readback",
            "schema_manager.py", "policy/host-finalization.json", "cost_telemetry.py", "test_manager.py"}
        self.assertEqual(set(atom.LIFECYCLE_FILES), expected_files)
        for name in expected_files:
            destination = self.runtime / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(atom.__file__).parent / name, destination)
        hashes = {name: atom.digest_file(self.runtime / name) for name in atom.LIFECYCLE_FILES}
        self.spec = {'path': str(self.runtime / 'issue-atom'),
                     'sha256': hashes['issue-atom'],
                     'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True,
                                                    separators=(',', ':')).encode())}
        self.fixture.selection['lifecycle_owner'] = self.spec
        self.fixture.path.write_text(json.dumps(self.fixture.selection))
        self.fixture.digest = atom.digest_file(self.fixture.path)

    def test_legacy_descriptor_keeps_exact_closure_but_current_import_is_required(self):
        (self.runtime / "cost_telemetry.py").unlink()
        with self.assertRaisesRegex(atom.AtomRefusal, "lifecycle_owner.file"):
            atom.validate_lifecycle_owner({"control_root": str(self.fixture.fixture.root),
                "landing_owner": self.fixture.selection["landing_owner"], "lifecycle_owner": self.spec})
        # Minimal legacy source fixture tests descriptor compatibility, not a
        # historical implementation replay or selected execution authority.
        (self.runtime / "issue_atom.py").write_text("# legacy owner without telemetry import\n")
        hashes = {name: atom.digest_file(self.runtime / name)
                  for name in atom.LIFECYCLE_FILES if name != "cost_telemetry.py"}
        spec = {**self.spec, "source_sha256": atom.digest_bytes(json.dumps(
            hashes, sort_keys=True, separators=(",", ":")).encode())}
        auth = {"control_root": str(self.fixture.fixture.root),
                "landing_owner": self.fixture.selection["landing_owner"], "lifecycle_owner": spec}
        self.assertEqual(atom.validate_lifecycle_owner(auth), self.runtime / "issue-atom")
        (self.runtime / "schema_manager.py").write_text("changed")
        with self.assertRaisesRegex(atom.AtomRefusal, "source_sha256"):
            atom.validate_lifecycle_owner(auth)

    def test_prepared_continuation_and_resume_keep_exact_external_owner(self):
        receipt = self.fixture.run_authorize()
        self.assertEqual(receipt['next']['argv'][0], self.spec['path'])
        auth = atom.read_json(receipt['authorization']['path'], 'authorization')
        self.assertEqual(auth['lifecycle_owner'], self.spec)
        self.assertEqual(auth['landing_owner'], self.fixture.selection['landing_owner'])
        # Provenance readback remains possible without present runtime bytes.
        (self.runtime / 'issue_atom.py').unlink()
        self.assertEqual(receipt, self.fixture.run_authorize())
        with self.assertRaises(atom.AtomRefusal):
            atom.validate_authorization(receipt['authorization']['path'], receipt['authorization']['sha256'])

    def test_unselected_process_refuses_before_any_effect(self):
        receipt = self.fixture.run_authorize()
        with patch.object(atom, '_run_owned', side_effect=AssertionError('effect')):
            with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.execution'):
                atom.run(receipt['authorization']['path'], environ=receipt['next']['environment'])
        self.assertFalse((self.fixture.fixture.root / '.noodle').exists())

    def test_transitive_byte_drift_refuses_before_publication(self):
        (self.runtime / 'issue_execution.py').write_text('# different source\n')
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.source_sha256'):
            self.fixture.run_authorize()
        self.assertFalse(self.fixture.output.exists())

    def test_selected_runtime_can_validate_its_own_execution_identity(self):
        receipt = self.fixture.run_authorize()
        script = ('import issue_atom,sys; a,d=issue_atom.validate_authorization(sys.argv[1],sys.argv[2]); '
                  'issue_atom.validate_lifecycle_owner(a, executing=True); '
                  'print(issue_atom.same_command(sys.argv[1])[0])')
        process = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys;sys.path.insert(0,sys.argv.pop(1));' + script,
            str(self.runtime), receipt['authorization']['path'], receipt['authorization']['sha256']],
            capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.strip(), self.spec['path'])

    def test_candidate_or_symlink_owner_is_not_an_external_snapshot(self):
        spec = dict(self.spec)
        spec['path'] = str(self.fixture.fixture.root / 'issue-atom')
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.path'):
            atom.validate_lifecycle_owner({**self.fixture.fixture.authorization, 'lifecycle_owner': spec})
        target = self.runtime / 'provider_credential.py'
        raw = target.read_bytes()
        other = self.runtime.parent / 'credential-copy.py'
        other.write_bytes(raw)
        target.unlink()
        target.symlink_to(other)
        with self.assertRaisesRegex(atom.AtomRefusal, 'lifecycle_owner.file'):
            self.fixture.run_authorize()

    def selected_copy(self, name):
        root = self.runtime.parent / name
        for entry in atom.LIFECYCLE_FILES:
            target = root / entry
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.runtime / entry, target)
        source = root / 'issue_atom.py'
        source.write_text(source.read_text() + '\n# selected ' + name + '\n')
        hashes = {entry: atom.digest_file(root / entry) for entry in atom.LIFECYCLE_FILES}
        return root, {'path': str(root / 'issue-atom'), 'sha256': hashes['issue-atom'],
                      'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True,
                                                                  separators=(',', ':')).encode())}

    def resumed_repair_fixture(self):
        from system_context import compile_repair
        receipt = self.fixture.run_authorize()
        path = Path(receipt['authorization']['path'])
        auth = atom.read_json(path, 'authorization')
        digest = receipt['authorization']['sha256']
        root, selected = self.selected_copy('repair-resume')
        policy = atom.atom_repair.load((self.runtime / atom.atom_repair.POLICY_PATH).read_bytes())
        history = atom.atom_repair.new_history(digest,
            atom.repair_binding(auth, policy, source_root=self.runtime), policy,
            context=compile_repair(self.runtime))
        history['used'].update(readback=1, actions=1)
        history['started'] = history['last_time']
        history['history'] = [{'signal': 'stale_pr', 'action': 'readback',
                               'status': 'confirmed', 'evidence': 'c' * 64}]
        state = {'schema_version': 1, 'authorization_sha256': digest, 'phase': 'landing',
                 'repair': history, 'lifecycle_resume': {
                     'from': self.spec, 'to': selected, 'authorization_sha256': digest}}
        return path, auth, state, root, selected

    def test_postwrite_resume_validates_original_repair_without_transferring_effects(self):
        path, auth, state, root, _ = self.resumed_repair_fixture()
        before = copy.deepcopy(state)
        with patch.object(atom, '__file__', str(root / 'issue_atom.py')), \
                patch.object(atom, 'postwrite_lifecycle') as postwrite:
            controller = atom.repair_controller(auth, state, atom.artifact_paths(path), authorization_path=path)
            with self.assertRaisesRegex(atom.atom_repair.RepairRefusal, 'preserves_original_repair_authority'):
                controller.perform('missing_projection', lambda _: self.fail('new repair effect'), lambda _: True)
        postwrite.assert_called_once_with(auth, state, atom.artifact_paths(path), allow_resolved=True)
        self.assertEqual(state, before)
        self.assertEqual(state['repair']['used']['readback'], 1)

    def test_explicit_original_closure_does_not_follow_new_runtime_file_list(self):
        path, auth, state, root, _ = self.resumed_repair_fixture()
        before = copy.deepcopy(state)
        with patch.object(atom, 'LIFECYCLE_FILES', ('new-runtime-only.py',)), \
                patch.object(atom, '__file__', str(root / 'issue_atom.py')), patch.object(atom, 'postwrite_lifecycle'):
            controller = atom.resumed_repair_controller(auth, state, atom.artifact_paths(path), path)
        self.assertEqual(controller.binding, state['repair']['binding'])
        self.assertEqual(state, before)

    def test_postwrite_resume_refuses_foreign_binding_lineage_limits_and_unknown_effects(self):
        path, auth, state, root, _ = self.resumed_repair_fixture()
        original = copy.deepcopy(state['repair'])
        for field, value in (('binding', 'f' * 64), ('lineage', 'f' * 64),
                             ('limits', {**original['limits'], 'model': 2}),
                             ('intent', None), ('failed', None)):
            with self.subTest(field=field):
                state['repair'] = copy.deepcopy(original)
                if field in {'intent', 'failed'}:
                    state['repair']['history'][0]['status'] = field
                else:
                    state['repair'][field] = value
                before = copy.deepcopy(state)
                with patch.object(atom, '__file__', str(root / 'issue_atom.py')), \
                        patch.object(atom, 'postwrite_lifecycle'):
                    with self.assertRaises((atom.AtomRefusal, atom.atom_repair.RepairRefusal)):
                        atom.repair_controller(auth, state, atom.artifact_paths(path), authorization_path=path)
                self.assertEqual(state, before)

    def test_legacy_postwrite_without_repair_history_does_not_create_one(self):
        path, auth, state, root, _ = self.resumed_repair_fixture()
        del state['repair']
        del auth['lifecycle_owner']
        path.write_text(json.dumps(auth))
        state['authorization_sha256'] = atom.digest_file(path)
        state['lifecycle_resume']['from'] = None
        state['lifecycle_resume']['authorization_sha256'] = state['authorization_sha256']
        with patch.object(atom, '__file__', str(root / 'issue_atom.py')), \
                patch.object(atom, 'postwrite_lifecycle'):
            controller = atom.repair_controller(auth, state, atom.artifact_paths(path), authorization_path=path)
        self.assertIsNotNone(controller.disabled)
        self.assertNotIn('repair', state)

    def test_implicit_original_git_source_survives_control_drift_and_new_closure(self):
        from system_context import compile_repair
        path, auth, state, root, _ = self.resumed_repair_fixture()
        control = Path(auth['control_root'])
        for name in atom.LIFECYCLE_FILES:
            destination = control / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.runtime / name, destination)
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=control, text=True, stderr=subprocess.PIPE).strip()
        git('add', *atom.LIFECYCLE_FILES)
        git('-c', 'user.name=Fixture', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'pin original repair source')
        auth.pop('lifecycle_owner')
        auth['base_head'] = git('rev-parse', 'HEAD')
        path.write_text(json.dumps(auth))
        digest = atom.digest_file(path)
        policy = atom.atom_repair.load((control / atom.atom_repair.POLICY_PATH).read_bytes())
        history = state['repair']
        history.update(lineage=digest, binding=atom.repair_binding(auth, policy, source_root=control),
                       context=compile_repair(control))
        state['authorization_sha256'] = digest
        state['lifecycle_resume'].update({'from': None, 'authorization_sha256': digest})
        before = copy.deepcopy(state)
        (control / 'supervisor_admission.py').write_text('control source advanced\n')
        with patch.object(atom, 'LIFECYCLE_FILES', ('new-runtime-only.py',)):
            self.assertEqual(atom.original_repair_source(auth)[2], history['binding'])
        with patch.object(atom, '__file__', str(root / 'issue_atom.py')), \
                patch.object(atom, 'postwrite_lifecycle'):
            controller = atom.resumed_repair_controller(auth, state, atom.artifact_paths(path), path)
        self.assertEqual(controller.binding, history['binding'])
        self.assertEqual(state, before)
        original_base = auth['base_head']
        for bad in ('f' * 40, git('hash-object', 'supervisor_admission.py')):
            auth['base_head'] = bad
            with self.assertRaises(atom.AtomRefusal):
                atom.original_repair_source(auth)
        auth['base_head'] = original_base
        for field in ('binding', 'context', 'policy'):
            state['repair'] = copy.deepcopy(before['repair'])
            state['repair'][field] = {} if field == 'context' else 'f' * 64
            with patch.object(atom, '__file__', str(root / 'issue_atom.py')), patch.object(atom, 'postwrite_lifecycle'):
                with self.assertRaises(atom.atom_repair.RepairRefusal):
                    atom.resumed_repair_controller(auth, state, atom.artifact_paths(path), path)

    def test_second_resume_persists_previous_selection_without_repair_or_projection_reset(self):
        path, auth, state, _, first = self.resumed_repair_fixture()
        root, second = self.selected_copy('second-selected-runtime')
        descriptor = root.parent / 'second-selection.json'
        descriptor.write_text(json.dumps(second))
        paths = atom.artifact_paths(path)
        atom.save_json(paths['state'], state)
        before = copy.deepcopy(state)
        auth_bytes = path.read_bytes()
        runtime = Path(auth['control_root']) / '.noodle'
        runtime.mkdir(exist_ok=True)
        owner = {'state': {'orders': {}}}
        with patch.object(atom, '__file__', str(root / 'issue_atom.py')), \
                patch.object(atom, 'postwrite_lifecycle', return_value=({'execution': {}}, owner)), \
                patch.object(atom.issue_execution, 'read_owner', return_value=owner):
            result = atom.resume(path, str(descriptor), atom.digest_file(descriptor),
                environ={'SOODLES_AUTHORIZATION_SHA256': state['authorization_sha256']})
            once = paths['state'].read_bytes()
            atom.resume(path, str(descriptor), atom.digest_file(descriptor),
                environ={'SOODLES_AUTHORIZATION_SHA256': state['authorization_sha256']})
        saved = atom.read_json(paths['state'], 'state')
        self.assertEqual(result['status'], 'resumed')
        self.assertEqual(saved['lifecycle_resume']['from'], first)
        self.assertEqual(saved['lifecycle_resume']['to'], second)
        self.assertEqual(saved['lifecycle_resume']['previous'], before['lifecycle_resume'])
        self.assertEqual(saved['repair'], before['repair'])
        self.assertNotIn('host_finalization', saved)
        self.assertEqual(path.read_bytes(), auth_bytes)
        self.assertEqual(paths['state'].read_bytes(), once)

    def test_resume_chain_binds_every_selected_owner_to_original_authorization(self):
        _, auth, state, _, first = self.resumed_repair_fixture()
        _, second = self.selected_copy('second-resume')
        previous = copy.deepcopy(state['lifecycle_resume'])
        state['lifecycle_resume'] = {'from': first, 'to': second,
            'authorization_sha256': state['authorization_sha256'], 'previous': previous}
        self.assertEqual(atom.resumed_lifecycle(auth, state)['lifecycle_owner'], second)
        for field in ('from', 'authorization_sha256', 'to'):
            with self.subTest(field=field):
                changed = copy.deepcopy(state)
                if field == 'from':
                    changed['lifecycle_resume'][field] = self.spec
                elif field == 'to':
                    changed['lifecycle_resume'][field] = self.spec
                else:
                    changed['lifecycle_resume']['previous'][field] = 'f' * 64
                with self.assertRaises(atom.AtomRefusal):
                    atom.resumed_lifecycle(auth, changed)
        (Path(first['path']).parent / 'issue_atom.py').write_text('changed historical selection')
        with self.assertRaisesRegex(atom.AtomRefusal, 'source_sha256'):
            atom.resumed_lifecycle(auth, state)

    def test_postwrite_host_projection_rebind_keeps_original_facts_and_sequence(self):
        new_root = self.runtime.parent / 'postwrite-lifecycle'
        for name in atom.LIFECYCLE_FILES:
            target = new_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.runtime / name, target)
        source = new_root / 'issue_atom.py'
        source.write_text(source.read_text() + '\n# selected post-write source\n')
        hashes = {name: atom.digest_file(new_root / name) for name in atom.LIFECYCLE_FILES}
        selected = {'path': str(new_root / 'issue-atom'), 'sha256': hashes['issue-atom'],
                    'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True,
                                                               separators=(',', ':')).encode())}
        auth = {**self.fixture.fixture.authorization, 'lifecycle_owner': self.spec}
        state = {'authorization_sha256': 'a' * 64, 'envelope_sha256': 'b' * 64}
        with patch.object(atom, '__file__', str(self.runtime / 'issue_atom.py')):
            manager = atom.host_manager(auth, state)
        manager.observe({'stop_offered': {'value': True, 'evidence': 'c' * 64,
                                         'producer': 'issue_atom.py:finish_host'}})
        prior = manager.record()
        state['host_finalization'] = prior
        state['lifecycle_resume'] = {'from': self.spec, 'to': selected, 'authorization_sha256': 'a' * 64}
        with patch.object(atom, '__file__', str(new_root / 'issue_atom.py')):
            atom.resume_host_finalization(auth, state)
            resumed = atom.host_manager(auth, state)
        self.assertEqual(state['host_finalization_resume']['prior'], prior)
        self.assertEqual(resumed.sequence, prior['sequence'])
        self.assertEqual(resumed.facts, prior['facts'])
        self.assertNotEqual(resumed.identity['plan'], prior['identity']['plan'])
        self.assertEqual(resumed.identity['subject'], prior['identity']['subject'])
        second_root, second = self.selected_copy('second-host-resume')
        first_history = copy.deepcopy(state['host_finalization_resume'])
        first_projection = copy.deepcopy(state['host_finalization'])
        state['lifecycle_resume'] = {'from': selected, 'to': second,
            'authorization_sha256': 'a' * 64, 'previous': state['lifecycle_resume']}
        with patch.object(atom, '__file__', str(second_root / 'issue_atom.py')):
            atom.resume_host_finalization(auth, state)
            second_manager = atom.host_manager(auth, state)
        self.assertEqual(state['host_finalization_resume']['previous'], first_history)
        self.assertEqual(state['host_finalization_resume']['prior'], first_projection)
        self.assertEqual(second_manager.sequence, prior['sequence'])
        self.assertEqual(second_manager.facts, prior['facts'])
        source.write_text(source.read_text() + '# drift\n')
        with patch.object(atom, '__file__', str(new_root / 'issue_atom.py')):
            with self.assertRaises(atom.AtomRefusal):
                atom.host_manager(auth, state)


if __name__ == '__main__':
    unittest.main()
