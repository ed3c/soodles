"""External experiment recorder. Inherit Noodle streams/group; wait one exec chain.

Missing exit.json is incomplete evidence, including recorder SIGKILL or disk failure.
This recorder supplies observations, never an Agent outcome or landing authority.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def persist(directory, name, value):
    temporary = directory / (name + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, directory / name)
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record(directory, command):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    child = None
    forwarded = []
    previous = {}
    start = time.monotonic()

    def forward(signum, _frame):
        forwarded.append(signum)
        if child is not None and child.poll() is None:
            child.send_signal(signum)

    for signum in (signal.SIGTERM, signal.SIGINT):
        previous[signum] = signal.signal(signum, forward)
    identity = dict(recorder_pid=os.getpid(), cwd=str(Path.cwd()), argv=command,
                    session_id=os.environ.get('NOODLE_SESSION_ID'),
                    order_id=os.environ.get('NOODLE_ORDER_ID'),
                    stage_index=os.environ.get('NOODLE_STAGE_INDEX'),
                    started_at=now(), authorizes_landing=False)
    try:
        # Keep Noodle's process group, stdin and stderr. Its terminal-meta repair
        # may kill this entire group as soon as it sees a terminal stdout event.
        child = subprocess.Popen(command, stdout=subprocess.PIPE)
        for signum in forwarded[:]:
            child.send_signal(signum)
        identity.update(child_pid=child.pid, child_pgid=os.getpgrp())
        persist(directory, 'launch.json', identity)
        tail = []
        deferred = False
        digest = hashlib.sha256()
        size = 0
        with (directory / 'stdout.log').open('xb') as raw:
            for line in child.stdout:
                raw.write(line)
                raw.flush()
                digest.update(line)
                size += len(line)
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    event = None
                if isinstance(event, dict) and event.get('type') in ('turn.completed', 'turn.failed', 'error'):
                    deferred = True
                if deferred:
                    tail.append(line)
                else:
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()
            os.fsync(raw.fileno())
        returncode = child.wait()
        persist(directory, 'exit.json', dict(identity, returncode=returncode,
                termination_signal=-returncode if returncode < 0 else None,
                finished_at=now(), elapsed_seconds=time.monotonic() - start,
                forwarded_signals=forwarded, waited=True,
                stdout_sha256=digest.hexdigest(), stdout_bytes=size,
                terminal_tail_lines_deferred=len(tail)))
        # Never rewrite bytes. Receipt persistence precedes terminal delivery;
        # missing/failed persistence cannot publish an apparent completed turn.
        for line in tail:
            sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()
        return returncode if returncode >= 0 else 128 - returncode
    except BaseException as error:
        # Do not orphan a writer when recording itself fails. No success receipt
        # is produced on this path; the enclosing Noodle owner observes failure.
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        print('process recorder failed: ' + repr(error), file=sys.stderr)
        raise
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[2] != '--':
        raise SystemExit('usage: record_process.py NEW_DIRECTORY -- COMMAND [ARGS...]')
    raise SystemExit(record(sys.argv[1], sys.argv[3:]))
