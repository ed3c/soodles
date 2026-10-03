"""Original custody and worker refusal controls over disposable processes."""
import copy
import fcntl
import hashlib
import json
import os
import signal
import traceback
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from unittest.mock import Mock

import issue_atom as atom
import issue_admission as admission
import issue_execution as execution
import test_issue_execution as fixtures
import test_supervisor_admission as supervisor_fixtures
import supervisor_admission


class InterruptionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IssueExecutionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.admit('supervised')
        f.promote_fixture()
        original = f.directory / 'original.json'
        original.write_bytes(f.path.read_bytes())
        e = f.envelope['execution']
        subject = f.envelope['repository'] + '#18'
        evidence = f.runtime / 'interruptions' / hashlib.sha256((e['order_id'] + '\n' + subject).encode()).hexdigest()
        evidence.mkdir(parents=True)
        self.recovery = {'kind': 'prepublication_interruption',
            'original_envelope': {'path': str(original), 'sha256': f.pin},
            'custody': {'order_id': e['order_id'], 'stage_index': 0, 'attempt_id': 'old-attempt',
                'session_id': 'old-session', 'subject': subject, 'envelope_sha256': f.pin,
                'worktree_name': e['worktree'], 'worktree_path': str(f.worktree),
                'branch': e['worktree'], 'head': e['source_head'], 'session_sha256': {}, 'candidate_manifest': {}},
            'custody_sha256': 'c' * 64, 'evidence_path': str(evidence)}
        e['recovery_context'] = self.recovery
        f.bind_envelope()
        self.stage = f.snapshot['state']['orders'][e['order_id']]['stages'][0]
        binding = admission.validate_issue(f.issue, f.envelope)
        self.stage['prompt'] = json.dumps(execution.projection(binding, f.pin, 'supervised'))
        self.stage['attempts'] = [{'attempt_id': 'new-attempt', 'session_id': f.session, 'status': 'running'}]
        self.stage['status'] = 'running'
        f.save_owner()
        self.offer = {'custody_sha256': 'c' * 64, 'attempt_id': 'new-attempt'}
        (evidence / 'dispatch-offered.json').write_text(json.dumps(self.offer))
        self.result = evidence / 'dispatch-result.json'
        self.result.write_text(json.dumps({**self.offer, 'session_id': f.session}))
        self.receipt = {**{key: self.recovery[key] for key in ('custody', 'custody_sha256', 'evidence_path')},
            'owner': 'Noodle interrupted execution', 'status': 'dispatched', 'candidate_unchanged': True,
            'candidate_invalid': '', 'successor': {'attempt_id': 'new-attempt', 'session_id': f.session}}
        self.lock = (f.runtime / 'noodle.lock').open('w')
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        self.addCleanup(self.lock.close)
        (f.worktree / 'allowed.py').write_text('retained candidate\n')

    def launch(self):
        with patch.object(execution, 'interruption_readback', return_value=self.receipt):
            return self.fixture.launch()

    def test_exact_dirty_successor_reaches_sentinel(self):
        result = self.launch()
        self.assertEqual(result['session_id'], self.fixture.session)
        self.assertTrue(self.fixture.effect.exists())
        self.assertEqual((self.fixture.worktree / 'allowed.py').read_text(), 'retained candidate\n')

    def test_delayed_result_is_observed_before_model_and_without_dispatch(self):
        self.result.unlink()
        child = subprocess.Popen([sys.executable, '-c',
            'import pathlib,time,sys; time.sleep(.15); pathlib.Path(sys.argv[1]).write_text(sys.argv[2])',
            str(self.result), json.dumps({**self.offer, 'session_id': self.fixture.session})])
        self.addCleanup(lambda: child.wait(timeout=5))
        started = time.monotonic()
        self.launch()
        self.assertGreaterEqual(time.monotonic() - started, .1)
        self.assertTrue(self.fixture.effect.exists())
        self.assertEqual(len(self.stage['attempts']), 1)

    def test_timeout_owner_loss_foreign_receipt_and_candidate_drift_refuse(self):
        for case in ('timeout', 'owner', 'foreign', 'drift', 'readerror'):
            with self.subTest(case=case):
                self.result.write_text(json.dumps({**self.offer, 'session_id': self.fixture.session}))
                self.receipt['candidate_unchanged'] = True
                self.receipt['candidate_invalid'] = ''
                if case == 'timeout':
                    self.result.unlink()
                if case == 'owner':
                    fcntl.flock(self.lock, fcntl.LOCK_UN)
                if case == 'foreign':
                    self.result.write_text(json.dumps({**self.offer, 'session_id': 'foreign'}))
                if case in ('drift', 'readerror'):
                    self.receipt.update(candidate_unchanged=False, candidate_invalid=case)
                with self.assertRaises(admission.AdmissionRefusal):
                    self.launch()
                self.assertFalse(self.fixture.effect.exists())
                fcntl.flock(self.lock, fcntl.LOCK_EX)

    def test_changed_original_binding_and_fresh_issue_refuse_before_model(self):
        for field in ('task', 'source_head'):
            with self.subTest(field=field):
                original = self.fixture.envelope['execution'][field]
                self.fixture.envelope['execution'][field] = 'f' * 40 if field == 'source_head' else 'new task'
                self.fixture.bind_envelope()
                with self.assertRaises(admission.AdmissionRefusal):
                    self.launch()
                self.fixture.envelope['execution'][field] = original
        self.fixture.bind_envelope()
        self.fixture.issue['state'] = 'closed'
        with self.assertRaises(admission.AdmissionRefusal):
            self.launch()
        self.assertFalse(self.fixture.effect.exists())

    def test_native_candidate_diagnostic_is_preserved(self):
        result = subprocess.CompletedProcess([], 1, json.dumps({**self.receipt, 'status': 'refused',
                                                               'invalid': 'original session hashes changed'}), '')
        with patch.object(execution.subprocess, 'run', return_value=result):
            with self.assertRaises(admission.AdmissionRefusal) as error:
                execution.interruption_readback(self.fixture.envelope)
        self.assertEqual(error.exception.invalid['value']['invalid'], 'original session hashes changed')

    def test_prepare_intent_is_saved_before_call_and_unknown_result_never_replays(self):
        f = self.fixture
        auth = {'control_root': str(f.root)}
        paths = atom.artifact_paths(f.directory / 'authorization.json')
        packet = {**self.recovery, 'carrier': f.envelope['execution']['carrier']}
        state = {'issue': {'number': 18}, 'interruption': {'logs': [], 'prior_start': {}}}
        argv = [packet['carrier']['noodle']['path'], '--project-dir', str(f.root),
                'interruption', 'prepare', self.recovery['custody']['order_id'],
                self.recovery['custody']['subject'], 'c' * 64]
        receipt = {**self.receipt, 'status': 'recoverable', 'next': {'argv': argv}}
        def native_call(*args, **kwargs):
            saved = atom.read_json(paths['state'], 'state')
            self.assertEqual(saved['interruption']['prepare'], {'argv': argv, 'status': 'offered'})
            raise subprocess.TimeoutExpired(argv, 30)
        with patch.object(atom, 'interruption_record', return_value=packet), \
                patch.object(atom, 'interruption_binding', return_value=f.envelope), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'), \
                patch.object(execution, 'interruption_readback', return_value=receipt), \
                patch.object(atom.subprocess, 'run', side_effect=native_call) as effect:
            with self.assertRaisesRegex(atom.AtomRefusal, 'prepare.outcome'):
                atom.advance_interruption(auth, paths, state, Mock(issue=lambda _: f.issue), {})
            with self.assertRaisesRegex(atom.AtomRefusal, 'interruption.prepare'):
                atom.advance_interruption(auth, paths, state, Mock(issue=lambda _: f.issue), {})
            effect.assert_called_once()

    def test_provider_refusal_precedes_native_prepare(self):
        f = self.fixture
        f.issue['state'] = 'closed'
        with patch.object(atom, 'interruption_record', return_value={}), \
                patch.object(atom, 'interruption_binding', return_value=f.envelope), \
                patch.object(execution, 'interruption_readback', side_effect=AssertionError('native call')):
            with self.assertRaises(admission.AdmissionRefusal):
                atom.advance_interruption({'control_root': str(f.root)}, {},
                    {'issue': {'number': 18}, 'interruption': {}}, Mock(issue=lambda _: f.issue), {})

    def test_adoption_preserves_identity_and_rejects_foreign_prompt_without_effects(self):
        f = self.fixture
        auth_path = f.directory / 'authorization.json'
        original_path = Path(self.recovery['original_envelope']['path'])
        original = json.loads(original_path.read_bytes())
        auth = {'control_root': str(f.root), 'repository': 'ed3c/soodles', 'base_head': original['base_head'],
            'task': original['execution']['task'], 'noodle': original['execution']['carrier']['noodle'],
            'carrier': {k: v for k, v in original['execution']['carrier'].items() if k != 'noodle'},
            'issue': {'number': 18, 'body': f.issue['body']}}
        auth_path.write_text(json.dumps(auth))
        logs = f.directory / 'original.log'
        logs.write_text('original failure')
        config = original_path.parent / 'noodle.toml'
        config.write_text('mode="supervised"\n')
        (f.root / '.noodle.toml').write_bytes(config.read_bytes())
        start = {'argv': [str(f.binary)], 'config_sha256': atom.digest_file(config),
                 'stdout': str(logs), 'stderr': str(logs)}
        prepared = original_path.parent / 'prepared.json'
        prepared.write_text(json.dumps({'envelope_sha256': self.recovery['original_envelope']['sha256'],
            'next': {'argv': start['argv']}, 'start': str(f.binary), 'start_sha256': atom.digest_file(f.binary)}))
        paths = {**atom.artifact_paths(auth_path), 'envelope': original_path}
        state = {'phase': 'execution', 'publication': None, 'writes': {}, 'issue': {'number': 18},
            'authorization_sha256': atom.digest_file(auth_path), 'envelope_sha256': atom.digest_file(original_path),
            'admission_sha256': atom.digest_file(prepared), 'noodle_start': start}
        binary = f.directory / 'new-native'
        binary.write_bytes(f.binary.read_bytes()); binary.chmod(0o755)
        packet = {'schema': 1, **self.recovery, 'authorization': {'path': str(auth_path), 'sha256': atom.digest_file(auth_path)},
            'lifecycle_owner': {'path': str(f.directory / 'selected/issue-atom')},
            'carrier': {**original['execution']['carrier'], 'noodle': {'path': str(binary), 'sha256': atom.digest_file(binary)}}}
        descriptor = f.directory / 'descriptor.json'; descriptor.write_text(json.dumps(packet))
        ref = {'path': str(descriptor), 'sha256': atom.digest_file(descriptor)}
        receipt = {**self.receipt, 'status': 'recoverable'}
        with patch.object(atom, 'validate_lifecycle_owner'), \
                patch.object(atom, 'observe_prior_loop', return_value='stopped'), \
                patch.object(execution, 'interruption_readback', return_value=receipt) as native:
            with self.assertRaisesRegex(atom.AtomRefusal, 'original_prompt'):
                atom.adopt_interruption(auth_path, auth, state, paths, ref, packet)
            self.assertNotIn('interruption', state)
            native.assert_not_called()
            self.stage['prompt'] = json.dumps(execution.projection(
                admission.validate_issue(f.issue, original), atom.digest_file(original_path), 'supervised'))
            f.save_owner()
            atom.adopt_interruption(auth_path, auth, state, paths, ref, packet)
            saved = copy.deepcopy(state)
            atom.adopt_interruption(auth_path, auth, state, paths, ref, packet)
            self.assertEqual(state, saved)
            self.assertEqual(state['interruption']['prior_start'], start)
            self.assertEqual(state['lifecycle_resume']['authorization_sha256'], atom.digest_file(auth_path))
            native.assert_called_once()

    def test_unknown_held_start_does_not_offer_another_process(self):
        f = self.fixture
        state = {'interruption': {'start_offered': True}, 'noodle_start': {'status': 'offered'}}
        before = copy.deepcopy(state)
        with patch.object(atom.subprocess, 'Popen', side_effect=AssertionError('duplicate start')):
            with self.assertRaisesRegex(atom.AtomRefusal, 'interruption.start'):
                atom.ensure_noodle({'control_root': str(f.root)}, {}, state,
                    {'action': 'interruption_prepared'}, {}, interruption_restart=True)
        self.assertEqual(state, before)

    def held_control(self):
        f = self.fixture
        paths = atom.artifact_paths(f.directory / 'authorization.json')
        output = f.directory / 'interruption-recovery'
        (output / 'admission').mkdir(parents=True)
        config = output / 'admission/noodle.toml'
        config.write_text('mode="supervised"\n')
        (f.root / '.noodle.toml').write_bytes(config.read_bytes())
        auth = {'control_root': str(f.root), 'noodle': f.envelope['execution']['carrier']['noodle']}
        packet = {**self.recovery, 'carrier': f.envelope['execution']['carrier']}
        binding = admission.validate_issue(f.issue, f.envelope)
        state = {'issue': {'number': 18}, 'envelope_sha256': f.pin,
            'noodle_start': {'status': 'started', 'config_sha256': atom.digest_file(config),
                'process_argv': [auth['noodle']['path'], '--project-dir', str(f.root), 'start', '--mode', 'manual']},
            'interruption': {'logs': [], 'start_offered': True, 'prepare': {'status': 'observed'},
                'prepared': {'path': str(output / 'admission/prepared.json')},
                'output': str(output), 'selection': {'sha256': 'd' * 64}, 'ack_prefix': ''}}
        self.stage.update(status='pending', prompt='original prompt',
            extra={'interrupted_execution': {'custody_sha256': self.recovery['custody_sha256'],
                'prior_attempt_id': self.recovery['custody']['attempt_id']}})
        f.snapshot['state'].update(mode='manual', mode_epoch=4)
        f.save_owner()
        native = {**self.receipt, 'status': 'prepared'}
        for target, name, kwargs in (
                (atom, 'interruption_record', {'return_value': packet}),
                (atom, 'interruption_binding', {'return_value': f.envelope}),
                (atom, 'validate_prior_atom_ref', {}),
                (atom, 'scope_projection', {'return_value': (auth, paths)}),
                (atom, 'observe_prior_loop', {'return_value': 'running'}),
                (execution, 'context', {'return_value': binding}),
                (execution, 'interruption_readback', {'return_value': native}),
                (atom.subprocess, 'Popen', {'side_effect': AssertionError('another start')})):
            context = patch.object(target, name, **kwargs)
            context.start()
            self.addCleanup(context.stop)
        return state, native, lambda: atom.advance_interruption(auth, paths, state,
            Mock(issue=lambda _: f.issue), {})

    def acknowledge_control(self, state, name):
        command = state[name]
        (self.fixture.runtime / 'control.ndjson').write_text('')
        with (self.fixture.runtime / 'control-ack.ndjson').open('a') as stream:
            stream.write(json.dumps({'id': command['id'], 'action': command['action'], 'status': 'ok'}) + '\n')
        if name == 'interruption_edit':
            self.stage['prompt'] = command['prompt']
        else:
            self.fixture.snapshot['state'].update(mode='supervised', mode_epoch=5)
        self.fixture.save_owner()

    def test_control_ack_reentry_releases_once_and_accepts_successor_writes(self):
        state, native, advance = self.held_control()
        mailbox = self.fixture.runtime / 'control.ndjson'
        self.assertEqual(advance()['action'], 'interruption_edit_pending')
        offered = mailbox.read_bytes()
        self.assertEqual(advance()['action'], 'interruption_edit_pending')
        self.assertEqual(mailbox.read_bytes(), offered)
        self.acknowledge_control(state, 'interruption_edit')
        self.assertEqual(advance()['action'], 'interruption_release_pending')
        offered = mailbox.read_bytes()
        self.assertEqual(advance()['action'], 'interruption_release_pending')
        self.assertEqual(mailbox.read_bytes(), offered)
        self.acknowledge_control(state, 'interruption_release')
        self.assertEqual(advance()['action'], 'interruption_dispatch_pending')
        native.update(status='dispatched', candidate_unchanged=False)
        self.stage['status'] = 'running'
        self.fixture.save_owner()
        self.assertEqual(advance()['action'], 'interruption_released')
        self.assertEqual(state['interruption']['status'], 'released')
        self.assertEqual(mailbox.read_bytes(), b'')
        self.assertEqual(set(state) & {'interruption_edit', 'interruption_release'},
                         {'interruption_edit', 'interruption_release'})

    def test_unknown_or_foreign_control_never_resends(self):
        state, _, advance = self.held_control()
        mailbox = self.fixture.runtime / 'control.ndjson'
        self.assertEqual(advance()['action'], 'interruption_edit_pending')
        mailbox.write_text('')
        self.assertEqual(advance()['action'], 'interruption_edit_pending')
        self.assertEqual(mailbox.read_bytes(), b'')
        foreign = {'id': 'foreign', 'action': 'mode', 'status': 'ok'}
        (self.fixture.runtime / 'control-ack.ndjson').write_text(json.dumps(foreign) + '\n')
        with self.assertRaisesRegex(atom.AtomRefusal, 'interruption.control.foreign'):
            advance()
        self.assertEqual(mailbox.read_bytes(), b'')
        self.assertNotIn('interruption_release', state)

    def test_ack_arriving_after_owner_snapshot_uses_fresh_readback(self):
        state, _, advance = self.held_control()
        self.assertEqual(advance()['action'], 'interruption_edit_pending')
        control = atom.amendment_control
        for name, expected in (('interruption_edit', 'interruption_release_pending'),
                               ('interruption_release', 'interruption_dispatch_pending')):
            def acknowledge_then_read(authorization, paths, current, key, command):
                if key == name:
                    self.acknowledge_control(state, name)
                return control(authorization, paths, current, key, command)
            with patch.object(atom, 'amendment_control', side_effect=acknowledge_then_read):
                self.assertEqual(advance()['action'], expected)


