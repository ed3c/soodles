"""Supervised single-Issue landing. The provider adapter never runs in candidate code."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from soodles import Refusal, checked, clean_env, runtime_check, source_identity

REPOSITORY = "ed3c/soodles"
ACTION = "./soodles landing"


def require(condition, field, value):
    if not condition:
        raise Refusal(f"landing: invalid {field}={value!r}; supported help: {ACTION} --help")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verifier_digest():
    # A supervisor selects this implementation outside the candidate under evaluation.
    root = Path(__file__).resolve().parent
    return fingerprint({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                        for name in ("landing.py", "soodles.py", "policy/runtime.lock.json")})


def read(path):
    return json.loads(Path(path).read_text())


@contextlib.contextmanager
def locked(path):
    path = Path(path).resolve()
    require(path.parent.is_dir(), "checkpoint.parent", str(path.parent))
    with open(str(path) + ".lock", "a") as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield path


def save(path, state):
    # Persist intent before returning a provider request. A crash cannot silently re-offer it.
    fd, temporary = tempfile.mkstemp(prefix=".landing-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_claim(claim):
    fields = {"repository", "issue", "pr", "head", "tree", "base_head", "run_id", "run_attempt",
              "worktree", "control_root", "verifier_sha256"}
    require(isinstance(claim, dict) and set(claim) == fields, "claim.fields", list(claim))
    require(claim["repository"] == REPOSITORY, "claim.repository", claim["repository"])
    for key in ("issue", "pr", "run_id", "run_attempt"):
        require(type(claim[key]) is int and claim[key] > 0, "claim." + key, claim[key])
    for key in ("head", "tree", "base_head"):
        require(isinstance(claim[key], str) and re.fullmatch("[0-9a-f]{40}", claim[key]), "claim." + key, claim[key])
    require(claim["verifier_sha256"] == verifier_digest(), "claim.verifier_sha256", claim["verifier_sha256"])
    require(isinstance(claim["worktree"], str) and re.fullmatch("[a-z0-9][a-z0-9-]{0,99}", claim["worktree"]),
            "claim.worktree", claim["worktree"])
    require(isinstance(claim["control_root"], str) and Path(claim["control_root"]).is_absolute(),
            "claim.control_root", claim["control_root"])


def validate_snapshot(claim, snapshot):
    pr, issue, run, jobs, commit = (snapshot[k] for k in ("pr", "issue", "run", "jobs", "commit"))
    for kind, obj, number in (("pr", pr, claim["pr"]), ("issue", issue, claim["issue"])):
        require(obj.get("number") == number, kind + ".number", obj.get("number"))
        suffix = "pull" if kind == "pr" else "issues"
        require(obj.get("html_url") == f"https://github.com/{REPOSITORY}/{suffix}/{number}", kind + ".html_url", obj.get("html_url"))
    refs = re.findall(r"^Refs ([^\n\r]+)\s*$", pr.get("body") or "", re.MULTILINE)
    require(refs == [f"{REPOSITORY}#{claim['issue']}"], "pr.Refs", refs)
    require(not re.search(r"\b(?:closes?|fix(?:es)?|resolves?)\s+(?:\S+#|#)\d+", pr.get("body") or "", re.I), "pr.auto_close", "must use Refs")
    require(pr["head"]["repo"]["full_name"] == REPOSITORY, "pr.head.repository", pr["head"]["repo"]["full_name"])
    require(pr["base"]["repo"]["full_name"] == REPOSITORY and pr["base"]["ref"] == "main", "pr.base", pr["base"])
    require(pr["head"]["sha"] == claim["head"], "pr.head.sha", pr["head"]["sha"])
    require(pr["head"]["ref"] == claim["worktree"], "pr.head.ref", pr["head"]["ref"])
    require(commit.get("sha") == claim["head"] and commit["tree"]["sha"] == claim["tree"], "commit.identity", commit.get("sha"))
    require(run.get("id") == claim["run_id"] and run.get("run_attempt") == claim["run_attempt"], "run.identity", run.get("id"))
    require(run["repository"]["full_name"] == REPOSITORY and run["head_repository"]["full_name"] == REPOSITORY,
            "run.repository", run["repository"]["full_name"])
    require(run.get("head_sha") == claim["head"], "run.head_sha", run.get("head_sha"))
    require(run.get("event") == "pull_request" and run.get("path") == ".github/workflows/runtime.yml", "run.workflow", run.get("path"))
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "run.conclusion", run.get("conclusion"))
    require(jobs.get("total_count") == len(jobs["jobs"]) == 1, "jobs.count", jobs.get("total_count"))
    job = jobs["jobs"][0]
    require(job.get("name") == "runtime-evidence" and job.get("run_id") == claim["run_id"] and job.get("head_sha") == claim["head"], "job.identity", job.get("id"))
    require(job.get("status") == "completed" and job.get("conclusion") == "success", "job.conclusion", job.get("conclusion"))
    steps = job.get("steps") or []
    require(any(s.get("name") == "Canonical acceptance on the exact candidate head" for s in steps), "job.acceptance", steps)
    require(all(s.get("status") == "completed" and s.get("conclusion") == "success" for s in steps), "job.steps", steps)
    require(snapshot["branch"].get("name") == "main", "branch.name", snapshot["branch"].get("name"))
    if not pr.get("merged"):
        require(pr.get("state") == "open" and not pr.get("draft"), "pr.state", {"state": pr.get("state"), "draft": pr.get("draft")})
        require(issue.get("state") == "open", "issue.state", issue.get("state"))
        require(snapshot["branch"]["commit"]["sha"] == claim["base_head"] and pr["base"]["sha"] == claim["base_head"], "base.head", snapshot["branch"]["commit"]["sha"])
    else:
        merge = snapshot["merge_commit"]
        require(pr.get("state") == "closed" and pr.get("merged_at"), "pr.merge_readback", pr.get("state"))
        require(merge.get("sha") == pr.get("merge_commit_sha"), "merge.sha", merge.get("sha"))
        require([p["sha"] for p in merge["parents"]] == [claim["base_head"], claim["head"]], "merge.parents", merge["parents"])
        require(merge["tree"]["sha"] == claim["tree"], "merge.tree", merge["tree"]["sha"])
        require(issue.get("state") == "open" or (issue.get("state") == "closed" and issue.get("state_reason") == "completed" and issue.get("closed_at")), "issue.classification", issue.get("state_reason"))


def start(claim, snapshot, checkpoint):
    validate_claim(claim)
    validate_snapshot(claim, snapshot)
    require(not snapshot["pr"].get("merged"), "pr.merged", True)
    with locked(checkpoint) as path:
        require(not path.exists(), "checkpoint", "already admitted; use landing advance")
        save(path, {"schema": 1, "claim": claim, "phase": "admitted", "observations": [fingerprint(snapshot)],
                    "classification": None, "scope": "supervised single-Issue landing", "writes_offered": []})
    return {"action": "readback", "checkpoint": str(path)}


def advance(checkpoint, snapshot):
    with locked(checkpoint) as path:
        state = read(path)
        require(state.get("schema") == 1, "checkpoint.schema", state.get("schema"))
        claim = state["claim"]
        validate_claim(claim)
        validate_snapshot(claim, snapshot)
        phase = state["phase"]
        require(phase in {"admitted", "merge_pending", "close_pending", "awaiting_reconcile", "reconciling", "resolved"}, "checkpoint.phase", phase)
        observation = fingerprint(snapshot)
        if observation not in state["observations"]:
            state["observations"].append(observation)
            state["observations"] = state["observations"][-8:]
        request = None
        if snapshot["pr"].get("merged"):
            require(phase != "admitted", "merge.owner", "no merge request offered by this checkpoint")
            state["merge_sha"] = snapshot["pr"]["merge_commit_sha"]
            if snapshot["issue"]["state"] == "closed":
                require("close" in state["writes_offered"], "closure.owner", "no close request offered by this checkpoint")
                state["issue_closed_at"] = snapshot["issue"]["closed_at"]
                if phase not in {"reconciling", "resolved"}:
                    state["phase"] = "awaiting_reconcile"
            elif phase == "merge_pending":
                state["phase"] = "close_pending"
                state["writes_offered"].append("close")
                request = {"action": "close", "repository_full_name": REPOSITORY, "issue_number": claim["issue"],
                           "state": "closed", "state_reason": "completed"}
        elif phase == "admitted":
            require(snapshot["pr"].get("mergeable") is True, "pr.mergeable", snapshot["pr"].get("mergeable"))
            state["phase"] = "merge_pending"
            state["writes_offered"].append("merge")
            request = {"action": "merge", "repository_full_name": REPOSITORY, "pr_number": claim["pr"],
                       "expected_head_sha": claim["head"], "merge_method": "merge"}
        save(path, state)
        return request or {"action": "reconcile" if state["phase"] == "awaiting_reconcile" else "readback",
                           "phase": state["phase"], "classification": state["classification"],
                           "reason": "Pending writes require owner readback; no retry is offered."}


def resume(checkpoint, claim):
    """Re-admit a corrected verifier only after provider writes are complete."""
    validate_claim(claim)
    with locked(checkpoint) as path:
        state = read(path)
        require(state.get("schema") == 1, "checkpoint.schema", state.get("schema"))
        require(state["phase"] == "reconciling" and state.get("merge_sha") and state.get("issue_closed_at")
                and state["writes_offered"] == ["merge", "close"], "resume.phase", state["phase"])
        old = state["claim"]
        require({k: v for k, v in old.items() if k != "verifier_sha256"} ==
                {k: v for k, v in claim.items() if k != "verifier_sha256"}, "resume.claim", "identity changes are forbidden")
        require(old["verifier_sha256"] != claim["verifier_sha256"], "resume.verifier", "unchanged")
        state.setdefault("prior_verifiers", []).append(old["verifier_sha256"])
        state["claim"] = claim
        save(path, state)
        return {"action": "reconcile", "phase": "reconciling", "provider_requests": []}


def fetch_main(root):
    # Network Git needs the carrier's proxy route, unlike isolated runtime fixtures.
    env = clean_env()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        if key in os.environ:
            env[key] = os.environ[key]
    result = subprocess.run(["git", "fetch", "origin", "main"], cwd=root, env=env, stdin=subprocess.DEVNULL,
                            text=True, capture_output=True, timeout=45)
    require(result.returncode == 0, "git.fetch.exit", result.returncode)


def reconcile(checkpoint, binary):
    with locked(checkpoint) as path:
        state = read(path)
        require(state.get("schema") == 1, "checkpoint.schema", state.get("schema"))
        claim = state["claim"]
        validate_claim(claim)
        require(state["phase"] in {"awaiting_reconcile", "reconciling", "resolved"}, "checkpoint.phase", state["phase"])
        root = Path(claim["control_root"]).resolve()
        require(not path.is_relative_to(root), "checkpoint.path", "must be outside source/worktree lifecycle")
        require(checked(["git", "remote", "get-url", "origin"], root) == f"https://github.com/{REPOSITORY}.git", "origin", "unexpected; no automatic correction")
        require(checked(["git", "branch", "--show-current"], root) == "main", "local.branch", "expected main")
        before = source_identity(root)
        runtime = runtime_check(Path(__file__).resolve().parent, binary)
        worktree = root / ".worktrees" / claim["worktree"]
        branch = checked(["git", "branch", "--list", claim["worktree"]], root)
        branch_head = checked(["git", "rev-parse", "refs/heads/" + claim["worktree"]], root) if branch else None
        if worktree.exists():
            require(source_identity(worktree) == {"head": claim["head"], "tree": claim["tree"]}, "worktree.identity", str(worktree))
        else:
            require(state["phase"] in {"reconciling", "resolved"}, "worktree.path", "missing before cleanup intent")
            if branch:
                require(state["phase"] == "reconciling", "cleanup.phase", state["phase"])
                require(branch_head == claim["head"], "cleanup.branch_head", branch_head)
                entries = checked(["git", "worktree", "list", "--porcelain"], root).split("\n\n")
                for entry in entries:
                    lines = entry.splitlines()
                    if "branch refs/heads/" + claim["worktree"] in lines:
                        registered = next((line[9:] for line in lines if line.startswith("worktree ")), None)
                        require(registered == str(worktree), "cleanup.checkout", registered)
        state["phase"] = "reconciling"
        save(path, state)
        fetch_main(root)
        checked(["git", "merge-base", "--is-ancestor", state["merge_sha"], "origin/main"], root)
        checked(["git", "merge-base", "--is-ancestor", before["head"], "origin/main"], root)
        checked(["git", "merge", "--ff-only", "origin/main"], root)
        if worktree.exists() or branch:
            git_path = shutil.which("git")
            require(git_path is not None, "cleanup.git", "not found")
            observation = {"path_present": worktree.exists(), "branch_head": branch_head,
                           "main_head": checked(["git", "rev-parse", "HEAD"], root),
                           "git_path": str(Path(git_path).resolve()),
                           "git_sha256": hashlib.sha256(Path(git_path).read_bytes()).hexdigest(),
                           "noodle_sha256": runtime["observed_binary_sha256"],
                           "verifier_sha256": claim["verifier_sha256"]}
            # Git owns ref path resolution, including a shared common directory.
            ref_lock = checked(["git", "rev-parse", "--path-format=absolute", "--git-path",
                                "refs/heads/" + claim["worktree"] + ".lock"], root)
            blocked = {"observation": observation, "ref_lock": ref_lock}
            if os.path.lexists(ref_lock):
                # This is a capability readback, not another cleanup attempt. Never remove the lock.
                if state.get("cleanup_blocked") != blocked:
                    state["cleanup_blocked"] = blocked
                    save(path, state)
                require(False, "cleanup.ref_lock", ref_lock)
            released = state.get("cleanup_blocked") == blocked
            # Missing legacy lock evidence means unknown, not a present->absent transition.
            require(state.get("cleanup_intent") != observation or released,
                    "cleanup.observation", "unchanged; owner readback or changed capability required")
            state.pop("cleanup_blocked", None)  # Consume the observed release before calling its owner.
            state["cleanup_intent"] = observation
            save(path, state)
            checked([str(Path(binary).resolve()), "worktree", "cleanup", claim["worktree"]], root)
        require(not worktree.exists(), "cleanup.path", str(worktree))
        require(not checked(["git", "branch", "--list", claim["worktree"]], root), "cleanup.branch", claim["worktree"])
        require(str(worktree) not in checked(["git", "worktree", "list", "--porcelain"], root), "cleanup.registration", str(worktree))
        state["local"] = {**source_identity(root), "removed_worktree": claim["worktree"], "worktree_owner": "Noodle"}
        state["phase"], state["classification"] = "resolved", "RESOLVED"
        save(path, state)
        return state
