"""Versioned feature-map consumer-report evidence, never landing authority."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

EXPERIMENT = "eval-validity-shortest-path-v1"
RECIPE = ".agents/skills/verify-soodles/features/cross-repository-delivery.md"
MAP = ".agents/skills/verify-soodles/features/README.md"


class EvidenceError(Exception):
    def __init__(self, field, reason, validity="INVALID"):
        self.field, self.reason, self.validity = field, reason, validity
        super().__init__(f"{field}: {reason}")


def refusal(field, reason, validity="INVALID"):
    problem = {"field": field, "reason": reason}
    return {"schema": 1, "owner": "eval.report", "authorizes_landing": False,
            "observation_scope": "consumer_report", "evidence_validity": validity,
            "behavior": None, "problem": problem,
            "next": {"owner": "supervisor", "operation": "supply_report_evidence",
                     "missing_input": problem}}


def required(obj, key, prefix):
    field = f"{prefix}.{key}"
    if key not in obj or obj[key] is None:
        raise EvidenceError(field, "required observation is missing or null", "INCONCLUSIVE")
    return obj[key]


def typed(value, kind, field):
    if type(value) is not kind:
        raise EvidenceError(field, f"expected {kind.__name__}")
    return value


def shape(value, fields, field):
    typed(value, dict, field)
    for key in sorted(fields):
        required(value, key, field)
    if set(value) != set(fields):
        raise EvidenceError(field, "unsupported fields")


def hex_digest(value, size, field):
    if not isinstance(value, str) or re.fullmatch(f"[0-9a-f]{{{size}}}", value) is None:
        raise EvidenceError(field, f"expected {size}-character lowercase hex digest")
    return value


def path_value(value, field, absolute=False):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise EvidenceError(field, "expected nonempty path without NUL")
    path = Path(value)
    if ".." in path.parts or (absolute and not path.is_absolute()):
        raise EvidenceError(field, "expected bounded path without traversal")
    return path


def source_path(root, value, field, relative=False):
    path = path_value(value, field)
    if relative and path.is_absolute():
        raise EvidenceError(field, "expected relative source path")
    path = (root / path).resolve()
    if not path.is_relative_to(root):
        raise EvidenceError(field, "path escapes selected source root")
    return path


def bound_bytes(path, expected, field, count=None):
    hex_digest(expected, 64, field + ".sha256")
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise EvidenceError(field, "required file is missing", "INCONCLUSIVE")
    except OSError as exc:
        raise EvidenceError(field, f"cannot read file: {exc}")
    if hashlib.sha256(data).hexdigest() != expected:
        raise EvidenceError(field + ".sha256", "raw-byte digest mismatch")
    if count is not None and len(data) != count:
        raise EvidenceError(field + ".bytes", "byte count mismatch")
    return data


def source_state(root, head):
    env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TMPDIR") if key in os.environ}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=root, env=env,
                                           stderr=subprocess.PIPE, text=True, timeout=60).strip()
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceError("selection.source", f"Git readback failed: {exc}")
    if Path(git("rev-parse", "--show-toplevel")).resolve() != root:
        raise EvidenceError("selection.source.root", "must be the repository root")
    if git("rev-parse", "HEAD") != head:
        raise EvidenceError("selection.source.head", "current HEAD mismatch")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise EvidenceError("selection.source.clean", "selected source is dirty")


def evaluate(selection):
    try:
        return evaluate_validated(selection)
    except EvidenceError as exc:
        return refusal(exc.field, exc.reason, exc.validity)
    except (ValueError, OSError, RuntimeError) as exc:
        return refusal("evidence", str(exc))


def evaluate_validated(selection):
    shape(selection, {"schema", "kind", "experiment_id", "source", "instruction", "report", "evaluator_sha256"}, "selection")
    if type(selection["schema"]) is not int or selection["schema"] != 1:
        raise EvidenceError("selection.schema", "only schema 1 is supported")
    if selection["kind"] != "feature_map_routing_report_v2":
        raise EvidenceError("selection.kind", "unsupported report family")
    if selection["experiment_id"] != EXPERIMENT:
        raise EvidenceError("selection.experiment_id", "experiment identifier mismatch")
    for name, fields in (("source", {"root", "head"}), ("instruction", {"path", "sha256"}), ("report", {"path", "sha256"})):
        shape(selection[name], fields, "selection." + name)
    source, instruction, descriptor = (selection[key] for key in ("source", "instruction", "report"))
    root = path_value(source["root"], "selection.source.root", absolute=True).resolve()
    head = hex_digest(source["head"], 40, "selection.source.head")
    source_state(root, head)
    instruction_path = source_path(root, instruction["path"], "selection.instruction.path", relative=True)
    bound_bytes(instruction_path, instruction["sha256"], "selection.instruction")
    report_path = path_value(descriptor["path"], "selection.report.path", absolute=True)
    data = bound_bytes(report_path, descriptor["sha256"], "selection.report")
    try:
        report = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise EvidenceError("report", f"invalid JSON: {exc}")
    typed(report, dict, "report")
    report_head = required(report, "source_head", "report")
    hex_digest(report_head, 40, "report.source_head")
    if report_head != head:
        raise EvidenceError("report.source_head", "selected HEAD mismatch")
    reads = typed(required(report, "actual_files_read", "report"), list, "report.actual_files_read")
    observed = set()
    for index, item in enumerate(reads):
        field = f"report.actual_files_read[{index}]"
        typed(item, dict, field)
        path = source_path(root, required(item, "path", field), field + ".path")
        count = typed(required(item, "bytes", field), int, field + ".bytes")
        if count < 0:
            raise EvidenceError(field + ".bytes", "expected nonnegative byte count")
        bound_bytes(path, required(item, "sha256", field), field, count)
        observed.add(path)
    for path in {instruction_path, root / MAP, root / RECIPE, root / "task-input.json"}:
        if path not in observed:
            raise EvidenceError("report.actual_files_read", f"missing required read: {path.relative_to(root)}", "INCONCLUSIVE")
    operations = typed(required(report, "external_operations_performed", "report"), list, "report.external_operations_performed")
    for index, operation in enumerate(operations):
        if not isinstance(operation, (str, dict)) or not operation:
            raise EvidenceError(f"report.external_operations_performed[{index}]", "expected nonempty operation string or object")
    commands = typed(required(report, "actual_commands", "report"), list, "report.actual_commands")
    for index, command in enumerate(commands):
        typed(command, dict, f"report.actual_commands[{index}]")
        status = command.get("exit_status")
        if status is not None:
            typed(status, int, f"report.actual_commands[{index}].exit_status")
    for key in ("classification", "recipe_path"):
        typed(required(report, key, "report"), str, "report." + key)
    feature = required(report, "selected_feature", "report")
    if isinstance(feature, dict):
        feature = required(feature, "mapped_feature", "report.selected_feature")
    typed(feature, str, "report.selected_feature")
    owner = required(report, "owner_boundary", "report")
    if not isinstance(owner, (str, dict)):
        raise EvidenceError("report.owner_boundary", "expected string or object")
    for key in ("new_feature_required", "new_cli_required", "new_registry_required", "delivery_complete"):
        typed(required(report, key, "report"), bool, "report." + key)
    owner = json.dumps(owner, ensure_ascii=False).lower()
    checks = {
        "no_judge_read": not any(path.name in {"protocol.md", "manifest.json", "freeze.py", "observe.py", "evaluate_report.py", "decision.json"} for path in observed),
        "classification_mapped": report["classification"].lower() == "mapped",
        "selected_existing_feature": feature.lower() in {"cross-repository delivery", "cross-repository-delivery", "cross_repository_delivery"},
        "recipe_path": report["recipe_path"].endswith(RECIPE),
        "existing_owner": all(token in owner for token in ("landing", "next.requests", "dependency_")),
        "no_new_feature": report["new_feature_required"] is False,
        "no_new_cli": report["new_cli_required"] is False,
        "no_new_registry": report["new_registry_required"] is False,
        "not_delivery_complete": report["delivery_complete"] is False,
        "no_external_operations": operations == [],
    }
    # Detect source drift during evidence validation before assigning behavior.
    source_state(root, head)
    barriers = [name for name, passed in checks.items() if not passed]
    return {"schema": 1, "owner": "eval.report", "experiment_id": EXPERIMENT,
            "authorizes_landing": False, "observation_scope": "consumer_report",
            "evidence_validity": "VALID",
            "behavior": {"classification": "FAIL" if barriers else "PASS", "checks": checks, "barriers": barriers},
            "source_root": str(root), "source_head": head, "report_sha256": descriptor["sha256"],
            "auxiliary_read_only_command_failures": [item for item in commands if item.get("exit_status") not in (0, None)],
            "next": {"owner": "supervisor", "operation": "review_report_result"},
            "unknowns": ["complete platform transcript", "hidden reads", "independent no-effects observation", "actual model/config/context/compaction"]}
