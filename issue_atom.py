"""One resumable local Issue-atom lifecycle owner.

The external authorization fixes identity and capability.  This module routes
existing Issue admission, Noodle custody, candidate publication and landing
owners; it does not replace their validation.
"""
import hashlib
import base64
import fcntl
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.parse

import candidate_publication
import issue_admission
import issue_execution
import provider_credential
import supervisor_admission
from repository_binding import git_origins


SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
AUTH_FIELDS = {
    "schema_version", "owner", "repository", "control_root", "base_head",
    "task", "issue", "noodle", "carrier", "workflow", "host_config_sha256",
}
OWNER_FILES = ("landing.py", "provider-execute", "provider_transport.py", "soodles.py",
               "issue_admission.py", "repository_binding.py", "dependency_binding.py",
               "issue_execution.py", "policy/runtime.lock.json")
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
    # These claim/readiness/landing children need no provider credential. The
    # separate supervisor start wrapper supplies its narrow Issue-read token.
    return provider_credential.clean_child_env()


def validate_authorization(path, expected_digest, *, allow_advanced=False):
    value, actual = _validate_authorization(path, expected_digest, allow_advanced=allow_advanced)
    require_clean_control_root(value)
    return value, actual


def require_clean_control_root(authorization):
    require(_git(authorization["control_root"], "status", "--porcelain", "--untracked-files=all") == "",
            "git.status", "dirty", "clean_exact_control_root")


