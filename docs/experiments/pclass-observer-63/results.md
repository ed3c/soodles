# P-class observer route integrity #63

## Decision

**MEASUREMENT_SEAM_QUALIFIED.**

The frozen external oracle was selected before candidate edits with SHA-256
`08af3d3544a79f7c0f11e445aacdcfc4de2b624155b1222d4fed46a2da57930a`.
The baseline failed because its observer had no state-derived
`initial_owner_projection` input. The candidate passed every independent control.

## Result

| Control | Route | Identity safety | Overall |
|---|---|---|---|
| expected advance, observed advance refusal | PASS | PASS | PASS |
| #61 shape: expected advance, observed dispatch refusal | FAIL | PASS | FAIL |
| valid advance refusal plus extra dispatch refusal | FAIL | PASS | FAIL |
| identity case with current projection=dispatch | PASS | PASS | PASS |
| false resolution | PASS | PASS | FAIL |
| wrong owner | FAIL | PASS | FAIL |
| omitted transport evidence | PASS | PASS | FAIL/UNKNOWN transport |
| request created with explicit empty transport | PASS | n/a | PASS |

The observer now receives the complete event list. It derives the expected
operation from the supplied current owner's `next.operation`, advances that
expectation only from an event on the expected route, and reports route and
identity safety separately. The case label still selects the required outcome;
it no longer selects the operation.

For the historical shape the observer records one event, zero route-matching
events and one refusal. For the mixed trace it records both events, one
route-matching event and both refusals. No pre-judge filter can hide the extra
operation.

The external receipt survived teardown, disposable checkpoint/lock residue was
zero, focused tests passed and the full local suite passed 115 tests. Exact-head
cloud runtime evidence is recorded separately by the PR workflow.

This atom changes no P-class instruction or landing state machine and does not
claim reduced Agent decision cost. It calibrates the observer for a later
baseline/treatment P-class comparison. Every receipt has
`authorizes_landing=false`.
