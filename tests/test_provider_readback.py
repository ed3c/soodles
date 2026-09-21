"""Focused controls for local provider-readback executable continuation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import provider_readback


ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_FILES = (
    "landing.py",
    "soodles.py",
    "issue_admission.py",
    "issue_execution.py",
    "repository_binding.py",
    "dependency_binding.py",
    "policy/runtime.lock.json",
)


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.external = self.root / "external"
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
            cwd=self.publisher,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        self.verifier = json.loads(identity.stdout)["verifier_sha256"]
        self.context = {
            "schema": 1,
            "kind": "landing",
            "publisher": {
                "root": str(self.publisher),
                "verifier_sha256": self.verifier,
            },
        }
        self.checkpoint = self.external / "checkpoint.json"
        self.checkpoint.write_text("{}\n")
        self.calls = []

    def close(self):
        self.temp.cleanup()

    def landing_result(self, *, merged=False, method="GET", host="api.github.com"):
        base = f"https://{host}/repos/ed3c/soodles/"
        return {
            "owner": "landing.advance",
            "action": "readback",
            "next": {
                "kind": "provider_readback",
                "owner": "GitHub",
                "operation": "advance",
                "required": ["readback"],
                "known": {"checkpoint": str(self.checkpoint)},
                "requests": {
                    "pr": {"method": method, "url": base + "pulls/9"},
                    "issue": {"method": "GET", "url": base + "issues/8"},
                    "commit": {
                        "method": "GET",
                        "url": base + "git/commits/" + "a" * 40,
                    },
                    "branch": {"method": "GET", "url": base + "branches/main"},
                    "run": {"method": "GET", "url": base + "actions/runs/77"},
                    "jobs": {
                        "method": "GET",
                        "url": base + "actions/runs/77/jobs",
                    },
                },
                "merge_commit": (
                    "If pr.merged, GET git/commits/{pr.merge_commit_sha} "
                    "in this repository."
                ),
            },
        }

    def landing_api(self, merged):
        merge_sha = "d" * 40

        def api(method, url, token):
            self.calls.append((method, url, token))
            if token != "fixture-token":
                raise AssertionError("wrong token")
            if method != "GET":
                raise AssertionError(method)
            if url.endswith("/pulls/9"):
                return {
                    "number": 9,
                    "merged": merged,
                    "merge_commit_sha": merge_sha if merged else None,
                }, {}
            if "/git/commits/" + merge_sha in url:
                return {
                    "sha": merge_sha,
                    "tree": {"sha": "b" * 40},
                    "parents": [{"sha": "c" * 40}, {"sha": "a" * 40}],
                }, {}
            if url.endswith("/issues/8"):
                return {
                    "number": 8, "state": "open",
                    "html_url": "https://github.com/ed3c/soodles/issues/8",
                }, {}
            if "/git/commits/" + "a" * 40 in url:
                return {"sha": "a" * 40, "tree": {"sha": "b" * 40}}, {}
            if url.endswith("/branches/main"):
                return {"name": "main", "commit": {"sha": "c" * 40}}, {}
            if url.endswith("/actions/runs/77"):
                return {
                    "id": 77, "run_attempt": 1,
                    "head_sha": "a" * 40,
                    "status": "completed", "conclusion": "success",
                }, {}
            if url.endswith("/actions/runs/77/jobs"):
                return {"total_count": 0, "jobs": []}, {}
            raise AssertionError(url)

        return api


class ProviderReadbackTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)
        self.env = {"GH_TOKEN": "fixture-token"}

    def test_landing_preserves_keys_and_returns_exact_reentry(self):
        output = self.f.external / "landing-unmerged"
        result = provider_readback.consume(
            self.f.landing_result(merged=False),
            self.f.context,
            output,
            environ=self.env,
            api=self.f.landing_api(False),
        )
        self.assertEqual(result["consumer"], "landing")
        self.assertEqual(result["provider_reads"], 6)
        self.assertEqual(result["next"]["owner"], "landing.advance")
        self.assertEqual(
            result["next"]["argv"],
            [
                sys.executable, "-B", str(self.f.publisher / "soodles.py"),
                "landing", "advance", str(self.f.checkpoint),
                str(output / "readback.json"),
            ],
        )
        readback = json.loads((output / "readback.json").read_text())
        self.assertEqual(
            set(readback),
            {"pr", "issue", "commit", "branch", "run", "jobs"})
        self.assertNotIn("merge_commit", readback)
        self.assertNotIn("fixture-token", (output / "result.json").read_text())

    def test_merged_pr_adds_exactly_one_confirmed_merge_commit_get(self):
        output = self.f.external / "landing-merged"
        result = provider_readback.consume(
            self.f.landing_result(merged=True),
            self.f.context,
            output,
            environ=self.env,
            api=self.f.landing_api(True),
        )
        self.assertEqual(result["provider_reads"], 7)
        merge_calls = [
            call for call in self.f.calls
            if "/git/commits/" + "d" * 40 in call[1]
        ]
        self.assertEqual(len(merge_calls), 1)
        readback = json.loads((output / "readback.json").read_text())
        self.assertEqual(readback["merge_commit"]["sha"], "d" * 40)

    def test_next_issue_paginates_filters_prs_and_returns_reconcile_argv(self):
        consumer_root = self.f.external / "consumer"
        consumer_root.mkdir()
        cli = consumer_root / "next-issue"
        cli.write_text("#!/usr/bin/env python3\n")
        intent = self.f.external / "intent.json"
        intent.write_text("{}\n")
        first = (
            "https://api.github.com/repos/ed3c/soodles/issues"
            "?state=all&per_page=100&page=1"
        )
        second = (
            "https://api.github.com/repos/ed3c/soodles/issues"
            "?state=all&per_page=100&page=2"
        )
        owner_result = {
            "owner": "next-issue.execute",
            "action": "unknown",
            "next": {
                "kind": "provider_readback",
                "owner": "GitHub",
                "operation": "reconcile",
                "required": ["frontier"],
                "known": {
                    "intent": str(intent),
                    "causal_fingerprint": "f" * 64,
                },
                "requests": {
                    "issues": {"method": "GET", "url": first},
                },
            },
        }
        context = {
            "schema": 1,
            "kind": "next_issue",
            "consumer_root": str(consumer_root),
        }
        calls = []

        def api(method, url, token):
            calls.append((method, url, token))
            if url == first:
                return [
                    {
                        "number": 1,
                        "state": "open",
                        "state_reason": None,
                        "closed_at": None,
                        "html_url": "https://github.com/ed3c/soodles/issues/1",
                        "body": "one",
                    },
                    {
                        "number": 9,
                        "state": "open",
                        "html_url": "https://github.com/ed3c/soodles/pull/9",
                        "body": "pr",
                        "pull_request": {"url": "x"},
                    },
                ], {"Link": f'<{second}>; rel="next"'}
            if url == second:
                return [
                    {
                        "number": 2,
                        "state": "closed",
                        "state_reason": "completed",
                        "closed_at": "2026-09-21T00:00:00Z",
                        "html_url": "https://github.com/ed3c/soodles/issues/2",
                        "body": "two",
                    }
                ], {}
            raise AssertionError(url)

        output = self.f.external / "frontier"
        result = provider_readback.consume(
            owner_result, context, output,
            environ=self.env, api=api)
        self.assertEqual(result["consumer"], "next_issue")
        self.assertEqual(result["provider_reads"], 2)
        frontier = json.loads((output / "frontier.json").read_text())
        self.assertTrue(frontier["complete"])
        self.assertEqual(
            [item["number"] for item in frontier["issues"]], [1, 2])
        self.assertEqual(
            result["next"]["argv"],
            [
                sys.executable, "-B", str(cli), "reconcile",
                str(intent), str(output / "frontier.json"),
            ],
        )
        self.assertEqual([call[1] for call in calls], [first, second])

    def test_wrong_method_host_missing_token_and_output_overwrite_refuse(self):
        calls = []

        def api(method, url, token):
            calls.append((method, url, token))
            return {}, {}

        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            provider_readback.consume(
                self.f.landing_result(method="POST"),
                self.f.context,
                self.f.external / "post",
                environ=self.env,
                api=api,
            )
        self.assertEqual(caught.exception.invalid["field"],
                         "next.requests.pr.method")
        self.assertEqual(calls, [])

        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            provider_readback.consume(
                self.f.landing_result(host="example.com"),
                self.f.context,
                self.f.external / "foreign-host",
                environ=self.env,
                api=api,
            )
        self.assertEqual(caught.exception.invalid["field"], "request.host")
        self.assertEqual(calls, [])

        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            provider_readback.consume(
                self.f.landing_result(),
                self.f.context,
                self.f.external / "missing-token",
                environ={},
                api=api,
            )
        self.assertEqual(caught.exception.invalid["field"], "credential")
        self.assertEqual(calls, [])

        output = self.f.external / "once"
        provider_readback.consume(
            self.f.landing_result(),
            self.f.context,
            output,
            environ=self.env,
            api=self.f.landing_api(False),
        )
        before = sorted(str(path.relative_to(output)) for path in output.rglob("*"))
        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            provider_readback.consume(
                self.f.landing_result(),
                self.f.context,
                output,
                environ=self.env,
                api=self.f.landing_api(False),
            )
        self.assertEqual(caught.exception.invalid["field"], "output.exists")
        after = sorted(str(path.relative_to(output)) for path in output.rglob("*"))
        self.assertEqual(before, after)

    def test_wrong_publisher_and_redirect_are_hard_refusals(self):
        context = json.loads(json.dumps(self.f.context))
        context["publisher"]["verifier_sha256"] = "f" * 64
        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            provider_readback.consume(
                self.f.landing_result(),
                context,
                self.f.external / "wrong-publisher",
                environ=self.env,
                api=self.f.landing_api(False),
            )
        self.assertEqual(caught.exception.invalid["field"],
                         "publisher.identity")

        handler = provider_readback._NoRedirect()
        with self.assertRaises(provider_readback.ReadbackRefusal) as caught:
            handler.redirect_request(
                None, None, 302, "redirect",
                {"Location": "https://example.com/"}, "https://example.com/")
        self.assertEqual(caught.exception.invalid["field"],
                         "provider.redirect")

    def test_pclass_routes_provider_readback_without_manual_get_assembly(self):
        skill = (
            ROOT / ".agents/skills/provider-readback/SKILL.md"
        ).read_text()
        verify = (
            ROOT / ".agents/skills/verify-noodle/SKILL.md"
        ).read_text()
        self.assertIn("./provider-readback consume", skill)
        self.assertIn("provider-readback Skill", verify)
        self.assertIn("Do not use curl, gh, browser", skill)
        self.assertIn("do not translate GETs, pagination", verify)


if __name__ == "__main__":
    unittest.main()
