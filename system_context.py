"""Read one explicit system-v1 prerequisite closure from committed Git objects."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from issue_admission import (
    AdmissionRefusal, exact_object, git_bytes, git_path, require,
    resolve_instruction_context,
)

ROUTES = "contracts/system-v1/routes.json"
KNOWN_PATHS = frozenset(
    f"contracts/system-v1/{name}.md" for name in (
        "common", "runtime", "landing", "recovery", "candidate", "readback",
        "issue-atom", "instruction-context",
    )
)
OWNER = "soodles.system-context"


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "routes.duplicate_key", key)
        value[key] = item
    return value


def invalid_constant(value):
    raise ValueError(f"non-JSON number: {value}")


def dependency_order(paths, roots):
    ordered, active, done = [], set(), set()

    def visit(path):
        require(path not in active, "routes.cycle", path)
        if path in done:
            return
        active.add(path)
        for dependency in sorted(paths[path]["requires"]):
            visit(dependency)
        active.remove(path)
        done.add(path)
        ordered.append(path)

    for path in sorted(roots):
        visit(path)
    return ordered


def validate_routes(value):
    exact_object(value, {"schema", "paths"}, "routes.fields")
    require(type(value["schema"]) is int and value["schema"] == 1,
            "routes.schema", value["schema"])
    paths = value["paths"]
    require(isinstance(paths, dict) and bool(paths), "routes.paths", paths)
    for path, record in paths.items():
        git_path(path, "routes.path")
        require(path in KNOWN_PATHS, "routes.path", path)
        exact_object(record, {"requires"}, "routes.record")
        dependencies = record["requires"]
        require(isinstance(dependencies, list), "routes.requires", dependencies)
        for dependency in dependencies:
            git_path(dependency, "routes.requires.path")
            require(dependency in paths, "routes.dangling", dependency)
        require(len(dependencies) == len(set(dependencies)),
                "routes.requires.duplicate", path)
    # Invalid unselected records cannot hide behind a legal root.
    dependency_order(paths, paths)
    return paths


def committed_pins(root, head, paths):
    return [{"path": path, "sha256": hashlib.sha256(
        git_bytes(root, head, path)).hexdigest()} for path in paths]


def select(root, roots):
    require(isinstance(roots, list) and bool(roots), "roots", roots)
    for path in roots:
        git_path(path, "roots.path")
        require(path in KNOWN_PATHS, "roots.path", path)
    result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root,
                            capture_output=True, text=True, timeout=30)
    require(result.returncode == 0, "source_head", result.stderr.strip())
    head = result.stdout.strip()
    route_context = resolve_instruction_context(
        root, head, committed_pins(root, head, [ROUTES]))
    try:
        value = json.loads(route_context["files"][0]["content"],
                           object_pairs_hook=unique_object,
                           parse_constant=invalid_constant)
    except (ValueError, RecursionError) as error:
        raise AdmissionRefusal("routes.json", str(error)) from error
    paths = validate_routes(value)
    for path in roots:
        require(path in paths, "roots.path", path)
    selected = dependency_order(paths, roots)
    pins = committed_pins(root, head, selected)
    context = resolve_instruction_context(root, head, pins)
    return {"owner": OWNER, "status": "ready", "source_head": head,
            "paths": {path: paths[path] for path in selected},
            "instruction_paths": selected, "instruction_pins": pins,
            "instruction_context": context, "authorizes_landing": False}


def main(argv=None):
    try:
        value = select(Path(__file__).resolve().parent,
                       sys.argv[1:] if argv is None else argv)
    except AdmissionRefusal as error:
        value = {"owner": OWNER, "status": "refused", "invalid": error.invalid,
                 "next": {"kind": "input", "owner": "Soodles Issue admission",
                          "required": ["valid_committed_system_context_selection"]},
                 "authorizes_landing": False}
    except (OSError, subprocess.SubprocessError) as error:
        value = {"owner": OWNER, "status": "refused",
                 "invalid": {"field": "git.read", "value": str(error)},
                 "next": {"kind": "input", "owner": "Git",
                          "required": ["readable_committed_repository"]},
                 "authorizes_landing": False}
    print(json.dumps(value, ensure_ascii=True, indent=2))
    return 0 if value["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
