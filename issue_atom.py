"""One resumable local Issue-atom lifecycle owner.

The external authorization fixes identity and capability.  This module routes
existing Issue admission, Noodle custody, candidate publication and landing
owners; it does not replace their validation.
"""
import hashlib
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import urllib.parse

import candidate_publication
import issue_admission
import issue_execution
import landing


SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
AUTH_FIELDS = {
    "schema_version", "owner", "repository", "control_root", "base_head",
    "task", "issue", "noodle", "carrier", "workflow",
}
MARKER_PREFIX = "<!-- soodles:local-atom-v1:"


class AtomRefusal(ValueError):
    def __init__(self, field, value, required="corrected_external_authorization"):
        super().__init__(f"issue atom: invalid {field}={value!r}")
        self.invalid = {"field": field, "value": value}
        self.required = required


class MutationUnknown(Exception):
    pass


def require(condition, field, value, required="corrected_external_authorization"):
    if not condition:
        raise AtomRefusal(field, value, required)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_file(path):
    try:
        return digest_bytes(Path(path).read_bytes())
    except OSError as error:
        raise AtomRefusal("authorization.path", type(error).__name__) from None


def read_json(path, field):
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise AtomRefusal(field, type(error).__name__) from None
    require(isinstance(value, dict), field, value)
    return value


def save_json(path, value, *, fresh=False):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if fresh:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as error:
            raise AtomRefusal("state.path", type(error).__name__) from None
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        try:
            fd, temporary = tempfile.mkstemp(prefix=".issue-atom-", dir=path.parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except OSError as error:
            try:
                os.unlink(temporary)
            except (NameError, OSError):
                pass
            raise AtomRefusal("state.path", type(error).__name__) from None
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "git." + ".".join(args[:2]), result.stderr.strip(),
            "clean_exact_control_root")
    return result.stdout.strip()


def clean_child_env():
    # Provider credentials never enter candidate or Noodle child processes.
    return {key: value for key, value in os.environ.items()
            if key not in {"GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS",
                           "SSH_ASKPASS", "GIT_SSH_COMMAND"}}


def validate_authorization(path, expected_digest, *, allow_advanced=False):
    source = Path(path)
    require(source.is_absolute(), "authorization.path", str(source), "absolute_external_authorization")
    value = read_json(source, "authorization")
    actual = digest_file(source)
    require(isinstance(expected_digest, str) and SHA64.fullmatch(expected_digest),
            "authorization.digest", expected_digest, "SOODLES_AUTHORIZATION_SHA256")
    require(actual == expected_digest, "authorization.digest", actual, "matching_external_digest")
    require(set(value) == AUTH_FIELDS, "authorization.fields", sorted(value))
    require(value["schema_version"] == 1 and value["owner"] == "external-supervisor",
            "authorization.owner", [value["schema_version"], value["owner"]])
    repository = value["repository"]
    require(isinstance(repository, str) and REPOSITORY.fullmatch(repository),
            "authorization.repository", repository)
    root = Path(value["control_root"]).resolve()
    require(Path(value["control_root"]).is_absolute() and root.is_dir(),
            "authorization.control_root", value["control_root"])
    require(not source.resolve().is_relative_to(root), "authorization.path", str(source),
            "authorization_outside_control_root")
    require(isinstance(value["base_head"], str) and SHA40.fullmatch(value["base_head"]),
            "authorization.base_head", value["base_head"])
    current_head = _git(root, "rev-parse", "HEAD")
    if allow_advanced:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", value["base_head"], current_head],
            cwd=root, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
        require(ancestor.returncode == 0, "git.head", current_head,
                "authorized_base_ancestry_after_checkpoint")
    else:
        require(current_head == value["base_head"],
                "git.head", current_head, "exact_authorized_base")
    require(_git(root, "status", "--porcelain", "--untracked-files=all") == "",
            "git.status", "dirty", "clean_exact_control_root")
    origins = {_git(root, "remote", "get-url", "origin")}
    require(any(url.rstrip("/").removesuffix(".git").endswith(repository) for url in origins),
            "git.origin", sorted(origins))
    issue = value["issue"]
    require(isinstance(issue, dict) and set(issue) == {"title", "body"},
            "authorization.issue", issue)
    require(all(isinstance(issue[key], str) and issue[key].strip() for key in issue),
            "authorization.issue", issue)
    contract = issue_admission.parse_contract(issue["body"])
    require(contract.get("base_head") == value["base_head"],
            "authorization.issue.base_head", contract.get("base_head"))
    noodle = value["noodle"]
    require(isinstance(noodle, dict) and set(noodle) == {"path", "sha256"},
            "authorization.noodle", noodle)
    require(Path(noodle["path"]).is_absolute() and Path(noodle["path"]).is_file()
            and isinstance(noodle["sha256"], str) and SHA64.fullmatch(noodle["sha256"])
            and digest_file(noodle["path"]) == noodle["sha256"],
            "authorization.noodle", noodle, "exact_noodle_binary")
    carrier = value["carrier"]
    require(isinstance(carrier, dict) and set(carrier) == {"platform", "codex"},
            "authorization.carrier", carrier)
    observed_platform = platform.system().lower() + "_" + platform.machine().lower()
    require(carrier["platform"] == observed_platform,
            "authorization.carrier.platform", carrier["platform"],
            "current_local_execution_platform")
    codex = carrier.get("codex")
    require(isinstance(codex, dict) and set(codex) == {"path", "sha256", "model", "argv"},
            "authorization.carrier.codex", codex)
    require(Path(codex["path"]).is_absolute() and Path(codex["path"]).is_file()
            and digest_file(codex["path"]) == codex["sha256"]
            and isinstance(codex["model"], str) and codex["model"].strip()
            and isinstance(codex["argv"], list) and all(isinstance(v, str) for v in codex["argv"]),
            "authorization.carrier.codex", codex, "exact_worker_carrier")
    workflow = value["workflow"]
    require(isinstance(workflow, dict) and set(workflow) == {"path", "job", "step"},
            "authorization.workflow", workflow)
    require(all(isinstance(workflow[key], str) and workflow[key].strip() for key in workflow),
            "authorization.workflow", workflow)
    require(isinstance(value["task"], str) and value["task"].strip(),
            "authorization.task", value["task"])
    return value, actual


