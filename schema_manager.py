"""Fixed host-finalization decisions. The atom alone owns evidence and effects."""
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

    def validate_sources(self, root):
        for name, expected in self.sources.items():
            require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected,
                    "source_changed:" + name)


def compile_plan(root):
    root = Path(root)
    raw = (root / PLAN_PATH).read_bytes()
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(value == {"schema": 1, "owner": "issue_atom",
                      "context": "cleanup_residue", "facts": list(FACTS), "nodes": RULES}, "plan")
    require(type(value["schema"]) is int and all(type(v) is bool
            for rule in value["nodes"].values() for v in rule.values()), "plan_types")
    context = compile_repair(root)["cleanup_residue"]
    require(context["consumer"] == "issue_atom.finish_host", "consumer")
    names = ["schema_manager.py", PLAN_PATH, "issue_atom.py", "system_context.py",
             "atom_repair.py", "policy/repair-policy.json", "contracts/system-v1/routes.json"]
    names += context["requires"]
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
    return Plan(digest(sources), context, sources, value["nodes"],
                {fact: tuple(node for node, rule in RULES.items() if fact in rule) for fact in FACTS})


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
            self.validate_facts(record["facts"])
            self.sequence = record["sequence"]
            self.facts = {k: dict(v) for k, v in record["facts"].items()}
        self.ready = {node: self.evaluate(node) for node in plan.rules}

    @staticmethod
    def validate_facts(facts):
        require(isinstance(facts, dict) and set(facts) <= set(FACTS), "facts")
        for name, fact in facts.items():
            require(isinstance(fact, dict) and set(fact) == {"value", "evidence"}
                    and type(fact["value"]) is bool and isinstance(fact["evidence"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", fact["evidence"]), "fact:" + name)
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
                "authorizes_landing": False}


def project_cost(facts, gate=None):
    """Data-only observation projection; original owners retain every hard gate."""
    require(isinstance(facts, dict) and set(facts) == {"subject", "coverage", "summary", "sources"},
            "cost_facts")
    # Finite numeric evidence was normalized before entry. Recheck at this public
    # boundary so a direct caller cannot silently introduce NaN or negative cost.
    import math
    for key, value in facts["summary"].items():
        if type(value) in (int, float):
            require(math.isfinite(value) and value >= 0, "cost_number:" + key)
    gate = gate or {"status": "unknown", "basis": "original owner evidence unavailable"}
    return {"status": "observed", "subject": facts["subject"],
            "coverage": facts["coverage"], "cost": facts["summary"],
            "hard_gate": gate, "required": gate.get("required"),
            "budget_basis": gate.get("basis"),
            "authorizes_landing": False, "effects": [], "test_demand": None}
