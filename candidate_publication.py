"""Publish one accepted Noodle-owned local candidate to one exact GitHub PR.

The acceptance receipt and Noodle claim select all mutable identity. This
module performs no merge, Issue closure, worktree cleanup, or retry loop.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from issue_admission import parse_contract
from repository_binding import git_origins, issue_urls, profile, selected, valid_name


SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
SUBJECT = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#([1-9][0-9]*)")
CLAIM_FIELDS = {
    "schema_version", "owner", "repository", "subject", "order_id",
    "stage_index", "attempt_id", "session_id", "worktree_name",
    "worktree_path", "branch", "head", "tree", "base_branch",
    "base_head", "push_remote", "remote_url", "evidence",
    "authorizes_provider_write", "authorizes_landing",
}
NATIVE_SCOPE = "native publication readiness"
# Legacy schema-1 receipts included these regressions. Preserve validation of
# those receipts; schema 2 checks native capabilities and leaves regressions to CI.
NATIVE_TESTS = ("test_issue_atom.py", "test_issue_execution.py", "test_candidate_publication.py",
                "test_local_continuation.py", "test_supervisor_admission.py")


class PublicationRefusal(ValueError):
    def __init__(self, field, value, required="exact_publication_input"):
        super().__init__(f"candidate publication: invalid {field}={value!r}")
        self.invalid = {"field": field, "value": value}
        self.next = {
            "kind": "input", "owner": "supervisor", "required": [required],
            "reason": "Refresh the named owner's input; never reconstruct identity or retry an unknown write.",
        }


class ProviderMutationUnknown(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _require(condition, field, value, required="exact_publication_input"):
    if not condition:
        raise PublicationRefusal(field, value, required)


def _read(path, field):
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise PublicationRefusal(field, type(error).__name__) from None
    _require(isinstance(value, dict), field, value)
    return value


def _digest(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as error:
        raise PublicationRefusal("claim.evidence", type(error).__name__) from None


def _git(root, *args, check=True):
    result = subprocess.run(["git", *args], cwd=root, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=30)
    if check and result.returncode:
        raise PublicationRefusal("git." + ".".join(args[:2]), result.returncode)
    return result


def _git_value(root, *args):
    return _git(root, *args).stdout.strip()


def validate_claim(root, claim, target_binding=None):
    root = Path(root).resolve()
    _require(set(claim) == CLAIM_FIELDS, "claim.fields", sorted(claim))
    for field in ("head", "tree", "base_head"):
        _require(isinstance(claim[field], str) and SHA40.fullmatch(claim[field]), "claim." + field, claim[field])
    evidence = claim["evidence"]
    _require(isinstance(evidence, dict) and set(evidence) == {
        "canonical_snapshot_sha256", "session_events_sha256"}, "claim.evidence", evidence)
    _require(all(isinstance(value, str) and SHA64.fullmatch(value) for value in evidence.values()),
             "claim.evidence", evidence)
    _require(claim["schema_version"] == 1 and claim["owner"] == "Noodle",
             "claim.owner", [claim["schema_version"], claim["owner"]])
    _require(claim["authorizes_provider_write"] is False and claim["authorizes_landing"] is False,
             "claim.authority", [claim["authorizes_provider_write"], claim["authorizes_landing"]])
    match = SUBJECT.fullmatch(claim["subject"] if isinstance(claim["subject"], str) else "")
    _require(match is not None and match.group(1) == claim["repository"],
             "claim.subject", claim["subject"])
    binding = {"repository": claim["repository"], "control_root": str(root.parent.parent)}
    if target_binding is not None:
        binding["target_binding"] = target_binding
    acceptance = selected(binding, _require)
    _require(target_binding is not None or claim["repository"] == "ed3c/soodles",
             "claim.repository", claim["repository"])
    _require(claim["base_branch"] == acceptance["base_ref"], "claim.base_branch", claim["base_branch"])
    _require(all(isinstance(claim[field], str) and claim[field].strip() for field in (
        "order_id", "attempt_id", "session_id", "worktree_name", "worktree_path",
        "branch", "base_branch", "push_remote", "remote_url")), "claim.identity", claim)
    _require(type(claim["stage_index"]) is int and claim["stage_index"] >= 0,
             "claim.stage_index", claim["stage_index"])
    _require(Path(claim["worktree_path"]).resolve() == root,
             "claim.worktree_path", claim["worktree_path"])
    _require(claim["push_remote"] == "origin" and claim["remote_url"] in git_origins(claim["repository"]),
             "claim.remote", [claim["push_remote"], claim["remote_url"]])

    events = root.parent.parent / ".noodle" / "sessions" / claim["session_id"] / "events.ndjson"
    snapshot = root.parent.parent / ".noodle" / "state.snapshot.json"
    _require(_digest(snapshot) == evidence["canonical_snapshot_sha256"],
             "claim.evidence.canonical_snapshot_sha256", evidence["canonical_snapshot_sha256"])
    _require(_digest(events) == evidence["session_events_sha256"],
             "claim.evidence.session_events_sha256", evidence["session_events_sha256"])

    _require(_git_value(root, "rev-parse", "--show-toplevel") == str(root), "git.root", str(root))
    _require(_git_value(root, "status", "--porcelain", "--untracked-files=all") == "", "git.status", "dirty")
    _require(_git_value(root, "symbolic-ref", "--short", "HEAD") == claim["branch"],
             "git.branch", claim["branch"])
    _require(_git_value(root, "rev-parse", "HEAD") == claim["head"], "git.head", claim["head"])
    _require(_git_value(root, "rev-parse", "HEAD^{tree}") == claim["tree"], "git.tree", claim["tree"])
    _require(_git_value(root, "remote", "get-url", "--push", claim["push_remote"]) == claim["remote_url"],
             "git.remote", claim["remote_url"])
    _require(_git(root, "merge-base", "--is-ancestor", claim["base_head"], claim["head"], check=False).returncode == 0,
             "git.base", claim["base_head"])
    _require(bool(_git_value(root, "diff", "--name-only", claim["base_head"] + ".." + claim["head"])),
             "git.changes", "none")
    return root, int(match.group(2))


def native_readiness(root, claim, noodle, target_binding=None):
    """Produce non-authorizing, native-only evidence before PR publication.

    Claim custody and clean source are checked on both sides of execution. Raw
    process results are retained; a failed native check cannot become a receipt.
    """
    from concurrent.futures import ThreadPoolExecutor
    from soodles import measured

    root, _ = measured("native_readiness.claim_before", validate_claim, root, claim, target_binding,
                       head=claim.get("head") if isinstance(claim, dict) else None)
    binary = measured("native_readiness.binary_before", _native_binary, noodle, head=claim["head"])
    checks = []
    # Use a physical temporary path: this is fixture configuration, not a
    # portability claim for the Linux-only runtime acceptance implementation.
    with tempfile.TemporaryDirectory(prefix="soodles-native-") as temporary:
        env = {key: value for key, value in os.environ.items()
               if key not in {"GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS",
                              "GIT_SSH_COMMAND", "SOODLES_AUTHORIZATION_SHA256"}
               and not key.startswith(("NOODLES_APP_", "NOODLES_TOKEN_", "GIT_CONFIG_"))}
        env["TMPDIR"] = str(Path(temporary).resolve())
        commands = [[binary, "publication", "claim", "--help"],
                    [binary, "worktree", "cleanup", "--help"]]
        def execute(argv):
            try:
                process = subprocess.run(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                         capture_output=True, text=True,
                                         timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise PublicationRefusal("readiness.process", {"argv": argv, "error": type(error).__name__}) from None
            return {"argv": argv, "exit_status": process.returncode,
                    "stdout": process.stdout, "stderr": process.stderr}

        with ThreadPoolExecutor(max_workers=min(2, os.cpu_count() or 1)) as pool:
            checks = list(pool.map(lambda argv: measured(
                "native_readiness.check", execute, argv, head=claim["head"],
                check=" ".join(argv[1:])), commands))
        for result in checks:
            _require(result["exit_status"] == 0, "readiness.check", result, "changed_candidate_or_native_capability")
    measured("native_readiness.claim_after", validate_claim, root, claim, target_binding, head=claim["head"])
    measured("native_readiness.binary_after", _native_binary, noodle, head=claim["head"])
    return {"schema_version": 2, "scope": NATIVE_SCOPE,
            **({"target_binding": target_binding} if target_binding is not None else {}),
            "repository": claim["repository"], "subject": claim["subject"],
            "candidate": {"head": claim["head"], "tree": claim["tree"]},
            "platform": platform.system().lower() + "_" + platform.machine().lower(),
            "noodle": {"path": binary, "sha256": noodle["sha256"]}, "checks": checks,
            "canonical_acceptance": "required after publication on exact-head Linux Actions",
            "authorizes_landing": False}


def _native_binary(spec):
    from issue_admission import AdmissionRefusal
    from issue_execution import executable_identity
    try:
        return executable_identity(spec, "readiness.noodle")
    except AdmissionRefusal as error:
        raise PublicationRefusal(error.invalid["field"], error.invalid["value"],
                                 "exact_native_noodle_capability") from error


def validate_inputs(root, acceptance, claim):
    candidate = acceptance.get("candidate")
    scope = acceptance.get("scope")
    _require(acceptance.get("repository") == claim.get("repository")
             and scope in {"candidate runtime acceptance", NATIVE_SCOPE}
             and acceptance.get("authorizes_landing") is False
             and isinstance(candidate, dict), "acceptance.identity", acceptance)
    _require(candidate.get("head") == claim.get("head") and candidate.get("tree") == claim.get("tree"),
             "acceptance.candidate", candidate)
    root, number = validate_claim(root, claim, acceptance.get("target_binding"))
    if scope == NATIVE_SCOPE:
        _require(acceptance.get("schema_version") in (1, 2) and acceptance.get("subject") == claim["subject"],
                 "readiness.identity", acceptance.get("subject"))
        observed = platform.system().lower() + "_" + platform.machine().lower()
        _require(acceptance.get("platform") == observed, "readiness.platform", acceptance.get("platform"))
        binary = _native_binary(acceptance.get("noodle"))
        checks = acceptance.get("checks")
        expected = [[binary, "publication", "claim", "--help"], [binary, "worktree", "cleanup", "--help"]]
        if acceptance["schema_version"] == 1:
            expected += [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", name]
                         for name in NATIVE_TESTS]
        _require(isinstance(checks, list) and len(checks) == len(expected), "readiness.checks", checks)
        _require(all(isinstance(check, dict) and check.get("argv") == argv
                     and type(check.get("exit_status")) is int and check["exit_status"] == 0
                     and isinstance(check.get("stdout"), str) and isinstance(check.get("stderr"), str)
                     for check, argv in zip(checks, expected)), "readiness.checks", checks)
    return root, number


class GitHubProvider:
    def __init__(self, repository, token=None):
        self.repository = repository
        self.token = token if token is not None else os.environ.get("GH_TOKEN", "")
        _require(bool(self.token) and all(33 <= ord(c) <= 126 for c in self.token),
                 "github.credential", "missing or invalid GH_TOKEN",
                 "repository_scoped_installation_token_in_GH_TOKEN")
        self.api = "https://api.github.com/repos/" + repository

    def request(self, method, path, body=None, mutation=False, missing=False):
        url = self.api + path
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        request = urllib.request.Request(url, data=data, method=method, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "soodles-candidate-publication",
            **({"Content-Type": "application/json"} if data is not None else {}),
        })
        try:
            try:
                response = urllib.request.build_opener(NoRedirect()).open(request, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                if response.url != url:
                    raise PublicationRefusal("github.url", response.url)
                status = response.code
                if missing and status == 404:
                    return None
                if status not in (200, 201):
                    if mutation:
                        raise ProviderMutationUnknown(f"{method} {path} returned {status}")
                    raise PublicationRefusal("github.readback", {"method": method, "url": url, "status": status},
                                             "fresh_provider_readback")
                value = json.loads(response.read().decode("utf-8"))
                _require(isinstance(value, (dict, list)), "github.response", type(value).__name__)
                return value
        except ProviderMutationUnknown:
            raise
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError) as error:
            if mutation:
                raise ProviderMutationUnknown(type(error).__name__) from None
            raise PublicationRefusal("github.readback", type(error).__name__, "fresh_provider_readback") from None

    def repository_info(self):
        return self.request("GET", "")

    def issue(self, number):
        return self.request("GET", f"/issues/{number}")

    def branch(self, branch):
        quoted = urllib.parse.quote(branch, safe="")
        return self.request("GET", "/git/ref/heads/" + quoted, missing=True)

    def base_head(self, branch):
        value = self.branch(branch)
        return None if value is None else value.get("object", {}).get("sha")

    def pulls(self, branch, base):
        owner = self.repository.split("/", 1)[0]
        query = urllib.parse.urlencode({"state": "open", "head": owner + ":" + branch,
                                       "base": base, "per_page": 100})
        return self.request("GET", "/pulls?" + query)

    def create_pull(self, title, branch, base, body):
        return self.request("POST", "/pulls", {"title": title, "head": branch,
                                                "base": base, "body": body}, mutation=True)

    def pull(self, number):
        return self.request("GET", f"/pulls/{number}")


def _exact_pull(pull, branch, head, base, body):
    return (isinstance(pull, dict) and pull.get("state") == "open"
            and pull.get("head", {}).get("ref") == branch
            and pull.get("head", {}).get("sha") == head
            and pull.get("base", {}).get("ref") == base
            and pull.get("body") == body
            and type(pull.get("number")) is int and pull["number"] > 0)


def _read_exact_pull(provider, branch, head, base, body):
    pulls = provider.pulls(branch, base)
    _require(isinstance(pulls, list), "github.pulls", pulls, "fresh_provider_readback")
    competing = [pull for pull in pulls if pull.get("head", {}).get("ref") == branch
                 or pull.get("head", {}).get("sha") == head]
    _require(all(_exact_pull(pull, branch, head, base, body) for pull in competing),
             "github.pull.shape", [pull.get("number") for pull in competing], "exact_provider_pr")
    _require(len(competing) <= 1, "github.pull.count", len(competing), "one_exact_provider_pr")
    return competing[0] if competing else None


def _comparison_before_effect(root, claim, issue, number, expected_body=None, target_binding=None):
    _require(issue.get("number") == number and issue.get("state") == "open"
             and "pull_request" not in issue, "github.issue", issue, "current_open_issue")
    if expected_body is not None and issue.get("body") != expected_body:
        from issue_admission import ComparisonRefusal
        raise ComparisonRefusal("comparison.issue.body", "changed", "fresh_issue_contract")
    contract = parse_contract(issue.get("body"))
    _require(contract["base_head"] == claim["base_head"], "github.issue.base_head", contract["base_head"])
    if contract["schema"] == 4 or target_binding is not None:
        from issue_admission import verify_candidate
        from issue_admission import comparison_require
        api, html = issue_urls(claim["repository"], number)
        comparison_require(issue.get("url") == api and issue.get("html_url") == html,
                           "comparison.issue.identity", [issue.get("url"), issue.get("html_url")],
                           "fresh_exact_issue_readback")
        # Schema 4 requires provider URL identity in the fresh readback.
        receipt = verify_candidate(root, claim["base_head"], claim["head"], issue, target_binding=target_binding)
        _require(receipt["issue"] == number and receipt["tree"] == claim["tree"],
                 "comparison.candidate", receipt)
    return contract


def push_disposition(receipt):
    """Only a complete single-ref porcelain rejection proves no ref update."""
    if not isinstance(receipt, dict) or receipt.get("process") != "completed":
        return "unknown"
    argv = receipt.get("argv", [])
    lines = [line.split("\t") for line in receipt.get("stdout", "").splitlines()
             if "\t" in line]
    if (type(receipt.get("exit_status")) is int and receipt["exit_status"] > 0
            and len(lines) == 1 and len(lines[0]) == 3 and lines[0][0] == "!"
            and argv and lines[0][1] == argv[-1]
            and lines[0][2].startswith(("[rejected]", "[remote rejected]"))):
        return "rejected"
    return "unknown"  # Even exit zero needs exact provider readback.


def run_push(root, argv, *, env=None, secrets=(), record=None):
    def redact(value):
        value = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        for secret in secrets:
            value = value.replace(secret, "[REDACTED]") if secret else value
        value = re.sub(r"(?i)(authorization:\s*(?:basic|bearer)\s+)\S+", r"\1[REDACTED]", value)
        value = re.sub(r"(https?://)[^/\s@]+@", r"\1[REDACTED]@", value)
        return value
    receipt = {"schema": 1, "argv": list(argv), "cwd": str(Path(root).resolve()),
               "process": "started", "started_ns": time.time_ns(), "exit_status": None, "stdout": "", "stderr": "",
               "seconds": None, "authorizes_landing": False}
    # Caller persists started before spawn; a crash cannot look like no attempt.
    if record:
        record(dict(receipt))
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=30, env=env)
        receipt.update(process="completed", exit_status=result.returncode,
                       stdout=redact(result.stdout), stderr=redact(result.stderr))
    except subprocess.TimeoutExpired as error:
        receipt.update(process="timed_out", stdout=redact(error.stdout), stderr=redact(error.stderr))
    except OSError as error:
        receipt.update(process="not_started", stderr=redact(str(error)), errno=error.errno)
    except UnicodeError:
        receipt.update(process="output_decode_error", stderr="Git output could not be decoded")
    except (KeyboardInterrupt, SystemExit):
        receipt.update(process="interrupted", stderr="Push interrupted; provider effect unknown")
        raise
    finally:
        receipt["seconds"] = round(time.monotonic() - started, 3)
        if record:
            record(dict(receipt))
    return receipt


def push_failure(receipt, remote_head, required="fresh_provider_branch_readback_without_retry"):
    if push_disposition(receipt) == "rejected":
        raise PublicationRefusal("github.push.rejected", {
            "exit_status": receipt["exit_status"], "stdout": receipt["stdout"],
            "stderr": receipt["stderr"], "remote_head": remote_head},
            "corrected_provider_push_capability_then_same_owner")
    raise PublicationRefusal("github.branch.outcome", remote_head, required)


def publish(root, acceptance, claim, provider, push=None, before_effect=None, refresh=None):
    root, number = validate_inputs(root, acceptance, claim)
    repository = provider.repository_info()
    _require(repository.get("full_name") == claim["repository"]
             and (acceptance.get("target_binding") is not None
                  or repository.get("default_branch") == claim["base_branch"]),
             "github.repository", repository, "exact_provider_repository")
    issue = provider.issue(number)
    _require(issue.get("number") == number and issue.get("state") == "open"
             and "pull_request" not in issue and isinstance(issue.get("title"), str),
             "github.issue", issue, "current_open_issue")
    _comparison_before_effect(root, claim, issue, number, target_binding=acceptance.get("target_binding"))
    _require(provider.base_head(claim["base_branch"]) == claim["base_head"],
             "github.base_head", claim["base_head"], "fresh_provider_base")

    branch = f"soodles/issue-{number}-{claim['head'][:12]}"
    remote = provider.branch(branch)
    if remote is not None:
        _require(remote.get("object", {}).get("sha") == claim["head"],
                 "github.branch.head", remote.get("object", {}).get("sha"), "exact_provider_branch")
    else:
        _comparison_before_effect(root, claim, provider.issue(number), number, issue["body"], acceptance.get("target_binding"))
        if before_effect is not None:
            before_effect("branch_push")
        push = push or _git
        result = push(root, "push", "--porcelain",
                      "--force-with-lease=refs/heads/" + branch + ":",
                      claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                      check=False)
        remote = provider.branch(branch)
        if remote is None or remote.get("object", {}).get("sha") != claim["head"]:
            push_failure(result, None if remote is None else remote.get("object", {}).get("sha"))

    body = "Refs " + claim["subject"]
    pull = _read_exact_pull(provider, branch, claim["head"], claim["base_branch"], body)
    created = False
    if pull is None:
        _comparison_before_effect(root, claim, provider.issue(number), number, issue["body"], acceptance.get("target_binding"))
        if before_effect is not None:
            before_effect("pr_create")
        try:
            provider.create_pull(issue["title"], branch, claim["base_branch"], body)
        except ProviderMutationUnknown:
            pass
        pull = _read_exact_pull(provider, branch, claim["head"], claim["base_branch"], body)
        _require(pull is not None, "github.pull.outcome", "unknown", "fresh_provider_pr_readback")
        created = True
    confirmed_number = pull["number"]
    pull = provider.pull(confirmed_number)
    # List and branch already confirm this candidate; only the known base head
    # in the same PR detail is eligible for one bounded, read-only refresh.
    if (refresh is not None and _exact_pull(pull, branch, claim["base_head"], claim["base_branch"], body)
            and pull.get("number") == confirmed_number and pull.get("merged") is not True):
        pull = refresh(confirmed_number, lambda value: (
            _exact_pull(value, branch, claim["head"], claim["base_branch"], body)
            and value.get("number") == confirmed_number and value.get("merged") is not True))
    _require(_exact_pull(pull, branch, claim["head"], claim["base_branch"], body),
             "github.pull.readback", pull, "exact_provider_pr")
    return {
        "owner": "soodles.candidate-publication", "status": "created" if created else "reused",
        "repository": claim["repository"], "subject": claim["subject"],
        "branch": branch, "head": claim["head"], "tree": claim["tree"],
        "pr": {"number": pull["number"], "url": pull.get("html_url")},
        "next": None, "authorizes_landing": False,
    }


def publish_amendment(root, acceptance, claim, provider, prior, *, offered, push=None, refresh=None, previous_push=None):
    """Read back one already offered update to the same PR, or offer it once.

    The lifecycle owner supplies its persisted prior publication and records
    ``offered`` before allowing ``push``. A repeated call with ``push=None``
    observes the provider only; it cannot repeat an uncertain write.
    """
    root, number = validate_inputs(root, acceptance, claim)
    branch, pr = validate_amendment_prior(prior, claim["repository"], claim["subject"], number)
    _require(prior["head"] != claim["head"], "amendment.head", prior["head"])
    _require(offered is True, "amendment.offer", offered, "persisted_owner_write_intent")

    repository = provider.repository_info()
    _require(repository.get("full_name") == claim["repository"]
             and (acceptance.get("target_binding") is not None
                  or repository.get("default_branch") == claim["base_branch"]),
             "github.repository", repository)
    issue = provider.issue(number)
    _comparison_before_effect(root, claim, issue, number, target_binding=acceptance.get("target_binding"))
    _require(provider.base_head(claim["base_branch"]) == claim["base_head"],
             "github.base_head", claim["base_head"], "fresh_provider_base")
    body = "Refs " + claim["subject"]
    current = provider.pull(pr["number"])
    _require(isinstance(current, dict) and current.get("state") == "open"
             and current.get("merged") is not True
             and current.get("head", {}).get("ref") == branch
             and current.get("head", {}).get("sha") in {prior["head"], claim["head"]}
             and current.get("base", {}).get("ref") == claim["base_branch"]
             and current.get("body") == body
             and current.get("number") == pr["number"],
             "github.pull.identity", current, "same_open_provider_pr")
    remote = provider.branch(branch)
    remote_head = None if remote is None else remote.get("object", {}).get("sha")
    _require(remote_head in {prior["head"], claim["head"]},
             "github.branch.head", remote_head, "exact_old_or_new_branch_readback")
    if remote_head == prior["head"] and push is not None:
        # The owner supplies ``push`` only for a durable allowed offer. Its exit
        # code cannot establish outcome; fresh provider readback below does.
        previous_push = push(root, "push", "--porcelain",
             "--force-with-lease=refs/heads/" + branch + ":" + prior["head"],
             claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
             check=False)
        remote = provider.branch(branch)
        remote_head = None if remote is None else remote.get("object", {}).get("sha")
    if remote_head != claim["head"]:
        push_failure(previous_push, remote_head)
    current = provider.pull(pr["number"])
    # Only an exact old PR beside a confirmed new branch is stale evidence.
    # Conflicting identity, unknown push outcome and ordinary waits never enter
    # this adapter. The atom callback owns its durable budget, not this publisher.
    if (refresh is not None
            and _exact_pull(current, branch, prior["head"], claim["base_branch"], body)
            and current["number"] == pr["number"] and current.get("merged") is not True):
        current = refresh(pr["number"], lambda value: (
            _exact_pull(value, branch, claim["head"], claim["base_branch"], body)
            and value["number"] == pr["number"] and value.get("merged") is not True))
    _require(_exact_pull(current, branch, claim["head"], claim["base_branch"], body)
             and current["number"] == pr["number"], "github.pull.readback", current,
             "same_exact_provider_pr")
    return {
        "owner": "soodles.candidate-publication", "status": "amended",
        "repository": claim["repository"], "subject": claim["subject"],
        "branch": branch, "head": claim["head"], "tree": claim["tree"],
        "pr": pr, "next": None, "authorizes_landing": False,
    }


def validate_amendment_prior(prior, repository, subject, number):
    """Validate the externally selected previous publication before effects."""
    _require(isinstance(prior, dict) and set(prior) == {
        "owner", "status", "repository", "subject", "branch", "head", "tree", "pr",
        "next", "authorizes_landing"}, "amendment.prior", prior)
    _require(prior["owner"] == "soodles.candidate-publication"
             and prior["status"] in {"created", "reused", "amended"}
             and prior["repository"] == repository
             and prior["subject"] == subject
             and prior["next"] is None and prior["authorizes_landing"] is False,
             "amendment.prior.identity", prior)
    _require(isinstance(prior["head"], str) and SHA40.fullmatch(prior["head"])
             and isinstance(prior["tree"], str) and SHA40.fullmatch(prior["tree"]),
             "amendment.head", prior["head"])
    branch = prior["branch"]
    _require(isinstance(branch, str) and re.fullmatch(
        rf"soodles/issue-{number}-[0-9a-f]{{12}}", branch),
        "amendment.branch", branch)
    pr = prior["pr"]
    _require(isinstance(pr, dict) and set(pr) == {"number", "url"}
             and type(pr["number"]) is int and pr["number"] > 0
             and pr["url"] == f"https://github.com/{repository}/pull/{pr['number']}",
             "amendment.pr", pr)
    return branch, pr


def run(root, acceptance_path, claim_path):
    acceptance = _read(acceptance_path, "acceptance")
    claim = _read(claim_path, "claim")
    if "target_binding" in acceptance:
        _require(isinstance(claim.get("worktree_path"), str), "claim.worktree_path", "missing")
        root = Path(claim["worktree_path"])
        validate_claim(root, claim, target_binding=acceptance["target_binding"])
    # Standalone publication retains the same one-offer/readback contract.
    # Store its process evidence beside the external readiness receipt, never
    # in the candidate whose clean identity is being published.
    import issue_atom
    journal = Path(acceptance_path).resolve().with_name(Path(acceptance_path).name + ".publication.json")
    _require(not journal.is_relative_to(Path(root).resolve()), "publication.journal", str(journal),
             "external_acceptance_receipt")
    with Path(acceptance_path).open("rb") as lock:
        import fcntl
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise PublicationRefusal("publication.busy", str(journal), "current_publication_owner") from None
        binding = {"claim": _digest(claim_path), "acceptance": _digest(acceptance_path)}
        state = _read(journal, "publication.journal") if journal.exists() else {
            "binding": binding, "writes": {}, "push_receipts": []}
        _require(state.get("binding") == binding, "publication.binding", "changed")
        def before(action):
            _require(action not in state["writes"], "publication.effect", action,
                     "fresh_provider_readback_without_retry")
            state["writes"][action] = "offered"
            issue_atom.save_json(journal, state)
        def record(receipt):
            if receipt["process"] == "started":
                state["push_receipts"].append(receipt)
            else:
                state["push_receipts"][-1] = receipt
            issue_atom.save_json(journal, state)
        provider = GitHubProvider(claim.get("repository"))
        return publish(root, acceptance, claim, provider,
                       push=issue_atom.authenticated_push(provider, record=record), before_effect=before)


def refusal_output(error):
    return {"owner": "soodles.candidate-publication", "status": "refused",
            "invalid": error.invalid, "next": error.next, "authorizes_landing": False,
            **({"repair": error.repair} if hasattr(error, "repair") else {})}
