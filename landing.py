"""Supervised single-Issue landing. The provider adapter never runs in candidate code."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import sys
import subprocess
import tempfile

from soodles import Refusal, checked, clean_env, runtime_check, source_identity
from repository_binding import PROFILES, git_origins, profile
from dependency_binding import (dependencies as claim_dependencies,
                                requests as dependency_requests,
                                validate as validate_dependency)

ACTION = "./soodles landing"
COMMON_CLAIM_FIELDS = {"repository", "issue", "pr", "head", "tree", "base_head", "run_id",
                       "run_attempt", "worktree", "verifier_sha256"}
DEPENDENCY_CLAIM_FIELDS = COMMON_CLAIM_FIELDS | {"dependencies"}


class LandingRefusal(Refusal):
    def __init__(self, field, value, next_action=None):
        self.invalid = {"field": field, "value": value}
        self.next_action = next_action
        super().__init__(f"landing: invalid {field}={value!r}")


def require(condition, field, value, next_action=None):
    if not condition:
        raise LandingRefusal(field, value, next_action)


def cli_argv(operation, *arguments):
    return [sys.executable, "-B", str(Path(__file__).resolve().parent / "soodles.py"),
            "landing", *([operation] if operation else []), *map(str, arguments)]


def provider_cli_argv(checkpoint):
    return [sys.executable, "-B", str(Path(__file__).resolve().parent / "provider-execute"),
            str(Path(checkpoint).resolve())]


def input_next(operation, required, checkpoint=None):
    return {"kind": "input", "owner": "supervisor", "operation": operation, "required": required,
            "known": {"checkpoint": str(Path(checkpoint).resolve())} if checkpoint else {},
            "help_argv": cli_argv(operation, "--help")}


def provider_next(claim, operation, checkpoint):
    base = "https://api.github.com/repos/" + claim["repository"] + "/"
    base_ref = profile(claim["repository"])["base_ref"]
    paths = {"pr": f"pulls/{claim['pr']}", "issue": f"issues/{claim['issue']}",
             "commit": f"git/commits/{claim['head']}", "branch": "branches/" + base_ref,
             "run": f"actions/runs/{claim['run_id']}", "jobs": f"actions/runs/{claim['run_id']}/jobs"}
    requests = {key: {"method": "GET", "url": base + path} for key, path in paths.items()}
    requests.update(dependency_requests(claim, require))
    return {**input_next(operation, ["readback"], checkpoint), "kind": "provider_readback", "owner": "GitHub",
            "requests": requests,
            "merge_commit": "If pr.merged, GET git/commits/{pr.merge_commit_sha} in this repository."}


def delivery_request(claim, action):
    if action == "merge":
        return {"action": "merge", "repository_full_name": claim["repository"],
                "pr_number": claim["pr"], "expected_head_sha": claim["head"],
                "merge_method": "merge"}
    if action == "close":
        return {"action": "close", "repository_full_name": claim["repository"],
                "issue_number": claim["issue"], "state": "closed",
                "state_reason": "completed"}
    raise LandingRefusal("delivery.action", action)


def response(operation, state, action, next_action, **details):
    return {"owner": "landing." + operation, "action": action, "phase": state["phase"],
            "classification": state.get("classification"), "next": next_action, **details}


def refusal_output(error, operation):
    # The invoked action supplies ownership; field spelling never selects a route.
    next_action = error.next_action or input_next(operation, ["corrected_input"])
    return {"owner": "landing." + operation if operation else "landing", "status": "refused",
            "invalid": error.invalid, "next": next_action}


def refusal_text(result):
    invalid = result["invalid"]
    help_argv = result["next"]["help_argv"]
    return (f"REFUSED: {result['owner']}: invalid {invalid['field']}={invalid['value']!r}; "
            f"supported help: {shlex.join(help_argv)}"
            + ("; " + result["next"]["reason"] if result["next"].get("reason") else ""))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verifier_digest():
    # A supervisor selects this implementation outside the candidate under evaluation.
    root = Path(__file__).resolve().parent
    return fingerprint({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                        for name in ("landing.py", "provider_transport.py", "soodles.py",
                                     "issue_admission.py", "repository_binding.py",
                                     "dependency_binding.py", "issue_execution.py",
                                     "policy/runtime.lock.json")})


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


def validate_claim(claim, *, verify_verifier=True):
    local_fields = COMMON_CLAIM_FIELDS | {"control_root"}
    dependency_local_fields = DEPENDENCY_CLAIM_FIELDS | {"control_root"}
    require(isinstance(claim, dict) and set(claim) in
            (COMMON_CLAIM_FIELDS, DEPENDENCY_CLAIM_FIELDS,
             local_fields, dependency_local_fields,
             local_fields | {"execution_envelope"},
             dependency_local_fields | {"execution_envelope"}),
            "claim.fields", list(claim))
    if "execution_envelope" in claim:
        ref = claim["execution_envelope"]
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "claim.execution_envelope", ref)
        require(isinstance(ref["path"], str) and Path(ref["path"]).is_absolute(), "claim.envelope.path", ref["path"])
        require(isinstance(ref["sha256"], str) and re.fullmatch("[0-9a-f]{64}", ref["sha256"]),
                "claim.envelope.sha256", ref["sha256"])
    require(profile(claim["repository"]) is not None, "claim.repository", claim["repository"])
    for key in ("issue", "pr", "run_id", "run_attempt"):
        require(type(claim[key]) is int and claim[key] > 0, "claim." + key, claim[key])
    for key in ("head", "tree", "base_head"):
        require(isinstance(claim[key], str) and re.fullmatch("[0-9a-f]{40}", claim[key]), "claim." + key, claim[key])
    if verify_verifier:
        require(claim["verifier_sha256"] == verifier_digest(), "claim.verifier_sha256", claim["verifier_sha256"])
    require(isinstance(claim["worktree"], str) and re.fullmatch("[a-z0-9][a-z0-9-]{0,99}", claim["worktree"]),
            "claim.worktree", claim["worktree"])
    if "control_root" in claim:
        require(isinstance(claim["control_root"], str) and Path(claim["control_root"]).is_absolute(),
                "claim.control_root", claim["control_root"])
    claim_dependencies(claim, require)


def claim_route(claim):
    return "local" if "control_root" in claim else "cloud"


def validate_merge_commit(claim, snapshot, *, operation, checkpoint):
    """Project dependent readback only from an identity-checked PR and valid SHA."""
    sha = snapshot["pr"].get("merge_commit_sha")
    next_action = provider_next(claim, operation, checkpoint)
    if operation in {"start", "readmit"}:
        next_action["known"]["claim"] = claim
    next_action["reason"] = (f"Supply fresh readback.pr from GET {next_action['requests']['pr']['url']}; "
                             "its merge_commit_sha must be a complete commit SHA before requesting that commit.")
    require(isinstance(sha, str) and re.fullmatch("[0-9a-f]{40}", sha),
            "pr.merge_commit_sha", sha, next_action)
    url = f"https://api.github.com/repos/{claim['repository']}/git/commits/{sha}"
    next_action["requests"]["merge_commit"] = {"method": "GET", "url": url}
    next_action["reason"] = (f"Supply readback.merge_commit from GET {url}; re-enter {operation} "
                             "with fresh provider readback. Retry only after the readback materially changes.")
    try:
        merge = snapshot.get("merge_commit")
        require(isinstance(merge, dict), "merge_commit", merge)
        require(merge.get("sha") == sha, "merge.sha", merge.get("sha"))
        parents = merge.get("parents")
        require(isinstance(parents, list) and all(isinstance(p, dict) for p in parents),
                "merge.parents", parents)
        require([p.get("sha") for p in parents] == [claim["base_head"], claim["head"]], "merge.parents", parents)
        tree = merge.get("tree")
        require(isinstance(tree, dict), "merge.tree", tree)
        require(tree.get("sha") == claim["tree"], "merge.tree", tree.get("sha"))
    except LandingRefusal as error:
        error.next_action = next_action
        raise


def validate_provider_main(claim, snapshot, *, operation, checkpoint):
    """Require the admitted merge on provider main without using shell Git."""
    merge_sha = snapshot["pr"]["merge_commit_sha"]
    main_sha = snapshot["branch"]["commit"]["sha"]
    if main_sha != merge_sha:
        validate_comparison(snapshot, "main_comparison", merge_sha, main_sha,
                            claim=claim, checkpoint=checkpoint, operation=operation)
    return main_sha


def execution_binding(claim, issue=None, *, operation="start", checkpoint=None):
    """The supervisor's claim selects external bytes; no candidate self-admission."""
    from issue_admission import AdmissionRefusal, load_external_envelope, validate_issue, validate_delivery_paths
    ref = claim.get("execution_envelope")
    if claim_route(claim) == "cloud":
        # Cloud claims are bound by the exact-head candidate-evidence workflow
        # step checked in validate_snapshot; they cannot carry a local envelope.
        require(ref is None, "claim.execution_envelope", "cloud execution cannot bind a local envelope")
        return None
    if ref is None:
        require(issue is None or "soodles:execution-v1" not in (issue.get("body") or ""),
                "claim.execution_envelope", "required for an execution contract")
        return None
    root = Path(claim["control_root"]).resolve()
    subject = root / ".worktrees" / claim["worktree"]
    try:
        envelope = load_external_envelope(ref["path"], ref["sha256"], root)
        require(envelope["repository"] == claim["repository"],
                "claim.envelope.repository", envelope["repository"])
        require(envelope["issue"] == claim["issue"], "claim.envelope.issue", envelope["issue"])
        for key in ("control_root", "worktree"):
            require(envelope["execution"][key] == claim[key], "claim.envelope." + key, envelope["execution"][key])
        if issue is not None:
            validate_issue(issue, envelope, completed=issue.get("state") == "closed")
        validate_delivery_paths(subject if subject.exists() else root, claim["base_head"], claim["head"], envelope)
        return envelope
    except AdmissionRefusal as error:
        raise LandingRefusal(error.invalid["field"], error.invalid["value"],
                             {**input_next(operation, error.next["required"], checkpoint), **error.next,
                              "reason": "Preserve the original claim/checkpoint. Supervisor corrections use "
                                        "invalidate/readmit only for unoffered work; unknown offered writes "
                                        "remain readback-only. This refusal does not renew authority."}) from error


