"""Read-only process, lock and bundle observation for the selected local atom."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tomllib


AUTH = Path('/Users/neon/.codex/experiments/authorization-reentry-enjygyfl/admission/authorization.json')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    auth = json.loads(AUTH.read_text())
    state = json.loads(AUTH.with_name(AUTH.name + '.state.json').read_text())
    root = Path(auth['control_root'])
    start = state['noodle_start']
    pid = start['pid']
    process = subprocess.run(['ps', '-p', str(pid), '-o', 'command='],
                             capture_output=True, text=True)
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        group_present = False
    except PermissionError:
        group_present = None
    else:
        group_present = True
    logical = subprocess.run([auth['noodle']['path'], '--project-dir', str(root), 'status'],
                             capture_output=True, text=True)
    config_path = root / '.noodle.toml'
    config = tomllib.loads(config_path.read_text())
    lock_path = root / '.noodle/noodle.lock'
    with lock_path.open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_held = True
        else:
            lock_held = False
    bundle = AUTH.parent / (AUTH.name + '.d/admission')
    paths = [Path(config['agents']['codex']['path']),
             *(Path(shlex.split(command)[0]) for command in
               config['adapters']['backlog']['scripts'].values())]
    result = {
        'scope': 'read-only local owner liveness and installed bundle identity',
        'authorization_sha256': sha256(AUTH),
        'phase': state['phase'],
        'recorded_pid': pid,
        'ps_exit_status': process.returncode,
        'ps_command': process.stdout.strip() or None,
        'process_group_present': group_present,
        'noodle_status_exit': logical.returncode,
        'noodle_status': logical.stdout.strip(),
        'noodle_lock_held': lock_held,
        'installed_config_sha256': sha256(config_path),
        'matches_recorded_config': sha256(config_path) == start['config_sha256'],
        'installed_adapter_paths_all_in_prior_bundle': all(
            path.resolve().is_relative_to(bundle.resolve()) for path in paths),
        'installed_envelope_sha256': sha256(bundle / 'envelope.json'),
        'matches_recorded_envelope': sha256(bundle / 'envelope.json') == state['envelope_sha256'],
        'authorizes_landing': False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
