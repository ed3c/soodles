"""Frozen process controls plus real shared-owner and effect-boundary controls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import candidate_publication as publication
import issue_admission as gate
import issue_admission as admission
import landing
from test_candidate_publication import Provider, Result
import test_landing

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/experiments/comparison-delivery-gate"
PINS = {
    "fixture.py": "58f54b71b67c5fc229d8ca50a25f72cf428696af7d5f931d352e71afeadbcb24",
    "oracle.py": "64ade25a8e8046c4247acb6bb4f9712dbba56b8e7b875ba8b8b9dac771be0b40",
    "protocol.md": "8a14ea9cf62e40460e3d796d9d79a249312c335b62c506f9321a2fb389eee9e7",
    "task.md": "819a7c462070c15a136b69ef257cb48944e667cd6ef5672f47fd3c2d2b0853bd",
}


def fixture_module():
    for name, expected in PINS.items():
        if hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() != expected:
            raise AssertionError("frozen external bytes changed: " + name)
    spec = importlib.util.spec_from_file_location("comparison_fixture", FROZEN / "fixture.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def body(contract):
    return "<!-- soodles:execution-v1 -->\n```json\n" + json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->\n"


class ComparisonGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.fixture = fixture_module()
        cls.value = cls.fixture.build(ROOT, Path(cls.temp.name) / "control" / ".worktrees" / "candidate")
        cls.root = Path(cls.value["root"])
        cls.issue = json.loads(Path(cls.value["issue"]).read_text())
        cls.contract = admission.parse_contract(cls.issue["body"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def binding(self, contract=None):
        contract = self.contract if contract is None else contract
        return {"repository": "ed3c/soodles", "issue": 1, "base_head": self.value["base"],
                "write_paths": contract["write_paths"], "contract": contract}

    def test_frozen_nine_case_process_oracle(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "oracle"
            process = subprocess.run([sys.executable, "-B", str(FROZEN / "oracle.py"), str(ROOT), str(output)],
                                     capture_output=True, text=True, timeout=240)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertEqual(receipt["classification"], "GREEN")
            self.assertEqual(len(receipt["records"]), 9)
            for record in receipt["records"]:
                result = json.loads(record["stdout"])
                if record["case"] not in ("ordinary", "admitted"):
                    self.assertEqual(result["next"]["owner"], "supervisor")
                    self.assertEqual(result["next"]["kind"], "input")
                    self.assertEqual(result["next"]["help_argv"], gate.COMPARISON_HELP)
                    self.assertNotIn("request", result)

    def test_direct_shared_owner_matches_final_head_and_cleans_replayer(self):
        receipt = admission.verify_candidate(self.root, self.value["base"], self.value["head"], self.issue)
        self.assertEqual(receipt["comparison"]["decision"], "ADMIT_IMPROVEMENT")
        self.assertEqual(receipt["comparison"]["head"], receipt["head"])
        self.assertEqual(receipt["tree"], self.fixture.git(self.root, "rev-parse", "HEAD^{tree}"))
        self.assertFalse(receipt["authorizes_landing"])
        actual_run = subprocess.run
        observed = []

        def capture(argv, **kwargs):
            if argv[0] == sys.executable:
                observed.append(kwargs)
                self.assertEqual(set(kwargs["env"]), {"HOME", "TMPDIR"})
                self.assertTrue(kwargs["start_new_session"])
                self.assertEqual(kwargs["timeout"], 30)
            return actual_run(argv, **kwargs)

        with patch.object(gate.subprocess, "run", side_effect=capture):
            admission.validate_delivery_paths(self.root, self.value["base"], self.value["head"], self.binding())
        self.assertEqual(len(observed), 1)
        self.assertFalse(Path(observed[0]["cwd"]).exists())

    def test_malformed_requirement_refuses_without_replayer(self):
        mutations = [
            lambda c: c.pop("comparison"),
            lambda c: c["comparison"].update(kind="admission_recovery"),
            lambda c: c["comparison"].update(extra=True),
            lambda c: c["comparison"]["raw"].update(path="../raw"),
            lambda c: c["comparison"]["raw"].update(path="unrequired.json"),
            lambda c: c["comparison"]["subject"].update(issue=True),
            lambda c: c["comparison"]["analyzers"]["observer"].update(revision="head"),
            lambda c: c["comparison"]["analyzers"]["observer"].update(path="plugin.py"),
            lambda c: c["comparison"]["instructions"][0].update(treatment_sha256="wrong"),
        ]
        for mutation in mutations:
            contract = copy.deepcopy(self.contract)
            mutation(contract)
            with self.subTest(contract=contract), patch.object(gate.subprocess, "run") as run:
                with self.assertRaises(admission.AdmissionRefusal):
                    admission.parse_contract(body(contract))
                run.assert_not_called()

    def test_replay_timeout_preserves_raw_output_and_cleans_extracted_bytes(self):
        actual_run = subprocess.run
        directories = []
        def timeout(argv, **kwargs):
            if argv[0] == sys.executable:
                directories.append(kwargs["cwd"])
                raise subprocess.TimeoutExpired(argv, 30, output=b"partial result", stderr=b"timed out")
            return actual_run(argv, **kwargs)
        with patch.object(gate.subprocess, "run", side_effect=timeout):
            with self.assertRaises(gate.ComparisonRefusal) as caught:
                gate.verify_comparison(self.root, self.value["base"], self.value["head"], self.binding())
        self.assertEqual(caught.exception.comparison["stdout"], "partial result")
        self.assertTrue(caught.exception.comparison["timed_out"])
        self.assertEqual(len(directories), 1)
        self.assertFalse(Path(directories[0]).exists())

    def test_direct_owner_rejects_foreign_binding_and_missing_comparison(self):
        binding = self.binding()
        binding["issue"] = 2
        with self.assertRaisesRegex(gate.ComparisonRefusal, "comparison.subject"):
            admission.validate_delivery_paths(self.root, self.value["base"], self.value["head"], binding)
        binding = copy.deepcopy(self.binding())
        del binding["contract"]["comparison"]
        with self.assertRaises(gate.ComparisonRefusal):
            admission.validate_delivery_paths(self.root, self.value["base"], self.value["head"], binding)

    def test_nonregression_requires_its_exact_external_target(self):
        with tempfile.TemporaryDirectory() as folder:
            value = self.fixture.build(ROOT, Path(folder) / "nonregression", "weak_target")
            issue = json.loads(Path(value["issue"]).read_text())
            contract = admission.parse_contract(issue["body"])
            contract["comparison"]["admission_target"] = "nonregression"
            issue["body"] = body(contract)
            receipt = admission.verify_candidate(value["root"], value["base"], value["head"], issue)
            self.assertEqual(receipt["comparison"]["decision"], "ADMIT_NONREGRESSION")
            contract["comparison"]["admission_target"] = "improvement"
            issue["body"] = body(contract)
            with self.assertRaises(gate.ComparisonRefusal):
                admission.verify_candidate(value["root"], value["base"], value["head"], issue)

    def test_raw_packet_and_observations_cannot_substitute_instruction(self):
        for field in ("packet", "observation", "family"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                value = self.fixture.build(ROOT, Path(folder) / "raw")
                root = Path(value["root"])
                issue = json.loads(Path(value["issue"]).read_text())
                contract = admission.parse_contract(issue["body"])
                raw = json.loads((root / self.fixture.RAW).read_text())
                if field == "packet":
                    raw["runs"][0]["packet"]["instruction"]["sha256"] = "f" * 64
                elif field == "observation":
                    raw["runs"][0]["instruction_observations"][0]["bytes"] = True
                else:
                    raw["runs"][0]["packet"]["case"] = "admission_recovery"
                data = self.fixture.encoded(raw)
                (root / self.fixture.RAW).write_bytes(data)
                head = self.fixture.commit(root, "Plant internally foreign raw instruction")
                contract["comparison"]["raw"]["sha256"] = gate.comparison_digest(data)
                binding = {**self.binding(contract), "base_head": value["base"]}
                # Exact raw Git bytes and external hash now agree; the actual
                # packet/observation still must match the selected instruction.
                actual_run = subprocess.run
                def guard(argv, **kwargs):
                    self.assertNotEqual(argv[0], sys.executable, "analyzer ran before binding refusal")
                    return actual_run(argv, **kwargs)
                with patch.object(gate.subprocess, "run", side_effect=guard):
                    with self.assertRaises(gate.ComparisonRefusal):
                        gate.verify_comparison(root, value["base"], head, binding)

    def publication_inputs(self):
        runtime = self.root.parent.parent / ".noodle"
        events = runtime / "sessions" / "session-1" / "events.ndjson"
        events.parent.mkdir(parents=True, exist_ok=True)
        snapshot = runtime / "state.snapshot.json"
        snapshot.write_text('{}\n')
        events.write_text('{}\n')
        self.fixture.git(self.root, "remote", "add", "origin", "git@github.com:ed3c/soodles.git")
        self.addCleanup(lambda: self.fixture.git(self.root, "remote", "remove", "origin"))
        head = self.value["head"]
        tree = self.fixture.git(self.root, "rev-parse", "HEAD^{tree}")
        claim = {"schema_version": 1, "owner": "Noodle", "repository": "ed3c/soodles",
                 "subject": "ed3c/soodles#1", "order_id": "soodles-1", "stage_index": 0,
                 "attempt_id": "soodles-1:0:0", "session_id": "session-1",
                 "worktree_name": "main", "worktree_path": str(self.root), "branch": "main",
                 "head": head, "tree": tree, "base_branch": "main", "base_head": self.value["base"],
                 "push_remote": "origin", "remote_url": "git@github.com:ed3c/soodles.git",
                 "evidence": {"canonical_snapshot_sha256": publication._digest(snapshot),
                              "session_events_sha256": publication._digest(events)},
                 "authorizes_provider_write": False, "authorizes_landing": False}
        acceptance = {"repository": "ed3c/soodles", "scope": "candidate runtime acceptance",
                      "candidate": {"head": head, "tree": tree}, "authorizes_landing": False}
        return acceptance, claim

    def test_publication_replays_before_push_and_pr_and_rejects_changed_subject(self):
        acceptance, claim = self.publication_inputs()
        fixture_issue = self.issue

        class FreshProvider(Provider):
            def issue(self, number):
                return {**fixture_issue, "title": "Synthetic publication", "body": self.issue_body}

        for case in ("foreign", "matching", "changed_after_push"):
            provider = FreshProvider(self.value["base"], self.issue["body"])
            invalid = copy.deepcopy(self.contract)
            invalid["comparison"]["subject"]["issue"] = 2
            if case == "foreign":
                provider.issue_body = body(invalid)
            pushes = []

            def push(*args, **kwargs):
                pushes.append(args)
                provider.ref = claim["head"]
                if case == "changed_after_push":
                    downgraded = copy.deepcopy(self.contract)
                    downgraded["schema"] = 3
                    del downgraded["comparison"]
                    provider.issue_body = body(downgraded)
                return Result()

            with self.subTest(case=case):
                if case == "matching":
                    result = publication.publish(self.root, acceptance, claim, provider, push=push)
                    self.assertEqual(result["status"], "created")
                    self.assertEqual(provider.create_calls, 1)
                else:
                    with self.assertRaises(gate.ComparisonRefusal):
                        publication.publish(self.root, acceptance, claim, provider, push=push)
                    self.assertEqual(provider.create_calls, 0)
                self.assertEqual(len(pushes), 0 if case == "foreign" else 1)

    def landing_inputs(self, folder):
        fixture = test_landing.LandingTests("test_intent_is_persisted_before_exact_head_request_and_no_unchanged_retry")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        claim, snapshot = copy.deepcopy(fixture.claim), copy.deepcopy(fixture.snapshot)
        tree = self.fixture.git(self.root, "rev-parse", "HEAD^{tree}")
        claim.update(head=self.value["head"], tree=tree, base_head=self.value["base"],
                     control_root=str(self.root.parent), worktree="candidate")
        # Local owner reads the actual candidate Git objects under its control root.
        claim.update(control_root=str(self.root.parent.parent), worktree="candidate")
        contract = self.contract
        envelope = {"schema": 1, "repository": claim["repository"], "issue": 1,
                    "body_sha256": admission.body_digest(self.issue["body"]),
                    "body_updated_at": self.issue["updated_at"], "owner": contract["owner"],
                    "write_paths": contract["write_paths"], "base_head": claim["base_head"],
                    "execution": {"control_root": claim["control_root"], "worktree": claim["worktree"],
                                  "order_id": "soodles-1", "stage_index": 0, "task": "Fixture",
                                  "source_head": claim["base_head"], "carrier": {"platform": "fixture"}}}
        path = Path(folder) / "envelope.json"
        path.write_text(json.dumps(envelope))
        claim["execution_envelope"] = {"path": str(path), "sha256": gate.comparison_digest(path.read_bytes())}
        snapshot["pr"]["head"].update(sha=claim["head"], ref=claim["worktree"])
        snapshot["pr"]["base"]["sha"] = claim["base_head"]
        snapshot["commit"] = {"sha": claim["head"], "tree": {"sha": tree}}
        snapshot["run"]["head_sha"] = claim["head"]
        snapshot["jobs"]["jobs"][0]["head_sha"] = claim["head"]
        snapshot["branch"]["commit"]["sha"] = claim["base_head"]
        snapshot["issue"] = copy.deepcopy(self.issue)
        return claim, snapshot, envelope

    def test_landing_start_advance_dispatch_consume_fresh_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            claim, snapshot, envelope = self.landing_inputs(folder)
            checkpoint = Path(folder) / "checkpoint.json"
            original = copy.deepcopy(snapshot)
            landing.start(claim, snapshot, checkpoint)
            landing.advance(checkpoint, snapshot)
            before = checkpoint.read_bytes()
            snapshot["issue"]["body"] += "changed"
            with self.assertRaises(landing.LandingRefusal):
                landing.dispatch(checkpoint, snapshot)
            self.assertEqual(checkpoint.read_bytes(), before)
            request = landing.dispatch(checkpoint, original)["request"]
            self.assertEqual(request["expected_head_sha"], claim["head"])

            bad = copy.deepcopy(self.contract)
            bad["comparison"]["subject"]["issue"] = 2
            snapshot["issue"]["body"] = body(bad)
            envelope["body_sha256"] = admission.body_digest(snapshot["issue"]["body"])
            path = Path(claim["execution_envelope"]["path"])
            path.write_text(json.dumps(envelope))
            claim["execution_envelope"]["sha256"] = gate.comparison_digest(path.read_bytes())
            with self.assertRaises(landing.LandingRefusal) as caught:
                landing.start(claim, snapshot, Path(folder) / "rejected.json")
            self.assertEqual(caught.exception.invalid["field"], "comparison.subject")
            self.assertFalse((Path(folder) / "rejected.json").exists())
            with self.assertRaises(landing.LandingRefusal):
                landing.execution_binding(claim, snapshot["issue"])

    def test_cloud_fresh_schema4_refuses_without_request(self):
        with tempfile.TemporaryDirectory() as folder:
            claim, snapshot, _ = self.landing_inputs(folder)
            claim.pop("execution_envelope")
            claim.pop("control_root")
            # Direct owner entry does not depend on any green workflow projection.
            with self.assertRaises(landing.LandingRefusal) as caught:
                landing.execution_binding(claim, snapshot["issue"])
            self.assertEqual(caught.exception.next_action["required"], ["supported_local_comparison_delivery"])
            self.assertEqual(caught.exception.next_action["help_argv"], gate.COMPARISON_HELP)
            snapshot["jobs"]["jobs"][0]["steps"].append({
                "name": "Verify exact candidate evidence from fresh Issue readback",
                "status": "completed", "conclusion": "success"})
            checkpoint = Path(folder) / "cloud.json"
            with self.assertRaises(landing.LandingRefusal):
                landing.start(claim, snapshot, checkpoint)
            self.assertFalse(checkpoint.exists())
            ordinary = copy.deepcopy(self.contract)
            ordinary["schema"] = 3
            del ordinary["comparison"]
            selected = snapshot["issue"]["body"]
            snapshot["issue"]["body"] = body(ordinary)
            landing.start(claim, snapshot, checkpoint)
            landing.advance(checkpoint, snapshot)
            before = checkpoint.read_bytes()
            snapshot["issue"]["body"] = selected
            for operation in (landing.advance, landing.dispatch):
                with self.assertRaises(landing.LandingRefusal) as refused:
                    operation(checkpoint, snapshot)
                output = landing.refusal_output(refused.exception, operation.__name__)
                self.assertEqual(output["next"]["required"], ["supported_local_comparison_delivery"])
                self.assertNotIn("request", output)
                self.assertFalse(output["authorizes_landing"])
                self.assertEqual(checkpoint.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