def reconcile_next(claim, checkpoint):
    envelope = execution_binding(claim, operation="reconcile", checkpoint=checkpoint)
    if envelope is None:
        return input_next("reconcile", ["binary"], checkpoint)
    from issue_execution import validate_carrier
    try:
        identity = validate_carrier(envelope)
    except Refusal as error:
        raise LandingRefusal("reconcile.carrier", str(error)) from error
    binary = identity["noodle"]
    return {"kind": "executable", "owner": "landing.reconcile",
            "operation": "reconcile",
            "known": {"checkpoint": str(Path(checkpoint).resolve()), "binary": binary},
            "argv": cli_argv("reconcile", checkpoint, binary)}


def validate_snapshot(claim, snapshot, *, operation, checkpoint):
    repository = claim["repository"]
    acceptance = profile(repository)
    base_ref = acceptance["base_ref"]
    dependency_next = provider_next(claim, operation, checkpoint)
    dependency_next["reason"] = ("Supply every registered producer GET in next.requests, then re-enter "
                                 f"{operation} with the changed readback. Issue closure alone is insufficient.")
    validate_dependency(claim, snapshot, require, dependency_next)
    pr, issue, run, jobs, commit = (snapshot[k] for k in ("pr", "issue", "run", "jobs", "commit"))
    for kind, obj, number in (("pr", pr, claim["pr"]), ("issue", issue, claim["issue"])):
        require(obj.get("number") == number, kind + ".number", obj.get("number"))
        suffix = "pull" if kind == "pr" else "issues"
        require(obj.get("html_url") == f"https://github.com/{repository}/{suffix}/{number}", kind + ".html_url", obj.get("html_url"))
    refs = re.findall(r"^Refs ([^\n\r]+)\s*$", pr.get("body") or "", re.MULTILINE)
    require(refs == [f"{repository}#{claim['issue']}"], "pr.Refs", refs)
    require(not re.search(r"\b(?:closes?|fix(?:es)?|resolves?)\s+(?:\S+#|#)\d+", pr.get("body") or "", re.I), "pr.auto_close", "must use Refs")
    require(pr["head"]["repo"]["full_name"] == repository, "pr.head.repository", pr["head"]["repo"]["full_name"])
    require(pr["base"]["repo"]["full_name"] == repository and pr["base"]["ref"] == base_ref, "pr.base", pr["base"])
    require(pr["head"]["sha"] == claim["head"], "pr.head.sha", pr["head"]["sha"])
    require(pr["head"]["ref"] == claim["worktree"], "pr.head.ref", pr["head"]["ref"])
    require(commit.get("sha") == claim["head"] and commit["tree"]["sha"] == claim["tree"], "commit.identity", commit.get("sha"))
    require(run.get("id") == claim["run_id"] and run.get("run_attempt") == claim["run_attempt"], "run.identity", run.get("id"))
    require(run["repository"]["full_name"] == repository and run["head_repository"]["full_name"] == repository,
            "run.repository", run["repository"]["full_name"])
    require(run.get("head_sha") == claim["head"], "run.head_sha", run.get("head_sha"))
    require(run.get("event") == "pull_request" and run.get("path") == acceptance["workflow_path"], "run.workflow", run.get("path"))
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "run.conclusion", run.get("conclusion"))
    expected_jobs = acceptance["jobs"]
    require(jobs.get("total_count") == len(jobs.get("jobs", [])) == len(expected_jobs), "jobs.count", jobs.get("total_count"))
    observed_jobs = {job.get("name"): job for job in jobs["jobs"]}
    require(set(observed_jobs) == set(expected_jobs), "jobs.names", sorted(observed_jobs))
    for name, required_steps in expected_jobs.items():
        job = observed_jobs[name]
        require(job.get("run_id") == claim["run_id"] and job.get("head_sha") == claim["head"], "job.identity", job.get("id"))
        require(job.get("status") == "completed" and job.get("conclusion") == "success", "job.conclusion", job.get("conclusion"))
        steps = job.get("steps") or []
        names = {s.get("name") for s in steps}
        require(all(step in names for step in required_steps), "job.acceptance", {"job": name, "steps": sorted(names)})
        require(all(s.get("status") == "completed" and s.get("conclusion") == "success" for s in steps), "job.steps", steps)
    if (claim_route(claim) == "cloud"
            and "soodles:execution-v1" in (issue.get("body") or "")):
        require(any(s.get("name") == "Verify exact candidate evidence from fresh Issue readback"
                    for job in observed_jobs.values() for s in (job.get("steps") or [])), "job.candidate_evidence", observed_jobs)
    require(snapshot["branch"].get("name") == base_ref, "branch.name", snapshot["branch"].get("name"))
    if not pr.get("merged"):
        require(pr.get("state") == "open" and not pr.get("draft"), "pr.state", {"state": pr.get("state"), "draft": pr.get("draft")})
        require(issue.get("state") == "open", "issue.state", issue.get("state"))
        require(snapshot["branch"]["commit"]["sha"] == claim["base_head"] and pr["base"]["sha"] == claim["base_head"], "base.head", snapshot["branch"]["commit"]["sha"])
    else:
        require(pr.get("state") == "closed" and pr.get("merged_at"), "pr.merge_readback", pr.get("state"))
        validate_merge_commit(claim, snapshot, operation=operation, checkpoint=checkpoint)
        require(issue.get("state") == "open" or (issue.get("state") == "closed" and issue.get("state_reason") == "completed" and issue.get("closed_at")), "issue.classification", issue.get("state_reason"))
    execution_binding(claim, issue, operation=operation, checkpoint=checkpoint)


