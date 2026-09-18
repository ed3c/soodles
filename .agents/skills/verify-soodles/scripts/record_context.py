#!/usr/bin/env python3
"""Record one bounded command, not a native Session trace or a verdict."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time


SHELLS = {"bash", "dash", "ksh", "sh", "zsh"}


def referenced_values(argv):
    """Return direct argv values plus literal tokens inside a shell -c script."""
    values = [("argv", value) for value in argv]
    if not argv or Path(argv[0]).name not in SHELLS:
        return values, None
    script = None
    for index, value in enumerate(argv[1:], 1):
        if value.startswith("-") and "c" in value[1:]:
            if index + 1 < len(argv):
                script = argv[index + 1]
            break
        if not value.startswith("-"):
            break
    if script is None:
        return values, None
    try:
        lexer = shlex.shlex(script, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        values.extend(("shell", value) for value in lexer)
        return values, None
    except ValueError as error:
        return values, type(error).__name__


def files(argv):
    result = {}
    values, parse_error = referenced_values(argv)
    for source, value in values:
        path = Path(value)
        try:
            if path.is_file():
                data = path.read_bytes()
                key = str(path.resolve())
                observed = set(result.get(key, {}).get("observed_from", []))
                observed.add(source)
                result[key] = {
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                    "observed_from": sorted(observed)
                }
        except OSError as error:
            if source == "argv":
                result[value] = {"snapshot_error": type(error).__name__,
                                 "observed_from": [source]}
    return result, parse_error


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
    before, parse_error = files(argv)
    request = {"argv": argv, "cwd": os.getcwd(), "time_ns": time.time_ns(),
               "files_before": before, "timeout_seconds": timeout}
    if parse_error:
        request["shell_parse_error"] = parse_error
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
    after, after_parse_error = files(argv)
    result.update(elapsed_seconds=time.monotonic() - started,
                  files_after=after,
                  stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                  stderr_sha256=hashlib.sha256(stderr).hexdigest())
    if after_parse_error:
        result["shell_parse_error"] = after_parse_error
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
