"""Controls for local landing provider transport and exact Noodle continuation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import patch

import landing
import provider_transport


class ProviderFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.checkpoint = self.root / "checkpoint.json"
        repo = {"full_name": "ed3c/soodles"}
        self.claim = {
            "repository": "ed3c/soodles", "issue": 1, "pr": 2,
            "head": "a" * 40, "tree": "b" * 40, "base_head": "c" * 40,
            "run_id": 10, "run_attempt": 1, "worktree": "example",
            "control_root": str(self.root / "control"),
            "verifier_sha256": landing.verifier_digest(),
        }
        self.snapshot = {
            "pr": {"number": 2, "html_url": "https://github.com/ed3c/soodles/pull/2",
                   "body": "Refs ed3c/soodles#1\n",
                   "head": {"repo": repo, "sha": "a" * 40, "ref": "example"},
                   "base": {"repo": repo, "sha": "c" * 40, "ref": "main"},
                   "merged": False, "state": "open", "draft": False, "mergeable": True},
            "issue": {"number": 1, "html_url": "https://github.com/ed3c/soodles/issues/1",
                      "state": "open"},
            "run": {"id": 10, "run_attempt": 1, "repository": repo,
                    "head_repository": repo, "head_sha": "a" * 40,
                    "event": "pull_request", "path": ".github/workflows/runtime.yml",
                    "status": "completed", "conclusion": "success"},
            "commit": {"sha": "a" * 40, "tree": {"sha": "b" * 40}},
            "jobs": {"total_count": 1, "jobs": [{
                "id": 11, "name": "runtime-evidence", "run_id": 10,
                "head_sha": "a" * 40, "status": "completed", "conclusion": "success",
                "steps": [{"name": "Canonical acceptance on the exact candidate head",
                           "status": "completed", "conclusion": "success"}]}]},
            "branch": {"name": "main", "commit": {"sha": "c" * 40}},
        }
        self.calls = []
        self.merge_calls = 0
        self.close_calls = 0

    def close(self):
        self.temp.cleanup()

    def api(self, method, url, payload, token):
        self.assert_token(token)
        self.calls.append((method, url, copy.deepcopy(payload)))
        prefix = "https://api.github.com/repos/ed3c/soodles/"
        if method == "GET":
            suffix = url.removeprefix(prefix)
            mapping = {
                "pulls/2": self.snapshot["pr"],
                "issues/1": self.snapshot["issue"],
                "git/commits/" + "a" * 40: self.snapshot["commit"],
                "branches/main": self.snapshot["branch"],
                "actions/runs/10": self.snapshot["run"],
                "actions/runs/10/jobs": self.snapshot["jobs"],
            }
            if suffix.startswith("git/commits/") and suffix != "git/commits/" + "a" * 40:
                return copy.deepcopy(self.snapshot["merge_commit"])
            return copy.deepcopy(mapping[suffix])
        if method == "PUT":
            self.merge_calls += 1
            self.snapshot["pr"].update(
                merged=True, state="closed", merged_at="2026-09-21T00:00:00Z",
                merge_commit_sha="d" * 40)
            self.snapshot["merge_commit"] = {
                "sha": "d" * 40, "tree": {"sha": "b" * 40},
                "parents": [{"sha": "c" * 40}, {"sha": "a" * 40}],
            }
            return {"merged": True, "sha": "d" * 40}
        if method == "PATCH":
            self.close_calls += 1
            self.snapshot["issue"].update(
                state="closed", state_reason="completed",
                closed_at="2026-09-21T00:01:00Z")
            return copy.deepcopy(self.snapshot["issue"])
        raise AssertionError((method, url, payload))

    @staticmethod
    def assert_token(token):
        if token != "fixture-token":
            raise AssertionError("unexpected token")

    def start_and_dispatch(self):
        landing.start(self.claim, self.snapshot, self.checkpoint)
        self.assert_action(landing.advance(self.checkpoint, self.snapshot), "dispatch")
        return landing.dispatch(self.checkpoint, self.snapshot)

    @staticmethod
    def assert_action(result, action):
        if result["action"] != action:
            raise AssertionError(result)


class LocalProviderTransportTests(unittest.TestCase):
    def setUp(self):
        self.f = ProviderFixture()
        self.addCleanup(self.f.close)
        self.env = {"GH_TOKEN": "fixture-token"}

    def test_local_merge_close_are_exact_executable_continuations(self):
        dispatch = self.f.start_and_dispatch()
        self.assertEqual(dispatch["next"]["kind"], "executable")
        self.assertEqual(dispatch["next"]["operation"], "execute")
        self.assertEqual(dispatch["next"]["argv"], landing.provider_cli_argv(self.f.checkpoint))
        persisted = landing.read(self.f.checkpoint)["delivery"]
        self.assertEqual(persisted["request"], dispatch["request"])

        merged = provider_transport.execute(
            self.f.checkpoint, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.merge_calls, 1)
        self.assertEqual(merged["provider_mutations"], 1)
        self.assertEqual(merged["next"]["operation"], "advance")
        merge_readback = json.loads(Path(merged["readback"]).read_text())
        prepared_close = landing.advance(self.f.checkpoint, merge_readback)
        self.assertEqual(prepared_close["action"], "dispatch")

        close_dispatch = landing.dispatch(self.f.checkpoint, merge_readback)
        self.assertEqual(close_dispatch["next"]["kind"], "executable")
        closed = provider_transport.execute(
            self.f.checkpoint, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.close_calls, 1)
        close_readback = json.loads(Path(closed["readback"]).read_text())
        awaiting = landing.advance(self.f.checkpoint, close_readback)
        self.assertEqual(awaiting["action"], "reconcile")
        self.assertEqual(awaiting["next"]["kind"], "input")
        self.assertEqual(awaiting["next"]["required"], ["binary"])

        # Replaying transport after observed close does not emit a second PATCH.
        replay = provider_transport.execute(
            self.f.checkpoint, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.close_calls, 1)
        self.assertEqual(replay["provider_mutations"], 0)

    def test_cloud_route_keeps_connector_request_and_no_local_executable(self):
        cloud = {k: v for k, v in self.f.claim.items() if k != "control_root"}
        cp = self.f.root / "cloud.json"
        landing.start(cloud, self.f.snapshot, cp)
        landing.advance(cp, self.f.snapshot)
        dispatch = landing.dispatch(cp, self.f.snapshot)
        self.assertEqual(dispatch["next"]["kind"], "provider_readback")
        self.assertNotIn("argv", dispatch["next"])
        self.assertEqual(dispatch["request"]["action"], "merge")

    def test_missing_token_request_drift_and_cloud_checkpoint_refuse_before_mutation(self):
        self.f.start_and_dispatch()
        with self.assertRaises(provider_transport.ProviderRefusal):
            provider_transport.execute(self.f.checkpoint, environ={}, api=self.f.api)
        self.assertEqual(self.f.merge_calls, 0)

        state = landing.read(self.f.checkpoint)
        state["delivery"]["request"]["pr_number"] = 99
        landing.save(self.f.checkpoint, state)
        with self.assertRaises(provider_transport.ProviderRefusal):
            provider_transport.execute(self.f.checkpoint, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.merge_calls, 0)

        cloud = copy.deepcopy(state)
        cloud["claim"].pop("control_root")
        cloud["delivery"]["request"] = landing.delivery_request(cloud["claim"], "merge")
        cp = self.f.root / "cloud-offered.json"
        landing.save(cp, cloud)
        with self.assertRaises(provider_transport.ProviderRefusal):
            provider_transport.execute(cp, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.merge_calls, 0)

    def test_unknown_merge_outcome_reads_back_without_second_mutation(self):
        self.f.start_and_dispatch()
        def unknown_after_effect(method, url, payload, token):
            result = self.f.api(method, url, payload, token)
            if method == "PUT":
                raise provider_transport.ProviderUnknown("lost-response")
            return result

        result = provider_transport.execute(
            self.f.checkpoint, environ=self.env, api=unknown_after_effect)
        self.assertEqual(self.f.merge_calls, 1)
        self.assertIsNone(result["provider_mutations"])
        self.assertEqual(result["next"]["operation"], "advance")

        replay = provider_transport.execute(
            self.f.checkpoint, environ=self.env, api=self.f.api)
        self.assertEqual(self.f.merge_calls, 1)
        self.assertEqual(replay["provider_mutations"], 0)

    def test_envelope_bound_reconcile_projects_measured_noodle_binary(self):
        binary = self.f.root / "noodle"
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
        identity = {
            "path": str(binary),
            "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        }
        envelope = {
            "execution": {
                "carrier": {
                    "platform": platform.system().lower() + "_" + platform.machine().lower(),
                    "noodle": identity,
                }
            }
        }
        claim = {**self.f.claim, "execution_envelope": {
            "path": str(self.f.root / "external-envelope.json"),
            "sha256": "f" * 64}}
        with patch.object(landing, "execution_binding", return_value=envelope):
            projected = landing.reconcile_next(claim, self.f.checkpoint)
        self.assertEqual(projected["kind"], "executable")
        self.assertEqual(projected["known"]["binary"], str(binary))
        self.assertEqual(
            projected["argv"],
            landing.cli_argv("reconcile", self.f.checkpoint, str(binary)))


if __name__ == "__main__":
    unittest.main()