def start(claim, snapshot, checkpoint):
    validate_claim(claim)
    validate_snapshot(claim, snapshot, operation="start", checkpoint=checkpoint)
    require(not snapshot["pr"].get("merged"), "pr.merged", True)
    with locked(checkpoint) as path:
        require(not path.exists(), "checkpoint", "already admitted")
        state = {"schema": 2, "claim": claim, "phase": "admitted", "observations": [fingerprint(snapshot)],
                 "classification": None, "scope": f"supervised single-Issue {claim_route(claim)} landing",
                 "writes_offered": []}
        save(path, state)
        return response("start", state, "readback", provider_next(claim, "advance", path), checkpoint=str(path))


def delivery_state(path):
    state = read(path)
    require(state.get("schema") in (1, 2), "checkpoint.schema", state.get("schema"))
    phase = state["phase"]
    require(phase in {"admitted", "readmission_pending", "merge_pending", "close_pending", "awaiting_reconcile", "reconciling", "resolved"},
            "checkpoint.phase", phase)
    if phase in {"admitted", "readmission_pending"}:
        require(state.get("writes_offered") == [], "checkpoint.writes_offered", state.get("writes_offered"))
    if phase == "readmission_pending":
        recovery = state.get("recovery")
        require(isinstance(recovery, dict) and recovery.get("previous_base") == state["claim"]["base_head"],
                "checkpoint.recovery", recovery)
        if recovery.get("kind") == "amendment":
            require(recovery.get("base_head") == state["claim"]["base_head"]
                    and recovery.get("previous_head") == state["claim"]["head"], "checkpoint.recovery", recovery)
        else:
            require("kind" not in recovery and recovery.get("base_head") != state["claim"]["base_head"]
                    and recovery.get("readback_sha256"), "checkpoint.recovery", recovery)
    if phase in {"merge_pending", "close_pending"}:
        action = phase.removesuffix("_pending")
        if state["schema"] == 1:
            # Old advance could already have emitted the request. Absence is never proof of non-delivery.
            state["delivery"] = {"action": action, "status": "offered"}
        delivery = state.get("delivery")
        require(isinstance(delivery, dict) and set(delivery) == {"action", "status"}
                and delivery["action"] == action and delivery["status"] in {"prepared", "offered"},
                "checkpoint.delivery", delivery)
        expected = [] if action == "merge" else ["merge"]
        if delivery["status"] == "offered":
            expected = [*expected, action]
        require(state["writes_offered"] == expected, "checkpoint.writes_offered", state["writes_offered"])
    state["schema"] = 2
    return state


