"""Supervisor-selected dependency eligibility without a source edge registry."""
import copy
from pathlib import Path
import tempfile
import unittest

import dependency_binding
import landing
from test_cross_repository_delivery import (
    OPS, SOODLES, UP_HEAD, UP_MERGE, dependency_claim, fixture,
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
                "dependency_0_issue", "dependency_0_pr", "dependency_0_commit",
                "dependency_0_branch", "dependency_0_ancestry", "dependency_0_run",
                "dependency_0_jobs"})

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
                   if not key.startswith("dependency_") or key == "dependency_0_issue"}
        self.refused(closure, "dependency[0].pr")

    def test_foreign_repository_and_wrong_revision_refuse(self):
        foreign = copy.deepcopy(self.snapshot)
        foreign["dependency_0_pr"]["head"]["repo"]["full_name"] = OPS
        self.refused(foreign, "dependency[0].pr.repository")
        wrong = copy.deepcopy(self.snapshot)
        wrong["dependency_0_commit"]["sha"] = UP_HEAD
        self.refused(wrong, "dependency[0].commit.sha")

    def test_stale_or_incomplete_producer_receipt_refuses(self):
        stale = copy.deepcopy(self.snapshot)
        stale["dependency_0_ancestry"]["status"] = "behind"
        self.refused(stale, "dependency[0].ancestry.status")
        incomplete = copy.deepcopy(self.snapshot)
        incomplete["dependency_0_jobs"]["jobs"][0]["steps"] = []
        self.refused(incomplete, "dependency[0].job.acceptance")

    def test_forward_main_keeps_exact_artifact_eligible(self):
        advanced = copy.deepcopy(self.snapshot)
        current = "a" * 40
        advanced["dependency_0_branch"]["commit"]["sha"] = current
        advanced["dependency_0_ancestry"].update(
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

    def test_claim_selects_edges_without_a_source_consumer_registry(self):
        expected = {f"dependency_0_{kind}" for kind in
                    ("issue", "pr", "commit", "branch", "ancestry", "run", "jobs")}
        self.assertEqual(set(dependency_binding.requests(self.claim, landing.require)), expected)
        alternate = {**self.claim, "repository": SOODLES, "issue": 115,
                     "dependencies": [dependency_claim()]}
        self.assertEqual(set(dependency_binding.requests(alternate, landing.require)), expected)
        no_dependencies = {key: value for key, value in alternate.items()
                           if key != "dependencies"}
        self.assertEqual(dependency_binding.requests(no_dependencies, landing.require), {})

    def test_malformed_or_duplicate_claim_dependency_refuses_before_state(self):
        malformed = copy.deepcopy(self.claim)
        malformed["dependencies"][0]["repository"] = "not-a-repository"
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(malformed, self.snapshot, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"],
                         "claim.dependencies[0].repository")
        self.assertFalse(self.checkpoint.exists())
        duplicate = copy.deepcopy(self.claim)
        duplicate["dependencies"].append(copy.deepcopy(duplicate["dependencies"][0]))
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(duplicate, self.snapshot, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"],
                         "claim.dependencies.identity")
        self.assertFalse(self.checkpoint.exists())

    def test_every_selected_edge_gets_stable_requests_and_must_be_present(self):
        second = copy.deepcopy(dependency_claim())
        second.update(issue=113, pr=114, candidate_head="a" * 40,
                      tree="b" * 40, revision="c" * 40, run_id=99)
        multiple = copy.deepcopy(self.claim)
        multiple["dependencies"].append(second)
        requests = dependency_binding.requests(multiple, landing.require)
        self.assertEqual({key for key in requests if key.startswith("dependency_1_")},
                         {f"dependency_1_{kind}" for kind in
                          ("issue", "pr", "commit", "branch", "ancestry", "run", "jobs")})
        with self.assertRaises(landing.LandingRefusal) as raised:
            landing.start(multiple, self.snapshot, self.checkpoint)
        self.assertEqual(raised.exception.invalid["field"], "dependency[1].issue")
        self.assertFalse(self.checkpoint.exists())


if __name__ == "__main__":
    unittest.main()
