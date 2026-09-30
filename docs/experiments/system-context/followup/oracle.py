"""Independent Issue 199 observer. Owner state is a labelled disposable fixture."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASELINE = Path('/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/publisher')
NOODLE = Path('/Users/neon/.codex/experiments/soodles133-bootstrap.QpepPK/noodle-source/bin/noodle')
NOODLE_SHA = '965cfd6f985e207551d0664e728ae9fae10ae0cc8cd2885a816415823d9d103d'
sys.path[:0] = [str(BASELINE / 'tests'), str(BASELINE)]
from test_issue_execution import IssueExecutionTests


def fixture(destination):
    assert hashlib.sha256(NOODLE.read_bytes()).hexdigest() == NOODLE_SHA
    f = IssueExecutionTests()
    f.setUp()
    # Preserve this explicitly disposable fixture across consumer processes.
    f.temp._finalizer.detach()
    f.envelope['execution']['carrier']['noodle'] = {'path': str(NOODLE), 'sha256': NOODLE_SHA}
    f.bind_envelope()
    f.admit('supervised')
    f.promote_fixture()
    stage = f.snapshot['state']['orders']['soodles-18']['stages'][0]
    stage['status'] = 'running'
    stage['attempts'][-1].update(status='running', session_id=f.session)
    f.save_owner()
    launcher = f.directory / 'launcher'
    launcher.write_text('#!/bin/sh\nexit 64\n')
    launcher.chmod(0o755)
    f.env['SOODLES_ADMISSION_LAUNCHER'] = str(launcher)
    session_dir = f.runtime / 'sessions' / f.session
    (session_dir / 'process.json').write_text(json.dumps({'pid': os.getpid(), 'session_id': f.session}))
    (session_dir / 'meta.json').write_text(json.dumps({'session_id': f.session, 'status': 'running', 'alive': True}))
    packet = {'kind': 'disposable_owner_fixture', 'directory': str(f.directory),
              'cwd': str(f.worktree), 'environment': f.env, 'noodle': str(NOODLE),
              'events': str(session_dir / 'events.ndjson'), 'envelope': str(f.path),
              'snapshot': str(f.runtime / 'state.snapshot.json')}
    Path(destination).write_text(json.dumps(packet, indent=2) + '\n')
    return packet


def events(packet):
    p = Path(packet['events'])
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def outcome(packet):
    return [e for e in events(packet) if e['type'] == 'stage_message' and e.get('payload', {}).get('outcome')]


def run(candidate, packet, argv, override=None):
    env = {**os.environ, **packet['environment'], **(override or {})}
    p = subprocess.run([str(Path(candidate) / 'stage-outcome'), *argv], cwd=packet['cwd'],
                       env=env, capture_output=True, text=True, timeout=30)
    return {'argv': [str(Path(candidate) / 'stage-outcome'), *argv],
            'exit_status': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def verify(candidate, output):
    output = Path(output)
    output.mkdir()
    records = []
    for label in ('completed', 'blocked', 'failed', 'unknown', 'empty', 'wrong-session',
                  'wrong-order', 'wrong-stage', 'missing-launcher', 'envelope-drift', 'binary-drift'):
        packet = fixture(output / (label + '.json'))
        args = [label if label in ('completed', 'blocked', 'failed') else 'completed', 'fixture observation']
        override = {}
        if label == 'unknown': args[0] = 'resolved'
        if label == 'empty': args[1] = ' '
        if label == 'wrong-session': override['NOODLE_SESSION_ID'] = 'foreign-session'
        if label == 'wrong-order': override['NOODLE_ORDER_ID'] = 'foreign-order'
        if label == 'wrong-stage': override['NOODLE_STAGE_INDEX'] = '1'
        if label == 'missing-launcher': override['SOODLES_ADMISSION_LAUNCHER'] = ''
        if label == 'envelope-drift':
            p = Path(packet['envelope']); p.write_text(p.read_text() + ' ')
        if label == 'binary-drift':
            p = Path(packet['envelope']); d = json.loads(p.read_text())
            d['execution']['carrier']['noodle']['sha256'] = '0' * 64
            p.write_text(json.dumps(d))
            # Bind changed fixture admission into its canonical prompt, so this
            # tests executable identity rather than the preceding envelope gate.
            s = Path(packet['snapshot']); state = json.loads(s.read_text())
            st = state['state']['orders']['soodles-18']['stages'][0]
            subject = json.loads(st['prompt'])
            subject['envelope_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
            st['prompt'] = json.dumps(subject); s.write_text(json.dumps(state))
        before = Path(packet['snapshot']).read_bytes()
        result = run(candidate, packet, args, override)
        observed = outcome(packet)
        value = json.loads(result['stdout'])
        assert Path(packet['snapshot']).read_bytes() == before, label
        if label in ('completed', 'blocked', 'failed'):
            assert result['exit_status'] == 0 and value['status'] == 'recorded', (label, result)
            assert len(observed) == 1, (label, observed)
            assert observed[0]['session_id'] == packet['environment']['NOODLE_SESSION_ID']
            assert observed[0]['payload'] == {'message': args[1], 'blocking': label != 'completed',
                'outcome': label, 'order_id': 'soodles-18', 'stage_index': 0}, observed
            first = Path(packet['events']).read_bytes()
            repeated = run(candidate, packet, args)
            assert repeated['exit_status'] != 0 and Path(packet['events']).read_bytes() == first
            records.append({'case': label + '-duplicate', 'process': repeated, 'no_new_event': True})
        else:
            assert result['exit_status'] != 0 and value['status'] == 'refused' and not observed, (label, result)
            assert value['next']['owner'] and value['next']['required']
        records.append({'case': label, 'process': result, 'events': observed})
    return {'classification': 'PASS', 'scope': 'actual Noodle event CLI over disposable owner fixtures',
            'processes': records, 'authorizes_landing': False}


if __name__ == '__main__':
    if sys.argv[1] == 'fixture':
        print(json.dumps(fixture(sys.argv[2]), indent=2))
    else:
        print(json.dumps(verify(sys.argv[1], sys.argv[2]), indent=2))