def validate_comparison(snapshot, field, base, head, *, claim, checkpoint, operation):
    """Validate ancestry; only confirmed endpoints can produce readback guidance."""
    for name, value in (("base", base), ("head", head)):
        require(isinstance(value, str) and re.fullmatch("[0-9a-f]{40}", value),
                field + ".request." + name, value)
    url = f"https://api.github.com/repos/{claim['repository']}/compare/{base}...{head}"
    next_action = provider_next(claim, operation, checkpoint)
    next_action["requests"][field] = {"method": "GET", "url": url}
    if operation == "readmit":
        next_action["known"]["claim"] = claim
    next_action["reason"] = (f"Supply readback.{field} from GET {url}; re-enter {operation} "
                             "with fresh provider readback. Retry only after the readback materially changes.")
    try:
        comparison = snapshot.get(field)
        require(isinstance(comparison, dict), field, comparison)
        for key in ("base_commit", "merge_base_commit"):
            commit = comparison.get(key)
            require(isinstance(commit, dict), field + "." + key, commit)
            require(commit.get("sha") == base, field + "." + key + ".sha", commit.get("sha"))
        require(comparison.get("status") == "ahead", field + ".status", comparison.get("status"))
        commits, total = comparison.get("commits"), comparison.get("total_commits")
        require(isinstance(commits, list) and len(commits) > 0, field + ".commits", commits)
        require(type(total) is int and total == len(commits), field + ".total_commits", total)
        require(isinstance(commits[-1], dict), field + ".commits[-1]", commits[-1])
        require(commits[-1].get("sha") == head, field + ".commits[-1].sha", commits[-1].get("sha"))
    except LandingRefusal as error:
        error.next_action = next_action
        raise


