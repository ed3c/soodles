"""Focused controls for RESOLVED -> exact next-Issue authority."""
import json
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import next_issue


def contract(*, trigger="One causal gap.", owner="Next atom owner",
             write_paths=None, dependencies=None):
    return {
        "schema": 1,
        "trigger": trigger,
        "source": "supervisor supplied bounded candidate",
        "owner": owner,
        "changes": ["Close one exact causal gap."],
        "write_paths": write_paths or ["src/example.py"],
        "behavior": ["Preserve existing owners outside this atom."],
        "defect_controls": ["A planted wrong route must refuse."],
        "non_cases": ["No unrelated scheduler change."],
        "dependencies": dependencies or [],
        "acceptance": "Focused controls and exact-head acceptance pass.",
        "delivery": "Use one PR and the existing landing owner.",
        "reconciliation": "Read back exact provider state.",
        "feature_scope": "One bounded causal atom.",
    }


def candidate(candidate_id, *, repository="ed3c/soodles", title=None,
              write_paths=None, dependencies=None, trigger=None):
    return {
        "candidate_id": candidate_id,
        "repository": repository,
        "title": title or ("Atom " + candidate_id),
        "contract": contract(
            trigger=trigger or ("Trigger " + candidate_id),
            write_paths=write_paths,
            dependencies=dependencies,
        ),
    }


def resolved():
    return {
        "schema": 2,
        "claim": {"repository": "ed3c/soodles", "issue": 120},
        "phase": "resolved",
        "classification": "RESOLVED",
        "next": None,
    }


def provider_issue(repository, number, *, state="open", state_reason=None,
                   closed_at=None, body=""):
    return {
        "repository": repository,
        "number": number,
        "state": state,
        "state_reason": state_reason,
        "closed_at": closed_at,
        "html_url": f"https://github.com/{repository}/issues/{number}",
        "body": body,
    }


def packet(*values, selected=None):
    return {"schema": 1, "selected_candidate": selected,
            "candidates": list(values)}


def frontier(*issues):
    return {"schema": 1, "complete": True, "issues": list(issues)}


class FakeProvider:
    def __init__(self):
        self.posts = 0
        self.created = []

    def api(self, method, url, payload, token):
        if token != "fixture-token":
            raise AssertionError("wrong token")
        if method == "GET":
            return next(issue for issue in self.created
                        if url.endswith('/' + str(issue['number'])))
        if method != "POST":
            raise AssertionError((method, url, payload))
        self.posts += 1
        repository = url.removeprefix(
            "https://api.github.com/repos/").removesuffix("/issues")
        issue = {
            "number": 200 + self.posts,
            "html_url": (
                f"https://github.com/{repository}/issues/{200 + self.posts}"),
            "title": payload["title"],
            "body": payload["body"],
            "state": "open",
        }
        self.created.append(issue)
        return issue


class NextIssueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.host = patch.object(next_issue.provider_credential,
                                 "resolve_host_environment", return_value={})
        self.supplier = patch.object(next_issue.provider_credential,
                                     "supply_token", return_value="fixture-token")
        self.host.start()
        self.token_supplier = self.supplier.start()
        self.addCleanup(self.host.stop)
        self.addCleanup(self.supplier.stop)

    def prepare(self, name, candidates, provider_frontier=None, route="cloud"):
        output = self.root / name
        result = next_issue.prepare(
            resolved(),
            candidates,
            provider_frontier or frontier(),
            {"kind": route},
            output,
        )
        return output, result

    def test_unique_candidate_materializes_exact_cloud_intent(self):
        c = candidate("one")
        output, result = self.prepare("one", packet(c))
        self.assertEqual(result["action"], "create")
        self.assertEqual(result["next"]["kind"], "provider_write")
        self.assertEqual(result["next"]["operation"], "create_issue")
        self.assertEqual(
            result["request"]["repository_full_name"], "ed3c/soodles")
        self.assertEqual(result["request"]["title"], "Atom one")
        self.assertIn(
            "soodles:causal-atom-sha256:", result["request"]["body"])
        intent = json.loads((output / "intent.json").read_text())
        self.assertEqual(intent["request"], result["request"])
        self.assertEqual(intent["status"], "prepared")
        self.assertFalse(intent["authorizes_landing"])
        parsed = next_issue.issue_admission.parse_contract(
            result["request"]["body"])
        self.assertEqual(parsed["write_paths"], ["src/example.py"])

    def test_zero_and_multiple_eligible_never_invent_priority(self):
        duplicate = candidate("duplicate")
        digest = next_issue._fingerprint(duplicate)
        duplicate_body = next_issue._body(duplicate, digest)
        _, stopped = self.prepare(
            "zero",
            packet(duplicate),
            frontier(provider_issue(
                "ed3c/soodles", 9, body=duplicate_body)),
        )
        self.assertEqual(stopped["action"], "stop")
        self.assertIsNone(stopped["next"])
        self.assertFalse((self.root / "zero").exists())

        _, multiple = self.prepare(
            "multiple",
            packet(candidate("a"), candidate("b")),
        )
        self.assertEqual(multiple["action"], "select")
        self.assertEqual(multiple["next"]["owner"], "supervisor")
        self.assertEqual(
            multiple["next"]["required"], ["selected_candidate"])
        self.assertEqual(
            set(multiple["next"]["known"]["eligible"]), {"a", "b"})
        self.assertFalse((self.root / "multiple").exists())

        output = self.root / "selected"
        selected = next_issue.prepare(
            resolved(),
            packet(candidate("a"), candidate("b"), selected="b"),
            frontier(),
            {"kind": "cloud"},
            output,
        )
        self.assertEqual(selected["request"]["title"], "Atom b")
        self.assertTrue((output / "intent.json").is_file())

    def test_dependency_and_write_boundary_are_mechanical_gates(self):
        dep = {
            "repository": "ed3c/soodles",
            "issue": 7,
            "owner": "dependency owner",
            "evidence": "exact provider closure",
        }
        _, blocked = self.prepare(
            "dependency",
            packet(candidate("dep", dependencies=[dep])),
        )
        self.assertEqual(blocked["action"], "stop")
        self.assertIn(
            "dependency_unsatisfied:ed3c/soodles#7",
            blocked["qualification"][0]["reasons"],
        )

        existing_candidate = candidate(
            "existing", write_paths=["src/shared.py"])
        existing_body = next_issue._body(
            existing_candidate, next_issue._fingerprint(existing_candidate))
        _, collision = self.prepare(
            "collision",
            packet(candidate("new", write_paths=["src/shared.py"])),
            frontier(provider_issue(
                "ed3c/soodles", 11, body=existing_body)),
        )
        self.assertEqual(collision["action"], "stop")
        self.assertTrue(any(
            reason.startswith("write_boundary_collision:11:")
            for reason in collision["qualification"][0]["reasons"]
        ))

        completed_dependency = provider_issue(
            "ed3c/soodles", 7,
            state="closed", state_reason="completed",
            closed_at="2026-09-21T00:00:00Z")
        output, ready = self.prepare(
            "dep-ready",
            packet(candidate("dep", dependencies=[dep])),
            frontier(completed_dependency),
        )
        self.assertEqual(ready["action"], "create")
        self.assertTrue((output / "intent.json").exists())

    def test_unresolved_predecessor_and_incomplete_frontier_refuse(self):
        bad = resolved()
        bad["classification"] = None
        with self.assertRaises(next_issue.NextIssueRefusal) as caught:
            next_issue.prepare(
                bad, packet(candidate("one")), frontier(),
                {"kind": "cloud"}, self.root / "bad")
        self.assertEqual(
            caught.exception.invalid["field"], "resolved.classification")

        incomplete = {"schema": 1, "complete": False, "issues": []}
        with self.assertRaises(next_issue.NextIssueRefusal) as caught:
            next_issue.prepare(
                resolved(), packet(candidate("one")), incomplete,
                {"kind": "cloud"}, self.root / "incomplete")
        self.assertEqual(
            caught.exception.invalid["field"], "frontier.complete")

    def test_local_create_uses_only_persisted_intent_and_stops_at_issue_identity(self):
        c = candidate("local")
        output, prepared = self.prepare(
            "local", packet(c), route="local")
        self.assertEqual(prepared["next"]["kind"], "executable")
        self.assertEqual(prepared["next"]["operation"], "execute")
        self.assertEqual(
            prepared["next"]["known"]["intent"], str(output / "intent.json"))

        provider = FakeProvider()
        terminal = next_issue.execute(
            output / "intent.json",
            environ={"GH_TOKEN": "fixture-token"},
            api=provider.api,
        )
        self.assertEqual(provider.posts, 1)
        self.assertEqual(terminal["action"], "created")
        self.assertEqual(terminal["issue"]["number"], 201)
        self.assertIsNone(terminal["next"])
        self.token_supplier.assert_called_with(
            "ed3c/soodles", {"issues": "write"}, environ={})
        again = next_issue.execute(output / "intent.json", environ={}, api=provider.api)
        self.assertEqual(again["issue"], terminal["issue"])
        self.assertEqual(provider.posts, 1)

    def test_unknown_create_never_retries_and_readback_adopts_exactly_one(self):
        c = candidate("unknown")
        output, _ = self.prepare(
            "unknown", packet(c), route="local")
        provider = FakeProvider()

        def lost_response(method, url, payload, token):
            provider.api(method, url, payload, token)
            raise next_issue.ProviderUnknown("lost-response")

        unknown = next_issue.execute(
            output / "intent.json",
            environ={"GH_TOKEN": "fixture-token"},
            api=lost_response,
        )
        self.assertEqual(provider.posts, 1)
        self.assertEqual(unknown["action"], "unknown")
        self.assertEqual(unknown["next"]["kind"], "provider_readback")
        self.assertEqual(unknown["next"]["argv"][-3:], [
            "reconcile", str(output / "intent.json"),
            unknown["next"]["readback_path"]])
        again = next_issue.execute(output / "intent.json", environ={}, api=lost_response)
        self.assertEqual(again["next"]["kind"], "provider_readback")
        self.assertEqual(provider.posts, 1)

        created = provider.created[0]
        readback_issue = provider_issue(
            "ed3c/soodles", created["number"], body=created["body"])
        adopted = next_issue.reconcile(
            output / "intent.json", frontier(readback_issue))
        self.assertEqual(provider.posts, 1)
        self.assertEqual(adopted["action"], "created")
        self.assertEqual(
            adopted["issue"]["number"], created["number"])

        second = provider_issue(
            "ed3c/soodles", created["number"] + 1, body=created["body"])
        with self.assertRaises(next_issue.NextIssueRefusal) as caught:
            next_issue.reconcile(
                output / "intent.json",
                frontier(readback_issue, second))
        self.assertEqual(
            caught.exception.invalid["field"],
            "provider.fingerprint_matches")

    def test_pclass_contains_one_entry_and_no_manual_decisions(self):
        skill = (
            Path(__file__).resolve().parents[1]
            / ".agents/skills/next-issue/SKILL.md"
        ).read_text()
        self.assertIn("./next-issue prepare", skill)
        self.assertIn("current next", skill)
        for forbidden in (
            "pick the first",
            "rank candidates",
            "gh issue create",
            "write the Issue body",
            "retry the POST",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, skill)

    def test_http_500_keeps_request_id_and_offered_state_prevents_reentry(self):
        output, _ = self.prepare("http", packet(candidate("http")), route="local")
        def fail(request, **kwargs):
            state = json.loads((output / "create-state.json").read_text())
            self.assertEqual(state["phase"], "offered")
            self.assertEqual(request.get_header("User-agent"), "soodles-next-issue")
            raise urllib.error.HTTPError(request.full_url, 500, "fixture",
                                         {"X-GitHub-Request-Id": "fixture-id"},
                                         io.BytesIO(b"do not retain echoed credentials"))
        with patch.object(next_issue.urllib.request, "urlopen", side_effect=fail) as http:
            result = next_issue.execute(output / "intent.json", environ={})
            again = next_issue.execute(output / "intent.json", environ={})
        self.assertEqual(http.call_count, 1)
        self.assertEqual(result["diagnostic"], {"status": 500, "request_id": "fixture-id"})
        self.assertEqual(again["next"], result["next"])
        self.assertNotIn("credentials", (output / "create-state.json").read_text())

    def test_legacy_missing_state_and_changed_intent_never_send(self):
        output, _ = self.prepare("legacy", packet(candidate("legacy")), route="local")
        state = output / "create-state.json"
        raw = state.read_bytes()
        state.unlink()
        api = unittest.mock.Mock()
        self.assertEqual(next_issue.execute(output / "intent.json", api=api)["action"], "unknown")
        api.assert_not_called()
        state.write_bytes(raw)
        intent = output / "intent.json"
        intent.write_text(intent.read_text() + " ")
        with self.assertRaises(next_issue.NextIssueRefusal):
            next_issue.execute(intent, api=api)
        api.assert_not_called()

    def test_missing_supplier_refuses_before_offer_without_token_fallback(self):
        output, _ = self.prepare("credential", packet(candidate("credential")), route="local")
        self.token_supplier.side_effect = next_issue.provider_credential.CredentialRefusal(
            "provider_credential_supplier", "absent", "configured_supplier")
        api = unittest.mock.Mock()
        with self.assertRaises(next_issue.NextIssueRefusal):
            next_issue.execute(output / "intent.json", environ={"GH_TOKEN": "ignored"}, api=api)
        api.assert_not_called()
        self.assertEqual(json.loads((output / "create-state.json").read_text())["phase"], "ready")

    def test_concurrent_entry_cannot_send_second_post(self):
        output, _ = self.prepare("concurrent", packet(candidate("concurrent")), route="local")
        provider = FakeProvider()
        def api(method, url, payload, token):
            if method == "POST":
                other = next_issue.execute(output / "intent.json", environ={}, api=provider.api)
                self.assertEqual(other["action"], "unknown")
            return provider.api(method, url, payload, token)
        self.assertEqual(next_issue.execute(output / "intent.json", environ={}, api=api)["action"], "created")
        self.assertEqual(provider.posts, 1)

    def test_process_exit_after_offer_cannot_replay_transport(self):
        for effect in (False, True):
            with self.subTest(effect=effect):
                name = "crash-" + str(effect).lower()
                output, _ = self.prepare(name, packet(candidate(name)), route="local")
                ledger = output / "fixture-effect"
                def crash(*args):
                    if effect:
                        with ledger.open("xb") as stream:
                            stream.write(b"one effect\n")
                            stream.flush()
                            os.fsync(stream.fileno())
                    os._exit(23)
                pid = os.fork()
                if pid == 0:
                    next_issue.execute(output / "intent.json", environ={}, api=crash)
                    os._exit(99)
                _, status = os.waitpid(pid, 0)
                self.assertEqual(os.waitstatus_to_exitcode(status), 23)
                api = unittest.mock.Mock()
                result = next_issue.execute(output / "intent.json", environ={}, api=api)
                self.assertEqual(result["action"], "unknown")
                self.assertEqual(ledger.exists(), effect)
                api.assert_not_called()

    def test_wrong_subject_or_unreadable_response_keeps_one_post(self):
        for kind in ("wrong-post", "wrong-get", "wrong-number", "invalid-json"):
            with self.subTest(kind=kind):
                output, _ = self.prepare(kind, packet(candidate(kind)), route="local")
                provider = FakeProvider()
                def api(method, url, payload, token):
                    issue = provider.api(method, url, payload, token)
                    if kind == "invalid-json" and method == "POST":
                        raise next_issue.ProviderUnknown("provider.json")
                    if kind == "wrong-number" and method == "GET":
                        return {**issue, "number": 999,
                                "html_url": "https://github.com/ed3c/soodles/issues/999"}
                    if (kind == "wrong-post" and method == "POST"
                            or kind == "wrong-get" and method == "GET"):
                        return {**issue, "title": "another subject"}
                    return issue
                for _ in range(2):
                    if kind in ("wrong-get", "wrong-number"):
                        with self.assertRaises(next_issue.NextIssueRefusal):
                            next_issue.execute(output / "intent.json", environ={}, api=api)
                    else:
                        self.assertEqual(next_issue.execute(
                            output / "intent.json", environ={}, api=api)["action"], "unknown")
                self.assertEqual(provider.posts, 1)

    def test_child_and_corrupt_state_refuse_without_transport(self):
        output, _ = self.prepare("child", packet(candidate("child")), route="local")
        api = unittest.mock.Mock()
        with self.assertRaises(next_issue.NextIssueRefusal):
            next_issue.execute(output / "intent.json", environ={"NOODLE_SESSION_ID": "child"}, api=api)
        (output / "create-state.json").write_text('{"phase":')
        with self.assertRaises(next_issue.NextIssueRefusal):
            next_issue.execute(output / "intent.json", environ={}, api=api)
        api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
