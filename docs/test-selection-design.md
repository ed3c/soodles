# On-demand Test Manager

The user requires one owner for testing scope. That owner selects only the controls
needed now. It never predicts or defaults to a full-suite run. This document is
N-class rationale, not test evidence. The Test Manager skill owns P-class guidance;
`test_manager.py` resolves requests and executes unit tests. Canonical acceptance
executes its named physical controls. Other skills, CLI and CI consume that result.

## Ground and decision

The former flow scattered scope across the selector, a no-base acceptance default,
CI's missing-base fallback, and the order-handoff recipe. Even after narrowing CI,
those other callers could still force full coverage. Treating shared or unknown
paths as full also turned missing analysis into runtime cost.

The actual call chain suggested two designs. One kept separate defaults with more
exceptions. The other moved decisions and unit execution into one manager.
The manager was selected to remove policy leakage. It replaces `test_selection.py`
rather than adding another layer. CLI argument parsing remains in `soodles.py` so
non-test commands and existing external publisher bundles need no manager import.

The API is `plan(root, base, full=False, modules=(), controls=(), reason=None)`.
It returns ready/needs_scope, focused/full/none, the exact base and changed paths.
It also returns named controls, reasons and unresolved inputs. `execute_units` refuses unresolved scope. Only
an explicit full request selects full. Otherwise existing traced boundaries select
local controls. For unknown inputs or removed tests, the current Agent must analyze the impact.
For a missing canonical base, use the admitted provider readback.
No extra scheduler, report gate, policy file or human relay is introduced.

On-demand verification of unchanged behavior uses named modules/physical controls
with a reason. In particular order-handoff requests only `order_handoff`, including
its necessary runtime admission. A shared filename alone neither proves broad
impact nor licenses full coverage. When observed callers or requirements establish a different reusable boundary,
update the existing map. Do not encode a guessed future regression.
Do not request full coverage merely to remove a scope refusal.

Native publication schema 2 checks source custody and CLI capabilities, leaving
regressions to manager-selected exact-head CI. Existing schema-1 receipts retain
their original validation. Scope changes do not replace the external landing judge
or prove provider merge/closure and local reconciliation.

## Method and evidence limits

This work applied Noodle's pstack `architect` method. It traced callers and ownership,
compared designs and removed duplicated policy decisions. Provider source commit:
`68836ddaf5697224520f1847d90cdb90ca8babaa`; local skill:
`/Users/neon/noodles/.noodle/providers/cursor-pstack/pstack/skills/architect/SKILL.md`.
The user's no-test/no-experiment instruction overrides multi-model trials here.
No arena, benchmark or runtime correctness result is claimed. Normal selection
and timing logs are the inputs for subsequent cost comparisons.

## Issue 201 static delivery review

The admitted prepared-v2 patch has SHA-256
`591f47a2171aa5a875a04fb9995283dd4502729c57691369450dcc29de7f5f9c`
and applies to base `d4897583eea4a490bbfa45b40187cbf7e812690a`.
Static review found one stale evaluator in `tests/test_admission.py`: it still
called acceptance without scope and asserted automatic full discovery with a
600-second timeout. The new manager refuses missing scope before that path.
This is a source-level incompatibility, not an executed failure reproduction.

Method: installed `eval-audit/SKILL.md`, SHA-256
`c11338900d88d114c353a8865d9b7a4780d972bf740b80d5eb4e38357b1bf133`,
adapted to deterministic repository controls. The evaluator review found that the old assertion measured retired behavior.
Replace that assertion with the successful selected-unit-to-physical boundary. The adjacent failure control
and `test_test_suite` retain failed, empty, skipped and incomplete execution
checks. Judge calibration, human labels and subjective scoring are inapplicable.
Error analysis is limited to the actual source diff; no fresh runtime traces
or Agent comparison were collected. Product and Agent behavior remain
INCONCLUSIVE in this local stage. The admitted no-test/no-experiment task leaves
selected execution to exact-head Actions and makes no Agent improvement claim.
No further instruction or runtime-owner change was needed for this stale test.
