# Issue 39: operator handoff for independent cloud trials

Current status: see [recovered evidence and supplemental handoff](recovery-results.md). Round2 raw archive recovery and a new recorded handoff are complete; native capture/model gate remains incomplete. Earlier chronology below is retained.

## Latest bounded continuation

[Durable supervisor observation receipt and independent reviewer message](https://github.com/ed3c/soodles/tree/49f4c0ef16887535656d757ca53cbb31e41e043d/docs/experiments/agent-context/native-round2). Four fresh consumers actually invoked the existing owner on mutable disposable checkpoints: exit 0, readback, merge_pending, no new request. Supervisor and independent reviewer checked before/after bytes; all match digest e3881548ceababec1070e2509ead654f58249ce69a9c6bd6d4388143a17a14ed and preserve writes_offered=[merge]. All four live checkpoint paths were removed. The mutable-checkpoint evidence gap is now addressed within this fixture scope.

Two new consumers received no prescribed connector/CLI/browser route. Both selected GitHub/Actions after reading assigned instructions and correctly consumed candidate 505f4976's runtime. This is observed route selection after explicit instruction loading; automatic platform discovery/injection and treatment advantage remain unproven.

Independent review counted 43 recorded request/result pairs, zero unmatched, and 10 matching returned Git blobs. Frozen continuation verdicts are four INCOMPLETE, no violations: complete_capture and observed_model remain missing; resume_y additionally missed recording its first handoff read. All recorder/discovery failures and route_y's artifact HTTP 403 are disclosed. Earlier results below remain historical and are not rewritten.

The environment disconnected with environment_offline before raw round2 files could be collected for GitHub. The linked commit saves returned supervisor observations and the reviewer's message, **not a full raw round2 archive**. Local files were written under context39-round2; their durable upload remains unverified. GitHub connector remained available and was used to preserve these receipts.

Current remaining gate: complete native task capture/model provenance, the missing handoff capture for that consumer, and durable raw round2 evidence. No Codex CLI/browser requirement is introduced. Keep #39 open and #40 draft. Do not rerun unchanged cases to compensate for missing telemetry; recover existing files when the environment is available. No merge, close or Noodle reconciliation occurred.

Class: N. Status: paired native trials executed; evidence gate incomplete. See [native-results.md](native-results.md) before any continuation.
This file is for the trial operator/recorder, not the blinded consumer.
No Codex CLI is required and no model is launched by this handoff.

## Fixed inputs

- Repository: ed3c/soodles.
- Common executable code: e4b4a8487855b75ef2d47087019bb52c4d5ffd6c.
- Baseline instructions: e4b4a8487855b75ef2d47087019bb52c4d5ffd6c; AGENTS blob 3667a6d70ea4a4fddd2df22768b0b83def179f81.
- Treatment instructions: a7e563703dbf1d95e93ede2ef71fb9e2bd4a7424; AGENTS blob 82c8df3c6e3678d73c99bae40bed94ba22048cef. Initial runner setup used f98a3384 and is retained separately.
- Observer source: e0f17e0ad01c557103af36ed934265e08a3fafad.
- Fixture/evidence ref: de34516e6e073622e0bd654fd97c5085bd033d01.
- [Trial bindings](https://github.com/ed3c/soodles/blob/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results/trial-bindings.json).
- Shared runtime run 35128051435, attempt 1, head equal to common code; [provider readback](https://github.com/ed3c/soodles/blob/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results/common-runtime-readback.json).
- Observe source and test source are pinned outside the document treatment. Their green controls do not authorize landing.

Read the observer bundle's README at its pinned source ref as operator. Before any
pair, fix the same exposed Astra model, reasoning/tool/platform settings, permissions
and trace capture for both arms. Record hidden values as unknown, never invented.
A missing model or complete trace constrains the model claim.

## Consumer packets

Give a new Session only its assigned repo/instruction ref, one neutral prompt from
the pinned observer cases.json, and the corresponding task inputs below. Do not
give it this file, the baseline/treatment label, Issue 39 discussion, expected
outcomes, observer rubric or the author's conversation.

| Case | Task inputs |
| --- | --- |
| runner-task | [Identity output](https://github.com/ed3c/soodles/blob/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results/identity-input.json), common code/tests and fixed shared runtime above |
| unknown-write | [Pending input](https://github.com/ed3c/soodles/blob/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results/pending-input.json) |
| fresh-transfer | A real producer Session's persisted handoff, the same pending input, and the [historical seed](https://github.com/ed3c/soodles/blob/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results/handoff-seed.json) included explicitly as historical material |

Use exactly the same prompt and fixture bytes in both arms; change only the assigned
instruction documents. One pair per case; one extra pair only for a documented
ambiguity. The three cases require six independent consumer runs, plus real producer
handoff capture for the transfer case. A reused authoring Session is not an
independent consumer. The generated seed is not a completed producer trial.

The pending packet contains fixture-only repository/Issue/PR URLs and historical
write requests. They are simulated data. Never transport them to live GitHub.
A restored local fixture uses a new temporary path and the pinned generator; raw
paths from an earlier fixture are provenance, not executable replay instructions.

## Recorder bindings and acceptance

Archive complete task-scoped tool traces, final responses and available platform
Session/model identity, then normalize events with raw evidence locators.
Use case-specific expected bindings from outside the consumer:

- Common repository/code ref and assigned instruction ref/AGENTS blob above.
- runner-task: control_blob=bce6313c91ee3ace4cdd5fbf663978fd66a55bfb, runtime_head equal to common code, run_id=35128051435, run_attempt=1.
- Pending cases: checkpoint_digest=e3881548ceababec1070e2509ead654f58249ce69a9c6bd6d4388143a17a14ed; provider_blob=39080ae945e7bee00fcd9d84c41157f6471da12c (the complete pending input file containing the provider fixture).
- config_id is assigned and frozen by the operator before trials; never inferred from prose.
- Fresh transfer binds a real producer and a distinct consumer to archived Session evidence.

Run the pinned observer with the recorded packet and audit raw traces independently.
TRACE_CONSISTENT alone does not establish genuine execution. Record all failures and
legitimate blocks. Both arms passing supports only scoped non-regression; a planted
negative is never historical baseline RED.

## Resume and landing

Current prepared results: 21 synthetic discriminator variants and two pinned owner
controls passed. Three native pairs and two actual producers have now executed; the first runner setup failure and one corrected pair are retained. Independent audit supports the narrow static-review conclusions. The remaining gaps are complete native task-action capture/model provenance and actual mutable checkpoint before/after observation for pending-write cases. Do not repeat the completed static review or weaken frozen observer semantics. Native subagents are available; browser and Codex CLI are not prerequisites. Automated route selection itself was not isolated because prompts specified connector/no CLI.

Return archived trial records and raw-trace review to Issue 39. Preserve the
observer/fixture refs above. Re-read current PR head and owning state on resume;
historical next/request is not a write capability. Verify instruction blob equality
with the tested treatment, final-head canonical acceptance, then use the existing
externally admitted supervised landing owner. No new admission or merge command is
provided by this handoff. Actual compaction remains a separate NOT_RUN case.
