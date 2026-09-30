#!/usr/bin/env python3
"""Supervisor preparation for one explicitly selected Local-entry case."""
import hashlib
import io
import tarfile
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
    label, task_path, summary_path = sys.argv[1:4]
    work_id = 'optimizer'
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
    public.mkdir()
    all_files = subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=SOURCE,text=True).splitlines()
    files = all_files
    archive = subprocess.check_output(['git', 'archive', '--format=tar', 'HEAD'], cwd=SOURCE)
    subject = public / 'subject'
    subject.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source_tar:
        source_tar.extractall(subject, filter='data')
    required = {'supervisor_admission.py', 'issue_atom.py', 'provider-execute',
                'tests/test_supervisor_authorization.py', 'tests/test_supervisor_admission.py',
                'tests/test_issue_atom.py'}
    if not required <= set(files) or any(not (subject/p).is_file() for p in required):
        raise RuntimeError('complete committed optimizer source unavailable before model launch')
    dump(packet / 'source-preflight.json', {'source_head': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
        'tracked_file_count': len(files), 'method': 'complete git archive, no path pruning',
        'required_paths': sorted(required),
        'limitation': 'The model worktree does not carry original Git history; historical-object tests run externally.'})
    (public/'input.json').write_text('{}\n')
    shutil.copyfile(summary_path,public/'selection-summary.json')
    shutil.copyfile(BASE/'synthesis.md',public/'design.md')
    shutil.copyfile(BASE/'discovery/train-observation.json',public/'train-observation.json')
    shutil.copyfile('/private/tmp/soodles-local-utvm7crq/run/raw/stdout.bin',public/'train-trace.jsonl')
    if len(sys.argv)==5:
        prior = json.loads(Path(sys.argv[4]).read_text())
        for rel,item in prior['files'].items():
            data = Path(item['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('prior candidate changed')
            (public/'subject'/rel).write_bytes(data)
    treatment = None
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
        task_file=str(Path(task_path).resolve()),
        codex_home=str(secret_home), probe_public_path=str(secret_home / 'public-probe.txt'),
        probe_denied_paths=[str(BASE / 'evaluator/check.py'),
                            str(BASE / 'private/cases.json'),
                            str(BASE / 'discovery/reproduction.json')],
        path=str(Path(PYTHON).parent) + ':/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin',
        timeout_seconds=900,
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
