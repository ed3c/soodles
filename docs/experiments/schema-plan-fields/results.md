# Host finalization field evidence

Issue: ed3c/soodles#217. This evidence covers the admitted first U1 slice and grants no landing authority.

All nine existing host facts now have a fixed producer/readback/consumer catalog. Normal owner output derives its diagnostic from the existing record and retains the original continuation. An absent landing readback is represented as unknown rather than false. Existing stop, restore, confirm and complete rules match the admitted baseline exactly.

One Test Manager round passed 198 controls across 12 selected modules in 43.837 seconds. The raw command, stdout, stderr, source hashes and case/module timing records are in [results.json](results.json). The run includes an actual issue_atom.run response through finish_host, temporary configuration restoration and planted unknown-effect, stale-evidence, identity and producer failures. Provider and process observations use the existing small fixtures; this is not production execution.

The [timing receipt](timing.json) contains the reproducible Python observation, event templates, selected plan/source hashes and 1000 raw perf_counter_ns samples after 100 warmups on darwin_arm64. Each operation applies a deterministic valid event and projects the result. p50 was 0.025792 ms, p95 0.026583 ms and max 0.051125 ms; the frozen p95 target was 10 ms. Separate cold compilation took 87.989 ms. CLI startup, event construction, serialization and disk/Git/network/process validation are excluded. This observation is not a recurring gate.

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
| R09 | covered | One changed candidate verification round through Test Manager: 12 selected modules, 198 controls, no full-suite request, evals or model agents. CI continues to consume the same boundary map. See `results.json` coverage. |
| R10 | partial | Actual host owner responses expose plan identity, producers, P context, DAG and unknown inputs beside existing next. No complete runtime/budget/provider view or model-behavior measurement is claimed. See `results.json` coverage. |
| R11 | covered | The frozen native hot-operation observation is recorded with 100 warmups, 1000 raw samples and separate cold compilation. This is not a recurring gate or production end-to-end measurement. See `results.json` coverage. |
| R12 | partial | Candidate retains Noodle ownership and original effects. Exact-head Linux Actions, publication, external landing and original live host reconciliation are pending outside candidate authority. See `results.json` coverage. |

U1 remains partial overall. U2 and U3 are not addressed. U4 has this local observation only. Exact-head Linux Actions, PR publication, external landing and original Noodle/host reconciliation remain with their existing owners. No Agent comparison or eval was requested or run.
