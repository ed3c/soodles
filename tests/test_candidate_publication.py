import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import candidate_publication as publication


class Result:
    def __init__(self, returncode=0):
        self.returncode = returncode


class Provider:
    def __init__(self, base, issue_body):
        self.base = base
        self.issue_body = issue_body
        self.ref = None
        self.pull_value = None
        self.create_calls = 0
        self.unknown_create = False
        self.drop_create = False
        self.reads = 0

    def repository_info(self):
        self.reads += 1
        return {"full_name": "ed3c/soodles", "default_branch": "main"}

    def issue(self, number):
        self.reads += 1
        return {"number": number, "state": "open", "title": "Publication atom",
                "body": self.issue_body}

    def base_head(self, branch):
        self.reads += 1
        return self.base if branch == "main" else None

    def branch(self, branch):
        self.reads += 1
        return None if self.ref is None else {"ref": "refs/heads/" + branch,
                                               "object": {"sha": self.ref}}

    def pulls(self, branch, base):
        self.reads += 1
        return [] if self.pull_value is None else [self.pull_value]

    def create_pull(self, title, branch, base, body):
        self.create_calls += 1
        if not self.drop_create:
            self.pull_value = exact_pull(41, branch, self.ref, base, body)
        if self.unknown_create:
            raise publication.ProviderMutationUnknown("lost response")
        return self.pull_value

    def pull(self, number):
        self.reads += 1
        return self.pull_value if self.pull_value and self.pull_value["number"] == number else None


def exact_pull(number, branch, head, base, body):
    return {"number": number, "state": "open", "body": body,
            "html_url": f"https://github.com/ed3c/soodles/pull/{number}",
            "head": {"ref": branch, "sha": head}, "base": {"ref": base}}


class CandidatePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        outer = Path(self.temp.name)
        self.project = outer / "project"
        self.root = self.project / ".worktrees" / "candidate"
        self.command(outer, "git", "init", "-b", "main", self.project)
        self.command(self.project, "git", "config", "user.name", "Publication Test")
        self.command(self.project, "git", "config", "user.email", "publication@example.invalid")
        (self.project / ".gitignore").write_text(".worktrees/\n.noodle/\n")
        self.command(self.project, "git", "add", ".gitignore")
        self.command(self.project, "git", "commit", "-m", "base")
        self.base = self.value(self.project, "git", "rev-parse", "HEAD")
        self.command(self.project, "git", "remote", "add", "origin", "git@github.com:ed3c/soodles.git")
        self.command(self.project, "git", "worktree", "add", "-b", "candidate", self.root, self.base)
        (self.root / "candidate.txt").write_text("candidate\n")
        self.command(self.root, "git", "add", "candidate.txt")
        self.command(self.root, "git", "commit", "-m", "candidate")
        self.head = self.value(self.root, "git", "rev-parse", "HEAD")
        self.tree = self.value(self.root, "git", "rev-parse", "HEAD^{tree}")
        runtime = self.project / ".noodle"
        events = runtime / "sessions" / "session-1" / "events.ndjson"
        events.parent.mkdir(parents=True)
        snapshot = runtime / "state.snapshot.json"
        snapshot.write_text('{"fixture":"canonical"}\n')
        events.write_text('{"type":"stage_message","fixture":"completed"}\n')
        self.acceptance = {"repository": "ed3c/soodles", "scope": "candidate runtime acceptance",
                           "candidate": {"head": self.head, "tree": self.tree},
                           "authorizes_landing": False}
        self.claim = {
            "schema_version": 1, "owner": "Noodle", "repository": "ed3c/soodles",
            "subject": "ed3c/soodles#128", "order_id": "soodles-128", "stage_index": 0,
            "attempt_id": "soodles-128:0:0", "session_id": "session-1",
            "worktree_name": "candidate", "worktree_path": str(self.root), "branch": "candidate",
            "head": self.head, "tree": self.tree, "base_branch": "main", "base_head": self.base,
            "push_remote": "origin", "remote_url": "git@github.com:ed3c/soodles.git",
            "evidence": {"canonical_snapshot_sha256": publication._digest(snapshot),
                         "session_events_sha256": publication._digest(events)},
            "authorizes_provider_write": False, "authorizes_landing": False,
        }
        self.provider = Provider(self.base, issue_body(self.base))

    def command(self, cwd, *argv):
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def value(self, cwd, *argv):
        return self.command(cwd, *argv).stdout.strip()

    def push(self, result=0):
        def operation(root, *args, **kwargs):
            self.assertEqual(Path(root), self.root)
            self.assertIn("--force-with-lease=refs/heads/soodles/issue-128-" + self.head[:12] + ":", args)
            self.provider.ref = self.head
            return Result(result)
        return operation

    def test_creates_exact_branch_and_pr(self):
        result = publication.publish(self.root, self.acceptance, self.claim,
                                     self.provider, push=self.push())
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["pr"]["number"], 41)
        self.assertFalse(result["authorizes_landing"])
        self.assertEqual(self.provider.create_calls, 1)

    def test_reuses_exact_branch_and_pr_without_writes(self):
        branch = "soodles/issue-128-" + self.head[:12]
        self.provider.ref = self.head
        self.provider.pull_value = exact_pull(41, branch, self.head, "main", "Refs ed3c/soodles#128")
        result = publication.publish(self.root, self.acceptance, self.claim, self.provider,
                                     push=lambda *_a, **_k: self.fail("push called"))
        self.assertEqual(result["status"], "reused")
        self.assertEqual(self.provider.create_calls, 0)

    def test_lost_create_response_adopts_only_fresh_exact_readback(self):
        self.provider.unknown_create = True
        result = publication.publish(self.root, self.acceptance, self.claim,
                                     self.provider, push=self.push())
        self.assertEqual(result["status"], "created")
        self.assertEqual(self.provider.create_calls, 1)

    def test_unknown_create_without_effect_refuses_without_retry(self):
        self.provider.unknown_create = True
        self.provider.drop_create = True
        with self.assertRaisesRegex(publication.PublicationRefusal, "github.pull.outcome"):
            publication.publish(self.root, self.acceptance, self.claim,
                                self.provider, push=self.push())
        self.assertEqual(self.provider.create_calls, 1)

    def test_failed_push_is_adopted_only_after_exact_readback(self):
        result = publication.publish(self.root, self.acceptance, self.claim,
                                     self.provider, push=self.push(result=1))
        self.assertEqual(result["head"], self.head)

    def test_dirty_or_stale_candidate_refuses_before_provider_read(self):
        (self.root / "dirty.txt").write_text("dirty\n")
        with self.assertRaisesRegex(publication.PublicationRefusal, "git.status"):
            publication.publish(self.root, self.acceptance, self.claim, self.provider)
        self.assertEqual(self.provider.reads, 0)
        (self.root / "dirty.txt").unlink()
        self.acceptance["candidate"]["head"] = "f" * 40
        with self.assertRaisesRegex(publication.PublicationRefusal, "acceptance.candidate"):
            publication.publish(self.root, self.acceptance, self.claim, self.provider)
        self.assertEqual(self.provider.reads, 0)

    def test_drifted_competing_pr_refuses_without_create(self):
        branch = "soodles/issue-128-" + self.head[:12]
        self.provider.ref = self.head
        self.provider.pull_value = exact_pull(41, branch, self.head, "main", "wrong body")
        with self.assertRaisesRegex(publication.PublicationRefusal, "github.pull.shape"):
            publication.publish(self.root, self.acceptance, self.claim, self.provider)
        self.assertEqual(self.provider.create_calls, 0)


def issue_body(base):
    contract = {
        "schema": 3, "trigger": "fixture", "source": "fixture", "owner": "fixture",
        "changes": ["fixture"], "write_paths": ["evidence.json"],
        "behavior": ["fixture"], "defect_controls": ["fixture"], "non_cases": ["fixture"],
        "dependencies": [], "acceptance": "fixture", "delivery": "fixture",
        "reconciliation": "fixture", "feature_scope": "fixture",
        "required_paths": ["evidence.json"], "evidence_manifest": "evidence.json",
        "base_head": base,
        "frozen_paths": [{"path": "evidence.json", "revision": "head", "sha256": "a" * 64}],
    }
    return "<!-- soodles:execution-v1 -->\n```json\n" + json.dumps(contract) + "\n```\n<!-- /soodles:execution-v1 -->"


if __name__ == "__main__":
    unittest.main()
