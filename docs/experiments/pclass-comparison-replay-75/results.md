# P-class comparison completeness and replay — issue #75

This issue atom preserves the previously observed comparison failure and closes it with an executable discriminator. It does not rerun the six issue #73 model consumers.

## Preserved RED

The pre-change decision script (`sha256:90fe8285…8621a1f`) received three baseline receipts and one treatment receipt, each with barrier value `1`. It summed `3` versus `1` and returned `ADMIT_IMPROVEMENT`. The exact compact input is bound by `sha256:09423116…83cdf`; the result is summarized in `legacy-red.json`.

## Fixed experiment contract

`manifest.json` is canonically bound by `sha256:f7615036…a54ade1e`. It fixes:

- all six run IDs and their baseline/treatment arm plus recovery case;
- the canonical hash of each raw run object;
- `observe_pclass.py` at `sha256:7f9285d7…b1096123`;
- `replay_pclass.py` at `sha256:d7712523…f0cfeb10`;
- the exact six required sensitivity controls.

The decision entrypoint rejects any incomplete, duplicate, extra, or incorrectly bound evidence before comparing totals. Telemetry remains report-only, and every receipt remains non-authorizing.

## #73 replay

The executable replayer recomputed the completion projection from the owner events, verified projection/instruction/transport/evidence bindings, and counted owner requests after the exact completion event.

| Arm | Run barriers | Total | Hard gates |
|---|---:|---:|---|
| baseline | 1, 1, 1 | 3 | 3/3 PASS |
| treatment | 0, 0, 0 | 0 | 3/3 PASS |

The manifest-bound comparison returned `ADMIT_IMPROVEMENT` with six observed runs, six declared runs, and no hard-gate errors. This reproduces the issue #73 behavioral result from committed raw evidence; it does not confer landing authority.

## Planted discriminators

The frozen external oracle was created before the candidate edit (`sha256:f5a051d7…c3193`). Its six black-box cases pass: complete 3+3 improvement; complete 0→0 improvement rejection; incomplete 3-to-1 rejection; duplicate-run rejection; missing-control rejection; and evidence-binding rejection. Unit tests additionally cover extra runs, arm/case/analyzer/manifest binding, hard-gate failure, telemetry non-authority, missing audit/delta/barrier, invalid counts, raw evidence tampering, and analyzer digest mismatch.

A fresh read-only consumer independently recomputed the final frozen inputs and matched the replay receipt and decision exactly. During the pre-freeze revision it also detected that the earlier manifest/normalizer pair had changed; reusing the stale pin failed closed with manifest and normalizer mismatches. `independent-replay.json` preserves both that superseded discrepancy and the final no-discrepancy result.
