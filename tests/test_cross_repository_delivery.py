"""One bounded Ops target proves repository identity reaches every owner."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import github_reader
import issue_admission
import landing


OPS = "ed3c/ops-reconciliation-copilot"
HEAD = "e3c530340aa8d8070206b0a893b9a9aef5e462d0"
TREE = "f0a2032ef3f4f1195a8deaf35175b94e211607c3"
BASE = "24a56d18661630b0dba97dcb0b057dce07b0ab32"
RUN = 35217009263


def step(name):
    return {"name": name, "status": "completed", "conclusion": "success"}


def fixture(identity, *, draft=False):
    repo = {"full_name": OPS}
    claim = {"repository": OPS, "issue": 21, "pr": 22, "head": HEAD,
             "tree": TREE, "base_head": BASE, "run_id": RUN, "run_attempt": 1,
             "worktree": "research-jev-foundation-21", "verifier_sha256": identity}
    common = ["Run python scripts/verify_runtime.py", "Run python scripts/verify_owner.py",
              "Run python scripts/verify_browser.py", "Run python scripts/verify_mapping.py"]
    jobs = [
        {"id": 1, "name": "runtime", "run_id": RUN, "head_sha": HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [step(name) for name in common]},
        {"id": 2, "name": "postgres", "run_id": RUN, "head_sha": HEAD,
         "status": "completed", "conclusion": "success",
         "steps": [step(name) for name in [*common[:2], "Run python scripts/verify_postgres.py", *common[2:]]]},
    ]
    snapshot = {
        "pr": {"number": 22, "html_url": f"https://github.com/{OPS}/pull/22",
               "body": f"Refs {OPS}#21", "head": {"repo": repo, "sha": HEAD, "ref": claim["worktree"]},
               "base": {"repo": repo, "sha": BASE, "ref": "main"},
               "merged": False, "state": "open", "draft": draft, "mergeable": True},
        "issue": {"number": 21, "html_url": f"https://github.com/{OPS}/issues/21", "state": "open"},
        "run": {"id": RUN, "run_attempt": 1, "repository": repo, "head_repository": repo,
                "head_sha": HEAD, "event": "pull_request", "path": ".github/workflows/runtime.yml",
                "status": "completed", "conclusion": "success"},
        "commit": {"sha": HEAD, "tree": {"sha": TREE}},
        "jobs": {"total_count": 2, "jobs": jobs},
        "branch": {"name": "main", "commit": {"sha": BASE}},
    }
    return claim, snapshot


class CrossRepositoryDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "checkpoint.json"
        self.claim, self.snapshot = fixture(landing.verifier_digest())

    def test_ops_acceptance_produces_only_ops_readbacks_and_request(self):
        start = landing.start(self.claim, self.snapshot, self.checkpoint)
        requests = start["next"]["requests"]
        self.assertTrue(all(f"/repos/{OPS}/" in item["url"] for item in requests.values()))
        prepared = landing.advance(self.checkpoint, self.snapshot)
        self.assertEqual(prepared["action"], "dispatch")
        offered = landing.dispatch(self.checkpoint, self.snapshot)
        self.assertEqual(offered["request"], {
            "action": "merge", "repository_full_name": OPS, "pr_number": 22,
            "expected_head_sha": HEAD, "merge_method": "merge"})
        self.assertEqual(landing.read(self.checkpoint)["writes_offered"], ["merge"])

    def test_real_current_draft_and_incomplete_acceptance_refuse_without_state(self):
        _, draft = fixture(landing.verifier_digest(), draft=True)
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(self.claim, draft, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"], "pr.state")
        self.assertFalse(self.checkpoint.exists())
        missing = copy.deepcopy(self.snapshot)
        missing["jobs"]["jobs"][1]["steps"] = [
            item for item in missing["jobs"]["jobs"][1]["steps"]
            if item["name"] != "Run python scripts/verify_postgres.py"]
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(self.claim, missing, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"], "job.acceptance")
        self.assertFalse(self.checkpoint.exists())

    def test_unsupported_repository_refuses_before_reader_transport_or_checkpoint(self):
        foreign = {**self.claim, "repository": "ed3c/unregistered"}
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(foreign, self.snapshot, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"], "claim.repository")
        with patch.object(github_reader, "_request") as transport:
            with self.assertRaises(issue_admission.AdmissionRefusal) as raised:
                github_reader.issue("ed3c/unregistered", 1)
        self.assertEqual(raised.exception.invalid["field"], "issue.repository")
        transport.assert_not_called()
        self.assertFalse(self.checkpoint.exists())


if __name__ == "__main__":
    unittest.main()
