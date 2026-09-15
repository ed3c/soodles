import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import soodles


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "policy").mkdir()
        self.lock = soodles.load_lock(soodles.ROOT)
        self.binary = self.root / "noodle"
        self.binary.write_text("#!/bin/sh\nprintf '%s\\n' '" + self.lock["release"] + "'\n")
        self.binary.chmod(0o755)
        self.lock["binary_sha256"] = soodles.digest(self.binary)
        self.write_lock()

    def write_lock(self):
        (self.root / "policy/runtime.lock.json").write_text(json.dumps(self.lock))

    def test_admitted_version_is_observed_not_inferred_from_filename(self):
        result = soodles.runtime_check(self.root, self.binary)
        self.assertEqual(result["observed_version"], self.lock["release"])
        self.assertFalse(result["authorizes_landing"])

    def test_wrong_digest_refuses_before_executable_sentinel(self):
        sentinel = self.root / "effect"
        self.binary.write_text(f"#!/bin/sh\ntouch '{sentinel}'\n")
        with self.assertRaisesRegex(soodles.Refusal, r"runtime check: invalid binary.sha256=.*runtime check --help"):
            soodles.runtime_check(self.root, self.binary)
        self.assertFalse(sentinel.exists())

    def test_missing_binary_does_not_fall_back_to_path(self):
        self.binary.unlink()
        with patch.object(soodles, "run") as run:
            with self.assertRaisesRegex(soodles.Refusal, "binary.path"):
                soodles.runtime_check(self.root, self.binary)
            run.assert_not_called()

    def test_wrong_observed_version_refuses_worktree_execution(self):
        self.binary.write_text("#!/bin/sh\nprintf '%s\\n' 'v0.0.0'\n")
        self.lock["binary_sha256"] = soodles.digest(self.binary)
        self.write_lock()
        with self.assertRaisesRegex(soodles.Refusal, "binary.version"):
            soodles.runtime_check(self.root, self.binary)

    def test_unsupported_host_refuses_before_execution(self):
        with patch.object(soodles.platform, "system", return_value="Darwin"), patch.object(soodles, "run") as run:
            with self.assertRaisesRegex(soodles.Refusal, "invalid platform"):
                soodles.runtime_check(self.root, self.binary)
            run.assert_not_called()

    def test_wrong_repository_and_unknown_policy_fields_refuse(self):
        for field, value in (("repository", "other/repo"), ("permission", "write")):
            with self.subTest(field=field):
                original = dict(self.lock)
                self.lock[field] = value
                self.write_lock()
                with patch.object(soodles, "run") as run:
                    with self.assertRaises(soodles.Refusal):
                        soodles.runtime_check(self.root, self.binary)
                    run.assert_not_called()
                self.lock = original

    def test_dirty_candidate_rejects_before_binary_and_tests(self):
        soodles.checked(["git", "init", "-b", "main"], self.root)
        soodles.checked(["git", "add", "."], self.root)
        soodles.checked(["git", "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid",
                         "commit", "-m", "fixture"], self.root)
        (self.root / "untracked").write_text("dirty")
        with patch.object(soodles, "runtime_check") as check:
            with self.assertRaisesRegex(soodles.Refusal, "source.residue"):
                soodles.acceptance_verify(self.root, self.binary)
            check.assert_not_called()

    def test_fixture_environment_drops_provider_and_live_noodle_identity(self):
        values = {"GH_TOKEN": "sentinel", "NOODLE_PROJECT_DIR": "/production",
                  "NOODLE_SESSION_ID": "live", "PYTHONPATH": "/other", "GIT_DIR": "/other/.git"}
        with patch.dict(os.environ, values):
            self.assertFalse(set(values) & set(soodles.clean_env()))

    def test_all_command_help_routes_are_noninteractive(self):
        for route in ([], ["runtime"], ["runtime", "check"], ["acceptance"], ["acceptance", "verify"]):
            result = soodles.run(["./soodles", *route, "--help"], soodles.ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Examples:", result.stdout)

    def test_missing_required_binary_is_actionable(self):
        result = soodles.run(["./soodles", "runtime", "check"], soodles.ROOT)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("binary", result.stderr)
        self.assertIn("./soodles runtime check --help", result.stderr)


if __name__ == "__main__":
    unittest.main()
