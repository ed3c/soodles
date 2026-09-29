#!/usr/bin/env python3
"""Assemble public bytes for this one local-routing experiment, without a model."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path('/Users/neon/.codex/experiments/eval-loop-contract-lzwb_hq9')
SOURCE = Path('/Users/neon/.codex/experiments/claim-refusal-closure-39lph64z/control-r02')
spec = importlib.util.spec_from_file_location('workspace_factory', BASE / 'fixture-public/workspace.py')
factory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory)


def build(destination, work_id):
    destination.mkdir()
    for name in ('workspace.py', 'drive.py'):
        shutil.copy2(BASE / 'fixture-public' / name, destination / name)
    paths = set(factory.CONTROL_PATHS) | set(factory.OWNER_PATHS)
    paths.update(factory.git(SOURCE, 'ls-tree', '-r', '--name-only', 'HEAD', '--',
                             '.agents/skills', 'contracts').splitlines())
    paths.add('.agents/skills/verify-soodles/scripts/record_context.py')
    for relative in sorted(paths):
        data, executable = factory.committed_blob(SOURCE, '', 'HEAD', relative)
        target = destination / 'subject' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if executable else 0o644)
    (destination / 'workspace.py').unlink()
    (destination / 'input.json').write_text(json.dumps({
        'source_dir': 'subject', 'work_id': work_id,
    }, indent=2) + '\n')


if __name__ == '__main__':
    build(Path(sys.argv[1]), sys.argv[2])
