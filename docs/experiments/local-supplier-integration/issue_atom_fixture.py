import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import issue_atom as atom


class Result:
    def __init__(self, returncode, stderr=""):
        self.returncode = returncode
        self.stderr = stderr


class Provider:
    def __init__(self):
        self.token = "fixture-token"
        self.value = None
        self.create_calls = 0
        self.create_effect = True
        self.create_unknown = False
        self.merge_calls = 0

    def issues(self):
        return [] if self.value is None else [self.value]

    def issue(self, number):
        if self.value is None or self.value["number"] != number:
            return None
        return dict(self.value)

    def create_issue(self, title, body):
        self.create_calls += 1
        if self.create_effect:
            self.value = {"number": 131, "title": title, "body": body,
                          "state": "open", "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131"}
        if self.create_unknown:
            raise atom.MutationUnknown("lost response")
        return self.value

    def merge(self, number, head, method):
        self.merge_calls += 1
        return {"merged": True}

    def close_issue(self, number, state_reason):
        self.value["state"] = "closed"
        return self.value


class IssueAtomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.root = self.outer / "project"
        subprocess.run(["git", "init", "-b", "main", self.root], check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Atom Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "atom@example.invalid"],
                       cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(".noodle/\n.worktrees/\n")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "remote", "add", "origin",
                        "https://github.com/ed3c/soodles.git"], cwd=self.root, check=True)
        self.base = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                            cwd=self.root, text=True).strip()
        self.binary = self.outer / "carrier"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary),
                    "sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        contract = {
            "schema": 3, "trigger": "fixture", "source": "fixture",
            "owner": "fixture owner", "changes": ["fixture"],
            "write_paths": ["allowed.py"], "behavior": ["fixture"],
            "defect_controls": ["fixture"], "non_cases": ["fixture"],
            "dependencies": [], "acceptance": "fixture", "delivery": "fixture",
            "reconciliation": "fixture", "feature_scope": "fixture",
            "required_paths": ["allowed.py"], "evidence_manifest": "allowed.py",
            "base_head": self.base,
            "frozen_paths": [{"path": "allowed.py", "revision": "head",
                              "sha256": "a" * 64}],
        }
        body = ("<!-- soodles:execution-v1 -->\n```json\n"
                + json.dumps(contract) + "\n```\n"
                "<!-- /soodles:execution-v1 -->")
        self.authorization = {
            "schema_version": 1, "owner": "external-supervisor",
            "repository": "ed3c/soodles", "control_root": str(self.root),
            "base_head": self.base, "task": "Execute exact Issue.",
            "issue": {"title": "Fixture atom", "body": body},
            "noodle": dict(identity),
            "carrier": {"platform": __import__("platform").system().lower() + "_"
                                    + __import__("platform").machine().lower(),
                        "codex": {**identity, "model": "fixture-model",
                                  "argv": ["exec", "--json"]}},
            "workflow": {"path": ".github/workflows/runtime.yml",
                         "job": "runtime-evidence",
                         "step": "Canonical acceptance on the exact candidate head"},
        }
        self.path = self.outer / "authorization.json"
        self.path.write_text(json.dumps(self.authorization))
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.env = {"SOODLES_AUTHORIZATION_SHA256": self.digest, "GH_TOKEN": "fixture"}

    def ready_issue(self, provider):
        body = self.authorization["issue"]["body"].rstrip() + "\n\n" + atom.marker(self.digest) + "\n"
        provider.value = {"number": 131, "title": self.authorization["issue"]["title"],
                          "body": body, "state": "open",
                          "updated_at": "2026-09-22T00:00:00Z",
                          "html_url": "https://github.com/ed3c/soodles/issues/131"}

    def pending_patches(self):
        return (
            patch("issue_atom.issue_execution.supervised", return_value={"published": True}),
            patch("issue_atom._run_claim", return_value=Result(1, "order is not ready")),
        )

    def test_help_exposes_only_same_lifecycle_command(self):
        result = subprocess.run([str(Path(atom.__file__).parent / "issue-atom"), "--help"],
                                cwd=Path(atom.__file__).parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("authorization", result.stdout)
        self.assertIn("same command", result.stdout)

    def test_lost_issue_create_adopts_exact_readback_and_never_recreates(self):
        provider = Provider()
        provider.create_unknown = True
        first, second = self.pending_patches()
        with first, second:
            result = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(result["waiting_on"], "Noodle")
        self.assertEqual(provider.create_calls, 1)
        first, second = self.pending_patches()
        with first, second:
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)

    def test_unknown_issue_create_without_effect_refuses_without_retry(self):
        provider = Provider()
        provider.create_unknown = True
        provider.create_effect = False
        with self.assertRaisesRegex(atom.AtomRefusal, "github.issue.outcome"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)
        with self.assertRaisesRegex(atom.AtomRefusal, "github.issue.outcome"):
            atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(provider.create_calls, 1)

    def test_authorization_must_be_external_exact_and_clean(self):
        inside = self.root / "authorization.json"
        inside.write_bytes(self.path.read_bytes())
        digest = hashlib.sha256(inside.read_bytes()).hexdigest()
        with self.assertRaisesRegex(atom.AtomRefusal, "authorization.path"):
            atom.validate_authorization(inside, digest)
        (self.root / "dirty").write_text("dirty")
        with self.assertRaisesRegex(atom.AtomRefusal, "git.status"):
            atom.validate_authorization(self.path, self.digest)

    def test_provider_credentials_are_removed_from_child_environment(self):
        with patch.dict(os.environ, {"GH_TOKEN": "secret", "GITHUB_TOKEN": "other",
                                     "SAFE_VALUE": "kept"}, clear=True):
            child = atom.clean_child_env()
        self.assertNotIn("GH_TOKEN", child)
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertEqual(child["SAFE_VALUE"], "kept")

    def test_one_entry_routes_publication_landing_and_resolution(self):
        provider = Provider()
        self.ready_issue(provider)
        paths = atom.artifact_paths(self.path)
        claim = {
            "worktree_path": str(self.root), "worktree_name": "soodles-131-0-execute",
            "head": "b" * 40, "tree": "c" * 40, "base_head": self.base,
        }

        def claim_ready(_authorization, _subject, output):
            atom.save_json(output, claim, fresh=True)
            return Result(0)

        def accepted(_authorization, _claim, output):
            value = {"repository": "ed3c/soodles",
                     "scope": "candidate runtime acceptance",
                     "candidate": {"head": "b" * 40, "tree": "c" * 40},
                     "authorizes_landing": False}
            atom.save_json(output, value, fresh=True)
            return value

        publication = {
            "pr": {"number": 132, "url": "https://github.com/ed3c/soodles/pull/132"},
            "head": "b" * 40, "tree": "c" * 40, "authorizes_landing": False,
        }
        run = {"id": 7, "run_attempt": 1, "status": "completed"}
        jobs = {"jobs": []}

        def start(landing_claim, _snapshot, checkpoint):
            atom.save_json(checkpoint, {"claim": landing_claim}, fresh=True)
            return {"action": "readback"}

        first_transition = {"action": "dispatch"}
        second_transition = {"action": "reconcile"}
        transitions = [first_transition, second_transition]

        def advance(_checkpoint, _snapshot):
            return transitions.pop(0)

        dispatch = {"request": {"action": "merge", "pr_number": 132,
                                "expected_head_sha": "b" * 40, "merge_method": "merge"}}
        resolved = {"classification": "RESOLVED", "phase": "resolved", "next": None}
        patches = [
            patch("issue_atom.issue_execution.supervised", return_value={"published": True}),
            patch("issue_atom._run_claim", side_effect=claim_ready),
            patch("issue_atom._accept", side_effect=accepted),
            patch("issue_atom.candidate_publication.publish", return_value=publication),
            patch("issue_atom.select_run", return_value=(run, jobs)),
            patch("issue_atom.provider_snapshot", return_value={"fixture": True}),
            patch("issue_atom.landing.start", side_effect=start),
            patch("issue_atom.landing.advance", side_effect=advance),
            patch("issue_atom.landing.dispatch", return_value=dispatch),
            patch("issue_atom.landing.reconcile", return_value=resolved),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        first = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(first["waiting_on"], "fresh provider readback")
        self.assertEqual(first["next"]["argv"], atom.same_command(self.path))
        self.assertEqual(provider.merge_calls, 1)
        second = atom.run(self.path, environ=self.env, provider=provider)
        self.assertEqual(second["status"], "resolved")
        self.assertIsNone(second["next"])
        self.assertFalse(second["authorizes_landing"])
        self.assertTrue(paths["landing"].exists())


if __name__ == "__main__":
    unittest.main()
