"""Bound the tested CLI to read-only Git; record every attempted external effect."""
import json
import os
from pathlib import Path
import sys

def audit(event, args):
    if event == 'subprocess.Popen':
        executable, argv = args[:2]
        allowed = (Path(str(executable)).name == 'git' and isinstance(argv, (list, tuple)))
        if allowed:
            words = list(argv[1:])
            if words[:1] == ['--no-pager']:
                words = words[1:]
            allowed = bool(words) and (words[0] in ('rev-parse', 'status', 'ls-tree', 'cat-file', 'show')
                        or words[:3] == ['remote', 'get-url', 'origin'])
        if not allowed:
            deny(event, repr(args[:2]))
    elif event in ('socket.connect', 'socket.getaddrinfo', 'os.system', 'os.exec', 'os.posix_spawn'):
        deny(event, repr(args))

def deny(event, args):
    with open(os.environ['ORACLE_EFFECT_LOG'], 'a') as stream:
        stream.write(json.dumps({'event': event, 'args': args}) + '\n')
    raise RuntimeError('external oracle forbids effect: ' + event)

sys.addaudithook(audit)
