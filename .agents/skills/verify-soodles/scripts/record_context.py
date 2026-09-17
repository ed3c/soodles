#!/usr/bin/env python3
"""Record one bounded command, not a native Session trace or a verdict."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def files(argv):
    result = {}
    for value in argv:
        path = Path(value)
        try:
            if path.is_file():
                data = path.read_bytes()
                result[str(path.resolve())] = {
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
                }
        except OSError as error:
            result[value] = {"snapshot_error": type(error).__name__}
    return result


def record(destination, label, argv, timeout=60):
    destination = Path(destination)
    checkout = Path(__file__).resolve().parents[4]
    if not destination.is_absolute() or destination.resolve().is_relative_to(checkout):
        raise ValueError("evidence must be absolute and outside this checkout")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", label) or not argv:
        raise ValueError("fresh simple label and command required")
    destination.mkdir(parents=True, exist_ok=True)
    entry = destination / label
    entry.mkdir()  # Refuse reuse before any effect.
    request = {"argv": argv, "cwd": os.getcwd(), "time_ns": time.time_ns(),
               "files_before": files(argv), "timeout_seconds": timeout}
    (entry / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    started = time.monotonic()
    result = {"exit_code": None, "timed_out": False, "error": None,
              "authorizes_landing": False, "scope": "one_subprocess"}
    stdout = stderr = b""
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        result["exit_code"] = process.returncode
    except OSError as error:
        result["error"] = str(error)
    (entry / "stdout.bin").write_bytes(stdout)
    (entry / "stderr.bin").write_bytes(stderr)
    result.update(elapsed_seconds=time.monotonic() - started,
                  files_after=files(argv),
                  stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                  stderr_sha256=hashlib.sha256(stderr).hexdigest())
    (entry / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result, stdout, stderr


if __name__ == "__main__":
    try:
        value, out, err = record(sys.argv[1], sys.argv[2], sys.argv[3:])
    except (ValueError, FileExistsError, IndexError) as error:
        raise SystemExit(str(error))
    sys.stdout.buffer.write(out)
    sys.stderr.buffer.write(err)
    raise SystemExit(value["exit_code"] if value["exit_code"] is not None else 125)
