"""Bounded recorder for disposable native consumers; it never selects a transition."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append(root, event):
    with (root / 'events.jsonl').open('a') as stream:
        stream.write(json.dumps(event) + '\n')


def execute(source, args):
    argv = [sys.executable, '-B', str(source / 'soodles.py'), 'landing', *map(str, args)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30,
                            env={k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ})
    return argv, result


def prepare(root, source, instructions):
    root, source = Path(root).resolve(), Path(source).resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / 'state').mkdir()
    (root / 'instructions').mkdir()
    for name, content in instructions.items():
        (root / 'instructions' / name).write_text(content)
    _, result = execute(source, ['identity'])
    identity = json.loads(result.stdout)['verifier_sha256']
    repo = {'full_name': 'ed3c/soodles'}
    claim = {'repository': 'ed3c/soodles', 'issue': 1, 'pr': 2, 'head': 'a'*40,
             'tree': 'b'*40, 'base_head': 'c'*40, 'run_id': 10, 'run_attempt': 1,
             'worktree': 'fixture', 'verifier_sha256': identity}
    snapshot = {'pr': {'number': 2, 'html_url': 'https://github.com/ed3c/soodles/pull/2',
                      'body': 'Refs ed3c/soodles#1', 'head': {'repo': repo, 'sha': 'a'*40, 'ref': 'fixture'},
                      'base': {'repo': repo, 'sha': 'c'*40, 'ref': 'main'}, 'merged': False,
                      'state': 'open', 'draft': False, 'mergeable': True},
                'issue': {'number': 1, 'html_url': 'https://github.com/ed3c/soodles/issues/1', 'state': 'open'},
                'run': {'id': 10, 'run_attempt': 1, 'repository': repo, 'head_repository': repo,
                        'head_sha': 'a'*40, 'event': 'pull_request', 'path': '.github/workflows/runtime.yml',
                        'status': 'completed', 'conclusion': 'success'},
                'commit': {'sha': 'a'*40, 'tree': {'sha': 'b'*40}},
                'jobs': {'total_count': 1, 'jobs': [{'id': 11, 'name': 'runtime-evidence', 'run_id': 10,
                         'head_sha': 'a'*40, 'status': 'completed', 'conclusion': 'success',
                         'steps': [{'name': 'Canonical acceptance on the exact candidate head',
                                    'status': 'completed', 'conclusion': 'success'}]}]},
                'branch': {'name': 'main', 'commit': {'sha': 'c'*40}}}
    packet = {'scope': 'synthetic provider fixtures; no transport', 'publisher': str(source),
              'publisher_identity': identity, 'python': sys.executable, 'cases': {},
              'instructions': [str(root / 'instructions' / name) for name in instructions],
              'transport_events': [], 'model_identity': 'UNKNOWN', 'setup': []}
    providers = {}
    for case in ('prepared', 'offered', 'recovery'):
        directory = root / 'state' / case
        directory.mkdir()
        cp, rp, cf = directory / 'checkpoint.json', directory / 'readback.json', directory / 'claim.json'
        dump(cf, claim); dump(rp, snapshot)
        projection = None
        for args in (['start', cf, rp, cp], ['advance', cp, rp]):
            argv, result = execute(source, args)
            packet['setup'].append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise RuntimeError(result.stderr)
            projection = json.loads(result.stdout)
        if case != 'prepared':
            for operation in ('dispatch', 'advance'):
                argv, result = execute(source, [operation, cp, rp])
                packet['setup'].append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
                if result.returncode:
                    raise RuntimeError(result.stderr)
                projection = json.loads(result.stdout)
        missing = json.loads(json.dumps(snapshot))
        missing['pr'].update(merged=True, state='closed', merged_at='2026-09-20T00:00:00Z', merge_commit_sha='d'*40)
        corrected = json.loads(json.dumps(missing))
        corrected['merge_commit'] = {'sha': 'd'*40, 'tree': {'sha': 'b'*40},
                                    'parents': [{'sha': 'c'*40}, {'sha': 'a'*40}]}
        providers[case] = [missing, corrected] if case == 'recovery' else [snapshot]
        packet['cases'][case] = {'checkpoint': str(cp), 'readback': str(rp),
                                'initial_owner_projection': projection,
                                'initial_checkpoint': json.loads(cp.read_text())}
    dump(root / 'setup.json', packet.pop('setup'))
    dump(root / 'packet.json', packet)
    dump(root / 'fixture-provider.json', providers)
    dump(root / 'driver-state.json', {'refreshes': {}, 'current': {
        case: data['initial_owner_projection'] for case, data in packet['cases'].items()}})
    (root / 'events.jsonl').touch()


def main():
    root = Path(sys.argv[1]).resolve()
    operation = sys.argv[2]
    packet = json.loads((root / 'packet.json').read_text())
    state = json.loads((root / 'driver-state.json').read_text())
    if operation == 'read':
        items = []
        for name in packet['instructions']:
            path = Path(name)
            items.append({'path': name, 'sha256': sha(path), 'content': path.read_text()})
        append(root, {'kind': 'instruction_read', 'files': items})
        print(json.dumps({'instructions': items, 'packet': packet}, indent=2))
        return
    case = sys.argv[3]
    data = packet['cases'][case]
    if operation == 'refresh':
        stage = state['refreshes'].get(case, 0)
        frames = json.loads((root / 'fixture-provider.json').read_text())[case]
        if stage >= len(frames):
            raise ValueError('No further fixture readback admitted')
        value = frames[stage]
        value['fixture_observed_at_ns'] = time.time_ns()
        dump(Path(data['readback']), value)
        state['refreshes'][case] = stage + 1
        dump(root / 'driver-state.json', state)
        event = {'kind': 'fixture_provider_readback', 'case': case, 'stage': stage,
                 'path': data['readback'], 'sha256': sha(Path(data['readback'])), 'snapshot': value,
                 'network_transport': False}
        append(root, event)
        print(json.dumps(event, indent=2))
        return
    if operation != 'call':
        raise ValueError('Supported operations: read, refresh CASE, call CASE JSON_ARGV')
    argv = json.loads(sys.argv[4])
    append(root, {'kind': 'submitted_argv', 'case': case, 'argv': argv})
    prefix = [sys.executable, '-B', str(Path(packet['publisher']) / 'soodles.py'), 'landing']
    if not isinstance(argv, list) or argv[:4] != prefix or not all(isinstance(v, str) for v in argv):
        raise ValueError('Only selected publisher landing argv admitted')
    if len(argv) < 5 or argv[4] not in ('advance', 'dispatch'):
        raise ValueError('Only existing advance/dispatch transitions admitted')
    if argv[5:] == ['--help']:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        event = {'kind': 'help_call', 'case': case, 'argv': argv, 'exit': result.returncode,
                 'stdout': result.stdout, 'stderr': result.stderr}
        append(root, event)
        print(json.dumps(event, indent=2))
        return
    if argv[5:] != [data['checkpoint'], data['readback']]:
        raise ValueError('Only this case checkpoint/readback admitted')
    if not state['refreshes'].get(case):
        raise ValueError('Obtain the current fixture provider readback first')
    before = Path(data['checkpoint']).read_text()
    projection = state['current'][case]
    started = time.monotonic_ns()
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30,
                            env={k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ})
    elapsed = time.monotonic_ns() - started
    try:
        output = json.loads(result.stdout)
    except ValueError:
        output = None
    event = {'kind': 'owner_call', 'case': case, 'argv': argv, 'exit': result.returncode,
             'stdout': result.stdout, 'stderr': result.stderr, 'elapsed_ns': elapsed,
             'before': json.loads(before), 'after': json.loads(Path(data['checkpoint']).read_text()),
             'prior_projection': projection, 'output': output,
             'copied_current_argv': argv == (projection.get('next') or {}).get('argv')}
    append(root, event)
    if output is not None:
        state['current'][case] = output
        dump(root / 'driver-state.json', state)
    print(json.dumps(event, indent=2))


if __name__ == '__main__':
    main()
