"""External oracle controls. Mutations are not fresh model executions."""
import copy
import json
from pathlib import Path
import shlex
import shutil
import tempfile
import unittest
from unittest.mock import patch

import oracle


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "host/smoke-r03"
CAPTURE_FILES = {"binding": "binding.json", "launch": "raw/launch.json", "exit": "raw/exit.json",
                 "stdout": "raw/stdout.bin", "stderr": "raw/stderr.bin", "task_boundary": "raw/task-boundary.json",
                 "isolation": "raw/isolation-probe.json", "profile": "raw/consumer.sb"}


def real_smoke():
    return {name: (SMOKE / path).read_bytes() for name, path in CAPTURE_FILES.items()}


def mutate_json(blobs, name, change):
    value = json.loads(blobs[name])
    change(value)
    blobs[name] = json.dumps(value).encode()


def replace_events(blobs, events):
    blobs["stdout"] = b"".join(json.dumps(x).encode() + b"\n" for x in events)
    def update(value):
        value["stdout_sha256"] = oracle.sha(blobs["stdout"])
        value["emitted_usage"] = [{"line": n, "usage": x.get("usage")} for n, x in enumerate(events, 1) if x["type"] == "turn.completed"]
    mutate_json(blobs, "exit", update)


class CaptureControls(unittest.TestCase):
    def test_real_smoke_completed_count_not_started_count(self):
        capture = oracle.decode_capture(real_smoke())
        self.assertEqual(oracle.costs(capture)["completed_commands"], 4)
        self.assertIsNone(oracle.costs(capture)["split"])
        self.assertEqual(capture["incomplete_commands"], 0)
        self.assertEqual(capture["usage"][0]["usage"]["input_tokens"], 80478)

    def test_real_failed_completed_events_are_counted(self):
        # Actual r02 observations, not a fabricated positive capture seal.
        stdout = (ROOT / "host/smoke-r02/raw/stdout.bin").read_bytes()
        decoded = oracle.decode_events(stdout)
        failed = [x for x in decoded["commands"] if x["item"]["status"] == "failed"]
        self.assertEqual(len(decoded["commands"]), 10)
        self.assertEqual(len(failed), 4)
        self.assertEqual([x["item"]["exit_code"] for x in failed], [127, 1, 1, 1])

    def test_terminal_without_eof_is_inconclusive(self):
        blobs = real_smoke()
        mutate_json(blobs, "exit", lambda x: x["streams_eof"].update({"stdout.bin": False}))
        with self.assertRaises(oracle.EvidenceError) as caught:
            oracle.decode_capture(blobs)
        self.assertEqual(caught.exception.validity, "INCONCLUSIVE")

    def test_missing_raw_is_not_zero(self):
        blobs = real_smoke()
        blobs["stdout"] = None
        with self.assertRaises(oracle.EvidenceError) as caught:
            oracle.decode_capture(blobs)
        self.assertEqual(caught.exception.validity, "INCONCLUSIVE")

    def test_started_and_exact_duplicate_completed_do_not_add(self):
        blobs = real_smoke()
        events = [json.loads(x) for x in blobs["stdout"].splitlines()]
        event = next(x for x in events if x["type"] == "item.completed" and x["item"]["type"] == "command_execution")
        events.insert(-1, copy.deepcopy(event))
        replace_events(blobs, events)
        self.assertEqual(len(oracle.decode_capture(blobs)["commands"]), 4)

    def test_conflicting_same_item_is_invalid(self):
        blobs = real_smoke()
        events = [json.loads(x) for x in blobs["stdout"].splitlines()]
        event = copy.deepcopy(next(x for x in events if x["type"] == "item.completed" and x["item"]["type"] == "command_execution"))
        event["item"]["exit_code"] = 19
        events.insert(-1, event)
        replace_events(blobs, events)
        with self.assertRaisesRegex(oracle.EvidenceError, "conflicting_completed_item"):
            oracle.decode_capture(blobs)

    def test_same_command_new_item_is_a_real_second_observation(self):
        blobs = real_smoke()
        events = [json.loads(x) for x in blobs["stdout"].splitlines()]
        event = copy.deepcopy(next(x for x in events if x["type"] == "item.completed" and x["item"]["type"] == "command_execution"))
        event["item"]["id"] = "control-distinct-retry"
        events.insert(-1, event)
        replace_events(blobs, events)
        self.assertEqual(len(oracle.decode_capture(blobs)["commands"]), 5)

    def test_sealed_no_action_is_still_valid_capture(self):
        blobs = real_smoke()
        events = [json.loads(x) for x in blobs["stdout"].splitlines()]
        events = [x for x in events if x.get("item", {}).get("type") != "command_execution"]
        replace_events(blobs, events)
        capture = oracle.decode_capture(blobs)
        self.assertEqual(capture["commands"], [])
        self.assertEqual(oracle.judge_behavior({"work_id": "soodles-work-2", "entries": {"issue_atom": "/case/issue-atom"}, "authorization": {"path": "/case/missing"}, "host": {"python": "/python"}}, [])["classification"], "FAIL")

    def test_enoent_is_not_isolation(self):
        blobs = real_smoke()
        def replace_probe(value):
            result = json.loads(value["stdout"])
            result["denied"][0]["result"] = "FileNotFoundError"
            value["stdout"] = json.dumps(result)
        mutate_json(blobs, "isolation", replace_probe)
        with self.assertRaisesRegex(oracle.EvidenceError, "isolation_not_permission_denied"):
            oracle.decode_capture(blobs)

    def test_direct_shell_only_no_substring_proof(self):
        self.assertEqual(oracle.direct_argv("/bin/zsh -lc '/python -B /drive /case control -- /python -B /cli run /auth'"),
                         ["/python", "-B", "/drive", "/case", "control", "--", "/python", "-B", "/cli", "run", "/auth"])
        self.assertIsNone(oracle.direct_argv("/bin/zsh -lc 'echo ok; /cli run /auth'"))
        self.assertIsNone(oracle.direct_argv("/python - <<'PY'\nprint('fake /cli run /auth')\nPY"))

    def test_missing_usage_stays_unknown_and_does_not_invalidate_behavior(self):
        blobs = real_smoke()
        events = [json.loads(x) for x in blobs["stdout"].splitlines()]
        for event in events:
            if event["type"] == "turn.completed":
                event["usage"] = None
        replace_events(blobs, events)
        capture = oracle.decode_capture(blobs)
        self.assertIsNone(oracle.costs(capture)["whole_turn_usage"][0]["usage"])


