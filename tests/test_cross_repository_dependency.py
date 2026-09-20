"""Dependency eligibility for the single Soodles #111 to Ops #21 edge."""
import copy
from pathlib import Path
import tempfile
import unittest

import dependency_binding
import landing
from test_cross_repository_delivery import (
    OPS, SOODLES, UP_HEAD, UP_MERGE, fixture,
)


class CrossRepositoryDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "checkpoint.json"
        self.claim, self.snapshot = fixture(landing.verifier_digest())

    def refused(self, snapshot, field, *, dependency=True):
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(self.claim, snapshot, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"], field)
        self.assertFalse(self.checkpoint.exists())
        if dependency:
            self.assertEqual(raised.exception.next_action["owner"], "GitHub")
            self.assertEqual(raised.exception.next_action["operation"], "start")
            self.assertEqual(set(k for k in raised.exception.next_action["requests"]
                                 if k.startswith("dependency_")), {
                "dependency_issue", "dependency_pr", "dependency_commit",
                "dependency_branch", "dependency_ancestry", "dependency_run",
                "dependency_jobs"})

    def test_complete_result_reaches_existing_consumer_acceptance(self):
        result = landing.start(self.claim, self.snapshot, self.checkpoint)
        self.assertTrue(self.checkpoint.exists())
        self.assertEqual(result["phase"], "admitted")
        self.assertEqual(result["next"]["operation"], "advance")
        requests = result["next"]["requests"]
        self.assertTrue(all(f"/repos/{SOODLES}/" in request["url"]
                            for key, request in requests.items()
                            if key.startswith("dependency_")))
        self.assertTrue(all(f"/repos/{OPS}/" in request["url"]
                            for key, request in requests.items()
                            if not key.startswith("dependency_")))

    def test_issue_closure_alone_is_not_satisfaction(self):
        closure = {key: copy.deepcopy(value) for key, value in self.snapshot.items()
                   if not key.startswith("dependency_") or key == "dependency_issue"}
        self.refused(closure, "dependency.pr")

    def test_foreign_repository_and_wrong_revision_refuse(self):
        foreign = copy.deepcopy(self.snapshot)
        foreign["dependency_pr"]["head"]["repo"]["full_name"] = OPS
        self.refused(foreign, "dependency.pr.repository")
        wrong = copy.deepcopy(self.snapshot)
        wrong["dependency_commit"]["sha"] = UP_HEAD
        self.refused(wrong, "dependency.commit.sha")

    def test_stale_or_incomplete_producer_receipt_refuses(self):
        stale = copy.deepcopy(self.snapshot)
        stale["dependency_ancestry"]["status"] = "behind"
        self.refused(stale, "dependency.ancestry.status")
        incomplete = copy.deepcopy(self.snapshot)
        incomplete["dependency_jobs"]["jobs"][0]["steps"] = []
        self.refused(incomplete, "dependency.job.acceptance")

    def test_forward_main_keeps_exact_artifact_eligible(self):
        advanced = copy.deepcopy(self.snapshot)
        current = "a" * 40
        advanced["dependency_branch"]["commit"]["sha"] = current
        advanced["dependency_ancestry"].update(
            status="ahead", head_commit={"sha": current}, total_commits=1,
            commits=[{"sha": current}])
        result = landing.start(self.claim, advanced, self.checkpoint)
        self.assertEqual(result["phase"], "admitted")

    def test_consumer_acceptance_still_controls_after_dependency(self):
        incomplete = copy.deepcopy(self.snapshot)
        incomplete["jobs"]["jobs"][1]["steps"] = [
            step for step in incomplete["jobs"]["jobs"][1]["steps"]
            if step["name"] != "Run python scripts/verify_postgres.py"]
        self.refused(incomplete, "job.acceptance", dependency=False)

    def test_only_registered_consumer_gets_dependency_requests(self):
        self.assertEqual(set(dependency_binding.requests(self.claim)), {
            "dependency_issue", "dependency_pr", "dependency_commit",
            "dependency_branch", "dependency_ancestry", "dependency_run",
            "dependency_jobs"})
        self.assertEqual(dependency_binding.requests({"repository": SOODLES, "issue": 113}), {})


if __name__ == "__main__":
    unittest.main()
