"""Exercise the production revision owner with a pinned native process and local workers."""
import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SOURCE = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(SOURCE), str(SOURCE / 'tests')]
import issue_admission as admission
import issue_atom as atom
import issue_execution as execution
import supervisor_admission as supervisor
from test_interruption_recovery import native_control

ACCEPTED = Path('/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/prepublication-base-owner/native-accepted.json')
ACCEPTED_SHA = '175584927cd3ff119c640645072411951ccd05c787fbecd03b82535e9ea4906a'
BASE = 'a2e6f36bdffa893c6d9d31ad31b4880551634d80'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return ref(path)


def wait(predicate, label):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(.05)
    raise AssertionError('timeout: ' + label)


def continuation(stop_after, base_only=False):
    def drive(root, project, wt, original_bundle, selected, issue, carrier, env):
        runtime = project / '.noodle'
        issue = {**issue, 'title': 'Disposable native revision'}
        def git(*argv, cwd=project):
            result = subprocess.run(['git', *map(str, argv)], cwd=cwd, env=env, text=True, capture_output=True)
            with (root / 'owner-commands.ndjson').open('a') as stream:
                stream.write(json.dumps({'argv': ['git', *map(str, argv)], 'cwd': str(cwd), 'exit': result.returncode,
                                         'stdout': result.stdout, 'stderr': result.stderr}) + '\n')
            assert result.returncode == 0, result.stderr
            return result.stdout.strip()
        def snapshot():
            return json.loads((runtime / 'state.snapshot.json').read_text())['state']
        original = json.loads((original_bundle / 'envelope.json').read_text())
        order = original['execution']['order_id']
        old_stage = copy.deepcopy(snapshot()['orders'][order]['stages'][0])
        terminal = execution.blocked_outcome(original, execution.read_owner(original), completed=True)
        candidate = git('rev-parse', 'HEAD', cwd=wt)
        tree = git('rev-parse', 'HEAD^{tree}', cwd=wt)
        assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=wt) == ''
        git('rm', '--cached', '.noodle.toml')
        with (project / '.gitignore').open('a') as ignored:
            ignored.write('.noodle.toml\n')
        git('add', '.gitignore')
        (project / 'target.txt').write_text('selected provider target\n')
        git('add', 'target.txt'); git('commit', '-m', 'Advance disposable base for revision')
        target = git('rev-parse', 'HEAD')
        git('update-ref', 'refs/remotes/origin/main', target)
        for name in set(atom.LIFECYCLE_FILES) | set(supervisor.BUNDLE_PATHS):
            if name == 'github_reader.py':
                continue
            path = selected / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((SOURCE / name).read_bytes())
            path.chmod((SOURCE / name).stat().st_mode)
        hashes = {name: sha(selected / name) for name in atom.LIFECYCLE_FILES}
        lifecycle = {**ref(selected / 'issue-atom'), 'source_sha256': atom.digest_bytes(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode())}
        authorization = {'control_root': str(project), 'repository': original['repository'], 'base_head': original['base_head'],
            'task': original['execution']['task'], 'issue': issue, 'carrier': {k: v for k, v in carrier.items() if k != 'noodle'},
            'noodle': carrier['noodle'], 'lifecycle_owner': lifecycle, 'landing_owner': {'path': str(root / 'external-judge' / 'landing.py')}}
        auth_ref = save(root / 'authorization.json', authorization)
        output = root / 'revision'
        provider_ref = save(root / 'provider.json', {'repository': {'full_name': original['repository'], 'default_branch': 'main'},
            'branch': {'name': 'main', 'commit': {'sha': target}}})
        selection = {'schema': 2, 'type': 'base_advance', 'reason': 'Integrate exact disposable provider target.',
            'evidence': ref(root / '11-outcome-readback.json'), 'lifecycle_owner': lifecycle,
            'candidate_head': candidate, 'candidate_tree': tree, 'original_envelope': ref(original_bundle / 'envelope.json'),
            'order_id': order, 'stage_index': 0, 'terminal_session': terminal['session_id'],
            'before_contract': admission.parse_contract(issue['body']), 'target_base': target, 'references': [],
            'provider_readback': provider_ref, 'native_acceptance': ref(ACCEPTED)}
        packet_ref = save(output / 'selection.json', {'schema': 1, 'authorization': auth_ref, 'selection': selection, 'output': str(output)})
        daemon = json.loads((root / 'daemon-launch.json').read_text())
        prepared = json.loads((original_bundle / 'prepared.json').read_text())
        config = (project / '.noodle.toml').read_bytes()
        prior_start = {'status': 'started', 'pid': daemon['pid'], 'argv': daemon['argv'],
            'process_argv': atom.noodle_process_argv(authorization, prepared),
            'config_sha256': sha(project / '.noodle.toml'), 'original_config': base64.b64encode(config).decode()}
        state = {'authorization_sha256': auth_ref['sha256'], 'phase': 'execution', 'issue': {'number': issue['number']},
            'publication': None, 'writes': {}, 'noodle_start': prior_start, 'repair': {'history': []},
            'scope_amendment': {'selection': packet_ref, 'prior': {'envelope': ref(original_bundle / 'envelope.json'),
                'stage': old_stage, 'blocked': terminal, 'noodle_start': prior_start}}}
        paths = {'state': root / 'checkpoint.json', 'envelope': original_bundle / 'envelope.json', 'directory': root}
        save(paths['state'], state)
        current_issue = copy.deepcopy(issue)
        class Provider:
            def issue(self, number):
                assert number == current_issue['number']
                return copy.deepcopy(current_issue)
            def repository_info(self):
                return {'full_name': original['repository'], 'default_branch': 'main'}
            def branch_info(self, branch):
                assert branch == 'main'
                return {'name': branch, 'commit': {'sha': target}}
            def update_issue_body(self, number, body):
                assert number == current_issue['number']
                current_issue['body'] = body
                current_issue['updated_at'] = '2026-10-03T01:00:00Z'
                save(root / 'issue-readback.json', current_issue)
                raise atom.MutationUnknown('Fixture lost the successful local Issue patch response.')
        provider = Provider()
        before_launches = len((root / 'sentinel.ndjson').read_text().splitlines())
        starts = []
        def advance(module=atom):
            before = copy.deepcopy(state)
            started = time.monotonic()
            try:
                result = module.advance_scope_amendment(authorization, paths, state, provider, env)
            except Exception as error:
                with (root / 'owner-calls.ndjson').open('a') as stream:
                    stream.write(json.dumps({'elapsed_s': time.monotonic()-started, 'error': str(error),
                                             'before': before, 'after': state})+'\n')
                raise
            with (root / 'owner-calls.ndjson').open('a') as stream:
                stream.write(json.dumps({'elapsed_s': time.monotonic()-started, 'result': result, 'before': before, 'after': state})+'\n')
            if result.get('action') == 'started':
                starts.append(state['noodle_start']['pid'])
                expected = ' '.join(state['noodle_start']['process_argv'])
                wait(lambda: subprocess.run(['ps', '-p', str(state['noodle_start']['pid']), '-o', 'command='], capture_output=True, text=True).stdout.strip() == expected, 'native launcher exec')
                wait(lambda: atom.observe_prior_loop(authorization, state) == 'running', 'owner native lock')
            return result
        def acks():
            path = runtime / 'control-ack.ndjson'
            return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        def stop():
            pid = state['noodle_start']['pid']
            os.kill(pid, signal.SIGTERM)
            wait(lambda: not subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout.strip(), 'native process exit')
            assert atom.observe_prior_loop(authorization, state) == 'stopped'
        session_root = runtime / 'sessions' / terminal['session_id']
        session_files = [session_root / name for name in ('events.ndjson', 'prompt.txt', 'process.json', 'spawn.json')]
        try:
            assert advance()['action'] == 'scope_issue_readback_pending'
            assert advance()['action'] == 'scope_admission_prepared'
            code = root / 'fixture-code'
            code.mkdir()
            for name in ('test_admission_revision.py', 'test_issue_admission.py'):
                (code / name).write_bytes((SOURCE / 'tests' / name).read_bytes())
            env['PYTHONPATH'] = str(code) + os.pathsep + str(SOURCE)
            env['SOODLES_ADMISSION_LAUNCHER'] = str(output / 'admission' / 'launcher')
            assert advance()['action'] == 'started'
            for control_name in ('scope_request', 'scope_edit', 'scope_requeue'):
                result = advance()
                assert result['action'].endswith('pending'), result
                command = state[control_name]
                wait(lambda: next((ack for ack in acks() if ack['id'] == command['id']), None), control_name)
                assert len((root / 'sentinel.ndjson').read_text().splitlines()) == before_launches
                if control_name == stop_after:
                    break
            before_stop = {'snapshot': snapshot(), 'start': copy.deepcopy(state['noodle_start']),
                           'session_hashes': [ref(path) for path in session_files], 'acks': acks(), 'state': copy.deepcopy(state)}
            save(root / 'before-stop.json', before_stop)
            stop()
            save(root / 'stopped.json', {'snapshot': snapshot(), 'process': atom.observe_prior_loop(authorization, state), 'state': state})
            if base_only:
                base_path = root / 'base_issue_atom.py'
                base_path.write_bytes(subprocess.check_output(['git', 'show', BASE + ':issue_atom.py'], cwd=SOURCE))
                spec = importlib.util.spec_from_file_location('base_issue_atom', base_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                try:
                    advance(module)
                except module.AtomRefusal as error:
                    assert error.invalid['field'] == 'scope.process', vars(error)
                    result = {'status': 'observed_refusal', 'field': error.invalid['field'], 'message': str(error), 'base_source': ref(base_path)}
                    save(root / 'nearest-refusal.json', result)
                    return result
                raise AssertionError('base unexpectedly continued stopped owner')
            result = advance()
            assert result['action'] == 'started', result
            assert len(starts) == 2 and starts[0] != starts[1]
            save(root / 'held-restart.json', {'snapshot': snapshot(), 'start': state['noodle_start'], 'acks': acks(), 'state': state})
            assert len((root / 'sentinel.ndjson').read_text().splitlines()) == before_launches
            assert all(sha(item['path']) == item['sha256'] for item in before_stop['session_hashes'])
            until = time.monotonic() + 30
            while time.monotonic() < until:
                result = advance()
                if result['action'] == 'scope_released':
                    break
                time.sleep(.1)
            else:
                raise AssertionError('revision owner did not release')
            wait(lambda: (root / 'revision-outcome.json').exists(), 'successor terminal outcome')
            outcome = json.loads((root / 'revision-outcome.json').read_text())
            assert outcome['returncode'] == 0, outcome
            wait(lambda: snapshot()['orders'][order]['stages'][0]['status'] == 'review', 'successor native review')
            stage = snapshot()['orders'][order]['stages'][0]
            expected = state['scope_amendment']['requeued_attempts']
            assert stage['attempts'][:-1] == expected
            assert len(stage['attempts']) == len(old_stage['attempts']) + 1
            assert len((root / 'sentinel.ndjson').read_text().splitlines()) == before_launches + 1
            assert all(sha(item['path']) == item['sha256'] for item in before_stop['session_hashes'])
            own_ids = [state[key]['id'] for key in ('scope_request', 'scope_edit', 'scope_requeue', 'scope_release')]
            assert all(len([ack for ack in acks() if ack['id'] == control_id]) == 1 for control_id in own_ids)
            result = {'status': 'passed', 'stop_after': stop_after, 'owner_starts': starts, 'successor_count': 1,
                      'prior_session_hashes_preserved': True, 'prior_attempt_count': len(old_stage['attempts']),
                      'final_attempt_count': len(stage['attempts']), 'snapshot': snapshot(), 'state': state,
                      'model_calls': 0, 'live_provider_calls': 0, 'authorizes_landing': False}
            save(root / 'owner-result.json', result)
            return result
        finally:
            cleanup = []
            for pid in starts:
                command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout.strip()
                if command:
                    assert (carrier['noodle']['path'] in command and str(project) in command) or str(output / 'admission' / 'start-noodle') in command, command
                    os.kill(pid, signal.SIGTERM)
                    wait(lambda: not subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout.strip(), 'owner cleanup')
                cleanup.append({'pid': pid, 'absent': True})
            save(root / 'owner-cleanup.json', cleanup)
    return drive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--stop-after', choices=('request', 'edit', 'requeue'), default='request')
    parser.add_argument('--base-only', action='store_true')
    args = parser.parse_args()
    assert sha(ACCEPTED) == ACCEPTED_SHA
    accepted = json.loads(ACCEPTED.read_text())
    for key in ('binary', 'acceptance', 'interface'):
        assert sha(accepted[key]['path']) == accepted[key]['sha256']
    identity_root = Path(str(args.output.resolve()) + '.inputs')
    identity_root.mkdir()
    source_refs = []
    for name in ('issue_atom.py', 'issue_execution.py', 'tests/test_admission_revision.py', 'tests/test_interruption_recovery.py', 'tests/test_issue_admission.py', 'docs/experiments/failed-order-restart/observer.py'):
        original_path = SOURCE / name
        saved_path = identity_root / name
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        saved_path.write_bytes(original_path.read_bytes())
        source_refs.append({'source': str(original_path), 'saved': ref(saved_path)})
    save(identity_root / 'manifest.json', {'sources': source_refs, 'accepted': ref(ACCEPTED)})
    os.environ['FIXTURE_NATIVE_ACCEPTED'] = str(ACCEPTED)
    result = native_control(args.output, accepted['binary']['path'], accepted['binary']['sha256'], adapter=True,
                            completed_review=continuation('scope_' + args.stop_after, args.base_only))
    print(json.dumps({'status': result['revision']['status'], 'output': str(args.output), 'authorizes_landing': False}))


if __name__ == '__main__':
    main()
