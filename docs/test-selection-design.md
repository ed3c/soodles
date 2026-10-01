# On-demand Test Manager

User requirement: testing scope has one owner, selects only presently necessary
controls, and never predicts or defaults to a full-suite run. This document is
N-class rationale, not test evidence. The Test Manager skill owns P-class guidance;
`test_manager.py` resolves requests and executes unit tests. Canonical acceptance
executes its named physical controls. Other skills, CLI and CI consume that result.

## Ground and decision

The former flow scattered scope across the selector, a no-base acceptance default,
CI's missing-base fallback, and the order-handoff recipe. Even after narrowing CI,
those other callers could still force full coverage. Treating shared or unknown
paths as full also turned missing analysis into runtime cost.

Two shapes were considered from the actual call chain: keep separate defaults
with more exceptions, or move decisions and unit execution into one manager.
The manager was selected to remove policy leakage. It replaces `test_selection.py`
rather than adding another layer. CLI argument parsing remains in `soodles.py` so
non-test commands and existing external publisher bundles need no manager import.

API: `plan(root, base, full=False, modules=(), controls=(), reason=None)` returns
ready/needs_scope, focused/full/none, exact base, changed paths, named controls,
reasons and unresolved inputs. `execute_units` refuses unresolved scope. Only
an explicit full request selects full. Otherwise existing traced boundaries select
local controls. Unknown inputs and removed tests require impact analysis by the
current Agent; missing canonical base requires the admitted provider readback.
No extra scheduler, report gate, policy file or human relay is introduced.

On-demand verification of unchanged behavior uses named modules/physical controls
with a reason. In particular order-handoff requests only `order_handoff`, including
its necessary runtime admission. A shared filename alone neither proves broad
impact nor licenses full coverage. Update the existing map when observed callers
or requirements establish a different reusable boundary; don't encode a guessed
future regression or request full merely to make scope refusal disappear.

Native publication schema 2 checks source custody and CLI capabilities, leaving
regressions to manager-selected exact-head CI. Existing schema-1 receipts retain
their original validation. Scope changes do not replace the external landing judge
or prove provider merge/closure and local reconciliation.

## Method and evidence limits

Applied Noodle's pstack `architect` method: trace callers/ownership, compare shapes,
and remove policy leakage. Provider source commit:
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
adapted to deterministic repository controls. Evaluator design and pipeline
hygiene findings: the old assertion measured retired behavior; replace it with
the successful selected-unit-to-physical boundary. The adjacent failure control
and `test_test_suite` retain failed, empty, skipped and incomplete execution
checks. Judge calibration, human labels and subjective scoring are inapplicable.
Error analysis is limited to the actual source diff; no fresh runtime traces
or Agent comparison were collected. Product and Agent behavior remain
INCONCLUSIVE in this local stage. The admitted no-test/no-experiment task leaves
selected execution to exact-head Actions and makes no Agent improvement claim.
No further instruction or runtime-owner change was needed for this stale test.
