"""Selected Git bytes and effect boundaries; sentinels do not prove adherence."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import issue_admission as admission
import issue_atom as atom
import test_issue_atom
import test_issue_execution
from test_supervisor_admission import SupervisorFixture


def pin(path, data):
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest()}


class InstructionContextTests(unittest.TestCase):
    def supervisor(self):
        fixture = SupervisorFixture()
        self.addCleanup(fixture.close)
        return fixture

    def worker(self):
        fixture = test_issue_execution.IssueExecutionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.envelope["schema"] = 2
        head = fixture.envelope["execution"]["source_head"]
        data = admission.git_bytes(fixture.root, head, "allowed.py")
        context = admission.resolve_instruction_context(fixture.root, head, [pin("allowed.py", data)])
        fixture.envelope["execution"]["instruction_context"] = context
        fixture.bind_envelope()
        return fixture

    def test_producer_uses_committed_bytes_and_preserves_legacy(self):
        fixture = self.supervisor()
        path = ".agents/skills/execute/SKILL.md"
        data = admission.git_bytes(fixture.root, fixture.head, path)
        (fixture.root / path).write_text("unselected working copy")
        output, _ = fixture.prepare("selected", instruction_pins=[pin(path, data)])
        envelope = json.loads((output / "envelope.json").read_text())
        self.assertEqual(envelope["schema"], 2)
        self.assertEqual(envelope["execution"]["instruction_context"], {
            "source_head": fixture.head, "files": [{**pin(path, data), "content": data.decode()}]})
        output, _ = fixture.prepare("legacy")
        legacy = json.loads((output / "envelope.json").read_text())
        self.assertEqual(legacy["schema"], 1)
        self.assertNotIn("instruction_context", legacy["execution"])

    def test_invalid_selection_leaves_no_bundle(self):
        fixture = self.supervisor()
        valid = pin("allowed.py", (fixture.root / "allowed.py").read_bytes())
        invalid = [[], None, [valid, valid], [{**valid, "sha256": "0" * 64}],
                   [{"path": "allowed.py"}], [{**valid, "sha256": None}],
                   [valid] * (admission.INSTRUCTION_MAX_FILES + 1)]
        invalid += [[{**valid, "path": path}] for path in (
            "../escape", "/absolute", "a/../allowed.py", ".git/config", "a\\b",
            "missing", "./allowed.py", "a//b", "a\nb", ":(glob)*")]
        # None is the explicit legacy API value, not a selected empty list.
        invalid.remove(None)
        for index, pins in enumerate(invalid):
            with self.subTest(pins=pins), self.assertRaises(admission.AdmissionRefusal):
                fixture.prepare(f"invalid-{index}", instruction_pins=pins)
            self.assertFalse((fixture.external / f"invalid-{index}").exists())
        self.assertFalse(fixture.child_marker.exists())

    def test_committed_symlinks_utf8_and_bounds(self):
        fixture = self.supervisor()
        (fixture.root / "link.md").symlink_to("allowed.py")
        (fixture.root / "directory-link").symlink_to(".agents", target_is_directory=True)
        (fixture.root / "bad.md").write_bytes(b"\xff")
        big = b"a" * (admission.INSTRUCTION_MAX_FILE_BYTES + 1)
        (fixture.root / "big.md").write_bytes(big)
        chunk = b"b" * admission.INSTRUCTION_MAX_FILE_BYTES
        for i in range(5):
            (fixture.root / f"chunk-{i}.md").write_bytes(chunk)
        fixture._git("add", ".")
        fixture._git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "invalid input fixture")
        head = fixture._git("rev-parse", "HEAD")
        cases = [([pin("link.md", b"allowed.py")], "regular_file"),
                 ([pin("directory-link/skills/execute/SKILL.md", b"")], "regular_file"),
                 ([pin("bad.md", b"\xff")], "utf8"),
                 ([pin("big.md", big)], "file_bytes"),
                 ([pin(f"chunk-{i}.md", chunk) for i in range(5)], "total_bytes")]
        for pins, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(admission.AdmissionRefusal, diagnostic):
                admission.resolve_instruction_context(fixture.root, head, pins)

    def test_envelope_rejects_wrong_version_digest_content_and_downgrade(self):
        fixture = self.worker()
        original = copy.deepcopy(fixture.envelope)
        variants = []
        for schema in (0, 3, True, "2", 1):
            value = copy.deepcopy(original)
            value["schema"] = schema
            variants.append(value)
        value = copy.deepcopy(original)
        del value["execution"]["instruction_context"]
        variants.append(value)
        for field, invalid in (("content", "altered"), ("content", "\ud800"),
                               ("sha256", "0" * 64), ("sha256", None)):
            value = copy.deepcopy(original)
            value["execution"]["instruction_context"]["files"][0][field] = invalid
            variants.append(value)
        value = copy.deepcopy(original)
        value["execution"]["instruction_context"]["source_head"] = "0" * 40
        variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(admission.AdmissionRefusal):
                admission.validate_envelope(value)
        self.assertFalse(fixture.effect.exists())

    def test_projection_and_worker_refuse_dropped_or_altered_context_before_launch(self):
        for mode in ("valid", "dropped", "altered", "missing_prompt"):
            with self.subTest(mode=mode):
                fixture = self.worker()
                fixture.admit("supervised")
                fixture.promote_fixture()
                stage = fixture.snapshot["state"]["orders"]["soodles-18"]["stages"][0]
                subject = json.loads(stage["prompt"])
                self.assertEqual(subject["instruction_context"], fixture.envelope["execution"]["instruction_context"])
                if mode == "valid":
                    fixture.launch()
                    self.assertEqual(fixture.effect.read_text(), "observed")
                    continue
                if mode == "dropped":
                    del subject["instruction_context"]
                elif mode == "altered":
                    subject["instruction_context"]["files"][0]["content"] += "altered"
                stage["prompt"] = "" if mode == "missing_prompt" else json.dumps(subject)
                fixture.save_owner()
                with self.assertRaises(admission.AdmissionRefusal):
                    fixture.launch()
                self.assertFalse(fixture.effect.exists())

    def test_invalid_authorization_precedes_provider_checkpoint_and_bundle(self):
        fixture = test_issue_atom.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        path = ".agents/skills/execute/SKILL.md"
        valid = pin(path, admission.git_bytes(fixture.root, fixture.base, path))
        original = copy.deepcopy(fixture.authorization)
        for mode in ("missing", "null", "empty", "wrong_digest", "wrong_schema", "downgrade"):
            value = {**copy.deepcopy(original), "schema_version": 3, "instruction_pins": [valid]}
            if mode == "missing":
                del value["instruction_pins"]
            elif mode == "null":
                value["instruction_pins"] = None
            elif mode == "empty":
                value["instruction_pins"] = []
            elif mode == "wrong_digest":
                value["instruction_pins"] = [{**valid, "sha256": "0" * 64}]
            else:
                value["schema_version"] = 4 if mode == "wrong_schema" else 2
            fixture.path.write_text(json.dumps(value))
            env = {**fixture.env, "SOODLES_AUTHORIZATION_SHA256": atom.digest_file(fixture.path)}
            provider = test_issue_atom.Provider()
            with self.subTest(mode=mode), patch.object(provider, "issues", wraps=provider.issues) as reads:
                with self.assertRaises((admission.AdmissionRefusal, atom.AtomRefusal)):
                    atom.run(fixture.path, environ=env, provider=provider)
                reads.assert_not_called()
                self.assertEqual(provider.create_calls, 0)
                paths = atom.artifact_paths(fixture.path)
                self.assertFalse(paths["state"].exists())
                self.assertFalse(paths["envelope"].exists())

    def test_authorization_revalidated_by_envelope_owner(self):
        fixture = test_issue_atom.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        path = ".agents/skills/execute/SKILL.md"
        selected = pin(path, admission.git_bytes(fixture.root, fixture.base, path))
        value = {**fixture.authorization, "schema_version": 3, "instruction_pins": [selected]}
        fixture.path.write_text(json.dumps(value))
        checked, _ = atom.validate_authorization(fixture.path, atom.digest_file(fixture.path))
        provider = test_issue_atom.Provider()
        fixture.ready_issue(provider)
        output = fixture.outer / "selected" / "admission" / "envelope.json"
        envelope, _ = atom.create_envelope(checked, provider.value, provider.value["body"], output, environ=fixture.env)
        self.assertEqual(envelope["schema"], 2)
        self.assertEqual(envelope["execution"]["instruction_context"]["files"][0]["sha256"], selected["sha256"])
        checked["instruction_pins"][0]["sha256"] = "0" * 64
        invalid = fixture.outer / "invalid" / "admission" / "envelope.json"
        with self.assertRaises(atom.AtomRefusal):
            atom.create_envelope(checked, provider.value, provider.value["body"], invalid, environ=fixture.env)
        self.assertFalse(invalid.parent.parent.exists())

    def test_actual_atom_cli_keeps_same_continuation_on_instruction_refusal(self):
        fixture = test_issue_atom.IssueAtomTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        value = {**fixture.authorization, "schema_version": 3,
                 "instruction_pins": [{"path": ".agents/skills/execute/SKILL.md", "sha256": "0" * 64}]}
        fixture.path.write_text(json.dumps(value))
        env = {k: v for k, v in os.environ.items() if not k.startswith("NOODLE_")}
        env["SOODLES_AUTHORIZATION_SHA256"] = atom.digest_file(fixture.path)
        # Any attempted supplier invocation is an observable error. Admission
        # must reject before it can obtain credentials or construct a provider.
        marker = fixture.outer / "supplier-effect"
        env["NOODLES_TOKEN_COMMAND"] = f"touch '{marker}'"
        command = [str(Path(atom.__file__).parent / "issue-atom"), "run", str(fixture.path)]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["invalid"]["field"], "instruction_context.files.sha256")
        self.assertEqual(receipt["next"]["owner"], "external-supervisor")
        self.assertEqual(receipt["next"]["required"], ["corrected_external_authorization"])
        self.assertEqual(receipt["next"]["argv"], atom.same_command(fixture.path))
        self.assertFalse(receipt["authorizes_landing"])
        self.assertFalse(marker.exists())
        self.assertFalse(atom.artifact_paths(fixture.path)["state"].exists())
        self.assertFalse((fixture.root / ".noodle").exists())


if __name__ == "__main__":
    unittest.main()
