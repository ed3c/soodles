"""Physical admission and publication-fault controls for authorization preparation."""
import json
import os
import signal
import sys
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import issue_atom
import supervisor_admission as admission
import test_issue_atom as atom_tests


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        fixture = atom_tests.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        entry = fixture.root / 'issue-atom'
        entry.write_text('#!/bin/sh\nexit 97\n')
        entry.chmod(0o755)
        workflow = fixture.root / admission.CANONICAL_WORKFLOW['path']
        workflow.parent.mkdir(parents=True)
        workflow.write_bytes((Path(admission.__file__).parent / admission.CANONICAL_WORKFLOW['path']).read_bytes())
        subprocess.run(['git', 'add', '.'], cwd=fixture.root, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Bind canonical workflow'], cwd=fixture.root,
                       check=True, capture_output=True)
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fixture.root, text=True).strip()
        value = fixture.authorization
        self.selection = {
            'schema': 1, 'repository': value['repository'], 'control_root': str(fixture.root),
            'issue': {**value['issue'], 'body': value['issue']['body'].replace(fixture.base, head)},
            'task': value['task'], 'carrier': {**value['carrier'], 'noodle': value['noodle']},
            'landing_owner': value['landing_owner'], 'instruction_paths': [],
        }
        self.path = fixture.outer / 'selection.json'
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        self.output = fixture.outer / 'prepared'

    def run_authorize(self):
        return admission.authorize(str(self.path), self.digest, str(self.output))

    def test_completion_is_bound_to_final_paths_and_existing_validator(self):
        result = self.run_authorize()
        authorization, digest = issue_atom.validate_authorization(
            result['authorization']['path'], result['authorization']['sha256'])
        self.assertEqual(result, json.loads((self.output / 'prepared.json').read_text()))
        self.assertEqual(result['next']['environment'], {'SOODLES_AUTHORIZATION_SHA256': digest})
        self.assertEqual(result['next']['argv'],
                         [str(self.fixture.root / 'issue-atom'), 'run', str(self.output / 'authorization.json')])
        self.assertEqual(authorization['landing_owner'], self.selection['landing_owner'])
        self.assertFalse(result['authorizes_landing'])

    def test_amendment_selection_preserves_prior_pr_identity(self):
        self.selection['issue']['number'] = 128
        prior = {
            'owner': 'soodles.candidate-publication', 'status': 'created',
            'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#128',
            'branch': 'soodles/issue-128-' + 'b' * 12,
            'head': 'b' * 40, 'tree': 'c' * 40,
            'pr': {'number': 41, 'url': 'https://github.com/ed3c/soodles/pull/41'},
            'next': None, 'authorizes_landing': False,
        }
        self.selection['prior_publication'] = prior
        prior_path = self.fixture.outer / 'previous-authorization.json'
        parent = {**self.fixture.authorization, 'base_head': admission.parse_contract(self.selection['issue']['body'])['base_head'],
                  'issue': dict(self.selection['issue'])}
        prior_path.write_text(json.dumps(parent) + '\n')
        prior_atom = {'path': str(prior_path), 'sha256': issue_atom.digest_file(prior_path)}
        prior_path.with_name(prior_path.name + '.state.json').write_text(json.dumps({
            'authorization_sha256': prior_atom['sha256'], 'phase': 'ci',
            'noodle_start': {'status': 'started', 'config_sha256': '1' * 64,
                             'original_config': None, 'restored': True}}))
        self.selection['prior_atom'] = prior_atom
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        result = self.run_authorize()
        authorization, _ = issue_atom.validate_authorization(
            result['authorization']['path'], result['authorization']['sha256'])
        self.assertEqual(authorization['prior_publication'], prior)
        self.assertEqual(authorization['prior_atom'], prior_atom)
        self.assertEqual(self.run_authorize(), result)

        # A second correction can follow a P-class change. Its instructions
        # belong to the selected published head, not the unchanged control base.
        base = authorization['base_head']
        instruction = self.fixture.root / 'AGENTS.md'
        instruction.write_text('Published correction instructions\n')
        subprocess.run(['git', 'add', 'AGENTS.md'], cwd=self.fixture.root, check=True)
        subprocess.run(['git', 'commit', '-m', 'fixture published instructions'],
                       cwd=self.fixture.root, check=True, capture_output=True)
        published = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.fixture.root, text=True).strip()
        published_tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=self.fixture.root, text=True).strip()
        subprocess.run(['git', 'reset', '--hard', base], cwd=self.fixture.root, check=True, capture_output=True)
        self.selection['prior_publication'] = {**prior, 'head': published, 'tree': published_tree}
        self.selection['instruction_paths'] = ['AGENTS.md']
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        self.output = self.fixture.outer / 'published-instructions'
        selected = self.run_authorize()
        current, _ = issue_atom.validate_authorization(selected['authorization']['path'], selected['authorization']['sha256'])
        self.assertEqual(current['base_head'], base)
        context = issue_atom.issue_admission.resolve_instruction_context(
            self.fixture.root, published, current['instruction_pins'])
        self.assertEqual(context['source_head'], published)
        self.assertEqual(self.run_authorize(), selected)
        current['instruction_pins'][0]['sha256'] = 'f' * 64
        with self.assertRaisesRegex(issue_atom.AtomRefusal, 'instruction_context.files.sha256'):
            issue_atom.selected_instruction_pins(current)
        self.selection['instruction_paths'] = []

        self.output = self.fixture.outer / 'foreign-pr-selection'
        self.selection['prior_publication'] = {**prior, 'subject': 'ed3c/soodles#999'}
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior.identity') as caught:
            self.run_authorize()
        self.assertEqual(caught.exception.next['owner'], 'supervisor')
        self.assertEqual(caught.exception.next['required'], ['exact_prior_publication'])
        self.assertFalse(self.output.exists())

        self.selection['prior_publication'] = prior
        self.selection['prior_atom'] = {**prior_atom, 'sha256': 'f' * 64}
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'amendment.prior_atom.sha256'):
            self.run_authorize()
        self.assertFalse(self.output.exists())

    def test_amendment_pins_original_host_config_while_old_bundle_is_installed(self):
        self.selection['issue']['number'] = 128
        self.selection['prior_publication'] = {
            'owner': 'soodles.candidate-publication', 'status': 'created',
            'repository': 'ed3c/soodles', 'subject': 'ed3c/soodles#128',
            'branch': 'soodles/issue-128-' + 'b' * 12,
            'head': 'b' * 40, 'tree': 'c' * 40,
            'pr': {'number': 41, 'url': 'https://github.com/ed3c/soodles/pull/41'},
            'next': None, 'authorizes_landing': False,
        }
        config = self.fixture.root / '.noodle.toml'
        config.write_text('mode = "supervised"\n')
        installed = issue_atom.digest_file(config)
        previous = self.fixture.outer / 'previous-live.json'
        parent = {**self.fixture.authorization, 'base_head': admission.parse_contract(self.selection['issue']['body'])['base_head'],
                  'issue': dict(self.selection['issue'])}
        previous.write_text(json.dumps(parent) + '\n')
        digest = issue_atom.digest_file(previous)
        previous.with_name(previous.name + '.state.json').write_text(json.dumps({
            'authorization_sha256': digest, 'phase': 'ci',
            'noodle_start': {'status': 'started', 'config_sha256': installed,
                             'original_config': None}}))
        self.selection['prior_atom'] = {'path': str(previous), 'sha256': digest}
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        receipt = self.run_authorize()
        auth, _ = issue_atom.validate_authorization(
            receipt['authorization']['path'], receipt['authorization']['sha256'])
        self.assertIsNone(auth['host_config_sha256'])
        self.assertEqual(issue_atom.host_config_identity(self.fixture.root), installed)

        config.write_text('mode = "manual"\n')
        self.output = self.fixture.outer / 'changed-host-output'
        with self.assertRaisesRegex(admission.AdmissionRefusal,
                                    'amendment.current_host_config'):
            self.run_authorize()
        self.assertFalse(self.output.exists())

    def test_precommit_failure_cleans_only_staging(self):
        before = set(self.fixture.outer.iterdir())
        with patch.object(admission, '_publish_directory', side_effect=OSError('precommit')):
            with self.assertRaisesRegex(OSError, 'precommit'):
                self.run_authorize()
        self.assertEqual(set(self.fixture.outer.iterdir()), before)

    def test_postcommit_failure_retains_identity(self):
        original = admission._sync_directory
        def sync(path):
            if path == self.output.parent:
                raise OSError('postcommit')
            original(path)
        with patch.object(admission, '_sync_directory', sync):
            with self.assertRaisesRegex(OSError, 'postcommit'):
                self.run_authorize()
        saved = (self.output / 'authorization.json').read_bytes()
        self.run_authorize()
        self.assertEqual(saved, (self.output / 'authorization.json').read_bytes())

    def test_foreign_collisions_and_publication_races_preserve_inode(self):
        original = admission._publish_directory
        for race in (False, True):
            for kind in ('empty', 'nonempty', 'symlink'):
                with self.subTest(race=race, kind=kind):
                    self.output = self.fixture.outer / f'collision-{race}-{kind}'
                    def foreign():
                        if kind == 'symlink':
                            self.output.symlink_to(self.fixture.root, target_is_directory=True)
                        else:
                            self.output.mkdir()
                            if kind == 'nonempty':
                                (self.output / 'foreign').write_text('preserve')
                        return self.output.lstat().st_ino
                    inode = []
                    def publish(staging, target):
                        inode.append(foreign())
                        original(staging, target)
                    if not race:
                        inode.append(foreign())
                    with patch.object(admission, '_publish_directory', publish):
                        with self.assertRaises((admission.AdmissionRefusal, OSError)):
                            self.run_authorize()
                    self.assertEqual(self.output.lstat().st_ino, inode[0])
                    if kind == 'nonempty':
                        self.assertEqual((self.output / 'foreign').read_text(), 'preserve')

    def cli(self):
        return [sys.executable, '-B', admission.__file__, 'authorize',
                str(self.path), self.digest, str(self.output)]

    def test_same_argv_readback_preserves_bytes_without_live_validation(self):
        first = subprocess.run(self.cli(), capture_output=True, text=True, check=True)
        saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.output.iterdir()}
        (self.fixture.root / '.noodle.toml').write_text('changed config')
        (self.fixture.root / 'dirty').write_text('dirty')
        self.fixture.binary.unlink()
        second = subprocess.run(self.cli(), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        self.assertEqual(saved, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                 for p in self.output.iterdir()})
        result = json.loads(second.stdout)
        with self.assertRaises(issue_atom.AtomRefusal):
            issue_atom.validate_authorization(result['authorization']['path'],
                                             result['authorization']['sha256'])

    def test_committed_damage_and_legacy_bundle_are_never_repaired(self):
        for name in ('authorization', 'prepared', 'selection-binding'):
            for damage in ('missing', 'corrupt', 'unreadable', 'duplicate', 'encoding', 'symlink', 'directory'):
                with self.subTest(name=name, damage=damage):
                    self.output = self.fixture.outer / f'{name}-{damage}'
                    self.run_authorize()
                    path = self.output / (name + '.json')
                    data = path.read_bytes()
                    path.unlink()
                    if damage == 'corrupt':
                        path.write_bytes(data + b'x')
                    elif damage == 'unreadable':
                        path.write_bytes(data)
                        path.chmod(0)
                        self.addCleanup(path.chmod, 0o644)
                    elif damage == 'duplicate':
                        path.write_bytes(b'{"schema":1,"schema":1}')
                    elif damage == 'encoding':
                        path.write_bytes(b'\xff')
                    elif damage == 'symlink':
                        other = self.fixture.outer / f'{name}-original'
                        other.write_bytes(data)
                        path.symlink_to(other)
                    elif damage == 'directory':
                        path.mkdir()
                    before = {p.name: p.lstat().st_ino for p in self.output.iterdir()}
                    saved = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                             for p in self.output.iterdir()
                             if p.is_file() and p != path}
                    damaged_stat = path.lstat() if damage != 'missing' else None
                    result = subprocess.run(self.cli(), capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, '')
                    receipt = json.loads(result.stdout)
                    self.assertEqual(receipt['owner'], 'supervisor.authorization')
                    self.assertEqual(receipt['status'], 'refused')
                    self.assertEqual(receipt['invalid'], {
                        'field': 'authorization.bundle.' + name, 'value': str(path)})
                    self.assertEqual(receipt['next'], {
                        'kind': 'input', 'owner': 'supervisor',
                        'required': ['exact_committed_bundle_component']})
                    self.assertFalse(receipt['authorizes_landing'])
                    self.assertEqual(before, {p.name: p.lstat().st_ino for p in self.output.iterdir()})
                    self.assertEqual(saved, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                            for p in self.output.iterdir()
                                            if p.is_file() and p != path})
                    if damaged_stat is not None:
                        # Readback may update access time, but cannot mutate identity.
                        after = path.lstat()
                        for field in ('st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns'):
                            self.assertEqual(getattr(after, field), getattr(damaged_stat, field))
                    if damage == 'unreadable':
                        path.chmod(0o644)
                    if damage in ('corrupt', 'unreadable', 'duplicate', 'encoding'):
                        expected = {'corrupt': data + b'x', 'unreadable': data,
                                    'duplicate': b'{"schema":1,"schema":1}', 'encoding': b'\xff'}
                        self.assertEqual(path.read_bytes(), expected[damage])

    def test_changed_selection_even_with_updated_digest_refuses(self):
        self.run_authorize()
        self.selection['task'] += ' changed'
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        saved = {p.name: p.read_bytes() for p in self.output.iterdir()}
        result = subprocess.run(self.cli(), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['owner'], 'supervisor.authorization')
        self.assertEqual(receipt['status'], 'refused')
        self.assertEqual(receipt['invalid']['field'], 'authorization.selection_binding')
        self.assertEqual(saved, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_rehashed_arbitrary_continuation_or_authorization_refuses(self):
        for name in ('prepared', 'authorization'):
            self.output = self.fixture.outer / ('tampered-' + name)
            self.run_authorize()
            path = self.output / (name + '.json')
            value = json.loads(path.read_bytes())
            if name == 'prepared':
                value['next']['argv'] = ['/bin/false']
            else:
                value['task'] = 'different selection'
            path.write_bytes(admission._canonical(value))
            binding_path = self.output / 'selection-binding.json'
            binding = json.loads(binding_path.read_bytes())
            binding[name + '_sha256'] = issue_atom.digest_file(path)
            binding_path.write_bytes(admission._canonical(binding))
            with self.assertRaises(admission.AdmissionRefusal):
                self.run_authorize()

    def test_unsupported_primitive_refuses_without_publication(self):
        with patch.object(admission.sys, 'platform', 'unsupported'):
            with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.publication'):
                self.run_authorize()
        self.assertFalse(self.output.exists())
        with patch.object(admission.ctypes, 'CDLL', return_value=object()):
            with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.publication'):
                self.run_authorize()
        self.assertFalse(self.output.exists())

    def child(self, script, *args):
        return subprocess.Popen([sys.executable, '-B', '-c', script, str(self.path),
                                 self.digest, str(self.output), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_actual_sigkill_during_each_write_and_after_publication(self):
        script = r"""
import json, os, signal, sys
from pathlib import Path
import supervisor_admission as a
mode = sys.argv[4]
original_open = Path.open
class Interrupted:
    def __init__(self, stream): self.stream = stream
    def __enter__(self): return self
    def __exit__(self, *args): self.stream.close()
    def write(self, data):
        self.stream.write(data[:max(1, len(data)//2)])
        self.stream.flush()
        os.fsync(self.stream.fileno())
        os.kill(os.getpid(), signal.SIGKILL)
def opened(path, *args, **kwargs):
    stream = original_open(path, *args, **kwargs)
    if path.name == mode and args == ('wb',): return Interrupted(stream)
    return stream
Path.open = opened
publish = a._publish_directory
def published(staging, target):
    publish(staging, target)
    os.kill(os.getpid(), signal.SIGKILL)
if mode == 'published': a._publish_directory = published
a.authorize(*sys.argv[1:4])
"""
        for mode in ('authorization.json', 'prepared.json', 'selection-binding.json', 'published'):
            with self.subTest(mode=mode):
                self.output = self.fixture.outer / ('killed-' + mode)
                process = self.child(script, mode)
                stdout, stderr = process.communicate(timeout=30)
                self.assertEqual(process.returncode, -signal.SIGKILL, stderr)
                self.assertEqual(stdout, '')
                if mode == 'published':
                    saved = (self.output / 'authorization.json').read_bytes()
                    self.assertEqual(len(list(self.output.iterdir())), 3)
                else:
                    self.assertFalse(self.output.exists())
                self.run_authorize()
                if mode == 'published':
                    self.assertEqual(saved, (self.output / 'authorization.json').read_bytes())

    def test_concurrent_same_and_different_selection(self):
        script = r"""
import json, sys, time
from pathlib import Path
import supervisor_admission as a
publish = a._publish_directory
marker, peer = map(Path, sys.argv[4:6])
def barrier(staging, target):
    marker.write_text('ready')
    deadline = time.monotonic() + 15
    while not peer.exists():
        if time.monotonic() > deadline: raise RuntimeError('barrier timeout')
        time.sleep(.01)
    publish(staging, target)
a._publish_directory = barrier
try:
    print(json.dumps(a.authorize(*sys.argv[1:4])))
except a.AdmissionRefusal:
    sys.exit(1)
"""
        for different in (False, True):
            self.output = self.fixture.outer / f'concurrent-{different}'
            left = self.fixture.outer / f'left-{different}'
            right = self.fixture.outer / f'right-{different}'
            first = self.child(script, str(left), str(right))
            original_path, original_digest = self.path, self.digest
            if different:
                self.path = self.fixture.outer / 'other-selection.json'
                self.path.write_text(json.dumps({**self.selection, 'task': 'other task'}))
                self.digest = issue_atom.digest_file(self.path)
            second = self.child(script, str(right), str(left))
            out1, err1 = first.communicate(timeout=30)
            out2, err2 = second.communicate(timeout=30)
            self.assertEqual(sorted([first.returncode, second.returncode]),
                             [0, 1] if different else [0, 0], err1 + err2)
            if not different:
                self.assertEqual(json.loads(out1), json.loads(out2))
            self.path, self.digest = original_path, original_digest

    def test_git_subdirectory_cannot_become_a_control_root(self):
        self.selection['control_root'] = str(self.fixture.root / '.github')
        self.path.write_text(json.dumps(self.selection))
        self.digest = issue_atom.digest_file(self.path)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'selection.control_root'):
            self.run_authorize()
        self.assertFalse(self.output.exists())

    def test_missing_or_nonexecutable_continuation_refuses(self):
        entry = self.fixture.root / 'issue-atom'
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    entry.unlink()
                else:
                    entry.chmod(0o644)
                with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.next.entry'):
                    self.run_authorize()
                self.assertFalse(self.output.exists())

    def test_nonexecutable_selected_carrier_is_not_repaired(self):
        self.fixture.binary.chmod(0o644)
        with self.assertRaises(admission.AdmissionRefusal):
            self.run_authorize()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.fixture.binary.stat().st_mode & 0o777, 0o644)


class GenericCorrectionAuthorizationTests(unittest.TestCase):
    def test_descendant_base_keeps_original_control_source_and_bound_base_ref(self):
        import test_generic_repository_binding as generic_tests
        fixture = generic_tests.GenericBindingTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root, selection, _ = fixture.target(branch='trunk')
        prepared = fixture.authorize(selection)
        parent = json.loads(Path(prepared['authorization']['path']).read_text())
        source = parent['base_head']
        tree = fixture.git(root, 'rev-parse', 'HEAD^{tree}')
        parent_path = Path(prepared['authorization']['path'])
        issue_atom.save_json(issue_atom.artifact_paths(parent_path)['state'], {
            'authorization_sha256': prepared['authorization']['sha256'], 'phase': 'ci',
            'noodle_start': {'status': 'started', 'config_sha256': '1' * 64,
                             'original_config': None, 'restored': True}})
        (root / 'target.py').write_text("print('advanced target')\n")
        fixture.git(root, 'commit', '-am', 'Advance the selected provider base')
        target = fixture.git(root, 'rev-parse', 'HEAD')
        fixture.git(root, 'update-ref', 'refs/remotes/origin/trunk', target)
        fixture.git(root, 'reset', '--hard', source)
        correction = {**selection, 'prior_atom': prepared['authorization'],
            'prior_publication': {'owner': 'soodles.candidate-publication', 'status': 'created',
                'repository': selection['repository'], 'subject': selection['repository'] + '#7',
                'branch': 'soodles/issue-7-' + source[:12], 'head': source, 'tree': tree,
                'pr': {'number': 8, 'url': 'https://github.com/' + selection['repository'] + '/pull/8'},
                'next': None, 'authorizes_landing': False},
            'issue': {**selection['issue'], 'body': issue_atom.issue_admission.correction_base_body(
                parent, selection['issue']['body'], target, source)}}
        receipt = fixture.authorize(correction, 'correction')
        authorization, _ = issue_atom.validate_authorization(
            receipt['authorization']['path'], receipt['authorization']['sha256'])
        self.assertEqual(authorization['base_head'], target)
        self.assertEqual(authorization['target_binding'], selection['target_binding'])
        self.assertEqual(authorization['prior_atom'], prepared['authorization'])
        self.assertEqual(fixture.git(root, 'rev-parse', 'HEAD'), source)
        self.assertEqual(fixture.authorize(correction, 'correction'), receipt)
        fixture.git(root, 'update-ref', 'refs/remotes/origin/trunk', source)
        with self.assertRaisesRegex(admission.AdmissionRefusal, 'authorization.noodle_base'):
            fixture.authorize(correction, 'changed-base')


if __name__ == '__main__':
    unittest.main()