class GitHubProvider(candidate_publication.GitHubProvider):
    def issues(self):
        return self.request("GET", "/issues?state=all&sort=created&direction=desc&per_page=100")

    def create_issue(self, title, body):
        try:
            return self.request("POST", "/issues", {"title": title, "body": body}, mutation=True)
        except candidate_publication.ProviderMutationUnknown as error:
            raise MutationUnknown(str(error)) from None

    def workflow_runs(self, head):
        query = urllib.parse.urlencode({"head_sha": head, "event": "pull_request", "per_page": 100})
        return self.request("GET", "/actions/runs?" + query)

    def jobs(self, run_id):
        return self.request("GET", f"/actions/runs/{run_id}/jobs?per_page=100")

    def git_commit(self, sha):
        return self.request("GET", f"/git/commits/{sha}")

    def branch_info(self, branch):
        quoted = urllib.parse.quote(branch, safe="")
        return self.request("GET", "/branches/" + quoted)

    def merge(self, number, head, method):
        try:
            return self.request("PUT", f"/pulls/{number}/merge",
                                {"sha": head, "merge_method": method}, mutation=True)
        except candidate_publication.ProviderMutationUnknown as error:
            raise MutationUnknown(str(error)) from None

    def close_issue(self, number, state_reason):
        try:
            return self.request("PATCH", f"/issues/{number}",
                                {"state": "closed", "state_reason": state_reason}, mutation=True)
        except candidate_publication.ProviderMutationUnknown as error:
            raise MutationUnknown(str(error)) from None


def marker(authorization_digest):
    return MARKER_PREFIX + authorization_digest + " -->"


def exact_issue(provider, authorization, authorization_digest):
    expected_marker = marker(authorization_digest)
    expected_body = authorization["issue"]["body"].rstrip() + "\n\n" + expected_marker + "\n"
    issues = provider.issues()
    require(isinstance(issues, list), "github.issues", issues, "fresh_provider_readback")
    matches = [item for item in issues if isinstance(item, dict)
               and "pull_request" not in item and expected_marker in (item.get("body") or "")]
    require(len(matches) <= 1, "github.issue.marker", len(matches), "one_exact_provider_issue")
    if not matches:
        return None, expected_body
    issue = provider.issue(matches[0].get("number"))
    require(issue.get("title") == authorization["issue"]["title"]
            and issue.get("body") == expected_body,
            "github.issue.shape", issue.get("number"), "exact_provider_issue")
    return issue, expected_body


