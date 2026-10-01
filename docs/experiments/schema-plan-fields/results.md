# Host finalization field evidence

Issue: ed3c/soodles#217. This evidence covers the admitted first U1 slice and grants no landing authority.

All nine existing host facts now have a fixed producer/readback/consumer catalog. Normal owner output derives its diagnostic from the existing record and retains the original continuation. An absent landing readback is represented as unknown rather than false. Existing stop, restore, confirm and complete rules match the admitted baseline exactly.

The retained candidate `6fd13931a084196e66a46dc881cdd9ecaea8a14b` now includes the exact admitted base `f5df50628e5289788f4185fb9f10a8b15dd23c69`. Both the host field projection and the base's cost projection remain intact. The owner integration control checks that both projections refer to the same host record and preserve the original gate and repair budget.

Test Manager selected 13 affected modules and 218 controls. The first round passed 217 controls in 41.407 seconds. The new combined-output assertion exposed missing repository and session fields in the existing mocked publication claim. The fixture now supplies those identities and the provider run's repository and head. After this change, the 8 affected modules passed all 161 controls in 32.729 seconds. The remaining 57 controls retain their first-round pass. No product validation was loosened. [results.json](results.json) preserves both rounds, their source hashes, the failure diagnosis, raw output, and normal case/module timings.

The earlier candidate's 198-control run remains under `historical_evidence` with its original source hashes. It does not verify the integrated source. The protocol bytes remain unchanged, including the original base label. The manifest baseline hashes now refer to the admitted base.

The refreshed [timing receipt](timing.json) records 1000 raw perf_counter_ns samples after 100 warmups on darwin_arm64. Each operation applies a deterministic valid event and projects the result using a precompiled plan. p50 was 0.025166 ms, p95 0.026291 ms, and max 0.050792 ms, against the frozen p95 target of 10 ms. Separate cold compilation took 86.318 ms. CLI startup, event construction, serialization, and disk/Git/network/process validation are excluded. The original 1000 samples remain under `historical_evidence`. These observations are not recurring gates.

Producer keys cannot authenticate a success claim. Physical truth and effects remain with the original owner. Legacy observations retain their original record and expose missing producer metadata. Missing completion acknowledgement still requires current_noodle_owner_readback. No stopped-consumer recovery command is introduced.

| Requirement | Status | Evidence and remaining scope |
| --- | --- | --- |
| R01 | partial | Frozen protocol and source pins bind this local candidate. Live PR/provider admission and delivery remain external. See `results.json` coverage. |
| R02 | partial | All nine host facts are mapped and validated. Other runtime consumers, including landing/provider_readback, are not mapped here. See `results.json` coverage. |
| R03 | partial | Selected host consumer has the existing issue-atom run P closure and owner continuation. This does not provide a full runtime entry map. See `results.json` coverage. |
| R04 | partial | Existing subject/plan replay, source drift and explicit lifecycle resume remain checked. Legacy facts expose missing producer metadata. This does not solve every runtime checkpoint migration. See `results.json` coverage. |
| R05 | not addressed | No stopped-consumer recovery is implemented. Missing completion acknowledgement remains current_noodle_owner_readback; no recovery argv is offered. See `results.json` coverage. |
| R06 | covered | Within the selected host plan, changed facts update affected nodes; replay is idempotent, changed physical evidence invalidates confirmation, and unknown is distinct from false. Broader event consumers remain outside this slice. See `results.json` coverage. |
| R07 | not addressed | This candidate adds no repair signals or automatic recovery actions. Existing atom_repair behavior is retained. See `results.json` coverage. |
| R08 | not addressed | No shared-budget redesign or token telemetry is added. Host projection does not create or reset repair history. See `results.json` coverage. |
| R09 | covered | 13 affected modules cover 218 controls through one initial round and one scoped fixture repair. Raw failure and pass results remain separate. CI consumes the same boundary map; no full-suite request, evals, or model agents. See `results.json` coverage. |
| R10 | partial | Actual host owner responses expose plan identity, producers, P context, DAG and unknown inputs beside existing next. No complete runtime/budget/provider view or model-behavior measurement is claimed. See `results.json` coverage. |
| R11 | covered | The integrated source has one native observation with 100 warmups, 1000 raw samples, and separate cold compilation. Original samples remain historical. This is not a recurring gate or production end-to-end measurement. See `results.json` coverage. |
| R12 | partial | Candidate retains Noodle ownership and original effects. Exact-head Linux Actions, publication, external landing and original live host reconciliation are pending outside candidate authority. See `results.json` coverage. |

U1 remains partial overall. U2 and U3 are not addressed. U4 has this local observation only. Exact-head Linux Actions, PR publication, external landing and original Noodle/host reconciliation remain with their existing owners. No Agent comparison or eval was requested or run.