class RecoveryBundleTests(unittest.TestCase):
    def test_bundle_preserves_original_task_and_instructions_on_dirty_candidate(self):
        f = supervisor_fixtures.SupervisorFixture()
        self.addCleanup(f.close)
        f.carrier['codex']['argv'] = ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture-model']
        pins = [{'path': '.agents/skills/execute/SKILL.md', 'sha256': atom.digest_file(
            f.root / '.agents/skills/execute/SKILL.md')}]
        old, _ = f.prepare('original', wire_host=True, task='original task', instruction_pins=pins)
        envelope = json.loads((old / 'envelope.json').read_bytes())
        execution = envelope['execution']
        worktree = f.root / '.worktrees' / execution['worktree']
        f._git('worktree', 'add', '-b', execution['worktree'], str(worktree))
        (worktree / 'allowed.py').write_text('retained writer progress\n')
        subject = 'ed3c/soodles#118'
        recovery = {'kind': 'prepublication_interruption',
            'original_envelope': {'path': str(old / 'envelope.json'), 'sha256': atom.digest_file(old / 'envelope.json')},
            'custody_sha256': 'a' * 64,
            'custody': {'order_id': execution['order_id'], 'stage_index': 0, 'subject': subject,
                'envelope_sha256': atom.digest_file(old / 'envelope.json'), 'worktree_name': execution['worktree'],
                'worktree_path': str(worktree), 'branch': execution['worktree'], 'head': execution['source_head']},
            'evidence_path': str(f.root / '.noodle/interruptions' / hashlib.sha256(
                (execution['order_id'] + '\n' + subject).encode()).hexdigest())}
        source = f.external / 'selected-runtime'
        source.mkdir()
        for name in supervisor_admission.BUNDLE_PATHS:
            (source / name).write_bytes((Path(atom.__file__).parent / name).read_bytes())
        new, result = f.prepare('recovery', wire_host=True, correction=True, runtime_root=source,
                                recovery_context=recovery)
        actual = json.loads((new / 'envelope.json').read_bytes())
        self.assertEqual(actual, {**envelope, 'execution': {**execution, 'recovery_context': recovery}})
        self.assertEqual(result['process_argv'][-2:], ['--mode', 'manual'])
        self.assertEqual((worktree / 'allowed.py').read_text(), 'retained writer progress\n')
        synced = subprocess.run([str(new / 'backlog'), 'sync'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(synced.stdout), {'id': execution['order_id'], 'title': execution['order_id'],
            'plan': 'original task', 'repository': 'ed3c/soodles', 'issue': 118, 'source': 'admission_snapshot'})


def native_control(root, binary, digest, *, adapter=False):
    root=Path(root).resolve(); root.mkdir(parents=True,exist_ok=False)
    assert hashlib.sha256(Path(binary).read_bytes()).hexdigest()==digest
    project=root/'project'; runtime=project/'.noodle'
    order=admission.scoped_order_id(18, project) if adapter else 'order-1'
    repository='ed3c/soodles' if adapter else 'example/project'
    number=18 if adapter else 7
    subject=repository+'#'+str(number)
    wt=project/'.worktrees'/(order+'-0-execute')
    log=root/'commands.ndjson'; process=None
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('TOKEN','API_KEY','SECRET'))}
    env.update(NOODLE_NO_BROWSER='1',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
    def write(path, data):
        path.parent.mkdir(parents=True,exist_ok=True); path.write_text(data)
    def js(path, obj): write(path,json.dumps(obj,indent=2)+'\n')
    def run(args,cwd=None,check=True):
        p=subprocess.run([str(x) for x in args],cwd=cwd,env=env,text=True,capture_output=True,timeout=20)
        with log.open('a') as f: f.write(json.dumps(dict(argv=[str(x) for x in args],cwd=str(cwd),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))+'\n')
        if check and p.returncode: raise AssertionError(p.stderr or p.stdout)
        return p
    def cli(*args): return run([binary,'--project-dir',project,*args])
    def inspect(label):
        obj=json.loads(cli('interruption','inspect',order,subject).stdout); js(root/(label+'.json'),obj); return obj
    def wait(predicate, label, timeout=20):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            if process is not None and process.poll() is not None: raise AssertionError('native daemon exited: '+(root/'daemon.stderr').read_text())
            found=predicate()
            if found: return found
            time.sleep(.1)
        raise AssertionError('timeout: '+label)
    def launches(): return [json.loads(line) for line in (root/'sentinel.ndjson').read_text().splitlines()] if (root/'sentinel.ndjson').exists() else []
    def acks():
        p=runtime/'control-ack.ndjson'
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
    def control(command):
        with (runtime/'control.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            with (runtime/'control.ndjson').open('a') as f: f.write(json.dumps(command)+'\n')
        ack=wait(lambda: next((a for a in acks() if a['id']==command['id']),None),'control '+command['id'])
        js(root/(command['id']+'.json'),ack); assert ack['status']=='ok',ack
    def snapshot(): return json.loads((runtime/'state.snapshot.json').read_text())
    def preserved():
        assert (wt/'candidate.txt').read_text()=='uncommitted writer progress\n'
        assert (wt/'new.txt').read_text()=='untracked writer progress\n'
        assert (runtime/'sessions/session-1/events.ndjson').read_bytes()==old_events
    try:
        run(['git','init','-b','main',project])
        run(['git','config','user.name','Native Fixture'],project); run(['git','config','user.email','fixture@example.invalid'],project)
        write(project/'.gitignore','.noodle/\n.worktrees/\n')
        sentinel=root/'fixture-bin/codex'
        write(sentinel,'#!'+sys.executable+'\nimport json,os,pathlib,sys,time\nprompt=sys.stdin.read()\np=pathlib.Path('+repr(str(root/'sentinel.ndjson'))+')\nwith p.open("a") as f: f.write(json.dumps({"pid":os.getpid(),"argv":sys.argv,"cwd":os.getcwd(),"prompt":prompt})+"\\n")\nprint(json.dumps({"type":"thread.started","thread_id":"fixture-"+str(os.getpid())}),flush=True)\nwhile True: time.sleep(1)\n'); sentinel.chmod(0o755)
        if adapter:
            write(sentinel, '#!'+sys.executable+'\n'+"""
import json, os, pathlib, subprocess, sys, time
root = pathlib.Path(ROOT)
prompt = sys.stdin.read()
with (root / 'sentinel.ndjson').open('a') as stream:
    stream.write(json.dumps({'pid': os.getpid(), 'argv': sys.argv, 'cwd': os.getcwd(), 'prompt': prompt})+'\\n')
print(json.dumps({'type': 'thread.started', 'thread_id': 'fixture-'+str(os.getpid())}), flush=True)
deadline = time.monotonic()+20
while not (root / 'allow-outcome').exists():
    if time.monotonic() >= deadline:
        raise SystemExit('fixture exact-receipt readback timeout')
    time.sleep(.05)
receipt = json.loads((root / '07-dispatched.json').read_text())
assert receipt['candidate_unchanged'] is True
assert receipt['successor']['session_id'] == os.environ['NOODLE_SESSION_ID']
envelope = json.loads((pathlib.Path(os.environ['SOODLES_ADMISSION_LAUNCHER']).parent/'envelope.json').read_text())
recovery = envelope['execution']['recovery_context']
dispatched = json.loads((pathlib.Path(recovery['evidence_path'])/'dispatch-result.json').read_text())
assert dispatched == {'custody_sha256': recovery['custody_sha256'], **receipt['successor']}
argv = [envelope['execution']['carrier']['noodle']['path'], '--project-dir', os.environ['NOODLE_PROJECT_DIR'],
        'interruption', 'inspect', os.environ['NOODLE_ORDER_ID'], envelope['repository']+'#'+str(envelope['issue'])]
readback = subprocess.run(argv, capture_output=True, text=True, timeout=20)
(root/'sentinel-native-readback.json').write_text(json.dumps({'argv': argv, 'returncode': readback.returncode,
    'stdout': readback.stdout, 'stderr': readback.stderr}))
assert readback.returncode == 0 and json.loads(readback.stdout)['candidate_unchanged'] is True
pathlib.Path('candidate.txt').write_text('successor writer progress\\n')
argv = [os.environ['SOODLES_ADMISSION_LAUNCHER'], 'stage-outcome', 'completed',
        'Disposable native worker preserved original candidate and recorded the completed outcome.']
result = subprocess.run(argv, capture_output=True, text=True, timeout=20)
(root / 'outcome-process.json').write_text(json.dumps({'argv': argv, 'returncode': result.returncode,
    'stdout': result.stdout, 'stderr': result.stderr}))
assert result.returncode == 0, result.stdout+result.stderr
assert json.loads(result.stdout)['status'] == 'recorded', result.stdout
print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 0, 'output_tokens': 0}}), flush=True)
while True:
    time.sleep(1)
""".replace('ROOT', repr(str(root))))
            for name in supervisor_admission.BUNDLE_PATHS:
                write(project/name, (Path(atom.__file__).parent/name).read_text())
            reader = "import json, os\nfrom pathlib import Path\ndef fetch_issue(repository, number):\n    with Path(os.environ['FIXTURE_PROVIDER_CALLS']).open('a') as stream:\n        stream.write(json.dumps({'repository': repository, 'issue': number})+'\\n')\n    return json.loads(Path(os.environ['FIXTURE_ISSUE_READBACK']).read_text())\n"
            write(project/'github_reader.py', reader)
            for name in ('stage-outcome', 'stage_outcome.py'):
                write(project/name, run(['git', 'show', 'HEAD:'+name], Path(atom.__file__).parent).stdout)
            (project/'stage-outcome').chmod(0o755)
            write(project/'candidate.txt', 'candidate\n')
        for skill in ('execute','schedule'):
            write(project/'.agents/skills'/skill/'SKILL.md',f'---\nname: {skill}\ndescription: Local process fixture only.\nschedule: Local fixture only.\n---\nRemain idle.\n')
        backlog_script=root/'backlog-sync'; write(backlog_script,'#!/bin/sh\nexit 0\n'); backlog_script.chmod(0o755)
        write(project/'.noodle.toml',f'mode = "manual"\n[routing.defaults]\nprovider = "codex"\nmodel = "fixture"\n[agents.codex]\npath = {json.dumps(str(sentinel.parent))}\n[server]\nenabled = false\n[concurrency]\nmax_concurrency = 1\n[adapters.backlog.scripts]\nsync = {json.dumps(str(backlog_script))}\nadd = {json.dumps(str(backlog_script))}\ndone = {json.dumps(str(backlog_script))}\nedit = {json.dumps(str(backlog_script))}\n')
        run(['git','add','.'],project); run(['git','commit','-m','Keep local fixture inputs reproducible'],project)
        run(['git','remote','add','origin','git@github.com:'+repository+'.git'],project)
        base=run(['git','rev-parse','HEAD'],project).stdout.strip()
        run(['git','update-ref','refs/remotes/origin/main',base],project)
        run(['git','symbolic-ref','refs/remotes/origin/HEAD','refs/remotes/origin/main'],project)
        if adapter:
            from test_issue_admission import issue_fixture
            import platform
            issue, _ = issue_fixture()
            contract = admission.parse_contract(issue['body'])
            contract['write_paths'] = ['candidate.txt', 'new.txt']
            issue['body'] = '<!-- soodles:execution-v1 -->\n```json\n'+json.dumps(contract)+'\n```\n<!-- /soodles:execution-v1 -->'
            js(root/'issue-readback.json', issue)
            env.update(FIXTURE_ISSUE_READBACK=str(root/'issue-readback.json'),
                       FIXTURE_PROVIDER_CALLS=str(root/'provider-fixture.ndjson'),
                       NOODLES_TOKEN_COMMAND='printf fixture-installation-token')
            carrier={'platform': platform.system().lower()+'_'+platform.machine().lower(),
                'noodle': {'path': binary, 'sha256': digest},
                'codex': {'path': str(sentinel), 'sha256': atom.digest_file(sentinel), 'model': 'fixture',
                          'argv': ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture']}}
            original=root/'original-bundle'
            supervisor_admission.prepare(issue, carrier, project, original, environ=env, wire_host=True,
                                         task='Retain this disposable candidate and report one completed outcome.')
            original_envelope=json.loads((original/'envelope.json').read_bytes())
        run(['git','worktree','add','-b',wt.name,wt,base],project)
        if not adapter:
            write(wt/'candidate.txt','candidate\n'); run(['git','add','candidate.txt'],wt); run(['git','commit','-m','Keep candidate for interruption recovery'],wt)
        write(wt/'candidate.txt','uncommitted writer progress\n'); write(wt/'new.txt','untracked writer progress\n')
        stamp='2026-10-03T00:00:00Z'; prompt=json.dumps(dict(repository=repository,issue=number,envelope_sha256='a'*64),separators=(',',':'))
        if adapter:
            prompt=json.dumps(execution.projection(admission.validate_issue(issue, original_envelope), atom.digest_file(original/'envelope.json'), 'supervised'))
        stage=dict(stage_index=0,task_key='execute',status='running',provider='codex',model='fixture',runtime='process',skill='execute',prompt=prompt,attempts=[dict(attempt_id=order+'-0-attempt-0',session_id='session-1',status='running',worktree_name=wt.name)])
        canonical=dict(orders={order:dict(order_id=order,status='active',stages=[stage])},pending_reviews={},mode='supervised',schema_version=1,last_event_id='1')
        ledger=[dict(effect_id='dispatch-1',effect=dict(effect_id='dispatch-1',type='dispatch',payload=dict(order_id=order,stage_index=0,attempt_id=order+'-0-attempt-0')),status='pending')]
        js(runtime/'state.snapshot.json',dict(order_revision='a'*32,state=canonical,effect_ledger=ledger,generated_at=stamp))
        projection={k:v for k,v in stage.items() if k not in ('stage_index','attempts')}; projection['status']='active'
        js(runtime/'orders.json',dict(generated_at=stamp,orders=[dict(id=order,status='active',stages=[projection])]))
        js(runtime/'pending-review.json',[])
        child=subprocess.Popen(['git','--version'],stdout=subprocess.DEVNULL); dead_pid=child.pid; assert child.wait()==0
        session=runtime/'sessions/session-1'
        js(session/'process.json',dict(session_id='session-1',pid=dead_pid)); js(session/'meta.json',dict(session_id='session-1',status='exited',runtime='process'))
        js(session/'spawn.json',dict(session_id='session-1',worktree_path=str(wt),provider='codex',model='fixture',runtime='process',retry_count=0))
        write(session/'prompt.txt','[order:'+order+'] Work backlog item '+order+'\n\n'+prompt)
        write(session/'raw.ndjson','{"type":"thread.started","thread_id":"fixture"}\n')
        write(session/'events.ndjson','{"type":"stage_message","session_id":"session-1","payload":{"message":"feedback only"}}\n')
        old_events=(session/'events.ndjson').read_bytes()
        before=(runtime/'state.snapshot.json').read_bytes()
        read=inspect('01-inspect'); assert read['status']=='recoverable',read
        assert before==(runtime/'state.snapshot.json').read_bytes()
        prepared=json.loads(run(read['next']['argv']).stdout); js(root/'02-prepare.json',prepared)
        assert prepared['status']=='prepared' and not prepared['successor'] and not prepared['next']['argv'],prepared
        assert launches()==[]; preserved()
        saved=snapshot()['state']['orders'][order]['stages'][0]
        assert saved['status']=='pending' and len(saved['attempts'])==1 and saved['attempts'][0]['status']=='cancelled' and saved['attempts'][0]['exit_code'] is None
        js(root/'03-prepared-snapshot.json',snapshot())
        if adapter:
            selected=root/'selected-runtime'; selected.mkdir()
            for name in supervisor_admission.BUNDLE_PATHS:
                write(selected/name, reader if name=='github_reader.py' else (Path(atom.__file__).parent/name).read_text())
            recovery={'kind': 'prepublication_interruption',
                'original_envelope': {'path': str(original/'envelope.json'), 'sha256': atom.digest_file(original/'envelope.json')},
                **{key: prepared[key] for key in ('custody', 'custody_sha256', 'evidence_path')}}
            bundle=root/'recovery-bundle'
            bundle_receipt=supervisor_admission.prepare(issue, carrier, project, bundle, environ=env, wire_host=True,
                correction=True, runtime_root=selected, recovery_context=recovery)
            write(project/'.noodle.toml', (bundle/'noodle.toml').read_text())
            env['SOODLES_ADMISSION_LAUNCHER']=str(bundle/'launcher')
            new_envelope=json.loads((bundle/'envelope.json').read_bytes())
            assert (wt/'stage-outcome').read_bytes()==(project/'stage-outcome').read_bytes()
            assert (wt/'stage_outcome.py').read_bytes()==(project/'stage_outcome.py').read_bytes()
        out=(root/'daemon.stdout').open('w'); err=(root/'daemon.stderr').open('w')
        start_argv=bundle_receipt['next']['argv'] if adapter else [binary,'--project-dir',str(project),'start','--mode','manual']
        process=subprocess.Popen(start_argv,env=env,stdout=out,stderr=err,start_new_session=True)
        js(root/'daemon-launch.json',dict(pid=process.pid,argv=start_argv))
        wait(lambda: (runtime/'status.json').exists(),'native status')
        time.sleep(1)
        assert launches()==[], launches()
        read=inspect('04-manual-held'); assert read['status']=='prepared',read
        new_prompt=json.dumps(dict(repository=repository,issue=number,envelope_sha256='b'*64),separators=(',',':'))
        if adapter:
            new_prompt=json.dumps(execution.projection(admission.validate_issue(issue, new_envelope), atom.digest_file(bundle/'envelope.json'), 'supervised'))
        control(dict(id='05-edit-ack',action='edit-item',order_id=order,prompt=new_prompt))
        assert launches()==[]; assert snapshot()['state']['orders'][order]['stages'][0]['prompt']==new_prompt
        control(dict(id='06-mode-ack',action='mode',value='supervised'))
        wait(lambda: len(launches())>0,'native dispatch')
        read=wait(lambda: (r if (r:=json.loads(cli('interruption','inspect',order,subject).stdout))['status']=='dispatched' else None),'successor readback')
        js(root/'07-dispatched.json',read)
        assert read['candidate_unchanged'] and read['successor']['attempt_id']==order+'-0-attempt-1',read
        assert len(launches())==1 and new_prompt in launches()[0]['prompt'],launches()
        assert launches()[0]['cwd']==str(wt)
        preserved()
        time.sleep(1)
        again=inspect('08-repeat-readback'); assert again['successor']==read['successor'] and len(launches())==1
        if adapter:
            control(dict(id='10-hold-ack',action='mode',value='manual'))
            write(root/'allow-outcome', 'exact successor observed\n')
            outcome=wait(lambda: json.loads((root/'outcome-process.json').read_text()) if (root/'outcome-process.json').exists() else None, 'external outcome')
            assert outcome['returncode']==0, outcome
            recorded=json.loads(outcome['stdout'])
            assert recorded['status']=='recorded' and recorded['event']['payload']['outcome']=='completed',recorded
            assert (wt/'stage-outcome').read_bytes()==(project/'stage-outcome').read_bytes()
            assert (wt/'stage_outcome.py').read_bytes()==(project/'stage_outcome.py').read_bytes()
            assert (wt/'candidate.txt').read_text()=='successor writer progress\n'
            assert (wt/'new.txt').read_text()=='untracked writer progress\n'
            assert (runtime/'sessions/session-1/events.ndjson').read_bytes()==old_events
            events=runtime/'sessions'/read['successor']['session_id']/'events.ndjson'
            write(root/'successor-events.ndjson', events.read_text())
            assert len([json.loads(line) for line in events.read_text().splitlines()
                        if json.loads(line).get('payload',{}).get('outcome')=='completed'])==1
            js(root/'11-outcome-readback.json',recorded)
        js(root/'09-dispatched-snapshot.json',snapshot())
        result=dict(status='passed',binary=binary,binary_sha256=digest,prepare_dispatch_count=0,manual_dispatch_count=0,edit_ack='ok',mode_ack='ok',successor_count=1,successor=read['successor'],dirty_preserved=True,original_events_preserved=True,model_calls=0,provider_calls=0)
        if adapter:
            result.update(worker_adapter=str(bundle/'provider/codex'), external_outcome=recorded,
                candidate_outcome_unchanged=True, provider_scope='local fixture Issue reader; no live provider calls',
                provider_fixture_calls=len((root/'provider-fixture.ndjson').read_text().splitlines()))
        js(root/'result.json',result)
        return result
    except Exception as exc:
        js(root/'failure.json',dict(error=str(exc),traceback=traceback.format_exc()))
        raise
    finally:
        if process is not None:
            process.send_signal(signal.SIGTERM) if process.poll() is None else None
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            out.close(); err.close()
            # Only signal processes whose launch was recorded by this fixture sentinel.
            for record in launches():
                pid=record['pid']
                try:
                    command=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
                    if str(root/'fixture-bin/codex') in command: os.kill(pid,signal.SIGTERM)
                except ProcessLookupError: pass
            js(root/'cleanup.json',dict(daemon_pid=process.pid,daemon_returncode=process.returncode,sentinel_pids=[r['pid'] for r in launches()]))
            pids=[process.pid, *[r['pid'] for r in launches()]]
            remaining=[]
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                remaining=[pid for pid in pids if subprocess.run(['ps','-p',str(pid),'-o','pid='],
                    capture_output=True,text=True).stdout.strip()]
                if not remaining: break
                time.sleep(.05)
            js(root/'process-readback.json',{'pids': pids, 'remaining': remaining})
            assert not remaining, remaining


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] in ('--native', '--native-adapter'):
        print(json.dumps(native_control(sys.argv[4], sys.argv[2], sys.argv[3], adapter=sys.argv[1]=='--native-adapter'), indent=2))
    else:
        unittest.main()
