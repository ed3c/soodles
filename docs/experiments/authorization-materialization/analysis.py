#!/usr/bin/env python3
"""Aggregate fixed receipts without selecting judges or authorizing delivery."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rounds = []
for version in ("v2", "v3", "v4", "v5"):
    directory = ROOT / ("behavior-" + version)
    receipt_path = directory / "final-receipt.json"
    if not receipt_path.is_file():
        continue
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    decision = json.loads((directory / "decision.json").read_text())
    pairs = receipt.get("observed_counts", decision.get("pairs", []))
    counts = [{key: pair[key] for key in ("case", "kind", "baseline", "treatment") if key in pair}
              for pair in pairs]
    totals = None
    if counts and all(type(p.get("baseline")) is int and type(p.get("treatment")) is int for p in counts):
        totals = {arm: sum(p[arm] for p in counts) for arm in ("baseline", "treatment")}
    rounds.append({"version": version, "decision": receipt["decision"],
                   "adoption": receipt.get("adoption"), "counts": counts,
                   "within_round_totals": totals,
                   "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest()})
print(json.dumps({"rounds": rounds, "v1": "INCONCLUSIVE_UNCHANGED",
                  "scope": "Captured operations only; never compare scores across changed measurement setups.",
                  "authorizes_landing": False}, indent=2))
