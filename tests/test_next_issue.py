"""Focused controls for RESOLVED -> exact next-Issue authority."""
import json
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
