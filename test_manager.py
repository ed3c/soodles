"""Test Manager: resolve requested coverage once; never infer a full run.

All entrypoints consume this decision. It grants no publication/landing authority.
"""
import ast
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import subprocess

PHYSICAL = ("worktree", "cleanup_recovery", "cleanup_lock_recovery",
            "delivery_recovery", "base_recovery", "order_handoff", "interruption_resume")
# Retired historical replays retain their current executable discriminators.
REPLACEMENTS = {
    "tests/test_candidate_guidance.py": ("test_candidate_verification",),
    "tests/test_fresh_delivery_decisions.py": ("test_landing_continuation",),
    "tests/test_instruction_activation_evidence.py": ("test_instruction_context",),
}
# Traced owner/consumer coverage for bounded changes. A missing mapping is a
# scope decision for the supervising Session, never an instruction to run all.
BOUNDARIES = (
    (("issue_atom.py", "issue_execution.py", "issue_admission.py", "supervisor_admission.py", "stage_outcome.py"),
     ("admission_revision",), ()),
    (("issue_atom.py", "issue_execution.py", "issue_admission.py", "supervisor_admission.py"),
     ("interruption_recovery",), ()),
    (("tests/fixtures/atom-feedback/",), ("atom_feedback",), ()),
    (("supervisor_admission.py", "issue_atom.py"), ("correction_preparation",), ()),
    (("supervisor_admission.py", "issue_atom.py", "issue_admission.py",
      "issue_execution.py", "soodles.py"), ("scope_amendment",), ()),
    (("stage_outcome.py", "stage-outcome", "schema_manager.py", "issue_execution.py", "handoff_oracle.py"),
     ("feedback_owner", "stage_outcome"), ()),
    (("schema_manager.py", "soodles.py", "stage_outcome.py"), ("pclass_feedback",), ()),
    (("schema_manager.py", "issue_atom.py"), ("cost_telemetry",), ()),
    (("cost_telemetry.py", "docs/loop-cost/evidence.json"),
     ("cost_telemetry", "schema_manager", "issue_atom", "lifecycle_activation", "candidate_verification"), ()),
    (("schema_manager.py", "policy/host-finalization.json",
      "docs/experiments/schema-manager/manifest.json",
      "docs/experiments/schema-manager/product-results.json",
      "docs/experiments/schema-manager/timing.json",
      "docs/experiments/schema-plan-fields/"),
     ("schema_manager", "issue_atom", "lifecycle_activation", "system_context"), ()),
    (("docs/publisher-push-evidence.json",), ("candidate_verification", "publisher_receipts"), ()),
    (("atom_repair.py", "policy/repair-policy.json"),
     ("atom_repair", "issue_atom", "lifecycle_activation", "system_context"), ()),
    (("system_context.py", "contracts/system-v1/routes.json"),
     ("system_context", "atom_repair", "lifecycle_activation"), ()),
    (("docs/experiments/bounded-repair/manifest.json",
      "docs/experiments/bounded-repair/product-results.json"),
     ("candidate_verification", "atom_repair"), ()),
    (("docs/test-manager-delivery/evidence.json", "docs/ste-writing/manifest.json", "docs/small-loop/manifest.json"),
     ("candidate_verification",), ()),
    (("docs/owner-base-continuation-evidence.json",), ("candidate_verification",), ()),
    (("docs/cleanup-integration-evidence.json",), ("candidate_verification", "cleanup_continuation"), ()),
    (("soodles", "soodles.py", ".github/workflows/runtime.yml"),
     ("admission", "test_suite", "delivery_refs"), ()),
    (("test_manager.py", "test_selection.py"), ("test_suite",), ()),
    (("issue_admission.py",),
     ("issue_admission", "candidate_verification", "comparison_gate", "instruction_context",
      "cross_repository_delivery", "cross_repository_dependency", "supervisor_admission",
      "issue_execution", "issue_atom", "candidate_publication"),
     ("order_handoff", "interruption_resume")),
    (("issue_execution.py",),
     ("issue_execution", "issue_resume", "schedule_role", "supervisor_admission",
      "issue_atom", "instruction_context", "landing"),
     ("order_handoff", "interruption_resume")),
    (("repository_binding.py", "dependency_binding.py"),
     ("cross_repository_dependency", "cross_repository_delivery", "issue_admission",
      "candidate_publication", "landing", "next_issue", "provider_readback"),
     ("delivery_recovery",)),
    (("provider_credential.py",),
     ("provider_credential", "issue_atom", "supervisor_admission", "provider_readback",
      "local_provider_transport", "next_issue"), ()),
    (("policy/runtime.lock.json",), ("admission",), PHYSICAL),
    (("tests/comparison_fixture.py",), ("comparison_gate",), ()),
    ((".gitignore",), ("admission", "candidate_publication"), ()),
    (("issue_atom.py", "issue-atom"),
     ("issue_atom", "publisher_receipts", "base_readmission", "local_continuation",
      "instruction_context", "lifecycle_activation", "cleanup_continuation"), ()),
    (("candidate_publication.py", "candidate-publish"),
     ("candidate_publication", "publisher_receipts", "issue_atom", "comparison_gate"), ()),
    (("supervisor_admission.py", "supervisor-admission"),
     ("supervisor_admission", "issue_atom", "instruction_context", "issue_execution"),
     ("order_handoff", "interruption_resume")),
    (("landing.py",),
     ("landing", "landing_continuation", "cleanup_continuation", "landing_bootstrap", "landing_supervisor",
      "local_continuation", "local_provider_transport", "issue_atom",
      "comparison_gate", "cross_repository_dependency", "cross_repository_delivery"),
     ("cleanup_recovery", "cleanup_lock_recovery", "delivery_recovery", "base_recovery")),
    (("landing_supervisor.py", "landing-supervisor"),
     ("landing_supervisor", "issue_atom"), ()),
    (("provider_transport.py", "provider-execute"),
     ("local_provider_transport", "issue_atom"), ()),
    (("provider_readback.py", "provider-readback"), ("provider_readback",), ()),
    (("next_issue.py", "next-issue"), ("next_issue", "provider_readback"), ()),
    (("github_reader.py",),
     ("github_reader", "cross_repository_delivery", "issue_execution", "issue_atom"),
     ("interruption_resume",)),
    (("report_evaluation.py",),
     ("report_evaluation", "candidate_verification", "comparison_gate"), ()),
    (("portable_packet.py", "tests/fixtures/admission-recovery-portable/"),
     ("portable_packet", "schedule_role", "admission_recovery_pclass_replay"), ()),
    (("quality/", ".github/workflows/quality-report.yml"), ("quality",), ()),
    ((".agents/skills/verify-soodles/scripts/",),
     ("verify_skill", "pclass_decision", "pclass_replay", "context_recording",
      "admission_recovery_pclass_replay"), ()),
    (("cleanup_oracle.py",), (), ("cleanup_recovery",)),
    (("cleanup_lock_oracle.py",), (), ("cleanup_lock_recovery",)),
    (("delivery_oracle.py",), (), ("delivery_recovery",)),
    (("base_recovery_oracle.py",), (), ("base_recovery",)),
    (("handoff_oracle.py",), ("handoff_cleanup",), ("order_handoff",)),
    (("resume_oracle.py",), ("issue_resume",), ("interruption_resume",)),
)