def _validate_authorization(path, expected_digest, *, allow_advanced=False):
    source = Path(path)
    require(source.is_absolute(), "authorization.path", str(source), "absolute_external_authorization")
    value = read_json(source, "authorization")
    actual = digest_file(source)
    require(isinstance(expected_digest, str) and SHA64.fullmatch(expected_digest),
            "authorization.digest", expected_digest, "SOODLES_AUTHORIZATION_SHA256")
    require(actual == expected_digest, "authorization.digest", actual, "matching_external_digest")
    require(set(value) == AUTH_FIELDS | {"landing_owner"}, "authorization.fields", sorted(value),
            "external_authorization_with_pinned_host_and_landing_owner")
    require(value["schema_version"] == 2 and value["owner"] == "external-supervisor",
            "authorization.owner", [value["schema_version"], value["owner"]])
    repository = value["repository"]
    require(isinstance(repository, str) and REPOSITORY.fullmatch(repository)
            and repository == supervisor_admission.REPOSITORY,
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
    origins = {_git(root, "remote", "get-url", "origin")}
    require(origins.issubset(set(git_origins(repository))),
            "git.origin", sorted(origins))
    issue = value["issue"]
    require(isinstance(issue, dict) and set(issue) in ({"title", "body"}, {"title", "body", "number"}),
            "authorization.issue", issue)
    require(all(isinstance(issue[key], str) and issue[key].strip() for key in ("title", "body")),
            "authorization.issue", issue)
    if "number" in issue:
        require(type(issue["number"]) is int and issue["number"] > 0,
                "authorization.issue.number", issue["number"])
    config_digest = value["host_config_sha256"]
    require(config_digest is None or isinstance(config_digest, str) and SHA64.fullmatch(config_digest),
            "authorization.host_config_sha256", config_digest)
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
    validate_landing_owner(value)
    return value, actual


def validate_landing_owner(authorization):
    spec = authorization.get("landing_owner")
    require(isinstance(spec, dict) and set(spec) == {"path", "sha256", "verifier_sha256"},
            "authorization.landing_owner", spec, "immutable_external_landing_owner")
    path = Path(spec["path"]).resolve()
    root = Path(authorization["control_root"]).resolve()
    require(Path(spec["path"]).is_absolute() and path.name == "soodles.py"
            and not path.is_relative_to(root)
            and path.parent != Path(__file__).resolve().parent,
            "authorization.landing_owner.path", str(path), "owner_outside_candidate")
    require(digest_file(path) == spec["sha256"], "authorization.landing_owner.sha256",
            spec["sha256"], "unchanged_external_owner")
    hashes = {name: digest_file(path.parent / name) for name in OWNER_FILES}
    actual = digest_bytes(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode())
    require(actual == spec["verifier_sha256"], "authorization.landing_owner.verifier_sha256",
            actual, "unchanged_external_owner")
    return path


class LandingOwner:
    """Transport to the already selected owner, never import the candidate judge."""
    def __init__(self, authorization, directory):
        self.authorization = authorization
        self.directory = Path(directory)

    def call(self, operation, *arguments):
        path = validate_landing_owner(self.authorization)
        argv = [sys.executable, "-B", str(path), "landing", operation, *map(str, arguments)]
        process = subprocess.run(argv, cwd=path.parent, env=clean_child_env(),
                                 stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
        record = {"argv": argv, "exit_status": process.returncode,
                  "stdout": process.stdout, "stderr": process.stderr}
        # Each observation survives later invocations; do not overwrite unknown
        # write or cleanup evidence with a subsequent refusal.
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, record_path = tempfile.mkstemp(prefix="landing-" + operation + "-", suffix=".json",
                                         dir=self.directory)
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream, indent=2)
        try:
            result = json.loads(process.stdout)
        except ValueError:
            raise AtomRefusal("landing.output", record_path, "fresh_external_owner_readback") from None
        require(process.returncode == 0 and isinstance(result, dict), "landing.owner",
                {"receipt": record_path, "result": result}, "current_external_owner_next")
        return result

    def start(self, claim, snapshot, checkpoint):
        claim_path, readback = self.directory / "landing-claim.json", self.directory / "readback.json"
        save_json(claim_path, claim)
        save_json(readback, snapshot)
        return self.call("start", claim_path, readback, checkpoint)

    def advance(self, checkpoint, snapshot):
        readback = self.directory / "readback.json"
        save_json(readback, snapshot)
        return self.call("advance", checkpoint, readback)

    def dispatch(self, checkpoint, snapshot):
        readback = self.directory / "readback.json"
        save_json(readback, snapshot)
        return self.call("dispatch", checkpoint, readback)

    def reconcile(self, checkpoint, binary):
        return self.call("reconcile", checkpoint, binary)


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
    selected = authorization["issue"]
    if "number" in selected:
        # Explicit adoption never creates a replacement or changes provider bytes.
        issue = provider.issue(selected["number"])
        require(isinstance(issue, dict) and issue.get("number") == selected["number"]
                and issue.get("title") == selected["title"] and issue.get("body") == selected["body"]
                and issue.get("html_url") == f'https://github.com/{authorization["repository"]}/issues/{selected["number"]}'
                and "pull_request" not in issue,
                "github.issue.adoption", selected["number"], "exact_provider_issue")
        return issue, selected["body"]
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
        "envelope": directory / "admission/envelope.json",
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


def create_envelope(authorization, issue, body, path, *, environ=None):
    root = Path(authorization["control_root"]).resolve()
    require(issue["body"] == body, "envelope.issue_body", "changed")
    path.parent.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = supervisor_admission.prepare(
        issue, {**authorization["carrier"], "noodle": authorization["noodle"]},
        root, path.parent, environ=environ, task=authorization["task"], wire_host=True)
    save_json(path.parent / "prepared.json", result, fresh=True)
    return read_json(path, "envelope"), result["envelope_sha256"]


def host_config_identity(root):
    path = Path(root) / ".noodle.toml"
    require(not path.is_symlink(), "noodle.config", "symlink", "unchanged_host_configuration")
    return digest_file(path) if path.exists() else None


def ensure_noodle(authorization, paths, state, admission, environ):
    """Consume the producer's start once; Noodle's lock remains process authority."""
    root = Path(authorization["control_root"])
    prepared = read_json(paths["envelope"].parent / "prepared.json", "admission.prepared")
    require(digest_file(paths["envelope"].parent / "prepared.json") == state.get("admission_sha256"),
            "admission.prepared.digest", "changed", "unchanged_supervisor_start")
    start = prepared["next"]["argv"]
    require(start == [prepared["start"]] and digest_file(start[0]) == prepared["start_sha256"],
            "noodle.start.identity", start, "unchanged_supervisor_start")
    runtime = root / ".noodle"
    require(runtime.is_dir(), "noodle.runtime", str(runtime), "existing_noodle_owner")
    with (runtime / "noodle.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            require(host_config_identity(root) == digest_file(paths["envelope"].parent / "noodle.toml"),
                    "noodle.running.config", "foreign", "current_noodle_owner_readback")
            return {"action": "running", "start_repeated": False}
        # Never respawn a stopped or unknown prior attempt, even after a lost
        # Popen response. Its current owner must supply recovery/readback.
        require("noodle_start" not in state, "noodle.start.outcome", "stopped_or_unknown",
                "current_noodle_owner_readback_without_restart")
        require(admission.get("action") == "proposal_pending", "noodle.start.admission",
                admission.get("action"), "original_noodle_owner_continuation")
        binding = read_json(paths["envelope"], "envelope")
        owner = issue_execution.read_owner(binding)
        for order in owner["state"]["orders"].values():
            require(isinstance(order, dict) and isinstance(order.get("stages"), list)
                    and all(stage.get("status") in ("completed", "failed", "cancelled")
                            for stage in order["stages"]),
                    "noodle.start.orders", "nonquiescent", "quiescent_noodle_owner")
        for process in sorted((runtime / "sessions").glob("*/process.json")):
            issue_execution._absent_process(process.parent, process.parent.name)
        require(host_config_identity(root) == authorization["host_config_sha256"],
                "noodle.config.digest", host_config_identity(root), "unchanged_host_configuration")
        ignored = subprocess.run(["git", "check-ignore", "-q", ".noodle.toml"], cwd=root)
        require(ignored.returncode == 0, "noodle.config.tracked", ".noodle.toml",
                "host_owned_ignored_noodle_configuration")
        config = root / ".noodle.toml"
        original = config.read_bytes() if config.exists() else None
        generated = (paths["envelope"].parent / "noodle.toml").read_bytes()
        state["noodle_start"] = {"status": "offered", "argv": start,
                                 "config_sha256": digest_bytes(generated),
                                 "original_config": None if original is None else base64.b64encode(original).decode()}
        save_json(paths["state"], state)
        # Holding the existing Noodle lock excludes an active owner during the
        # bounded config replacement. Noodle itself acquires it on child start.
        config.write_bytes(generated)
    stdout_path = paths["directory"] / "noodle.stdout"
    stderr_path = paths["directory"] / "noodle.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        child = subprocess.Popen(start, cwd=root, env=dict(environ), stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, start_new_session=True)
    state["noodle_start"].update(pid=child.pid, status="started",
                                stdout=str(stdout_path), stderr=str(stderr_path))
    save_json(paths["state"], state)
    return {"action": "started", "pid": child.pid, "start_repeated": False}


def complete_noodle(authorization, paths, state, transition):
    """After landing's ff-only readback, ask the existing Noodle review owner once."""
    next_action = transition.get("next", {})
    binding = read_json(paths["envelope"], "envelope")
    order_id = binding["execution"]["order_id"]
    require(next_action.get("owner") == "Noodle"
            and next_action.get("known", {}).get("order_id") == order_id,
            "noodle.completion.owner", next_action, "current_landing_next")
    landing_state = read_json(paths["landing"], "landing.checkpoint")
    require(landing_state.get("phase") == "reconciling"
            and set(landing_state.get("writes_offered", [])) == {"merge", "close"},
            "noodle.completion.phase", landing_state.get("phase"), "confirmed_provider_closure")
    root = Path(authorization["control_root"])
    claim = landing_state["claim"]
    _git(root, "merge-base", "--is-ancestor", claim["head"], "HEAD")
    _git(root, "merge-base", "--is-ancestor", landing_state["merge_sha"], "HEAD")
    owner = issue_execution.read_owner(binding)
    issue_execution.quiescent_order(binding, owner)
    stages = owner["state"]["orders"][order_id]["stages"]
    require(len(stages) == 1 and stages[0].get("status") == "review",
            "noodle.completion.review", order_id, "current_original_review")
    command = {"id": "soodles-atom-" + state["authorization_sha256"][:24],
               "action": "merge", "order_id": order_id}
    runtime = root / ".noodle"
    with (runtime / "control.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ack_path = runtime / "control-ack.ndjson"
        acks = [json.loads(line) for line in ack_path.read_text().splitlines() if line.strip()] if ack_path.exists() else []
        matches = [ack for ack in acks if ack.get("id") == command["id"]]
        if matches:
            require(len(matches) == 1 and matches[0].get("action") == "merge"
                    and matches[0].get("status") == "ok",
                    "noodle.completion.ack", matches, "current_noodle_owner_readback")
            state["noodle_completion_ack"] = matches[0]
            save_json(paths["state"], state)
            return
        if "noodle_completion" in state:
            require(state["noodle_completion"] == command, "noodle.completion.command", "changed")
            # Missing acknowledgement is not permission to append the command again.
            return
        state["noodle_completion"] = command
        save_json(paths["state"], state)
        with (runtime / "control.ndjson").open("ab") as mailbox:
            mailbox.write((json.dumps(command, sort_keys=True) + "\n").encode())
            mailbox.flush()
            os.fsync(mailbox.fileno())


def finish_host(authorization, paths, state):
    """Retire only this entry's own loop; restore only unchanged installed config."""
    if state.get("noodle_completion"):
        command = state["noodle_completion"]
        ack_path = Path(authorization["control_root"]) / ".noodle/control-ack.ndjson"
        acks = [json.loads(line) for line in ack_path.read_text().splitlines() if line.strip()]
        matches = [ack for ack in acks if ack.get("id") == command["id"]]
        require(len(matches) == 1 and matches[0].get("action") == command["action"]
                and matches[0].get("status") == "ok",
                "noodle.completion.ack", matches, "current_noodle_owner_readback")
        if state.get("noodle_completion_ack") != matches[0]:
            state["noodle_completion_ack"] = matches[0]
            save_json(paths["state"], state)
    start = state.get("noodle_start")
    if start is None:
        return True  # An adopted external owner is not ours to terminate.
    require(type(start.get("pid")) is int and start["pid"] > 1,
            "noodle.stop.pid", start.get("pid"), "original_start_process_readback")
    pid = start["pid"]
    observed = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    if observed.returncode == 0 and observed.stdout.strip():
        expected = " ".join([authorization["noodle"]["path"], "--project-dir", authorization["control_root"], "start"])
        require(observed.stdout.strip() == expected, "noodle.stop.identity", "changed",
                "original_start_process_readback")
        if not start.get("stop_offered"):
            start["stop_offered"] = True
            save_json(paths["state"], state)
            os.kill(pid, signal.SIGTERM)  # Noodle's documented shutdown path.
        return False
    require(observed.returncode == 1, "noodle.stop.readback", observed.returncode,
            "original_start_process_readback")
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise AtomRefusal("noodle.stop.process_group", "present", "quiescent_noodle_owner")
    if start.get("restored"):
        require(host_config_identity(authorization["control_root"]) == authorization["host_config_sha256"],
                "noodle.config.restored", "changed", "unchanged_host_configuration")
        return True
    root = Path(authorization["control_root"])
    with (root / ".noodle/noodle.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("noodle.stop.owner", "running", "quiescent_noodle_owner") from None
        observed_config = host_config_identity(root)
        if start.get("restore_offered") and observed_config == authorization["host_config_sha256"]:
            start["restored"] = True
            save_json(paths["state"], state)
            return True
        require(observed_config == start["config_sha256"],
                "noodle.config.restore", "changed", "unchanged_installed_configuration")
        original = start["original_config"]
        require((None if original is None else digest_bytes(base64.b64decode(original)))
                == authorization["host_config_sha256"], "noodle.config.backup", "changed")
        start["restore_offered"] = True
        save_json(paths["state"], state)
        if original is None:
            (root / ".noodle.toml").unlink()
        else:
            (root / ".noodle.toml").write_bytes(base64.b64decode(original))
        start["restored"] = True
        save_json(paths["state"], state)
    return True


def _run_claim(authorization, subject, output):
    argv = [authorization["noodle"]["path"], "--project-dir", authorization["control_root"],
            "publication", "claim", f"soodles-{subject.rsplit('#', 1)[1]}", subject]
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                            timeout=30, env=clean_child_env())
    save_json(Path(output).with_name(f"claim-process-{time.time_ns()}.json"),
              {"argv": argv, "exit_status": result.returncode,
               "stdout": result.stdout, "stderr": result.stderr,
               "authorizes_landing": False}, fresh=True)
    if result.returncode == 0:
        try:
            claim = json.loads(result.stdout)
        except ValueError:
            raise AtomRefusal("noodle.claim", "malformed JSON", "fresh_noodle_claim") from None
        require(isinstance(claim, dict), "noodle.claim", claim, "fresh_noodle_claim")
        save_json(output, claim, fresh=not Path(output).exists())
    return result


def _accept(authorization, claim, output):
    result = candidate_publication.native_readiness(
        Path(claim["worktree_path"]), claim, authorization["noodle"])
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
    # GitHub may expose a queued run before creating any jobs or steps. This is
    # an observation to wait on, not a malformed completed acceptance receipt.
    if run.get("status") in {"queued", "in_progress", "waiting", "pending", "requested"}:
        return run, jobs
    require(run.get("status") == "completed", "github.workflow.status", run.get("status"),
            "fresh_exact_head_ci")
    target = [job for job in values if job.get("name") == authorization["workflow"]["job"]]
    require(len(target) == 1, "github.workflow_job.count", len(target), "one_exact_runtime_job")
    steps = target[0].get("steps")
    require(isinstance(steps, list), "github.workflow_steps", steps)
    step = [item for item in steps if item.get("name") == authorization["workflow"]["step"]]
    require(len(step) == 1, "github.workflow_step.count", len(step), "one_exact_acceptance_step")
    require(target[0].get("status") == "completed", "github.workflow_job.status",
            target[0].get("status"), "fresh_exact_head_ci")
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
    # Serialize the one authorization's existing checkpoint/intent transitions.
    # The Noodle instance lock still decides runtime ownership.
    with Path(authorization_path).open("rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("authorization.busy", str(authorization_path),
                              "current_same_entry_owner_readback") from None
        return _run(authorization_path, environ=environ, provider=provider)


def _run(authorization_path, *, environ=None, provider=None):
    environ = os.environ if environ is None else environ
    paths = artifact_paths(authorization_path)
    authorization, authorization_digest = _validate_authorization(
        authorization_path, environ.get("SOODLES_AUTHORIZATION_SHA256"),
        allow_advanced=paths["state"].exists())
    if provider is None:
        try:
            environ = provider_credential.resolve_host_environment(
                authorization["control_root"], environ=environ)
        except provider_credential.CredentialRefusal as error:
            raise AtomRefusal(error.field, error.value, error.required) from None
    # A profile placed inside the candidate names that boundary first. A valid
    # registration still cannot reach a supplier with a dirty control root.
    require_clean_control_root(authorization)
    landing_owner = LandingOwner(authorization, paths["directory"])
    state_path = paths["state"]
    if state_path.exists():
        state = read_json(state_path, "state")
        require(state.get("schema_version") == 1
                and state.get("authorization_sha256") == authorization_digest,
                "state.authorization", state.get("authorization_sha256"), "matching_lifecycle_checkpoint")
    else:
        state = {"schema_version": 1, "authorization_sha256": authorization_digest,
                 "phase": "issue", "writes": {}, "issue": None, "publication": None}
        require(host_config_identity(authorization["control_root"]) == authorization["host_config_sha256"],
                "noodle.config.digest", "changed", "unchanged_host_configuration")

    if provider is None:
        try:
            token = provider_credential.supply_token(
                authorization["repository"],
                {"contents": "write", "issues": "write",
                 "pull_requests": "write", "actions": "read"}, environ=environ)
        except provider_credential.CredentialRefusal as error:
            raise AtomRefusal(error.field, error.value, error.required) from None
        provider = GitHubProvider(authorization["repository"], token=token)
    if not state_path.exists():
        save_json(state_path, state, fresh=True)
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
            envelope, envelope_digest = create_envelope(authorization, issue, body, paths["envelope"], environ=environ)
            state["envelope_sha256"] = envelope_digest
            state["admission_sha256"] = digest_file(paths["envelope"].parent / "prepared.json")
            save_json(state_path, state)
        else:
            envelope_digest = digest_file(paths["envelope"])
            require(envelope_digest == state.get("envelope_sha256"),
                    "envelope.digest", envelope_digest, "unchanged_execution_envelope")
        admission = issue_execution.supervised(
            paths["envelope"], envelope_digest, Path(authorization["control_root"]),
            reader=lambda repository, number: provider.issue(number), observe_live=True)
        if admission.get("action") == "running":
            return response(state, authorization_path, waiting_on="Noodle",
                            details={"execution": admission})
        if admission.get("action") == "proposal_pending":
            execution = ensure_noodle(authorization, paths, state, admission, environ)
            return response(state, authorization_path, waiting_on="Noodle", details={"execution": execution})
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
            "publication_branch": publication["branch"],
            "control_root": authorization["control_root"],
            "verifier_sha256": authorization["landing_owner"]["verifier_sha256"],
            "execution_envelope": {"path": str(paths["envelope"]),
                                   "sha256": state["envelope_sha256"]},
        }
        snapshot = provider_snapshot(provider, landing_claim, run_value, jobs)
        landing_owner.start(landing_claim, snapshot, paths["landing"])
        state["phase"] = "landing"
        save_json(state_path, state)

    landing_state = read_json(paths["landing"], "landing.checkpoint")
    snapshot = provider_snapshot(provider, landing_state["claim"], run_value, jobs)
    transition = landing_owner.advance(paths["landing"], snapshot)
    if transition["action"] == "dispatch":
        dispatched = landing_owner.dispatch(paths["landing"], snapshot)
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
        transition = landing_owner.reconcile(paths["landing"], authorization["noodle"]["path"])
        if transition.get("action") == "noodle_reconcile":
            complete_noodle(authorization, paths, state, transition)
            return response(state, authorization_path, waiting_on="Noodle completion acknowledgement")
    if transition.get("classification") == "RESOLVED":
        if not finish_host(authorization, paths, state):
            return response(state, authorization_path, waiting_on="Noodle shutdown readback")
        state["phase"] = "resolved"
        save_json(state_path, state)
        return response(state, authorization_path, status="resolved",
                        details={"landing": transition})
    return response(state, authorization_path, waiting_on="fresh owner readback")


def drive(authorization_path, *, timeout=300, interval=5, sleep=time.sleep, clock=time.monotonic,
          environ=None, provider=None):
    """Observe normal waits through the same entry; never retry a refusal.

    Durable transitions and unknown-write readback remain in their existing
    owners. The bounded foreground wait creates no scheduler or new state.
    """
    require(timeout >= 0 and interval >= 0, "wait.bounds", [timeout, interval])
    deadline = clock() + timeout
    while True:
        result = run(authorization_path, environ=environ, provider=provider)
        if result.get("status") != "pending" or not result.get("next"):
            return result
        remaining = deadline - clock()
        if remaining <= 0:
            return {**result, "wait_exhausted": True}
        sleep(min(interval, remaining))


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
