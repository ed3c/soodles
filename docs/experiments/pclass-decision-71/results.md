# Executable P-class comparison decision #71

## Decision

**PRIORITIZE THE P-CLASS GATE, BUT NOT AS A PURE GOVERNANCE ISSUE.**

The missing reusable boundary was not another behavior inventory or quality
measurement policy. `observe_pclass.py` already normalizes one run, but #67 and
#69 each needed an experiment-local aggregator to decide whether equal green
arms meant nonregression, whether a lower barrier meant improvement, and
whether telemetry could affect admission.

Issue #71 adds `decide_pclass.py`, a non-authorizing local discriminator over
already-normalized receipts. It does not observe behavior, replace the owner or
observer, create provider requests, or turn quality telemetry into correctness.

## Replayed accepted evidence

| Existing experiment | Declared target | Baseline wrong routes | Treatment wrong routes | Decision |
|---|---|---:|---:|---|
| #69 guidance deletion | nonregression | 0 | 0 | `ADMIT_NONREGRESSION` |
| #67 packet comparison | improvement | 0 | 0 | `REJECT` — `primary_barrier_not_improved` |

This preserves both original claims. #69 may retain a duplicate deletion under
scoped nonregression. #67 cannot be relabelled as a behavioral improvement just
because the treatment packet was qualified or its telemetry differed.

The replay packets and exact decision receipts are under `raw/`. They bind the
six run gates, four sensitivity controls, causal-delta disposition, blind audit
and primary barrier. Telemetry is retained verbatim with
`telemetry_authority=report_only`.

## Planted discrimination

| Control | Expected | Observed |
|---|---|---|
| Equal green arms, nonregression target | Admit scoped nonregression | `ADMIT_NONREGRESSION` |
| Equal green arms, improvement target | Reject improvement claim | `REJECT` |
| Barrier 1 → 0, all gates green | Admit improvement | `ADMIT_IMPROVEMENT` |
| Treatment hard gate fails while elapsed/bytes improve | Reject | `REJECT` |
| Missing or mismatched sensitivity control | Reject | `REJECT` |
| Telemetry worsens while behavior remains nonregressed | Keep telemetry report-only | `ADMIT_NONREGRESSION` |
| Missing audit/causal delta/barrier count | Reject | `REJECT` |
| Negative, boolean, string or unknown barrier count | Reject | `REJECT` |

Eight focused decision tests and the existing eight P-class observer/recorder
tests pass. The candidate still requires full canonical acceptance and the
external landing owner; every decision receipt has `authorizes_landing=false`.

## Why the other governance Issues are not next

### Complete behavior enumeration

The feature recipe and `observe_pclass.py` already index the bounded
`pending`, `identity` and `recovery` cases. Runtime choice remains derived from
the real owner's current projection. A separate prose inventory would duplicate
that route and drift. Add a case only when an observed owner state lacks a
discriminator.

### SlopCodeBench pinning

The current quality path already pins `scb-check==0.1.3`,
`ast-grep-cli==0.42.1`, `tree-sitter==0.25.2`,
`tree-sitter-python==0.25.0`, bundled rule hashes, package versions, exact
base/head commits, scope classification and the measurement recipe hash.
`quality/measure.py` keeps the results report-only and carries planted analyzer
controls. Opening another pinning Issue without an observed measurement drift
would duplicate an existing boundary.

## Claim boundary

The new discriminator makes one policy executable: behavior gates and
sensitivity evidence decide admission; telemetry does not. It does not prove
that the upstream receipts are true, choose an intervention's admission target,
authorize landing, enumerate every future owner state, or convert structural
quality signals into merge gates.