CONTROL_ROOT = ROOT / "host/prepared-controls"
CONTROL_FILES = {"A": "A-drive.json", "B": "B-drive-shell.json", "C": "C-drive.json"}


def actual_cli_control(name):
    """Actual sandbox CLI, explicitly no model session and no invented capture."""
    facts = json.loads((CONTROL_ROOT / "output" / name / "workspace.json").read_bytes())
    outer = json.loads((CONTROL_ROOT / "raw" / CONTROL_FILES[name]).read_bytes())
    if outer.get("model_launched") is not False and name == "A":
        raise AssertionError("control provenance changed")
    record = json.loads(outer["stdout"])
    if record["result"]["exit_code"] != outer["exit"]:
        raise AssertionError("actual control exit mismatch")
    return facts, [{"record": record}]


class BehaviorControls(unittest.TestCase):
    def test_true_cli_three_strata_positive(self):
        for name in CONTROL_FILES:
            with self.subTest(stratum=name):
                facts, drives = actual_cli_control(name)
                result = oracle.judge_behavior(facts, drives)
                self.assertEqual(result["classification"], "PASS", result)

    def test_handoff_cannot_replace_exact_next(self):
        facts, drives = actual_cli_control("B")
        path = facts["task"]["handoff"]
        changed = json.loads(Path(path).read_bytes())
        changed["next"]["argv"][-1] = "/wrong/authorization.json"
        original = oracle.artifact
        with patch.object(oracle, "artifact", side_effect=lambda p: json.dumps(changed).encode() if str(p) == path else original(p)):
            result = oracle.judge_behavior(facts, drives)
        self.assertEqual(result["barriers"], ["exact_handoff_projection"])

    def test_a_same_python_without_bytecode_flag_is_equivalent(self):
        # Syntax mutation of a true CLI record, not a new real execution.
        facts, drives = actual_cli_control("A")
        drives[0]["record"]["argv"].remove("-B")
        self.assertEqual(oracle.judge_behavior(facts, drives)["classification"], "PASS")

    def test_prepare_help_is_not_a_transition_but_second_owner_run_is(self):
        facts, drives = actual_cli_control("A")
        help_record = {"record": {"argv": [facts["host"]["python"], facts["entries"]["supervisor_admission"], "prepare", "--help"]}}
        self.assertEqual(oracle.judge_behavior(facts, drives + [help_record])["classification"], "PASS")
        receipt = json.loads(drives[0]["record"]["stdout"])
        second = {"record": {"argv": receipt["next"]["argv"]}}
        self.assertEqual(oracle.judge_behavior(facts, drives + [help_record, second])["barriers"], ["no_other_owner_transition"])

    def test_model_report_without_actual_cli_does_not_pass(self):
        facts, _ = actual_cli_control("A")
        result = oracle.judge_behavior(facts, [])
        self.assertEqual(result["classification"], "FAIL")
        self.assertIn("one_exact_owner_invocation", result["barriers"])

    def test_prepared_authorization_byte_tamper(self):
        facts, drives = actual_cli_control("A")
        path = str(Path(facts["selection"]["external_output"]) / "authorization.json")
        original = oracle.artifact
        with patch.object(oracle, "artifact", side_effect=lambda p: original(p) + b" " if str(p) == path else original(p)):
            result = oracle.judge_behavior(facts, drives)
        self.assertEqual(result["classification"], "FAIL")
        self.assertIn("saved_authorization_binding", result["barriers"])

    def test_b_reauthorization_attempt_is_not_recovery(self):
        facts, drives = actual_cli_control("B")
        _, other = actual_cli_control("A")
        result = oracle.judge_behavior(facts, drives + other)
        self.assertEqual(result["barriers"], ["no_other_owner_transition"])

    def test_c_selected_authorization_cannot_change(self):
        facts, drives = actual_cli_control("C")
        path = facts["authorization"]["path"]
        original = oracle.artifact
        with patch.object(oracle, "artifact", side_effect=lambda p: original(p) + b" " if str(p) == path else original(p)):
            result = oracle.judge_behavior(facts, drives)
        self.assertEqual(result["barriers"], ["selected_auth_preserved"])

    def test_c_provider_profile_creation_is_a_failure(self):
        facts, drives = actual_cli_control("C")
        profile = Path(facts["host"]["environment"]["XDG_CONFIG_HOME"]) / "soodles/provider.json"
        original = Path.exists
        with patch.object(Path, "exists", lambda p: True if p == profile else original(p)):
            result = oracle.judge_behavior(facts, drives)
        self.assertEqual(result["barriers"], ["no_provider_registration_or_config_files"])

    def test_wrong_python_shell_entry_is_not_positive(self):
        facts, _ = actual_cli_control("B")
        outer = json.loads((CONTROL_ROOT / "raw/B-drive.json").read_bytes())
        record = json.loads(outer["stdout"])
        result = oracle.judge_behavior(facts, [{"record": record}])
        self.assertEqual(result["classification"], "FAIL")

    def test_driver_parser_matches_actual_cli_record(self):
        # A small parser-input container, explicitly NOT a fabricated Codex run.
        facts, _ = actual_cli_control("B")
        outer = json.loads((CONTROL_ROOT / "raw/B-drive-shell.json").read_bytes())
        argv = outer["argv"][3:]  # strip real sandbox-exec -f PROFILE only
        event = {"key": ["parser-control", 1, "command"], "line": 1,
                 "item": {"command": shlex.join(argv), "aggregated_output": outer["stdout"], "exit_code": outer["exit"]}}
        drives, opaque = oracle.extract_drives({"commands": [event]}, facts, argv[3], argv[2])
        self.assertEqual(len(drives), 1)
        self.assertEqual(opaque, [])
        record = json.loads(event["item"]["aggregated_output"])
        record["argv"][-1] = "/wrong/authorization.json"
        event["item"]["aggregated_output"] = json.dumps(record)
        with self.assertRaisesRegex(oracle.EvidenceError, "driver_argv_mismatch"):
            oracle.extract_drives({"commands": [event]}, facts, argv[3], argv[2])

    def test_home_fallback_empty_directories_are_not_credentials(self):
        # Predicate unit control; this does not claim a new live CLI execution.
        facts, drives = actual_cli_control("C")
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / ".config/soodles").mkdir(parents=True)
            facts["host"]["environment"].pop("XDG_CONFIG_HOME")
            facts["host"]["environment"]["HOME"] = directory
            result = oracle.judge_behavior(facts, drives)
        self.assertEqual(result["classification"], "PASS", result)

    def test_retained_prepared_receipt_requires_original_inventory_pin(self):
        facts, _ = actual_cli_control("B")
        facts["authorization"]["prepared_receipt"] = "/control/prepared.json"
        descriptor = {"stratum": "B", "drive": "driver-pin", "workspace": "workspace-pin", "source_before": {}}
        with patch.object(oracle, "read_pin", side_effect=lambda pin: json.dumps(facts).encode() if pin == "workspace-pin" else b"driver"):
            with self.assertRaisesRegex(oracle.EvidenceError, "missing_retained_prepared_pin"):
                oracle.evaluate(descriptor)


