#!/usr/bin/env python3
"""Supervisor preparation for one explicitly selected Local-entry case."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from prepare_public import SOURCE, build
BASE = Path(__file__).resolve().parents[1]

PYTHON = '/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/bin/python3.14'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def absent(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def main():
    label, work_id, context_path = sys.argv[1:4]
    if not label.replace('-', '').isalnum():
        raise ValueError('simple unique label required')
    freeze_path = BASE / 'freeze.json'
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text())
        for path, expected in freeze['pins'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise RuntimeError('frozen comparison input changed: ' + path)
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() != freeze['source_head']:
            raise RuntimeError('frozen source head changed')
    elif not label.startswith('train-'):
        raise RuntimeError('formal comparison has not been frozen')
    packet = BASE / 'host/runs' / label
    packet.mkdir(parents=True)
    public = packet / 'public'
    build(public, work_id)
    shutil.copyfile(context_path, public / 'context.json')
    treatment = None
    if len(sys.argv) == 5:
        treatment_path = Path(sys.argv[4]).resolve()
        treatment = json.loads(treatment_path.read_text())
        allowed = {'supervisor_admission.py', 'AGENTS.md', 'contracts/system-v1.md',
                   '.agents/skills/verify-soodles/features/local-supervisor-admission.md',
                   '.agents/skills/issue-atom/SKILL.md'}
        if set(treatment['files']) - allowed:
            raise RuntimeError('treatment outside declared product/instruction boundary')
        for rel, item in treatment['files'].items():
            data = Path(item['path']).read_bytes()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise RuntimeError('changed selected treatment: ' + rel)
            (public / 'subject' / rel).write_bytes(data)
    spec = json.loads((Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/host/smoke-preparation/case-r04.json')).read_text())
    for key in ('pins', 'source_head', 'public_files'):
        spec.pop(key)
    run_parent = Path(tempfile.mkdtemp(prefix='soodles-local-', dir='/private/tmp'))
    secret_home = Path(tempfile.mkdtemp(prefix='soodles-runtime-', dir='/private/tmp'))
    os.chmod(secret_home, 0o700)
    shutil.copyfile('/Users/neon/.codex/auth.json', secret_home / 'auth.json')
    os.chmod(secret_home / 'auth.json', 0o600)
    (secret_home / 'public-probe.txt').write_text('public runtime capability probe\n')
    spec['experiment_freeze_sha256'] = hashlib.sha256(freeze_path.read_bytes()).hexdigest() if freeze_path.exists() else None
    spec['treatment'] = treatment
    spec.update(
        run_root=str(run_parent / 'run'), public_dir=str(public),
        task_file=str(BASE / 'host/downstream-task.md'),
        workspace_factory=str(BASE / 'host/downstream_workspace.py'),
        codex_home=str(secret_home), probe_public_path=str(secret_home / 'public-probe.txt'),
        probe_denied_paths=[str(BASE / 'evaluator/check.py'),
                            str(BASE / 'private/cases.json'),
                            str(BASE / 'discovery/reproduction.json')],
        path=str(Path(PYTHON).parent) + ':/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin',
        timeout_seconds=360,
    )
    draft = packet / 'draft.json'
    case = packet / 'case.json'
    dump(draft, spec)
    selected = [PYTHON, '-B', str(Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/host/carrier/run_case.py'))]
    prepare = subprocess.run([*selected, '--prepare', str(draft), str(case)], capture_output=True, text=True)
    dump(packet / 'prepare.json', {'argv': [*selected, '--prepare', str(draft), str(case)],
                                 'exit': prepare.returncode, 'stdout': prepare.stdout, 'stderr': prepare.stderr})
    if prepare.returncode:
        shutil.rmtree(secret_home)
        return prepare.returncode
    digest = hashlib.sha256(case.read_bytes()).hexdigest()
    launched = [*selected, str(case), digest]
    try:
        result = subprocess.run(launched, capture_output=True, text=True)
        dump(packet / 'launch-result.json', {'argv': launched, 'exit': result.returncode,
                                           'stdout': result.stdout, 'stderr': result.stderr})
        return result.returncode
    finally:
        raw = Path(spec['run_root']) / 'raw'
        process_paths = list((Path(spec['run_root']) / 'control/.noodle/sessions').glob('*/process.json'))
        pids = [json.loads(p.read_text()).get('pid') for p in process_paths]
        if (raw / 'exit.json').exists():
            pids.append(json.loads((raw / 'exit.json').read_text()).get('pid'))
        safe = all(isinstance(pid, int) and pid > 0 and absent(pid) and absent(-pid) for pid in pids)
        if safe:
            shutil.rmtree(secret_home)
        dump(packet / 'runtime-cleanup.json', {'temporary_runtime_removed': safe,
                                             'owned_processes_observed_absent': safe,
                                             'credential_bytes_archived': False})
        print(json.dumps({'packet': str(packet), 'run_root': spec['run_root'], 'runtime_removed': safe}), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
