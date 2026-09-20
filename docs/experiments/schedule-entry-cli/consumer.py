"""Bounded native-consumer recorder; no complete-platform-transcript claim."""
import json
from pathlib import Path
import subprocess
import sys
import time


root = Path(sys.argv[1]).resolve()
packet = json.loads((root / 'packet.json').read_text())
log = root / 'requests.json'
records = json.loads(log.read_text()) if log.exists() else []
mode = sys.argv[2]
if mode == 'read':
    output = {'task': packet['task'], 'skill': (root / 'skill.md').read_text(),
              'checkout': packet['checkout'], 'current_environment': packet['env'],
              'python': sys.executable}
    records.append({'kind': 'instruction_read', 'output': output})
    print(json.dumps(output, indent=2))
elif mode == 'run':
    argv = sys.argv[3:]
    started = time.monotonic()
    proc = subprocess.run(argv, cwd=packet['checkout'], env=packet['env'],
                          text=True, capture_output=True, timeout=30)
    record = {'kind': 'process', 'argv': argv, 'exit_code': proc.returncode,
              'stdout': proc.stdout, 'stderr': proc.stderr,
              'elapsed_seconds': time.monotonic() - started}
    records.append(record)
    print(json.dumps(record, indent=2))
elif mode == 'finish':
    value = json.loads(sys.argv[3])
    (root / 'decision.json').write_text(json.dumps(value, indent=2) + '\n')
    records.append({'kind': 'decision', 'value': value})
    print(json.dumps(value))
else:
    raise SystemExit('expected read, run or finish')
log.write_text(json.dumps(records, indent=2) + '\n')
