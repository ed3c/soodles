"""One resumable local Issue-atom lifecycle owner.

The external authorization fixes identity and capability.  This module routes
existing Issue admission, Noodle custody, candidate publication and landing
owners; it does not replace their validation.
"""
import hashlib
import base64
import binascii
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
import tomllib
import urllib.parse
import urllib.request
import urllib.error

import candidate_publication
import atom_repair
import schema_manager
import cost_telemetry
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
LIFECYCLE_FILES = ("issue-atom", "soodles", "soodles.py", "issue_atom.py",
                   "supervisor_admission.py", "issue_admission.py", "issue_execution.py",
                   "candidate_publication.py", "provider_credential.py", "provider_transport.py",
                   "repository_binding.py", "dependency_binding.py", "github_reader.py",
                   "landing.py", "policy/runtime.lock.json", "atom_repair.py",
                   "policy/repair-policy.json", "provider_readback.py", "system_context.py",
                   "contracts/system-v1/routes.json", "contracts/system-v1/common.md",
                   "contracts/system-v1/issue-atom.md", "contracts/system-v1/candidate.md",
                   "contracts/system-v1/readback.md", "provider-readback",
                   "schema_manager.py", "policy/host-finalization.json", "cost_telemetry.py",
                   "test_manager.py")
MARKER_PREFIX = "<!-- soodles:local-atom-v1:"


class AtomRefusal(ValueError):
    def __init__(self, field, value, required="corrected_external_authorization", *,
                 owner="external-supervisor", known=None):
        super().__init__(f"issue atom: invalid {field}={value!r}")
        self.invalid = {"field": field, "value": value}
        self.required = required
        self.owner = owner
        self.known = known


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
    validate_lifecycle_owner(value)
    return value, actual


def require_clean_control_root(authorization):
    require(_git(authorization["control_root"], "status", "--porcelain", "--untracked-files=all") == "",
            "git.status", "dirty", "clean_exact_control_root")


def selected_instruction_pins(authorization):
    """Keep admission diagnostics on the atom's same-command refusal surface."""
    schema = authorization.get("schema_version")
    require(type(schema) is int and schema in (2, 3), "authorization.schema_version", schema)
    if schema == 2:
        require("instruction_pins" not in authorization, "authorization.instruction_pins", "legacy schema")
        return None
    pins = authorization.get("instruction_pins")
    prior = authorization.get("prior_publication") if "prior_atom" in authorization else None
    instruction_head = prior.get("head") if isinstance(prior, dict) else authorization["base_head"]
    require(isinstance(instruction_head, str) and SHA40.fullmatch(instruction_head),
            "authorization.instruction_head", instruction_head)
    try:
        issue_admission.resolve_instruction_context(
            authorization["control_root"], instruction_head, pins)
    except issue_admission.AdmissionRefusal as error:
        raise AtomRefusal(error.invalid["field"], error.invalid["value"]) from error
    return pins


def _validate_authorization(path, expected_digest, *, allow_advanced=False):
    source = Path(path)
    require(source.is_absolute(), "authorization.path", str(source), "absolute_external_authorization")
    value = read_json(source, "authorization")
    actual = digest_file(source)
    require(isinstance(expected_digest, str) and SHA64.fullmatch(expected_digest),
            "authorization.digest", expected_digest, "SOODLES_AUTHORIZATION_SHA256")
    require(actual == expected_digest, "authorization.digest", actual, "matching_external_digest")
    schema = value.get("schema_version")
    require(type(schema) is int and schema in (2, 3), "authorization.schema_version", schema)
    expected_fields = (AUTH_FIELDS | {"landing_owner"}
                       | ({"instruction_pins"} if schema == 3 else set()))
    amendment_fields = {"prior_publication", "prior_atom"}
    expected_fields |= {"failure_context"} if "failure_context" in value else set()
    expected_fields |= {"lifecycle_owner"} if "lifecycle_owner" in value else set()
    require(set(value) in (expected_fields, expected_fields | {"prior_publication"},
                           expected_fields | amendment_fields),
            "authorization.fields", sorted(value),
            "external_authorization_with_pinned_host_and_landing_owner")
    require(value["owner"] == "external-supervisor",
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
    selected_instruction_pins(value)
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
    if "prior_publication" in value:
        require("number" in issue, "authorization.issue.number", None,
                "existing_issue_for_candidate_amendment")
        if "prior_atom" in value:
            validate_prior_atom_ref(value["prior_atom"], root)
        try:
            candidate_publication.validate_amendment_prior(
                value["prior_publication"], repository,
                repository + "#" + str(issue["number"]), issue["number"])
        except candidate_publication.PublicationRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              "exact_prior_publication") from error
    validate_authorization_failure(value)
    config_digest = value["host_config_sha256"]
    require(config_digest is None or isinstance(config_digest, str) and SHA64.fullmatch(config_digest),
            "authorization.host_config_sha256", config_digest)
    if "prior_atom" in value:
        require(config_digest == prior_host_config(value["prior_atom"], root)["original_sha256"],
                "amendment.host_config_sha256", config_digest,
                "original_host_configuration_after_recovery")
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


def validate_prior_atom_ref(ref, root):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"},
            "amendment.prior_atom", ref, "selected_previous_atom")
    path, digest = ref["path"], ref["sha256"]
    require(isinstance(path, str) and Path(path).is_absolute()
            and not Path(path).is_symlink()
            and Path(path).is_file()
            and not Path(path).resolve().is_relative_to(Path(root).resolve()),
            "amendment.prior_atom.path", path, "external_previous_authorization")
    require(isinstance(digest, str) and SHA64.fullmatch(digest)
            and digest_file(path) == digest,
            "amendment.prior_atom.sha256", digest, "unchanged_previous_authorization")


def validate_authorization_failure(authorization):
    if "failure_context" not in authorization:
        return
    require("prior_atom" in authorization and "prior_publication" in authorization,
            "failure_context.lineage", "missing", "original_correction_lineage")
    prior = authorization["prior_publication"]
    try:
        issue_admission.validate_failure_context(
            authorization["failure_context"], authorization["repository"],
            authorization["issue"]["number"], prior["head"], authorization["workflow"], prior["pr"]["number"])
        issue_admission.validate_failure_logs(authorization["failure_context"], authorization["control_root"])
    except issue_admission.AdmissionRefusal as error:
        raise AtomRefusal(error.invalid["field"], error.invalid["value"], "exact_failed_ci_evidence") from error


def validate_correction_lineage(authorization, reference, state):
    """Count immutable automatic edges; leave every ancestor's repair ledger untouched."""
    root = authorization["control_root"]
    current = read_json(reference["path"], "correction.authorization")
    authorization, _ = scope_projection(current, state, artifact_paths(reference["path"]))
    ref, checkpoint = reference, state
    seen, heads = set(), set()
    count = 0
    identity = ("repository", "control_root", "base_head", "task", "noodle", "carrier",
                "workflow", "landing_owner", "host_config_sha256")
    contract = issue_admission.parse_contract(authorization["issue"]["body"])
    publication = state.get("publication")
    require(isinstance(publication, dict), "correction.publication", "missing")
    number = state.get("issue", {}).get("number")
    while True:
        key = str(Path(ref["path"]).resolve())
        require(key not in seen, "correction.lineage.cycle", key, "original_immutable_lineage")
        seen.add(key)
        validate_prior_atom_ref(ref, root)
        require(read_json(ref["path"], "correction.authorization") == current,
                "correction.lineage.authorization", "changed", "original_immutable_lineage")
        paths = artifact_paths(ref["path"])
        effective, paths = scope_projection(current, checkpoint, paths)
        resumed_lifecycle(current, checkpoint)
        require(all(effective.get(k) == authorization.get(k) for k in identity)
                and effective["issue"]["title"] == authorization["issue"]["title"]
                and issue_admission.parse_contract(effective["issue"]["body"]) == contract
                and effective["issue"].get("number", number) == number,
                "correction.lineage.scope", "changed", "unchanged_original_task_scope_and_runtime")
        published = checkpoint.get("publication")
        require(checkpoint.get("authorization_sha256") == ref["sha256"]
                and checkpoint.get("phase") == "ci"
                and checkpoint.get("issue", {}).get("number") == number
                and isinstance(published, dict)
                and all(published.get(k) == publication.get(k) for k in ("repository", "subject", "branch", "pr"))
                and not checkpoint.get("landing_activation") and not paths["landing"].exists(),
                "correction.lineage.state", "mismatch", "exact_prelanding_failed_candidate")
        try:
            candidate_publication.validate_amendment_prior(published, current["repository"],
                current["repository"] + "#" + str(number), number)
        except candidate_publication.PublicationRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              "exact_parent_publication") from error
        require(published["head"] not in heads, "correction.lineage.head", published["head"],
                "distinct_failed_candidate_heads")
        heads.add(published["head"])
        repair = checkpoint.get("repair")
        require(repair is None or isinstance(repair, dict), "correction.repair_history", "invalid")
        history = repair.get("history", []) if repair is not None else []
        require(isinstance(history, list) and all(isinstance(entry, dict)
                and entry.get("status") == "confirmed" for entry in history),
                "correction.repair_history", "unresolved", "original_repair_owner_readback_without_retry")
        for field, status in (("noodle_start", "started"), ("noodle_bootstrap", "complete"),
                              ("prior_host_recovery", "restored")):
            effect = checkpoint.get(field)
            require(effect is None or isinstance(effect, dict) and effect.get("status") == status,
                    "correction.lineage.effects", field, "original_effect_owner_readback")
        require(not checkpoint.get("landing_resume") and not checkpoint.get("noodle_reconciliation"),
                "correction.lineage.effects", "postlanding effect", "original_effect_owner_readback")
        writes = checkpoint.get("writes", {})
        require(isinstance(writes, dict), "correction.lineage.effects", "invalid")
        for name, effect in writes.items():
            confirmed = isinstance(effect, dict) and (
                (name == "issue_create" and effect == {"status": "offered"})
                or (name in {"publication_branch_push", "publication_pr_create"}
                    and effect == {"head": published["head"], "status": "offered"})
                or (name == "candidate_amendment" and effect == {
                    "old_head": current.get("prior_publication", {}).get("head"),
                    "new_head": published["head"], "pr": published["pr"]["number"], "status": "offered"})
                or (name == "issue_scope" and checkpoint.get("scope_amendment", {}).get("status") == "released"
                    and effect.get("status") == "observed"
                    and effect.get("selection_sha256") == checkpoint["scope_amendment"]["selection"]["sha256"]
                    and effect.get("body_sha256") == digest_bytes(effective["issue"]["body"].encode())))
            require(confirmed, "correction.lineage.effects", name, "original_effect_owner_readback")
        parent = current.get("prior_atom")
        if parent is None:
            require("prior_publication" not in current and "failure_context" not in current,
                    "correction.lineage.external", "unbound predecessor", "external_lineage_owner_review")
            break
        require("failure_context" in current, "correction.lineage.external", "nonautomatic predecessor",
                "external_lineage_owner_review")
        validate_authorization_failure(current)
        validate_prior_atom_ref(parent, root)
        parent_auth = read_json(parent["path"], "correction.parent")
        parent_paths = artifact_paths(parent["path"])
        parent_state = read_json(parent_paths["state"], "correction.parent_state")
        require(current.get("lifecycle_owner") == resumed_lifecycle(parent_auth, parent_state).get("lifecycle_owner"),
                "correction.lineage.runtime_edge", "changed", "parent_selected_runtime_at_child_admission")
        require(current["prior_publication"] == parent_state.get("publication"),
                "correction.lineage.parent", "mismatch", "exact_parent_publication")
        parent_effective, _ = scope_projection(parent_auth, parent_state, parent_paths)
        expected_body = parent_effective["issue"]["body"]
        if "number" not in parent_effective["issue"]:
            expected_body = expected_body.rstrip() + "\n\n" + marker(parent["sha256"]) + "\n"
        require(current["issue"]["body"] == expected_body,
                "correction.lineage.body", "changed", "unchanged_original_issue")
        target = parent_paths["directory"] / "correction"
        require(Path(ref["path"]).resolve() == target / "prepared/authorization.json",
                "correction.lineage.edge", "external predecessor", "original_automatic_preparation")
        # The committed producer receipt binds the exact parent, selection and child.
        require((target / "prepared").is_dir(), "correction.lineage.prepared", "missing",
                "original_committed_preparation")
        try:
            receipt = supervisor_admission._correction_readback(target, parent_auth, parent)
        except issue_admission.AdmissionRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              error.next["required"][0], owner=error.next["owner"]) from error
        require(receipt["authorization"] == ref, "correction.lineage.binding", "changed")
        count += 1
        current, ref, checkpoint = parent_auth, parent, parent_state
    return count


def prior_host_config(ref, root):
    """Derive the host state that the original lifecycle must restore."""
    validate_prior_atom_ref(ref, root)
    prior_path = Path(ref["path"])
    old = read_json(prior_path, "amendment.prior_authorization")
    state = read_json(artifact_paths(prior_path)["state"], "amendment.prior_state")
    start = state.get("noodle_start")
    require(old.get("control_root") == str(Path(root).resolve())
            and state.get("authorization_sha256") == ref["sha256"]
            and state.get("phase") == "ci"
            and isinstance(start, dict) and start.get("status") == "started"
            and isinstance(start.get("config_sha256"), str)
            and SHA64.fullmatch(start["config_sha256"]),
            "amendment.prior_host", "mismatch", "exact_previous_host_owner")
    original = start.get("original_config")
    require(original is None or isinstance(original, str),
            "amendment.prior_host.original", original)
    try:
        raw = None if original is None else base64.b64decode(original, validate=True)
    except (ValueError, TypeError, binascii.Error) as error:
        raise AtomRefusal("amendment.prior_host.original", type(error).__name__) from error
    digest = None if raw is None else digest_bytes(raw)
    require(old.get("host_config_sha256") == digest,
            "amendment.prior_host.original", digest, "original_host_configuration")
    return {"original_sha256": digest, "installed_sha256": start["config_sha256"],
            "restored": start.get("restored") is True}


def validate_lifecycle_owner(authorization, *, executing=False):
    """Validate supervisor-selected runtime bytes separately from the landing judge."""
    spec = authorization.get("lifecycle_owner")
    if spec is None:
        return Path(authorization["control_root"]) / "issue-atom"
    require(isinstance(spec, dict) and set(spec) == {"path", "sha256", "source_sha256"},
            "authorization.lifecycle_owner", spec, "immutable_external_lifecycle_owner")
    raw_path = Path(spec["path"])
    path = raw_path.resolve()
    root = Path(authorization["control_root"]).resolve()
    require(raw_path.is_absolute() and raw_path == path and path.name == "issue-atom"
            and not path.is_relative_to(root)
            and path.parent != Path(authorization["landing_owner"]["path"]).resolve().parent,
            "authorization.lifecycle_owner.path", str(path), "separate_external_lifecycle_owner")
    atom_source = path.parent / "issue_atom.py"
    require(atom_source.is_file() and not atom_source.is_symlink()
            and atom_source.resolve() == atom_source,
            "authorization.lifecycle_owner.file", "issue_atom.py", "fixed_regular_runtime_files")
    hashes = {}
    # Old immutable descriptors retain their original exact source closure.
    names = LIFECYCLE_FILES
    if not (path.parent / "cost_telemetry.py").exists():
        require(b"import cost_telemetry" not in (path.parent / "issue_atom.py").read_bytes(),
                "authorization.lifecycle_owner.file", "cost_telemetry.py")
        names = tuple(name for name in names if name != "cost_telemetry.py")
    if not (path.parent / "test_manager.py").exists():
        cost_source = path.parent / "cost_telemetry.py"
        require(not cost_source.exists() or b"from test_manager import" not in cost_source.read_bytes(),
                "authorization.lifecycle_owner.file", "test_manager.py")
        names = tuple(name for name in names if name != "test_manager.py")
    for name in names:
        source = path.parent / name
        require(source.is_file() and not source.is_symlink() and source.resolve() == source,
                "authorization.lifecycle_owner.file", name, "fixed_regular_runtime_files")
        hashes[name] = digest_file(source)
    require(os.access(path, os.X_OK) and os.access(path.parent / "soodles", os.X_OK)
            and hashes["issue-atom"] == spec["sha256"],
            "authorization.lifecycle_owner.sha256", "mismatch", "unchanged_external_lifecycle_owner")
    actual = digest_bytes(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode())
    require(actual == spec["source_sha256"], "authorization.lifecycle_owner.source_sha256",
            actual, "unchanged_external_lifecycle_owner")
    if executing:
        require(Path(__file__).resolve() == path.parent / "issue_atom.py",
                "authorization.lifecycle_owner.execution", str(Path(__file__).resolve()),
                "execute_selected_prepared_continuation")
    return path


def resumed_lifecycle(authorization, state):
    resume = state.get("lifecycle_resume")
    if resume is None:
        return authorization
    require(isinstance(state.get("authorization_sha256"), str)
            and SHA64.fullmatch(state["authorization_sha256"]),
            "lifecycle.resume.authorization", "missing", "original_authorization_digest")
    chain, seen = [], set()
    while resume is not None:
        require(isinstance(resume, dict) and set(resume) in (
                    {"from", "to", "authorization_sha256"},
                    {"from", "to", "authorization_sha256", "previous"})
                and id(resume) not in seen
                and resume["authorization_sha256"] == state.get("authorization_sha256"),
                "lifecycle.resume.binding", "changed", "original_lifecycle_resume")
        seen.add(id(resume))
        chain.append(resume)
        resume = resume.get("previous")
    selected = authorization
    identities = [authorization.get("lifecycle_owner")]
    validate_lifecycle_owner(authorization)
    for item in reversed(chain):
        require(item["from"] == selected.get("lifecycle_owner")
                and item["to"] not in identities,
                "lifecycle.resume.chain", "changed", "continuous_external_lifecycle_selections")
        selected = {**authorization, "lifecycle_owner": item["to"]}
        try:
            validate_lifecycle_owner(selected)
        except AtomRefusal as error:
            raise AtomRefusal("lifecycle.resume.intent",
                              error.invalid,
                              "original_lifecycle_resume") from error
        identities.append(item["to"])
    return selected


def postwrite_lifecycle(authorization, state, paths, *, allow_resolved=False):
    """Bind the stopped original writer and confirmed landing without rewriting either."""
    authorization, paths = scope_projection(authorization, state, paths)
    require(state.get("phase") in ({"landing", "resolved"} if allow_resolved else {"landing"}),
            "lifecycle.resume.phase", state.get("phase"),
            "original_postwrite_checkpoint")
    root = Path(authorization["control_root"])
    binding = issue_admission.load_external_envelope(paths["envelope"], state["envelope_sha256"], root)
    execution = binding["execution"]
    claim = read_json(paths["claim"], "publication.claim")
    number = state["issue"]["number"]
    body = authorized_issue_body(authorization, state["authorization_sha256"])
    require(binding["repository"] == authorization["repository"]
            and binding["issue"] == number
            and binding["base_head"] == authorization["base_head"]
            and binding["body_sha256"] == digest_bytes(body.encode())
            and execution["control_root"] == str(root)
            and claim.get("schema_version") == 1 and claim.get("owner") == "Noodle"
            and claim.get("authorizes_provider_write") is False and claim.get("authorizes_landing") is False
            and claim.get("repository") == binding["repository"]
            and claim.get("subject") == binding["repository"] + "#" + str(number)
            and claim.get("base_head") == binding["base_head"]
            and claim.get("order_id") == execution["order_id"]
            and claim.get("stage_index") == execution["stage_index"]
            and claim.get("worktree_name") == execution["worktree"]
            and claim.get("worktree_path") == str(root / ".worktrees" / execution["worktree"]),
            "lifecycle.resume.custody", "changed", "original_native_claim_and_envelope")
    publication = state["publication"]
    if state.get("publication_source") is not None:
        require(state["publication_source"].get("claim_sha256") == atom_repair.digest(claim),
                "lifecycle.resume.claim", "changed", "original_native_claim")
    checkpoint_path = paths["landing"]
    if state.get("landing_activation"):
        activation = state["landing_activation"]
        manifest = Path(activation["manifest"])
        require(digest_file(manifest) == activation["sha256"],
                "lifecycle.resume.activation", "changed", "original_activation")
        checkpoint_path = manifest.parent / "checkpoint.json"
    checkpoint = read_json(checkpoint_path, "landing.checkpoint")
    landed = checkpoint.get("claim", {})
    require(checkpoint.get("phase") in ({"awaiting_reconcile", "reconciling", "resolved"}
            if allow_resolved else {"awaiting_reconcile", "reconciling"})
            and checkpoint.get("writes_offered") == ["merge", "close"]
            and checkpoint.get("merge_sha") and checkpoint.get("issue_closed_at")
            and all(landed.get(key) == claim.get(key) for key in
                    ("repository", "head", "tree", "base_head"))
            and landed.get("issue") == number and landed.get("pr") == publication["pr"]["number"]
            and landed.get("publication_branch") == publication["branch"]
            and landed.get("worktree") == execution["worktree"]
            and landed.get("control_root") == str(root)
            and landed.get("execution_envelope") == {
                "path": str(paths["envelope"]), "sha256": state["envelope_sha256"]},
            "lifecycle.resume.landing", "unconfirmed or changed", "confirmed_original_merge_and_closure")
    # This checks the canonical prompt/stage and all sessions without changing them.
    require_available_owner(authorization, paths, state)
    owner = issue_execution.read_owner(binding)
    order = owner["state"]["orders"].get(execution["order_id"])
    if order is None:
        completion = issue_execution.completed_original_order(binding, owner, claim)
        sessions = [item["session_id"] for item in completion["quiescent_sessions"]]
        require(sessions == [claim.get("session_id")], "lifecycle.resume.session", sessions)
    else:
        attempts = order["stages"][execution["stage_index"]]["attempts"]
        require(any(attempt.get("attempt_id") == claim.get("attempt_id")
                    and attempt.get("session_id") == claim.get("session_id")
                    and attempt.get("worktree_name") == claim.get("worktree_name")
                    for attempt in attempts), "lifecycle.resume.attempt", "changed",
                "original_native_attempt")
    return binding, owner


