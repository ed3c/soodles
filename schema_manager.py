"""Fixed host-finalization decisions. The atom alone owns evidence and effects."""
import ast
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import re
import time
from pathlib import Path

from system_context import compile_repair, unique_object

PLAN_PATH = "policy/host-finalization.json"
FACTS = ("cleanup_allowed", "landing_resolved", "loop_live", "loop_absent",
         "config_installed", "config_restored", "stop_offered", "restore_offered",
         "owner_confirmed")
RULES = {
    "stop": {"cleanup_allowed": True, "loop_live": True, "stop_offered": False},
    "restore": {"cleanup_allowed": True, "loop_absent": True,
                "config_installed": True, "restore_offered": False},
    "confirm": {"cleanup_allowed": True, "loop_absent": True, "config_restored": True},
    "complete": {"landing_resolved": True, "loop_absent": True,
                 "config_restored": True, "owner_confirmed": True},
}

# Finite adapter vocabulary. These are readback labels, never expressions to run.
READBACKS = {
    "cleanup_allowed": (["authorization_sha256"], "soodles.issue-atom", "original_owner_readback"),
    "landing_resolved": (["landing.classification"], "external landing owner", "fresh_owner_readback"),
    "loop_live": (["noodle_start.pid", "ps.returncode", "ps.stdout", "noodle_process_argv"],
                  "Noodle", "original_start_process_readback"),
    "loop_absent": (["noodle_start", "ps.returncode", "os.killpg:ProcessLookupError"],
                    "Noodle", "quiescent_noodle_owner"),
    "config_installed": (["host_config_identity", "noodle_start.config_sha256"],
                         "soodles.issue-atom", "unchanged_installed_configuration"),
    "config_restored": (["host_config_identity", "authorization.host_config_sha256"],
                        "soodles.issue-atom", "original_host_recovery_readback"),
    "stop_offered": (["noodle_start.stop_offered"], "Noodle", "original_start_process_readback"),
    "restore_offered": (["noodle_start.restore_offered"], "soodles.issue-atom", "original_host_recovery_readback"),
    "owner_confirmed": (["host_finalization.facts.landing_resolved", "host_finalization.facts.loop_absent",
                         "host_finalization.facts.config_restored", "noodle_completion_ack"],
                        "soodles.issue-atom", "original_owner_readback"),
}


def field_contract(name):
    readbacks, owner, required = READBACKS[name]
    return {
        "type": "boolean", "legal_values": [False, True],
        "producer": {"file": "issue_atom.py", "function":
                     "finish_host.confirm" if name == "owner_confirmed" else "finish_host"},
        "readbacks": readbacks,
        "consumers": [node for node, rule in RULES.items() if name in rule],
        "identity": ["authorization", "subject", "plan"],
        "invalidation": (["landing_resolved", "loop_absent", "config_restored"]
                         if name == "owner_confirmed" else ["original_owner_readback_changed"]),
        "missing_input": {"owner": owner, "required": required},
    }


def producer_key(field):
    return field["producer"]["file"] + ":" + field["producer"]["function"]


class SchemaRefusal(ValueError):
    pass


def require(value, field):
    if not value:
        raise SchemaRefusal("host_finalization." + field)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Plan:
    identity: str
    context: dict
    sources: dict
    rules: dict
    affected: dict
    catalog: dict

    def validate_sources(self, root):
        for name, expected in self.sources.items():
            require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected,
                    "source_changed:" + name)


