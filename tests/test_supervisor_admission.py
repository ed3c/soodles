"""Physical controls for the trusted local supervisor admission seam."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest

from issue_admission import AdmissionRefusal
from issue_execution import inspect_schedule
import supervisor_admission


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATHS = supervisor_admission.BUNDLE_PATHS


def _sha(data):
    return hashlib.sha256(data).hexdigest()


class SupervisorFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name).resolve()
        self.root = self.directory / "control"
        self.root.mkdir()
        self.external = self.directory / "external"
        self.external.mkdir()
        self._git("init", "-b", "main")
        (self.root / ".gitignore").write_text(".noodle/\n.worktrees/\n")
        (self.root / "allowed.py").write_text("print('fixture')\n")
        for path in BUNDLE_PATHS:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if path == "github_reader.py":
                target.write_text(
                    "import json, os\n"
                    "from pathlib import Path\n"
                    "def fetch_issue(repository, number):\n"
                    "    value=json.loads(Path(os.environ['FIXTURE_ISSUE_READBACK']).read_text())\n"
                    "    if value.get('number') != number:\n"
                    "        raise RuntimeError('fixture issue mismatch')\n"
                    "    return value\n"
                )
            else:
                target.write_bytes((ROOT / path).read_bytes())
        self._git("add", ".")
        self._git("-c", "user.name=Supervisor Test",
                  "-c", "user.email=test@example.invalid",
                  "commit", "-m", "supervisor fixture")
        self._git("remote", "add", "origin", "https://github.com/ed3c/soodles.git")
        self.head = self._git("rev-parse", "HEAD")

        self.binary = self.external / "carrier-sentinel"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary), "sha256": _sha(self.binary.read_bytes())}
        self.carrier = {
            "platform": platform.system().lower() + "_" + platform.machine().lower(),
            "noodle": dict(identity),
            "codex": {**identity, "model": "fixture-model", "argv": ["exec"]},
        }

        self.contract = {
            "schema": 3,
            "trigger": "A local supervisor capability is absent.",
            "source": "physical local fixture",
            "owner": "Soodles Issue admission",
            "changes": ["Materialize one external admission bundle."],
            "write_paths": ["allowed.py", "evidence.json"],
            "behavior": ["Use only the externally selected bundle."],
            "defect_controls": ["Missing launcher is a refusal."],
            "non_cases": ["No provider writes."],
            "dependencies": [],
            "acceptance": "Run the physical supervisor controls.",
            "delivery": "Use the existing landing owner.",
            "reconciliation": "Read back the exact owner.",
            "feature_scope": "One local supervisor admission seam.",
            "required_paths": ["evidence.json"],
            "evidence_manifest": "evidence.json",
            "base_head": self.head,
            "frozen_paths": [{
                "path": "evidence.json", "revision": "head", "sha256": "0" * 64
            }],
        }
        body = (
            "<!-- soodles:execution-v1 -->\n```json\n"
            + json.dumps(self.contract, indent=2)
            + "\n```\n<!-- /soodles:execution-v1 -->\n"
        )
        self.issue = {
            "url": "https://api.github.com/repos/ed3c/soodles/issues/118",
            "html_url": "https://github.com/ed3c/soodles/issues/118",
            "number": 118,
            "body": body,
            "updated_at": "2026-09-21T03:06:47Z",
            "state": "open",
        }
        self.issue_path = self.external / "issue.json"
        self.issue_path.write_text(json.dumps(self.issue))

        runtime = self.root / ".noodle"
        runtime.mkdir()
        (runtime / "state.snapshot.json").write_text(json.dumps({
            "order_revision": "a" * 32,
            "state": {"orders": {}},
            "effect_ledger": [],
        }))
        self.session = "schedule-supervisor-fixture"
        spawn = runtime / "sessions" / self.session
        spawn.mkdir(parents=True)
        (spawn / "spawn.json").write_text(json.dumps({
            "session_id": self.session,
            "skill": "schedule",
            "worktree_path": str(self.root),
        }))
        self.schedule_env = {
            "NOODLE_SESSION_ID": self.session,
            "NOODLE_WORKTREE": str(self.root),
        }

        with (self.root / "soodles.py").open("a") as stream:
            stream.write("\n# DIRTY_WORKTREE_SENTINEL\n")
        self.status_before = self._git("status", "--porcelain=v1", "--untracked-files=all")

    def close(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.root, text=True, stderr=subprocess.PIPE
        ).strip()

    def prepare(self, name="bundle"):
        output = self.external / name
        result = supervisor_admission.prepare(
            self.issue, self.carrier, self.root, output)
        return output, result

    def baseline(self):
        try:
            inspect_schedule(self.root, dict(self.schedule_env))
        except AdmissionRefusal as error:
            return {
                "classification": "OBSERVED_CAPABILITY_GAP",
                "field": error.invalid["field"],
                "owner": error.next["owner"],
                "required": error.next["required"],
                "proposal_exists": (self.root / ".noodle/orders-next.json").exists(),
            }
        raise AssertionError("baseline unexpectedly found a launcher")

    def treatment(self):
        output, prepared = self.prepare()
        status_after_prepare = self._git(
            "status", "--porcelain=v1", "--untracked-files=all")
        committed_soodles = subprocess.check_output(
            ["git", "show", self.head + ":soodles.py"], cwd=self.root)
        bundle_soodles = (output / "runtime/soodles.py").read_bytes()

        env = {**self.schedule_env,
               "SOODLES_ADMISSION_LAUNCHER": prepared["launcher"]}
        projected = inspect_schedule(self.root, env)
        process_env = os.environ.copy()
        process_env["FIXTURE_ISSUE_READBACK"] = str(self.issue_path)
        run = subprocess.run(
            projected["next"]["argv"], cwd=self.root, env=process_env,
            capture_output=True, text=True, timeout=30)
        payload = json.loads(run.stdout)
        return {
            "prepared_action": prepared["action"],
            "start_operation": prepared["next"]["operation"],
            "start_argv": prepared["next"]["argv"],
            "inspect_action": projected["action"],
            "inspect_argv": projected["next"]["argv"],
            "launcher_exit": run.returncode,
            "launcher_action": payload.get("action"),
            "proposal_exists": (self.root / ".noodle/orders-next.json").exists(),
            "status_unchanged_by_prepare": status_after_prepare == self.status_before,
            "bundle_uses_committed_soodles": bundle_soodles == committed_soodles,
            "dirty_sentinel_excluded": b"DIRTY_WORKTREE_SENTINEL" not in bundle_soodles,
            "authorizes_landing": prepared["authorizes_landing"],
        }


def observe_baseline_and_treatment():
    fixture = SupervisorFixture()
    try:
        return {"baseline": fixture.baseline(), "treatment": fixture.treatment()}
    finally:
        fixture.close()


def observe_sensitivity():
    results = {}

    fixture = SupervisorFixture()
    try:
        historical = fixture.external / "historical-launcher"
        historical.write_text("#!/bin/sh\nexit 99\n")
        historical.chmod(0o755)
        baseline = fixture.baseline()
        results["historical_unselected_launcher"] = {
            "field": baseline["field"],
            "owner": baseline["owner"],
            "historical_executed": False,
        }
    finally:
        fixture.close()

    fixture = SupervisorFixture()
    try:
        output, _ = fixture.prepare("envelope-tamper")
        (output / "envelope.json").write_bytes(
            (output / "envelope.json").read_bytes() + b" ")
        env = os.environ.copy()
        env["FIXTURE_ISSUE_READBACK"] = str(fixture.issue_path)
        run = subprocess.run(
            [str(output / "launcher"), "automatic"],
            cwd=fixture.root, env=env, capture_output=True, text=True, timeout=30)
        payload = json.loads(run.stdout)
        results["envelope_tamper"] = {
            "exit": run.returncode,
            "field": payload["invalid"]["field"],
            "proposal_exists": (fixture.root / ".noodle/orders-next.json").exists(),
        }
    finally:
        fixture.close()

    fixture = SupervisorFixture()
    try:
        output, _ = fixture.prepare("runtime-tamper")
        with (output / "runtime/issue_execution.py").open("a") as stream:
            stream.write("\n# tampered\n")
        env = os.environ.copy()
        env["FIXTURE_ISSUE_READBACK"] = str(fixture.issue_path)
        run = subprocess.run(
            [str(output / "launcher"), "automatic"],
            cwd=fixture.root, env=env, capture_output=True, text=True, timeout=30)
        payload = json.loads(run.stdout)
        results["runtime_tamper"] = {
            "exit": run.returncode,
            "field": payload["invalid"]["field"],
            "proposal_exists": (fixture.root / ".noodle/orders-next.json").exists(),
        }
        try:
            supervisor_admission.prepare(
                fixture.issue, fixture.carrier, fixture.root, output)
        except AdmissionRefusal as error:
            results["existing_output"] = {
                "field": error.invalid["field"],
                "owner": error.next["owner"],
            }
        else:
            raise AssertionError("existing output was overwritten")
    finally:
        fixture.close()

    return results


class SupervisorAdmissionTests(unittest.TestCase):
    def test_baseline_to_exact_launcher_automatic_closes_capability_gap(self):
        observed = observe_baseline_and_treatment()
        baseline = observed["baseline"]
        treatment = observed["treatment"]
        self.assertEqual(baseline["field"], "scheduler.launcher")
        self.assertEqual(baseline["owner"], "supervisor")
        self.assertEqual(baseline["required"], ["SOODLES_ADMISSION_LAUNCHER"])
        self.assertFalse(baseline["proposal_exists"])

        self.assertEqual(treatment["prepared_action"], "ready")
        self.assertEqual(treatment["start_operation"], "start_noodle")
        self.assertEqual(treatment["inspect_action"], "ready")
        self.assertEqual(treatment["inspect_argv"][1], "automatic")
        self.assertEqual(treatment["launcher_exit"], 0)
        self.assertEqual(treatment["launcher_action"], "proposal_pending")
        self.assertTrue(treatment["proposal_exists"])
        self.assertTrue(treatment["status_unchanged_by_prepare"])
        self.assertTrue(treatment["bundle_uses_committed_soodles"])
        self.assertTrue(treatment["dirty_sentinel_excluded"])
        self.assertFalse(treatment["authorizes_landing"])

    def test_tamper_historical_and_overwrite_controls_refuse_before_proposal(self):
        observed = observe_sensitivity()
        self.assertEqual(
            observed["historical_unselected_launcher"]["field"],
            "scheduler.launcher")
        self.assertFalse(
            observed["historical_unselected_launcher"]["historical_executed"])
        self.assertEqual(
            observed["envelope_tamper"]["field"],
            "launcher.envelope_sha256")
        self.assertEqual(observed["envelope_tamper"]["exit"], 64)
        self.assertFalse(observed["envelope_tamper"]["proposal_exists"])
        self.assertEqual(
            observed["runtime_tamper"]["field"],
            "launcher.runtime_sha256")
        self.assertEqual(observed["runtime_tamper"]["exit"], 64)
        self.assertFalse(observed["runtime_tamper"]["proposal_exists"])
        self.assertEqual(
            observed["existing_output"]["field"],
            "supervisor.output.exists")

    def test_wrong_origin_and_carrier_digest_refuse_before_output(self):
        fixture = SupervisorFixture()
        try:
            fixture._git("remote", "set-url", "origin", "https://example.invalid/foreign.git")
            with self.assertRaises(AdmissionRefusal) as caught:
                fixture.prepare("foreign")
            self.assertEqual(
                caught.exception.invalid["field"],
                "supervisor.control_root.origin")
            self.assertFalse((fixture.external / "foreign").exists())
        finally:
            fixture.close()

        fixture = SupervisorFixture()
        try:
            fixture.carrier["noodle"]["sha256"] = "f" * 64
            with self.assertRaises(AdmissionRefusal) as caught:
                fixture.prepare("bad-carrier")
            self.assertEqual(
                caught.exception.invalid["field"],
                "carrier.noodle.sha256")
            self.assertFalse((fixture.external / "bad-carrier").exists())
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
