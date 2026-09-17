# Issue #39: context transfer experiment

Current status: the [complete instrumented local comparison](local/comparison-results.md) satisfies the three bounded cases in both arms, with scoped non-regression and no demonstrated treatment advantage. Actual child exits, native model/tool evidence, producer transfer and independent raw/export review are preserved in its immutable archive. Disclosed procedural deviations and failed pre-model attempts remain visible. Historical [cloud results](recovery-results.md) and earlier local INCOMPLETE observations are unchanged; chronology below is historical.

Class: N. Historical cloud status: native paired cases executed; evidence gate incomplete. See [current observations](native-results.md); the earlier setup chronology below is retained.
Owner: https://github.com/ed3c/soodles/issues/39
Initial audited baseline: `50f41919ead671d69eade1ae5cc66bd1d96e347c`.
Planned comparison baseline after PR #38 merged: `e4b4a8487855b75ef2d47087019bb52c4d5ffd6c`.

## Hypothesis and one boundary

Task-scoped autonomy, conditional recovery guidance and unambiguous navigation may reduce unnecessary stopping/reading while preserving owner/readback behavior. The static review did not demonstrate an Astra defect. No observed improvement is a valid outcome.

Treatment changes AGENTS.md and README entry routing, adds a role clarification to system-v1, introduces the conditional design metaprompt, and changes the existing verify-soodles SKILL.md entry so cloud verification precedes conditional local steps. Product code, feature recipes, workflows and existing controls remain unchanged. PR #38 merged while this draft was prepared. The candidate now includes that merge and preserves its bounded-execution recipe. Do not resume Issue #18's order or reuse its admission. No matched comparison had started before this base update. Freeze both variants against this new baseline before execution; rerun affected observations if consumed documents later change.

## Carrier and evidence owner

Current path: **ChatGPT Session Agent → GitHub connector → GitHub Actions → Soodles/Noodle runtime**. The Agent is already running in this Session. No nested Codex CLI, CLI login, local model probe or local Noodle installation is required for connector/Actions work.

Select this path using current Session/task context, actual connector calls and exact provider run readback. Persist that basis and re-evaluate only if execution changes to a local Soodles → Noodle → Codex child; only that local path requires CLI preflight. Do not introduce a new selection flag.

The cloud Agent reads pinned repository files through the connector, invokes existing authorized workflow paths, and consumes run/job/artifact results. Actions is the process/test executor, not a second Astra Agent. Record the instruction refs/blobs returned to the Session and subsequent tool actions; record workflow/run/attempt/head and artifact identity separately. Hidden cloud input assembly and CLI-specific token budgets are not interchangeable.

