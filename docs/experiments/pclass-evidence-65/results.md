# P-class evidence validity #65

## Decision

**BOUNDED_EVIDENCE_GATE_QUALIFIED.**

The candidate-independent oracle was frozen before edits with SHA-256
`cefbade8ec5ca65e4a5bf1a8fa9a3fd8c2579effb5a1d073359686fadeefd5b4`.
On base `d1a09f50fa38449dd7a00bc3ef207b77c03d3561`, the observer had no
projection-binding input and classified a foreign-identity refusal carrying a
new request as overall and identity-safety PASS.

The candidate requires the externally selected digest of the complete initial
owner projection. Its legal advance and dispatch controls use projections
returned by the real landing owner from offered and prepared checkpoints.

## Independent gates

| Control | Route | Identity safety | Overall |
|---|---|---|---|
| Real offered-state advance | PASS | PASS | PASS |
| Real prepared-state dispatch | PASS | PASS | PASS |
| Replaced projection with stale digest | FAIL | PASS | FAIL |
| Foreign refusal plus owner request | PASS | FAIL | FAIL |
| Omitted transport evidence | PASS | UNKNOWN | FAIL |
| Transport observed after refusal | PASS | FAIL | FAIL |
| #61 wrong route, no request or transport | FAIL | PASS | FAIL |

The projection digest detects replacement relative to an external selection; it
does not make caller-supplied bytes authoritative. The experiment coordinator
must select the projection from the real owner invocation before the consumer
acts.

Identity safety is now a conjunction: the required refusal is present, no owner
request was produced for that refused trace, and transport is explicitly
observed absent. Missing transport stays UNKNOWN. Route, identity safety and
transport remain separate observations, so a safe refusal does not hide a wrong
operation and a correct route does not hide an unsafe request.

Focused tests passed 8/8 and the full local suite passed 115/115. External
receipts are preserved under `raw/`. Every receipt has
`authorizes_landing=false`.

## Claim boundary

This qualifies the bounded observer predicate used by a later P-class
baseline/treatment experiment. It does not establish native trace completeness,
the trustworthiness of the external selector, reduced Agent decision cost,
general scheduling, Issue DAG behavior or A → cleanup → B automation.

Structural quality measurements remain independent telemetry. They may trigger
investigation but do not authorize this behavior claim or landing.

The first candidate added a third explicit refusal block to the existing long
integration test. That crossed the analyzer's `3+ try/except` threshold and
marked 135 test lines, moving the test union from 63 to 179. The controls were
kept and the repeated refusal capture was moved to one transparent test helper.
The final test union is 55. This is a threshold-cliff diagnosis, not evidence
that the first candidate was behaviorally wrong.

Final base-to-head telemetry under one pinned recipe:

| Scope | SLOC | High-CC mass | Total mass | Union lines |
|---|---:|---:|---:|---:|
| production | 0 | 0 | 0 | 0 |
| tests | +24 | 0 | -9.29 | -8 |
| unclassified | +35 | -15.55 | +39.38 | +7 |
| all Python | +59 | -15.55 | +30.10 | -1 |

In the observer, `evaluate()` moves from CC 15 / mass 96.05 to CC 12 /
mass 80.50. The new projection-binding and identity-safety functions remain
below the high-CC threshold. These values describe structure only.
