"""Portable failure controls; real positive Noodle handoff remains Linux acceptance."""
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
import unittest
from unittest.mock import Mock, call, patch

import handoff_oracle as oracle
import issue_execution
import landing


class HandoffCleanupTests(unittest.TestCase):
    def probe(self, failed_projection=None, cleanup_error=None, original_env="prior"):
        events, children, roots = [], [], []
        failure = RuntimeError("projection failed")
        state = {"effect_ledger": [{"effect_id": "B-projected", "effect": {
            "type": "write_projection", "payload": {"order_id": "soodles-106"}}}]}

        def start(noodle, root):
            self.assertEqual(os.environ["FIXTURE_NOODLE"], str(Path(sys.executable).resolve()))
            roots.append(root)
            process = Mock(pid=100 + len(children), returncode=None)
            process.poll.return_value = None

            def communicate(timeout):
                self.assertTrue(root.is_dir(), "fixture removed before child reap")
                self.assertEqual(timeout, 15)
                process.returncode = 0
                events.append("stop " + str(process.pid))
                label = "A projection" if process.pid == 100 else "B projection"
                if (cleanup_error and label == failed_projection
                        and process.communicate.call_count == 1):
                    raise cleanup_error
                return "out", ""

            process.communicate.side_effect = communicate
            children.append(process)
            events.append("start " + str(process.pid))
            return process

        def wait(predicate, label):
            events.append(label)
            if label == failed_projection:
                raise failure
            return state

        def session(root, order):
            directory = root / order
            directory.mkdir()
            (directory / "spawn.json").write_text("{}")
            # Deterministically later than cleanup_at without sleeping.
            started = time.time_ns() + 1_000_000_000
            os.utime(directory / "spawn.json", ns=(started, started))
            return directory, {"session_id": order}, {}, {"payload": {"outcome": "completed"}}

        def reconcile(*args):
            events.append("cleanup A")
            return {"classification": "RESOLVED"}

        def run(argv, root):
            if argv[:3] == ["git", "worktree", "list"]:
                return "worktree fixture"
            if argv[:3] == ["git", "branch", "--list"]:
                return ""
            return "a" * 40

        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ))
            if original_env is None:
                os.environ.pop("FIXTURE_NOODLE", None)
            else:
                os.environ["FIXTURE_NOODLE"] = original_env
            for name, replacement in (("_start", start), ("_wait", wait),
                    ("_session", session), ("_run", run)):
                stack.enter_context(patch.object(oracle, name, side_effect=replacement))
            stack.enter_context(patch.object(oracle, "_envelope", return_value=(
                {}, Path("envelope"), "digest", {})))
            stack.enter_context(patch.object(oracle, "_consume_probe", return_value={"actions": []}))
            stack.enter_context(patch.object(oracle.subprocess, "run"))
            stack.enter_context(patch.object(oracle.os, "killpg"))
            stack.enter_context(patch.object(landing, "save"))
            stack.enter_context(patch.object(landing, "reconcile", side_effect=reconcile))
            stack.enter_context(patch.object(issue_execution, "completed_original_order",
                                            return_value={"source": "projection"}))
            stack.enter_context(patch.object(issue_execution, "automatic",
                                            return_value={"published": True}))
            if failed_projection:
                with self.assertRaises(RuntimeError) as caught:
                    oracle.handoff_probe(sys.executable)
                self.assertIs(caught.exception, failure)
                if cleanup_error:
                    self.assertIs(caught.exception.__cause__, cleanup_error)
                    self.assertIn(str(cleanup_error), "".join(traceback.format_exception(caught.exception)))
                receipt = None
            else:
                receipt = oracle.handoff_probe(sys.executable)
            self.assertEqual(os.environ.get("FIXTURE_NOODLE"), original_env)
            self.assertTrue(all(not root.exists() for root in roots))
        return receipt, children, events

    def test_first_projection_failure_reaps_before_fixture_deletion(self):
        _, children, events = self.probe("A projection", original_env=None)
        self.assertEqual(events, ["start 100", "A projection", "stop 100"])
        children[0].communicate.assert_called_once_with(timeout=15)

    def test_second_projection_failure_does_not_stop_first_twice(self):
        _, children, events = self.probe("B projection")
        self.assertEqual(events, ["start 100", "A projection", "stop 100", "cleanup A",
                                  "start 101", "B projection", "stop 101"])
        for child in children:
            child.communicate.assert_called_once_with(timeout=15)

    def test_cleanup_error_preserves_projection_error_and_restores_environment(self):
        for label in ("A projection", "B projection"):
            with self.subTest(label=label):
                self.probe(label, OSError("cleanup failed"))

    def test_normal_sequence_and_exit_evidence_are_unchanged(self):
        receipt, children, events = self.probe()
        self.assertEqual(receipt["classification"], "VERIFIED")
        self.assertEqual(receipt["sequence"], ["A", "cleanup", "B"])
        self.assertTrue(receipt["zero_residue"])
        self.assertFalse(receipt["authorizes_landing"])
        self.assertEqual(events, ["start 100", "A projection", "stop 100", "cleanup A",
                                  "start 101", "B projection", "stop 101"])
        for label, child in zip(("A", "B"), children):
            self.assertEqual(receipt[label]["process"], {
                "pid": child.pid, "returncode": 0, "waited": True,
                "stdout_sha256": hashlib.sha256(b"out").hexdigest(),
                "stderr_sha256": hashlib.sha256(b"").hexdigest()})
            child.communicate.assert_called_once_with(timeout=15)

    def test_successful_stop_signals_only_a_running_process(self):
        for status in (None, 0):
            with self.subTest(status=status):
                process = Mock(pid=123, returncode=0)
                process.poll.return_value = status
                process.communicate.return_value = ("out", "err")
                with patch.object(oracle.os, "killpg") as killpg:
                    receipt = oracle._stop(process)
                self.assertEqual(killpg.call_args_list,
                                 [call(123, signal.SIGINT)] if status is None else [])
                process.communicate.assert_called_once_with(timeout=15)
                self.assertTrue(receipt["waited"])

    def test_timeout_kills_owned_group_reaps_and_still_raises(self):
        process = Mock(pid=123, returncode=-signal.SIGKILL)
        process.poll.return_value = None
        timeout = subprocess.TimeoutExpired("noodle", 15)
        process.communicate.side_effect = [timeout, ("", "")]
        with patch.object(oracle.os, "killpg") as killpg:
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                oracle._stop(process)
        self.assertIs(caught.exception, timeout)
        self.assertEqual(killpg.call_args_list,
                         [call(123, signal.SIGINT), call(123, signal.SIGKILL)])
        self.assertEqual(process.communicate.call_args_list, [call(timeout=15)] * 2)

    def test_forced_reap_failure_remains_visible_beneath_timeout(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        timeout = subprocess.TimeoutExpired("noodle", 15)
        cleanup = OSError("forced reap failed")
        process.communicate.side_effect = [timeout, cleanup]
        with patch.object(oracle.os, "killpg"):
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                oracle._stop(process)
        self.assertIs(caught.exception, timeout)
        self.assertIs(caught.exception.__cause__, cleanup)

    def test_nonzero_exit_cannot_supply_success_receipt(self):
        process = Mock(pid=123, returncode=7)
        process.poll.return_value = 7
        process.communicate.return_value = ("", "exit detail")
        with patch.object(oracle.os, "killpg") as killpg:
            with self.assertRaisesRegex(RuntimeError, "Noodle exited 7: exit detail"):
                oracle._stop(process)
        killpg.assert_not_called()
        process.communicate.assert_called_once_with(timeout=15)


if __name__ == "__main__":
    unittest.main()
