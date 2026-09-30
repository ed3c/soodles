"""External timing observer for the unchanged stdlib discovery invocation."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time
import unittest

output = Path(sys.argv[1]).resolve()
if not output.is_absolute() or output.is_relative_to(Path.cwd().resolve()):
    raise SystemExit("timing destination must be outside candidate")
stream = output.open("x")
original_start = unittest.TestResult.startTest
original_stop = unittest.TestResult.stopTest
started = {}

def emit(value):
    stream.write(json.dumps(value, sort_keys=True) + "\n")
    stream.flush()

def start(self, test):
    original_start(self, test)
    started[id(test)] = time.monotonic()
    emit({"event": "start", "test": test.id()})

def stop(self, test):
    original_stop(self, test)
    emit({"event": "stop", "test": test.id(),
          "elapsed_seconds": time.monotonic() - started.pop(id(test)),
          "cumulative_failures": len(self.failures), "cumulative_errors": len(self.errors),
          "cumulative_skips": len(self.skipped)})

emit({"event": "observer", "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      "cwd": os.getcwd(), "scope": "per-test timings; assertions remain candidate controls"})
unittest.TestResult.startTest = start
unittest.TestResult.stopTest = stop
sys.path[:0] = [str(Path.cwd()), str(Path.cwd() / "tests")]
sys.argv = ["unittest", "discover", "-s", "tests", "-q"]
try:
    runpy.run_module("unittest", run_name="__main__", alter_sys=True)
finally:
    emit({"event": "observer_end", "unfinished_tests": len(started)})
    stream.close()