def recovery_action(state, base, checkpoint, operation):
    unknown = bool(state["writes_offered"])
    next_action = provider_next(state["claim"], "advance", checkpoint) if unknown else input_next("readmit", ["claim", "readback"], checkpoint)
    details = {} if state.get("recovery", {}).get("kind") == "amendment" else {
        "invalid": {"field": "base.head", "value": base, "expected": state["claim"]["base_head"]}}
    return response(operation, state, "readback" if unknown else "readmit", next_action,
                    provider_requests=[], reason="Offered write requires owner readback." if unknown else
                    "Prior acceptance is invalidated; supply a fresh supervisor claim and exact-head evidence.", **details)


def observe_base(path, state, snapshot, operation):
    """Checkpoint coherent pre-offer base advancement; never infer non-delivery."""
    claim = state["claim"]
    if snapshot["pr"].get("merged"):
        return None
    base = snapshot["branch"]["commit"]["sha"]
    if base == claim["base_head"] and snapshot["pr"]["base"]["sha"] == base:
        return None
    require(base == snapshot["pr"]["base"]["sha"], "base.head", base)
    # All original subject/run/target checks still apply. Only base is separately proved.
    validate_snapshot({**claim, "base_head": base}, snapshot, operation=operation, checkpoint=path)
    validate_comparison(snapshot, "base_comparison", claim["base_head"], base,
                        claim=claim, checkpoint=path, operation=operation)
    if state["writes_offered"]:
        return recovery_action(state, base, path, operation)
    require(state["phase"] in {"admitted", "merge_pending", "readmission_pending"}, "recovery.phase", state["phase"])
    recovery = {"previous_base": claim["base_head"], "base_head": base, "readback_sha256": fingerprint(snapshot)}
    if state.get("recovery") != recovery:
        if state["phase"] == "readmission_pending" and state["recovery"]["base_head"] != base:
            validate_comparison(snapshot, "recovery_comparison", state["recovery"]["base_head"], base,
                                claim=claim, checkpoint=path, operation=operation)
        state["phase"] = "readmission_pending"
        state["recovery"] = recovery
        save(path, state)
    return recovery_action(state, base, path, operation)


def invalidate(checkpoint):
    """Withdraw only a known-unoffered acceptance; never guess a provider outcome."""
    with locked(checkpoint) as path:
        state = delivery_state(path)
        validate_claim(state["claim"])
        if state["writes_offered"] or state["phase"] not in {"admitted", "merge_pending", "readmission_pending"}:
            raise LandingRefusal("checkpoint.phase", state["phase"], provider_next(state["claim"], "advance", path))
        if state["phase"] != "readmission_pending":
            claim = state["claim"]
            state["phase"] = "readmission_pending"
            state["recovery"] = {"kind": "amendment", "previous_head": claim["head"],
                                 "previous_base": claim["base_head"], "base_head": claim["base_head"]}
            save(path, state)
        return recovery_action(state, state["recovery"]["base_head"], path, "invalidate")


def readmit(checkpoint, claim, snapshot):
    """Replace only an invalidated, unoffered admission under the same supervisor."""
    validate_claim(claim)
    with locked(checkpoint) as path:
        state = delivery_state(path)
        old = state["claim"]
        validate_claim(old)
        require(state["phase"] == "readmission_pending", "readmit.phase",
                state["phase"], provider_next(old, "advance", path))
        require(state["writes_offered"] == [], "readmit.writes_offered", state["writes_offered"])
        require(claim_route(claim) == claim_route(old), "readmit.route", claim_route(claim))
        for field in ("repository", "issue", "pr", "worktree", "verifier_sha256"):
            require(claim[field] == old[field], "readmit." + field, claim[field])
        if claim_route(claim) == "local":
            require(claim["control_root"] == old["control_root"], "readmit.control_root", claim["control_root"])
        require(("execution_envelope" in claim) == ("execution_envelope" in old),
                "readmit.execution_envelope", "binding cannot be added or removed during readmission")
        amendment = state["recovery"].get("kind") == "amendment"
        fields = ("head", "run_id") if amendment else ("head", "base_head", "run_id")
        for field in fields:
            require(claim[field] != old[field], "readmit." + field, "unchanged " + str(claim[field]))
        validate_snapshot(claim, snapshot, operation="readmit", checkpoint=path)
        require(not snapshot["pr"].get("merged"), "readmit.pr.merged", True)
        if claim["base_head"] != old["base_head"]:
            validate_comparison(snapshot, "base_comparison", old["base_head"], claim["base_head"],
                                claim=claim, checkpoint=path, operation="readmit")
        if not amendment and state["recovery"]["base_head"] != claim["base_head"]:
            validate_comparison(snapshot, "recovery_comparison", state["recovery"]["base_head"], claim["base_head"],
                                claim=claim, checkpoint=path, operation="readmit")
        validate_comparison(snapshot, "candidate_comparison", claim["base_head"], claim["head"],
                            claim=claim, checkpoint=path, operation="readmit")
        state.setdefault("prior_admissions", []).append({
            "claim": old, "classification": "SUPERSEDED", "recovery": state.pop("recovery"),
            "delivery": state.pop("delivery", None), "writes_offered": [], "observations": state["observations"]})
        state.update(claim=claim, phase="admitted", observations=[fingerprint(snapshot)], classification=None)
        save(path, state)
        return response("readmit", state, "readback", provider_next(claim, "advance", path), provider_requests=[])


