"""Exercise committed selection through the real CLI in disposable repositories."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import issue_admission
import system_context


COMMON = "contracts/system-v1/common.md"
CONTEXT = "contracts/system-v1/instruction-context.md"
LANDING = "contracts/system-v1/landing.md"
RECOVERY = "contracts/system-v1/recovery.md"


class SystemContextTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        source = Path(system_context.__file__).parent
        for name in ("system-context", "system_context.py", "issue_admission.py",
                     "soodles.py", "repository_binding.py"):
            shutil.copy2(source / name, self.root / name)
        self.routes = {"schema": 1, "paths": {
            path: {"requires": [] if path == COMMON else [COMMON]}
            for path in sorted(system_context.KNOWN_PATHS)}}
        self.routes["paths"][RECOVERY]["requires"].append(LANDING)
        for path in self.routes["paths"]:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("# " + path + "\nCommitted 中文.\n").encode())
        self.write_routes(self.routes)
        self.git("init", "-q")
        self.head = self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root,
                                       stderr=subprocess.PIPE, text=True).strip()

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "Commit context fixture to distinguish Git from checkout")
        return self.git("rev-parse", "HEAD")

    def write_routes(self, value):
        (self.root / system_context.ROUTES).write_text(
            value if isinstance(value, str) else json.dumps(value))

    def cli(self, *roots):
        before = self.git("status", "--porcelain", "--untracked-files=all")
        result = subprocess.run([str(self.root / "system-context"), *roots],
                                cwd=self.root.parent, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all"), before)
        value = json.loads(result.stdout)
        self.assertFalse(value["authorizes_landing"])
        self.assertEqual(value["owner"], "soodles.system-context")
        return result.returncode, value

    def refused(self, *roots, field=None):
        code, value = self.cli(*roots)
        self.assertNotEqual(code, 0)
        self.assertEqual(value["status"], "refused")
        self.assertNotIn("instruction_context", value)
        self.assertEqual(set(value["invalid"]), {"field", "value"})
        self.assertEqual(value["next"]["kind"], "input")
        self.assertTrue(value["next"]["owner"])
        self.assertTrue(value["next"]["required"])
        self.assertNotIn("argv", value["next"])
        if field:
            self.assertEqual(value["invalid"]["field"], field)

    def test_single_root_exact_committed_bytes_and_source_identity(self):
        code, value = self.cli(CONTEXT)
        self.assertEqual(code, 0)
        self.assertEqual(value["status"], "ready")
        self.assertEqual(value["source_head"], self.head)
        self.assertEqual(value["instruction_context"]["source_head"], self.head)
        self.assertEqual(value["instruction_paths"], [COMMON, CONTEXT])
        self.assertEqual(value["paths"], {
            path: self.routes["paths"][path] for path in (COMMON, CONTEXT)})
        for item, pin in zip(value["instruction_context"]["files"], value["instruction_pins"]):
            data = (self.root / item["path"]).read_bytes()
            self.assertEqual(item["content"].encode(), data)
            self.assertEqual(pin, {"path": item["path"], "sha256": hashlib.sha256(data).hexdigest()})
            self.assertEqual(item["sha256"], pin["sha256"])

    def test_shared_and_roots_are_deduplicated_and_deterministic(self):
        code, value = self.cli(RECOVERY, CONTEXT, RECOVERY)
        self.assertEqual(code, 0)
        self.assertEqual(value, self.cli(CONTEXT, RECOVERY)[1])
        self.assertEqual(value["instruction_paths"], [COMMON, CONTEXT, LANDING, RECOVERY])
        self.assertEqual(self.cli(COMMON)[1]["instruction_paths"], [COMMON])

    def test_dirty_routes_and_instructions_are_not_consumed(self):
        expected = self.cli(CONTEXT)[1]
        (self.root / CONTEXT).write_text("dirty instruction")
        self.write_routes("not JSON")
        self.assertEqual(self.cli(CONTEXT)[1], expected)
        (self.root / CONTEXT).unlink()
        (self.root / CONTEXT).symlink_to("/missing")
        self.assertEqual(self.cli(CONTEXT)[1], expected)

    def test_unknown_traversal_and_empty_roots(self):
        self.refused(field="roots")
        for path in ("../contracts/system-v1.md", "/etc/passwd", "contracts/system-v1.md",
                     "contracts/system-v1/missing.md", "./" + CONTEXT,
                     "contracts//system-v1/common.md", "contracts/system-v1/../common.md",
                     ".git/config", "contracts\\system-v1\\common.md", "a\nb", ":(glob)*"):
            with self.subTest(path=path):
                self.refused(path, field="roots.path")

    def test_cycles_and_dangling_edges_even_when_unselected(self):
        for mode in ("cycle", "self", "dangling"):
            value = copy.deepcopy(self.routes)
            value["paths"][LANDING]["requires"] = [
                RECOVERY if mode == "cycle" else LANDING if mode == "self" else "missing.md"]
            self.write_routes(value)
            self.commit()
            with self.subTest(mode=mode):
                self.refused(CONTEXT, field="routes.dangling" if mode == "dangling" else "routes.cycle")

    def test_duplicate_json_keys_at_every_level(self):
        samples = [
            '{"schema":1,"schema":1,"paths":{}}',
            '{"schema":1,"paths":{"%s":{"requires":[]},"%s":{"requires":[]}}}' % (COMMON, COMMON),
            '{"schema":1,"paths":{"%s":{"requires":[],"requires":[]}}}' % COMMON,
        ]
        for raw in samples:
            self.write_routes(raw)
            self.commit()
            self.refused(CONTEXT, field="routes.duplicate_key")

    def test_invalid_graph_shapes(self):
        samples = [[], {}, {**self.routes, "extra": 1},
                   {**self.routes, "schema": True}, {**self.routes, "schema": 2},
                   {"schema": 1, "paths": []}, {"schema": 1, "paths": {}},
                   {"schema": 1, "paths": {"arbitrary.md": {"requires": []}}}]
        for record in (None, [], {}, {"requires": [], "extra": 1}, {"requires": COMMON},
                       {"requires": [COMMON, COMMON]}, {"requires": [None]},
                       {"requires": [[COMMON]]}, {"requires": ["../common.md"]}):
            value = copy.deepcopy(self.routes)
            value["paths"][RECOVERY] = record
            samples.append(value)
        for value in samples:
            with self.subTest(value=value):
                self.write_routes(value)
                self.commit()
                self.refused(CONTEXT)
        self.write_routes("{")
        self.commit()
        self.refused(CONTEXT, field="routes.json")

    def test_committed_symlink_directory_missing_and_non_utf8(self):
        target = self.root / CONTEXT
        target.unlink()
        target.symlink_to("common.md")
        self.commit()
        self.refused(CONTEXT, field="instruction_pins.regular_file")
        target.unlink()
        target.mkdir()
        (target / "child").write_text("directory")
        self.commit()
        self.refused(CONTEXT, field="instruction_pins.regular_file")
        shutil.rmtree(target)
        self.commit()
        self.refused(CONTEXT, field="candidate.evidence_path")
        target.write_bytes(b"\xff")
        self.commit()
        self.refused(CONTEXT, field="instruction_pins.utf8")

    def test_committed_route_symlink_is_refused(self):
        route = self.root / system_context.ROUTES
        route.unlink()
        route.symlink_to("common.md")
        self.commit()
        self.refused(CONTEXT, field="instruction_pins.regular_file")

    def test_non_json_numbers_and_excessive_nesting_refuse_as_json(self):
        for raw in ('NaN', '{"schema":Infinity,"paths":{}}',
                    '{"schema":-Infinity,"paths":{}}'):
            self.write_routes(raw)
            self.commit()
            self.refused(CONTEXT, field="routes.json")
        # Parser depth limits differ across Python versions; both a parse
        # refusal and an invalid top-level shape must remain structured JSON.
        self.write_routes('[' * 1100 + ']' * 1100)
        self.commit()
        self.refused(CONTEXT)

    def test_recursion_faults_at_cli_boundaries_remain_bounded_json(self):
        # Controlled faults distinguish parsing, validation, diagnostic repr,
        # and output encoding without relying on a carrier's depth threshold.
        faults = (
            'patch.object(c.json, "loads", side_effect=RecursionError("parse"))',
            'patch.object(c, "validate_routes", side_effect=RecursionError("validate"))',
            'patch.object(c, "validate_routes", side_effect=bad_diagnostic)',
            'patch.object(c.json, "dumps", side_effect=fail_first_encoding)',
        )
        prefix = """import sys
