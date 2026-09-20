"""Shared Issue binding. The supervisor supplies trust; a body/hash cannot grant it.

This module reads no credentials and performs no provider writes. Automatic,
supervised and worker consumers must provide fresh provider readback and the
externally selected envelope before asking their existing owner for effects.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

from soodles import Refusal
from repository_binding import issue_urls, profile, valid_name

MARKER = "soodles:execution-v1"
CONTRACT_V1_FIELDS = {
    "schema", "trigger", "source", "owner", "changes", "write_paths",
    "behavior", "defect_controls", "non_cases", "dependencies",
    "acceptance", "delivery", "reconciliation", "feature_scope",
}
CONTRACT_V2_FIELDS = CONTRACT_V1_FIELDS | {"required_paths", "evidence_manifest"}
CONTRACT_FIELDS = CONTRACT_V2_FIELDS | {"base_head", "frozen_paths"}
ENVELOPE_FIELDS = {
    "schema", "repository", "issue", "body_sha256", "body_updated_at",
    "owner", "write_paths", "base_head", "execution",
}


class AdmissionRefusal(Refusal):
    def __init__(self, field, value, owner="supervisor", required="execution_envelope"):
        self.invalid = {"field": field, "value": value}
        self.next = {"kind": "input", "owner": owner, "required": [required]}
        super().__init__(f"Issue admission: invalid {field}={value!r}; owner: {owner}; required: {required}")


def require(condition, field, value, **source):
    if not condition:
        raise AdmissionRefusal(field, value, **source)


def body_digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def exact_object(value, fields, field, **source):
    require(isinstance(value, dict) and set(value) == fields, field,
            sorted(value) if isinstance(value, dict) else value, **source)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def git_path(value, field="write_paths"):
    valid = (isinstance(value, str) and bool(value) and not value.startswith("/")
             and "\\" not in value and not any(ord(c) < 32 or ord(c) == 127 for c in value))
    if valid:
        parts = value.split("/")
        valid = (all(p and p not in (".", "..") and p.lower() != ".git" for p in parts)
                 and str(PurePosixPath(value)) == value)
    require(valid, field, value)
    return value


def path_set(values, field):
    require(isinstance(values, list) and bool(values), field, values)
    paths = [git_path(value, field) for value in values]
    require(len(paths) == len(set(paths)), field, values)
    return sorted(paths)


def parse_contract(body):
    source = {"owner": "GitHub", "required": "current_issue_contract"}
    require(isinstance(body, str), "issue.body", body, **source)
    pattern = r"<!--\s*" + MARKER + r"\s*-->\s*```json\s*\n(.*?)\n\s*```\s*<!--\s*/" + MARKER + r"\s*-->"
    blocks = re.findall(pattern, body, re.DOTALL)
    require(len(blocks) == 1 and len(re.findall(r"<!--\s*" + MARKER + r"\s*-->", body)) == 1,
            "issue.contract.count", len(blocks), **source)
    try:
        contract = json.loads(blocks[0])
    except (ValueError, TypeError) as error:
        raise AdmissionRefusal("issue.contract.json", str(error), **source) from error
    require(isinstance(contract, dict), "issue.contract.fields", contract, **source)
    schema = contract.get("schema")
    require(type(schema) is int and schema in (1, 2, 3),
            "issue.contract.schema", schema, **source)
    fields = (CONTRACT_V1_FIELDS if schema == 1 else
              CONTRACT_V2_FIELDS if schema == 2 else CONTRACT_FIELDS)
    exact_object(contract, fields,
                 "issue.contract.fields", **source)
    for field in ("trigger", "source", "owner", "acceptance", "delivery", "reconciliation", "feature_scope"):
        require(nonempty(contract[field]), "issue.contract." + field, contract[field], **source)
    for field in ("changes", "behavior", "defect_controls", "non_cases"):
        values = contract[field]
        require(isinstance(values, list) and bool(values) and all(nonempty(v) for v in values),
                "issue.contract." + field, values, **source)
    contract["write_paths"] = path_set(contract["write_paths"], "issue.contract.write_paths")
    if schema >= 2:
        contract["required_paths"] = path_set(
            contract["required_paths"], "issue.contract.required_paths")
        contract["evidence_manifest"] = git_path(
            contract["evidence_manifest"], "issue.contract.evidence_manifest")
        require(contract["evidence_manifest"] in contract["required_paths"],
                "issue.contract.evidence_manifest",
                contract["evidence_manifest"], **source)
        require(set(contract["required_paths"]) <= set(contract["write_paths"]),
                "issue.contract.required_paths",
                sorted(set(contract["required_paths"]) - set(contract["write_paths"])),
                **source)
    if schema == 3:
        base_head = contract["base_head"]
        require(isinstance(base_head, str) and re.fullmatch(r"[0-9a-f]{40}", base_head),
                "issue.contract.base_head", base_head, **source)
        frozen = contract["frozen_paths"]
        require(isinstance(frozen, list) and bool(frozen),
                "issue.contract.frozen_paths", frozen, **source)
        identities = []
        for pin in frozen:
            exact_object(pin, {"path", "revision", "sha256"},
                         "issue.contract.frozen_path", **source)
            path = git_path(pin["path"], "issue.contract.frozen_path.path")
            require(path in contract["required_paths"],
                    "issue.contract.frozen_path.path", path, **source)
            require(pin["revision"] in ("base", "head"),
                    "issue.contract.frozen_path.revision", pin["revision"], **source)
            require(isinstance(pin["sha256"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]),
                    "issue.contract.frozen_path.sha256", pin["sha256"], **source)
            identity = (path, pin["revision"])
            require(identity not in identities,
                    "issue.contract.frozen_paths", list(identity), **source)
            identities.append(identity)
    dependencies = contract["dependencies"]
    require(isinstance(dependencies, list), "issue.contract.dependencies", dependencies, **source)
    for dependency in dependencies:
        exact_object(dependency, {"repository", "issue", "owner", "evidence"}, "issue.contract.dependency", **source)
        require(isinstance(dependency["repository"], str)
                and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", dependency["repository"]),
                "issue.contract.dependency.repository", dependency["repository"], **source)
        require(type(dependency["issue"]) is int and dependency["issue"] > 0,
                "issue.contract.dependency.issue", dependency["issue"], **source)
        for field in ("owner", "evidence"):
            require(nonempty(dependency[field]), "issue.contract.dependency." + field, dependency[field], **source)
    return contract


def validate_envelope(envelope):
    exact_object(envelope, ENVELOPE_FIELDS, "envelope.fields")
    require(type(envelope["schema"]) is int and envelope["schema"] == 1, "envelope.schema", envelope["schema"])
    require(valid_name(envelope["repository"]) and profile(envelope["repository"]) is not None,
            "envelope.repository", envelope["repository"],
            owner="supervisor", required="supported_repository_envelope")
    require(type(envelope["issue"]) is int and envelope["issue"] > 0, "envelope.issue", envelope["issue"])
    for field, length in (("body_sha256", 64), ("base_head", 40)):
        require(isinstance(envelope[field], str) and re.fullmatch(r"[0-9a-f]{" + str(length) + "}", envelope[field]),
                "envelope." + field, envelope[field])
    require(nonempty(envelope["body_updated_at"]), "envelope.body_updated_at", envelope["body_updated_at"])
    require(nonempty(envelope["owner"]), "envelope.owner", envelope["owner"])
    paths = path_set(envelope["write_paths"], "envelope.write_paths")
    execution = envelope["execution"]
    exact_object(execution, {"control_root", "worktree", "order_id", "stage_index", "carrier", "task", "source_head"},
                 "envelope.execution.fields")
    require(isinstance(execution["source_head"], str) and re.fullmatch(r"[0-9a-f]{40}", execution["source_head"]),
            "envelope.execution.source_head", execution["source_head"])
    require(nonempty(execution["task"]), "envelope.execution.task", execution["task"])
    require(isinstance(execution["control_root"], str) and Path(execution["control_root"]).is_absolute(),
            "envelope.execution.control_root", execution["control_root"])
    require(isinstance(execution["worktree"], str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", execution["worktree"]),
            "envelope.execution.worktree", execution["worktree"])
    require(execution["order_id"] == f"soodles-{envelope['issue']}",
            "envelope.execution.order_id", execution["order_id"])
    require(type(execution["stage_index"]) is int and execution["stage_index"] == 0,
            "envelope.execution.stage_index", execution["stage_index"])
    require(isinstance(execution["carrier"], dict) and bool(execution["carrier"]),
            "envelope.execution.carrier", execution["carrier"])
    return {**envelope, "write_paths": paths}


def validate_issue(readback, envelope, *, completed=False):
    """Validate common binding; no route-dependent authorization or side effects."""
    envelope = validate_envelope(envelope)
    source = {"owner": "GitHub", "required": "fresh_issue_readback"}
    require(isinstance(readback, dict), "issue.readback", readback, **source)
    number = envelope["issue"]
    repository = envelope["repository"]
    api_url, html_url = issue_urls(repository, number)
    for field, expected in (("url", api_url),
                            ("html_url", html_url),
                            ("number", number)):
        actual = readback.get(field)
        require(type(actual) is type(expected) and actual == expected, "issue." + field, actual, **source)
    require("pull_request" not in readback, "issue.pull_request", readback.get("pull_request"), **source)
    expected_state = "closed" if completed else "open"
    require(readback.get("state") == expected_state, "issue.state", readback.get("state"), **source)
    if completed:
        require(readback.get("state_reason") == "completed" and bool(readback.get("closed_at")),
                "issue.closure", readback.get("state_reason"), **source)
    body = readback.get("body")
    contract = parse_contract(body)
    amendment = {"owner": "supervisor", "required": "fresh_execution_envelope"}
    require(body_digest(body) == envelope["body_sha256"], "issue.body_sha256", body_digest(body), **amendment)
    # Closure changes provider metadata. It never changes the admitted body bytes
    # or grants permission to execute; only the landing owner uses this readback.
    require(completed or readback.get("updated_at") == envelope["body_updated_at"],
            "issue.updated_at", readback.get("updated_at"), **amendment)
    require(contract["owner"] == envelope["owner"], "envelope.owner", envelope["owner"])
    require(contract["write_paths"] == envelope["write_paths"], "envelope.write_paths", envelope["write_paths"])
    return {
        "repository": repository, "issue": number, "body_sha256": envelope["body_sha256"],
        "body_updated_at": envelope["body_updated_at"], "owner": contract["owner"],
        "write_paths": envelope["write_paths"], "base_head": envelope["base_head"],
        "execution": envelope["execution"], "contract": contract, "authorizes_landing": False,
    }


def load_external_envelope(path, expected_digest, subject_root):
    """The installed supervisor launcher pins these bytes outside the candidate."""
    path, root = Path(path).resolve(), Path(subject_root).resolve()
    require(not path.is_relative_to(root), "envelope.path", str(path))
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    require(actual == expected_digest, "envelope.sha256", actual)
    return validate_envelope(json.loads(data))


def changed_paths(root, base, head):
    for field, value in (("base", base), ("head", head)):
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value), "candidate." + field, value)
    result = subprocess.run(["git", "--no-pager", "diff", "--no-ext-diff", "--no-textconv",
                             "--name-status", "-z", "--find-renames", base, head, "--"],
                            cwd=root, capture_output=True, timeout=30)
    require(result.returncode == 0, "candidate.diff", result.stderr.decode("utf-8", errors="replace"),
            owner="Git", required="exact_candidate_readback")
    try:
        fields = result.stdout.decode("utf-8").split("\0")
    except UnicodeDecodeError as error:
        raise AdmissionRefusal("candidate.paths.encoding", str(error), "Git", "valid_repository_paths") from error
    require(fields.pop() == "", "candidate.diff.termination", result.stdout.hex(),
            owner="Git", required="exact_candidate_readback")
    paths = []
    while fields:
        status = fields.pop(0)
        require(bool(re.fullmatch(r"(?:[AMDTUXB]|[RC][0-9]{1,3})", status)), "candidate.diff.status", status)
        count = 2 if status[0] in "RC" else 1
        require(len(fields) >= count, "candidate.diff.paths", fields)
        for _ in range(count):
            paths.append(git_path(fields.pop(0), "candidate.path"))
    return sorted(set(paths))


def git_bytes(root, revision, path):
    result = subprocess.run(
        ["git", "--no-pager", "show", f"{revision}:{path}"],
        cwd=root, capture_output=True, timeout=30)
    require(result.returncode == 0, "candidate.evidence_path", path,
            owner="Git", required="exact_candidate_evidence")
    return result.stdout


def candidate_repository(binding):
    """Return a bound repository, with one explicit schema-2 compatibility."""
    repository = binding.get("repository")
    if repository is None:
        require(binding.get("contract", {}).get("schema") == 2,
                "candidate.binding.repository", repository,
                owner="Soodles Issue admission",
                required="repository_bound_candidate")
        return "ed3c/soodles"
    require(profile(repository) is not None,
            "candidate.binding.repository", repository,
            owner="Soodles Issue admission",
            required="supported_repository_binding")
    return repository


def validate_candidate_evidence(root, base, head, binding, paths):
    contract = binding.get("contract", {})
    evidence = contract.get("candidate_evidence")
    if evidence is None and contract.get("schema") in (2, 3):
        evidence = {
            "manifest_path": contract.get("evidence_manifest"),
            "required_paths": contract.get("required_paths"),
        }
    if evidence is None:
        return None
    exact_object(evidence, {"manifest_path", "required_paths"},
                 "candidate.evidence.fields")
    manifest_path = git_path(evidence["manifest_path"],
                             "candidate.evidence.manifest_path")
    required_paths = path_set(evidence["required_paths"],
                              "candidate.evidence.required_paths")
    require(manifest_path in required_paths, "candidate.evidence.manifest_path",
            manifest_path)
    missing = sorted(set(required_paths) - set(paths))
    require(not missing, "candidate.missing_required_paths", missing,
            owner="Soodles Issue admission",
            required="complete_candidate_evidence")
    raw_manifest = git_bytes(root, head, manifest_path)
    try:
        manifest = json.loads(raw_manifest)
    except (TypeError, ValueError) as error:
        raise AdmissionRefusal(
            "candidate.evidence_manifest.json", str(error),
            "Soodles Issue admission", "valid_candidate_evidence") from error
    exact_object(manifest, {
        "schema", "issue", "instructions", "artifacts", "owner",
        "authorizes_landing"}, "candidate.evidence_manifest.fields")
    require(type(manifest["schema"]) is int and manifest["schema"] == 1,
            "candidate.evidence_manifest.schema", manifest["schema"])
    issue = manifest["issue"]
    # Schema 2 predates repository-bearing bindings and was Soodles-only.
    # Replay those frozen observers without deriving a current repository from
    # candidate-owned manifest bytes. Current schema 3 must carry the owner.
    repository = candidate_repository(binding)
    exact_object(issue, {"repository", "number"},
                 "candidate.evidence_manifest.issue")
    require(issue == {"repository": repository, "number": binding.get("issue")},
            "candidate.evidence_manifest.issue", issue)
    owner = manifest["owner"]
    exact_object(owner, {"name", "tool", "authorization"},
                 "candidate.evidence_manifest.owner")
    require(all(nonempty(owner[field]) for field in owner),
            "candidate.evidence_manifest.owner", owner)
    require(owner["tool"] == "issue_admission.validate_delivery_paths",
            "candidate.evidence_manifest.owner.tool", owner["tool"])
    require(owner["authorization"]
            == f"{repository}#{binding.get('issue')}",
            "candidate.evidence_manifest.owner.authorization",
            owner["authorization"])
    require(manifest["authorizes_landing"] is False,
            "candidate.evidence_manifest.authorizes_landing",
            manifest["authorizes_landing"])

    instructions = manifest["instructions"]
    require(isinstance(instructions, list) and bool(instructions),
            "candidate.evidence_manifest.instructions", instructions)
    instruction_paths = []
    for instruction in instructions:
        exact_object(instruction, {
            "path", "baseline_sha256", "treatment_sha256"},
            "candidate.evidence_manifest.instruction")
        path = git_path(instruction["path"], "candidate.instruction.path")
        require(path in required_paths, "candidate.instruction.path", path)
        require(path not in instruction_paths, "candidate.instruction.path", path)
        instruction_paths.append(path)
        for label, revision in (("baseline", base), ("treatment", head)):
            actual = hashlib.sha256(git_bytes(root, revision, path)).hexdigest()
            expected = instruction[label + "_sha256"]
            require(isinstance(expected, str)
                    and re.fullmatch(r"[0-9a-f]{64}", expected)
                    and actual == expected,
                    f"candidate.instruction.{label}_sha256", expected,
                    owner="Soodles Issue admission",
                    required="candidate_instruction_matches_frozen_evidence")

    artifacts = manifest["artifacts"]
    require(isinstance(artifacts, list),
            "candidate.evidence_manifest.artifacts", artifacts)
    artifact_paths = []
    for artifact in artifacts:
        exact_object(artifact, {"path", "role", "sha256"},
                     "candidate.evidence_manifest.artifact")
        path = git_path(artifact["path"], "candidate.artifact.path")
        require(path in required_paths and path != manifest_path
                and path not in instruction_paths and path not in artifact_paths,
                "candidate.artifact.path", path)
        require(nonempty(artifact["role"]),
                "candidate.artifact.role", artifact["role"])
        actual = hashlib.sha256(git_bytes(root, head, path)).hexdigest()
        expected = artifact["sha256"]
        require(isinstance(expected, str)
                and re.fullmatch(r"[0-9a-f]{64}", expected)
                and actual == expected,
                "candidate.artifact.sha256", expected)
        artifact_paths.append(path)
    expected_artifacts = (
        set(required_paths) - {manifest_path} - set(instruction_paths))
    require(set(artifact_paths) == expected_artifacts,
            "candidate.evidence_manifest.artifacts",
            sorted(expected_artifacts - set(artifact_paths)))
    return hashlib.sha256(raw_manifest).hexdigest()


def validate_delivery_paths(root, base, head, binding):
    require(base == binding["base_head"], "candidate.base", base)
    paths = changed_paths(root, base, head)
    outside = sorted(set(paths) - set(binding["write_paths"]))
    require(not outside, "candidate.outside_write_paths", outside)
    manifest_sha256 = validate_candidate_evidence(
        root, base, head, binding, paths)
    return {"head": head, "base_head": base, "changed_paths": paths,
            "evidence_manifest_sha256": manifest_sha256,
            "authorizes_landing": False}


def verify_candidate(root, base, head, readback):
    """Verify exact Git objects against one fresh, read-only Issue readback."""
    if isinstance(readback, dict) and readback.get("owner") == "github.issue":
        require(readback.get("status") == "read"
                and readback.get("next") is None
                and readback.get("authorizes_landing") is False,
                "candidate.issue_readback", readback.get("status"),
                owner="GitHub", required="fresh_issue_readback")
        readback = readback.get("issue")
    require(isinstance(readback, dict), "candidate.issue_readback", readback,
            owner="GitHub", required="fresh_issue_readback")
    number = readback.get("number")
    require(type(number) is int and number > 0,
            "candidate.issue.number", number,
            owner="GitHub", required="exact_issue_readback")
    match = re.fullmatch(r"https://api\.github\.com/repos/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/[0-9]+",
                         str(readback.get("url")))
    repository = match.group(1) if match else None
    require(repository is not None and profile(repository) is not None,
            "candidate.issue.repository", repository,
            owner="supervisor", required="supported_repository_readback")
    api_url, html_url = issue_urls(repository, number)
    require(readback.get("url") == api_url,
            "candidate.issue.url", readback.get("url"),
            owner="GitHub", required="exact_issue_readback")
    require(readback.get("html_url") == html_url,
            "candidate.issue.html_url", readback.get("html_url"),
            owner="GitHub", required="exact_issue_readback")
    require("pull_request" not in readback,
            "candidate.issue.pull_request", readback.get("pull_request"),
            owner="GitHub", required="exact_issue_readback")
    require(readback.get("state") == "open", "candidate.issue.state",
            readback.get("state"), owner="GitHub", required="open_issue")
    body = readback.get("body")
    contract = parse_contract(body)
    require(contract["schema"] >= 2, "candidate.issue.contract.schema",
            contract["schema"], owner="Soodles candidate verification",
            required="schema_2_or_3_evidence_contract")
    if contract["schema"] == 3:
        require(base == contract["base_head"], "candidate.base", base)
    checkout = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
        text=True, timeout=30)
    require(checkout.returncode == 0 and checkout.stdout.strip() == head,
            "candidate.checkout_head", checkout.stdout.strip(),
            owner="Git", required="exact_candidate_checkout")
    binding = {
        "issue": number,
        "repository": repository,
        "base_head": base,
        "write_paths": contract["write_paths"],
        "contract": contract,
    }
    receipt = validate_delivery_paths(root, base, head, binding)
    frozen_receipts = []
    for pin in contract.get("frozen_paths", []):
        revision = base if pin["revision"] == "base" else head
        actual = hashlib.sha256(git_bytes(root, revision, pin["path"])).hexdigest()
        require(actual == pin["sha256"], "candidate.frozen_path.sha256",
                {"path": pin["path"], "revision": pin["revision"],
                 "expected": pin["sha256"], "actual": actual},
                owner="Soodles candidate verification",
                required="externally_frozen_candidate_bytes")
        frozen_receipts.append({**pin, "actual_sha256": actual})
    tree = subprocess.run(
        ["git", "rev-parse", f"{head}^{{tree}}"], cwd=root,
        capture_output=True, text=True, timeout=30)
    require(tree.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", tree.stdout.strip()),
            "candidate.tree", tree.stdout.strip(),
            owner="Git", required="exact_candidate_tree")
    return {
        **receipt,
        "issue": number,
        "issue_body_sha256": body_digest(body),
        "tree": tree.stdout.strip(),
        "frozen_paths": frozen_receipts,
        "owner": "candidate.verify",
        "classification": "VERIFIED",
        "authorizes_landing": False,
    }