def advance(checkpoint, snapshot):
    with locked(checkpoint) as path:
        state = delivery_state(path)
        claim = state["claim"]
        validate_claim(claim)
        if state["phase"] == "readmission_pending" and state["recovery"].get("kind") == "amendment":
            return recovery_action(state, state["recovery"]["base_head"], path, "advance")
        recovery = observe_base(path, state, snapshot, "advance")
        if recovery:
            return recovery
        validate_snapshot(claim, snapshot, operation="advance", checkpoint=path)
        if state["phase"] == "readmission_pending":
            return recovery_action(state, state["recovery"]["base_head"], path, "advance")
        phase = state["phase"]
        if phase == "resolved":
            return response("advance", state, "stop", None)
        observation = fingerprint(snapshot)
        if observation not in state["observations"]:
            state["observations"].append(observation)
            state["observations"] = state["observations"][-8:]
        if snapshot["pr"].get("merged"):
            require("merge" in state["writes_offered"], "merge.owner", "no merge request offered by this checkpoint")
            state["merge_sha"] = snapshot["pr"]["merge_commit_sha"]
            if snapshot["issue"]["state"] == "closed":
                require("close" in state["writes_offered"], "closure.owner", "no close request offered by this checkpoint")
                state["issue_closed_at"] = snapshot["issue"]["closed_at"]
                if claim_route(claim) == "cloud":
                    main_sha = validate_provider_main(claim, snapshot, operation="advance", checkpoint=path)
                    state["provider_reconciliation"] = {
                        "mode": "cloud", "main_head": main_sha, "merge_sha": state["merge_sha"],
                        "provider": "GitHub", "local_reconciliation_required": False}
                    state["phase"], state["classification"] = "resolved", "RESOLVED"
                elif phase not in {"reconciling", "resolved"}:
                    state["phase"] = "awaiting_reconcile"
            elif phase == "merge_pending":
                state["phase"] = "close_pending"
                state["delivery"] = {"action": "close", "status": "prepared"}
        elif phase == "admitted":
            require(snapshot["pr"].get("mergeable") is True, "pr.mergeable", snapshot["pr"].get("mergeable"))
            state["phase"] = "merge_pending"
            state["delivery"] = {"action": "merge", "status": "prepared"}
        save(path, state)
        if state["phase"] == "resolved":
            return {**state, **response("advance", state, "stop", None)}
        prepared = state["phase"] in {"merge_pending", "close_pending"} and state["delivery"]["status"] == "prepared"
        if prepared:
            return response("advance", state, "dispatch", provider_next(claim, "dispatch", path))
        if state["phase"] in {"awaiting_reconcile", "reconciling"}:
            return response("advance", state, "reconcile", reconcile_next(claim, path))
        return response("advance", state, "readback", provider_next(claim, "advance", path))


def dispatch(checkpoint, snapshot):
    """Consume one prepared intent for the supervisor's existing connector transport."""
    with locked(checkpoint) as path:
        state = delivery_state(path)
        claim = state["claim"]
        validate_claim(claim)
        require(state["phase"] != "readmission_pending", "dispatch.phase",
                state["phase"], input_next("readmit", ["claim", "readback"], path))
        recovery = observe_base(path, state, snapshot, "dispatch")
        if recovery:
            return recovery
        validate_snapshot(claim, snapshot, operation="dispatch", checkpoint=path)
        require(state["phase"] in {"merge_pending", "close_pending"}, "dispatch.phase", state["phase"])
        delivery = state["delivery"]
        require(delivery["status"] == "prepared", "dispatch.status",
                delivery["status"], provider_next(claim, "advance", path))
        if delivery["action"] == "merge":
            require(not snapshot["pr"].get("merged") and snapshot["pr"].get("mergeable") is True,
                    "dispatch.pr", "merge no longer eligible", provider_next(claim, "advance", path))
        else:
            require(snapshot["pr"].get("merged") and snapshot["issue"]["state"] == "open",
                    "dispatch.issue", "closure no longer eligible", provider_next(claim, "advance", path))
        request = delivery_request(claim, delivery["action"])
        delivery["request"] = request
        delivery["status"] = "offered"
        state["writes_offered"].append(delivery["action"])
        save(path, state)  # Must precede request emission; an interrupted offer remains unknown.
        next_action = provider_next(claim, "advance", path)
        if claim_route(claim) == "local":
            next_action = {"kind": "executable", "owner": "local-provider",
                           "operation": "execute",
                           "known": {"checkpoint": str(path)},
                           "argv": provider_cli_argv(path)}
        return response("dispatch", state, request["action"], next_action, request=request)