def compile_plan(root, *, read_bytes=None):
    root = Path(root)
    if read_bytes is None:
        def read_bytes(name):
            return (root / name).read_bytes()
    raw = read_bytes(PLAN_PATH)
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(isinstance(value, dict) and type(value.get("schema")) is int
            and value["schema"] in (1, 2), "plan.schema")
    fields = {"schema", "owner", "context", "facts", "nodes"}
    require(set(value) == fields | ({"entry"} if value["schema"] == 2 else set()), "plan.fields")
    require(value["owner"] == "issue_atom" and value["context"] == "cleanup_residue", "plan.owner")
    require(value["nodes"] == RULES and all(type(v) is bool
            for rule in value["nodes"].values() for v in rule.values()), "plan.nodes")
    catalog = {}
    if value["schema"] == 1:
        require(value["facts"] == list(FACTS), "plan.facts")
    else:
        require(value["entry"] == "issue-atom run", "catalog.entry")
        catalog = value["facts"]
        require(isinstance(catalog, dict), "catalog.facts")
        for name in sorted(set(catalog) ^ set(FACTS)):
            require(False, "catalog.fact:" + name)
        for name, field in catalog.items():
            expected = field_contract(name)
            require(isinstance(field, dict) and set(field) == set(expected), "catalog.fields:" + name)
            for key, item in expected.items():
                require(field[key] == item, "catalog." + name + "." + key)
            require(all(type(v) is bool for v in field["legal_values"]), "catalog." + name + ".legal_values")
        source = ast.parse(read_bytes("issue_atom.py").decode("utf-8"))
        owner = next((n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "finish_host"), None)
        require(owner is not None, "catalog.producer:issue_atom.py:finish_host")
        require(any(isinstance(n, ast.FunctionDef) and n.name == "confirm" for n in owner.body),
                "catalog.producer:issue_atom.py:finish_host.confirm")
    context = compile_repair(root, read=lambda name: read_bytes(name).decode("utf-8"))["cleanup_residue"]
    require(context["consumer"] == "issue_atom.finish_host", "consumer")
    names = ["schema_manager.py", PLAN_PATH, "issue_atom.py", "system_context.py",
             "atom_repair.py", "policy/repair-policy.json", "contracts/system-v1/routes.json"]
    names += context["requires"]
    sources = {name: hashlib.sha256(read_bytes(name)).hexdigest() for name in names}
    return Plan(digest(sources), context, sources, value["nodes"],
                {fact: tuple(node for node, rule in RULES.items() if fact in rule) for fact in FACTS}, catalog)


@lru_cache(maxsize=4)
def compiled(root):
    """One bounded owner process reuses compilation; effects still check bytes."""
    return compile_plan(root)