from unittest.mock import patch
import system_context as c
class Unrepresentable:
    def __repr__(self):
        raise RecursionError("diagnostic repr")
def bad_diagnostic(value):
    raise c.AdmissionRefusal("routes.fields", Unrepresentable())
real_dumps = c.json.dumps
encoding_calls = 0
def fail_first_encoding(*args, **kwargs):
    global encoding_calls
    encoding_calls += 1
    if encoding_calls == 1:
        raise RecursionError("output encoding")
    return real_dumps(*args, **kwargs)
"""
        for fault in faults:
            with self.subTest(fault=fault):
                script = prefix + "with " + fault + ":\n    raise SystemExit(c.main([" + repr(CONTEXT) + "]))\n"
                result = subprocess.run([sys.executable, "-c", script], cwd=self.root,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr, "")
                self.assertLess(len(result.stdout), 1024)
                value = json.loads(result.stdout)
                self.assertEqual(value["status"], "refused")
                self.assertFalse(value["authorizes_landing"])
                self.assertNotIn("instruction_context", value)
                self.assertTrue(value["invalid"]["field"])
                self.assertEqual(value["next"]["required"],
                                 ["valid_committed_system_context_selection"])

    def test_committed_digest_changes_and_resolver_rejects_old_pin(self):
        original = self.cli(CONTEXT)[1]
        (self.root / CONTEXT).write_text("new committed context\n")
        head = self.commit()
        current = self.cli(CONTEXT)[1]
        self.assertEqual(current["source_head"], head)
        self.assertNotEqual(original["instruction_pins"], current["instruction_pins"])
        with self.assertRaisesRegex(issue_admission.AdmissionRefusal, "sha256"):
            issue_admission.resolve_instruction_context(
                self.root, head, original["instruction_pins"])

    def test_entry_consumers_are_committed_complete_and_fail_on_dangling_mapping(self):
        source = Path(system_context.__file__).parent
        for name in ("atom_repair.py", "policy/repair-policy.json", "issue_atom.py",
                     "schema_manager.py", "policy/host-finalization.json",
                     "candidate_publication.py", "provider_readback.py", "issue-atom", "provider-readback", "soodles"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, target)
        routes = json.loads((source / system_context.ROUTES).read_text())
        self.write_routes(routes)
        head = self.commit()
        code, value = self.cli("entry", "issue-atom", "run")
        self.assertEqual(code, 0)
        self.assertEqual(value["source_head"], head)
        self.assertEqual(value["entry"], "issue-atom run")
        self.assertEqual(set(value["instruction_paths"]), {
            COMMON, "contracts/system-v1/issue-atom.md", "contracts/system-v1/candidate.md",
            "contracts/system-v1/readback.md"})
        self.assertNotIn(LANDING, value["instruction_paths"])
        self.assertIn("issue_atom.refresh_publication", {d["consumer"] for d in value["consumers"]})
        self.assertIn("policy/repair-policy.json", {p["path"] for p in value["source_pins"]})
        (self.root / "policy/repair-policy.json").write_text("dirty policy")
        self.assertEqual(self.cli("entry", "issue-atom", "run")[1], value)
        for entry in (("soodles", "candidate", "publish"), ("provider-readback", "consume")):
            self.assertEqual(self.cli("entry", *entry)[0], 0)
        self.refused("entry", "issue-atom", "run", "--retry", field="entry.arguments")
        self.refused("entry", "issue-atom", "restart", field="entry.unknown")
        shutil.copy2(source / "policy/repair-policy.json", self.root / "policy/repair-policy.json")
        routes["paths"]["contracts/system-v1/candidate.md"]["requires"] = []
        self.write_routes(routes)
        self.commit()
        self.refused("entry", "soodles", "candidate", "publish", field="entry.prerequisite")
        routes["paths"]["contracts/system-v1/candidate.md"]["requires"] = [COMMON]
        routes["entries"]["issue-atom run"]["decisions"][0]["requires"] = ["missing.md"]
        self.write_routes(routes)
        self.commit()
        self.refused("entry", "issue-atom", "run", field="entry.requires")


if __name__ == "__main__":
    unittest.main()
