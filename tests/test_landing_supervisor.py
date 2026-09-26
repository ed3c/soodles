"""Physical controls for terminal candidate -> landing owner activation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import issue_admission
import landing_supervisor


ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_FILES = (
    "landing.py",
    "provider-execute",
    "provider_transport.py",
    "soodles.py",
    "issue_admission.py",
    "issue_execution.py",
    "repository_binding.py",
    "dependency_binding.py",
    "policy/runtime.lock.json",
)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SupervisorFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.external = self.directory / "external"
        self.external.mkdir()
        self.publisher = self.external / "publisher"
        self.publisher.mkdir()
        for name in PUBLISHER_FILES:
            target = self.publisher / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

        identity = subprocess.run(
            [sys.executable, "-B", str(self.publisher / "soodles.py"),
             "landing", "identity"],
            cwd=self.publisher, capture_output=True, text=True, timeout=30, check=True)
        self.verifier = json.loads(identity.stdout)["verifier_sha256"]
        self.publisher_descriptor = {
            "root": str(self.publisher),
            "verifier_sha256": self.verifier,
        }

        self.repository = "ed3c/soodles"
        self.issue_number = 122
        self.pr_number = 123
        self.head = "a" * 40
        self.tree = "b" * 40
        self.base = "c" * 40
        repo = {"full_name": self.repository}
        self.snapshot = {
            "pr": {
                "number": self.pr_number,
                "html_url": f"https://github.com/{self.repository}/pull/{self.pr_number}",
                "body": f"Refs {self.repository}#{self.issue_number}\n",
                "head": {"repo": repo, "sha": self.head, "ref": "issue-122-fixture"},
                "base": {"repo": repo, "sha": self.base, "ref": "main"},
                "merged": False, "state": "open", "draft": False, "mergeable": True,
            },
            "issue": {
                "number": self.issue_number,
                "html_url": f"https://github.com/{self.repository}/issues/{self.issue_number}",
                "state": "open",
                "body": "plain fixture body",
            },
            "run": {
                "id": 55, "run_attempt": 1, "repository": repo,
                "head_repository": repo, "head_sha": self.head,
                "event": "pull_request", "path": ".github/workflows/runtime.yml",
                "status": "completed", "conclusion": "success",
            },
            "commit": {"sha": self.head, "tree": {"sha": self.tree}},
            "jobs": {
                "total_count": 1,
                "jobs": [{
                    "id": 56, "name": "runtime-evidence", "run_id": 55,
                    "head_sha": self.head, "status": "completed",
                    "conclusion": "success",
                    "steps": [{
                        "name": "Canonical acceptance on the exact candidate head",
                        "status": "completed", "conclusion": "success",
                    }],
                }],
            },
            "branch": {"name": "main", "commit": {"sha": self.base}},
        }

    def close(self):
        self.temp.cleanup()

    def prepare(self, name, snapshot=None, publisher=None, route=None):
        output = self.external / name
        return output, landing_supervisor.prepare(
            self.snapshot if snapshot is None else snapshot,
            self.publisher_descriptor if publisher is None else publisher,
            {"kind": "cloud"} if route is None else route,
            output,
        )

    def local_case(self):
        root = self.directory / "control"
        root.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True,
                       capture_output=True)
        (root / "fixture.txt").write_text("fixture\n")
        subprocess.run(["git", "add", "fixture.txt"], cwd=root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Fixture", "-c",
             "user.email=fixture@example.invalid", "commit", "-m", "fixture"],
            cwd=root, check=True, capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin",
             "https://github.com/ed3c/soodles.git"],
            cwd=root, check=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True).strip()
        tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root,
                                       text=True).strip()

        contract = {
            "schema": 1,
            "trigger": "Terminal local candidate is ready for landing.",
            "source": "physical landing supervisor fixture",
            "owner": "Soodles Issue admission",
            "changes": ["Activate the existing landing owner."],
            "write_paths": ["fixture.txt"],
            "behavior": ["Use one supervisor-selected publisher."],
            "defect_controls": ["Wrong publisher identity refuses."],
            "non_cases": ["Provider mutation is outside this fixture."],
            "dependencies": [],
            "acceptance": "Run the landing supervisor controls.",
            "delivery": "Use the existing landing owner.",
            "reconciliation": "Noodle remains the local cleanup owner.",
            "feature_scope": "Terminal candidate to landing owner activation.",
        }
        body = ("<!-- soodles:execution-v1 -->\n```json\n"
                + json.dumps(contract, indent=2)
                + "\n```\n<!-- /soodles:execution-v1 -->\n")
        updated = "2026-09-21T00:00:00Z"
        worktree = "issue-122-local"
        envelope = {
            "schema": 1,
            "repository": self.repository,
            "issue": self.issue_number,
            "body_sha256": issue_admission.body_digest(body),
            "body_updated_at": updated,
            "owner": contract["owner"],
            "write_paths": contract["write_paths"],
            "base_head": head,
            "execution": {
                "control_root": str(root),
                "worktree": worktree,
                "order_id": f"soodles-{self.issue_number}",
                "stage_index": 0,
                "carrier": {"fixture": True},
                "task": "Landing supervisor local fixture.",
                "source_head": head,
            },
        }
        envelope_path = self.external / "local-envelope.json"
        envelope_path.write_text(json.dumps(envelope, sort_keys=True) + "\n")
        snapshot = json.loads(json.dumps(self.snapshot))
        snapshot["pr"]["head"]["sha"] = head
        snapshot["pr"]["head"]["ref"] = worktree
        snapshot["pr"]["base"]["sha"] = head
        snapshot["issue"]["url"] = (
            f"https://api.github.com/repos/{self.repository}/issues/{self.issue_number}")
        snapshot["issue"]["body"] = body
        snapshot["issue"]["updated_at"] = updated
        snapshot["commit"] = {"sha": head, "tree": {"sha": tree}}
        snapshot["run"]["head_sha"] = head
        snapshot["jobs"]["jobs"][0]["head_sha"] = head
        snapshot["branch"]["commit"]["sha"] = head
        route = {
            "kind": "local",
            "control_root": str(root),
            "execution_envelope": {
                "path": str(envelope_path),
                "sha256": _sha(envelope_path),
            },
        }
        return snapshot, route


class LandingSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.f = SupervisorFixture()
        self.addCleanup(self.f.close)

    def test_cloud_terminal_candidate_activates_current_landing_owner(self):
        output, result = self.f.prepare("cloud")
        self.assertEqual(result["owner"], "landing-supervisor")
        self.assertEqual(result["action"], "activated")
        self.assertEqual(result["route"], "cloud")
        self.assertEqual(result["landing_owner"]["owner"], "landing.start")
        self.assertEqual(result["landing_owner"]["action"], "readback")
        self.assertEqual(result["landing_owner"]["next"]["kind"], "provider_readback")
        self.assertEqual(
            result["landing_owner"]["next"]["known"]["checkpoint"],
            str(output / "checkpoint.json"))
        self.assertEqual(
            result["landing_owner"]["next"]["known"]["readback"],
            str(output / "readback.json"))
        self.assertEqual(
            result["landing_owner"]["next"]["argv"][-2:],
            [str(output / "checkpoint.json"), str(output / "readback.json")])
        claim = json.loads((output / "claim.json").read_text())
        self.assertNotIn("control_root", claim)
        self.assertEqual(claim["head"], self.f.head)
        self.assertEqual(claim["tree"], self.f.tree)
        self.assertEqual(claim["run_id"], 55)
        self.assertTrue((output / "checkpoint.json").is_file())
        self.assertFalse(result["authorizes_landing"])

    def test_local_terminal_candidate_binds_supplied_execution_identity(self):
        snapshot, route = self.f.local_case()
        output, result = self.f.prepare("local", snapshot=snapshot, route=route)
        self.assertEqual(result["route"], "local")
        claim = json.loads((output / "claim.json").read_text())
        self.assertEqual(claim["control_root"], route["control_root"])
        self.assertEqual(
            claim["execution_envelope"]["sha256"],
            route["execution_envelope"]["sha256"])
        self.assertEqual(result["landing_owner"]["owner"], "landing.start")
        self.assertEqual(result["landing_owner"]["next"]["kind"], "provider_readback")
        self.assertEqual(result["landing_owner"]["next"]["argv"][-2:],
                         [str(output / "checkpoint.json"), str(output / "readback.json")])

    def test_inconsistent_owner_continuation_refuses(self):
        temporary = self.f.external / ".temporary"
        output = self.f.external / "final"
        next_action = {
            "kind": "provider_readback",
            "known": {
                "checkpoint": str(temporary / "checkpoint.json"),
                "readback": str(temporary / "readback.json"),
            },
            "argv": ["python", "landing", "advance", "wrong-checkpoint",
                     str(temporary / "readback.json")],
        }
        with self.assertRaises(landing_supervisor.SupervisorRefusal) as caught:
            landing_supervisor._rebase_next(next_action, temporary, output)
        self.assertEqual(caught.exception.invalid["field"],
                         "landing.start.next.argv")
        self.assertEqual(next_action["argv"][-2], "wrong-checkpoint")

    def test_stale_green_wrong_publisher_and_existing_output_refuse_before_checkpoint(self):
        stale = json.loads(json.dumps(self.f.snapshot))
        stale["run"]["head_sha"] = "f" * 40
        with self.assertRaises(landing_supervisor.SupervisorRefusal) as caught:
            self.f.prepare("stale", snapshot=stale)
        self.assertEqual(caught.exception.invalid["field"], "snapshot.run.head_sha")
        self.assertFalse((self.f.external / "stale").exists())

        bad = dict(self.f.publisher_descriptor)
        bad["verifier_sha256"] = "f" * 64
        with self.assertRaises(landing_supervisor.SupervisorRefusal) as caught:
            self.f.prepare("wrong-publisher", publisher=bad)
        self.assertEqual(caught.exception.invalid["field"], "publisher.identity")
        self.assertFalse((self.f.external / "wrong-publisher").exists())

        output, _ = self.f.prepare("once")
        before = sorted(str(path.relative_to(output)) for path in output.rglob("*"))
        with self.assertRaises(landing_supervisor.SupervisorRefusal) as caught:
            self.f.prepare("once")
        self.assertEqual(caught.exception.invalid["field"], "output.exists")
        after = sorted(str(path.relative_to(output)) for path in output.rglob("*"))
        self.assertEqual(before, after)

    def test_candidate_cannot_select_itself_as_publisher(self):
        publisher = {
            "root": str(ROOT),
            "verifier_sha256": subprocess.check_output(
                [sys.executable, "-B", str(ROOT / "soodles.py"),
                 "landing", "identity"], cwd=ROOT, text=True),
        }
        publisher["verifier_sha256"] = json.loads(
            publisher["verifier_sha256"])["verifier_sha256"]
        with self.assertRaises(landing_supervisor.SupervisorRefusal) as caught:
            self.f.prepare("self", publisher=publisher)
        self.assertEqual(caught.exception.invalid["field"], "publisher.root")
        self.assertFalse((self.f.external / "self").exists())

    def test_pclass_terminal_entry_points_only_to_landing_supervisor(self):
        text = (ROOT / "AGENTS.md").read_text()
        marker = "Terminal candidate delivery entry"
        self.assertIn(marker, text)
        section = text.split(marker, 1)[1].split("\n## ", 1)[0]
        self.assertIn("landing-supervisor", section)
        for forbidden in (
            "git log",
            "landing start --help",
            "construct claim",
            "choose checkpoint",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, section)


if __name__ == "__main__":
    unittest.main()