def resume(authorization_path, selected_owner, selected_digest, *, environ=None):
    """Select one immutable runtime for a stopped post-write original atom."""
    environ = os.environ if environ is None else environ
    paths = artifact_paths(authorization_path)
    with Path(authorization_path).open("rb") as auth_lock:
        try:
            fcntl.flock(auth_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("authorization.busy", str(authorization_path),
                              "current_same_entry_owner_readback") from None
        authorization, auth_digest = validate_authorization(
            authorization_path, environ.get("SOODLES_AUTHORIZATION_SHA256"), allow_advanced=True)
        descriptor = Path(selected_owner)
        require(descriptor.is_absolute() and not descriptor.resolve().is_relative_to(
                    Path(authorization["control_root"]).resolve())
                and digest_file(descriptor) == selected_digest,
                "lifecycle.resume.selection", "changed", "selected_external_lifecycle_owner")
        spec = read_json(descriptor, "lifecycle.resume.owner")
        selected = {**authorization, "lifecycle_owner": spec}
        validate_lifecycle_owner(selected, executing=True)
        runtime = Path(authorization["control_root"]) / ".noodle"
        with (runtime / "issue-atom.lock").open("a+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise AtomRefusal("noodle.atom_entry", "busy", "current_same_entry_owner_readback") from None
            state = read_json(paths["state"], "state")
            require(state.get("schema_version") == 1 and state.get("authorization_sha256") == auth_digest,
                    "state.authorization", "changed", "original_lifecycle_checkpoint")
            current = resumed_lifecycle(authorization, state)
            previous = state.get("lifecycle_resume")
            intent = {"from": current.get("lifecycle_owner"), "to": spec,
                      "authorization_sha256": auth_digest}
            if previous is not None:
                intent["previous"] = previous
            if current.get("lifecycle_owner") != spec:
                scoped = state.get("scope_amendment") is not None and state.get("phase") == "execution"
                startup = (not scoped and state.get("phase") == "execution"
                           and {"prior_atom", "failure_context"} <= authorization.keys())
                if startup:
                    recovery, binding, observed_owner = correction_start_selection(
                        authorization_path, authorization, state, paths, spec)
                elif scoped:
                    _, effective_paths = scope_projection(authorization, state, paths)
                    binding = issue_admission.load_external_envelope(
                        effective_paths["envelope"], state["envelope_sha256"], authorization["control_root"])
                    observed_owner = issue_execution.read_owner(binding)
                    stage = observed_owner["state"]["orders"][binding["execution"]["order_id"]]["stages"][0]
                    require(not any(attempt.get("status") in {"launching", "running"}
                                    for attempt in stage.get("attempts", [])),
                            "scope.resume.writer", "active", "quiescent_original_scope_writer")
                else:
                    binding, observed_owner = postwrite_lifecycle(authorization, state, paths)
                with (runtime / "noodle.lock").open("a+b") as native:
                    try:
                        fcntl.flock(native, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        require(scoped and "scope_release" not in state
                                and noodle_process_argv(authorization, state["noodle_start"])[-2:]
                                == ["--mode", "manual"]
                                and observe_prior_loop(authorization, state) == "running",
                                "lifecycle.resume.noodle", "running", "quiescent_manual_scope_owner")
                    owner = issue_execution.read_owner(binding)
                    require(owner == observed_owner, "lifecycle.resume.owner", "changed",
                            "fresh_canonical_checkpoint")
                    for order_id, order in owner["state"]["orders"].items():
                        if order_id == "schedule" and native_idle_schedule(
                                order, binding["execution"]["carrier"]["codex"]["model"]):
                            continue
                        if scoped and order_id == binding["execution"]["order_id"]:
                            require(all(attempt.get("status") in {"completed", "failed", "cancelled"}
                                        for stage in order["stages"] for attempt in stage.get("attempts", [])),
                                    "scope.resume.attempts", "active", "quiescent_original_scope_writer")
                            continue
                        issue_execution.quiescent_order(
                            {"execution": {"control_root": str(runtime.parent), "order_id": order_id}}, owner)
                    for process in sorted((runtime / "sessions").glob("*/process.json")):
                        issue_execution._absent_process(process.parent, process.parent.name)
                    if startup:
                        path = paths["directory"] / "correction-start-recovery.json"
                        if path.exists():
                            require(read_json(path, "correction.start.record") == recovery,
                                    "correction.start.selection", "changed", "original_startup_recovery_record")
                        else:
                            save_json(path, recovery, fresh=True)
                        state["correction_start_recovery"] = {"record": {"path": str(path), "sha256": digest_file(path)}}
                    state["lifecycle_resume"] = intent
                    resumed_lifecycle(authorization, state)
                    if startup:
                        repair_controller(authorization, state, paths, authorization_path=authorization_path)
                    resume_host_finalization(authorization, state)
                    save_json(paths["state"], state)
    return {"owner": "soodles.issue-atom", "status": "resumed", "continuation_state": "ready",
            "authorizes_landing": False,
            "next": {"argv": same_command(authorization_path),
                     "environment": {"SOODLES_AUTHORIZATION_SHA256": auth_digest}}}


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

    def resume(self, checkpoint, claim_path):
        return self.call("resume", checkpoint, claim_path)


def external_landing_activation(authorization, state, paths, environ,
                                claim, publication, run_value):
    """Adopt one supervisor-pinned, pre-write activation without changing authorization."""
    selected = state.get("landing_activation")
    if selected is None:
        manifest_path = environ.get("SOODLES_LANDING_ACTIVATION")
        expected = environ.get("SOODLES_LANDING_ACTIVATION_SHA256")
        if manifest_path is None and expected is None:
            return None
        require(isinstance(manifest_path, str) and Path(manifest_path).is_absolute()
                and isinstance(expected, str) and SHA64.fullmatch(expected),
                "landing_activation.input", [manifest_path, expected],
                "pinned_external_activation")
        refusals = sorted(paths["directory"].glob("landing-start-*.json"))
        require(len(refusals) == 1, "landing_activation.prior_refusal", len(refusals),
                "one_recorded_prewrite_owner_refusal")
        selected = {"manifest": str(Path(manifest_path).resolve()), "sha256": expected,
                    "refusal_sha256": digest_file(refusals[0])}
    else:
        require(environ.get("SOODLES_LANDING_ACTIVATION") in
                (None, selected["manifest"])
                and environ.get("SOODLES_LANDING_ACTIVATION_SHA256") in
                (None, selected["sha256"]),
                "landing_activation.reselection", "changed", "original_activation")
    manifest_path = Path(selected["manifest"])
    refusals = sorted(paths["directory"].glob("landing-start-*.json"))
    require(len(refusals) == 1 and digest_file(refusals[0]) == selected["refusal_sha256"],
            "landing_activation.prior_refusal", len(refusals),
            "unchanged_prewrite_owner_refusal")
    refusal = read_json(refusals[0], "landing_activation.prior_refusal")
    try:
        rejected = json.loads(refusal["stdout"])
    except (KeyError, TypeError, ValueError) as error:
        raise AtomRefusal("landing_activation.prior_refusal", type(error).__name__,
                          "typed_owner_refusal") from error
    require(refusal.get("exit_status") != 0
            and isinstance(refusal.get("argv"), list)
            and len(refusal["argv"]) >= 7
            and refusal["argv"][2] == authorization["landing_owner"]["path"]
            and refusal["argv"][3:5] == ["landing", "start"]
            and refusal["argv"][-1] == str(paths["directory"] / "landing.json")
            and rejected.get("owner") == "landing.start"
            and rejected.get("status") == "refused"
            and isinstance(rejected.get("invalid"), dict)
            and "request" not in rejected,
            "landing_activation.prior_refusal", rejected, "prewrite_pinned_owner_refusal")
    root = Path(authorization["control_root"]).resolve()
    require(not manifest_path.is_relative_to(root)
            and not manifest_path.is_relative_to(Path(__file__).resolve().parent),
            "landing_activation.path", str(manifest_path), "external_supervisor_package")
    require(digest_file(manifest_path) == selected["sha256"],
            "landing_activation.sha256", selected["sha256"], "unchanged_activation_manifest")
    manifest = read_json(manifest_path, "landing_activation.manifest")
    require(set(manifest) == {"schema", "publisher_root", "publisher_verifier_sha256",
                              "route", "claim_sha256", "readback_sha256", "authorizes_landing"}
            and manifest["schema"] == 1 and manifest["route"] == "local"
            and manifest["authorizes_landing"] is False,
            "landing_activation.manifest", manifest, "terminal_local_activation")
    directory = manifest_path.parent
    claim_path, checkpoint = directory / "claim.json", directory / "checkpoint.json"
    require(digest_file(claim_path) == manifest["claim_sha256"]
            and digest_file(directory / "readback.json") == manifest["readback_sha256"],
            "landing_activation.package", str(directory), "unchanged_activation_inputs")
    external_claim = read_json(claim_path, "landing_activation.claim")
    expected_claim = {
        "repository": authorization["repository"], "issue": state["issue"]["number"],
        "pr": publication["pr"]["number"], "head": claim["head"],
        "tree": claim["tree"], "base_head": claim["base_head"],
        "run_id": run_value["id"], "run_attempt": run_value["run_attempt"],
        "worktree": claim["worktree_name"], "publication_branch": publication["branch"],
        "control_root": str(root),
        "verifier_sha256": manifest["publisher_verifier_sha256"],
        "execution_envelope": {"path": str(paths["envelope"]),
                               "sha256": state["envelope_sha256"]},
    }
    require(external_claim == expected_claim,
            "landing_activation.claim", external_claim, "same_terminal_candidate_and_order")
    publisher_root = Path(manifest["publisher_root"]).resolve()
    publisher_cli = publisher_root / "soodles.py"
    publisher = {**authorization, "landing_owner": {
        "path": str(publisher_cli), "sha256": digest_file(publisher_cli),
        "verifier_sha256": manifest["publisher_verifier_sha256"],
    }}
    validate_landing_owner(publisher)
    require(checkpoint.is_file(), "landing_activation.checkpoint", str(checkpoint),
            "prewrite_landing_checkpoint")
    checkpoint_state = read_json(checkpoint, "landing_activation.checkpoint")
    allowed_claims = [external_claim]
    if state.get("landing_resume"):
        allowed_claims.append({**external_claim,
                               "verifier_sha256": state["landing_resume"]["verifier_sha256"]})
    require(checkpoint_state.get("claim") in allowed_claims,
            "landing_activation.checkpoint.claim", "mismatch", "matching_activation_claim")
    if state.get("landing_activation") is None:
        require(state["phase"] == "ci" and not paths["landing"].exists()
                and checkpoint_state.get("schema") == 2
                and checkpoint_state.get("phase") == "admitted"
                and checkpoint_state.get("writes_offered") == []
                and checkpoint_state.get("classification") is None,
                "landing_activation.prewrite", checkpoint_state.get("phase"),
                "prewrite_activation_only")
        state["landing_activation"] = selected
        state["phase"] = "landing"
        save_json(paths["state"], state)
    paths["landing"] = checkpoint
    return publisher


def external_landing_resume(authorization, state, paths, environ):
    """Bind a corrected external publisher after both provider writes were confirmed."""
    selected = state.get("landing_resume")
    if selected is None:
        descriptor = environ.get("SOODLES_LANDING_RESUME_OWNER")
        expected = environ.get("SOODLES_LANDING_RESUME_OWNER_SHA256")
        if descriptor is None and expected is None:
            return None
        require(isinstance(descriptor, str) and Path(descriptor).is_absolute()
                and isinstance(expected, str) and SHA64.fullmatch(expected),
                "landing_resume.input", [descriptor, expected],
                "pinned_external_postwrite_owner")
        selected = {"descriptor": str(Path(descriptor).resolve()), "sha256": expected,
                    "status": "new"}
    else:
        require(environ.get("SOODLES_LANDING_RESUME_OWNER") in
                (None, selected["descriptor"])
                and environ.get("SOODLES_LANDING_RESUME_OWNER_SHA256") in
                (None, selected["sha256"]),
                "landing_resume.reselection", "changed", "original_postwrite_owner")
    source = Path(selected["descriptor"])
    root = Path(authorization["control_root"]).resolve()
    require(not source.is_relative_to(root)
            and not source.is_relative_to(Path(__file__).resolve().parent),
            "landing_resume.path", str(source), "external_supervisor_selection")
    require(digest_file(source) == selected["sha256"],
            "landing_resume.sha256", selected["sha256"], "unchanged_postwrite_selection")
    spec = read_json(source, "landing_resume.descriptor")
    corrected = {**authorization, "landing_owner": spec}
    validate_landing_owner(corrected)
    require(state["phase"] in {"landing", "resolved"},
            "landing_resume.phase", state["phase"], "original_landing_checkpoint")
    checkpoint = read_json(paths["landing"], "landing.checkpoint")
    original_path = (paths["landing"].parent / "claim.json" if state.get("landing_activation")
                     else paths["directory"] / "landing-claim.json")
    original = read_json(original_path, "landing.original_claim")
    require(isinstance(checkpoint.get("claim"), dict)
            and {key: value for key, value in checkpoint["claim"].items()
                 if key != "verifier_sha256"}
                == {key: value for key, value in original.items()
                    if key != "verifier_sha256"}
            and checkpoint.get("writes_offered") == ["merge", "close"]
            and checkpoint.get("merge_sha") and checkpoint.get("issue_closed_at")
            and checkpoint.get("classification") in {None, "RESOLVED"},
            "landing_resume.checkpoint", checkpoint.get("phase"),
            "confirmed_postwrite_original_claim")
    target = spec["verifier_sha256"]
    require(target != original["verifier_sha256"],
            "landing_resume.verifier", target, "corrected_external_verifier")
    if selected["status"] == "new":
        require(checkpoint["claim"] == original
                and checkpoint.get("phase") in {"awaiting_reconcile", "reconciling"},
                "landing_resume.prewrite", checkpoint.get("phase"),
                "unreconciled_confirmed_provider_closure")
        selected["verifier_sha256"] = target
        selected["status"] = "offered"
        state["landing_resume"] = selected
        save_json(paths["state"], state)
        claim_path = paths["directory"] / "landing-resume-claim.json"
        save_json(claim_path, {**original, "verifier_sha256": target}, fresh=True)
        try:
            LandingOwner(corrected, paths["directory"]).resume(paths["landing"], claim_path)
        except subprocess.TimeoutExpired as error:
            raise AtomRefusal("landing_resume.outcome", "unknown",
                              "current_checkpoint_readback_without_retry") from error
        checkpoint = read_json(paths["landing"], "landing.checkpoint")
    expected_claim = {**original, "verifier_sha256": target}
    if checkpoint["claim"] != expected_claim:
        raise AtomRefusal("landing_resume.outcome", "unknown",
                          "current_checkpoint_readback_without_retry")
    require(original["verifier_sha256"] in checkpoint.get("prior_verifiers", [])
            and checkpoint.get("phase") in {"awaiting_reconcile", "reconciling", "resolved"},
            "landing_resume.adoption", checkpoint.get("phase"),
            "same_postwrite_resumption")
    if selected["status"] != "adopted":
        selected["status"] = "adopted"
        state["landing_resume"] = selected
        save_json(paths["state"], state)
    return corrected


class GitHubProvider(candidate_publication.GitHubProvider):
    def repair_pull(self, number, timeout):
        from provider_readback import bounded_pull
        return bounded_pull(self.repository, number, self.token, timeout)

    def issues(self):
        return self.request("GET", "/issues?state=all&sort=created&direction=desc&per_page=100")

    def create_issue(self, title, body):
        try:
            return self.request("POST", "/issues", {"title": title, "body": body}, mutation=True)
        except candidate_publication.ProviderMutationUnknown as error:
            raise MutationUnknown(str(error)) from None

    def update_issue_body(self, number, body):
        try:
            return self.request("PATCH", f"/issues/{number}", {"body": body}, mutation=True)
        except candidate_publication.ProviderMutationUnknown as error:
            raise MutationUnknown(str(error)) from None

    def workflow_runs(self, head):
        query = urllib.parse.urlencode({"head_sha": head, "event": "pull_request", "per_page": 100})
        return self.request("GET", "/actions/runs?" + query)

    def jobs(self, run_id):
        return self.request("GET", f"/actions/runs/{run_id}/jobs?per_page=100")

    def job_log(self, job_id):
        """Read diagnostic bytes; signed redirects never receive the installation token."""
        url = self.api + f"/actions/jobs/{job_id}/logs"
        diagnostic = {"job_id": job_id, "raw": None, "gap": None}
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "soodles-candidate-publication"})
        opener = urllib.request.build_opener(candidate_publication.NoRedirect())
        try:
            for redirect in range(2):
                try:
                    response = opener.open(request, timeout=30)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    if response.url != request.full_url:
                        diagnostic["gap"] = "unexpected_log_response_url"
                        break
                    if response.code == 302 and redirect == 0:
                        location = response.headers.get("Location", "")
                        parsed = urllib.parse.urlsplit(location)
                        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                            diagnostic["gap"] = "invalid_log_redirect"
                            break
                        request = urllib.request.Request(location, headers={"User-Agent": "soodles-candidate-publication"})
                        continue
                    if response.code != 200:
                        diagnostic["gap"] = f"log_http_status_{response.code}"
                        break
                    diagnostic["raw"] = response.read()
                    break
        except (urllib.error.URLError, OSError, ValueError, UnicodeError) as error:
            diagnostic["gap"] = "log_unavailable_" + type(error).__name__
        return diagnostic

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


def authorized_issue_body(authorization, authorization_digest):
    body = authorization["issue"]["body"]
    if "number" in authorization["issue"]:
        return body
    return body.rstrip() + "\n\n" + marker(authorization_digest) + "\n"


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
    expected_body = authorized_issue_body(authorization, authorization_digest)
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


def readmit_issue_base(provider, authorization, state, paths):
    """Rebind one failed PR's Issue to a freshly admitted descendant base.

    A fresh control root uses the existing prior-publication path. Old Noodle
    orders and immutable authorizations remain historical, never transplanted.
    """
    if "prior_publication" not in authorization or "prior_atom" in authorization:
        return
    selected = authorization["issue"]
    current = provider.issue(selected["number"])
    require(isinstance(current, dict) and current.get("number") == selected["number"]
            and current.get("title") == selected["title"]
            and current.get("html_url") == f'https://github.com/{authorization["repository"]}/issues/{selected["number"]}'
            and "pull_request" not in current,
            "readmission.issue.identity", selected["number"], "exact_provider_issue")
    intent = state["writes"].get("issue_base")
    if current.get("body") == selected["body"]:
        if intent is not None:
            require(intent.get("body_sha256") == issue_admission.body_digest(selected["body"])
                    and intent.get("base_head") == authorization["base_head"]
                    and intent.get("prior_head") == authorization["prior_publication"]["head"]
                    and intent.get("status") in {"offered", "observed"},
                    "readmission.issue.intent", intent, "unchanged_base_readmission")
            if intent["status"] == "offered":
                state["writes"]["issue_base"] = {**intent, "status": "observed"}
                save_json(paths["state"], state)
        return
    require(current.get("state") == "open" and state["phase"] == "issue"
            and state.get("issue") is None and state.get("publication") is None
            and not paths["envelope"].exists() and not paths["landing"].exists(),
            "readmission.issue.phase", state["phase"], "fresh_pre_execution_admission")
    require(intent is None, "readmission.issue.outcome", "unknown",
            "fresh_provider_issue_readback_without_retry")
    old = issue_admission.parse_contract(current.get("body"))
    new = issue_admission.parse_contract(selected["body"])
    require(old.get("schema") == new.get("schema") == 3,
            "readmission.issue.schema", new.get("schema"), "schema_three_base_readmission")
    previous, target = old["base_head"], authorization["base_head"]
    require(previous != target and new["base_head"] == target,
            "readmission.issue.base", [previous, target], "changed_admitted_base")
    root = Path(authorization["control_root"])
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", previous, target],
                              cwd=root, capture_output=True, timeout=30)
    require(ancestor.returncode == 0, "readmission.issue.ancestry", [previous, target],
            "descendant_provider_base")
    pins = []
    for pin in old["frozen_paths"]:
        if pin["revision"] == "base":
            require(digest_bytes(issue_admission.git_bytes(root, previous, pin["path"])) == pin["sha256"],
                    "readmission.issue.previous_pin", pin["path"], "exact_previous_base_pin")
            pin = {**pin, "sha256": digest_bytes(issue_admission.git_bytes(root, target, pin["path"]))}
        pins.append(pin)
    require(new == {**old, "base_head": target, "frozen_paths": pins},
            "readmission.issue.scope", "changed", "same_contract_with_current_base_pins")
    marker = re.escape(issue_admission.MARKER)
    block = r"<!--\s*" + marker + r"\s*-->\s*```json\s*\n.*?\n\s*```\s*<!--\s*/" + marker + r"\s*-->"
    require(re.sub(block, "<contract>", current["body"], flags=re.DOTALL)
            == re.sub(block, "<contract>", selected["body"], flags=re.DOTALL),
            "readmission.issue.prose", "changed", "unchanged_issue_prose_and_marker")
    verify_failed_prior(provider, authorization)
    # Refresh the actual Issue immediately before recording the only write offer.
    require(provider.issue(selected["number"]) == current,
            "readmission.issue.race", "changed", "fresh_provider_issue_readback")
    state["writes"]["issue_base"] = {
        "status": "offered", "previous_body_sha256": issue_admission.body_digest(current["body"]),
        "body_sha256": issue_admission.body_digest(selected["body"]),
        "previous_base": previous, "base_head": target,
        "prior_head": authorization["prior_publication"]["head"]}
    save_json(paths["state"], state)
    try:
        provider.update_issue_body(selected["number"], selected["body"])
    except MutationUnknown:
        pass
    # Only provider readback commits the transition; an unknown result never reoffers.
    readmit_issue_base(provider, authorization, state, paths)


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


