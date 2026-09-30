#!/usr/bin/env python3
"""Live preparation controls adapted from the archived materialization oracle.

Historical oracle bytes remain unchanged. This suite verifies the current
three-file contract and is not the selected behavior evaluator.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1] / 'docs/experiments/authorization-materialization/evaluator'
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'frozen'))
import issue_atom as validator

BASE = '7e602dbe3fd4db670b15ef0267025e6c1dfffd4d'
WORKFLOW = {'path': '.github/workflows/runtime.yml', 'job': 'runtime-evidence',
            'step': 'Canonical acceptance on the exact candidate head'}
CASES = ('schema2', 'schema3', 'numbered_config', 'dirty', 'wrong_base', 'wrong_repository',
         'wrong_origin', 'selection_digest', 'missing_selection', 'duplicate_key',
         'extra_field', 'missing_field', 'carrier_noodle_bytes', 'carrier_codex_bytes',
         'carrier_platform', 'carrier_argv', 'publisher_bytes', 'publisher_bundle_bytes',
         'instruction_parent', 'instruction_absolute', 'instruction_missing',
         'instruction_symlink', 'instruction_duplicate', 'existing_output',
         'inside_root_output', 'relative_output', 'missing_output_parent', 'wrong_workflow')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE).decode().strip()

def snapshot(root):
    return {str(p.relative_to(root)): ('symlink:' + os.readlink(p) if p.is_symlink()
            else sha(p.read_bytes())) for p in root.rglob('*') if p.is_file() or p.is_symlink()}

def fixture(directory):
    root = directory / 'project'
    root.mkdir()
    git(root, 'init', '-b', 'main')
    git(root, 'config', 'user.name', 'External authorization oracle')
    git(root, 'config', 'user.email', 'oracle@example.invalid')
    git(root, 'remote', 'add', 'origin', 'https://github.com/ed3c/soodles.git')
    (root / '.gitignore').write_text('.noodle/\n.noodle.toml\n')
    (root / 'AGENTS.md').write_text('Only the exact supplied task is admitted.\n')
    (root / 'issue-atom').write_text('#!/bin/sh\nexit 97\n')
    (root / 'issue-atom').chmod(0o755)
    (root / 'linked.md').symlink_to('AGENTS.md')
    wf = root / WORKFLOW['path']
    wf.parent.mkdir(parents=True)
    wf.write_bytes((HERE / 'frozen' / WORKFLOW['path']).read_bytes())
    git(root, 'add', '.')
    git(root, 'commit', '-m', 'Pin isolated authorization fixture')
    head = git(root, 'rev-parse', 'HEAD')
    contract = dict(schema=3, trigger='fixture', source='fixture', owner='fixture owner',
                    changes=['fixture'], write_paths=['allowed.py'], behavior=['fixture'],
                    defect_controls=['fixture'], non_cases=['fixture'], dependencies=[],
                    acceptance='fixture', delivery='fixture', reconciliation='fixture',
                    feature_scope='fixture', required_paths=['allowed.py'], evidence_manifest='allowed.py',
                    base_head=head, frozen_paths=[dict(path='allowed.py', revision='head', sha256='a' * 64)])
    body = '<!-- soodles:execution-v1 -->\n```json\n' + json.dumps(contract) + '\n```\n<!-- /soodles:execution-v1 -->'
    identities = {}
    for name in ('noodle', 'codex'):
        path = directory / name
        path.write_text('#!/bin/sh\nexit 98\n')
        path.chmod(0o755)
        identities[name] = dict(path=str(path), sha256=sha(path.read_bytes()))
    publisher = directory / 'publisher'
    hashes = {}
    for rel in validator.OWNER_FILES:
        path = publisher / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('external selected bytes: ' + rel + '\n').encode())
        hashes[rel] = sha(path.read_bytes())
    owner = dict(path=str(publisher / 'soodles.py'), sha256=hashes['soodles.py'],
                 verifier_sha256=sha(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()))
    carrier = dict(platform=platform.system().lower() + '_' + platform.machine().lower(),
                   noodle=identities['noodle'], codex={**identities['codex'], 'model': 'fixture-model',
                   'argv': ['exec', '--skip-git-repo-check', '--json', '--model', 'fixture-model']})
    selection = dict(schema=1, repository='ed3c/soodles', control_root=str(root),
                     issue=dict(title='External fixture atom', body=body), task='Execute this exact isolated fixture.',
                     carrier=carrier, landing_owner=owner, instruction_paths=[])
    return root, head, selection

def check(condition, detail):
    if not condition:
        raise AssertionError(detail)

def run_case(subject, evidence, name):
    directory = evidence / name
    directory.mkdir()
    root, head, selection = fixture(directory)
    selection_path = directory / 'selection.json'
    output = directory / 'output'
    accepted = name in ('schema2', 'schema3', 'numbered_config')
    if name == 'schema3': selection['instruction_paths'] = ['AGENTS.md', '.github/workflows/runtime.yml']
    elif name == 'numbered_config':
        selection['issue']['number'] = 991
        (root / '.noodle.toml').write_text('mode = "supervised"\n')
    elif name == 'dirty': (root / 'AGENTS.md').write_text('dirty\n')
    elif name == 'wrong_base': selection['issue']['body'] = selection['issue']['body'].replace(head, '1' * 40)
    elif name == 'wrong_repository': selection['repository'] = 'ed3c/other'
    elif name == 'wrong_origin': git(root, 'remote', 'set-url', 'origin', 'https://github.com/ed3c/other.git')
    elif name == 'extra_field': selection['unselected'] = True
    elif name == 'missing_field': del selection['landing_owner']
    elif name in ('carrier_noodle_bytes', 'carrier_codex_bytes'):
        binary = 'noodle' if name == 'carrier_noodle_bytes' else 'codex'
        Path(selection['carrier'][binary]['path']).write_text('#!/bin/sh\nexit 99\n')
    elif name == 'carrier_platform': selection['carrier']['platform'] = 'unselected_host'
    elif name == 'carrier_argv': selection['carrier']['codex']['argv'] = []
    elif name == 'publisher_bytes': Path(selection['landing_owner']['path']).write_text('changed publisher')
    elif name == 'publisher_bundle_bytes': (directory / 'publisher/landing.py').write_text('changed owner dependency')
    elif name == 'instruction_parent': selection['instruction_paths'] = ['../selection.json']
    elif name == 'instruction_absolute': selection['instruction_paths'] = [str(root / 'AGENTS.md')]
    elif name == 'instruction_missing': selection['instruction_paths'] = ['absent.md']
    elif name == 'instruction_symlink': selection['instruction_paths'] = ['linked.md']
    elif name == 'instruction_duplicate': selection['instruction_paths'] = ['AGENTS.md', 'AGENTS.md']
    elif name == 'existing_output':
        output.mkdir()
        (output / 'untouched').write_text('preserve existing output\n')
    elif name == 'inside_root_output': output = root / 'output'
    elif name == 'relative_output': output = Path('relative-output')
    elif name == 'missing_output_parent': output = directory / 'absent-parent/output'
    elif name == 'wrong_workflow':
        (root / WORKFLOW['path']).write_text('name: different\n')
        git(root, 'add', '.')
        git(root, 'commit', '-m', 'Change workflow to reject unbound runtime identity')
        new_head = git(root, 'rev-parse', 'HEAD')
        selection['issue']['body'] = selection['issue']['body'].replace(head, new_head)
    raw = (json.dumps(selection, indent=2) + '\n').encode()
    if name == 'duplicate_key': raw = raw.replace(b'"schema": 1', b'"schema": 1, "schema": 1', 1)
    selection_path.write_bytes(raw)
    expected = sha(raw)
    if name == 'selection_digest': selection_path.write_bytes(raw + b' ')
    elif name == 'missing_selection': selection_path.unlink()
    temp = directory / 'tmp'
    temp.mkdir()
    effect_log = directory / 'effects.jsonl'
    before = snapshot(directory)
    env = {key: value for key, value in os.environ.items()
           if not any(token in key for token in ('TOKEN', 'SECRET', 'CREDENTIAL', 'PASSWORD', 'SOODLES_', 'NOODLE_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(HERE / 'guard'),
               ORACLE_EFFECT_LOG=str(effect_log), TMPDIR=str(temp))
    argv = [sys.executable, '-B', str(subject / 'supervisor-admission'), 'authorize', str(selection_path), expected, str(output)]
    run = subprocess.run(argv, cwd=directory, env=env, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, timeout=40)
    record = dict(argv=argv, exit_status=run.returncode, stdout=run.stdout, stderr=run.stderr)
    (evidence / (name + '.process.json')).write_text(json.dumps(record, indent=2) + '\n')
    check(not effect_log.exists(), 'non-Git external effect attempted')
    after = snapshot(directory)
    try:
        result = json.loads(run.stdout)
    except ValueError:
        raise AssertionError('CLI did not emit a JSON receipt') from None
    if not accepted:
        check(run.returncode != 0, 'invalid input accepted')
        check(result.get('status') == 'refused' and result.get('authorizes_landing') is False, 'untyped refusal')
        check(isinstance(result.get('invalid'), dict) and bool(result['invalid'].get('field')), 'missing invalid field')
        nxt = result.get('next', {})
        check(nxt.get('kind') == 'input' and bool(nxt.get('owner')) and bool(nxt.get('required')), 'missing corrected input continuation')
        check(before == after, 'refusal left residue or changed existing bytes')
        return dict(status='PASS', classification='typed_refusal', invalid=result['invalid'])
    check(run.returncode == 0, 'valid selection refused')
    check(output.is_dir(), 'missing output directory')
    check(set(p.name for p in output.iterdir()) == {'authorization.json', 'prepared.json', 'selection-binding.json'}, 'unexpected output files/state')
    auth_path = output / 'authorization.json'
    digest = sha(auth_path.read_bytes())
    binding_path = output / 'selection-binding.json'
    check(not binding_path.is_symlink() and binding_path.is_file(), 'binding must be a regular file')
    check(json.loads(binding_path.read_text()) == {
        'schema': 1, 'selection_sha256': expected, 'authorization_sha256': digest,
        'prepared_sha256': sha((output / 'prepared.json').read_bytes()),
        'output': str(output)}, 'selection binding differs from exact selected/output bytes')
    auth, actual = validator.validate_authorization(str(auth_path), digest)
    expected_auth = dict(schema_version=3 if selection['instruction_paths'] else 2, owner='external-supervisor',
        repository=selection['repository'], control_root=str(root), base_head=head, task=selection['task'],
        issue=selection['issue'], noodle=selection['carrier']['noodle'], landing_owner=selection['landing_owner'],
        carrier={k: selection['carrier'][k] for k in ('platform', 'codex')}, workflow=WORKFLOW,
        host_config_sha256=sha((root / '.noodle.toml').read_bytes()) if (root / '.noodle.toml').exists() else None)
    if selection['instruction_paths']:
        expected_auth['instruction_pins'] = [dict(path=p, sha256=sha(subprocess.check_output(['git', 'show', head + ':' + p], cwd=root))) for p in selection['instruction_paths']]
    check(auth == expected_auth, 'authorization differed from exact selected/derived structure')
    check(result == json.loads((output / 'prepared.json').read_text()), 'stdout and prepared receipt differ')
    check(result.get('owner') == 'supervisor.authorization' and result.get('status') == 'prepared'
          and result.get('authorizes_landing') is False, 'incorrect prepared receipt identity')
    check(result.get('authorization') == dict(path=str(auth_path), sha256=digest), 'authorization receipt path/digest mismatch')
    check(result.get('next') == dict(kind='executable', owner='soodles.issue-atom',
          argv=[str(root / 'issue-atom'), 'run', str(auth_path)], environment={'SOODLES_AUTHORIZATION_SHA256': digest}),
          'continuation not exact final argv/environment')
    after = {p: h for p, h in after.items() if not p.startswith('output/')}
    check(before == after, 'preparation changed unrelated bytes')
    return dict(status='PASS', classification='prepared', schema=auth['schema_version'], authorization_sha256=digest)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('subject', type=Path)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    subject, evidence = args.subject.resolve(), args.evidence.absolute()
    check(not evidence.exists(), 'evidence must be a new directory')
    evidence.mkdir(parents=False)
    results = {}
    for name in CASES:
        try:
            results[name] = run_case(subject, evidence, name)
        except Exception as error:
            results[name] = dict(status='FAIL', error=type(error).__name__ + ': ' + str(error))
    passed = all(value['status'] == 'PASS' for value in results.values())
    report = dict(schema=1, oracle_base=BASE, subject=str(subject), results=results,
                  status='GREEN' if passed else 'RED', authorizes_landing=False,
                  scope='bounded deterministic executable controls; no model improvement claim')
    (evidence / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
