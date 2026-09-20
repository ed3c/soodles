"""Bounded real-process interruption observer; provider reads are fixtures.

Reuse the frozen original-order lifecycle. Only its B admission call is replaced
with separate CLI consumer processes. No production fault-injection flag exists.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch


def resume_probe(binary, source):
    source = Path(source).resolve()
    sys.path.insert(0, str(source))
    import handoff_oracle as lifecycle
    import issue_execution

    events = []
    recovery = {}
    original_session = lifecycle._session

    def consumer(root, packet, mode):
        adapter = packet.parent / 'consumer.py'
        adapter.write_text('''import json, os, signal, sys, time
from pathlib import Path
packet = json.loads(Path(sys.argv[1]).read_text())
sys.path.insert(0, packet['source'])
import github_reader, issue_execution, soodles
def fetch_issue(repository, number):
    if repository != 'ed3c/soodles' or number != 106:
        raise RuntimeError(f'unexpected Issue read {repository}#{number}')
    return packet['issue']
github_reader.fetch_issue = fetch_issue
mode = sys.argv[2]
def stopped():
    marker = Path(packet['marker'])
    with marker.open('w') as stream:
        stream.write('ready'); stream.flush(); os.fsync(stream.fileno())
    while True: signal.pause()
if mode == 'before': stopped()
if mode == 'after':
    original = issue_execution.publish_once
    def publish(path, proposal):
        result = original(path, proposal)
        if result: stopped()
        return result
    issue_execution.publish_once = publish
sys.argv = packet['argv']
soodles.main()
''')
        marker = packet.parent / 'consumer-ready'
        marker.unlink(missing_ok=True)
        argv = [sys.executable, '-B', str(adapter), str(packet), mode]
        started = time.monotonic()
        child = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        try:
            if mode != 'readback':
                lifecycle._wait(lambda: marker.exists() or child.poll() is not None, 'consumer fault seam')
                if not marker.exists():
                    out, err = child.communicate(timeout=5)
                    raise RuntimeError('consumer did not reach fault seam: ' + out + err)
                child.kill()
            out, err = child.communicate(timeout=30)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)
        event = {'argv': argv, 'cli_argv': json.loads(packet.read_text())['argv'],
                 'mode': mode, 'pid': child.pid, 'exit_code': child.returncode,
                 'waited': True, 'stdout': out, 'stderr': err,
                 'elapsed_seconds': time.monotonic() - started}
        events.append(event)
        if mode != 'readback':
            if child.returncode != -signal.SIGKILL:
                raise RuntimeError('consumer interruption was not SIGKILL')
            return None
        if child.returncode:
            raise RuntimeError('resume CLI refused: ' + out + err)
        return json.loads(out)

    def interrupted_admission(envelope, digest, root, reader):
        outside = Path(envelope).parent
        checkpoint = outside / 'landing-checkpoint.json'
        state = json.loads(checkpoint.read_text())
        if state['classification'] != 'RESOLVED' or state['local']['cleanup_mode'] != 'noodle':
            raise RuntimeError('fault must occur after actual Noodle cleanup')
        snapshot = root / '.noodle/state.snapshot.json'
        mailbox = root / '.noodle/orders-next.json'
        before = snapshot.read_bytes(), checkpoint.read_bytes()
        if mailbox.exists():
            raise RuntimeError('B mailbox already exists before interruption')
        packet = outside / 'resume-input.json'
        packet.write_text(json.dumps({'source': str(source),
            'issue': reader('ed3c/soodles', 106),
            'marker': str(outside / 'consumer-ready'),
            'argv': [str(source / 'soodles'), 'issue', 'resume', str(checkpoint), str(envelope), digest]}))
        consumer(root, packet, 'before')
        if mailbox.exists() or before != (snapshot.read_bytes(), checkpoint.read_bytes()):
            raise RuntimeError('interruption before admission changed owner state')
        consumer(root, packet, 'after')
        proposal = mailbox.read_bytes()
        identity = mailbox.stat().st_ino, mailbox.stat().st_mtime_ns
        resumed = consumer(root, packet, 'readback')
        if (resumed.get('action') != 'proposal_pending' or resumed.get('published') is not False
                or mailbox.read_bytes() != proposal
                or identity != (mailbox.stat().st_ino, mailbox.stat().st_mtime_ns)
                or before != (snapshot.read_bytes(), checkpoint.read_bytes())):
            raise RuntimeError('unknown publication was repeated or owner state changed')
        recovery.update(root=root, packet=packet, pending=resumed,
                        proposal_sha256=hashlib.sha256(proposal).hexdigest())
        # Adapter return to the legacy lifecycle driver, not an owner receipt:
        # the killed process demonstrably created this one mailbox.
        return {'published': True}

    def session(root, order):
        result = original_session(root, order)
        if order == 'soodles-106':
            snapshot = (root / '.noodle/state.snapshot.json').read_bytes()
            resumed = consumer(root, recovery['packet'], 'readback')
            if (resumed.get('action') != 'previously_admitted' or resumed.get('published') is not False
                    or snapshot != (root / '.noodle/state.snapshot.json').read_bytes()
                    or (root / '.noodle/orders-next.json').exists()):
                raise RuntimeError('retained B ownership was republished')
            recovery['retained'] = resumed
        return result

    with patch.object(issue_execution, 'automatic', interrupted_admission), patch.object(lifecycle, '_session', session):
        receipt = lifecycle.handoff_probe(binary, source)
    return {'classification': 'VERIFIED', 'sequence': ['A', 'cleanup', 'SIGKILL',
            'resume', 'publication', 'SIGKILL', 'readback', 'B', 'retained_readback'],
            'processes': events, 'pending': recovery['pending'], 'retained': recovery['retained'],
            'proposal_sha256': recovery['proposal_sha256'], 'lifecycle': receipt,
            'scope': 'Sequential consumer recovery with a stopped Noodle scheduler during admission; no concurrent-writer or cross-host claim.',
            'provider_fixture': True, 'authorizes_landing': False}


if __name__ == '__main__':
    print(json.dumps(resume_probe(sys.argv[1], sys.argv[2]), indent=2))
