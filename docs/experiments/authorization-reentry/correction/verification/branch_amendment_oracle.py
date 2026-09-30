"""External process oracle for one corrected head on an existing PR branch."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main(subject):
    subject = Path(subject).resolve()
    with tempfile.TemporaryDirectory(prefix="soodles-amendment-oracle-") as directory:
        root = Path(directory)
        repo = {"full_name": "ed3c/soodles"}
        new_head, tree, base = "a" * 40, "b" * 40, "c" * 40
        prior_branch = "soodles/issue-1-" + "d" * 12

        def invoke(command, claim=None, snapshot=None, name="probe"):
            args = [sys.executable, "-B", str(subject / "soodles.py"), "landing", command]
            if claim is not None:
                claim_path, snapshot_path = root / (name + "-claim.json"), root / (name + "-snapshot.json")
                claim_path.write_text(json.dumps(claim))
                snapshot_path.write_text(json.dumps(snapshot))
                args += [str(claim_path), str(snapshot_path), str(root / (name + "-checkpoint.json"))]
            return subprocess.run(args, cwd=root, text=True, capture_output=True, timeout=20)

        identity = invoke("identity")
        if identity.returncode:
            raise RuntimeError("identity failed: " + identity.stderr)
        digest = json.loads(identity.stdout)["verifier_sha256"]
        claim = {"repository": "ed3c/soodles", "issue": 1, "pr": 2,
                 "head": new_head, "tree": tree, "base_head": base,
                 "run_id": 10, "run_attempt": 1, "worktree": "fixture",
                 "control_root": str(root), "verifier_sha256": digest,
                 "publication_branch": prior_branch}
        snapshot = {
            "pr": {"number": 2, "html_url": "https://github.com/ed3c/soodles/pull/2",
                   "body": "Refs ed3c/soodles#1", "head": {"repo": repo, "sha": new_head, "ref": prior_branch},
                   "base": {"repo": repo, "sha": base, "ref": "main"}, "merged": False,
                   "state": "open", "draft": False, "mergeable": True},
            "issue": {"number": 1, "html_url": "https://github.com/ed3c/soodles/issues/1", "state": "open"},
            "run": {"id": 10, "run_attempt": 1, "repository": repo, "head_repository": repo,
                    "head_sha": new_head, "event": "pull_request", "path": ".github/workflows/runtime.yml",
                    "status": "completed", "conclusion": "success"},
            "commit": {"sha": new_head, "tree": {"sha": tree}},
            "jobs": {"total_count": 1, "jobs": [{"id": 11, "name": "runtime-evidence", "run_id": 10,
                "head_sha": new_head, "status": "completed", "conclusion": "success", "steps": [
                    {"name": "Canonical acceptance on the exact candidate head",
                     "status": "completed", "conclusion": "success"}]}]},
            "branch": {"name": "main", "commit": {"sha": base}}}
        result = invoke("start", claim, snapshot, "same-pr-new-head")
        if result.returncode:
            raise RuntimeError("same PR/new head refused: " + result.stderr)
        cases = ["same_pr_new_head"]

        def rejects(name, change):
            altered_claim, altered_snapshot = copy.deepcopy(claim), copy.deepcopy(snapshot)
            change(altered_claim, altered_snapshot)
            result = invoke("start", altered_claim, altered_snapshot, name)
            if result.returncode == 0 or (root / (name + "-checkpoint.json")).exists():
                raise RuntimeError(name + " was accepted")
            cases.append(name)

        rejects("foreign_pr_branch", lambda c, s: s["pr"]["head"].update(ref="foreign"))
        rejects("stale_pr_head", lambda c, s: s["pr"]["head"].update(sha="d" * 40))
        rejects("stale_runtime_head", lambda c, s: s["run"].update(head_sha="d" * 40))
        rejects("failed_new_runtime", lambda c, s: s["run"].update(conclusion="failure"))
        rejects("foreign_verifier", lambda c, s: c.update(verifier_sha256="0" * 64))
        rejects("malformed_branch", lambda c, s: c.update(publication_branch="soodles/issue-2-" + "d" * 12))
        return {"scope": "external process fixtures; no GitHub writes",
                "subject": str(subject), "verifier_sha256": digest,
                "cases": cases, "authorizes_landing": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(sys.argv[1]), indent=2))
    except Exception as error:
        print(json.dumps({"verdict": "NOT VERIFIED", "reason": str(error),
                          "authorizes_landing": False}))
        sys.exit(1)
