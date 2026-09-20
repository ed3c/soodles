import copy
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import issue_admission as admission


def issue_fixture():
    contract = {
        "schema": 1, "trigger": "An old body could reach execution.", "source": "provider Issue 18",
        "owner": "Soodles Issue admission", "changes": ["Bind the real consumers before effects."],
        "write_paths": ["allowed.py", "renamed.py", "資料[1].txt"],
        "behavior": ["Reject obsolete body before effects."],
        "defect_controls": ["Remove body binding: the same control must fail."],
        "non_cases": ["Current supervised runtime-only work remains legal."],
        "dependencies": [{"repository": "ed3c/noodle", "issue": 82, "owner": "Noodle",
                          "evidence": "An exact, externally supplied delivery receipt."}],
        "acceptance": "Canonical acceptance on the final clean head.",
        "delivery": "Use the existing landing next/request.",
        "reconciliation": "Noodle cleanup and provider readback.",
        "feature_scope": "No general scheduler or filesystem confinement claim.",
    }
    body = ("Free surrounding prose.\n<!-- soodles:execution-v1 -->\n```json\n"
            + json.dumps(contract, indent=2) + "\n```\n<!-- /soodles:execution-v1 -->\n")
    issue = {"url": "https://api.github.com/repos/ed3c/soodles/issues/18",
             "html_url": "https://github.com/ed3c/soodles/issues/18", "number": 18,
             "body": body, "updated_at": "2026-09-16T15:00:00Z", "state": "open"}
    envelope = {"schema": 1, "repository": "ed3c/soodles", "issue": 18,
                "body_sha256": admission.body_digest(body), "body_updated_at": issue["updated_at"],
                "owner": contract["owner"], "write_paths": contract["write_paths"], "base_head": "a" * 40,
                "execution": {"control_root": "/supervisor/control", "worktree": "soodles-18-0-execute",
                              "order_id": "soodles-18", "stage_index": 0,
                              "task": "Execute the admitted bounded fixture task.", "source_head": "a" * 40,
                              "carrier": {"platform": "darwin_arm64"}}}
    return issue, envelope


class IssueAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.issue, self.envelope = issue_fixture()

    def refused(self, field, issue=None, envelope=None):
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            admission.validate_issue(self.issue if issue is None else issue,
                                     self.envelope if envelope is None else envelope)
        self.assertEqual(caught.exception.invalid["field"], field)
        self.assertTrue(caught.exception.next["owner"])
        self.assertTrue(caught.exception.next["required"])

    def test_current_provider_binding_is_normalized_but_non_authorizing(self):
        binding = admission.validate_issue(self.issue, self.envelope)
        self.assertEqual(binding["write_paths"], sorted(self.envelope["write_paths"]))
        self.assertEqual(binding["issue"], 18)
        self.assertFalse(binding["authorizes_landing"])
        # The shared gate does not demand nested-Agent capability for every route.
        self.assertNotIn("codex", binding["execution"]["carrier"])

    def test_current_body_digest_cannot_grant_missing_or_wider_authority(self):
        self.refused("envelope.fields", envelope={})
        altered = copy.deepcopy(self.envelope)
        altered["write_paths"].append("unauthorized.py")
        self.refused("envelope.write_paths", envelope=altered)
        altered = copy.deepcopy(self.envelope)
        altered["owner"] = "candidate-selected owner"
        self.refused("envelope.owner", envelope=altered)

    def test_identity_is_derived_from_provider_fields_not_title_or_prose(self):
        for key, value in (("url", "https://api.github.com/repos/foreign/repo/issues/18"),
                           ("html_url", "https://github.com/ed3c/soodles/issues/19"),
                           ("number", 19), ("number", True), ("state", "closed")):
            with self.subTest(key=key, value=value):
                issue = {**self.issue, key: value}
                self.refused("issue." + key, issue=issue)
        self.refused("issue.pull_request", issue={**self.issue, "pull_request": {}})

    def test_whole_body_and_revision_changes_require_fresh_envelope(self):
        changed = {**self.issue, "body": self.issue["body"] + "An unrelated prose amendment.\n"}
        self.refused("issue.body_sha256", issue=changed)
        self.refused("issue.updated_at", issue={**self.issue, "updated_at": "2026-09-16T15:01:00Z"})
        # Equivalent presentation is valid when the external supervisor rebinds it.
        envelope = {**self.envelope, "body_sha256": admission.body_digest(changed["body"])}
        result = admission.validate_issue(changed, envelope)
        self.assertEqual(result["contract"], admission.parse_contract(self.issue["body"]))

    def test_one_active_contract_is_required(self):
        self.refused("issue.contract.count", issue={**self.issue, "body": "Only prose."})
        self.refused("issue.contract.count", issue={**self.issue, "body": self.issue["body"] * 2})
        malformed = self.issue["body"].replace('"schema": 1', '"schema":')
        self.refused("issue.contract.json", issue={**self.issue, "body": malformed})

    def test_human_template_and_machine_contract_have_the_same_fields(self):
        path = Path(admission.__file__).resolve().parent / ".github/ISSUE_TEMPLATE/execution.yml"
        template = path.read_text()
        block = re.search(r"```json\s*\n(.*?)\n\s*```", template, re.DOTALL)
        self.assertIsNotNone(block)
        self.assertEqual(set(json.loads(block.group(1))), admission.CONTRACT_FIELDS)
        with self.assertRaises(admission.AdmissionRefusal):
            admission.parse_contract(template)

    def test_schema_two_requires_manifest_and_evidence_inside_write_boundary(self):
        contract = admission.parse_contract(
            self.issue["body"].replace(
                '"schema": 1,',
                '"schema": 2,\n'
                '  "required_paths": ["allowed.py"],\n'
                '  "evidence_manifest": "allowed.py",',
                1))
        self.assertEqual(contract["required_paths"], ["allowed.py"])
        self.assertEqual(contract["evidence_manifest"], "allowed.py")
        outside = self.issue["body"].replace(
            '"schema": 1,',
            '"schema": 2,\n'
            '  "required_paths": ["outside.json"],\n'
            '  "evidence_manifest": "outside.json",',
            1)
        with self.assertRaises(admission.AdmissionRefusal) as caught:
            admission.parse_contract(outside)
        self.assertEqual(
            caught.exception.invalid["field"],
            "issue.contract.required_paths")

    def test_invalid_paths_and_duplicate_paths_refuse(self):
        for value in ("../escape", "/absolute", "a/../b", "a//b", "./a", "a\\b", ".git/config", "a\nfile"):
            with self.subTest(value=value), self.assertRaises(admission.AdmissionRefusal) as caught:
                admission.git_path(value)
            self.assertEqual(caught.exception.invalid["value"], value)
        with self.assertRaises(admission.AdmissionRefusal):
            admission.path_set(["same", "same"], "write_paths")
        self.assertEqual(admission.git_path("資料[1].txt"), "資料[1].txt")

    def test_candidate_local_or_changed_envelope_cannot_replace_fixed_external_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "candidate"
            root.mkdir()
            external = Path(folder) / "envelope.json"
            data = json.dumps(self.envelope).encode()
            external.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            admission.load_external_envelope(external, digest, root)
            local = root / "envelope.json"
            local.write_bytes(data)
            with self.assertRaises(admission.AdmissionRefusal) as caught:
                admission.load_external_envelope(local, digest, root)
            self.assertEqual(caught.exception.invalid["field"], "envelope.path")
            external.write_bytes(data + b"\n")
            with self.assertRaises(admission.AdmissionRefusal) as caught:
                admission.load_external_envelope(external, digest, root)
            self.assertEqual(caught.exception.invalid["field"], "envelope.sha256")

    def test_actual_git_rename_and_delete_check_both_endpoints(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
            git("init", "-b", "main")
            (root / "allowed.py").write_text("same contents\n" * 50)
            (root / "資料[1].txt").write_text("delete me\n")
            git("add", ".")
            git("-c", "user.name=Admission Test", "-c", "user.email=test@example.invalid",
                "commit", "-m", "fixture baseline")
            base = git("rev-parse", "HEAD")
            git("mv", "allowed.py", "renamed.py")
            git("rm", "資料[1].txt")
            git("-c", "user.name=Admission Test", "-c", "user.email=test@example.invalid",
                "commit", "-m", "fixture change")
            head = git("rev-parse", "HEAD")
            binding = admission.validate_issue(self.issue, self.envelope)
            binding["base_head"] = base
            result = admission.validate_delivery_paths(root, base, head, binding)
            self.assertEqual(result["changed_paths"], ["allowed.py", "renamed.py", "資料[1].txt"])
            for excluded in result["changed_paths"]:
                with self.subTest(excluded=excluded):
                    restricted = {**binding, "write_paths": [p for p in binding["write_paths"] if p != excluded]}
                    with self.assertRaises(admission.AdmissionRefusal) as caught:
                        admission.validate_delivery_paths(root, base, head, restricted)
                    self.assertEqual(caught.exception.invalid["field"], "candidate.outside_write_paths")
                    self.assertIn(excluded, caught.exception.invalid["value"])

    def test_frozen_observer_replays_treatment_and_preserves_baseline_red(self):
        root = Path(admission.__file__).resolve().parent
        evidence = root / "docs/experiments/pclass-atom-binding"
        observer = evidence / "observer.py"
        expected_sha = (
            "19c01cb1b4de51c20c3d9d0275e40633ae2a801d78d4d20f0e027c24be452ae7")
        self.assertEqual(hashlib.sha256(observer.read_bytes()).hexdigest(),
                         expected_sha)
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(root)
        result = subprocess.run(
            [sys.executable, str(observer), str(Path(admission.__file__)),
             "89", "treatment"],
            cwd=root, env=environment, capture_output=True, text=True,
            timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            json.loads((evidence / "raw/treatment.json").read_text()))
        baseline = json.loads((evidence / "raw/baseline.json").read_text())
        self.assertEqual(baseline["classification"], "RED")
        self.assertEqual(
            [item["outcome"] for item in baseline["records"]],
            ["accepted", "accepted", "accepted"])


if __name__ == "__main__":
    unittest.main()