def artifact_paths(authorization_path):
    source = Path(authorization_path)
    directory = source.parent / (source.name + ".d")
    return {
        "directory": directory,
        "state": source.with_name(source.name + ".state.json"),
        "envelope": directory / "envelope.json",
        "claim": directory / "publication-claim.json",
        "acceptance": directory / "acceptance.json",
        "landing": directory / "landing.json",
    }


def same_command(path):
    return [str((Path(__file__).resolve().parent / "issue-atom")), "run", str(Path(path).resolve())]


def response(state, authorization_path, *, status="pending", waiting_on=None, details=None):
    result = {
        "owner": "soodles.issue-atom", "status": status,
        "phase": state["phase"], "issue": state.get("issue"),
        "publication": state.get("publication"),
        "next": None if status == "resolved" else {
            "kind": "executable", "owner": "soodles.issue-atom",
            "required": ["material_owner_or_provider_state_change"],
            "argv": same_command(authorization_path),
            "reason": "Re-enter the same command; do not select a phase-specific Issue, publication, or landing verb.",
        },
        "authorizes_landing": False,
    }
    if waiting_on:
        result["waiting_on"] = waiting_on
    if details:
        result.update(details)
    return result


def create_envelope(authorization, issue, body, path):
    contract = issue_admission.parse_contract(body)
    number = issue["number"]
    root = Path(authorization["control_root"]).resolve()
    codex = authorization["carrier"]["codex"]
    envelope = {
        "schema": 1, "repository": authorization["repository"], "issue": number,
        "body_sha256": issue_admission.body_digest(body),
        "body_updated_at": issue["updated_at"], "owner": contract["owner"],
        "write_paths": contract["write_paths"], "base_head": authorization["base_head"],
        "execution": {
            "control_root": str(root), "worktree": f"soodles-{number}-0-execute",
            "order_id": f"soodles-{number}", "stage_index": 0,
            "task": authorization["task"], "source_head": authorization["base_head"],
            "carrier": {
                "platform": platform.system().lower() + "_" + platform.machine().lower(),
                "noodle": dict(authorization["noodle"]),
                "codex": dict(codex),
            },
        },
    }
    save_json(path, envelope, fresh=True)
    return envelope, digest_file(path)


def _run_claim(authorization, subject, output):
    argv = [authorization["noodle"]["path"], "--project-dir", authorization["control_root"],
            "publication", "claim", f"soodles-{subject.rsplit('#', 1)[1]}", subject]
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                            timeout=30, env=clean_child_env())
    if result.returncode == 0:
        try:
            claim = json.loads(result.stdout)
        except ValueError:
            raise AtomRefusal("noodle.claim", "malformed JSON", "fresh_noodle_claim") from None
        require(isinstance(claim, dict), "noodle.claim", claim, "fresh_noodle_claim")
        save_json(output, claim, fresh=not Path(output).exists())
    return result


def _accept(authorization, claim, output):
    from soodles import acceptance_verify
    captured_stdout, captured_stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
        result = acceptance_verify(Path(claim["worktree_path"]), authorization["noodle"]["path"])
    save_json(output, result, fresh=True)
    return result


def authenticated_push(provider):
    token = getattr(provider, "token", "")
    require(isinstance(token, str) and token, "github.credential", "missing",
            "repository_scoped_installation_token_in_GH_TOKEN")
    encoded = base64.b64encode(("x-access-token:" + token).encode()).decode()

    def push(root, *args, check=False):
        env = clean_child_env()
        env.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": "Authorization: Basic " + encoded,
            "GIT_TERMINAL_PROMPT": "0",
        })
        result = subprocess.run(["git", *args], cwd=root, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=30, env=env)
        if check and result.returncode:
            raise AtomRefusal("git.push", result.returncode, "fresh_provider_branch_readback")
        return result
    return push