def resume(checkpoint, claim):
    """Re-admit a corrected verifier/route only after provider writes are complete."""
    validate_claim(claim)
    with locked(checkpoint) as path:
        state = read(path)
        require(state.get("schema") in (1, 2), "checkpoint.schema", state.get("schema"))
        require(state["phase"] in {"awaiting_reconcile", "reconciling"}
                and state.get("merge_sha") and state.get("issue_closed_at")
                and state["writes_offered"] == ["merge", "close"], "resume.phase", state["phase"])
        old = state["claim"]
        validate_claim(old, verify_verifier=False)
        old_route, new_route = claim_route(old), claim_route(claim)
        if old_route == new_route:
            require({k: v for k, v in old.items() if k != "verifier_sha256"} ==
                    {k: v for k, v in claim.items() if k != "verifier_sha256"},
                    "resume.claim", "identity changes are forbidden")
        else:
            require(old_route == "local" and new_route == "cloud", "resume.route", f"{old_route}->{new_route}")
            require("execution_envelope" not in old, "resume.route", "local execution envelope is not cloud-migratable")
            cleanup = state.get("cleanup_intent")
            require(cleanup is None or (isinstance(cleanup, dict) and cleanup.get("mode") == "no_op"
                    and cleanup.get("path_present") is False and cleanup.get("branch_head") is None
                    and cleanup.get("registrations") == []), "resume.cleanup_intent", cleanup)
            old_identity = {key: old[key] for key in COMMON_CLAIM_FIELDS
                            if key != "verifier_sha256"}
            new_identity = {key: claim[key] for key in COMMON_CLAIM_FIELDS
                            if key != "verifier_sha256"}
            old_identity["dependencies"] = old.get("dependencies", [])
            new_identity["dependencies"] = claim.get("dependencies", [])
            require(old_identity == new_identity,
                    "resume.claim", "provider identity changes are forbidden")
            state.setdefault("prior_routes", []).append({"route": old_route, "control_root": old["control_root"]})
        require(old["verifier_sha256"] != claim["verifier_sha256"], "resume.verifier", "unchanged")
        state.setdefault("prior_verifiers", []).append(old["verifier_sha256"])
        state["claim"] = claim
        state["scope"] = f"supervised single-Issue {new_route} landing"
        save(path, state)
        next_action = (provider_next(claim, "advance", path) if new_route == "cloud"
                       else reconcile_next(claim, path))
        return response("resume", state, "readback" if new_route == "cloud" else "reconcile",
                        next_action, provider_requests=[])


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
        require(state.get("schema") in (1, 2), "checkpoint.schema", state.get("schema"))
        claim = state["claim"]
        validate_claim(claim)
        require(claim_route(claim) == "local", "reconcile.route", claim_route(claim))
        require(state["phase"] in {"awaiting_reconcile", "reconciling", "resolved"}, "checkpoint.phase", state["phase"])
        root = Path(claim["control_root"]).resolve()
        require(not path.is_relative_to(root), "checkpoint.path", "must be outside source/worktree lifecycle")
        acceptance = profile(claim["repository"])
        base_ref = acceptance["base_ref"]
        origins = git_origins(claim["repository"])
        require(checked(["git", "remote", "get-url", "origin"], root) in origins, "origin", "unexpected; no automatic correction")
        require(checked(["git", "branch", "--show-current"], root) == base_ref, "local.branch", "expected " + base_ref)
        before = source_identity(root)
        envelope = execution_binding(claim, operation="reconcile", checkpoint=path)
        if envelope is None:
            runtime = runtime_check(Path(__file__).resolve().parent, binary)
        else:
            from issue_execution import validate_carrier
            try:
                identity = validate_carrier(envelope)
            except Refusal as error:
                raise LandingRefusal("reconcile.carrier", str(error)) from error
            require(str(Path(binary).resolve()) == identity["noodle"], "reconcile.binary", binary)
            runtime = {"observed_binary_sha256": envelope["execution"]["carrier"]["noodle"]["sha256"]}
        worktree = root / ".worktrees" / claim["worktree"]
        branch = checked(["git", "branch", "--list", claim["worktree"]], root)
        branch_head = checked(["git", "rev-parse", "refs/heads/" + claim["worktree"]], root) if branch else None
        entries = checked(["git", "worktree", "list", "--porcelain"], root).split("\n\n")
        registrations = []
        for entry in entries:
            lines = entry.splitlines()
            registered = next((line[9:] for line in lines if line.startswith("worktree ")), None)
            registered_branch = next((line[7:] for line in lines if line.startswith("branch ")), None)
            if registered == str(worktree) or registered_branch == "refs/heads/" + claim["worktree"]:
                registrations.append({"worktree": registered, "branch": registered_branch})
        if worktree.exists():
            require(source_identity(worktree) == {"head": claim["head"], "tree": claim["tree"]}, "worktree.identity", str(worktree))
        else:
            if state["phase"] == "awaiting_reconcile":
                require(not registrations, "cleanup.registration", registrations)
                require(not branch, "cleanup.branch", branch_head)
                require("cleanup_intent" not in state, "cleanup.intent", state.get("cleanup_intent"))
                git_path = shutil.which("git")
                require(git_path is not None, "cleanup.git", "not found")
                state["cleanup_intent"] = {
                    "mode": "no_op", "path_present": False, "branch_head": None,
                    "registrations": [], "main_head": before["head"],
                    "git_path": str(Path(git_path).resolve()),
                    "git_sha256": hashlib.sha256(Path(git_path).read_bytes()).hexdigest(),
                    "noodle_sha256": runtime["observed_binary_sha256"],
                    "verifier_sha256": claim["verifier_sha256"]}
            else:
                require(state["phase"] in {"reconciling", "resolved"}, "worktree.path", "missing before cleanup intent")
                if state.get("cleanup_intent", {}).get("mode") == "no_op":
                    require(not registrations, "cleanup.registration", registrations)
                    require(not branch, "cleanup.branch", branch_head)
                    intent = state["cleanup_intent"]
                    git_path = shutil.which("git")
                    require(git_path is not None, "cleanup.git", "not found")
                    require(intent.get("git_path") == str(Path(git_path).resolve())
                            and intent.get("git_sha256") == hashlib.sha256(Path(git_path).read_bytes()).hexdigest()
                            and intent.get("noodle_sha256") == runtime["observed_binary_sha256"]
                            and intent.get("verifier_sha256") == claim["verifier_sha256"],
                            "cleanup.observation", "no-op owner identity changed")
            if branch:
                require(state["phase"] == "reconciling", "cleanup.phase", state["phase"])
                require(branch_head == claim["head"], "cleanup.branch_head", branch_head)
                for registration in registrations:
                    require(registration["worktree"] == str(worktree), "cleanup.checkout", registration["worktree"])
        state["phase"] = "reconciling"
        save(path, state)
        fetch_main(root)
        remote_ref = "origin/" + base_ref
        checked(["git", "merge-base", "--is-ancestor", state["merge_sha"], remote_ref], root)
        checked(["git", "merge-base", "--is-ancestor", before["head"], remote_ref], root)
        checked(["git", "merge", "--ff-only", remote_ref], root)
        if envelope is not None:
            from issue_execution import completed_original_order, read_owner
            try:
                owner = read_owner(envelope)
            except Refusal as error:
                invalid = getattr(error, "invalid", {"field": "reconcile.noodle", "value": str(error)})
                required = getattr(error, "next", {}).get("required", ["completed_original_order_and_quiescent_sessions"])
                next_action = input_next("reconcile", required, path)
                next_action["owner"] = "Noodle"
                next_action["known"]["order_id"] = envelope["execution"]["order_id"]
                raise LandingRefusal(invalid["field"], invalid["value"], next_action) from error
            try:
                completion = completed_original_order(envelope, owner)
            except Refusal as error:
                required = getattr(error, "next", {}).get(
                    "required", ["completed_original_order_and_quiescent_sessions"])
                return response("reconcile", state, "noodle_reconcile", {
                    "kind": "input", "owner": "Noodle", "operation": "reconcile",
                    "required": required,
                    "known": {"checkpoint": str(path),
                              "order_id": envelope["execution"]["order_id"]},
                    "help_argv": cli_argv("reconcile", "--help")})
            state["noodle_reconciliation"] = completion
            save(path, state)
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
        final_registrations = checked(["git", "worktree", "list", "--porcelain"], root)
        require(str(worktree) not in final_registrations
                and "branch refs/heads/" + claim["worktree"] not in final_registrations,
                "cleanup.registration", claim["worktree"])
        cleanup_mode = "no_op" if state.get("cleanup_intent", {}).get("mode") == "no_op" else "noodle"
        state["local"] = {**source_identity(root), "removed_worktree": claim["worktree"],
                          "worktree_owner": "Noodle", "cleanup_mode": cleanup_mode}
        state["phase"], state["classification"] = "resolved", "RESOLVED"
        save(path, state)
        return {**state, **response("reconcile", state, "stop", None)}
