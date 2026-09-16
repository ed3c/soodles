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

REPOSITORY = "ed3c/soodles"
MARKER = "soodles:execution-v1"
CONTRACT_FIELDS = {
    "schema", "trigger", "source", "owner", "changes", "write_paths",
    "behavior", "defect_controls", "non_cases", "dependencies",
    "acceptance", "delivery", "reconciliation", "feature_scope",
}
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
    exact_object(contract, CONTRACT_FIELDS, "issue.contract.fields", **source)
    require(type(contract["schema"]) is int and contract["schema"] == 1,
            "issue.contract.schema", contract["schema"], **source)
    for field in ("trigger", "source", "owner", "acceptance", "delivery", "reconciliation", "feature_scope"):
        require(nonempty(contract[field]), "issue.contract." + field, contract[field], **source)
    for field in ("changes", "behavior", "defect_controls", "non_cases"):
        values = contract[field]
        require(isinstance(values, list) and bool(values) and all(nonempty(v) for v in values),
                "issue.contract." + field, values, **source)
    contract["write_paths"] = path_set(contract["write_paths"], "issue.contract.write_paths")
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
    require(envelope["repository"] == REPOSITORY, "envelope.repository", envelope["repository"])
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
    for field, expected in (("url", f"https://api.github.com/repos/{REPOSITORY}/issues/{number}"),
                            ("html_url", f"https://github.com/{REPOSITORY}/issues/{number}"),
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
    require(body_digest(body) == envelope["body_sha256"], "issue.body_sha256", body_digest(body), **source)
    # Closure changes provider metadata. It never changes the admitted body bytes
    # or grants permission to execute; only the landing owner uses this readback.
    require(completed or readback.get("updated_at") == envelope["body_updated_at"],
            "issue.updated_at", readback.get("updated_at"), **source)
    require(contract["owner"] == envelope["owner"], "envelope.owner", envelope["owner"])
    require(contract["write_paths"] == envelope["write_paths"], "envelope.write_paths", envelope["write_paths"])
    return {
        "repository": REPOSITORY, "issue": number, "body_sha256": envelope["body_sha256"],
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


def validate_delivery_paths(root, base, head, binding):
    require(base == binding["base_head"], "candidate.base", base)
    paths = changed_paths(root, base, head)
    outside = sorted(set(paths) - set(binding["write_paths"]))
    require(not outside, "candidate.outside_write_paths", outside)
    return {"head": head, "base_head": base, "changed_paths": paths, "authorizes_landing": False}
