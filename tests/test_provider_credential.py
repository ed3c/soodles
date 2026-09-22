import json
import subprocess
import unittest
from unittest.mock import patch

import provider_credential as credential


class ProviderCredentialTests(unittest.TestCase):
    def test_real_supplier_gets_exact_scope_and_no_inherited_token(self):
        command = ('test -z "$GH_TOKEN$GITHUB_TOKEN" && '
                   'test "$NOODLES_APP_REPOSITORIES_JSON" = \'["soodles"]\' && '
                   'test "$NOODLES_APP_PERMISSIONS_JSON" = \'{"issues": "read"}\' && '
                   'printf fixture-token')
        self.assertEqual(credential.supply_token("ed3c/soodles", {"issues": "read"}, environ={
            "NOODLES_TOKEN_COMMAND": command, "GH_TOKEN": "stale", "GITHUB_TOKEN": "stale",
            "NOODLES_APP_REPOSITORIES_JSON": '["other"]',
            "NOODLES_APP_PERMISSIONS_JSON": '{"administration":"write"}',
        }), "fixture-token")

    def test_missing_supplier_does_not_fall_back_to_parent_token(self):
        with self.assertRaises(credential.CredentialRefusal) as caught:
            credential.supply_token("ed3c/soodles", {}, environ={"GH_TOKEN": "stale"})
        self.assertEqual(caught.exception.required, "NOODLES_TOKEN_COMMAND")

    def test_bad_output_and_failure_are_redacted(self):
        for command in ("printf 'fixture-secret\\nsecond'", "printf '\\001'",
                        "printf fixture-secret >&2; exit 7", "true"):
            with self.subTest(command=command), self.assertRaises(credential.CredentialRefusal) as caught:
                credential.supply_token("ed3c/soodles", {}, environ={"NOODLES_TOKEN_COMMAND": command})
            self.assertNotIn("fixture-secret", str(caught.exception))

    def test_timeout_exception_does_not_expose_output_or_command(self):
        error = subprocess.TimeoutExpired("fixture-secret-command", 30,
                                          output="fixture-secret", stderr="fixture-secret")
        with patch.object(credential.subprocess, "run", side_effect=error), \
             self.assertRaises(credential.CredentialRefusal) as caught:
            credential.supply_token("ed3c/soodles", {}, environ={"NOODLES_TOKEN_COMMAND": "configured"})
        self.assertEqual(caught.exception.value, "TimeoutExpired")
        self.assertNotIn("fixture-secret", str(caught.exception))

    def test_clean_child_keeps_normal_environment_not_host_capability(self):
        env = {key: "sensitive" for key in (
            "GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
            "NOODLES_TOKEN_COMMAND", "NOODLES_APP_CLIENT_ID", "NOODLES_APP_PRIVATE_KEY_PATH",
            "NOODLES_APP_INSTALLATION_ID", "NOODLES_GITHUB_TOKEN", "GITHUB_APP_ID",
            "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND")}
        env["PATH"] = "/fixture/bin"
        self.assertEqual(credential.clean_child_env(env), {"PATH": "/fixture/bin"})
