"""Frozen subprocess observer: never imports candidate verdict logic."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {str(p.relative_to(root)): digest(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


CASES = {
    'generic': ('not_applicable', None),
    'ready': ('ready', None),
    'missing_launcher': ('refused', 'scheduler.launcher'),
    'relative_launcher': ('refused', 'scheduler.launcher'),
    'nonexecutable_launcher': ('refused', 'scheduler.launcher'),
    'missing_root': ('refused', 'scheduler.control_root'),
    'foreign_root': ('refused', 'scheduler.control_root'),
    'invalid_session': ('refused', 'scheduler.session_id'),
    'missing_spawn': ('refused', 'scheduler.spawn'),
    'malformed_spawn': ('refused', 'scheduler.spawn'),
    'foreign_session': ('refused', 'scheduler.spawn.session_id'),
    'foreign_skill': ('refused', 'scheduler.spawn.skill'),
    'foreign_worktree': ('refused', 'scheduler.spawn.worktree_path'),
}


def prepare(root, case):
    root.mkdir(parents=True, exist_ok=True)
    session = 'schedule-observation'
    directory = root / '.noodle/sessions' / session
    directory.mkdir(parents=True)
    spawn = {'session_id': session, 'skill': 'schedule', 'worktree_path': str(root)}
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
    env.update(NOODLE_SESSION_ID=session, NOODLE_WORKTREE=str(root))
    launcher = root / 'selected launcher'
    launcher.write_text('#!' + sys.executable + '\nimport json,sys\nfrom pathlib import Path\np=Path(__file__).with_name("launcher-events.json")\ne=json.loads(p.read_text()) if p.exists() else []\ne.append(sys.argv[1:]);p.write_text(json.dumps(e))\nprint(json.dumps({"owner":"Noodle","action":"owned","published":False,"next":{"kind":"input","owner":"Noodle","required":["current_order_and_session_readback"]}}))\n')
    launcher.chmod(0o755)
    env['SOODLES_ADMISSION_LAUNCHER'] = str(launcher)
    if case == 'generic':
        env.pop('NOODLE_SESSION_ID'); env.pop('SOODLES_ADMISSION_LAUNCHER')
    elif case == 'missing_launcher':
        env.pop('SOODLES_ADMISSION_LAUNCHER')
    elif case == 'relative_launcher':
        env['SOODLES_ADMISSION_LAUNCHER'] = 'selected launcher'
    elif case == 'nonexecutable_launcher':
        launcher.chmod(0o644)
    elif case == 'missing_root':
        env.pop('NOODLE_WORKTREE')
    elif case == 'foreign_root':
        env['NOODLE_WORKTREE'] = str(root / 'foreign')
    elif case == 'invalid_session':
        env['NOODLE_SESSION_ID'] = '../foreign'
    elif case == 'foreign_session':
        spawn['session_id'] = 'foreign'
    elif case == 'foreign_skill':
        spawn['skill'] = 'execute'
    elif case == 'foreign_worktree':
        spawn['worktree_path'] = str(root / 'foreign')
    (directory / 'spawn.json').write_text(json.dumps(spawn))
    if case == 'missing_spawn':
        (directory / 'spawn.json').unlink()
    elif case == 'malformed_spawn':
        (directory / 'spawn.json').write_text('[]')
    (root / '.noodle/state.snapshot.json').write_text('{"fixture":"unchanged canonical sentinel"}\n')
    return env, str(launcher)


def classify(row):
    case = row['case']
    action, field = CASES[case]
    value = row.get('output')
    if not isinstance(value, dict) or row.get('unchanged') is not True:
        return False
    if row.get('inspect_launcher_events') != []:
        return False
    if field:
        owner = 'supervisor' if field == 'scheduler.launcher' else 'Noodle'
        nxt = value.get('next', {})
        return (row['exit_code'] == 1 and value.get('status') == 'refused'
                and value.get('invalid', {}).get('field') == field
                and nxt.get('kind') == 'input' and nxt.get('owner') == owner
                and nxt.get('operation') == 'inspect' and 'argv' not in nxt)
    if row['exit_code'] != 0 or value.get('owner') != 'issue.inspect' or value.get('action') != action:
        return False
    if value.get('authorizes_landing') is not False:
        return False
    if case == 'generic':
        return value.get('next', 'missing') is None
    nxt = value.get('next', {})
    return (nxt.get('kind') == 'executable' and nxt.get('owner') == 'supervisor'
            and nxt.get('operation') == 'automatic'
            and nxt.get('argv') == [row['launcher'], 'automatic'])


def cli(subject):
    rows = []
    with tempfile.TemporaryDirectory(prefix='schedule-observer-') as tmp:
        for case in CASES:
            root = Path(tmp) / case
            env, launcher = prepare(root, case)
            before = snapshot(root)
            argv = [sys.executable, '-B', str(subject / 'soodles.py'), 'issue', 'inspect']
            result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=15)
            try:
                output = json.loads(result.stdout)
            except ValueError:
                output = None
            events = root / 'launcher-events.json'
            row = {'case': case, 'argv': argv, 'exit_code': result.returncode,
                   'stdout': result.stdout, 'stderr': result.stderr, 'output': output,
                   'launcher': launcher, 'before': before, 'after': snapshot(root),
                   'unchanged': before == snapshot(root),
                   'inspect_launcher_events': json.loads(events.read_text()) if events.exists() else []}
            row['pass'] = classify(row)
            if case == 'ready' and row['pass']:
                invoked = subprocess.run(output['next']['argv'], cwd=root, env=env,
                                         capture_output=True, text=True, timeout=15)
                row['handoff'] = {'exit_code': invoked.returncode, 'stdout': invoked.stdout,
                                  'stderr': invoked.stderr, 'events': json.loads(events.read_text())}
                row['pass'] = (row['handoff']['events'] == [['automatic']]
                               and invoked.returncode == 0
                               and json.loads(invoked.stdout).get('action') == 'owned')
            rows.append(row)
    return {'scope': 'disposable subprocess fixtures; no real Noodle dispatch or provider writes',
            'authorizes_landing': False, 'rows': rows, 'pass': all(r['pass'] for r in rows),
            'cleanup': not Path(tmp).exists()}


def sensitivity(green):
    import copy
    row = next(r for r in green['rows'] if r['case'] == 'ready')
    controls = []
    for name in ('wrong_argv', 'false_completion', 'mutation', 'missing_events', 'inspect_executes'):
        bad = copy.deepcopy(row)
        if name == 'wrong_argv': bad['output']['next']['argv'][-1] = 'supervised'
        elif name == 'false_completion': bad['output']['action'] = 'resolved'
        elif name == 'mutation': bad['unchanged'] = False
        elif name == 'missing_events': bad.pop('inspect_launcher_events')
        else: bad['inspect_launcher_events'] = [['automatic']]
        controls.append({'control': name, 'rejected': not classify(bad)})
    return controls


if __name__ == '__main__':
    mode, path = sys.argv[1:3]
    if mode == 'cli': result = cli(Path(path).resolve())
    elif mode == 'sensitivity': result = sensitivity(json.loads(Path(path).read_text()))
    else: raise SystemExit('expected cli or sensitivity')
    print(json.dumps(result, indent=2))