def select_run(provider, authorization, head):
    value = provider.workflow_runs(head)
    runs = value.get("workflow_runs") if isinstance(value, dict) else None
    require(isinstance(runs, list), "github.workflow_runs", value, "fresh_exact_head_ci")
    matches = [run for run in runs if run.get("head_sha") == head
               and run.get("event") == "pull_request"
               and run.get("path") == authorization["workflow"]["path"]]
    require(len(matches) <= 1, "github.workflow_run.count", len(matches), "one_exact_head_runtime")
    if not matches:
        return None, None
    run = matches[0]
    jobs = provider.jobs(run["id"])
    values = jobs.get("jobs") if isinstance(jobs, dict) else None
    require(isinstance(values, list), "github.workflow_jobs", jobs, "fresh_exact_head_ci")
    target = [job for job in values if job.get("name") == authorization["workflow"]["job"]]
    require(len(target) == 1, "github.workflow_job.count", len(target), "one_exact_runtime_job")
    steps = target[0].get("steps")
    require(isinstance(steps, list), "github.workflow_steps", steps)
    step = [item for item in steps if item.get("name") == authorization["workflow"]["step"]]
    require(len(step) == 1, "github.workflow_step.count", len(step), "one_exact_acceptance_step")
    if run.get("status") != "completed" or target[0].get("status") != "completed":
        return run, jobs
    require(run.get("conclusion") == target[0].get("conclusion") == step[0].get("conclusion") == "success",
            "github.workflow.conclusion",
            [run.get("conclusion"), target[0].get("conclusion"), step[0].get("conclusion")],
            "new_candidate_head_after_failed_ci")
    return run, jobs


def provider_snapshot(provider, claim, run, jobs):
    pull = provider.pull(claim["pr"])
    issue = provider.issue(claim["issue"])
    snapshot = {
        "pr": pull, "issue": issue, "run": run, "jobs": jobs,
        "commit": provider.git_commit(claim["head"]),
        "branch": provider.branch_info("main"),
    }
    merge_sha = pull.get("merge_commit_sha") if pull.get("merged") else None
    if isinstance(merge_sha, str) and SHA40.fullmatch(merge_sha):
        snapshot["merge_commit"] = provider.git_commit(merge_sha)
    return snapshot