def ci_request(kind, event, base, reason=None):
    """CI adapters consume demand here; a merge event is not a new test request."""
    if kind not in {"runtime", "quality"}:
        raise ValueError("Test Manager: unknown CI observation: " + str(kind))
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base) or base == "0" * 40:
        raise ValueError("Test Manager: CI requires an exact nonzero base commit SHA")
    if kind == "runtime" and event == "pull_request":
        reason = "exact candidate acceptance for the current PR diff"
    elif event != "workflow_dispatch" or not isinstance(reason, str) or not reason.strip():
        raise ValueError("Test Manager: additional CI work requires an explicit request and reason")
    return {"owner": "test-manager", "kind": kind, "event": event,
            "base": base, "reason": reason.strip(), "authorizes_landing": False}


def fixture_imports(files):
    """Trace Python imports once; prose mentions do not make fixture consumers."""
    imports = {}
    for module, path in files.items():
        names = set()
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                package = module.split(".")[:-node.level] if node.level else []
                prefix = ".".join([*package, node.module or ""]).strip(".")
                names.add(prefix)
                names.update((prefix + "." + alias.name).strip(".") for alias in node.names)
            elif isinstance(node, ast.Call) and (
                    isinstance(node.func, ast.Name) and node.func.id == "__import__"
                    or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    names.add(node.args[0].value)
                else:
                    raise ValueError(f"Test Manager: resolve dynamic fixture import in {path}; do not expand to full")
        names.update(name.removeprefix("tests.") for name in tuple(names))
        imports[module] = names & files.keys()
    return imports



def candidate_evidence_input(root, path):
    source = root / path
    if not path.startswith("docs/") or source.suffix != ".json" or source.is_symlink():
        return False
    try:
        value = json.loads(source.read_text())
    except (OSError, UnicodeError, ValueError):
        return False
    return (isinstance(value, dict) and set(value) == {
        "schema", "issue", "instructions", "artifacts", "owner", "authorizes_landing"}
        and type(value.get("schema")) is int and value["schema"] == 1
        and value.get("authorizes_landing") is False
        and isinstance(value.get("owner"), dict)
        and value["owner"].get("tool") == "issue_admission.validate_delivery_paths")

def select(root, changed, *, base=None, full=False, modules=(), controls=(), reason=None):
    root = Path(root)
    files = {".".join(p.relative_to(root / "tests").with_suffix("").parts): p
             for p in (root / "tests").rglob("test_*.py")}
    changed = sorted(set(changed))
    requested = bool(modules or controls)
    if full and requested:
        raise ValueError("Test Manager: choose full OR named controls, not both")
    if requested and not (isinstance(reason, str) and reason.strip()):
        raise ValueError("Test Manager: name the observed behavior in --reason for explicit local scope")
    selected, physical, reasons, unresolved = set(modules), set(controls), [], []
    imports = None
    if full:
        selected, physical = set(files), set(PHYSICAL)
        reasons.append(reason or "explicit full-suite request")
    elif requested:
        reasons.append(reason)
    else:
        for path in changed:
            source = Path(path)
            if path.startswith("tests/") and source.name.startswith("test_") and source.suffix == ".py":
                module = ".".join(source.relative_to("tests").with_suffix("").parts)
                if module not in files:
                    if path in REPLACEMENTS:
                        selected.update(REPLACEMENTS[path])
                        reasons.append(f"{path}: retired historical replay; current controls {', '.join(REPLACEMENTS[path])}")
                    else:
                        unresolved.append({"path": path, "reason": "removed test: identify its replacement coverage"})
                else:
                    if imports is None:
                        imports = fixture_imports(files)
                    consumers = {module}
                    while True:
                        extra = {name for name, dependencies in imports.items()
                                 if dependencies & consumers}
                        if extra <= consumers:
                            break
                        consumers |= extra
                    selected |= consumers
                    reasons.append(f"{path}: changed tests and imported fixture consumers: {', '.join(sorted(consumers))}")
                continue
            matched = False
            for sources, tests, probes in BOUNDARIES:
                if any(path.startswith(s) if s.endswith("/") else path == s for s in sources):
                    matched = True
                    selected.update("test_" + name for name in tests)
                    physical.update(probes)
            if matched:
                reasons.append(f"{path}: traced owner and consumers")
            elif candidate_evidence_input(root, path):
                selected.add("test_candidate_verification")
                reasons.append(f"{path}: candidate evidence input; existing admission discriminator")
            elif path.endswith(".md") or path in ("LICENSE", ".github/ISSUE_TEMPLATE/execution.yml"):
                reasons.append(f"{path}: review meaning; no runtime regression claim")
            else:
                unresolved.append({"path": path, "reason": "trace the changed behavior and name its controls"})
    if selected - files.keys():
        raise ValueError("Test Manager: missing modules: " + ", ".join(sorted(selected - files.keys())))
    if physical - set(PHYSICAL):
        raise ValueError("Test Manager: unknown physical controls: " + ", ".join(sorted(physical - set(PHYSICAL))))
    if full and not selected:
        raise ValueError("Test Manager: full discovery found no tests")
    mode = "full" if full else "focused" if selected or physical else "none"
    return {"owner": "test-manager", "status": "needs_scope" if unresolved else "ready",
            "mode": mode, "base": base, "changed_paths": changed,
            "modules": sorted(selected), "physical": [p for p in PHYSICAL if p in physical],
            "reasons": reasons or ["no changed runtime behavior selected"],
            "unresolved": unresolved, "authorizes_landing": False}



def admission_scope(root, contract):
    paths = contract.get("required_paths", contract["write_paths"])
    evidence = contract.get("evidence_manifest")
    root = Path(root)
    planned_tests = [path for path in paths if path.startswith("tests/")
        and Path(path).name.startswith("test_") and path.endswith(".py")
        and not (root / path).exists()]
    decision = select(root, [path for path in paths if path != evidence and path not in planned_tests])
    for path in planned_tests:
        module = ".".join(Path(path).relative_to("tests").with_suffix("").parts)
        decision["modules"] = sorted(set(decision["modules"]) | {module})
        decision["reasons"].append(f"{path}: planned test module; writer must supply it before execution")
        decision["mode"] = "focused"
    if evidence in paths:
        decision["modules"] = sorted(set(decision["modules"]) | {"test_candidate_verification"})
        decision["reasons"].append(f"{evidence}: declared candidate evidence uses the existing discriminator")
        decision["mode"] = "focused"
    decision["required_write_paths"] = (["test_manager.py"] if decision["unresolved"]
        and "test_manager.py" not in contract["write_paths"] else [])
    decision["reason"] = "Resolve unmapped required behavior within the admitted owner; do not request a full suite."
    return decision

def plan(root, base=None, *, full=False, modules=(), controls=(), reason=None, require_base=False):
    """Use the supplied comparison; missing input never requests a full run."""
    root = Path(root).resolve()
    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError("Test Manager: " + result.stderr.strip())
        return result.stdout
    if require_base and not base and not (full or modules or controls):
        raise ValueError("Test Manager: supply the admitted --base or an explicit coverage request; no full fallback")
    if base is not None and not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("Test Manager requires a complete base commit SHA")
    selected_base = base or git("rev-parse", "HEAD").strip()
    git("cat-file", "-e", selected_base + "^{commit}")
    paths = git("diff", "--no-renames", "--name-only", "-z", selected_base, "--").split("\0")
    paths += git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return select(root, [p for p in paths if p], base=selected_base, full=full,
                  modules=modules, controls=controls, reason=reason)


def require_ready(decision):
    if decision["status"] != "ready":
        raise ValueError("Test Manager needs scope: " + json.dumps(decision["unresolved"]) +
                         "; inspect the diff and request its named controls with --reason; do not run full as a fallback")


def requested_plan(root, args, *, require_base=False):
    return plan(root, args.base, full=args.full, modules=args.module, controls=args.control,
                reason=args.reason, require_base=require_base)


def execute_units(root, decision):
    require_ready(decision)
    if not decision["modules"]:
        return {"exit": 0, "output": "", "count": 0, "scope": "not_required"}
    return _run_suite(root, None if decision["mode"] == "full" else decision["modules"])


def _run_suite(root, modules):
    """Discover once and run each module in its own process, with exact coverage readback."""
    from soodles import Refusal, run
    from concurrent.futures import ThreadPoolExecutor
    import unittest

    root = Path(root).resolve()
    discovery_started = time.monotonic()
    loader = unittest.TestLoader()
    if modules is None:
        discovered = loader.discover(str(root / "tests"))
    else:
        if not modules or any(not re.fullmatch(r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.)*test_[a-zA-Z0-9_]+", m) for m in modules):
            raise Refusal("test selection requires explicit test module names")
        discovered = unittest.TestSuite()
        for module in modules:
            module_path = root / "tests" / (module.replace(".", "/") + ".py")
            if not module_path.is_file():
                raise Refusal("selected test module missing: " + module)
            selected = loader.discover(str(module_path.parent), pattern=module_path.name,
                                       top_level_dir=str(root / "tests"))
            if not selected.countTestCases():
                raise Refusal("selected test module is empty: " + module)
            discovered.addTests(selected)
    if loader.errors:
        raise Refusal("test discovery failed:\n" + "\n".join(loader.errors))
    groups = {}

    def collect(suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                collect(test)
            else:
                groups.setdefault(type(test).__module__, []).append(test.id())

    collect(discovered)
    if not groups:
        raise Refusal("test discovery found no tests")
    workers = min(4, os.cpu_count() or 1, len(groups))
    print(json.dumps({"event": "soodles.timing", "operation": "test.discovery",
                      "modules": len(groups), "count": sum(map(len, groups.values())),
                      "seconds": round(time.monotonic() - discovery_started, 3)}),
          file=sys.stderr, flush=True)
    started = time.monotonic()
    # Workers keep mock patches and fixture globals out of other test modules.
    code = """
import json, sys, time, unittest
sys.path.insert(0, 'tests')
seen = []
class Result(unittest.TextTestResult):
    def startTest(self, test):
        seen.append(test.id())
        self.started = time.monotonic()
        super().startTest(test)
    def stopTest(self, test):
        super().stopTest(test)
        print(json.dumps({"event": "soodles.timing", "operation": "test.case",
                          "test": test.id(), "includes": "setup, body, teardown, cleanups",
                          "seconds": round(time.monotonic() - self.started, 6)}),
              file=sys.stderr, flush=True)
suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[2:])
result = unittest.TextTestRunner(verbosity=2, resultclass=Result, durations=5).run(suite)
with open(sys.argv[1], 'w') as stream:
    json.dump(seen, stream)
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
"""
    with tempfile.TemporaryDirectory(prefix="soodles-tests-") as directory:
        def execute(item):
            module, names = item
            receipt = Path(directory) / (module + ".json")
            module_started = time.monotonic()
            # Individual external operations retain their own timeouts. The CI
            # job budget bounds acceptance; suite size is not a 120-second failure.
            process = run([sys.executable, "-B", "-c", code, receipt, *names], root, timeout=None)
            seen = json.loads(receipt.read_text()) if receipt.exists() else []
            complete = sorted(seen) == sorted(names) and len(set(seen)) == len(names)
            output = process.stderr + process.stdout
            if not complete:
                output += f"\n{module}: test execution did not match discovery\n"
            print(json.dumps({"event": "soodles.timing", "operation": "test.module",
                              "module": module, "source": str(root), "count": len(names),
                              "seconds": round(time.monotonic() - module_started, 3),
                              "exit": process.returncode, "complete": complete}),
                  file=sys.stderr, flush=True)
            return process.returncode == 0 and complete, output

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(execute, sorted(groups.items())))
    return {"exit": 0 if all(ok for ok, _ in results) else 1,
            "output": "".join(output for _, output in results),
            "count": sum(map(len, groups.values())), "workers": workers,
            "seconds": round(time.monotonic() - started, 3)}


def review_cost(facts):
    """Review normal observations without selecting tests, repair, or effects."""
    findings, unknowns = [], []
    needs_readback = False
    for phase in facts["summary"].get("phase_costs", []):
        context = {"phase": phase["phase"], "worker": phase["worker"],
                   "sources": phase["sources"]}
        findings.append({**context, "kind": "observed_cost", "observation": {
            key: phase[key] for key in ("kind", "observations", "measured_spans",
                                       "inclusive_seconds", "statuses")}})
        if phase["measured_spans"] < phase["observations"] and set(phase["statuses"]) != {"not_required"}:
            unknowns.append({**context, "kind": "unmeasured_spans",
                             "reason": "Some observed spans have no duration."})
        if any(phase["statuses"].get(status, 0) for status in ("failed", "refused")):
            needs_readback = True
            findings.append({**context, "kind": "owner_readback_required",
                             "observation": phase["statuses"],
                             "reason": "Recorded failures or refusals need the original owner's current readback."})
        if phase["phase"] == "test.module" and phase["worker"] and phase["observations"] > 1:
            needs_readback = True
            findings.append({**context, "kind": "repeated_module_observations",
                             "observation": {"runs": phase["observations"]},
                             "reason": "Multiple runs are recorded. Their necessity is not established."})
            unknowns.append({**context, "kind": "repeat_necessity",
                             "reason": "The original owner must compare each run's inputs and required behavior."})
    for family, coverage in facts["coverage"].items():
        if coverage["status"] in {"unknown", "partial"}:
            unknowns.append({"family": family, "kind": "coverage",
                             "status": coverage["status"], "sources": coverage["evidence"],
                             "reason": coverage["reason"]})
    for metric, value in facts["summary"].items():
        if value is None:
            unknowns.append({"metric": metric, "kind": "unmeasured_summary",
                             "sources": facts["sources"],
                             "reason": "Available observations do not establish this measurement."})
    return {"owner": "test-manager", "subject": facts["subject"], "sources": facts["sources"],
            "status": "needs_owner_readback" if needs_readback else "reviewed",
            "findings": findings, "unknowns": unknowns,
            "next": {"owner": "original-owner", "required": "original_owner_readback",
                     "continuation": "existing_owner_next"} if needs_readback else None,
            "effects": [], "test_demand": None, "authorizes_landing": False}


def feedback_scope(result, previous=None):
    """Select consumer observations from current needs, never a software full suite."""
    old = previous or {}
    reuse, needed, verified = [], [], []
    prior_cases = {case["id"]: case for case in old.get("cases", [])}
    current_cases = {case["id"]: case for case in result.get("cases", [])}
    for name, identity in result.get("case_fingerprints", {}).items():
        reusable = (result.get("criteria", {}).get("status") == "SUPPORTED"
                    and old.get("criteria", {}).get("status") == "SUPPORTED"
                    and old.get("case_fingerprints", {}).get(name) == identity
                    and prior_cases.get(name, {}).get("status") == "passed")
        if current_cases.get(name, {}).get("status") == "passed":
            verified.append(name)
        elif (current_cases.get(name, {}).get("status") == "failed"
              or any(value is False for value in current_cases.get(name, {}).get("checks", {}).values())):
            needed.append(name)
        else:
            (reuse if reusable else needed).append(name)
    if result.get("criteria", {}).get("status") != "SUPPORTED":
        needed = []
    from schema_manager import project_cost
    cost = project_cost({"subject": result.get("subject"), "coverage": "current feedback projection only",
        "summary": {"schema_ms": result.get("elapsed_ms"), "projection_ms": result.get("projection_ms"),
                    "model_ms": None, "tokens": None},
        "sources": result.get("sources", [])})
    return {"owner": "test-manager", "mode": "focused", "cases": needed, "reuse": reuse, "verified": verified,
            "cost": cost,
            "modules": [], "physical": [], "full": False,
            "reason": "Resolve criteria first; reuse matching passed observations; observe only affected cases.",
            "authorizes_landing": False}
