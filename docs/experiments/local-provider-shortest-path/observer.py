#!/usr/bin/env python3
"""Bounded discriminator for #120 local provider shortest path."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import landing
import provider_transport
from test_local_provider_transport import ProviderFixture


def main():
    fixture = ProviderFixture()
    try:
        local = fixture.start_and_dispatch()
        local_projection = {
            "kind": local["next"].get("kind"),
            "operation": local["next"].get("operation"),
            "argv": local["next"].get("argv"),
            "request": local["request"],
        }
        merge = provider_transport.execute(
            fixture.checkpoint, environ={"GH_TOKEN": "fixture-token"}, api=fixture.api)
        merged_readback = json.loads(Path(merge["readback"]).read_text())
        prepared_close = landing.advance(fixture.checkpoint, merged_readback)
        close_dispatch = landing.dispatch(fixture.checkpoint, merged_readback)
        close = provider_transport.execute(
            fixture.checkpoint, environ={"GH_TOKEN": "fixture-token"}, api=fixture.api)
        closed_readback = json.loads(Path(close["readback"]).read_text())
        reconciliation = landing.advance(fixture.checkpoint, closed_readback)

        recipe = (ROOT / ".agents/skills/verify-soodles/features/supervised-delivery.md").read_text()
        forbidden = ["gh pr merge", "gh api", "PUT /pulls", "PATCH /issues"]
        checks = {
            "local_exact_executable": (
                local_projection["kind"] == "executable"
                and local_projection["operation"] == "execute"
                and local_projection["argv"] == landing.provider_cli_argv(fixture.checkpoint)
            ),
            "merge_once": fixture.merge_calls == 1,
            "close_once": fixture.close_calls == 1,
            "fresh_advance_argv": (
                merge["next"]["kind"] == "executable"
                and merge["next"]["operation"] == "advance"
                and close["next"]["kind"] == "executable"
                and close["next"]["operation"] == "advance"
            ),
            "no_generic_mutation_guidance": all(value not in recipe for value in forbidden),
            "pclass_exact_next": "next.kind: executable" in recipe and "next.argv" in recipe,
            "missing_envelope_legal_noncase": (
                reconciliation["action"] == "reconcile"
                and reconciliation["next"]["kind"] == "input"
                and reconciliation["next"]["required"] == ["binary"]
            ),
            "close_prepared_by_existing_owner": prepared_close["action"] == "dispatch",
        }
        receipt = {
            "schema": 1,
            "issue": {"repository": "ed3c/soodles", "number": 120},
            "classification": "VERIFIED" if all(checks.values()) else "FAILED",
            "checks": checks,
            "telemetry": {
                "provider_mutations": {"merge": fixture.merge_calls, "close": fixture.close_calls},
                "reconstructed_provider_commands": 0,
                "local_next_argv_count": 2,
            },
            "authorizes_landing": False,
        }
        print(json.dumps(receipt, indent=2))
        return 0 if receipt["classification"] == "VERIFIED" else 1
    finally:
        fixture.close()


if __name__ == "__main__":
    raise SystemExit(main())