class RelocationControls(unittest.TestCase):
    def test_true_three_strata_native_and_archive_identical(self):
        # Copies true CLI artifacts only; never rewrites their captured identities.
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive"
            shutil.copytree(CONTROL_ROOT, archive, symlinks=True)
            descriptor = {"captured_root": str(CONTROL_ROOT), "archived_root": str(archive)}
            for name in CONTROL_FILES:
                with self.subTest(stratum=name):
                    facts, drives = actual_cli_control(name)
                    native = oracle.judge_behavior(facts, drives)
                    workspace = CONTROL_ROOT / "output" / name / "workspace.json"
                    pin = {"path": str(workspace), "sha256": oracle.sha(workspace.read_bytes())}
                    with oracle.observation_scope(descriptor):
                        relocated_facts = json.loads(oracle.read_pin(pin))
                        self.assertEqual(relocated_facts, facts)
                        relocated = oracle.judge_behavior(relocated_facts, drives)
                    self.assertEqual(relocated, native)
                    self.assertEqual(relocated["classification"], "PASS")
            # Prove observations came from the archive, with no native fallback.
            facts, drives = actual_cli_control("B")
            (archive / Path(facts["task"]["handoff"]).relative_to(CONTROL_ROOT)).unlink()
            with oracle.observation_scope(descriptor):
                self.assertEqual(oracle.judge_behavior(facts, drives)["barriers"], ["exact_handoff_projection"])
            self.assertEqual(oracle.judge_behavior(facts, drives)["classification"], "PASS")

    def test_observation_rejects_external_prefix_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive"
            archive.mkdir()
            outside = Path(directory) / "outside"
            outside.write_bytes(b"not readable through relocation")
            (archive / "escape").symlink_to(outside)
            with oracle.observation_scope({"captured_root": "/captured", "archived_root": str(archive)}):
                for path in ("/elsewhere/file", "/captured-other/file", "/captured/../outside", "relative/file"):
                    with self.subTest(path=path):
                        with self.assertRaisesRegex(oracle.EvidenceError, "observation_outside_captured_root"):
                            oracle.artifact(path)
                with self.assertRaisesRegex(oracle.EvidenceError, "observation_symlink_escape"):
                    oracle.artifact("/captured/escape")

    def test_relocation_requires_pair_and_restores_scope_on_error(self):
        with self.assertRaisesRegex(oracle.EvidenceError, "relocation_requires_both_roots"):
            oracle.evaluate({"captured_root": "/captured"})
        with self.assertRaisesRegex(oracle.EvidenceError, "unsupported_stratum"):
            oracle.evaluate({"captured_root": "/captured", "archived_root": "/archive"})
        self.assertEqual(oracle.observed_path("/elsewhere"), Path("/elsewhere"))


if __name__ == "__main__":
    unittest.main()
