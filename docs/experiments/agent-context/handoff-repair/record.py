"""Temporary per-process recorder for one supplemental #39 experiment."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
tag, *argv = sys.argv[1:]
if not tag.isdigit() or not argv:
    raise SystemExit('usage: record.py NUMBER executable args...')
request = root / (tag + '-request.json')
result = root / (tag + '-result.json')
with request.open('x') as stream:
    json.dump({'argv': argv, 'recorded_before_invocation': True, 'time_ns': time.time_ns()}, stream, indent=2)
try:
    run = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    value = {'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
except Exception as error:
    value = {'error': type(error).__name__, 'detail': str(error)}
with result.open('x') as stream:
    json.dump(value, stream, indent=2)
print(json.dumps(value))
