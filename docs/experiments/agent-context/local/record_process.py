"""External experiment recorder. Inherit Noodle streams/group; wait one exec chain.

Missing exit.json is incomplete evidence, including recorder SIGKILL or disk failure.
This recorder supplies observations, never an Agent outcome or landing authority.
"""
import datetime
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
        # The checked Soodles entry execs Codex in this PID. Do not detach from
        # Noodle's process group, redirect its streams, or write an Agent outcome.
        child = subprocess.Popen(command)
        for signum in forwarded[:]:
            child.send_signal(signum)
        identity.update(child_pid=child.pid, child_pgid=os.getpgrp())
        persist(directory, 'launch.json', identity)
        returncode = child.wait()
        persist(directory, 'exit.json', dict(identity, returncode=returncode,
                termination_signal=-returncode if returncode < 0 else None,
                finished_at=now(), elapsed_seconds=time.monotonic() - start,
                forwarded_signals=forwarded, waited=True))
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