def validate_scope_request(authorization, selection):
    require(isinstance(selection, dict) and set(selection) == {
        "schema", "added_write_paths", "reason", "evidence", "lifecycle_owner", "candidate_head"}
        and type(selection["schema"]) is int and selection["schema"] == 1,
        "scope.selection.fields", selection, "pinned_external_scope_selection")
    require(isinstance(selection["reason"], str) and selection["reason"].strip()
            and isinstance(selection["candidate_head"], str)
            and SHA40.fullmatch(selection["candidate_head"]),
            "scope.selection.subject", selection.get("candidate_head"))
    issue_admission.supplemented_body(authorization["issue"]["body"], selection["added_write_paths"])
    validate_prior_atom_ref(selection["evidence"], authorization["control_root"])
    validate_lifecycle_owner({**authorization, "lifecycle_owner": selection["lifecycle_owner"]})


def scope_packet(authorization, state):
    amendment = state.get("scope_amendment")
    require(isinstance(amendment, dict), "scope.amendment", amendment, "original_scope_selection")
    ref = amendment["selection"]
    validate_prior_atom_ref(ref, authorization["control_root"])
    packet = read_json(ref["path"], "scope.selection")
    require(set(packet) == {"schema", "authorization", "selection", "output"}
            and packet["schema"] == 1
            and packet["authorization"]["sha256"] == state["authorization_sha256"]
            and digest_file(packet["authorization"]["path"]) == state["authorization_sha256"]
            and Path(ref["path"]).parent == Path(packet["output"]),
            "scope.authorization", "changed", "original_authorization_bytes")
    original = read_json(packet["authorization"]["path"], "scope.authorization")
    body = original["issue"]["body"]
    if "number" not in original["issue"]:
        body = body.rstrip() + "\n\n" + marker(state["authorization_sha256"]) + "\n"
    effective = {**original, "issue": {**original["issue"], "number": state["issue"]["number"],
        "body": issue_admission.supplemented_body(body, packet["selection"]["added_write_paths"])}}
    require(authorization in (original, effective), "scope.authority", "changed", "original_authorization_bytes")
    validate_scope_request(original, packet["selection"])
    return packet


def scope_projection(authorization, state, paths):
    """Project one adopted scope; raw authorization remains the repair identity."""
    if state.get("correction_start_recovery") is not None:
        recovery = correction_start_record(authorization, state)
        if state["correction_start_recovery"].get("prepared"):
            paths = {**paths, "envelope": Path(recovery["output"]) / "admission/envelope.json"}
    if state.get("scope_amendment") is None:
        return authorization, paths
    packet = scope_packet(authorization, state)
    amendment = state["scope_amendment"]
    authorization = read_json(packet["authorization"]["path"], "scope.authorization")
    old_body = authorized_issue_body(authorization, state["authorization_sha256"])
    body = issue_admission.supplemented_body(old_body, packet["selection"]["added_write_paths"])
    effective = {**authorization, "issue": {**authorization["issue"],
                 "number": state["issue"]["number"], "body": body}}
    if amendment.get("prepared"):
        paths = {**paths, "envelope": Path(packet["output"]) / "admission/envelope.json"}
    return effective, paths


def correction_start_record(authorization, state):
    ref = state["correction_start_recovery"]["record"]
    validate_prior_atom_ref(ref, authorization["control_root"])
    record = read_json(ref["path"], "correction.start.record")
    require(set(record) == {"schema", "authorization", "runtime", "from_runtime", "output", "envelope", "prepared",
                           "noodle_start", "correction_prior", "correction_ack_prefix", "logs"}
            and record["schema"] == 1
            and record.get("authorization", {}).get("sha256") == state["authorization_sha256"]
            and read_json(record["authorization"]["path"], "correction.start.authorization") == authorization
            and digest_file(record["authorization"]["path"]) == state["authorization_sha256"]
            and Path(record["output"]) == Path(ref["path"]).parent / "startup-recovery",
            "correction.start.binding", "changed", "original_startup_recovery_record")
    for item in (record["envelope"], record["prepared"], *record["logs"]):
        validate_prior_atom_ref(item, authorization["control_root"])
    validate_lifecycle_owner({**authorization, "lifecycle_owner": record["runtime"]})
    transition = state.get("lifecycle_resume")
    while transition is not None and not (transition.get("from") == record["from_runtime"]
            and transition.get("to") == record["runtime"]):
        transition = transition.get("previous")
    require(transition is not None, "correction.start.runtime", "unbound", "original_selected_startup_runtime")
    return record


