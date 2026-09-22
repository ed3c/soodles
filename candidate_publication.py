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
import urllib.error
import urllib.parse
import urllib.request

from issue_admission import parse_contract
from repository_binding import git_origins, profile, valid_name


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
# These controls exercise the native routing boundary. Linux runtime-lock
# admission and its process oracles remain in the post-publication Actions gate.
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


def validate_claim(root, claim):
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
    _require(valid_name(claim["repository"]) and profile(claim["repository"]) is not None,
             "claim.repository", claim["repository"])
    _require(claim["repository"] == "ed3c/soodles", "claim.repository", claim["repository"])
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


def native_readiness(root, claim, noodle):
    """Produce non-authorizing, native-only evidence before PR publication.

    Claim custody and clean source are checked on both sides of execution. Raw
    process results are retained; a failed native check cannot become a receipt.
    """
    root, _ = validate_claim(root, claim)
    binary = _native_binary(noodle)
    for name in NATIVE_TESTS:
        _require((root / "tests" / name).is_file(), "readiness.test", name)
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
        commands += [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", name]
                     for name in NATIVE_TESTS]
        for argv in commands:
            try:
                process = subprocess.run(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                         capture_output=True, text=True, timeout=180)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise PublicationRefusal("readiness.process", {"argv": argv, "error": type(error).__name__}) from None
            result = {"argv": argv, "exit_status": process.returncode,
                      "stdout": process.stdout, "stderr": process.stderr}
            checks.append(result)
            _require(process.returncode == 0, "readiness.check", result, "changed_candidate_or_native_capability")
    validate_claim(root, claim)
    _native_binary(noodle)
    return {"schema_version": 1, "scope": NATIVE_SCOPE,
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
    root, number = validate_claim(root, claim)
    if scope == NATIVE_SCOPE:
        _require(acceptance.get("schema_version") == 1 and acceptance.get("subject") == claim["subject"],
                 "readiness.identity", acceptance.get("subject"))
        observed = platform.system().lower() + "_" + platform.machine().lower()
        _require(acceptance.get("platform") == observed, "readiness.platform", acceptance.get("platform"))
        binary = _native_binary(acceptance.get("noodle"))
        checks = acceptance.get("checks")
        _require(isinstance(checks, list) and len(checks) == 2 + len(NATIVE_TESTS), "readiness.checks", checks)
        expected = [[binary, "publication", "claim", "--help"], [binary, "worktree", "cleanup", "--help"]]
        expected += [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", name]
                     for name in NATIVE_TESTS]
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


def publish(root, acceptance, claim, provider, push=None):
    root, number = validate_inputs(root, acceptance, claim)
    repository = provider.repository_info()
    _require(repository.get("full_name") == claim["repository"]
             and repository.get("default_branch") == claim["base_branch"],
             "github.repository", repository, "exact_provider_repository")
    issue = provider.issue(number)
    _require(issue.get("number") == number and issue.get("state") == "open"
             and "pull_request" not in issue and isinstance(issue.get("title"), str),
             "github.issue", issue, "current_open_issue")
    contract = parse_contract(issue.get("body"))
    _require(contract["base_head"] == claim["base_head"], "github.issue.base_head", contract["base_head"])
    _require(provider.base_head(claim["base_branch"]) == claim["base_head"],
             "github.base_head", claim["base_head"], "fresh_provider_base")

    branch = f"soodles/issue-{number}-{claim['head'][:12]}"
    remote = provider.branch(branch)
    if remote is not None:
        _require(remote.get("object", {}).get("sha") == claim["head"],
                 "github.branch.head", remote.get("object", {}).get("sha"), "exact_provider_branch")
    else:
        push = push or _git
        result = push(root, "push", "--porcelain",
                      "--force-with-lease=refs/heads/" + branch + ":",
                      claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                      check=False)
        remote = provider.branch(branch)
        _require(remote is not None and remote.get("object", {}).get("sha") == claim["head"],
                 "github.branch.readback", None if remote is None else remote.get("object", {}).get("sha"),
                 "fresh_provider_branch_readback")
        if result.returncode and remote.get("object", {}).get("sha") != claim["head"]:
            raise PublicationRefusal("github.branch.outcome", "unknown", "fresh_provider_branch_readback")

    body = "Refs " + claim["subject"]
    pull = _read_exact_pull(provider, branch, claim["head"], claim["base_branch"], body)
    created = False
    if pull is None:
        try:
            provider.create_pull(issue["title"], branch, claim["base_branch"], body)
        except ProviderMutationUnknown:
            pass
        pull = _read_exact_pull(provider, branch, claim["head"], claim["base_branch"], body)
        _require(pull is not None, "github.pull.outcome", "unknown", "fresh_provider_pr_readback")
        created = True
    pull = provider.pull(pull["number"])
    _require(_exact_pull(pull, branch, claim["head"], claim["base_branch"], body),
             "github.pull.readback", pull, "exact_provider_pr")
    return {
        "owner": "soodles.candidate-publication", "status": "created" if created else "reused",
        "repository": claim["repository"], "subject": claim["subject"],
        "branch": branch, "head": claim["head"], "tree": claim["tree"],
        "pr": {"number": pull["number"], "url": pull.get("html_url")},
        "next": None, "authorizes_landing": False,
    }


def run(root, acceptance_path, claim_path):
    acceptance = _read(acceptance_path, "acceptance")
    claim = _read(claim_path, "claim")
    return publish(root, acceptance, claim, GitHubProvider(claim.get("repository")))


def refusal_output(error):
    return {"owner": "soodles.candidate-publication", "status": "refused",
            "invalid": error.invalid, "next": error.next, "authorizes_landing": False}