class Manager:
    def __init__(self, plan, identity, record=None):
        require(set(identity) == {"authorization", "subject", "plan"}
                and identity["plan"] == plan.identity
                and all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v)
                        for v in identity.values()), "identity")
        self.plan, self.identity = plan, dict(identity)
        self.sequence, self.facts = 0, {}
        if record is not None:
            require(isinstance(record, dict) and set(record) == {"identity", "sequence", "facts"}, "record")
            require(record["identity"] == self.identity, "identity")
            require(type(record["sequence"]) is int and record["sequence"] > 0, "sequence")
            self.validate_facts(record["facts"], legacy=True)
            self.sequence = record["sequence"]
            self.facts = {k: dict(v) for k, v in record["facts"].items()}
        self.ready = {node: self.evaluate(node) for node in plan.rules}

    def validate_facts(self, facts, *, legacy=False):
        require(isinstance(facts, dict) and set(facts) <= set(FACTS), "facts")
        for name, fact in facts.items():
            require(isinstance(fact, dict) and set(fact) in ({"value", "evidence"}, {"value", "evidence", "producer"})
                    and type(fact["value"]) is bool and isinstance(fact["evidence"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", fact["evidence"]), "fact:" + name)
            if "producer" in fact:
                require(name in self.plan.catalog and fact["producer"] == producer_key(self.plan.catalog[name]),
                        "fact.producer:" + name)
            else:
                require(legacy or not self.plan.catalog or self.facts.get(name) == fact,
                        "fact.producer_missing:" + name)
        require(not (facts.get("loop_live", {}).get("value")
                     and facts.get("loop_absent", {}).get("value")), "contradictory_loop")

    def evaluate(self, node):
        return all(self.facts.get(k, {}).get("value") is v for k, v in self.plan.rules[node].items())

    def apply(self, event):
        require(isinstance(event, dict) and set(event) == {"identity", "sequence", "facts"}, "event")
        require(event["identity"] == self.identity, "identity")
        sequence, facts = event["sequence"], event["facts"]
        require(type(sequence) is int, "sequence")
        self.validate_facts(facts)
        if sequence == self.sequence:
            require(facts == self.facts, "conflicting_replay")
            return self.project()
        require(sequence == self.sequence + 1, "sequence")
        changed = {k for k in set(facts) | set(self.facts) if facts.get(k) != self.facts.get(k)}
        # Confirmation belongs to the original owner and the exact physical/landing facts.
        if changed & {"landing_resolved", "loop_absent", "config_restored"}:
            require(not facts.get("owner_confirmed", {}).get("value"), "confirmation_invalidated")
        self.sequence, self.facts = sequence, {k: dict(v) for k, v in facts.items()}
        affected = {node for fact in changed for node in self.plan.affected[fact]}
        for node in affected:
            self.ready[node] = self.evaluate(node)
        return self.project()

    def observe(self, updates):
        """Only the atom calls this adapter, using freshly validated owner evidence."""
        facts = {**self.facts, **updates}
        for name, value in updates.items():
            require(name in FACTS, "fact:" + name)
            if value is None:
                facts.pop(name, None)
        if any(facts.get(k) != self.facts.get(k) for k in
               ("landing_resolved", "loop_absent", "config_restored")):
            facts.pop("owner_confirmed", None)
        if facts == self.facts:
            return self.project()
        return self.apply({"identity": self.identity, "sequence": self.sequence + 1, "facts": facts})

    def record(self):
        return {"identity": dict(self.identity), "sequence": self.sequence,
                "facts": {k: dict(v) for k, v in self.facts.items()}}

    def project(self):
        actions = [node for node in ("stop", "restore", "confirm") if self.ready[node]]
        unknown = (self.facts.get("stop_offered", {}).get("value")
                   and self.facts.get("loop_live", {}).get("value")) or (
                       self.facts.get("restore_offered", {}).get("value")
                       and not self.facts.get("config_restored", {}).get("value"))
        return {"status": "complete" if self.ready["complete"] else "stop" if unknown
                else "ready" if actions else "wait", "ready": actions,
                "required": "original_owner_readback" if unknown else None,
                "authorizes_landing": False,
                "identity": dict(self.identity), "sequence": self.sequence,
                "entry": "issue-atom run", "context": self.plan.context,
                "catalog_status": "selected" if self.plan.catalog else "legacy_without_catalog",
                "facts": {name: {
                    "status": "observed" if name in self.facts else "unknown",
                    "observation": dict(self.facts[name]) if name in self.facts else None,
                    "provenance": ("recorded" if "producer" in self.facts.get(name, {}) else
                                   "legacy_without_producer" if name in self.facts else "missing"),
                    "field": self.plan.catalog.get(name),
                } for name in FACTS},
                "dag": {node: {
                    "status": "ready" if self.ready[node] else "blocked" if any(
                        name in self.facts and self.facts[name]["value"] is not value
                        for name, value in rule.items()) else "unknown",
                    "requires": [{"fact": name, "value": value,
                                  "status": "unknown" if name not in self.facts else
                                  "ready" if self.facts[name]["value"] is value else "blocked"}
                                 for name, value in rule.items()],
                } for node, rule in self.plan.rules.items()}}


def project_cost(facts, gate=None, *, review=None):
    """Data-only observation projection; original owners retain every hard gate."""
    require(isinstance(facts, dict) and set(facts) == {"subject", "coverage", "summary", "sources"},
            "cost_facts")
    # Finite numeric evidence was normalized before entry. Recheck at this public
    # boundary so a direct caller cannot silently introduce NaN or negative cost.
    import math
    def validate_numbers(value, path):
        if type(value) in (int, float):
            require(math.isfinite(value) and value >= 0, "cost_number:" + path)
        elif isinstance(value, dict):
            for key, child in value.items():
                validate_numbers(child, path + "." + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                validate_numbers(child, path + "." + str(index))
    validate_numbers(facts["summary"], "summary")
    gate = gate or {"status": "unknown", "basis": "original owner evidence unavailable"}
    if review is not None:
        require(review.get("owner") == "test-manager"
                and review.get("subject") == facts["subject"]
                and review.get("sources") == facts["sources"]
                and review.get("effects") == [] and review.get("test_demand") is None
                and review.get("authorizes_landing") is False, "cost_review_identity")
    return {"status": "observed", "subject": facts["subject"],
            "coverage": facts["coverage"], "cost": facts["summary"],
            "sources": facts["sources"], "review": review,
            "hard_gate": gate, "required": gate.get("required"),
            "budget_basis": gate.get("basis"),
            "authorizes_landing": False, "effects": [], "test_demand": None}


def owner_transition(result):
    state = result.get("continuation_state")
    next_action = result.get("next")
    action = next_action if isinstance(next_action, dict) else {}
    required = action.get("required", [])
    gaps = []
    if state not in ("ready", "waiting", "input_required", "complete", "unknown"):
        gaps.append("continuation_state: missing or invalid owner declaration")
    if not isinstance(result.get("owner"), str) or not result["owner"]:
        gaps.append("owner: missing transition owner")
    if state == "complete":
        if result.get("status") != "resolved" or "next" not in result or next_action is not None:
            gaps.append("complete: requires status=resolved and next=null")
        if result.get("waiting_on") is not None:
            gaps.append("waiting_on: conflicts with complete")
    elif state in ("ready", "waiting", "input_required"):
        if not isinstance(next_action, dict) or not next_action:
            gaps.append("next: requires the original owner continuation")
        if not isinstance(required, list) or any(not isinstance(item, str) or not item for item in required):
            gaps.append("next.required: requires a list of named prerequisites")
        if "owner" in action and (not isinstance(action["owner"], str) or not action["owner"]):
            gaps.append("next.owner: requires a named owner")
        if state == "ready":
            if result.get("status") not in ("refused", "resumed", "prepared"):
                gaps.append("status: inconsistent with ready continuation")
            if required:
                gaps.append("next.required: ready continuation has unmet prerequisites")
            if result.get("waiting_on") is not None:
                gaps.append("waiting_on: conflicts with ready")
            if "kind" in action and action["kind"] != "executable":
                gaps.append("next.kind: ready continuation must be executable")
            argv = action.get("argv")
            if not isinstance(argv, list) or not argv or not argv[0] or any(
                    not isinstance(arg, str) or "\0" in arg for arg in argv):
                gaps.append("next.argv: requires a nonempty executable and string arguments without NUL")
            environment = action.get("environment", {})
            if not isinstance(environment, dict) or any(
                    not isinstance(key, str) or not key or "=" in key or "\0" in key
                    or not isinstance(value, str) or "\0" in value
                    for key, value in environment.items()):
                gaps.append("next.environment: requires valid string names and string values without NUL")
        else:
            if result.get("status") != ("pending" if state == "waiting" else "refused"):
                gaps.append("status: inconsistent with " + state)
            if not required:
                gaps.append("next.required: missing wait condition or owner input")
            if state == "waiting" and action.get("kind") != "executable":
                gaps.append("next.kind: waiting must retain its executable continuation")
            if state == "input_required" and not action.get("owner"):
                gaps.append("next.owner: missing input owner")
            if state == "input_required" and action.get("kind") != "input":
                gaps.append("next.kind: input_required must name an input")
            if "waiting_on" in result and (
                    state != "waiting" or not isinstance(result["waiting_on"], str) or not result["waiting_on"]):
                gaps.append("waiting_on: inconsistent with " + state)
    if state == "unknown":
        gaps.append("continuation_state: owner has not established continuation readiness")
    return {"status": "unknown" if gaps else state, "owner": result.get("owner"),
            "continuation_owner": action.get("owner"), "requires": required,
            "waiting_on": result.get("waiting_on"), "gaps": gaps}


def project_owner_feedback(result):
    """Bind cost findings to the current owner's continuation, without effects."""
    started = time.perf_counter()
    cost = result.get("cost") or {}
    review = (cost.get("schema_projection") or {}).get("review")
    transition = owner_transition(result)
    legacy_terminal = ("continuation_state" not in result and result.get("status") == "resolved"
                       and "next" in result and result["next"] is None)
    dispositions = {"ready": "consume_current_owner_next", "waiting": "wait_for_owner_change",
                    "input_required": "supply_owner_input", "complete": "history_retained",
                    "unknown": "owner_readback_required"}
    return {"owner": "schema-manager", "state": result.get("status"),
            "phase": result.get("phase"), "transition_owner": result.get("owner"),
            "next": result.get("next"), "cost_review": review,
            "review_disposition": "history_retained" if legacy_terminal else dispositions[transition["status"]],
            "dag": {
                "cost_review": {"status": "observed" if review else "unknown",
                                "requires": ["normal_execution_logs", "test_manager_review"]},
                "owner_transition": transition,
                "effectiveness": {"status": "unknown", "requires": ["task_selected_normal_use_evidence"]}},
            "limits": ["Historical failures do not prove a current defect.",
                       "Owner resolution does not prove all requested outcomes or reduced cost.",
                       "Ready permits invoking the original continuation, not its effects.",
                       "Unknown projection does not invalidate the original owner response."],
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "effects": [], "test_demand": None, "authorizes_landing": False}


class FeedbackRefusal(ValueError):
    def __init__(self, field, reason, validity="INVALID"):
        self.field, self.reason, self.validity = field, reason, validity
        super().__init__(f"{field}: {reason}")


def feedback_require(condition, field, reason, validity="INVALID"):
    if not condition:
        raise FeedbackRefusal(field, reason, validity)


def feedback_object(value, fields, field):
    feedback_require(type(value) is dict and set(value) == set(fields), field,
                     "expected fields: " + ", ".join(sorted(fields)))


def feedback_json(raw, field):
    def pairs(items):
        result = {}
        for key, value in items:
            feedback_require(key not in result, field, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise FeedbackRefusal(field, "nonfinite JSON value: " + value)
    def number(value):
        import math
        parsed = float(value)
        feedback_require(math.isfinite(parsed), field, "nonfinite JSON number")
        return parsed
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)
    except (ValueError, UnicodeError) as error:
        if isinstance(error, FeedbackRefusal):
            raise
        raise FeedbackRefusal(field, str(error)) from error


def feedback_bytes(ref, field):
    feedback_object(ref, {"path", "sha256"}, field)
    feedback_require(isinstance(ref["path"], str) and Path(ref["path"]).is_absolute(),
                     field + ".path", "expected absolute file path")
    feedback_require(isinstance(ref["sha256"], str)
                     and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]),
                     field + ".sha256", "expected SHA-256")
    try:
        raw = Path(ref["path"]).read_bytes()
    except FileNotFoundError as error:
        raise FeedbackRefusal(field, "selected file is missing", "INCONCLUSIVE") from error
    except (OSError, ValueError) as error:
        raise FeedbackRefusal(field, str(error)) from error
    feedback_require(hashlib.sha256(raw).hexdigest() == ref["sha256"], field, "file digest mismatch")
    return raw


def feedback_input(selection, selected, instructions, cases):
    passed = {case["id"] for case in cases if case["status"] == "passed"}
    draft = {**selection, "observations": [item for item in selection["observations"]
                                          if item["case_id"] in passed]}
    requests = [{"case_id": name, "input": case["input"],
                 "report_identity": {"schema": 1, "case_id": name,
                                     "instructions": instructions,
                                     "input_sha256": case["input"]["sha256"]},
                 "required_output_fields": list(case["expected"])}
                for name, case in selected.items() if name not in passed]
    return {"selection": draft, "requests": requests}


def pclass_feedback(selection_path, expected_sha256):
    """Evaluate selected consumer reports. Never run an evaluator or infer effects."""
    started = time.perf_counter()
    result = {"schema": 1, "owner": "schema-manager.pclass-feedback",
              "observation_scope": "consumer_report", "evidence_validity": "INCONCLUSIVE",
              "behavior": None, "authorizes_landing": False, "effects": [],
              "test_demand": None, "selection_sha256": expected_sha256,
              "sources": [], "cases": [], "dag": {},
              "limits": ["File digests bind bytes, not observer independence or complete capture.",
                         "Field equality checks reported behavior, not unobserved effects.",
                         "No formal writing compliance or comparative improvement is established."]}
    try:
        selection = feedback_json(feedback_bytes(
            {"path": str(selection_path), "sha256": expected_sha256}, "selection"), "selection")
        version = selection.get("schema") if isinstance(selection, dict) else None
        selection_fields = {"schema", "protocol", "observations"}
        if version == 2:
            selection_fields.add("criteria_review")
        feedback_object(selection, selection_fields, "selection")
        feedback_require(type(version) is int and version in (1, 2),
                         "selection.schema", "unsupported schema")
        protocol = feedback_json(feedback_bytes(selection["protocol"], "protocol"), "protocol")
        protocol_fields = {"schema", "subject", "instructions", "methods", "cases"}
        if version == 2:
            protocol_fields.add("requirements")
        feedback_object(protocol, protocol_fields, "protocol")
        feedback_require(type(protocol["schema"]) is int and protocol["schema"] == version,
                         "protocol.schema", "unsupported schema")
        feedback_require(isinstance(protocol["subject"], str) and protocol["subject"].strip(),
                         "protocol.subject", "expected named behavior claim")
        result["subject"] = protocol["subject"]
        result["protocol"] = selection["protocol"]
        result["instructions"] = protocol["instructions"]
        result["sources"].append(selection["protocol"])
        for field in ("instructions", "methods"):
            refs = protocol[field]
            feedback_require(type(refs) is list and bool(refs), "protocol." + field, "expected selected files")
            paths = set()
            for ref in refs:
                feedback_bytes(ref, "protocol." + field)
                path = str(Path(ref["path"]).resolve())
                feedback_require(path not in paths, "protocol." + field, "duplicate file")
                paths.add(path)
                result["sources"].append(ref)
        instructions = {ref["path"]: ref["sha256"] for ref in protocol["instructions"]}
        result["dag"]["instructions"] = {"status": "ready", "requires": []}
        cases = protocol["cases"]
        feedback_require(type(cases) is list and bool(cases), "protocol.cases", "expected selected cases")
        selected = {}
        for case in cases:
            feedback_object(case, {"id", "input", "expected"}, "protocol.case")
            name = case["id"]
            feedback_require(isinstance(name, str) and re.fullmatch(r"[a-zA-Z0-9_-]+", name)
                             and name not in selected, "protocol.case.id", "expected unique case ID")
            feedback_require(type(case["expected"]) is dict and bool(case["expected"]),
                             "protocol.case.expected", "expected nonempty output field predicates")
            feedback_bytes(case["input"], "protocol.case.input")
            result["sources"].append(case["input"])
            selected[name] = case
        result["case_fingerprints"] = {
            name: hashlib.sha256(json.dumps({"instructions": protocol["instructions"],
                "methods": protocol["methods"], "requirements": protocol.get("requirements"),
                "case": case}, sort_keys=True).encode()).hexdigest()
            for name, case in selected.items()}
        result["criteria"] = {"status": "NOT_REVIEWED", "scope": "legacy field comparison"}
        if version == 2:
            result["requirements"] = protocol["requirements"]
            result["criteria"] = review_criteria(protocol, selection, selected)
            result["sources"].append(protocol["requirements"])
            if selection["criteria_review"] is not None:
                result["sources"].append(selection["criteria_review"])
            if result["criteria"]["status"] != "SUPPORTED":
                result.update(evidence_validity="VALID", status="criteria_pending",
                    next={"owner": "review-writing", "operation": "review_criteria",
                          "required": result["criteria"]["required"], "argv": None, "input": None})
                result["dag"]["criteria"] = {"status": "unknown", "requires": ["requirements", "criteria_review"]}
                result["dag"]["feedback"] = {"status": "unknown", "requires": ["criteria"]}
                result["elapsed_ms"] = (time.perf_counter() - started) * 1000
                return result
            result["dag"]["criteria"] = {"status": "ready", "requires": ["requirements", "criteria_review"]}
        observations = selection["observations"]
        feedback_require(type(observations) is list, "observations", "expected list")
        observed = {}
        for observation in observations:
            feedback_object(observation, {"case_id", "report", "trace"}, "observation")
            name = observation["case_id"]
            feedback_require(isinstance(name, str) and name in selected and name not in observed,
                             "observation.case_id", "duplicate or unselected case")
            feedback_require(bool(feedback_bytes(observation["trace"], "observation.trace")),
                             "observation.trace", "capture is empty", "INCONCLUSIVE")
            report = feedback_json(feedback_bytes(observation["report"], "observation.report"), "report")
            feedback_object(report, {"schema", "case_id", "instructions", "input_sha256", "output"}, "report")
            feedback_require(type(report["schema"]) is int and report["schema"] == 1,
                             "report.schema", "unsupported schema")
            feedback_require(report["case_id"] == name and report["instructions"] == instructions
                             and report["input_sha256"] == selected[name]["input"]["sha256"],
                             "report.identity", "case, instruction or input identity mismatch")
            feedback_require(type(report["output"]) is dict, "report.output", "expected object")
            observed[name] = report["output"]
            result["sources"].extend((observation["report"], observation["trace"]))
        projection_started = time.perf_counter()
        missing, failed = [], []
        for name, case in selected.items():
            output = observed.get(name, {})
            checks = {}
            for key, expected in case["expected"].items():
                checks[key] = (None if key not in output else
                               json.dumps(output[key], sort_keys=True) == json.dumps(expected, sort_keys=True))
                if checks[key] is None:
                    missing.append(name + ".output." + key)
                elif checks[key] is False:
                    failed.append(name + ".output." + key)
            status = "unknown" if any(v is None for v in checks.values()) else "failed" if not all(checks.values()) else "passed"
            result["cases"].append({"id": name, "status": status, "checks": checks,
                                    "observed": output if name in observed else None})
            result["dag"]["case:" + name] = {"status": status, "requires": ["instructions"] + (["criteria"] if version == 2 else [])}
        result["evidence_validity"] = "INCONCLUSIVE" if missing else "VALID"
        if not missing:
            result["behavior"] = {"classification": "FAIL" if failed else "PASS", "barriers": failed}
        operation = "supply_behavior_evidence" if missing else "correct_pclass" if failed else "consume_verified_behavior"
        result["next"] = {"owner": "evals" if missing else "review-writing" if failed else "task-owner",
                          "operation": operation, "required": missing or failed, "argv": None,
                          "input": feedback_input(selection, selected, instructions, result["cases"])
                              if missing else None}
        result["dag"]["feedback"] = {"status": "unknown" if missing else "failed" if failed else "ready",
                                      "requires": ["case:" + name for name in selected]}
        result["projection_ms"] = (time.perf_counter() - projection_started) * 1000
    except FeedbackRefusal as error:
        result["evidence_validity"] = error.validity
        result["behavior"] = None
        result["problem"] = {"field": error.field, "reason": error.reason}
        result["next"] = {"owner": "supervisor", "operation": "supply_bound_evidence",
                          "required": [error.field], "argv": None, "input": None}
        result["dag"]["feedback"] = {"status": "unknown" if error.validity == "INCONCLUSIVE" else "invalid",
                                      "requires": [error.field]}
    result["status"] = ("inconclusive" if result["evidence_validity"] == "INCONCLUSIVE" else
                        "refused" if result["evidence_validity"] == "INVALID" else
                        "passed" if result["behavior"]["classification"] == "PASS" else "failed")
    result["elapsed_ms"] = (time.perf_counter() - started) * 1000
    return result


def project_feedback_scope(result, scope, reusable_observations):
    """Expose the manager's evidence plan without treating reuse as a verdict."""
    evidence = {"observe": scope["cases"], "reuse": reusable_observations,
                "verified": scope["verified"]}
    pending = scope["cases"] + scope["reuse"]
    dag = {**result["dag"], "verification": {
        "status": "unknown" if pending or result["criteria"]["status"] != "SUPPORTED" else "ready",
        "requires": ["case:" + name for name in pending] or ["criteria"]}}
    next_action = {**result["next"], "evidence": evidence}
    if next_action["operation"] == "supply_behavior_evidence":
        current_input = next_action["input"]
        draft = current_input["selection"]
        observations = {item["case_id"]: item for item in reusable_observations}
        observations.update({item["case_id"]: item for item in draft["observations"]})
        next_action["input"] = {
            "selection": {**draft, "observations": list(observations.values())},
            "requests": [item for item in current_input["requests"]
                         if item["case_id"] not in observations]}
    return {**result, "dag": dag, "next": next_action}


def project_feedback_history(result, failed_attempts):
    """Expose the existing owner's failure history and its required reassessment."""
    result = {**result, "failed_attempts": failed_attempts}
    if failed_attempts >= 3 and (result.get("criteria", {}).get("status") == "REVISION_REQUIRED"
            or (result.get("behavior") or {}).get("classification") == "FAIL"):
        result["next"] = {"owner": "review-writing", "operation": "reassess_cause",
                          "required": ["root_cause_review_with_original_requirements"],
                          "argv": None, "input": None}
    return result


def review_criteria(protocol, selection, cases):
    """Validate scoped reasoning evidence; do not certify its semantic truth."""
    try:
        requirements = feedback_bytes(protocol["requirements"], "protocol.requirements").decode("utf-8")
    except UnicodeError as error:
        raise FeedbackRefusal("protocol.requirements", "expected UTF-8 requirements") from error
    ref = selection["criteria_review"]
    if ref is None:
        return {"status": "UNKNOWN", "required": ["criteria_review"]}
    review = feedback_json(feedback_bytes(ref, "criteria_review"), "criteria_review")
    feedback_object(review, {"schema", "protocol_sha256", "reviewer", "checks"}, "criteria_review")
    feedback_require(type(review["schema"]) is int and review["schema"] == 1
                     and review["protocol_sha256"] == selection["protocol"]["sha256"],
                     "criteria_review.protocol", "review must bind the selected protocol")
    feedback_require(isinstance(review["reviewer"], str) and review["reviewer"].strip(),
                     "criteria_review.reviewer", "name the actual reviewing Agent or observer")
    feedback_object(review["checks"], cases, "criteria_review.checks")
    required, unsupported = [], []
    for name, case in cases.items():
        feedback_object(review["checks"][name], case["expected"], "criteria_review." + name)
        for field, check in review["checks"][name].items():
            key = name + "." + field
            feedback_object(check, {"status", "requirement_quote", "reason"}, "criteria_review." + key)
            feedback_require(check["status"] in ("supported", "unsupported", "unknown")
                and isinstance(check["reason"], str) and check["reason"].strip()
                and isinstance(check["requirement_quote"], str),
                "criteria_review." + key, "supply status, requirement quote, and reasoning")
            if check["status"] == "supported":
                feedback_require(bool(check["requirement_quote"].strip())
                    and check["requirement_quote"] in requirements,
                    "criteria_review." + key, "supported condition needs an exact requirement quote")
            else:
                required.append(key)
                if check["status"] == "unsupported":
                    unsupported.append(key)
    return {"status": "REVISION_REQUIRED" if unsupported else "UNKNOWN" if required else "SUPPORTED",
            "required": required, "reviewer": review["reviewer"], "source": ref,
            "requirements": protocol["requirements"],
            "limits": "Agent reasoning bound to requirements; not independent authority or universal correctness."}