def stopped_correction_start(authorization, record):
    """Observe the exact startup that stopped before changing native custody."""
    root = Path(authorization["control_root"])
    runtime = root / ".noodle"
    envelope = issue_admission.load_external_envelope(
        record["envelope"]["path"], record["envelope"]["sha256"], root)
    prior = record["correction_prior"]
    start = record["noodle_start"]
    require(start.get("status") == "started" and not any(start.get(key) for key in
            ("stop_offered", "restore_offered", "restored"))
            and noodle_process_argv(authorization, start)[-2:] == ["--mode", "manual"]
            and observe_prior_loop(authorization, {"noodle_start": start}) == "stopped",
            "correction.start.process", "not_stopped", "stopped_original_correction_start")
    prepared = read_json(record["prepared"]["path"], "correction.start.prepared")
    require(digest_file(record["prepared"]["path"]) == record["prepared"]["sha256"]
            and start["argv"] == prepared["next"]["argv"] == [prepared["start"]]
            and digest_file(prepared["start"]) == prepared["start_sha256"]
            and prepared["envelope_sha256"] == record["envelope"]["sha256"]
            and prepared["process_argv"] == start["process_argv"]
            and host_config_identity(root) == start["config_sha256"]
            == digest_file(Path(record["prepared"]["path"]).parent / "noodle.toml"),
            "correction.start.identity", "changed", "original_start_bundle_and_configuration")
    require(envelope["repository"] == authorization["repository"]
            and envelope["issue"] == authorization["issue"]["number"]
            and envelope["base_head"] == authorization["base_head"]
            and envelope["body_sha256"] == digest_bytes(authorization["issue"]["body"].encode())
            and envelope["execution"]["task"] == authorization["task"]
            and envelope["execution"].get("failure_context") == authorization["failure_context"]
            and envelope["execution"]["source_head"] == authorization["prior_publication"]["head"]
            and envelope["execution"]["order_id"] == prior["order_id"]
            and envelope["execution"]["worktree"] == prior["worktree"],
            "correction.start.envelope", "changed", "original_correction_envelope")
    require(digest_file(runtime / "state.snapshot.json") == prior["owner_snapshot_sha256"],
            "correction.start.snapshot", "changed", "unchanged_predispatch_native_snapshot")
    owner = issue_execution.read_owner(envelope)
    require(owner["state"]["orders"][prior["order_id"]]["stages"] == [prior["stage"]]
            and prior["stage"]["status"] == "review",
            "correction.start.stage", "changed", "original_parked_review")
    with (runtime / "control.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ack_path = runtime / "control-ack.ndjson"
        require((ack_path.read_text() if ack_path.exists() else "") == record["correction_ack_prefix"],
                "correction.start.acks", "changed", "original_control_ack_history")
        mailbox = runtime / "control.ndjson"
        require(not mailbox.exists() or not mailbox.read_bytes().strip(),
                "correction.start.mailbox", "pending", "original_control_readback_without_replay")
    for oid, order in owner["state"]["orders"].items():
        if oid == "schedule" and native_idle_schedule(order, authorization["carrier"]["codex"]["model"]):
            continue
        issue_execution.quiescent_order({"execution": {"control_root": str(root), "order_id": oid}}, owner)
    for process in (runtime / "sessions").glob("*/process.json"):
        issue_execution._absent_process(process.parent, process.parent.name)
    issue_execution.validate_worktree(Path(prior["worktree_path"]), envelope)
    return envelope, owner


def correction_start_selection(authorization_path, authorization, state, paths, runtime):
    require(state.get("phase") == "execution" and state.get("publication") is None
            and {"prior_atom", "failure_context"} <= authorization.keys()
            and state.get("prior_host_recovery", {}).get("status") == "restored"
            and state.get("writes") == {} and not state.get("scope_amendment")
            and not any(key in state for key in ("correction_review", "correction_proposal", "correction_release",
                "noodle_amendment", "host_finalization", "correction_start_recovery"))
            and not any(paths[name].exists() for name in ("claim", "acceptance", "landing")),
            "correction.start.phase", state.get("phase"), "stopped_predispatch_correction_only")
    start = state["noodle_start"]
    record = {"schema": 1, "authorization": {"path": str(Path(authorization_path).resolve()), "sha256": state["authorization_sha256"]},
              "runtime": runtime, "from_runtime": resumed_lifecycle(authorization, state).get("lifecycle_owner"),
              "output": str(paths["directory"] / "startup-recovery"),
              "envelope": {"path": str(paths["envelope"]), "sha256": state["envelope_sha256"]},
              "prepared": {"path": str(paths["envelope"].parent / "prepared.json"), "sha256": state["admission_sha256"]},
              "noodle_start": start, "correction_prior": state["correction_prior"],
              "correction_ack_prefix": state["correction_ack_prefix"],
              "logs": [{"path": start[key], "sha256": digest_file(start[key])} for key in ("stdout", "stderr")]}
    binding, owner = stopped_correction_start(authorization, record)
    return record, binding, owner


def advance_correction_start(authorization, paths, state, provider, environ):
    recovery = state["correction_start_recovery"]
    record = correction_start_record(authorization, state)
    if recovery.get("start_offered"):
        require(state.get("noodle_start", {}).get("status") == "started",
                "correction.start.outcome", "unknown", "original_start_process_readback_without_restart")
        _, selected_paths = scope_projection(authorization, state, paths)
        correction_owner(authorization, selected_paths, state)
        recovery["status"] = "started"
        save_json(paths["state"], state)
        return {"action": "correction_start_observed"}
    envelope, _ = stopped_correction_start(authorization, record)
    issue, body = exact_issue(provider, authorization, state["authorization_sha256"])
    issue_admission.validate_issue(issue, envelope)
    output = Path(record["output"]) / "admission"
    if not recovery.get("prepared"):
        output.parent.mkdir(mode=0o700, exist_ok=True)
        source = Path(validate_lifecycle_owner({**authorization, "lifecycle_owner": record["runtime"]})).parent
        result = supervisor_admission.prepare(issue, {**authorization["carrier"], "noodle": authorization["noodle"]},
            authorization["control_root"], output, environ=environ, task=authorization["task"], wire_host=True,
            instruction_pins=selected_instruction_pins(authorization), correction=True,
            failure_context=authorization["failure_context"], runtime_root=source, readback=output.exists())
        require(read_json(output / "envelope.json", "correction.start.envelope") == envelope,
                "correction.start.semantics", "changed", "unchanged_original_correction_envelope")
        recovery["prepared"] = {"path": str(output / "prepared.json"), "sha256": digest_file(output / "prepared.json")}
        state["admission_sha256"] = recovery["prepared"]["sha256"]
        state["envelope_sha256"] = result["envelope_sha256"]
        save_json(paths["state"], state)
        return {"action": "correction_start_prepared"}
    validate_prior_atom_ref(recovery["prepared"], authorization["control_root"])
    _, selected_paths = scope_projection(authorization, state, paths)
    return ensure_noodle(authorization, selected_paths, state, {"action": "correction_review"},
                         environ, correction_restart=True)


def scope_custody(authorization, state, paths, selection):
    require(state.get("phase") == "execution" and state.get("publication") is None
            and not paths["landing"].exists() and not paths["claim"].exists()
            and not paths["acceptance"].exists() and not state.get("host_finalization")
            and not ({"prior_atom", "prior_publication"} & authorization.keys()),
            "scope.phase", state.get("phase"), "stopped_original_prepublication_atom")
    require(set(state.get("writes", {})) <= {"issue_create"},
            "scope.writes", state.get("writes"), "original_write_readback_before_scope_amendment")
    envelope = issue_admission.load_external_envelope(
        paths["envelope"], state["envelope_sha256"], authorization["control_root"])
    old_body = authorized_issue_body(authorization, state["authorization_sha256"])
    require(envelope["repository"] == authorization["repository"]
            and envelope["issue"] == state["issue"]["number"]
            and envelope["base_head"] == authorization["base_head"]
            and envelope["body_sha256"] == digest_bytes(old_body.encode())
            and envelope["execution"]["task"] == authorization["task"],
            "scope.original_binding", "changed", "original_execution_envelope")
    binding = {**envelope, "contract": issue_admission.parse_contract(old_body),
               "issue_body": old_body}
    owner = issue_execution.read_owner(binding)
    blocked = issue_execution.blocked_outcome(binding, owner)
    require(blocked is not None, "scope.blocked", "missing", "original_typed_blocked_outcome")
    order_id = envelope["execution"]["order_id"]
    stage = owner["state"]["orders"][order_id]["stages"][0]
    subject = json.loads(stage["prompt"])
    require(subject.get("route") in {"automatic", "supervised"}
            and subject == issue_execution.projection(binding, state["envelope_sha256"], subject["route"]),
            "scope.original_prompt", "changed", "original_admitted_task")
    for oid, order in owner["state"]["orders"].items():
        if oid == "schedule" and native_idle_schedule(order, authorization["carrier"]["codex"]["model"]):
            continue
        issue_execution.quiescent_order({"execution": {
            "control_root": authorization["control_root"], "order_id": oid}}, owner)
    for process in (Path(authorization["control_root"]) / ".noodle/sessions").glob("*/process.json"):
        issue_execution._absent_process(process.parent, process.parent.name)
    require(observe_prior_loop(authorization, state) == "stopped",
            "scope.process", "not_stopped", "stopped_original_owner")
    worktree = Path(authorization["control_root"]) / ".worktrees" / envelope["execution"]["worktree"]
    issue_execution.validate_worktree(worktree, {**binding, "execution": {
        **binding["execution"], "source_head": selection["candidate_head"]}})
    return {"envelope": {"path": str(paths["envelope"]), "sha256": state["envelope_sha256"]},
            "admission_sha256": state["admission_sha256"], "issue": state["issue"],
            "noodle_start": state["noodle_start"], "stage": stage, "blocked": blocked}


def adopt_scope_amendment(authorization_path, selection_path, selection_sha256, *, environ=None):
    """Adopt external bytes on the original checkpoint; no provider or native effect."""
    environ = os.environ if environ is None else environ
    paths = artifact_paths(authorization_path)
    with Path(authorization_path).open("rb") as authority:
        fcntl.flock(authority, fcntl.LOCK_EX | fcntl.LOCK_NB)
        authorization, digest = validate_authorization(
            authorization_path, environ.get("SOODLES_AUTHORIZATION_SHA256"), allow_advanced=True)
        ref = {"path": str(Path(selection_path).resolve()), "sha256": selection_sha256}
        validate_prior_atom_ref(ref, authorization["control_root"])
        packet = read_json(selection_path, "scope.selection")
        require(packet.get("authorization") == {"path": str(Path(authorization_path).resolve()), "sha256": digest},
                "scope.authorization", packet.get("authorization"), "original_authorization_bytes")
        validate_scope_request(authorization, packet["selection"])
        selected = {**authorization, "lifecycle_owner": packet["selection"]["lifecycle_owner"]}
        validate_lifecycle_owner(selected, executing=True)
        runtime = Path(authorization["control_root"]) / ".noodle"
        with (runtime / "issue-atom.lock").open("a+b") as atom_lock, \
                (runtime / "noodle.lock").open("a+b") as native_lock:
            fcntl.flock(atom_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = read_json(paths["state"], "scope.state")
            require(state.get("authorization_sha256") == digest,
                    "scope.state.authorization", "changed", "original_lifecycle_checkpoint")
            if state.get("scope_amendment") is not None:
                require(state["scope_amendment"]["selection"] == ref,
                        "scope.selection", "already_adopted", "original_scope_selection")
                scope_packet(authorization, state)
            else:
                prior = scope_custody(authorization, state, paths, packet["selection"])
                fcntl.flock(native_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                envelope = read_json(paths["envelope"], "scope.envelope")
                owner = issue_execution.read_owner(envelope)
                require(owner["state"]["orders"][envelope["execution"]["order_id"]]["stages"][0]
                        == prior["stage"], "scope.owner.race", "changed", "fresh_canonical_checkpoint")
                current = resumed_lifecycle(authorization, state)
                intent = {"from": current.get("lifecycle_owner"),
                          "to": selected["lifecycle_owner"], "authorization_sha256": digest}
                if state.get("lifecycle_resume") is not None:
                    intent["previous"] = state["lifecycle_resume"]
                state["scope_amendment"] = {"selection": ref, "prior": prior}
                if intent["from"] != intent["to"]:
                    state["lifecycle_resume"] = intent
                scope_packet(authorization, state)
                resumed_lifecycle(authorization, state)
                repair_controller(authorization, state, paths, authorization_path=authorization_path)
                require(all(entry.get("status") == "confirmed" for entry in
                            (state.get("repair") or {}).get("history", [])),
                        "scope.repair_effect", "unresolved", "original_repair_owner_readback_without_retry")
                save_json(paths["state"], state)
    return {"owner": "soodles.issue-atom", "status": "prepared", "continuation_state": "ready",
            "authorizes_landing": False,
            "next": {"kind": "executable", "owner": "soodles.issue-atom",
                     "argv": same_command(authorization_path),
                     "environment": {"SOODLES_AUTHORIZATION_SHA256": digest}}}


def advance_scope_amendment(authorization, paths, state, provider, environ):
    """Continue the original blocked order through existing provider and native controls."""
    packet = scope_packet(authorization, state)
    selection = packet["selection"]
    amendment = state["scope_amendment"]
    effective, selected_paths = scope_projection(authorization, state, paths)
    number = state["issue"]["number"]
    issue = provider.issue(number)
    expected_body = effective["issue"]["body"]
    original = amendment["prior"]["envelope"]
    old_envelope = issue_admission.load_external_envelope(
        original["path"], original["sha256"], authorization["control_root"])
    retained = amendment["prior"]["blocked"]["source"]
    require(digest_file(retained["path"]) == retained["sha256"],
            "scope.blocked.history", "changed", "original_terminal_event_bytes")
    if not amendment.get("restart_offered"):
        old_state = {**state, "noodle_start": amendment["prior"]["noodle_start"]}
        require(observe_prior_loop(authorization, old_state) == "stopped",
                "scope.prior_process", "changed", "stopped_original_owner")
        owner = issue_execution.read_owner(old_envelope)
        order_id = old_envelope["execution"]["order_id"]
        require(owner["state"]["orders"][order_id]["stages"][0] == amendment["prior"]["stage"]
                and issue_execution.blocked_outcome(old_envelope, owner) == amendment["prior"]["blocked"],
                "scope.prior_order", "changed", "original_typed_blocked_outcome")
        worktree = Path(authorization["control_root"]) / ".worktrees" / old_envelope["execution"]["worktree"]
        issue_execution.validate_worktree(worktree, {**old_envelope, "execution": {
            **old_envelope["execution"], "source_head": selection["candidate_head"]}})
    require(issue.get("number") == number and issue.get("state") == "open"
            and issue.get("title") == authorization["issue"]["title"]
            and issue.get("html_url") == f'https://github.com/{authorization["repository"]}/issues/{number}'
            and "pull_request" not in issue,
            "scope.issue.identity", number, "exact_open_original_issue")
    intent = state["writes"].get("issue_scope")
    identity = {"selection_sha256": amendment["selection"]["sha256"],
                "previous_body_sha256": old_envelope["body_sha256"],
                "body_sha256": digest_bytes(expected_body.encode())}
    if issue.get("body") != expected_body:
        require(intent is None, "scope.issue.outcome", "unknown",
                "fresh_provider_issue_readback_without_retry")
        require(digest_bytes(issue.get("body", "").encode()) == old_envelope["body_sha256"],
                "scope.issue.body", "changed", "exact_original_issue_readback")
        require(provider.issue(number) == issue, "scope.issue.race", "changed", "fresh_issue_readback")
        state["writes"]["issue_scope"] = {**identity, "status": "offered"}
        save_json(paths["state"], state)
        try:
            provider.update_issue_body(number, expected_body)
        except MutationUnknown:
            pass
        return {"action": "scope_issue_readback_pending"}
    require(intent in ({**identity, "status": "offered"}, {**identity, "status": "observed"}),
            "scope.issue.intent", intent, "original_scope_write_readback")
    if intent["status"] != "observed":
        state["writes"]["issue_scope"] = {**identity, "status": "observed"}
        save_json(paths["state"], state)
    output = Path(packet["output"]) / "admission"
    if amendment.get("prepared") is None:
        if amendment.get("preparation") is None:
            require(not output.exists(), "scope.admission.identity", str(output),
                    "original_prepared_admission_readback_without_replacement")
            amendment["preparation"] = {"owner": resumed_lifecycle(authorization, state)["lifecycle_owner"],
                                       "issue": issue}
            save_json(paths["state"], state)
        preparation = amendment["preparation"]
        source = Path(validate_lifecycle_owner({**authorization, "lifecycle_owner": preparation["owner"]})).parent
        pins = authorization.get("instruction_pins")
        if pins is not None:
            pins = [{"path": item["path"], "sha256": digest_bytes(issue_admission.git_bytes(
                authorization["control_root"], selection["candidate_head"], item["path"]))} for item in pins]
        prepared = supervisor_admission.prepare(
            preparation["issue"], {**authorization["carrier"], "noodle": authorization["noodle"]},
            authorization["control_root"], output, environ=environ, task=authorization["task"],
            wire_host=True, instruction_pins=pins, correction=True,
            runtime_root=source, readback=output.exists())
        amendment["prepared"] = {"path": str(output / "prepared.json"),
                                 "sha256": digest_file(output / "prepared.json")}
        state["envelope_sha256"] = prepared["envelope_sha256"]
        state["admission_sha256"] = amendment["prepared"]["sha256"]
        save_json(paths["state"], state)
        return {"action": "scope_admission_prepared"}
    validate_prior_atom_ref(amendment["prepared"], authorization["control_root"])
    require(state["admission_sha256"] == amendment["prepared"]["sha256"],
            "scope.admission", "changed", "original_prepared_scope_admission")
    effective, selected_paths = scope_projection(authorization, state, paths)
    binding = issue_execution.context(selected_paths["envelope"], state["envelope_sha256"],
                                      authorization["control_root"], lambda *_: issue)
    require(binding["execution"]["source_head"] == selection["candidate_head"],
            "scope.candidate", binding["execution"]["source_head"], "selected_retained_candidate")
    if not amendment.get("restart_offered"):
        return ensure_noodle(authorization, selected_paths, state, {"action": "scope_review"},
                             environ, scope_restart=True)
    require(state.get("noodle_start", {}).get("status") == "started",
            "scope.start.outcome", state.get("noodle_start", {}).get("status"),
            "original_process_readback_without_restart")
    require(observe_prior_loop(authorization, state) == "running",
            "scope.process", "stopped", "original_process_readback_without_restart")
    require(host_config_identity(authorization["control_root"]) == state["noodle_start"]["config_sha256"],
            "scope.config", "changed", "unchanged_scope_owner_configuration")
    owner = issue_execution.read_owner(binding)
    order_id = binding["execution"]["order_id"]
    stage = owner["state"]["orders"][order_id]["stages"][0]
    require(all(stage.get(key) == amendment["prior"]["stage"].get(key)
                for key in ("task_key", "skill", "provider", "model", "runtime")),
            "scope.stage.identity", "changed", "original_dispatch_identity")
    if "scope_release" not in state:
        require(noodle_process_argv(authorization, state["noodle_start"])[-2:] == ["--mode", "manual"],
                "scope.mode", state["noodle_start"].get("process_argv"), "original_manual_process_hold")
    prefix = "soodles-scope-" + amendment["selection"]["sha256"][:24]
    prompt = json.dumps(issue_execution.projection(binding, state["envelope_sha256"], "supervised"), sort_keys=True)
    commands = {
        "scope_edit": {"id": prefix + "-edit", "action": "edit-item", "order_id": order_id, "prompt": prompt},
        "scope_requeue": {"id": prefix + "-requeue", "action": "requeue", "order_id": order_id},
        "scope_release": {"id": prefix + "-release", "action": "mode", "value": "supervised"}}
    runtime = Path(authorization["control_root"]) / ".noodle"
    with (runtime / "control.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        raw = (runtime / "control-ack.ndjson").read_text() if (runtime / "control-ack.ndjson").exists() else ""
        require(raw.startswith(amendment["ack_prefix"]), "scope.control.history", "changed")
        allowed = {command["id"]: command for key, command in commands.items() if key in state}
        acks = [json.loads(line) for line in raw[len(amendment["ack_prefix"]):].splitlines() if line.strip()]
        require(all(ack.get("id") in allowed and ack.get("action") == allowed[ack["id"]]["action"]
                    and ack.get("status") == "ok" for ack in acks),
                "scope.control.foreign", acks, "exclusive_scope_control_readback")
        mailbox = runtime / "control.ndjson"
        pending = [json.loads(line) for line in mailbox.read_text().splitlines() if line.strip()] if mailbox.exists() else []
        require(all(command == allowed.get(command.get("id")) for command in pending),
                "scope.control.pending", pending, "exclusive_scope_control_readback")
    original_attempts = amendment["prior"]["stage"]["attempts"]
    if "scope_requeue" not in state:
        require(stage.get("attempts") == original_attempts,
                "scope.attempts", "changed", "original_retained_attempts")
    ack = amendment_control(authorization, paths, state, "scope_edit", commands["scope_edit"])
    if ack is None:
        return {"action": "scope_edit_pending"}
    require(stage.get("prompt") == prompt, "scope.prompt", "changed", "native_edited_prompt_readback")
    ack = amendment_control(authorization, paths, state, "scope_requeue", commands["scope_requeue"])
    if ack is None:
        return {"action": "scope_requeue_pending"}
    if "scope_release" not in state:
        expected_attempts = [*original_attempts[:-1], {**original_attempts[-1],
                             "status": "failed", "error": "requeue typed blocked outcome"}]
        require(stage.get("status") == "pending" and stage.get("attempts") == expected_attempts
                and order_id not in owner["state"].get("pending_reviews", {}),
                "scope.requeue", stage.get("status"), "canonical_requeued_original_order")
        amendment["requeued_attempts"] = expected_attempts
        amendment["release_epoch"] = owner["state"].get("mode_epoch")
        require(type(amendment["release_epoch"]) is int, "scope.mode_epoch", amendment["release_epoch"])
        save_json(paths["state"], state)
    ack = amendment_control(authorization, paths, state, "scope_release", commands["scope_release"])
    if ack is None:
        return {"action": "scope_release_pending"}
    require(owner["state"].get("mode") == "supervised"
            and owner["state"].get("mode_epoch") == amendment["release_epoch"] + 1,
            "scope.release", "changed", "canonical_supervised_release_readback")
    amendment["status"] = "released"
    save_json(paths["state"], state)
    return {"action": "scope_released"}


def same_command(path):
    return [str((Path(__file__).resolve().parent / "issue-atom")), "run", str(Path(path).resolve())]


def host_projection(record):
    """A disposable view of the owner's record, never a source of effect authority."""
    try:
        plan = schema_manager.compiled(Path(__file__).resolve().parent)
        return schema_manager.Manager(plan, record["identity"], record).project()
    except (schema_manager.SchemaRefusal, issue_admission.AdmissionRefusal, OSError) as error:
        return {"status": "unavailable", "gap": str(error), "authorizes_landing": False}


def response(state, authorization_path, *, status="pending", waiting_on=None, details=None, repair=None):
    result = {
        "owner": "soodles.issue-atom", "status": status,
        "continuation_state": "complete" if status == "resolved" else
            "waiting" if status == "pending" else "unknown",
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
    if "host_finalization" in state:
        result["host_finalization_projection"] = host_projection(state["host_finalization"])
    if repair is not None:
        result["repair_budget"] = repair.cost_status()
    if waiting_on:
        result["waiting_on"] = waiting_on
    if details:
        result.update(details)
    return result


def create_envelope(authorization, issue, body, path, *, environ=None):
    root = Path(authorization["control_root"]).resolve()
    require(issue["body"] == body, "envelope.issue_body", "changed")
    pins = selected_instruction_pins(authorization)
    correction = "prior_atom" in authorization
    runtime_root = None
    if correction:
        prior = verify_prior_atom(authorization)
        require(prior["prior_loop_status"] == "restored",
                "envelope.prior_host", prior["prior_loop_status"],
                "original_host_recovery_readback")
    if authorization.get("lifecycle_owner") is not None:
        runtime_root = Path(validate_lifecycle_owner(authorization, executing=True)).parent
    path.parent.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = supervisor_admission.prepare(
        issue, {**authorization["carrier"], "noodle": authorization["noodle"]},
        root, path.parent, environ=environ, task=authorization["task"], wire_host=True,
        instruction_pins=pins, correction=correction,
        failure_context=authorization.get("failure_context"), runtime_root=runtime_root)
    if runtime_root is None:
        save_json(path.parent / "prepared.json", result, fresh=True)
    return read_json(path, "envelope"), result["envelope_sha256"]


def host_config_identity(root):
    path = Path(root) / ".noodle.toml"
    require(not path.is_symlink(), "noodle.config", "symlink", "unchanged_host_configuration")
    return digest_file(path) if path.exists() else None


def noodle_process_argv(authorization, start):
    """Read the owner's pinned process form, including its temporary start hold."""
    base = [authorization["noodle"]["path"], "--project-dir",
            authorization["control_root"], "start"]
    argv = start.get("process_argv", base)
    require(argv in (base, base + ["--mode", "manual"]),
            "noodle.process.argv", argv, "original_start_process_readback")
    return argv


def bootstrap_noodle(authorization, paths, state, environ):
    """Let the pinned Noodle owner create the first canonical checkpoint once."""
    root = Path(authorization["control_root"])
    runtime = root / ".noodle"
    snapshot = runtime / "state.snapshot.json"
    prior = state.get("noodle_bootstrap")
    if prior:
        if prior.get("status") != "exited_zero":
            raise AtomRefusal("noodle.bootstrap.outcome", prior.get("status"),
                              "current_noodle_owner_readback_without_restart", owner="Noodle")
    else:
        if snapshot.exists() or {p.name for p in runtime.iterdir()} != {"issue-atom.lock"}:
            raise AtomRefusal("noodle.bootstrap.runtime", str(runtime),
                              "pristine_noodle_owner", owner="Noodle")
        require(host_config_identity(root) == authorization["host_config_sha256"],
                "noodle.config.digest", host_config_identity(root), "unchanged_host_configuration")
        ignored = subprocess.run(["git", "check-ignore", "-q", ".noodle.toml"], cwd=root)
        require(ignored.returncode == 0, "noodle.config.tracked", ".noodle.toml",
                "host_owned_ignored_noodle_configuration")
        prepared_path = paths["envelope"].parent / "prepared.json"
        prepared = read_json(prepared_path, "admission.prepared")
        require(digest_file(prepared_path) == state.get("admission_sha256"),
                "admission.prepared.digest", "changed", "unchanged_supervisor_start")
        argv = prepared.get("bootstrap", {}).get("argv")
        require(argv == [prepared["start"], "--once"]
                and digest_file(prepared["start"]) == prepared["start_sha256"],
                "noodle.bootstrap.identity", argv, "unchanged_supervisor_start")
        bootstrap_config = paths["envelope"].parent / "bootstrap-noodle.toml"
        descriptor = prepared["bootstrap"]
        require(descriptor.get("config") == str(bootstrap_config)
                and descriptor.get("config_sha256") == digest_file(bootstrap_config),
                "noodle.bootstrap.config", descriptor.get("config"),
                "pinned_supervisor_bootstrap_config")
        generated = bootstrap_config.read_bytes()
        config = root / ".noodle.toml"
        original = config.read_bytes() if config.exists() else None
        try:
            lock = (runtime / "noodle.lock").open("xb")
        except FileExistsError:
            raise AtomRefusal("noodle.bootstrap.lock", "present",
                              "current_noodle_owner_readback", owner="Noodle") from None
        with lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise AtomRefusal("noodle.bootstrap.lock", "running",
                                  "quiescent_noodle_owner", owner="Noodle") from None
            state["noodle_bootstrap"] = {
                "status": "offered", "argv": argv,
                "config_sha256": digest_bytes(generated),
                "original_config": None if original is None else base64.b64encode(original).decode(),
            }
            save_json(paths["state"], state)
            config.write_bytes(generated)
        with (paths["directory"] / "bootstrap.stdout").open("xb") as stdout, \
                (paths["directory"] / "bootstrap.stderr").open("xb") as stderr:
            try:
                result = subprocess.run(argv, cwd=root, env=dict(environ), stdin=subprocess.DEVNULL,
                                        stdout=stdout, stderr=stderr, start_new_session=True, timeout=120)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise AtomRefusal("noodle.bootstrap.outcome", type(error).__name__,
                                  "current_noodle_owner_readback_without_restart", owner="Noodle") from error
        state["noodle_bootstrap"]["status"] = "exited_zero" if result.returncode == 0 else "failed"
        state["noodle_bootstrap"]["returncode"] = result.returncode
        save_json(paths["state"], state)
        if result.returncode != 0:
            raise AtomRefusal("noodle.bootstrap.exit", result.returncode,
                              "current_noodle_owner_readback_without_restart", owner="Noodle")

    # A lost exit response is never inferred from a snapshot alone. Only a
    # recorded zero exit may complete the bootstrap without rerunning Noodle.
    if not snapshot.is_file() or snapshot.is_symlink():
        raise AtomRefusal("noodle.bootstrap.snapshot", str(snapshot),
                          "canonical_checkpoint_readback", owner="Noodle")
    try:
        owner = issue_execution.read_owner({"execution": {"control_root": str(root)}})
    except issue_admission.AdmissionRefusal as error:
        raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                          "canonical_checkpoint_readback", owner="Noodle") from error
    if owner["state"]["orders"] != {} or owner["effect_ledger"] != []:
        raise AtomRefusal("noodle.bootstrap.owner", "nonempty",
                          "pristine_noodle_owner", owner="Noodle")
    with (runtime / "noodle.lock").open("r+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("noodle.bootstrap.lock", "running",
                              "quiescent_noodle_owner", owner="Noodle") from None
        config = root / ".noodle.toml"
        original = state["noodle_bootstrap"]["original_config"]
        original_bytes = None if original is None else base64.b64decode(original)
        original_digest = None if original_bytes is None else digest_bytes(original_bytes)
        require(original_digest == authorization["host_config_sha256"],
                "noodle.bootstrap.original_config", "changed", "unchanged_host_configuration")
        installed = host_config_identity(root)
        if installed == state["noodle_bootstrap"]["config_sha256"]:
            if original_bytes is None:
                config.unlink()
            else:
                config.write_bytes(original_bytes)
        else:
            require(installed == original_digest, "noodle.bootstrap.config", "changed",
                    "unchanged_installed_configuration")
        state["noodle_bootstrap"]["status"] = "complete"
        save_json(paths["state"], state)


def ensure_noodle(authorization, paths, state, admission, environ, *, correction=False, scope_restart=False,
                  correction_restart=False):
    """Consume the producer's start once; Noodle's lock remains process authority."""
    root = Path(authorization["control_root"])
    prior = None
    restarting = scope_restart or correction_restart
    held = correction or restarting
    amendment = state.get("scope_amendment") if scope_restart else None
    recovery = state.get("correction_start_recovery") if correction_restart else None
    if correction_restart:
        record = correction_start_record(authorization, state)
        require(not recovery.get("start_offered") and state.get("noodle_start") == record["noodle_start"]
                and admission.get("action") == "correction_review",
                "correction.start.restart", "changed", "original_stopped_correction_start")
        prior = record["correction_prior"]
    if scope_restart:
        require(isinstance(amendment, dict) and not amendment.get("restart_offered")
                and state.get("noodle_start") == amendment["prior"]["noodle_start"]
                and admission.get("action") == "scope_review",
                "scope.restart", "changed", "original_stopped_owner_start")
    if correction:
        require("prior_atom" in authorization
                and admission.get("action") == "correction_review",
                "noodle.start.correction", admission.get("action"),
                "restored_original_host_and_review")
        prior = verify_prior_atom(authorization)
        require(prior["prior_loop_status"] == "restored",
                "noodle.start.prior_loop", prior["prior_loop_status"],
                "original_host_recovery_readback")
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
        require("noodle_start" not in state or restarting, "noodle.start.outcome", "stopped_or_unknown",
                "current_noodle_owner_readback_without_restart")
        require(admission.get("action") in ({"scope_review"} if scope_restart else {"correction_review"} if correction or correction_restart
                else {"proposal_pending"}), "noodle.start.admission",
                admission.get("action"), "original_noodle_owner_continuation")
        binding = read_json(paths["envelope"], "envelope")
        owner = issue_execution.read_owner(binding)
        if correction or correction_restart:
            require(digest_file(runtime / "state.snapshot.json")
                    == prior["owner_snapshot_sha256"],
                    "noodle.start.prior_snapshot", "changed",
                    "unchanged_original_review")
        for order_id, order in owner["state"]["orders"].items():
            if held and order_id == "schedule" and native_idle_schedule(
                    order, authorization["carrier"]["codex"]["model"]):
                continue
            if held and order_id == (binding["execution"]["order_id"] if scope_restart else prior["order_id"]):
                require(isinstance(order, dict)
                        and len(order.get("stages", [])) == 1
                        and order["stages"][0].get("status") == "review",
                        "noodle.start.prior_review", order_id,
                        "original_pending_review")
            else:
                require(isinstance(order, dict) and isinstance(order.get("stages"), list)
                        and all(stage.get("status") in ("completed", "failed", "cancelled")
                                for stage in order["stages"]),
                        "noodle.start.orders", "nonquiescent", "quiescent_noodle_owner")
        for process in sorted((runtime / "sessions").glob("*/process.json")):
            issue_execution._absent_process(process.parent, process.parent.name)
        retained_start = amendment["prior"]["noodle_start"] if scope_restart else record["noodle_start"] if correction_restart else None
        expected_config = retained_start["config_sha256"] if restarting else authorization["host_config_sha256"]
        require(host_config_identity(root) == expected_config,
                "noodle.config.digest", host_config_identity(root), "unchanged_host_configuration")
        ignored = subprocess.run(["git", "check-ignore", "-q", ".noodle.toml"], cwd=root)
        require(ignored.returncode == 0, "noodle.config.tracked", ".noodle.toml",
                "host_owned_ignored_noodle_configuration")
        config = root / ".noodle.toml"
        original = config.read_bytes() if config.exists() else None
        if restarting:
            encoded = retained_start["original_config"]
            original = base64.b64decode(encoded) if encoded is not None else None
        generated = (paths["envelope"].parent / "noodle.toml").read_bytes()
        process_argv = noodle_process_argv(authorization, prepared)
        if held:
            try:
                correction_mode = tomllib.loads(generated.decode("utf-8")).get("mode")
            except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
                raise AtomRefusal("noodle.start.correction_config", type(error).__name__,
                                  "isolated_correction_owner") from error
            require(correction_mode == "supervised"
                    and process_argv[-2:] == ["--mode", "manual"],
                    "noodle.start.correction_mode", process_argv,
                    "pinned_manual_process_hold")
        else:
            require(process_argv[-1:] == ["start"], "noodle.start.process_mode",
                    process_argv, "original_noodle_owner_continuation")
        state["noodle_start"] = {"status": "offered", "argv": start,
                                 "process_argv": process_argv,
                                 "config_sha256": digest_bytes(generated),
                                 "original_config": None if original is None else base64.b64encode(original).decode()}
        if held:
            with (runtime / "control.lock").open("a+b") as control_lock:
                fcntl.flock(control_lock, fcntl.LOCK_EX)
                mailbox = runtime / "control.ndjson"
                require(not mailbox.exists() or not mailbox.read_bytes().strip(),
                        "amendment.control.pending", "foreign", "pending_control_readback")
                ack_path = runtime / "control-ack.ndjson"
                prefix = ack_path.read_text() if ack_path.exists() else ""
            if scope_restart:
                amendment["ack_prefix"] = prefix
                amendment["restart_offered"] = True
            elif correction_restart:
                require(prefix == record["correction_ack_prefix"], "correction.start.acks", "changed",
                        "original_control_ack_history")
                recovery["start_offered"] = True
            else:
                state["correction_ack_prefix"] = prefix
                state["correction_prior"] = {**prior, "stage": owner["state"]["orders"][prior["order_id"]]["stages"][0]}
        save_json(paths["state"], state)
        # Holding the existing Noodle lock excludes an active owner during the
        # bounded config replacement. Noodle itself acquires it on child start.
        config.write_bytes(generated)
    log_root = paths["envelope"].parent.parent if restarting else paths["directory"]
    stdout_path = log_root / "noodle.stdout"
    stderr_path = log_root / "noodle.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        child = subprocess.Popen(start, cwd=root, env=dict(environ), stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, start_new_session=True)
    state["noodle_start"].update(pid=child.pid, status="started",
                                stdout=str(stdout_path), stderr=str(stderr_path))
    save_json(paths["state"], state)
    return {"action": "started", "pid": child.pid, "start_repeated": False}


def amendment_control(authorization, paths, state, name, command):
    """Persist one control intent; an absent ack never permits another append."""
    runtime = Path(authorization["control_root"]) / ".noodle"
    with (runtime / "control.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ack_path = runtime / "control-ack.ndjson"
        acks = [json.loads(line) for line in ack_path.read_text().splitlines()
                if line.strip()] if ack_path.exists() else []
        matches = [ack for ack in acks if ack.get("id") == command["id"]]
        intent = state.get(name)
        if intent is not None:
            require(intent == command, "amendment.control.identity", name,
                    "unchanged_correction_control")
        if matches:
            require(intent == command and len(matches) == 1
                    and matches[0].get("action") == command["action"]
                    and matches[0].get("status") == "ok",
                    "amendment.control.ack", matches, "exact_correction_ack_readback")
            return matches[0]
        if intent is None:
            mailbox = runtime / "control.ndjson"
            require(not mailbox.exists() or not mailbox.read_bytes().strip(),
                    "amendment.control.pending", "foreign", "pending_control_readback")
            state[name] = command
            save_json(paths["state"], state)
            with mailbox.open("ab") as stream:
                stream.write((json.dumps(command, sort_keys=True) + "\n").encode())
                stream.flush()
                os.fsync(stream.fileno())
        return None


def correction_owner(authorization, paths, state):
    """Bind correction readback to this entry's held process and selected bytes."""
    start = state.get("noodle_start", {})
    require(start.get("status") == "started" and not any(start.get(key) for key in
            ("stop_offered", "restore_offered", "restored")),
            "amendment.process.lifecycle", "not_running", "original_correction_process_readback")
    require(noodle_process_argv(authorization, start)[-2:] == ["--mode", "manual"],
            "amendment.process.hold", "missing", "pinned_manual_process_hold")
    require(observe_prior_loop(authorization, state) == "running",
            "amendment.process", "stopped", "original_correction_process_readback")
    prepared_path = paths["envelope"].parent / "prepared.json"
    require(digest_file(prepared_path) == state["admission_sha256"],
            "amendment.prepared", "changed", "unchanged_supervisor_start")
    prepared = read_json(prepared_path, "admission.prepared")
    require(start["argv"] == prepared["next"]["argv"]
            and digest_file(prepared["start"]) == prepared["start_sha256"]
            and start["process_argv"] == noodle_process_argv(authorization, prepared)
            and host_config_identity(authorization["control_root"]) == start["config_sha256"]
            == digest_file(paths["envelope"].parent / "noodle.toml"),
            "amendment.process.identity", "changed", "unchanged_correction_owner")
    require(digest_file(paths["envelope"]) == state["envelope_sha256"],
            "amendment.envelope", "changed", "unchanged_execution_envelope")
    runtime = Path(authorization["control_root"]) / ".noodle"
    with (runtime / "control.lock").open("a+b") as control_lock:
        fcntl.flock(control_lock, fcntl.LOCK_EX)
        ack_path = runtime / "control-ack.ndjson"
        raw = ack_path.read_text() if ack_path.exists() else ""
        prefix = state.get("correction_ack_prefix")
        require(isinstance(prefix, str) and raw.startswith(prefix),
                "amendment.control.history", "changed", "original_control_history")
        allowed = {state[key]["id"]: state[key] for key in
                   ("correction_review", "correction_release") if key in state}
        acks = [json.loads(line) for line in raw[len(prefix):].splitlines() if line.strip()]
        require(all(ack.get("id") in allowed and ack.get("action") ==
                    allowed[ack["id"]]["action"] and ack.get("status") == "ok" for ack in acks),
                "amendment.control.foreign", acks, "exclusive_correction_control_readback")
        mailbox = runtime / "control.ndjson"
        pending = [json.loads(line) for line in mailbox.read_text().splitlines()
                   if line.strip()] if mailbox.exists() else []
        require(all(command == allowed.get(command.get("id")) for command in pending),
                "amendment.control.pending", pending, "exclusive_correction_control_readback")
        binding = read_json(paths["envelope"], "envelope")
        body = authorized_issue_body(authorization, state["authorization_sha256"])
        require(binding["body_sha256"] == digest_bytes(body.encode()),
                "amendment.envelope.body_sha256", "changed", "unchanged_execution_envelope")
        binding["contract"] = issue_admission.parse_contract(body)
        binding["issue_body"] = body
        owner = issue_execution.read_owner(binding)
    order_id = binding["execution"]["order_id"]
    orders = owner["state"]["orders"]
    schedule = orders.get("schedule", {})
    released_schedule = (state.get("correction_release") is not None
                         and schedule.get("status") == "active"
                         and len(schedule.get("stages", [])) == 1
                         and schedule["stages"][0].get("status") in ("dispatching", "running"))
    if released_schedule:
        def refuse(field, value, required="current_noodle_owner_readback"):
            raise AtomRefusal(field, value, required, owner="Noodle")
        own_start_wait(authorization, paths, state, binding, owner, refuse)
    require(all(key == order_id or (key == "schedule" and released_schedule)
                or (key == "schedule" and native_idle_schedule(
                value, authorization["carrier"]["codex"]["model"])) or (isinstance(value, dict)
                and bool(value.get("stages")) and all(stage.get("status") in
                ("completed", "failed", "cancelled") for stage in value["stages"]))
                for key, value in orders.items()),
            "amendment.foreign_orders", sorted(orders), "quiescent_noodle_owner")
    return binding, owner


def advance_correction(authorization, paths, state, provider):
    """Review → failed → replacement → release, through the original Noodle owner."""
    binding, owner = correction_owner(authorization, paths, state)
    order_id = binding["execution"]["order_id"]
    prior = state.get("correction_prior")
    require(isinstance(prior, dict) and prior.get("order_id") == order_id
            and prior.get("worktree") == binding["execution"]["worktree"],
            "amendment.prior_identity", prior, "original_review_custody")
    order = owner["state"]["orders"].get(order_id)
    require(isinstance(order, dict) and len(order.get("stages", [])) == 1,
            "amendment.order", order, "single_original_order")
    stage = order["stages"][0]
    prefix = "soodles-correction-" + state["authorization_sha256"][:24]
    change = {"id": prefix + "-review", "action": "request-changes",
              "order_id": order_id, "prompt": "Correct the selected failed exact-head runtime"}
    release = {"id": prefix + "-release", "action": "mode", "value": "supervised"}
    if state.get("correction_proposal") is None:
        # Before replacement the original completed attempt and source stay fixed.
        original = prior["stage"]
        require(all(stage.get(key) == original.get(key) for key in
                    ("prompt", "skill", "provider", "model"))
                and isinstance(stage.get("attempts"), list)
                and len(stage["attempts"]) == len(original["attempts"])
                and all({k: v for k, v in current.items() if k not in ("status", "error")} ==
                        {k: v for k, v in old.items() if k not in ("status", "error")}
                        for current, old in zip(stage["attempts"], original["attempts"])),
                "amendment.review.identity", "changed", "original_completed_review")
        worktree = Path(prior["worktree_path"])
        require(_git(worktree, "rev-parse", "HEAD") == authorization["prior_publication"]["head"]
                and _git(worktree, "status", "--porcelain", "--untracked-files=all") == "",
                "amendment.worktree", "changed", "clean_published_candidate")
        issue_execution.quiescent_order(binding, owner)
        if state.get("correction_review") is None:
            verify_failed_prior(provider, authorization)
            require(stage.get("status") == "review" and order.get("status") == "active"
                    and set(owner["state"].get("pending_reviews", {})) == {order_id}
                    and stage["attempts"] == original["attempts"],
                    "amendment.review", stage.get("status"), "original_pending_review")
        ack = amendment_control(authorization, paths, state, "correction_review", change)
        if ack is None:
            return {"action": "correction_review_pending"}
        require(order.get("status") == stage.get("status") == "failed"
                and not owner["state"].get("pending_reviews")
                and all(a.get("status") == "failed" for a in stage["attempts"]),
                "amendment.review.transition", stage.get("status"),
                "canonical_failed_order_after_ack_without_resend")
        # Persist before the proposal effect. Recovery observes promotion only;
        # a crash before publication is ambiguous and cannot silently re-offer.
        def before_publish():
            state["correction_failed_attempts"] = stage["attempts"]
            state["correction_proposal"] = {"status": "offered",
                                            "envelope_sha256": state["envelope_sha256"]}
            save_json(paths["state"], state)
        try:
            result = issue_execution.supervised_correction(
                paths["envelope"], state["envelope_sha256"], authorization["control_root"], prior,
                reader=lambda repository, number: provider.issue(number),
                before_publish=before_publish)
        except issue_admission.AdmissionRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              error.next["required"][0], owner="Noodle") from error
        return {"action": "correction_proposal_pending", "published": result["published"]}
    require(state["correction_proposal"] == {"status": "offered",
                                            "envelope_sha256": state["envelope_sha256"]},
            "amendment.proposal.identity", "changed", "selected_proposal_readback")
    try:
        prompt = json.loads(stage.get("prompt", ""))
    except (TypeError, ValueError):
        prompt = None
    if prompt == json.loads(prior["stage"]["prompt"]) and stage.get("status") == "failed":
        mailbox = Path(authorization["control_root"]) / ".noodle/orders-next.json"
        require(mailbox.is_file(), "amendment.proposal.outcome", "unknown",
                "fresh_canonical_promotion_readback_without_resend")
        require(read_json(mailbox, "amendment.proposal") ==
                issue_execution.correction_proposal(binding, state["envelope_sha256"]),
                "amendment.proposal.identity", "foreign", "selected_proposal_readback")
        return {"action": "correction_proposal_pending", "published": False}
    require(prompt == issue_execution.projection(binding, state["envelope_sha256"], "supervised")
            and stage.get("skill") == "execute" and stage.get("provider") == "codex"
            and stage.get("model") == authorization["carrier"]["codex"]["model"],
            "amendment.promotion", "mismatch", "exact_canonical_replacement")
    if state.get("correction_release") is None:
        require(order.get("status") == "active" and stage.get("status") == "pending"
                and stage.get("attempts") == state["correction_failed_attempts"]
                and not owner["state"].get("pending_reviews"),
                "amendment.promotion.hold", stage.get("status"), "undispatched_replacement")
        epoch = owner["state"].get("mode_epoch")
        require(type(epoch) is int and epoch >= 0
                and state.get("correction_release_epoch", epoch) == epoch,
                "amendment.release.epoch", epoch, "unchanged_pre_release_mode_epoch")
        state["correction_release_epoch"] = epoch
        save_json(paths["state"], state)
    ack = amendment_control(authorization, paths, state, "correction_release", release)
    if ack is None:
        return {"action": "correction_release_pending"}
    require(owner["state"].get("mode") == "supervised"
            and owner["state"].get("mode_epoch") == state["correction_release_epoch"] + 1,
            "amendment.release.transition", owner["state"].get("mode"),
            "canonical_supervised_mode_after_ack")
    state["noodle_amendment"] = {"order_id": order_id,
                                  "envelope_sha256": state["envelope_sha256"],
                                  "release_ack": ack}
    save_json(paths["state"], state)
    return {"action": "correction_released"}


def complete_noodle(authorization, paths, state, transition):
    """Reconcile the original order after the external owner has landed it."""
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
    publication_claim = read_json(paths["claim"], "publication.claim")
    require(publication_claim.get("order_id") == order_id
            and publication_claim.get("head") == claim["head"]
            and publication_claim.get("tree") == claim["tree"],
            "noodle.completion.claim", "changed", "original_publication_claim")
    binary = authorization["noodle"]
    require(digest_file(binary["path"]) == binary["sha256"],
            "noodle.completion.binary", "changed", "selected_noodle_reconciler")
    argv = [binary["path"], "--project-dir", str(root), "publication", "reconcile",
            str(paths["claim"]), digest_file(paths["claim"]), landing_state["merge_sha"]]
    intent = {"argv": argv, "order_id": order_id, "head": claim["head"],
              "merge_head": landing_state["merge_sha"]}
    prior = state.get("noodle_reconciliation")
    require(prior is None or prior["intent"] == intent,
            "noodle.completion.intent", "changed", "original_reconciliation_identity")
    owner = issue_execution.read_owner(binding)
    order = owner["state"]["orders"].get(order_id)
    if prior is not None and prior.get("status") == "observed":
        completion = issue_execution.completed_original_order(binding, owner, publication_claim)
        prior.update(status="observed", completion=completion)
        save_json(paths["state"], state)
        return
    if order is None:
        issue_execution.completed_original_order(binding, owner, publication_claim)
    else:
        issue_execution.quiescent_order(binding, owner)
    # The stopped owner reconciles the published facts. An old merge ack does
    # not establish completion. A lost native result first needs owner readback.
    if not finish_host(authorization, paths, state, stop_only=True):
        return
    if prior is None:
        state["noodle_reconciliation"] = {"intent": intent, "status": "offered"}
        save_json(paths["state"], state)
    # Native recovery persists before/after custody and can resume an
    # interrupted projection. Re-entry never starts a merge or writer.
    state["noodle_reconciliation"]["process"] = {"status": "started", "started_ns": time.time_ns()}
    save_json(paths["state"], state)
    started = time.monotonic()
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30, env=clean_child_env())
    except (subprocess.TimeoutExpired, OSError) as error:
        state["noodle_reconciliation"]["process"].update(
            status="unknown", error=type(error).__name__, seconds=round(time.monotonic() - started, 3))
        save_json(paths["state"], state)
        raise AtomRefusal("noodle.completion.process", type(error).__name__,
                          "selected_noodle_reconciler_readback") from None
    state["noodle_reconciliation"]["process"] = {
        "status": "completed", "exit_status": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
        "seconds": round(time.monotonic() - started, 3)}
    save_json(paths["state"], state)
    require(result.returncode == 0, "noodle.completion.reconcile",
            state["noodle_reconciliation"]["process"], "selected_noodle_reconciler_readback")
    completion = issue_execution.completed_original_order(binding, issue_execution.read_owner(binding), publication_claim)
    state["noodle_reconciliation"].update(status="observed", completion=completion)
    save_json(paths["state"], state)


def host_manager(authorization, state):
    """Compile once; source identity remains checked outside the hot reducer."""
    root = Path(__file__).resolve().parent
    try:
        plan = schema_manager.compiled(root)
        plan.validate_sources(root)
        if resumed_lifecycle(authorization, state).get("lifecycle_owner"):
            validate_lifecycle_owner(resumed_lifecycle(authorization, state), executing=True)
        else:
            for name in ("schema_manager.py", schema_manager.PLAN_PATH):
                source = issue_admission.git_bytes(
                    authorization["control_root"], authorization["base_head"], name)
                require(digest_bytes(source) == plan.sources[name], "host_finalization.source", name,
                        "supervisor_selected_lifecycle_source")
        start = state.get("noodle_start")
        subject = {"repository": authorization["repository"],
                   "root": authorization["control_root"], "base": authorization["base_head"],
                   "envelope": state.get("envelope_sha256"),
                   "start": None if start is None else {k: start.get(k) for k in
                       ("pid", "argv", "config_sha256", "original_config")}}
        identity = {"authorization": state["authorization_sha256"],
                    "subject": schema_manager.digest(subject), "plan": plan.identity}
        return schema_manager.Manager(plan, identity, state.get("host_finalization"))
    except schema_manager.SchemaRefusal as error:
        raise AtomRefusal("host_finalization", str(error), "original_owner_readback") from error


def resume_host_finalization(authorization, state):
    """Carry the original facts/sequence across an explicitly selected source change."""
    record = state.get("host_finalization")
    if record is None:
        return
    resumed_lifecycle(authorization, state)
    previous = state["lifecycle_resume"]["from"]
    require(previous is not None, "lifecycle.resume.host_source", "missing",
            "original_pinned_host_finalization_source")
    old_root = Path(validate_lifecycle_owner({**authorization, "lifecycle_owner": previous})).parent
    try:
        old_plan = schema_manager.compiled(old_root)
        old_plan.validate_sources(old_root)
        current = host_manager(authorization, {k: v for k, v in state.items() if k != "host_finalization"})
        require(old_plan.rules == current.plan.rules
                and all(old_plan.context[key] == current.plan.context[key] for key in ("consumer", "requires"))
                and old_plan.affected == current.plan.affected,
                "lifecycle.resume.host_plan", "changed semantics", "unchanged_host_finalization_rules")
        schema_manager.Manager(old_plan, {**current.identity, "plan": old_plan.identity}, record)
        history = state.get("host_finalization_resume")
        require(history is None or (isinstance(history, dict)
                and history.get("identity") == record.get("identity")),
                "lifecycle.resume.host_history", "changed", "previous_host_projection_identity")
        transferred = {"prior": record, "identity": current.identity}
        if history is not None:
            transferred["previous"] = history
        state["host_finalization_resume"] = transferred
        state["host_finalization"] = {**record, "identity": current.identity}
    except schema_manager.SchemaRefusal as error:
        raise AtomRefusal("lifecycle.resume.host_finalization", str(error), "original_owner_readback") from error


def finish_host(authorization, paths, state, *, landing=None, stop_only=False):
    """Retire only this entry's own loop; restore only unchanged installed config."""
    if (not stop_only and state.get("noodle_completion")
            and state.get("noodle_reconciliation", {}).get("status") != "observed"):
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
    manager = host_manager(authorization, state)

    def check_sources():
        try:
            manager.plan.validate_sources(Path(__file__).resolve().parent)
        except (schema_manager.SchemaRefusal, OSError) as error:
            raise AtomRefusal("host_finalization.source", str(error),
                              "supervisor_selected_lifecycle_source") from error

    def observe(values, evidence):
        try:
            result = manager.observe({k: None if v is None else {
                                         "value": v, "evidence": schema_manager.digest(evidence),
                                         "producer": schema_manager.producer_key(manager.plan.catalog[k])}
                                      for k, v in values.items()})
        except schema_manager.SchemaRefusal as error:
            raise AtomRefusal("host_finalization", str(error), "original_owner_readback") from error
        record = manager.record()
        if state.get("host_finalization") != record:
            state["host_finalization"] = record
            save_json(paths["state"], state)
        return result

    def confirm():
        require("confirm" in manager.project()["ready"], "host_finalization.confirm", "missing physical facts",
                "original_owner_readback")
        # This owner, after its physical readback, produces confirmation. It is
        # never a prerequisite of shutdown or restoration.
        projection = observe({"owner_confirmed": True}, {
            "facts": {k: manager.facts.get(k) for k in ("landing_resolved", "loop_absent", "config_restored")},
            "ack": state.get("noodle_completion_ack")})
        return projection["status"] == "complete" if landing is not None else True

    observe({"cleanup_allowed": True}, {"authorization": state["authorization_sha256"]})
    observe({"landing_resolved": (None if landing is None or "classification" not in landing
                                  else landing["classification"] == "RESOLVED")}, landing)
    start = state.get("noodle_start")
    if start is None:
        if stop_only:
            return True  # Native reconciliation still requires the canonical lock.
        # No owned loop may be signalled; original config still needs readback.
        config = host_config_identity(authorization["control_root"])
        observe({"config_restored": config == authorization["host_config_sha256"]}, config)
        require(config == authorization["host_config_sha256"],
                "noodle.config.restored", "changed", "unchanged_host_configuration")
        observe({"loop_live": False, "loop_absent": True}, {"owned_start": None})
        return confirm()
    require(type(start.get("pid")) is int and start["pid"] > 1,
            "noodle.stop.pid", start.get("pid"), "original_start_process_readback")
    pid = start["pid"]
    observed = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    if observed.returncode == 0 and observed.stdout.strip():
        expected = " ".join(noodle_process_argv(authorization, start))
        if observed.stdout.strip() != expected:
            observe({"loop_live": False, "loop_absent": False}, {"pid": pid, "identity": "foreign"})
        require(observed.stdout.strip() == expected, "noodle.stop.identity", "changed",
                "original_start_process_readback")
        observe({"loop_live": True, "loop_absent": False}, {"pid": pid, "argv": expected})
        projection = observe({"stop_offered": bool(start.get("stop_offered"))}, bool(start.get("stop_offered")))
        if "stop" in projection["ready"]:
            check_sources()
            start["stop_offered"] = True
            save_json(paths["state"], state)
            observe({"stop_offered": True}, True)
            try:
                os.kill(pid, signal.SIGTERM)  # Noodle's documented shutdown path.
            except OSError as error:
                raise AtomRefusal("noodle.stop.outcome", type(error).__name__,
                                  "original_start_process_readback", owner="Noodle") from error
        return False
    if observed.returncode != 1:
        observe({"loop_live": False, "loop_absent": False}, {"pid": pid, "ps_exit": observed.returncode})
    require(observed.returncode == 1, "noodle.stop.readback", observed.returncode,
            "original_start_process_readback")
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        pass
    else:
        observe({"loop_live": False, "loop_absent": False}, {"pid": pid, "group_absent": False})
        raise AtomRefusal("noodle.stop.process_group", "present", "quiescent_noodle_owner")
    observe({"loop_live": False, "loop_absent": True}, {"pid": pid, "ps_exit": 1, "group_absent": True})
    if stop_only:
        return True  # Keep the installed configuration until reconciliation.
    if start.get("restored"):
        config = host_config_identity(authorization["control_root"])
        observe({"config_restored": config == authorization["host_config_sha256"]}, config)
        require(config == authorization["host_config_sha256"],
                "noodle.config.restored", "changed", "unchanged_host_configuration")
        return confirm()
    root = Path(authorization["control_root"])
    with (root / ".noodle/noodle.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("noodle.stop.owner", "running", "quiescent_noodle_owner") from None
        observed_config = host_config_identity(root)
        observe({"config_restored": observed_config == authorization["host_config_sha256"]}, observed_config)
        if start.get("restore_offered") and observed_config == authorization["host_config_sha256"]:
            start["restored"] = True
            save_json(paths["state"], state)
            return confirm()
        require(observed_config == start["config_sha256"],
                "noodle.config.restore", "changed", "unchanged_installed_configuration")
        original = start["original_config"]
        require((None if original is None else digest_bytes(base64.b64decode(original)))
                == authorization["host_config_sha256"], "noodle.config.backup", "changed")
        observe({"config_installed": True, "config_restored": False}, observed_config)
        projection = observe({"restore_offered": bool(start.get("restore_offered"))}, bool(start.get("restore_offered")))
        require("restore" in projection["ready"], "noodle.config.restore_outcome", "unknown",
                "original_host_recovery_readback")
        check_sources()
        start["restore_offered"] = True
        save_json(paths["state"], state)
        observe({"restore_offered": True}, True)
        try:
            if original is None:
                (root / ".noodle.toml").unlink()
            else:
                (root / ".noodle.toml").write_bytes(base64.b64decode(original))
        except OSError as error:
            raise AtomRefusal("noodle.config.restore_outcome", type(error).__name__,
                              "original_host_recovery_readback", owner="soodles.issue-atom") from error
        require(host_config_identity(root) == authorization["host_config_sha256"],
                "noodle.config.restored", "changed", "original_host_recovery_readback")
        start["restored"] = True
        save_json(paths["state"], state)
        observe({"config_installed": False, "config_restored": True}, authorization["host_config_sha256"])
    return confirm()


def _run_claim(authorization, subject, output, order_id):
    argv = [authorization["noodle"]["path"], "--project-dir", authorization["control_root"],
            "publication", "claim", order_id, subject]
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


def publish_candidate(authorization, state, paths, claim, acceptance, provider, repair=None):
    # The existing checkpoint owns process evidence as well as write intent.
    receipts = state.setdefault("publication_push_receipts", [])
    def record(receipt):
        if receipt["process"] == "started":
            receipts.append(receipt)
        else:
            require(receipts and receipts[-1]["process"] == "started"
                    and receipts[-1]["argv"] == receipt["argv"],
                    "publication.push.receipt", "unbound", "original_push_process_receipt")
            receipts[-1] = receipt
        save_json(paths["state"], state)
    def previous_rejected():
        if len(receipts) != 1 or candidate_publication.push_disposition(receipts[-1]) != "rejected":
            return False
        prior = authorization.get("prior_publication")
        branch = prior["branch"] if prior else f"soodles/issue-{claim['subject'].split('#')[1]}-{claim['head'][:12]}"
        lease = prior["head"] if prior else ""
        return (receipts[-1]["cwd"] == str(Path(claim["worktree_path"]).resolve())
                and receipts[-1]["argv"] == ["git", "push", "--porcelain",
                    "--force-with-lease=refs/heads/" + branch + ":" + lease,
                    "https://github.com/" + claim["repository"] + ".git",
                    claim["head"] + ":refs/heads/" + branch])
    push = authenticated_push(provider, record=record)
    if "prior_publication" not in authorization:
        def before_effect(action):
            key = "publication_" + action
            require(key not in state["writes"] or (action == "branch_push" and previous_rejected()), "publication.effect", action,
                    "fresh_provider_readback_without_retry")
            state["writes"][key] = {"head": claim["head"], "status": "offered"}
            save_json(paths["state"], state)
        return candidate_publication.publish(
            Path(claim["worktree_path"]), acceptance, claim, provider,
            push=push, before_effect=before_effect,
            refresh=(lambda number, confirm: refresh_publication(repair, provider, number, confirm))
            if repair is not None and state.get("repair") is not None and repair.disabled is None else None)
    intent = {"old_head": authorization["prior_publication"]["head"],
              "new_head": claim["head"],
              "pr": authorization["prior_publication"]["pr"]["number"],
              "status": "offered"}
    prior_intent = state["writes"].get("candidate_amendment")
    require(prior_intent is None or prior_intent == intent,
            "amendment.intent", prior_intent, "unchanged_offered_candidate")
    if prior_intent is None:
        state["writes"]["candidate_amendment"] = intent
        save_json(paths["state"], state)
    return candidate_publication.publish_amendment(
        Path(claim["worktree_path"]), acceptance, claim, provider,
        authorization["prior_publication"], offered=True,
        push=push if prior_intent is None or previous_rejected() else None,
        previous_push=receipts[-1] if receipts else None,
        refresh=(lambda number, confirm: refresh_publication(repair, provider, number, confirm))
        if repair is not None and state.get("repair") is not None and repair.disabled is None else None)


def refresh_publication(repair, provider, number, confirm):
    from provider_readback import ReadbackRefusal
    try:
        return repair.perform("stale_pr", lambda remaining: provider.repair_pull(number, remaining()), confirm)
    except (ReadbackRefusal, OSError, subprocess.TimeoutExpired) as error:
        raise AtomRefusal("repair.readback", type(error).__name__,
                          "fresh_provider_readback_without_retry", owner="GitHub") from error


def repair_binding(authorization, policy, *, source_root=None):
    # Candidate head and prior-reference fields are continuity, not permission to
    # change the original evidence requirements or independently selected judge.
    fixed = {key: authorization.get(key) for key in (
        "repository", "control_root", "base_head", "noodle", "carrier", "workflow",
        "landing_owner", "lifecycle_owner")}
    fixed["issue"] = {key: authorization["issue"][key] for key in ("title", "body")}
    root = Path(__file__).resolve().parent if source_root is None else Path(source_root)
    source = {name: digest_file(root / name) for name in LIFECYCLE_FILES}
    return atom_repair.digest({"authorization": fixed, "policy": policy, "source": source})


def resumed_repair_controller(authorization, state, paths, authorization_path):
    """Validate historical repair authority without transferring its effects."""
    from system_context import compile_repair

    require(authorization_path is not None
            and digest_file(authorization_path) == state.get("authorization_sha256")
            and read_json(authorization_path, "repair.authorization") == authorization,
            "repair.authorization", "changed", "original_authorization_bytes")
    selected = resumed_lifecycle(authorization, state)
    validate_lifecycle_owner(selected, executing=True)
    if state.get("scope_amendment") is not None:
        scope_packet(authorization, state)
        disabled = "scope_amendment_preserves_original_repair_authority"
    elif state.get("correction_start_recovery") is not None:
        correction_start_record(authorization, state)
        disabled = "startup_resume_preserves_original_repair_authority"
    else:
        postwrite_lifecycle(authorization, state, paths, allow_resolved=True)
        disabled = "postwrite_resume_preserves_original_repair_authority"
    if state.get("repair") is None:
        root = Path(__file__).resolve().parent
        policy = atom_repair.load((root / atom_repair.POLICY_PATH).read_bytes())
        return atom_repair.Controller(state, policy, repair_binding(authorization, policy),
            lambda: save_json(paths["state"], state), disabled=disabled)
    require(authorization.get("lifecycle_owner") is not None,
            "repair.original_owner", "missing", "original_pinned_repair_source")
    original = Path(validate_lifecycle_owner(authorization)).parent
    require(all((original / name).is_file() for name in LIFECYCLE_FILES),
            "repair.original_source", "incomplete", "original_complete_repair_source_closure")
    policy = atom_repair.load((original / atom_repair.POLICY_PATH).read_bytes())
    context = compile_repair(original)
    binding = repair_binding(authorization, policy, source_root=original)
    controller = atom_repair.Controller(state, policy, binding, lambda: save_json(paths["state"], state),
                                       context=context)
    record, _ = controller.check()
    require(record["lineage"] == state["authorization_sha256"],
            "repair.lineage", "changed", "original_authorization_repair_history")
    require(all(item["status"] == "confirmed" for item in record["history"]),
            "repair.original_effect", "unresolved", "original_repair_owner_readback_without_retry")
    controller.disabled = disabled
    return controller


def repair_controller(authorization, state, paths, *, fresh=False, authorization_path=None):
    if state.get("lifecycle_resume") is not None:
        return resumed_repair_controller(authorization, state, paths, authorization_path)
    root = Path(__file__).resolve().parent
    raw = (root / atom_repair.POLICY_PATH).read_bytes()
    policy = atom_repair.load(raw)
    binding = repair_binding(authorization, policy)
    # Independent successors cannot share mutable counters safely. No copying,
    # reset or new ledger; prior history stays with its original owner.
    disabled = "exclusive_lineage_continuity_required" if (
        "prior_atom" in authorization or "prior_publication" in authorization) else None
    context = {}
    if state.get("repair") is not None:
        context = json.loads(json.dumps(state["repair"].get("context", {})))
    if fresh and disabled is None and "number" not in authorization["issue"]:
        # Only this owner creating a new Issue can establish a new lineage.
        # Adopted Issues and legacy checkpoints remain normally operable.
        if authorization.get("lifecycle_owner") is not None:
            validate_lifecycle_owner(resumed_lifecycle(authorization, state), executing=True)
            trusted = True
        else:
            trusted = True
            names = ("atom_repair.py", atom_repair.POLICY_PATH) + LIFECYCLE_FILES
            for name in dict.fromkeys(names):
                result = subprocess.run(["git", "show", authorization["base_head"] + ":" + name],
                                        cwd=authorization["control_root"], capture_output=True, timeout=30)
                if result.returncode != 0 and name in {"atom_repair.py", atom_repair.POLICY_PATH}:
                    trusted = False  # Legacy base without repair bindings.
                    break
                require(result.returncode == 0, "repair.source", name,
                        "complete_supervisor_selected_repair_source")
                require(result.stdout == (root / name).read_bytes(), "repair.source", name,
                        "unchanged_supervisor_selected_repair_source")
        if trusted:
            from system_context import compile_repair
            context = compile_repair(root)
            state["repair"] = atom_repair.new_history(state["authorization_sha256"], binding, policy, context=context)
    def invariants():
        from system_context import compile_repair
        require(compile_repair(root) == context, "repair.context", "changed compiled closure")
        require(repair_binding(authorization, policy) == binding,
                "repair.source", "changed", "original_source_and_authorization_binding")
        _, evidence_paths = scope_projection(authorization, state, paths)
        files = {}
        for name in ("claim", "acceptance", "envelope"):
            # These inputs have already passed the owning publication boundary.
            # Their absence is not a stable invariant that can confirm repair.
            require(evidence_paths[name].is_file(), "repair.evidence." + name, str(evidence_paths[name]),
                    "unchanged_required_publication_evidence")
            files[name] = digest_file(evidence_paths[name])
        claim = read_json(paths["claim"], "publication_claim")
        acceptance = read_json(paths["acceptance"], "acceptance")
        candidate_publication.validate_inputs(Path(claim["worktree_path"]), acceptance, claim)
        require(files["envelope"] == state.get("envelope_sha256"),
                "repair.evidence.envelope", "changed", "original_execution_envelope")
        if authorization_path is not None:
            files["authorization"] = digest_file(authorization_path)
            require(files["authorization"] == state["authorization_sha256"],
                    "repair.authorization", "changed", "original_authorization_bytes")
        return {"files": files, "writes": atom_repair.digest(state.get("writes")),
                "publication_source": atom_repair.digest(state.get("publication_source")),
                "binding": binding}
    controller = atom_repair.Controller(state, policy, binding, lambda: save_json(paths["state"], state),
                                       invariants=invariants, context=context, disabled=disabled)
    if state.get("repair") is not None and disabled is None:
        controller.check()  # Changed policy/invariants refuse before normal effects too.
    return controller


def restore_publication(state, claim, repair):
    if state.get("publication") is not None:
        return state["publication"]
    source = state.get("publication_source")
    def valid(value):
        if not isinstance(source, dict) or set(source) != {"claim_sha256", "value", "sha256"}:
            return False
        if source["claim_sha256"] != atom_repair.digest(claim) or source["sha256"] != atom_repair.digest(value):
            return False
        candidate_publication.validate_amendment_prior(
            value, claim["repository"], claim["subject"], int(claim["subject"].split("#")[1]))
        return value["head"] == claim["head"] and value["tree"] == claim["tree"]
    require(isinstance(source, dict) and valid(source.get("value")), "repair.projection.source", "missing or changed",
            "unchanged_validated_publication_source")
    result = repair.perform("missing_projection", lambda remaining: json.loads(json.dumps(source["value"])), valid)
    state["publication"] = result
    repair.save()
    return result


def authenticated_push(provider, *, record=None):
    token = getattr(provider, "token", "")
    require(isinstance(token, str) and token, "github.credential", "missing",
            "repository_scoped_installation_token_in_GH_TOKEN")
    encoded = base64.b64encode(("x-access-token:" + token).encode()).decode()

    def push(root, *args, check=False):
        # The validated origin may be SSH. Pin this invocation to the same
        # repository over HTTPS so the selected installation token is actually used.
        repository = provider.repository
        endpoint = "https://github.com/" + repository + ".git"
        require(args[0:2] == ("push", "--porcelain") and args[-2] == "origin",
                "git.push.argv", "unexpected", "exact_publication_push")
        argv = ["git", *args[:-2], endpoint, args[-1]]
        env = clean_child_env()
        for key in list(env):
            if key.startswith(("GIT_CONFIG_", "GIT_TRACE", "GIT_CURL_VERBOSE")):
                env.pop(key)
        env.update({
            "GIT_CONFIG_COUNT": "3",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": "Authorization: Basic " + encoded,
            "GIT_CONFIG_KEY_1": "credential.helper", "GIT_CONFIG_VALUE_1": "",
            "GIT_CONFIG_KEY_2": "core.askPass", "GIT_CONFIG_VALUE_2": "",
            "GIT_TERMINAL_PROMPT": "0",
        })
        receipt = candidate_publication.run_push(
            root, argv, env=env, secrets=(token, encoded), record=record)
        if check and receipt["exit_status"] != 0:
            raise AtomRefusal("git.push", receipt["exit_status"], "fresh_provider_branch_readback")
        return receipt
    return push


def select_run(provider, authorization, head, *, allow_failure=False):
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
    require(step[0].get("status") == "completed", "github.workflow_step.status",
            step[0].get("status"), "fresh_exact_head_ci")
    if (allow_failure and run.get("conclusion") == target[0].get("conclusion") == "failure"
            and step[0].get("conclusion") in {"failure", "skipped"}):
        return run, jobs
    require(run.get("conclusion") == target[0].get("conclusion") == step[0].get("conclusion") == "success",
            "github.workflow.conclusion",
            [run.get("conclusion"), target[0].get("conclusion"), step[0].get("conclusion")],
            "new_candidate_head_after_failed_ci")
    return run, jobs


def verify_failed_prior(provider, authorization, *, failed_ci_only=False):
    """Prove correction of a failed CI or an exact pre-write publisher refusal."""
    prior = authorization["prior_publication"]
    number = authorization["issue"]["number"]
    branch = prior["branch"]
    repository = provider.repository_info()
    base_branch = repository.get("default_branch") if isinstance(repository, dict) else None
    require(isinstance(repository, dict)
            and repository.get("full_name") == authorization["repository"]
            and isinstance(base_branch, str)
            and provider.base_head(base_branch) == authorization["base_head"],
            "amendment.prior_base", repository, "exact_current_provider_base")
    pull = provider.pull(prior["pr"]["number"])
    require(isinstance(pull, dict) and pull.get("number") == prior["pr"]["number"]
            and pull.get("state") == "open" and pull.get("merged") is not True
            and pull.get("head", {}).get("ref") == branch
            and pull.get("head", {}).get("sha") == prior["head"]
            and pull.get("base", {}).get("ref") == base_branch
            and pull.get("body") == "Refs " + authorization["repository"] + "#" + str(number),
            "amendment.prior_pr", pull, "exact_failed_open_pr")
    remote = provider.branch(branch)
    require(isinstance(remote, dict)
            and remote.get("object", {}).get("sha") == prior["head"],
            "amendment.prior_branch", remote, "exact_failed_branch_readback")
    run_value, jobs = select_run(provider, authorization, prior["head"], allow_failure=True)
    failed = run_value is not None and run_value.get("status") == "completed" and run_value.get("conclusion") == "failure"
    if not failed:
        require(not failed_ci_only and run_value is not None and jobs is not None
                and prewrite_scope_refusal(authorization, run_value, jobs),
                "amendment.prior_runtime", "not failed",
                "terminal_failed_exact_head_runtime_or_pinned_prewrite_scope_refusal")
        return None
    return run_value, jobs


def failed_ci_context(provider, authorization, run_value, jobs, diagnostic_path):
    """Pin observed failure metadata and return raw log bytes for atomic preparation."""
    prior = authorization["prior_publication"]
    number = authorization["issue"]["number"]
    job = next(job for job in jobs["jobs"] if job.get("name") == authorization["workflow"]["job"])
    data = {"schema": 1, "repository": authorization["repository"], "issue": number,
            "pr": prior["pr"]["number"], "head": prior["head"],
            "workflow": authorization["workflow"], "run": run_value, "jobs": jobs,
            "diagnostics": [{"job_id": job.get("id"), "log": None,
                             "gap": "diagnostic_not_fetched"}]}
    context = {"data": data, "sha256": issue_admission.failure_digest(data)}
    issue_admission.validate_failure_context(context, authorization["repository"], number,
                                             prior["head"], authorization["workflow"], prior["pr"]["number"])
    diagnostic = provider.job_log(job["id"])
    raw = diagnostic["raw"]
    require(diagnostic["job_id"] == job["id"]
            and ((isinstance(raw, bytes) and diagnostic["gap"] is None)
                 or (raw is None and isinstance(diagnostic["gap"], str) and diagnostic["gap"])),
            "failure_context.diagnostic", "invalid", "exact_failed_ci_evidence")
    data["diagnostics"] = [{"job_id": job["id"], "gap": diagnostic["gap"],
        "log": None if raw is None else {"path": str(diagnostic_path),
            "sha256": digest_bytes(raw), "bytes": len(raw)}}]
    context["sha256"] = issue_admission.failure_digest(data)
    issue_admission.validate_failure_context(context, authorization["repository"], number,
                                             prior["head"], authorization["workflow"], prior["pr"]["number"])
    return context, raw


def prewrite_scope_refusal(authorization, run_value, jobs):
    """Allow source correction, never landing, after a pinned step-scope refusal."""
    ref = authorization.get("prior_atom")
    if ref is None:
        return False
    validate_prior_atom_ref(ref, authorization["control_root"])
    old = read_json(ref["path"], "amendment.prior_authorization")
    publisher = validate_landing_owner(old)
    paths = artifact_paths(ref["path"])
    records = list(paths["directory"].glob("landing-start-*.json"))
    if paths["landing"].exists() or len(records) != 1:
        return False
    record = read_json(records[0], "amendment.prewrite_receipt")
    try:
        result = json.loads(record["stdout"])
    except (KeyError, TypeError, ValueError):
        return False
    claim = read_json(paths["directory"] / "landing-claim.json", "amendment.prewrite_claim")
    prior = authorization["prior_publication"]
    return (record.get("exit_status") not in (None, 0)
            and record.get("argv") == [sys.executable, "-B", str(publisher), "landing", "start",
                str(paths["directory"] / "landing-claim.json"),
                str(paths["directory"] / "readback.json"), str(paths["landing"])]
            and isinstance(result, dict) and result.get("owner") == "landing.start"
            and result.get("status") == "refused" and "request" not in result
            and result.get("invalid", {}).get("field") == "job.steps"
            and any(result["invalid"].get("value") == job.get("steps") for job in jobs["jobs"])
            and all(claim.get(key) == value for key, value in {
                "repository": authorization["repository"], "issue": authorization["issue"]["number"],
                "pr": prior["pr"]["number"], "head": prior["head"], "tree": prior["tree"],
                "base_head": authorization["base_head"], "run_id": run_value["id"],
                "run_attempt": run_value["run_attempt"],
                "verifier_sha256": old["landing_owner"]["verifier_sha256"]}.items()))


def observe_prior_loop(authorization, prior_state):
    """Distinguish the original loop's durable status from OS custody."""
    root = Path(authorization["control_root"]).resolve()
    start = prior_state.get("noodle_start")
    require(isinstance(start, dict) and start.get("status") == "started"
            and type(start.get("pid")) is int and start["pid"] > 1,
            "amendment.prior_loop", start, "original_start_process_readback")
    pid = start["pid"]
    observed = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                              capture_output=True, text=True)
    expected = " ".join(noodle_process_argv(authorization, start))
    if observed.returncode == 0 and observed.stdout.strip():
        require(observed.stdout.strip() == expected,
                "amendment.prior_loop.identity", "changed", "original_start_process_readback")
        loop_status = "running"
    else:
        require(observed.returncode == 1,
                "amendment.prior_loop.readback", observed.returncode,
                "original_start_process_readback")
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            raise AtomRefusal("amendment.prior_loop.group", type(error).__name__,
                              "quiescent_noodle_owner") from error
        else:
            raise AtomRefusal("amendment.prior_loop.group", "present",
                              "quiescent_noodle_owner")
        loop_status = "stopped"
    lock_path = root / ".noodle/noodle.lock"
    require(lock_path.is_file(), "amendment.prior_loop.lock", "missing",
            "canonical_noodle_lock_readback")
    try:
        with lock_path.open("r+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_held = True
            else:
                lock_held = False
    except OSError as error:
        raise AtomRefusal("amendment.prior_loop.lock", type(error).__name__,
                          "canonical_noodle_lock_readback") from error
    require(lock_held == (loop_status == "running"),
            "amendment.prior_loop.lock", lock_held,
            "matching_process_and_noodle_lock")
    if start.get("restored") is True:
        require(loop_status == "stopped"
                and host_config_identity(root) == authorization["host_config_sha256"],
                "amendment.prior_loop.restored", "mismatch",
                "original_host_configuration_readback")
        return "restored"
    return loop_status


def verify_prior_atom(authorization):
    """Read the selected old lifecycle and the exact parked Noodle review."""
    ref = authorization["prior_atom"]
    root = Path(authorization["control_root"]).resolve()
    validate_prior_atom_ref(ref, root)
    prior_path = Path(ref["path"])
    prior_auth = read_json(prior_path, "amendment.prior_authorization")
    prior_paths = artifact_paths(prior_path)
    prior_state = read_json(prior_paths["state"], "amendment.prior_state")
    prior_auth, prior_paths = scope_projection(prior_auth, prior_state, prior_paths)
    old = authorization["prior_publication"]
    number = authorization["issue"]["number"]
    require(prior_auth.get("repository") == authorization["repository"]
            and prior_auth.get("control_root") == str(root)
            and prior_auth.get("base_head") == authorization["base_head"]
            and prior_auth.get("noodle") == authorization["noodle"]
            and prior_auth.get("carrier") == authorization["carrier"]
            and prior_state.get("authorization_sha256") == ref["sha256"]
            and prior_state.get("phase") == "ci"
            and prior_state.get("issue", {}).get("number") == number
            and prior_state.get("publication") == old
            and not prior_state.get("landing_activation")
            and not prior_paths["landing"].exists(),
            "amendment.prior_state", prior_state.get("phase"),
            "exact_prelanding_failed_candidate")
    prior_claim = read_json(prior_paths["claim"], "amendment.prior_claim")
    prior_envelope = read_json(prior_paths["envelope"], "amendment.prior_envelope")
    require(digest_file(prior_paths["envelope"]) == prior_state.get("envelope_sha256")
            and prior_claim.get("repository") == authorization["repository"]
            and prior_claim.get("subject") == authorization["repository"] + "#" + str(number)
            and prior_claim.get("head") == old["head"]
            and prior_claim.get("tree") == old["tree"]
            and prior_claim.get("base_head") == authorization["base_head"]
            and prior_envelope.get("repository") == authorization["repository"]
            and prior_envelope.get("issue") == number
            and prior_envelope.get("base_head") == authorization["base_head"],
            "amendment.prior_claim", prior_claim, "same_published_noodle_candidate")
    execution = prior_envelope.get("execution", {})
    order_id = issue_admission.scoped_order_id(number, root)
    worktree = execution.get("worktree")
    worktree_path = root / ".worktrees" / str(worktree)
    require(execution.get("order_id") == order_id
            and execution.get("control_root") == str(root)
            and prior_claim.get("order_id") == order_id
            and prior_claim.get("worktree_name") == worktree
            and prior_claim.get("worktree_path") == str(worktree_path)
            and worktree_path.is_dir(),
            "amendment.prior_order", order_id, "exact_original_noodle_order")
    prior_body = authorized_issue_body(prior_auth, prior_state["authorization_sha256"])
    require(prior_envelope["body_sha256"] == digest_bytes(prior_body.encode()),
            "amendment.prior_envelope.body_sha256", "changed", "original_execution_envelope")
    old_binding = {**prior_envelope, "contract": issue_admission.parse_contract(prior_body),
                   "issue_body": prior_body}
    try:
        owner = issue_execution.read_owner(old_binding)
        order = owner["state"]["orders"].get(order_id)
        issue_execution.quiescent_order(old_binding, owner)
    except issue_admission.AdmissionRefusal as error:
        raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                          error.next["required"][0], owner="Noodle") from error
    require(isinstance(order, dict) and order.get("status") == "active"
            and len(order.get("stages", [])) == 1,
            "amendment.prior_order", order, "single_original_review")
    stage = order["stages"][0]
    attempts = stage.get("attempts")
    require(stage.get("status") == "review"
            and stage.get("skill") == "execute"
            and stage.get("provider") == "codex"
            and stage.get("model") == authorization["carrier"]["codex"]["model"]
            and isinstance(attempts, list) and bool(attempts)
            and all(isinstance(attempt, dict) for attempt in attempts)
            and all(attempt.get("status") == "failed" for attempt in attempts[:-1])
            and all(isinstance(attempt.get("session_id"), str)
                    and attempt["session_id"] for attempt in attempts)
            and len({attempt["session_id"] for attempt in attempts}) == len(attempts)
            and attempts[-1].get("status") == "completed"
            and attempts[-1].get("session_id") == prior_claim.get("session_id"),
            "amendment.prior_review", stage.get("status"), "completed_original_attempt")
    try:
        prompt = json.loads(stage.get("prompt", ""))
    except (TypeError, ValueError):
        prompt = None
    require(prompt == issue_execution.projection(
        old_binding, prior_state["envelope_sha256"], "supervised"),
        "amendment.prior_prompt", prompt, "original_admitted_task")
    reviews = owner["state"].get("pending_reviews", {})
    require(isinstance(reviews, dict) and set(reviews) == {order_id},
            "amendment.prior_reviews", list(reviews) if isinstance(reviews, dict) else reviews,
            "one_original_pending_review")
    require(_git(worktree_path, "rev-parse", "HEAD") == old["head"]
            and _git(worktree_path, "rev-parse", "HEAD^{tree}") == old["tree"]
            and _git(worktree_path, "status", "--porcelain", "--untracked-files=all") == "",
            "amendment.prior_worktree", str(worktree_path), "clean_published_candidate")
    loop_status = observe_prior_loop(authorization, prior_state)
    return {"order_id": order_id, "worktree": worktree,
            "worktree_path": str(worktree_path),
            "prior_envelope_sha256": prior_state["envelope_sha256"],
            "owner_snapshot_sha256": digest_file(root / ".noodle/state.snapshot.json"),
            "prior_loop_status": loop_status}


def recover_prior_host(authorization, paths, state):
    """Retire only the selected original loop through its existing owner."""
    prior = verify_prior_atom(authorization)
    require(prior["prior_loop_status"] in {"running", "stopped"},
            "amendment.prior_host.status", prior["prior_loop_status"])
    ref = authorization["prior_atom"]
    old_path = Path(ref["path"])
    old_auth = read_json(old_path, "amendment.prior_authorization")
    old_paths = artifact_paths(old_path)
    old_state = read_json(old_paths["state"], "amendment.prior_state")
    _, old_paths = scope_projection(old_auth, old_state, old_paths)
    old_binding = read_json(old_paths["envelope"], "amendment.prior_envelope")
    owner = issue_execution.read_owner(old_binding)
    for order_id, order in owner["state"]["orders"].items():
        if order_id == "schedule" and native_idle_schedule(
                order, authorization["carrier"]["codex"]["model"]):
            continue
        try:
            issue_execution.quiescent_order(
                {"execution": {"control_root": authorization["control_root"],
                               "order_id": order_id}}, owner)
        except issue_admission.AdmissionRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              error.next["required"][0], owner="Noodle") from error
    runtime = Path(authorization["control_root"]) / ".noodle"
    for process in sorted((runtime / "sessions").glob("*/process.json")):
        try:
            issue_execution._absent_process(process.parent, process.parent.name)
        except issue_admission.AdmissionRefusal as error:
            raise AtomRefusal(error.invalid["field"], error.invalid["value"],
                              error.next["required"][0], owner="Noodle") from error
    intent = {"prior_authorization_sha256": ref["sha256"],
              "order_id": prior["order_id"], "status": "offered"}
    if "prior_host_recovery" not in state:
        state["prior_host_recovery"] = intent
        save_json(paths["state"], state)
    else:
        require(state["prior_host_recovery"] in (intent, {**intent, "status": "restored"}),
                "amendment.prior_host.intent", state["prior_host_recovery"],
                "same_original_host_recovery")
    if not finish_host(old_auth, old_paths, old_state):
        return False
    require(host_config_identity(authorization["control_root"])
            == authorization["host_config_sha256"],
            "amendment.prior_host.config", "changed",
            "original_host_configuration_readback")
    state["prior_host_recovery"] = {**intent, "status": "restored"}
    save_json(paths["state"], state)
    return True


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
    # The validated control root is also serialized across authorizations.
    try:
        lock = Path(authorization_path).open("rb")
    except OSError as error:
        raise AtomRefusal("authorization.path", type(error).__name__,
                          "readable_external_authorization") from None
    with lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("authorization.busy", str(authorization_path),
                              "current_same_entry_owner_readback", owner="soodles.issue-atom") from None
        # Telemetry failure never suppresses unknown-write readback or cleanup.
        handle, telemetry_error = None, None
        try:
            selected = os.environ if environ is None else environ
            if selected.get("SOODLES_AUTHORIZATION_SHA256") == digest_file(authorization_path):
                handle = cost_telemetry.begin(authorization_path, save_json)
        except (OSError, ValueError, KeyError, TypeError) as error:
            telemetry_error = error
        try:
            result = _run(authorization_path, environ=environ, provider=provider)
        except AtomRefusal as error:
            result = refusal_output(error, authorization_path)
            result["cost"] = cost_response(authorization_path, handle, result, telemetry_error)
            result["feedback"] = schema_manager.project_owner_feedback(result)
            error.owner_result = result
            raise
        cost = cost_response(authorization_path, handle, result, telemetry_error)
        if isinstance(result.get("status"), str):
            result["cost"] = cost
            result["feedback"] = schema_manager.project_owner_feedback(result)
        else:
            print(json.dumps({"event": "soodles.cost", **cost}), file=sys.stderr)
        return result


def cost_response(authorization_path, handle, result, error=None):
    try:
        if error is not None:
            raise error
        if handle is not None:
            return cost_telemetry.finish(authorization_path, handle, result, save_json)
        return cost_telemetry.report(authorization_path, result=result)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return cost_telemetry.failure(error)


native_idle_schedule = issue_execution.native_idle_schedule


def own_start_wait(authorization, paths, state, binding, owner, refuse):
    """Prove only a bounded read-only wait, never admission or effect custody."""
    root = Path(authorization["control_root"])
    runtime = root / ".noodle"
    order_id = binding["execution"]["order_id"]
    model = binding["execution"]["carrier"]["codex"]["model"]
    orders = owner["state"]["orders"]

    def check(condition, field, value="mismatch"):
        if not condition:
            refuse("noodle.wait." + field, value)

    start = state.get("noodle_start")
    check(state.get("phase") == "execution" and isinstance(start, dict), "phase")
    check(start.get("status") == "started" and not any(
        start.get(key) for key in ("stop_offered", "restore_offered", "restored")), "start")
    check(type(start.get("pid")) is int and start["pid"] > 1, "pid")
    # Bind the original producer bytes; matching installed config alone is not custody.
    prepared_path = paths["envelope"].parent / "prepared.json"
    captured = {}
    session_states = {}

    def meta_identity(value):
        check(isinstance(value, dict), "metadata")
        # Canonical JSON preserves scalar types (True must not equal 1).
        return json.dumps({key: value.get(key) for key in
                           ("session_id", "provider", "model", "runtime", "status", "alive")},
                          sort_keys=True)

    def owner_identity(value):
        # Observe all orders, including foreign additions. Timestamps and the
        # snapshot's event bookkeeping do not change this read-only wait.
        result = {}
        for oid, order in value["state"]["orders"].items():
            check(isinstance(order, dict), "order", oid)
            result[oid] = {key: item for key, item in order.items() if key != "updated_at"}
        return json.dumps(result, sort_keys=True)

    def read(path):
        raw = path.read_bytes()
        captured[path] = raw
        value = json.loads(raw)
        check(isinstance(value, dict), "metadata", str(path))
        return value

    prepared = read(prepared_path)
    check(digest_bytes(captured[prepared_path]) == state.get("admission_sha256"), "prepared")
    check(prepared.get("envelope_sha256") == state["envelope_sha256"]
          and prepared.get("action") == "ready", "prepared_binding")
    check(isinstance(prepared.get("next"), dict), "prepared_next")
    argv = prepared["next"].get("argv")
    check(argv == [prepared.get("start")] == start.get("argv"), "argv")
    check(isinstance(argv[0], str), "argv")
    captured[Path(argv[0])] = Path(argv[0]).read_bytes()
    check(digest_bytes(captured[Path(argv[0])]) == prepared.get("start_sha256"), "launcher")
    generated = paths["envelope"].parent / "noodle.toml"
    captured[generated] = generated.read_bytes()
    captured[root / ".noodle.toml"] = (root / ".noodle.toml").read_bytes()
    check(captured[generated] == captured[root / ".noodle.toml"] and
          digest_bytes(captured[generated]) == start.get("config_sha256"), "config")
    observed = subprocess.run(["ps", "-p", str(start["pid"]), "-o", "command="],
                              capture_output=True, text=True)
    expected = " ".join(noodle_process_argv(authorization, start))
    check(observed.returncode == 0 and observed.stdout.strip() == expected, "process")
    os.kill(start["pid"], 0)
    sessions = {}
    process_ids = {start["pid"]}
    for current_id, skill in (("schedule", "schedule"), (order_id, "execute")):
        order = orders.get(current_id)
        check(isinstance(order, dict) and order.get("order_id") == current_id
              and order.get("status") == "active", "order", current_id)
        stages = order.get("stages")
        check(isinstance(stages, list) and len(stages) == 1, "stages", current_id)
        stage = stages[0]
        check(type(stage.get("stage_index")) is int and stage["stage_index"] == 0
              and stage.get("task_key") == skill
              and stage.get("skill") == skill and stage.get("provider") == "codex"
              and stage.get("model") == model and stage.get("runtime") == "process",
              "stage", current_id)
        if skill == "schedule":
            check(stage.get("prompt") == "", "scheduler_prompt")
        else:
            subject = json.loads(stage.get("prompt", ""))
            check(isinstance(subject, dict) and subject.get("route") in ("automatic", "supervised")
                  and subject == issue_execution.projection(
                      binding, state["envelope_sha256"], subject["route"]), "projection")
        attempts = stage.get("attempts")
        if skill == "execute" and stage.get("status") == "pending":
            check(attempts in (None, []) or (
                state.get("correction_release") is not None
                and attempts == state.get("correction_failed_attempts")) or (
                state.get("scope_amendment", {}).get("status") == "released"
                and attempts == state["scope_amendment"]["requeued_attempts"]), "pending_attempts")
            continue
        check(stage.get("status") in ("dispatching", "running")
              and isinstance(attempts, list) and bool(attempts)
              and all(isinstance(a, dict) for a in attempts), "attempts", current_id)
        check(all(a.get("status") in ("launching", "running", "completed", "failed", "cancelled")
                  for a in attempts), "attempt_status", current_id)
        live = [a for a in attempts if a.get("status") in ("launching", "running")]
        check(len(live) == 1, "live_attempt", current_id)
        attempt = live[0]
        check((stage["status"], attempt["status"]) in
              (("dispatching", "launching"), ("running", "running")), "status_pair", current_id)
        sid = attempt.get("session_id")
        check(isinstance(sid, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]+", sid)), "session")
        check(isinstance(attempt.get("attempt_id"), str)
              and re.fullmatch(re.escape(current_id) + r"-0-attempt-[0-9]+",
                               attempt["attempt_id"]), "attempt_id")
        worktree = "" if skill == "schedule" else order_id + "-0-execute"
        check(attempt.get("worktree_name") == worktree, "worktree")
        directory = runtime / "sessions" / sid
        spawn, process, meta = (read(directory / name) for name in
                                ("spawn.json", "process.json", "meta.json"))
        session_states[directory / "meta.json"] = meta_identity(meta)
        del captured[directory / "meta.json"]
        check(all(value.get("session_id") == sid for value in (spawn, process, meta)), "session_binding")
        check(all(value.get("provider") == "codex" and value.get("model") == model
                  and value.get("runtime") == "process" for value in (spawn, meta)), "carrier")
        expected_path = root if skill == "schedule" else root / ".worktrees" / worktree
        check(spawn.get("skill") == skill and spawn.get("worktree_path") == str(expected_path), "spawn")
        check(meta.get("status") == attempt["status"] and meta.get("alive") is True, "meta")
        check(type(process.get("pid")) is int and process["pid"] > 1, "session_pid")
        check(process["pid"] not in process_ids, "distinct_processes")
        process_ids.add(process["pid"])
        os.kill(process["pid"], 0)
        sessions[skill] = sid
    check(len(set(sessions.values())) == len(sessions), "distinct_sessions")
    # The existing native lock must already exist and be held; never create it here.
    with (runtime / "noodle.lock").open("rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            refuse("noodle.wait.lock", "not_held")
        check(owner_identity(issue_execution.read_owner(binding)) == owner_identity(owner),
              "snapshot_changed")
        check(all(path.read_bytes() == raw for path, raw in captured.items()), "metadata_changed")
        check(all(meta_identity(json.loads(path.read_bytes())) == identity
                  for path, identity in session_states.items()), "metadata_changed")
    return {"action": "own_start_wait", "order_id": order_id, "sessions": sessions,
            "execute_status": orders[order_id]["stages"][0]["status"]}


def require_available_owner(authorization, paths, state):
    """Read Noodle custody before credentials, checkpoints or provider effects."""
    root = Path(authorization["control_root"])
    runtime = root / ".noodle"
    known = {"control_root": str(root)}
    if ("prior_atom" in authorization and state.get("phase") in {"issue", "execution"}
            and state.get("noodle_amendment") is None):
        # An externally selected correction may inspect the original parked
        # review. It gains no permission to mutate it from this readback.
        if state.get("noodle_start") is not None:
            correction_owner(authorization, paths, state)
            return
        prior = verify_prior_atom(authorization)
        if prior["prior_loop_status"] in {"stopped", "running"}:
            return {"action": "prior_loop_" + prior["prior_loop_status"], "owner": "Noodle",
                    "next": {"kind": "input", "owner": "original_issue_atom",
                             "required": ["original_host_recovery_before_new_bundle"],
                             "known": {"order_id": prior["order_id"]}}}
        return
    if state.get("phase") == "resolved" and (
            not state.get("noodle_start") or state["noodle_start"].get("restored") is True):
        return  # Historical readback still goes through the existing landing owner.

    def refuse(field, value, required="current_noodle_owner_readback"):
        raise AtomRefusal(field, value, required, owner="Noodle", known=dict(known))

    # A fresh root has no canonical owner yet. An incomplete existing runtime
    # is unknown, not an idle owner.
    if not (runtime / "state.snapshot.json").exists():
        if any(p.name != "issue-atom.lock" for p in runtime.iterdir()):
            refuse("noodle.snapshot", "missing", "canonical_checkpoint_readback")
        return
    try:
        owner = issue_execution.read_owner({"execution": {"control_root": str(root)}})
        orders = owner["state"]["orders"]
        blocking = []
        for order_id, order in orders.items():
            if (not isinstance(order, dict) or not isinstance(order.get("stages"), list)
                    or not order["stages"] or any(not isinstance(s, dict) for s in order["stages"])):
                refuse("noodle.order", order_id, "canonical_order_readback")
            if any(s.get("status") not in ("completed", "failed", "cancelled")
                   for s in order["stages"]):
                blocking.append(order_id)
        known["blocking_order_ids"] = blocking
        binding = None
        if state.get("envelope_sha256"):
            binding = issue_admission.load_external_envelope(
                paths["envelope"], state["envelope_sha256"], root)
            body = authorized_issue_body(authorization, state["authorization_sha256"])
            if (binding["repository"] != authorization["repository"]
                    or binding["issue"] != (state.get("issue") or {}).get("number")
                    or Path(binding["execution"]["control_root"]).resolve() != root.resolve()
                    or binding["base_head"] != authorization["base_head"]
                    or binding["body_sha256"] != digest_bytes(body.encode())):
                refuse("noodle.binding", "mismatch", "admitted_order_readback")
            binding["contract"] = issue_admission.parse_contract(body)
            binding["issue_body"] = body
        own_id = binding["execution"]["order_id"] if binding else None
        model = (binding["execution"]["carrier"]["codex"]["model"]
                 if binding else None)
        schedule = orders.get("schedule")
        active_schedule = (binding and state.get("noodle_start")
                           and isinstance(schedule, dict)
                           and schedule.get("status") == "active"
                           and len(schedule["stages"]) == 1
                           and schedule["stages"][0].get("status") in ("dispatching", "running")
                           and bool(schedule["stages"][0].get("attempts")))
        if active_schedule:
            if any(order_id not in (own_id, "schedule") for order_id in blocking):
                refuse("noodle.orders", "foreign_nonterminal", "quiescent_noodle_owner")
            return own_start_wait(authorization, paths, state, binding, owner, refuse)
        if any(order_id != own_id and not (
                order_id == "schedule" and state.get("noodle_start")
                and native_idle_schedule(orders[order_id], model)) for order_id in blocking):
            refuse("noodle.orders", "foreign_nonterminal", "quiescent_noodle_owner")
        exact_order = False
        if own_id in orders:
            stages = orders[own_id]["stages"]
            try:
                subject = json.loads(stages[0].get("prompt", ""))
            except (ValueError, TypeError):
                subject = None
            exact_order = (len(stages) == 1 and isinstance(subject, dict)
                           and subject.get("route") in ("automatic", "supervised")
                           and subject == issue_execution.projection(
                               binding, state["envelope_sha256"], subject["route"]))
            if not exact_order:
                refuse("noodle.order.binding", own_id, "admitted_order_readback")
            stage = stages[0]
            attempts = stage.get("attempts")
            if (state.get("scope_amendment", {}).get("status") == "released"
                    and stage.get("status") == "pending"
                    and attempts == state["scope_amendment"]["requeued_attempts"]):
                require(observe_prior_loop(authorization, state) == "running",
                        "scope.dispatch.owner", "stopped", "original_process_readback_without_restart")
                return {"action": "scope_dispatch_pending", "owner": "Noodle"}
            if (state.get("noodle_amendment") and stage.get("status") == "pending"
                    and attempts == state["correction_failed_attempts"]):
                correction_owner(authorization, paths, state)
                return {"action": "correction_dispatch_pending", "owner": "Noodle"}
            if (stage.get("skill") != "execute" or stage.get("provider") != "codex"
                    or stage.get("model") != binding["execution"]["carrier"]["codex"]["model"]
                    or not isinstance(attempts, list) or not attempts
                    or any(not isinstance(a, dict) for a in attempts)):
                refuse("noodle.order.stage", own_id, "current_dispatch_identity")
            live = [a for a in attempts if a.get("status") in ("launching", "running")]
            if live:
                if len(live) != 1 or stage.get("status") not in ("dispatching", "running"):
                    refuse("noodle.order.attempt", own_id, "current_dispatch_identity")
            else:
                issue_execution.quiescent_order(binding, owner)
        elif binding and state.get("phase") == "landing" and (
                state.get("noodle_completion") or state.get("noodle_reconciliation")):
            # Noodle may already have projected away the completed order while
            # this atom still needs its original shutdown/config cleanup.
            issue_execution.completed_original_order(
                binding, owner, read_json(paths["claim"], "publication.claim"))
            exact_order = True
        with (runtime / "noodle.lock").open("a+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                if not exact_order:
                    refuse("noodle.runtime", "foreign_or_unknown")
                generated = paths["envelope"].parent / "noodle.toml"
                if not generated.is_file() or host_config_identity(root) != digest_file(generated):
                    refuse("noodle.running.config", "foreign")
                return
            for order_id in orders:
                if (order_id == "schedule" and exact_order and state.get("noodle_start")
                        and native_idle_schedule(orders[order_id], model)):
                    continue  # Every actual session process is checked below.
                issue_execution.quiescent_order(
                    {"execution": {"control_root": str(root), "order_id": order_id}}, owner)
            for process in sorted((runtime / "sessions").glob("*/process.json")):
                issue_execution._absent_process(process.parent, process.parent.name)
    except issue_admission.AdmissionRefusal as error:
        refuse(error.invalid["field"], error.invalid["value"], error.next["required"][0])
    except (OSError, ValueError, TypeError) as error:
        if isinstance(error, AtomRefusal):
            raise
        refuse("noodle.readback", str(error), "canonical_checkpoint_readback")


def _run(authorization_path, *, environ=None, provider=None):
    environ = os.environ if environ is None else environ
    paths = artifact_paths(authorization_path)
    authorization, authorization_digest = _validate_authorization(
        authorization_path, environ.get("SOODLES_AUTHORIZATION_SHA256"),
        allow_advanced=paths["state"].exists())
    selected_state = read_json(paths["state"], "state") if paths["state"].exists() else {}
    if selected_state:
        require(selected_state.get("authorization_sha256") == authorization_digest,
                "state.authorization", "mismatch", "matching_lifecycle_checkpoint")
    selected_runtime = resumed_lifecycle(authorization, selected_state)
    validate_lifecycle_owner(selected_runtime, executing=True)
    runtime = Path(authorization["control_root"]) / ".noodle"
    runtime.mkdir(exist_ok=True)
    with (runtime / "issue-atom.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AtomRefusal("noodle.atom_entry", "busy", "current_same_entry_owner_readback",
                              owner="soodles.issue-atom",
                              known={"control_root": str(runtime.parent)}) from None
        selected_state = read_json(paths["state"], "state") if paths["state"].exists() else {}
        if selected_state:
            require(selected_state.get("authorization_sha256") == authorization_digest,
                    "state.authorization", "mismatch", "matching_lifecycle_checkpoint")
        require(resumed_lifecycle(authorization, selected_state).get("lifecycle_owner")
                == selected_runtime.get("lifecycle_owner"), "lifecycle.resume.race", "changed",
                "current_same_entry_owner_readback")
        try:
            return _run_owned(authorization_path, authorization, authorization_digest, paths,
                              environ=environ, provider=provider)
        except (AtomRefusal, candidate_publication.PublicationRefusal,
                atom_repair.RepairRefusal) as error:
            # Diagnostic projection only; preserve the invoked owner's next.
            state = read_json(paths["state"], "state") if paths["state"].exists() else {}
            if isinstance(error, AtomRefusal):
                result = refusal_output(error, authorization_path)
            else:
                result = {"owner": "soodles.issue-atom", "status": "refused",
                          "continuation_state": "input_required",
                          "invalid": getattr(error, "invalid", {"field": "process", "value": type(error).__name__}),
                          "next": getattr(error, "next", {
                              "kind": "input", "owner": "external-supervisor",
                              "required": ["material_owner_readback"],
                              "argv": same_command(authorization_path)}),
                          "authorizes_landing": False}
            if "host_finalization" in state:
                result["host_finalization_projection"] = host_projection(state["host_finalization"])
            if isinstance(error, candidate_publication.PublicationRefusal):
                result["next"] = {**result["next"], "argv": same_command(authorization_path)}
                result["push_receipts"] = state.get("publication_push_receipts", [])
                if (error.invalid["field"] == "github.push.rejected"
                        and len(state.get("publication_push_receipts", [])) >= 2):
                    result["next"]["required"] = ["push_rejection_budget_exhausted"]
            try:
                controller = repair_controller(authorization, state, paths,
                                               authorization_path=authorization_path)
                result["repair"] = controller.report(atom_repair.observation(error),
                                                     stop=getattr(error, "invalid", None)
                                                     if isinstance(error, atom_repair.RepairRefusal) else None)
            except (ValueError, OSError, KeyError, TypeError) as invalid:
                result["repair"] = {"classification": "identity_conflict" if isinstance(
                                        invalid, atom_repair.RepairRefusal) else "missing_input", "action": "stop",
                                    "missing_fact": "repair diagnostic owner readback", "producer": "external-supervisor",
                                    "remaining": None, "stop": str(invalid), "wake": "material_owner_readback",
                                    "model_invocations": 0}
            if isinstance(error, AtomRefusal):
                error.repair = result["repair"]
                raise
            wrapped = AtomRefusal(result["invalid"]["field"], result["invalid"]["value"])
            wrapped.owner_result = result
            raise wrapped from error


def _run_owned(authorization_path, authorization, authorization_digest, paths, *, environ, provider):
    state_path = paths["state"]
    state = read_json(state_path, "state") if state_path.exists() else {
        "schema_version": 1, "authorization_sha256": authorization_digest,
        "phase": "issue", "writes": {}, "issue": None, "publication": None}
    require(isinstance(state, dict) and state.get("schema_version") == 1
            and state.get("authorization_sha256") == authorization_digest,
            "state.authorization", "mismatch", "matching_lifecycle_checkpoint")
    repair = repair_controller(authorization, state, paths, fresh=not state_path.exists(),
                               authorization_path=authorization_path)
    if state.get("correction_start_recovery") is not None and state["correction_start_recovery"].get("status") != "started":
        if provider is None:
            environ = provider_credential.resolve_host_environment(authorization["control_root"], environ=environ)
            token = provider_credential.supply_token(authorization["repository"], {"issues": "read"}, environ=environ)
            provider = GitHubProvider(authorization["repository"], token=token)
        execution = advance_correction_start(authorization, paths, state, provider, environ)
        return response(state, authorization_path, repair=repair, waiting_on="correction startup readback",
                        details={"execution": execution})
    if state.get("scope_amendment") is not None and state["scope_amendment"].get("status") != "released":
        if provider is None:
            environ = provider_credential.resolve_host_environment(authorization["control_root"], environ=environ)
            token = provider_credential.supply_token(authorization["repository"], {"issues": "write"}, environ=environ)
            provider = GitHubProvider(authorization["repository"], token=token)
        execution = advance_scope_amendment(authorization, paths, state, provider, environ)
        return response(state, authorization_path, repair=repair, waiting_on="scope owner readback",
                        details={"execution": execution})
    authorization, paths = scope_projection(authorization, state, paths)
    observation = require_available_owner(authorization, paths, state)
    prior_recovery = (isinstance(observation, dict)
                      and observation.get("action") in
                      {"prior_loop_stopped", "prior_loop_running"})
    if observation is not None and not prior_recovery:
        return response(state, authorization_path, repair=repair, waiting_on="Noodle",
                        details={"execution": observation})
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
    if not state_path.exists():
        selected_config = authorization["host_config_sha256"]
        if prior_recovery:
            selected_config = prior_host_config(
                authorization["prior_atom"], authorization["control_root"])["installed_sha256"]
        require(host_config_identity(authorization["control_root"]) == selected_config,
                "noodle.config.digest", "changed", "unchanged_host_configuration")

    if provider is None:
        try:
            permissions = {"contents": "write", "issues": "write",
                           "pull_requests": "write", "actions": "read"}
            if any(path.startswith(".github/workflows/") for path in
                   issue_admission.parse_contract(authorization["issue"]["body"])["write_paths"]):
                permissions["workflows"] = "write"
            token = provider_credential.supply_token(
                authorization["repository"], permissions, environ=environ)
        except provider_credential.CredentialRefusal as error:
            raise AtomRefusal(error.field, error.value, error.required) from None
        provider = GitHubProvider(authorization["repository"], token=token)
    if not state_path.exists():
        save_json(state_path, state, fresh=True)
    readmit_issue_base(provider, authorization, state, paths)
    issue, body = exact_issue(provider, authorization, authorization_digest)
    if prior_recovery:
        require(issue is not None and issue.get("state") == "open",
                "amendment.issue", issue, "exact_open_provider_issue")
        verify_failed_prior(provider, authorization)
        restored = recover_prior_host(authorization, paths, state)
        return response(state, authorization_path, repair=repair, waiting_on=(
            "original host restored" if restored else "Noodle shutdown readback"),
            details={"prior_host_recovery": state["prior_host_recovery"]})
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
        if "prior_publication" in authorization:
            verify_failed_prior(provider, authorization)
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
        if "prior_atom" in authorization and state.get("noodle_amendment") is None:
            if state.get("noodle_start") is None:
                execution = ensure_noodle(
                    authorization, paths, state, {"action": "correction_review"},
                    environ, correction=True)
            else:
                execution = advance_correction(authorization, paths, state, provider)
            return response(state, authorization_path, repair=repair, waiting_on="new Noodle loop",
                            details={"execution": execution})
        if state.get("noodle_bootstrap", {}).get("status") == "exited_zero":
            bootstrap_noodle(authorization, paths, state, environ)
        try:
            admission = issue_execution.supervised(
                paths["envelope"], envelope_digest, Path(authorization["control_root"]),
                reader=lambda repository, number: provider.issue(number), observe_live=True)
        except issue_admission.AdmissionRefusal as error:
            if error.invalid["field"] != "noodle.snapshot" or \
                    (Path(authorization["control_root"]) / ".noodle/state.snapshot.json").exists():
                raise
            bootstrap_noodle(authorization, paths, state, environ)
            admission = issue_execution.supervised(
                paths["envelope"], envelope_digest, Path(authorization["control_root"]),
                reader=lambda repository, number: provider.issue(number), observe_live=True)
        if admission.get("action") == "running":
            return response(state, authorization_path, repair=repair, waiting_on="Noodle",
                            details={"execution": admission})
        if admission.get("action") == "proposal_pending":
            execution = ensure_noodle(authorization, paths, state, admission, environ)
            return response(state, authorization_path, repair=repair, waiting_on="Noodle", details={"execution": execution})
        subject = authorization["repository"] + "#" + str(issue["number"])
        if admission.get("action") == "blocked":
            blocked = admission["blocked"]
            raise AtomRefusal("noodle.stage.blocked", blocked["message"],
                "original_owner_input_for_blocked_stage", owner="original-admission-owner",
                known={"control_root": authorization["control_root"],
                       "order_id": admission["binding"]["execution"]["order_id"],
                       "subject": subject, "blocked": blocked})
        if not paths["claim"].exists() or state.get("failed_candidate_head"):
            order_id = read_json(paths["envelope"], "envelope")["execution"]["order_id"]
            claim_result = _run_claim(authorization, subject, paths["claim"], order_id)
            if claim_result.returncode:
                raise AtomRefusal(
                    "noodle.claim.exit",
                    {"exit_status": claim_result.returncode,
                     "diagnostic": claim_result.stderr.strip()[-1000:]},
                    "fresh_noodle_claim", owner="Noodle",
                    known={"control_root": authorization["control_root"],
                           "order_id": order_id, "subject": subject})
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
        publication = publish_candidate(authorization, state, paths, claim, acceptance, provider, repair)
        state["publication"] = publication
        state["publication_source"] = {"claim_sha256": atom_repair.digest(claim),
                                       "value": publication, "sha256": atom_repair.digest(publication)}
        state["phase"] = "ci"
        save_json(state_path, state)

    claim = read_json(paths["claim"], "publication_claim")
    publication = restore_publication(state, claim, repair)
    try:
        run_value, jobs = select_run(provider, authorization, claim["head"])
    except AtomRefusal as error:
        if error.required == "new_candidate_head_after_failed_ci" and error.invalid.get("value") in (
                ["failure", "failure", "failure"], ["failure", "failure", "skipped"]):
            count = validate_correction_lineage(authorization,
                {"path": str(authorization_path), "sha256": authorization_digest}, state)
            if count >= 3:
                raise AtomRefusal("correction.lineage.limit", count,
                    "reassess_cause_after_three_failed_corrections", owner="soodles.issue-atom") from error
            error.known = {"authorization_sha256": authorization_digest}
        raise
    try:
        cost_telemetry.record_provider(authorization_path, state, run_value, jobs, save_json)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"event": "soodles.cost", **cost_telemetry.failure(error)}), file=sys.stderr)
    if run_value is None or run_value.get("status") != "completed":
        return response(state, authorization_path, repair=repair, waiting_on="GitHub Actions")
    if state["phase"] in {"ci", "landing", "resolved"}:
        selected_owner = external_landing_activation(
            authorization, state, paths, environ,
            claim, publication, run_value)
        if selected_owner is not None:
            landing_owner = LandingOwner(selected_owner, paths["directory"])
    if state["phase"] in {"landing", "resolved"}:
        corrected_owner = external_landing_resume(authorization, state, paths, environ)
        if corrected_owner is not None:
            landing_owner = LandingOwner(corrected_owner, paths["directory"])
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
        return response(state, authorization_path, repair=repair, waiting_on="fresh provider readback")
    if transition["action"] == "reconcile":
        transition = landing_owner.reconcile(paths["landing"], authorization["noodle"]["path"])
        if transition.get("action") == "noodle_reconcile":
            complete_noodle(authorization, paths, state, transition)
            return response(state, authorization_path, repair=repair, waiting_on="Noodle original-order completion readback",
                            details={"host_finalization_projection": host_manager(authorization, state).project()})
    if transition.get("classification") == "RESOLVED":
        if not finish_host(authorization, paths, state, landing=transition):
            return response(state, authorization_path, repair=repair, waiting_on="Noodle shutdown readback")
        state["phase"] = "resolved"
        save_json(state_path, state)
        return response(state, authorization_path, repair=repair, status="resolved",
                        details={"landing": transition,
                                 "host_finalization": state["host_finalization"]})
    if transition.get("next") is None:
        # The owner has returned a nonterminal outcome with neither a legal
        # action nor a prerequisite. This is a structural deadlock, not a timer.
        return response(state, authorization_path, repair=repair, status="refused", details={
            "landing": transition, "repair": repair.report("no_legal_next")})
    return response(state, authorization_path, repair=repair, waiting_on="fresh owner readback",
                    details={"landing": transition})


def drive(authorization_path, *, timeout=300, interval=5, sleep=time.sleep, clock=time.monotonic,
          environ=None, provider=None):
    """Observe normal waits through the same entry; never retry a refusal.

    Durable transitions and unknown-write readback remain in their existing
    owners. The bounded foreground wait creates no scheduler or new state.
    """
    from soodles import measured

    require(timeout >= 0 and interval >= 0, "wait.bounds", [timeout, interval])
    deadline = clock() + timeout
    while True:
        result = measured("issue_atom.observe",
                          lambda: run(authorization_path, environ=environ, provider=provider),
                          authorization=str(Path(authorization_path).resolve()))
        if result.get("status") != "pending" or not result.get("next"):
            return result
        remaining = deadline - clock()
        if remaining <= 0:
            return {**result, "wait_exhausted": True}
        wait_cost(authorization_path, result, min(interval, remaining), sleep)


def wait_cost(authorization_path, result, seconds, sleep):
    from soodles import measured
    handle = None
    try:
        with Path(authorization_path).open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            handle = cost_telemetry.begin(authorization_path, save_json,
                                          waiting=result.get("waiting_on") or "owner")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"event": "soodles.cost", **cost_telemetry.failure(error)}), file=sys.stderr)
    measured("issue_atom.wait", sleep, seconds,
             authorization=str(Path(authorization_path).resolve()),
             authorization_sha256=(result.get("cost", {}).get("subject") or {}).get("authorization"),
             observation_id=wait_identity(result), status="pending",
             phase=result.get("phase"), waiting_on=result.get("waiting_on"))
    if handle is not None:
        try:
            with Path(authorization_path).open("rb") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                cost = cost_response(authorization_path, handle, result)
                if cost.get("status") == "refused":
                    print(json.dumps({"event": "soodles.cost", **cost}), file=sys.stderr)
        except OSError as error:
            print(json.dumps({"event": "soodles.cost", **cost_telemetry.failure(error)}), file=sys.stderr)


