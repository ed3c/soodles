# Completion-bound P-class recovery #73

## Decision

**ADMIT_IMPROVEMENT for the bounded recovery packet.**

Six fresh consumers started from the same real owner state and used the same
instruction, owner package, missing/corrected merge-commit readbacks and
transport prohibition. The three treatment packets added only an externally
selected completion projection, its SHA-256 and an exact-match stopping flag.

The primary executable barrier was an owner `request` created after the
required recovery completion projection had already been observed. Fresh
baseline runs produced three such untransported close requests; treatment runs
produced none. The frozen #71 discriminator returned `ADMIT_IMPROVEMENT`:

| Arm | Hard gates | `post_completion_owner_request` |
|---|---:|---:|
| Baseline | 3 / 3 PASS | 3 |
| Treatment | 3 / 3 PASS | 0 |

This admits one narrow P-class rule in the existing feature recipe: a bounded
recovery packet may stop at an externally selected exact completion projection
before following its next operation when provider transport is unauthorized.
It does not make the projection provider truth or authorize landing.

## Frozen boundary

| Subject | Identity |
|---|---|
| Source and owner package | `08a8c4cb0f94e9d246dabb428ee1f538f93a8ca1` |
| Entry instruction | SHA-256 `18572ed1a66239858b0f646656d65d98e9d8d9d4d000535df4c03d44c24cc46f` |
| Frozen observer | SHA-256 `7f9285d7f4ab9ee8009dda80483ec5c7a3a61533201734fec0103785b1096123` |
| Frozen discriminator | SHA-256 `90fe8285e300706c6b47fb1d622a5455e4a7d47e5610b98069c84c9688621a1f` |
| Initial owner state | `merge_pending`, merge write `offered`, `next.operation=advance` |
| Recovery sequence | missing `merge_commit` refusal, then corrected continuation to `close_pending/action=dispatch` |
| Requested carrier | six independent `gpt-6-astra` consumers with no inherited conversation |
| Observed native model identity | UNKNOWN |

The coordinator selected each run's complete initial and completion owner
projections before the consumer acted. Both projections were bound by canonical
JSON SHA-256. The completion digest differs per run because the projection
contains the run-specific checkpoint path; causal comparison canonicalized that
path and its derived digest, not any behavior field.

## Executable discrimination

All planted controls matched their predeclared result:

| Control | Expected | Observed |
|---|---|---|
| Premature stop before completion | FAIL | FAIL |
| Wrong owner operation | FAIL | FAIL |
| Stale completion digest | FAIL | FAIL |
| Missing transport evidence | FAIL | FAIL |
| Request after treatment completion | FAIL | FAIL |
| Exact completion with no request | PASS | PASS |

The causal-delta gate found exactly three treatment-only fields:
`completion_owner_projection`,
`expected_completion_owner_projection_sha256`, and
`stop_when_completion_projection_observed`. No shared field changed after
run-path canonicalization.

A fresh blind auditor received randomized receipts, opaque group labels and no
arm map. It confirmed six unique green hard gates, all six planted controls,
group barrier totals `3` and `0`, exact causal isolation, surviving evidence and
zero final residue. Only then did the #71 discriminator change from `REJECT`
(`independent_audit_not_pass`) to `ADMIT_IMPROVEMENT`.

## Independent telemetry

Telemetry was copied into the decision packet with
`telemetry_authority=report_only`; it did not affect admission.

| Arm | Commands | Captured elapsed seconds | Instruction reads | Owner events | Owner requests |
|---|---:|---:|---:|---:|---:|
| Baseline | 41 | 0.880 | 4 | 9 | 3 |
| Treatment | 37 | 0.823 | 4 | 6 | 0 |

Captured elapsed time covers recorded subprocesses, not complete Agent wall
time. Requested versus observed model identity, token counts, context occupancy,
hidden reads, hidden reasoning and compaction remain UNKNOWN.

## Cleanup observation

Every consumer attempted exact checkpoint/lock teardown. During parallel
shared-filesystem updates, three checkpoint pairs later reappeared even though
their consumers had observed successful deletion. The discrepancy is retained.
After all consumers stopped, the coordinator removed only the twelve
packet-declared paths and verified zero final residue while all evidence and
consumer receipts survived. This proves final cleanup, not transactional
isolation of concurrent teardown.

## Claim boundary

This atom demonstrates a lower observable decision barrier for one recovery
packet: baseline `3` to treatment `0`, with current behavior, sensitivity,
causal-delta and independent-audit gates intact. It does not enumerate all
P-class behavior, change the landing owner, prove provider transport safety
outside the explicit empty fixture, or turn command/time telemetry into a merge
gate.

The raw runs, normalized receipts, controls, causal comparison, discriminator
receipt, blind audit, unblind map and coordinator cleanup receipt are retained
under `raw/`. Every receipt has `authorizes_landing=false`.
