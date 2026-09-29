#!/usr/bin/env python3
"""Supplemental review controls; the original external judge stays unchanged."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ORIGINAL = Path('/Users/neon/.codex/experiments/authorization-oracle-ba7ygaqu')
PINS = {
    'manifest.json': '78867edb4b02eb786996a6f5242c836e15eeae1e122e59b9e59d8e708c8c0c6c',
    'oracle.py': 'f9b5e71a60b43c6402247c0f0277f7737871102f4602a303601d1b1fd2dd6786',
    'guard/sitecustomize.py': 'b51b88dbda2e87bd92214484d89644cd72cfaa934e9f4dee483e40cc14b7c2bd',
}
for name, expected in PINS.items():
    if hashlib.sha256((ORIGINAL / name).read_bytes()).hexdigest() != expected:
        raise SystemExit('changed external oracle dependency: ' + name)
manifest = json.loads((ORIGINAL / 'manifest.json').read_text())
for name, expected in manifest['files'].items():
    if hashlib.sha256((ORIGINAL / name).read_bytes()).hexdigest() != expected:
        raise SystemExit('changed frozen dependency: ' + name)
spec = importlib.util.spec_from_file_location('original_authorization_oracle', ORIGINAL / 'oracle.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)

CASES = ('root_is_git_subdirectory', 'missing_committed_entry', 'nonexecutable_committed_entry')

def one_case(subject, evidence, name):
    directory = evidence / name
    directory.mkdir()
    root, head, selection = original.fixture(directory)
    if name == 'root_is_git_subdirectory':
        selection['control_root'] = str(root / '.github')
    else:
        entry = root / 'issue-atom'
        if name == 'missing_committed_entry':
            entry.unlink()
        else:
            entry.chmod(0o644)
        original.git(root, 'add', '.')
        original.git(root, 'commit', '-m', 'Pin exact missing or unavailable lifecycle entry counterexample')
        new_head = original.git(root, 'rev-parse', 'HEAD')
        selection['issue']['body'] = selection['issue']['body'].replace(head, new_head)
    if original.git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise AssertionError('counterexample must be a clean committed fixture')
    path = directory / 'selection.json'
    path.write_text(json.dumps(selection, indent=2) + '\n')
    digest = original.sha(path.read_bytes())
    output = directory / 'output'
    temp = directory / 'tmp'
    temp.mkdir()
    effects = directory / 'effects.jsonl'
    before = original.snapshot(directory)
    env = {key: value for key, value in os.environ.items()
           if not any(token in key for token in ('TOKEN', 'SECRET', 'CREDENTIAL', 'PASSWORD', 'SOODLES_', 'NOODLE_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ORIGINAL / 'guard'),
               ORACLE_EFFECT_LOG=str(effects), TMPDIR=str(temp))
    argv = [sys.executable, '-B', str(subject / 'supervisor-admission'), 'authorize', str(path), digest, str(output)]
    run = subprocess.run(argv, cwd=directory, env=env, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, timeout=40)
    record = dict(argv=argv, exit_status=run.returncode, stdout=run.stdout, stderr=run.stderr)
    (evidence / (name + '.process.json')).write_text(json.dumps(record, indent=2) + '\n')
    after = original.snapshot(directory)
    errors = []
    try:
        result = json.loads(run.stdout)
    except ValueError:
        result = {}
        errors.append('CLI emitted no typed JSON receipt')
    if run.returncode == 0:
        errors.append('invalid selected root/entry was accepted')
    if result.get('status') != 'refused' or result.get('authorizes_landing') is not False:
        errors.append('missing typed non-authorizing refusal')
    if not isinstance(result.get('invalid'), dict) or not result['invalid'].get('field'):
        errors.append('missing invalid field')
    nxt = result.get('next', {})
    if nxt.get('kind') != 'input' or not nxt.get('owner') or not nxt.get('required'):
        errors.append('missing exact corrected-input continuation')
    if output.exists():
        errors.append('refusal left final output')
    if effects.exists():
        errors.append('external effect was attempted')
    if before != after:
        errors.append('invocation left residue or changed existing input bytes')
    changes = {key: {'before': before.get(key), 'after': after.get(key)}
               for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)}
    return dict(status='FAIL' if errors else 'PASS', errors=errors, exit_status=run.returncode,
                actual_status=result.get('status'), invalid=result.get('invalid'),
                actual_next=result.get('next'), before_sha256=original.sha(json.dumps(before, sort_keys=True).encode()),
                after_sha256=original.sha(json.dumps(after, sort_keys=True).encode()), changes=changes,
                clean_committed_fixture=True, selected_root=selection['control_root'],
                committed_head=original.git(root, 'rev-parse', 'HEAD'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('subject', type=Path)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    subject, evidence = args.subject.resolve(), args.evidence.absolute()
    if evidence.exists() or not evidence.parent.is_dir():
        raise SystemExit('evidence must be new with an existing parent')
    evidence.mkdir()
    results = {}
    for name in CASES:
        try:
            results[name] = one_case(subject, evidence, name)
        except Exception as error:
            results[name] = dict(status='FAIL', error=type(error).__name__ + ': ' + str(error))
    report = dict(schema=1, kind='supplemental_source_review_discriminator', original_oracle_pins=PINS,
                  subject=str(subject), subject_head=original.git(subject, 'rev-parse', 'HEAD'),
                  status='GREEN' if all(item['status'] == 'PASS' for item in results.values()) else 'RED',
                  results=results, authorizes_landing=False,
                  scope='Three nearest root/entry counterexamples; original behavioral adoption conditions unchanged')
    (evidence / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'GREEN' else 1

if __name__ == '__main__':
    raise SystemExit(main())