def wait_identity(result):
    if result.get("cost", {}).get("observation_id"):
        return result["cost"]["observation_id"]
    return cost_telemetry.digest(cost_telemetry.canonical({
        "phase": result.get("phase"), "issue": result.get("issue"),
        "publication": result.get("publication"), "waiting_on": result.get("waiting_on")}))


def refusal_output(error, authorization_path):
    if hasattr(error, "owner_result"):
        return error.owner_result
    correction_required = error.required == "new_candidate_head_after_failed_ci"
    if correction_required:
        reason = ("The selected authorization still binds the failed head. "
                  "The current authorized Local Session is the external supervisor "
                  "for deriving a fresh correction selection from current owner "
                  "and provider readbacks; do not ask the user to recreate "
                  "authorization or replay this failed head. A fresh admitted "
                  "candidate transition is required.")
    elif error.owner == "external-supervisor":
        reason = ("The current authorized Local Session is the external "
                  "supervisor for derivable inputs. Recover selected bytes "
                  "from their owner, or correct the named material state; "
                  "ask only for genuinely missing identity or capability. "
                  "Never choose a phase-specific route.")
    else:
        reason = ("Correct the named external input or material owner state; "
                  "never choose a phase-specific route.")
    result = {
        "owner": "soodles.issue-atom", "status": "refused",
        "continuation_state": "input_required",
        "invalid": error.invalid,
        "next": {
            "kind": "input", "owner": error.owner,
            "required": [error.required],
            **({"known": error.known} if error.known is not None else {}),
            **({} if correction_required or error.required == "execute_selected_prepared_continuation"
               else {"argv": same_command(authorization_path)}),
            "reason": reason,
        },
        "authorizes_landing": False,
        **({"repair": error.repair} if hasattr(error, "repair") else {}),
    }
    selected_digest = (error.known or {}).get("authorization_sha256") if isinstance(error.known, dict) else None
    if correction_required and isinstance(selected_digest, str) and SHA64.fullmatch(selected_digest):
        result["continuation_state"] = "ready"
        result["next"] = {
            "kind": "executable", "owner": "supervisor.authorization", "required": [],
            "argv": [sys.executable, "-B", str(Path(__file__).resolve().with_name("supervisor_admission.py")),
                     "correction", str(Path(authorization_path).resolve()), selected_digest,
                     str(artifact_paths(authorization_path)["directory"] / "correction")],
            "reason": "Prepare the bounded correction from original authority and fresh owner readback. Consume its returned next."}
    return result