def run(authorization_path, *, environ=None, provider=None):
    environ = os.environ if environ is None else environ
    paths = artifact_paths(authorization_path)
    authorization, authorization_digest = validate_authorization(
        authorization_path, environ.get("SOODLES_AUTHORIZATION_SHA256"),
        allow_advanced=paths["state"].exists())
    state_path = paths["state"]
    if state_path.exists():
        state = read_json(state_path, "state")
        require(state.get("schema_version") == 1
                and state.get("authorization_sha256") == authorization_digest,
                "state.authorization", state.get("authorization_sha256"), "matching_lifecycle_checkpoint")
    else:
        state = {"schema_version": 1, "authorization_sha256": authorization_digest,
                 "phase": "issue", "writes": {}, "issue": None, "publication": None}
        save_json(state_path, state, fresh=True)

    provider = provider or GitHubProvider(authorization["repository"],
                                          token=environ.get("GH_TOKEN", ""))
    issue, body = exact_issue(provider, authorization, authorization_digest)
    if issue is None:
        write = state["writes"].get("issue_create")
        if write is None:
            state["writes"]["issue_create"] = {"status": "offered"}
            save_json(state_path, state)
            try:
                provider.create_issue(authorization["issue"]["title"], body)
            except MutationUnknown:
                pass
            issue, body = exact_issue(provider, authorization, authorization_digest)
        require(issue is not None, "github.issue.outcome", "unknown",
                "fresh_provider_issue_readback_without_retry")
    require(issue.get("state") == "open" or state["phase"] in {"landing", "resolved"},
            "github.issue.state", issue.get("state"), "current_issue_state")
    if state["issue"] is None:
        state["issue"] = {"number": issue["number"], "url": issue.get("html_url"),
                          "body_sha256": issue_admission.body_digest(body)}
        state["phase"] = "execution"
        save_json(state_path, state)

    if state["phase"] == "execution":
        if not paths["envelope"].exists():
            envelope, envelope_digest = create_envelope(authorization, issue, body, paths["envelope"])
            state["envelope_sha256"] = envelope_digest
            save_json(state_path, state)
        else:
            envelope_digest = digest_file(paths["envelope"])
            require(envelope_digest == state.get("envelope_sha256"),
                    "envelope.digest", envelope_digest, "unchanged_execution_envelope")
        issue_execution.supervised(paths["envelope"], envelope_digest,
                                   Path(authorization["control_root"]),
                                   reader=lambda repository, number: provider.issue(number))
        subject = authorization["repository"] + "#" + str(issue["number"])
        if not paths["claim"].exists() or state.get("failed_candidate_head"):
            claim_result = _run_claim(authorization, subject, paths["claim"])
            if claim_result.returncode:
                return response(state, authorization_path, waiting_on="Noodle",
                                details={"diagnostic": claim_result.stderr.strip()[-1000:]})
        claim = read_json(paths["claim"], "publication_claim")
        if state.get("failed_candidate_head"):
            require(claim.get("head") != state["failed_candidate_head"],
                    "acceptance.head", claim.get("head"), "changed_candidate_head")
            state.pop("failed_candidate_head")
            save_json(state_path, state)
        if not paths["acceptance"].exists():
            try:
                _accept(authorization, claim, paths["acceptance"])
            except Exception as error:
                state["failed_candidate_head"] = claim.get("head")
                save_json(state_path, state)
                raise AtomRefusal("acceptance", str(error), "changed_candidate_head") from error
        acceptance = read_json(paths["acceptance"], "acceptance")
        publication = candidate_publication.publish(
            Path(claim["worktree_path"]), acceptance, claim, provider,
            push=authenticated_push(provider))
        state["publication"] = publication
        state["phase"] = "ci"
        save_json(state_path, state)

    claim = read_json(paths["claim"], "publication_claim")
    publication = state["publication"]
    run_value, jobs = select_run(provider, authorization, claim["head"])
    if run_value is None or run_value.get("status") != "completed":
        return response(state, authorization_path, waiting_on="GitHub Actions")
    if state["phase"] == "ci":
        landing_claim = {
            "repository": authorization["repository"], "issue": issue["number"],
            "pr": publication["pr"]["number"], "head": claim["head"], "tree": claim["tree"],
            "base_head": claim["base_head"], "run_id": run_value["id"],
            "run_attempt": run_value["run_attempt"], "worktree": claim["worktree_name"],
            "control_root": authorization["control_root"],
            "verifier_sha256": landing.verifier_digest(),
            "execution_envelope": {"path": str(paths["envelope"]),
                                   "sha256": state["envelope_sha256"]},
        }
        snapshot = provider_snapshot(provider, landing_claim, run_value, jobs)
        landing.start(landing_claim, snapshot, paths["landing"])
        state["phase"] = "landing"
        save_json(state_path, state)

    landing_state = landing.read(paths["landing"])
    snapshot = provider_snapshot(provider, landing_state["claim"], run_value, jobs)
    transition = landing.advance(paths["landing"], snapshot)
    if transition["action"] == "dispatch":
        dispatched = landing.dispatch(paths["landing"], snapshot)
        request = dispatched["request"]
        try:
            if request["action"] == "merge":
                provider.merge(request["pr_number"], request["expected_head_sha"],
                               request["merge_method"])
            else:
                provider.close_issue(request["issue_number"], request["state_reason"])
        except MutationUnknown:
            pass
        return response(state, authorization_path, waiting_on="fresh provider readback")
    if transition["action"] == "reconcile":
        transition = landing.reconcile(paths["landing"], authorization["noodle"]["path"])
    if transition.get("classification") == "RESOLVED":
        state["phase"] = "resolved"
        save_json(state_path, state)
        return response(state, authorization_path, status="resolved",
                        details={"landing": transition})
    return response(state, authorization_path, waiting_on="fresh owner readback")


def refusal_output(error, authorization_path):
    return {
        "owner": "soodles.issue-atom", "status": "refused",
        "invalid": error.invalid,
        "next": {
            "kind": "input", "owner": "external-supervisor",
            "required": [error.required],
            "argv": same_command(authorization_path),
            "reason": "Correct the named external input or material owner state; never choose a phase-specific route.",
        },
        "authorizes_landing": False,
    }
