# P-class ablation #59 — repaired-observer result

## Decision

**INCONCLUSIVE_HARD_GATES_FAILED_RESTORE_P_CLASS.**

The deletion is not authorized. Restore the target bullet in `AGENTS.md` and retain only this N-class report and receipts.

Baseline was `254db7776943a12181a507dee3499c959c3200c7`. Treatment commit `cfa9b03f7d50e82eca9294901a03d415a9059e3d` deleted exactly the one duplicated landing-guidance bullet. The executable owner, recorder, observer, fixtures, requested consumer model/config and task packets were fixed outside the treatment.

## Hard gates

| Case | Baseline PASS / runs | Treatment PASS / runs | Result |
|---|---:|---:|---|
| Pending | 0 / 3 | 0 / 3 | FAIL — consumers stopped before the required `landing.advance` observation |
| Foreign identity | 3 / 3 | 2 / 3 | FAIL — one treatment run left teardown residue |
| Recovery | 0 / 3 | 0 / 3 | FAIL — no run reached the required `close_pending` continuation |
| Total | 5 / 18 | — | 13 hard-gate failures |

All observed connector-event sets were explicitly empty; no live provider transport occurred. Fixed planted controls detected `false_resolution` and `wrong_owner`; omitted transport evidence remained `transport_evidence_unknown`.

Five runs retained checkpoint or lock residue despite consumer teardown claims: `i_t2`, `p_b1`, `p_t1`, `r_b2`, and `r_t2`. Evidence directories survived.

The recovery failure repeated in all three baseline and all three treatment runs: consumers applied merged readback without first completing the local landing dispatch that records the merge offer, so the owner correctly refused `merge.owner`. This is a stable task/decision barrier shared by both arms, not evidence that deletion is safe.

One baseline pending run (`p_b3`) was conservatively stopped after a coordinator reply to a recorder-path question even though a later positional invocation succeeded. It remains failed/incomplete; it is not repaired, excluded, or rerun.

## Blind audit

The auditor received normalized receipts without arm assignments. It reported 5 passes and 13 failures, `all_hard_gates_pass=false`, and `change_authorized=false`. The arm map was read only after that result was preserved. Instruction paths were a known possible identifying cue; the auditor reported that it did not infer or use arm identities.

## Independent decision telemetry

Values are retained per run in `normalized-receipts.json`; no composite score is calculated.

| Case / arm | Command counts | Recorded instruction reads | Elapsed seconds |
|---|---|---|---|
| Pending / baseline | 16, 18, 5 | 1, 2, 1 | 0.295, 0.224, 0.025 |
| Pending / treatment | 22, 17, 14 | 1, 1, 1 | 0.268, 0.231, 0.251 |
| Identity / baseline | 13, 17, 18 | 1, 1, 1 | 0.341, 0.486, 0.370 |
| Identity / treatment | 18, 17, 17 | 3, 1, 1 | 0.382, 0.357, 0.475 |
| Recovery / baseline | 26, 16, 20 | 2, 1, 1 | 0.439, 0.437, 0.285 |
| Recovery / treatment | 29, 13, 15 | 1, 1, 1 | 0.420, 0.402, 0.446 |

No case shows a decision-barrier reduction repeated across all three treatment runs. A treatment identity run added repeated instruction reads; a treatment pending run asked the coordinator for recorder syntax and stopped early. Requested model was `gpt-5.6-sol`; observed native model provenance, tokens, context-window occupancy, hidden reads and hidden reasoning were unavailable and remain unknown.

## Whole-repository quality boundary

The final candidate restores `AGENTS.md` and changes only N-class experiment documents. Existing PR quality automation compares exact base/head snapshots and reports SLOC, article/native V, complete-callable E, total/high complexity mass, rule/clone hits, changed callables, churn, scan time and provider runtime cost independently. Those metrics do not authorize deletion and are not averaged with behavior.

Because no tracked Python source is retained as changed, production/tests/oracles/tooling Python quality metrics should remain identical; the exact-head artifact is the authoritative observation. Non-Python documentation churn remains visible in Git numstat.

## Claim boundary

This result proves neither that the P-class bullet is necessary nor that it is removable. It proves the declared comparison did not satisfy its prospective gates. A future attempt needs a newly frozen task packet that makes local owner dispatch versus connector transport explicit without revealing expected case outcomes. It must not reuse these failed runs as favorable evidence.

All receipts have `authorizes_landing=false`. Exact-head runtime acceptance and the external landing owner remain separate delivery evidence.
