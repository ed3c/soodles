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
TOKEN_COMMAND_ENV = supervisor_admission.TOKEN_COMMAND_ENV


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
        for path in BUNDLE_PATHS + (".agents/skills/execute/SKILL.md", ".agents/skills/schedule/SKILL.md"):
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

        self.child_env = self.external / "child-env.json"
        self.child_marker = self.external / "child-started"
        self.binary = self.external / "carrier-sentinel"
        self.binary.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os\n"
            "from pathlib import Path\n"
            "target=os.environ.get('FIXTURE_CHILD_ENV_READBACK')\n"
            "if target:\n"
            "    Path(target).write_text(json.dumps({k:os.environ.get(k) for k in "
            "['GH_TOKEN','GITHUB_TOKEN','SOODLES_ADMISSION_LAUNCHER','NOODLES_TOKEN_COMMAND']}))\n"
            "marker=os.environ.get('FIXTURE_CHILD_STARTED')\n"
            "if marker:\n"
            "    Path(marker).write_text('started')\n"
        )
        self.binary.chmod(0o755)
        identity = {"path": str(self.binary), "sha256": _sha(self.binary.read_bytes())}
        self.carrier = {
            "platform": platform.system().lower() + "_" + platform.machine().lower(),
            "noodle": dict(identity),
            "codex": {**identity, "model": "fixture-model", "argv": ["exec"]},
        }
        self.token = "fixture-installation-token"
        self.token_command = "printf fixture-installation-token"

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

    def prepare(self, name="bundle", environ=None, **kwargs):
        output = self.external / name
        if environ is None:
            environ = {TOKEN_COMMAND_ENV: self.token_command}
        result = supervisor_admission.prepare(
            self.issue, self.carrier, self.root, output, environ=environ, **kwargs)
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

        start_env = os.environ.copy()
        start_env.update({
            TOKEN_COMMAND_ENV: self.token_command,
            "GH_TOKEN": "stale-parent-token",
            "GITHUB_TOKEN": "stale-parent-token",
            "FIXTURE_CHILD_ENV_READBACK": str(self.child_env),
            "FIXTURE_CHILD_STARTED": str(self.child_marker),
        })
        start_run = subprocess.run(
            prepared["next"]["argv"], cwd=self.root, env=start_env,
            capture_output=True, text=True, timeout=30)
        child = json.loads(self.child_env.read_text())

        env = {**self.schedule_env,
               "SOODLES_ADMISSION_LAUNCHER": prepared["launcher"]}
        projected = inspect_schedule(self.root, env)
        process_env = os.environ.copy()
        process_env["FIXTURE_ISSUE_READBACK"] = str(self.issue_path)
        run = subprocess.run(
            projected["next"]["argv"], cwd=self.root, env=process_env,
            capture_output=True, text=True, timeout=30)
        payload = json.loads(run.stdout)

        bundle_bytes = b"".join(
            path.read_bytes() for path in output.rglob("*") if path.is_file())
        return {
            "prepared_action": prepared["action"],
            "start_operation": prepared["next"]["operation"],
            "start_argv": prepared["next"]["argv"],
            "start_exit": start_run.returncode,
            "child_started": self.child_marker.exists(),
            "child_gh_token": child["GH_TOKEN"],
            "child_github_token": child["GITHUB_TOKEN"],
            "child_launcher": child["SOODLES_ADMISSION_LAUNCHER"],
            "child_supplier": child["NOODLES_TOKEN_COMMAND"],
            "token_absent_from_argv": self.token not in "\n".join(prepared["next"]["argv"]),
            "token_absent_from_bundle": self.token.encode() not in bundle_bytes,
            "supplier_command_absent_from_bundle": self.token_command.encode() not in bundle_bytes,
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
        output = fixture.external / "missing-supplier"
        try:
            supervisor_admission.prepare(
                fixture.issue, fixture.carrier, fixture.root, output, environ={})
        except AdmissionRefusal as error:
            results["missing_supplier"] = {
                "field": error.invalid["field"],
                "owner": error.next["owner"],
                "required": error.next["required"],
                "output_exists": output.exists(),
            }
        else:
            raise AssertionError("missing supplier unexpectedly prepared output")
    finally:
        fixture.close()

    fixture = SupervisorFixture()
    try:
        output, prepared = fixture.prepare("supplier-failure")
        env = os.environ.copy()
        env.update({
            TOKEN_COMMAND_ENV: "exit 23",
            "FIXTURE_CHILD_ENV_READBACK": str(fixture.child_env),
            "FIXTURE_CHILD_STARTED": str(fixture.child_marker),
        })
        run = subprocess.run(
            prepared["next"]["argv"], cwd=fixture.root, env=env,
            capture_output=True, text=True, timeout=30)
        payload = json.loads(run.stdout)
        results["failing_supplier"] = {
            "exit": run.returncode,
            "field": payload["invalid"]["field"],
            "child_started": fixture.child_marker.exists(),
            "proposal_exists": (fixture.root / ".noodle/orders-next.json").exists(),
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
                fixture.issue, fixture.carrier, fixture.root, output,
                environ={TOKEN_COMMAND_ENV: fixture.token_command})
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
    def test_host_bundle_binds_task_worker_and_single_issue_backlog(self):
        import tomllib
        fixture = SupervisorFixture()
        self.addCleanup(fixture.close)
        fixture.carrier["codex"]["argv"] = ["exec", "--skip-git-repo-check", "--json",
                                              "--model", "fixture-model", "-c", "approval_policy=never"]
        output, prepared = fixture.prepare(task="One exact supplied task.", wire_host=True)
        binding = json.loads((output / "envelope.json").read_text())
        self.assertEqual(binding["execution"]["task"], "One exact supplied task.")
        config = tomllib.loads((output / "noodle.toml").read_text())
        self.assertEqual(config["mode"], "supervised")
        self.assertEqual(config["agents"]["codex"]["path"], str(output / "provider"))
        self.assertEqual(config["agents"]["codex"]["args"], ["-c", "approval_policy=never"])
        bootstrap = tomllib.loads((output / "bootstrap-noodle.toml").read_text())
        self.assertNotIn("adapters", bootstrap)
        self.assertIn("backlog", config["adapters"])
        self.assertEqual(prepared["bootstrap"]["config"], str(output / "bootstrap-noodle.toml"))
        self.assertEqual(prepared["bootstrap"]["config_sha256"],
                         _sha((output / "bootstrap-noodle.toml").read_bytes()))
        self.assertFalse((fixture.root / ".noodle.toml").exists())
        env = {**os.environ, "FIXTURE_ISSUE_READBACK": str(fixture.issue_path)}
        sync = subprocess.run([str(output / "backlog"), "sync"], env=env,
                              capture_output=True, text=True)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        self.assertEqual(json.loads(sync.stdout)["id"], "soodles-118")
        self.assertEqual(json.loads(sync.stdout)["plan"], "One exact supplied task.")
        for argv in (["add", "foreign"], ["done", "soodles-119"], ["done", "soodles-118"]):
            result = subprocess.run([str(output / "backlog"), *argv], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        # Generated worker reaches the existing identity guard, not the sentinel.
        worker = subprocess.run([str(output / "provider/codex"), *fixture.carrier["codex"]["argv"]],
                                cwd=fixture.root, env=env, capture_output=True, text=True)
        self.assertNotEqual(worker.returncode, 0)
        self.assertEqual(json.loads(worker.stdout)["invalid"]["field"], "worker.session_id")
        self.assertFalse(fixture.child_marker.exists())
        (output / "runtime/issue_execution.py").write_text("raise RuntimeError('must not import')")
        changed = subprocess.run([str(output / "backlog"), "sync"], env=env, capture_output=True, text=True)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("changed admission bytes", changed.stderr)

    def test_unknown_worker_argv_refuses_before_host_bundle_creation(self):
        fixture = SupervisorFixture()
        self.addCleanup(fixture.close)
        with self.assertRaisesRegex(AdmissionRefusal, "supervisor.worker.argv"):
            fixture.prepare(wire_host=True)
        self.assertFalse((fixture.external / "bundle").exists())

    def test_bootstrap_injects_provider_identity_then_uses_exact_launcher(self):
        observed = observe_baseline_and_treatment()
        baseline = observed["baseline"]
        treatment = observed["treatment"]
        self.assertEqual(baseline["field"], "scheduler.launcher")
        self.assertEqual(baseline["owner"], "supervisor")
        self.assertEqual(baseline["required"], ["SOODLES_ADMISSION_LAUNCHER"])
        self.assertFalse(baseline["proposal_exists"])

        self.assertEqual(treatment["prepared_action"], "ready")
        self.assertEqual(treatment["start_operation"], "start_noodle")
        self.assertEqual(len(treatment["start_argv"]), 1)
        self.assertEqual(treatment["start_exit"], 0)
        self.assertTrue(treatment["child_started"])
        self.assertEqual(treatment["child_gh_token"], "fixture-installation-token")
        self.assertEqual(treatment["child_github_token"], "fixture-installation-token")
        self.assertEqual(treatment["child_launcher"], treatment["inspect_argv"][0])
        self.assertIsNone(treatment["child_supplier"])
        self.assertTrue(treatment["token_absent_from_argv"])
        self.assertTrue(treatment["token_absent_from_bundle"])
        self.assertTrue(treatment["supplier_command_absent_from_bundle"])

        self.assertEqual(treatment["inspect_action"], "ready")
        self.assertEqual(treatment["inspect_argv"][1], "automatic")
        self.assertEqual(treatment["launcher_exit"], 0)
        self.assertEqual(treatment["launcher_action"], "proposal_pending")
        self.assertTrue(treatment["proposal_exists"])
        self.assertTrue(treatment["status_unchanged_by_prepare"])
        self.assertTrue(treatment["bundle_uses_committed_soodles"])
        self.assertTrue(treatment["dirty_sentinel_excluded"])
        self.assertFalse(treatment["authorizes_landing"])

    def test_pinned_once_entry_accepts_only_exact_bootstrap_argv(self):
        fixture = SupervisorFixture()
        self.addCleanup(fixture.close)
        output, prepared = fixture.prepare("once-entry")
        self.assertEqual(prepared["bootstrap"]["argv"], [prepared["start"], "--once"])
        env = {**os.environ, TOKEN_COMMAND_ENV: fixture.token_command,
               "FIXTURE_CHILD_STARTED": str(fixture.child_marker)}
        accepted = subprocess.run(prepared["bootstrap"]["argv"], cwd=fixture.root,
                                  env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertTrue(fixture.child_marker.exists())
        fixture.child_marker.unlink()
        rejected = subprocess.run([str(output / "start-noodle"), "--once", "--repeat"],
                                  cwd=fixture.root, env=env,
                                  capture_output=True, text=True, timeout=30)
        self.assertEqual(rejected.returncode, 64)
        self.assertFalse(fixture.child_marker.exists())

    def test_host_once_refuses_full_backlog_config_before_noodle_effect(self):
        fixture = SupervisorFixture()
        self.addCleanup(fixture.close)
        fixture.carrier["codex"]["argv"] = ["exec", "--skip-git-repo-check", "--json",
                                            "--model", "fixture-model"]
        output, prepared = fixture.prepare("host-once", wire_host=True)
        env = {**os.environ, TOKEN_COMMAND_ENV: fixture.token_command,
               "FIXTURE_CHILD_STARTED": str(fixture.child_marker)}
        (fixture.root / ".noodle.toml").write_bytes((output / "noodle.toml").read_bytes())
        refused = subprocess.run(prepared["bootstrap"]["argv"], cwd=fixture.root,
                                 env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(refused.returncode, 64)
        self.assertEqual(json.loads(refused.stdout)["invalid"]["field"], "start.host_config")
        self.assertFalse(fixture.child_marker.exists())
        (fixture.root / ".noodle.toml").write_bytes((output / "bootstrap-noodle.toml").read_bytes())
        accepted = subprocess.run(prepared["bootstrap"]["argv"], cwd=fixture.root,
                                  env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertTrue(fixture.child_marker.exists())

    def test_supplier_integrity_and_overwrite_controls_refuse_before_effects(self):
        observed = observe_sensitivity()
        self.assertEqual(
            observed["historical_unselected_launcher"]["field"],
            "scheduler.launcher")
        self.assertFalse(
            observed["historical_unselected_launcher"]["historical_executed"])

        self.assertEqual(
            observed["missing_supplier"]["field"],
            "supervisor.provider_credential_supplier")
        self.assertEqual(observed["missing_supplier"]["owner"], "supervisor")
        self.assertEqual(
            observed["missing_supplier"]["required"], [TOKEN_COMMAND_ENV])
        self.assertFalse(observed["missing_supplier"]["output_exists"])

        self.assertEqual(
            observed["failing_supplier"]["field"],
            "start.provider_credential_supplier_exit")
        self.assertEqual(observed["failing_supplier"]["exit"], 64)
        self.assertFalse(observed["failing_supplier"]["child_started"])
        self.assertFalse(observed["failing_supplier"]["proposal_exists"])

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