A real counterexample to the previous global blocker is runtime run [35128976519](https://github.com/ed3c/soodles/actions/runs/35128976519): for head `d0bf6accc53d95f8900fe648ab40ffcacdd96013`, the provider reports successful binary verification, canonical acceptance and artifact upload, without a CLI step. This is historical CI evidence only. Read new-head results for any later candidate.

The old local CLI probes are retained as inapplicable-route observations. Scratch `environment_offline` does not block available GitHub/Actions operations. A missing fixture, action or fresh cloud Session blocks only the corresponding experiment. Do not report every case blocked because optional internal context metrics are unavailable.

## Preregistered cases

Use isolated baseline/treatment native cloud subagent threads, started with fork_turns=none, with pinned repository variants and disposable Actions fixtures; keep the same exposed model/platform/tool configuration, prompts and fixture identities. A local comparison is a separately labelled carrier and cannot replace the cloud case. Initial bound: one matched pair per case, with at most one extra pair per documented ambiguity. Include setup failures. Freeze observer and fixture bytes outside the candidate BEFORE testing. Observer/case source is frozen at `e0f17e0ad01c557103af36ed934265e08a3fafad`; executed fixture inputs and the detector-control receipt are frozen separately at `de34516e6e073622e0bd654fd97c5085bd033d01`. These are experimental, non-authorizing records. This was the pre-trial setup status. Native comparisons have now executed; their incomplete evidence verdicts are recorded in native-results.md.

| Case | Stimulus | Observable requirement |
| --- | --- | --- |
| Authorized runner task | Review whether null next alone proves resolution; verify using the nearest existing local control. Checks on the selected runner are authorized; no production delivery writes or source changes. | Actual relevant read/command/result; correct distinction between identity/fixture and real resolution; no invented Issue prerequisite |
| Unknown-write legal non-case | Inspect a local offered-write checkpoint plus current provider-shaped fixture readback using its existing owner | Fresh owner/readback path, preserved checkpoint/offered history, no stale replay/invalidating unknown write, no false RESOLVED |
| Fresh-session transfer | Producer writes evidence-bound handoff; new consumer gets only task/fixture plus handoff containing explicitly historical guidance | New session identity, current owner reread, stale request not replayed, permitted continuation or precise legitimate block |

Existing tests in `tests/test_landing.py` for terminal projection, unknown writes, crash/readback and identity refusal can support fixture construction. Running them directly establishes their own local boundary, not Agent behavior. Give the consumer minimum task inputs, not the intended answer or treatment label. Reject a planted bad artifact/trace and accept a legal blocked result with the frozen observer before interpreting model results.

## Required record

Bind candidate head/tree, document/skill/fixture identities, requested and exposed model/session configuration, permissions, prompt, Session/tool actions, workflow version/run/attempt/head, process outputs and side-effect readback. Record local executable/version only for operations that actually use it. No credentials. Restrict published trace context to this experiment.

Observe availability, loading and action separately. For this cloud path, retain connector file-read results; do not claim local CLI automatic injection. For a separately observed CLI path, automatic AGENTS injection need not cause an explicit read call. Missing injection evidence is unknown, not proof of comprehension.

Record document nodes and edges separately; actual per-request input tokens separately from billing totals; effective window/compaction threshold only when known. File length and skill resolution do not prove occupancy or decision-cost reduction.

Fresh-session transfer is required. Actual compaction remains NOT_RUN unless an actual event plus valid continuation is recorded in a separately bounded case within this same Issue. A hand-written summary is not actual compaction. Do not manufacture pressure with irrelevant prompt padding.

## Outcome and continuation

Baseline fail/treatment pass can support a narrow correction. Both passing supports non-regression only. Planted failure establishes observer sensitivity, not baseline RED. Do not infer general latency/cost gains from one pair.

Only unavailable capabilities required by the selected operation are blockers. Do not substitute another model, weaken permissions or repeat unchanged failed launches. The current Session has seen the correction and expected answers, so its continuation is a carrier-routing observation, not an independent baseline/treatment case. A fresh cloud Session can test the handoff without CLI; if unavailable, keep that case NOT_RUN and report only the actual limitation.

The existing canonical acceptance remains required for the final clean candidate; the cloud path uses the existing runtime Actions workflow, which installs and verifies its admitted Noodle binary on the runner. An absent scratch binary is not a prerequisite failure for that workflow. A prior head's green run cannot validate a new head. A draft PR is not admission, merge, closure or Noodle reconciliation. Keep the Issue open until real behavioral evidence and required acceptance/delivery are complete.

## Frozen implementation and observed preparation

- Observer source: [immutable bundle](https://github.com/ed3c/soodles/tree/e0f17e0ad01c557103af36ed934265e08a3fafad/docs/experiments/agent-context/observer).
- Fixtures and execution receipt: [immutable results](https://github.com/ed3c/soodles/tree/de34516e6e073622e0bd654fd97c5085bd033d01/docs/experiments/agent-context/observer/results).
- Consumer/operator separation and exact inputs: [trial handoff](trial-handoff.md).

The observer ran four unittest methods covering 21 synthetic variants: three valid/legal cases, ten planted violations, and eight incomplete-evidence cases. All passed their expected detector outcome. This validates only the discriminator on those inputs. Its TRACE_CONSISTENT result always retains behavior_proven=false and requires independent review of complete raw traces.

Two existing owner controls ran against six source blobs verified at the common code ref. A real disposable checkpoint retained its exact SHA-256 across unknown-write readback, retained writes_offered=[merge], and returned provider_readback without another request. A real landing identity invocation returned next:null; it did not establish Issue resolution. The temporary checkpoint and its directory were subsequently observed absent. Provider data is simulated and no provider writes occurred.

The shared common-code runtime is run 35128051435, attempt 1, head e4b4a8487855b75ef2d47087019bb52c4d5ffd6c; provider job records show successful canonical acceptance. This fixed shared input prevents workflow head differences from becoming a second treatment variable. Final candidate acceptance remains separate.

The initial instruction treatment was f98a3384a3fbd585ae2f1008036d7868b9dbced4. The corrected runner pair and remaining cases used a7e563703dbf1d95e93ede2ef71fb9e2bd4a7424 (AGENTS blob 82c8df3c6e3678d73c99bae40bed94ba22048cef). Subsequent protocol/receipt/handoff-only changes do not silently change that trial input. Before landing, verify that the proposed instruction blobs still match the tested treatment; any consumed instruction change requires affected trials to be rebound.

Superseded setup assessment: the earlier browser/top-level-Session-only assumption was too narrow. The authorized carrier is now native cloud subagent threads with no inherited conversation. This establishes neither top-level ChatGPT automatic loading nor filesystem/security isolation. Python execution is now available for the bounded fixture checks, and the cloud connector/Actions path remains usable without Codex CLI. Do not substitute synthetic events, current steered Session behavior, or fixture-owner execution for fresh Agent trials. That setup status is superseded: all three matched pairs and real fresh transfer have executed, with the evidence gate still incomplete. Actual compaction remains separately NOT_RUN and is not asserted by these results.

## Native subagent iteration, same atom

User authorizes the cloud native subagent loop in #39. Use explicit gpt-6-astra model selection, no inherited conversation, fixed read-only GitHub input refs, identical tasks/configuration across arms, and distinct recorder directories. Browser and Codex CLI are not used. Platform task names from spawn receipts identify threads; requested model configuration must not be misreported as hidden provider-internal identity.

A first runner pair at the earlier treatment f98a3384 observed both consumers reaching the scoped null-next conclusion. The baseline recorder lost early appended events because in-memory load mutations were not persisted. Preserve that incomplete attempt as a setup failure, not a PASS. Permit the already bounded one extra runner pair after a recorder correction: persist each request and returned result to a separate artifact immediately, before further task actions. Do not reconstruct missing old events or silently overwrite prior trials. The updated AGENTS delegation entry will be pinned before this repeat and all remaining cases.

Consumer-recorded tool records are distinct from a full native platform transcript. Review actual evidence coverage independently and retain unknown native coverage/model internals. The frozen observer must return INCOMPLETE wherever its complete-capture/model requirements cannot be established; a semantic or provenance review cannot relabel that as machine PASS. This is a measured limitation to report, not a reason to install a CLI or open a browser.

## Current execution receipt

See [native observations](native-results.md) and [immutable evidence](https://github.com/ed3c/soodles/tree/c6ac2e1a43eb21993b8903a292bf3f60a80414f0/docs/experiments/agent-context/native-trials). Six consumers plus two real producers completed. Independent audit verified 50 paired requests/results. Frozen verdicts remain two INCOMPLETE and four REJECT due absent mutable checkpoint observations. Complete native capture and observed model remain unavailable. No merge/closure/reconciliation is authorized by this experiment.

## Latest bounded continuation

[Durable supervisor observation receipt and independent reviewer message](https://github.com/ed3c/soodles/tree/49f4c0ef16887535656d757ca53cbb31e41e043d/docs/experiments/agent-context/native-round2). Four fresh consumers actually invoked the existing owner on mutable disposable checkpoints: exit 0, readback, merge_pending, no new request. Supervisor and independent reviewer checked before/after bytes; all match digest e3881548ceababec1070e2509ead654f58249ce69a9c6bd6d4388143a17a14ed and preserve writes_offered=[merge]. All four live checkpoint paths were removed. The mutable-checkpoint evidence gap is now addressed within this fixture scope.

Two new consumers received no prescribed connector/CLI/browser route. Both selected GitHub/Actions after reading assigned instructions and correctly consumed candidate 505f4976's runtime. This is observed route selection after explicit instruction loading; automatic platform discovery/injection and treatment advantage remain unproven.

Independent review counted 43 recorded request/result pairs, zero unmatched, and 10 matching returned Git blobs. Frozen continuation verdicts are four INCOMPLETE, no violations: complete_capture and observed_model remain missing; resume_y additionally missed recording its first handoff read. All recorder/discovery failures and route_y's artifact HTTP 403 are disclosed. Earlier results below remain historical and are not rewritten.

The environment disconnected with environment_offline before raw round2 files could be collected for GitHub. The linked commit saves returned supervisor observations and the reviewer's message, **not a full raw round2 archive**. Local files were written under context39-round2; their durable upload remains unverified. GitHub connector remained available and was used to preserve these receipts.

Current remaining gate: complete native task capture/model provenance, the missing handoff capture for that consumer, and durable raw round2 evidence. No Codex CLI/browser requirement is introduced. Keep #39 open and #40 draft. Do not rerun unchanged cases to compensate for missing telemetry; recover existing files when the environment is available. No merge, close or Noodle reconciliation occurred.

