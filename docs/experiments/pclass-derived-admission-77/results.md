# Derived P-class admission — issue #77

This issue atom closes one real P-class comparison failure without rerunning the six issue #73 model consumers or adding an eval service. The public comparison entry now derives receipts and planted controls from fixed raw evidence; a candidate cannot submit those results directly.

## Preserved RED

At base commit `5463e7b212dcdd578e39f3cfc9e5c6da800ea541`, the frozen probe (`sha256:126f4724…2809c0e4`) demonstrated four failures:

- a changed baseline barrier value was admitted while its raw-evidence digest stayed unchanged;
- six `UNKNOWN → UNKNOWN` controls were admitted;
- an externally declared 3-baseline/1-treatment comparison was admitted as `3 → 1` improvement;
- a treatment owner operation after the exact completion projection retained a PASS hard gate.

## Fixed executable boundary

`manifest.json` fixes three runs per arm, all six raw run identities, observer/normalizer/decider bytes, the gates digest, and six mutation predicates. `gates.json` has an exact narrow schema: causal-delta PASS, independent-audit PASS, and report-only telemetry. Extra candidate receipt or control fields are rejected.

`replay_pclass.py` is the single command entry. It verifies digests before analyzer import, normalizes raw runs, executes the manifest-selected mutations, builds the comparison, and calls the internal evaluator. `decide_pclass.py` rejects command-line comparison input. Neither receipt authorizes landing.

## Replayed evidence

The final manifest is canonically bound by `sha256:7fa30e1d…20ea93b`. Replaying the committed #73 raw evidence produced:

| Evidence | Result |
| --- | --- |
| Baseline exposure | 3 runs; barrier `1, 1, 1`; all hard gates PASS |
| Treatment exposure | 3 runs; barrier `0, 0, 0`; all hard gates PASS |
| Planted controls | 6/6 predicates PASS, including request-after-completion RED and legal completion GREEN |
| Decision | `ADMIT_IMPROVEMENT`, totals `3 → 0` |
| Telemetry | report-only |

The black-box oracle (`sha256:b003c230…c6e460`) also rejects forged receipt fields, candidate-supplied controls, unbalanced exposure, and the old direct comparison entry. A fresh read-only consumer with no inherited conversation matched every pinned digest, the `3 → 0` result, all control predicates, and comparison hash `35dfcc7e…c78207` without discrepancy. The full repository suite passes 134 tests.

## Scope and next hill climb

This proves the bounded #73 comparison can be replayed from pinned evidence and that the four preserved failures are discriminated. It does not prove general P-class effectiveness or provider truth. Supervisor machinery helps by pinning the external manifest/gates/analyzer bytes and by retaining delivery authority; it does not calculate behavior receipts or turn this result into R-class evidence.

With this atom closed, the next P-class hill climb should return to the existing `verify-soodles` or `verify-noodle` feature map and preselect one fresh real-owner state with a non-zero observable barrier. A fresh `0 → 0` result supports only scoped nonregression, not new improvement guidance.
