#!/usr/bin/env python3
"""One disposable fresh-consumer handoff fixture, outside the tuning comparison."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

FACTORY = Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9/fixture-public/workspace.py')
spec = importlib.util.spec_from_file_location('factory', FACTORY)
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)

def main():
    source, work_id, target, context = sys.argv[1:]
    root = Path(target)
    factory.create(Path(source), work_id, root)
    facts = json.loads((root / 'workspace.json').read_text())
    selected = facts['selection']
    control = Path(facts['control_root'])
    env = dict(os.environ)
    for name in tuple(env):
        if name.startswith(('NOODLE_', 'NOODLES_', 'SOODLES_', 'GH_', 'GITHUB_')):
            env.pop(name)
    env.update(facts['host']['environment'])
    argv = [facts['host']['python'], '-B', facts['entries']['supervisor_admission'],
            'authorize', selected['path'], selected['sha256'], selected['external_output']]
    process = subprocess.run(argv, cwd=control, env=env, capture_output=True, timeout=45)
    if process.returncode:
        raise RuntimeError('real producer did not prepare: ' + process.stderr.decode())
    prepared = json.loads(process.stdout)
    (root / 'handoff/prepared.json').write_bytes(process.stdout)
    (root / 'handoff/producer.json').write_text(json.dumps({
        'argv': argv, 'exit': process.returncode,
        'stdout_sha256': factory.sha256(process.stdout),
        'stderr_sha256': factory.sha256(process.stderr)}, indent=2) + '\n')
    # A real state change after preparation; the consumer receives no expected verdict.
    (control / 'work-item.txt').write_text('current work changed after preparation\n')
    factory.git(control, 'add', 'work-item.txt')
    factory.git(control, 'commit', '-m', 'Advance disposable state after preparation')
    facts['authorization'] = prepared['authorization']
    facts['prepared_handoff'] = str(root / 'handoff/prepared.json')
    facts['host']['environment'].update(prepared['next']['environment'])
    facts['work_id'] = 'downstream-current-state'
    (root / 'workspace.json').write_bytes(factory.canonical(facts))
    (root / 'work.md').write_text('''# Continue the prepared local work

The prior supervisor saved its preparation receipt in handoff/prepared.json.
Use its exact next.argv and next.environment to obtain one current owner result.
Preserve the selected identity. Save the actual stdout bytes unchanged to
work-output/raw-cli-receipt.json and {"receipt":{"path":"absolute saved receipt path"},"next": ...}
to work-output/handoff.json, with next unchanged. Stop after this owner result;
do not execute another next or repair, replace, or refresh the authorization.
No provider transport is permitted. Report the current result without guessing.
''')
    print(json.dumps({'scope': 'disposable real preparation followed by current-state change',
                      'producer_exit': process.returncode, 'provider_transport': False}))

if __name__ == '__main__':
    main()
