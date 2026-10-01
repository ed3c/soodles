"""Read one explicit system-v1 prerequisite closure from committed Git objects."""
import ast
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
    require(isinstance(value, dict) and set(value) in ({"schema", "paths"}, {"schema", "paths", "entries"}), "routes.fields", value)
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
    entry = roots[1:] if roots and roots[0] == "entry" else None
    if entry is not None:
        require(len(entry) in (2, 3) and all(isinstance(item, str) and not item.startswith("-")
                                           for item in entry), "entry.arguments", entry)
        roots = ["contracts/system-v1/common.md"]
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
    mappings = validate_entries(root, head, value, paths)
    if entry is not None:
        key = " ".join(entry)
        require(key in mappings, "entry.unknown", key)
        mapping = mappings[key]
        roots = sorted({path for decision in mapping["decisions"] for path in decision["requires"]})
    for path in roots:
        require(path in paths, "roots.path", path)
    selected = dependency_order(paths, roots)
    pins = committed_pins(root, head, selected)
    context = resolve_instruction_context(root, head, pins)
    return {"owner": OWNER, "status": "ready", "source_head": head,
            "paths": {path: paths[path] for path in selected},
            "instruction_paths": selected, "instruction_pins": pins,
            "instruction_context": context, "authorizes_landing": False,
            **({"entry": key, "consumers": mapping["decisions"],
                "source_pins": committed_pins(root, head, [ROUTES, "policy/repair-policy.json", "atom_repair.py"] + mapping["sources"])} if entry is not None else {})}



# Finite registration: paths are P requirements of decisions, not phase guesses.
ENTRY_CONSUMERS = {
    "issue-atom run": ("issue_atom.py", "issue_atom._run_owned"),
    "soodles candidate publish": ("candidate_publication.py", "candidate_publication.publish"),
    "provider-readback consume": ("provider_readback.py", "provider_readback.consume"),
}
ENTRY_DECISIONS = {
    "soodles candidate publish": {
        "validate_inputs": ("candidate_publication.validate_inputs", ["candidate"]),
        "confirm_effect": ("candidate_publication.publish", ["candidate", "readback"]),
    },
    "provider-readback consume": {
        "validate_GET_projection": ("provider_readback._next_projection", ["readback"]),
        "materialize_readback": ("provider_readback.consume", ["readback"]),
    },
}


def validate_entries(root, head, value, paths, read_source=None):
    entries = value.get("entries")
    if entries is None:
        return {}  # Existing committed file-root graphs stay compatible.
    require(isinstance(entries, dict) and set(entries) == set(ENTRY_CONSUMERS), "entries", entries)
    def read(names):
        if read_source is not None:
            return {"files": [{"path": name, "content": read_source(name)} for name in names]}
        return resolve_instruction_context(root, head, committed_pins(root, head, names))
    # Cold validation only; runtime decisions consume the compiled data.
    from atom_repair import load, DECISIONS, RepairRefusal
    read(["atom_repair.py"])
    raw = read(["policy/repair-policy.json"])
    try:
        policy = load(raw["files"][0]["content"])
    except RepairRefusal as error:
        raise AdmissionRefusal(error.invalid["field"], error.invalid["value"]) from error
    for path in paths:
        if path != "contracts/system-v1/common.md":
            require("contracts/system-v1/common.md" in dependency_order(paths, [path]),
                    "entry.prerequisite", path)
    for entry, (source, consumer) in ENTRY_CONSUMERS.items():
        record = entries[entry]
        exact_object(record, {"sources", "decisions"}, "entry.fields")
        expected_sources = [source] + (["candidate_publication.py", "provider_readback.py", "system_context.py", "issue-atom"] if entry == "issue-atom run" else ["soodles", "soodles.py"] if entry == "soodles candidate publish" else ["provider-readback"])
        require(record["sources"] == expected_sources, "entry.sources", record["sources"])
        committed = read(expected_sources)
        definitions = set()
        for file in committed["files"]:
            if not file["path"].endswith(".py"):
                continue
            try:
                tree = ast.parse(file["content"])
            except SyntaxError as error:
                raise AdmissionRefusal("entry.source_syntax", file["path"]) from error
            definitions.update(file["path"][:-3] + "." + node.name for node in tree.body
                               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        decisions = record["decisions"]
        require(isinstance(decisions, list) and bool(decisions), "entry.decisions", decisions)
        expected = list(DECISIONS) if entry == "issue-atom run" else list(ENTRY_DECISIONS[entry])
        require([d.get("signal") for d in decisions if isinstance(d, dict)] == expected, "entry.coverage", decisions)
        for decision in decisions:
            exact_object(decision, {"signal", "consumer", "requires"}, "entry.decision")
            signal = decision["signal"]
            if entry == "issue-atom run":
                expected_consumer = policy["signals"][signal]["consumer"]
                requires = policy["signals"][signal]["requires"]
            else:
                expected_consumer, names = ENTRY_DECISIONS[entry][signal]
                requires = ["contracts/system-v1/" + name + ".md" for name in names]
            require(decision["consumer"] == expected_consumer, "entry.consumer", decision["consumer"])
            require(decision["consumer"] in definitions, "entry.consumer_missing", decision["consumer"])
            require(decision["requires"] == requires, "entry.requires", decision["requires"])
            require(all(path in paths for path in decision["requires"]), "entry.dangling", decision)
    return entries


def compile_repair(root):
    """Compile the already source-bound owner's finite P closure at admission."""
    def read(name):
        return (root / name).read_text()
    value = json.loads(read(ROUTES), object_pairs_hook=unique_object,
                       parse_constant=invalid_constant)
    paths = validate_routes(value)
    entries = validate_entries(root, None, value, paths, read)
    require("issue-atom run" in entries, "entry.unknown", "issue-atom run")
    decisions = {}
    for decision in entries["issue-atom run"]["decisions"]:
        closure = dependency_order(paths, decision["requires"])
        decisions[decision["signal"]] = {
            "consumer": decision["consumer"], "requires": closure,
            "pins": [{"path": name, "sha256": hashlib.sha256(read(name).encode()).hexdigest()}
                     for name in closure]}
    return decisions


def _main(argv=None):
    try:
        value = select(Path(__file__).resolve().parent,
                       sys.argv[1:] if argv is None else argv)
    except AdmissionRefusal as error:
        value = {"owner": OWNER, "status": "refused", "invalid": error.invalid,
                 "classification": "invalid_entry",
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


def main(argv=None):
    # Nested input can exceed a carrier's recursion limit while parsing,
    # constructing a refusal, or serializing the diagnostic.
    try:
        return _main(argv)
    except RecursionError:
        print(json.dumps({"owner": OWNER, "status": "refused",
                          "invalid": {"field": "routes.depth",
                                      "value": "nested input exceeds interpreter capacity"},
                          "next": {"kind": "input", "owner": "Soodles Issue admission",
                                   "required": ["valid_committed_system_context_selection"]},
                          "authorizes_landing": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
