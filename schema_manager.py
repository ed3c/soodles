"""Fixed host-finalization decisions. The atom alone owns evidence and effects."""
import ast
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import re
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


def compile_plan(root):
    root = Path(root)
    raw = (root / PLAN_PATH).read_bytes()
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
        source = ast.parse((root / "issue_atom.py").read_text())
        owner = next((n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "finish_host"), None)
        require(owner is not None, "catalog.producer:issue_atom.py:finish_host")
        require(any(isinstance(n, ast.FunctionDef) and n.name == "confirm" for n in owner.body),
                "catalog.producer:issue_atom.py:finish_host.confirm")
    context = compile_repair(root)["cleanup_residue"]
    require(context["consumer"] == "issue_atom.finish_host", "consumer")
    names = ["schema_manager.py", PLAN_PATH, "issue_atom.py", "system_context.py",
             "atom_repair.py", "policy/repair-policy.json", "contracts/system-v1/routes.json"]
    names += context["requires"]
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
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


def project_cost(facts, gate=None):
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
    return {"status": "observed", "subject": facts["subject"],
            "coverage": facts["coverage"], "cost": facts["summary"],
            "hard_gate": gate, "required": gate.get("required"),
            "budget_basis": gate.get("basis"),
            "authorizes_landing": False, "effects": [], "test_demand": None}
