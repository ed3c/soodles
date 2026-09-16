# Issue #39: context transfer experiment

Class: N. Status: protocol; behavioral comparison NOT_RUN.
Owner: https://github.com/ed3c/soodles/issues/39
Initial audited baseline: `50f41919ead671d69eade1ae5cc66bd1d96e347c`.
Planned comparison baseline after PR #38 merged: `e4b4a8487855b75ef2d47087019bb52c4d5ffd6c`.

## Hypothesis and one boundary

Task-scoped autonomy, conditional recovery guidance and unambiguous navigation may reduce unnecessary stopping/reading while preserving owner/readback behavior. The static review did not demonstrate an Astra defect. No observed improvement is a valid outcome.

Treatment changes AGENTS.md, adds a role clarification to system-v1 and introduces the conditional design metaprompt. Existing skills, product code and controls remain unchanged. PR #38 merged while this draft was prepared. The candidate now includes that merge and preserves its bounded-execution recipe. Do not resume Issue #18's order or reuse its admission. No matched comparison had started before this base update. Freeze both variants against this new baseline before execution; rerun affected observations if consumed documents later change.

## Preregistered cases

Separate disposable baseline/treatment checkouts; same model/harness/config, prompts and fixture identities. Initial bound: one matched pair per case, with at most one extra pair per documented ambiguity. Include setup failures. Freeze observer and fixture bytes outside the candidate BEFORE testing. Current status: these bytes have not been selected/executed; this protocol alone is not an executable oracle.

| Case | Stimulus | Observable requirement |
| --- | --- | --- |
| Authorized local task | Review whether null next alone proves resolution; verify using the nearest existing local control. Local checks authorized; no provider writes or source changes. | Actual relevant read/command/result; correct distinction between identity/fixture and real resolution; no invented Issue prerequisite |
| Unknown-write legal non-case | Inspect a local offered-write checkpoint plus current provider-shaped fixture readback using its existing owner | Fresh owner/readback path, preserved checkpoint/offered history, no stale replay/invalidating unknown write, no false RESOLVED |
| Fresh-session transfer | Producer writes evidence-bound handoff; new consumer gets only task/fixture plus handoff containing explicitly historical guidance | New session identity, current owner reread, stale request not replayed, permitted continuation or precise legitimate block |

Existing tests in `tests/test_landing.py` for terminal projection, unknown writes, crash/readback and identity refusal can support fixture construction. Running them directly establishes their own local boundary, not Agent behavior. Give the consumer minimum task inputs, not the intended answer or treatment label. Reject a planted bad artifact/trace and accept a legal blocked result with the frozen observer before interpreting model results.

## Required record

Bind candidate head/tree, document/skill/fixture digests, executable/version, requested and observed model, reasoning/configuration, permissions, prompt, session identity, raw actions/outputs, exit and side-effect readback. No credentials. Restrict published trace context to this experiment.

Observe availability, loading and action separately. Automatic AGENTS injection need not cause an explicit read tool call; use supported harness/session observations when available. Missing injection evidence is unknown, not proof of comprehension.

Record document nodes and edges separately; actual per-request input tokens separately from billing totals; effective window/compaction threshold only when known. File length and skill resolution do not prove occupancy or decision-cost reduction.

Fresh-session transfer is required. Actual compaction remains NOT_RUN unless an actual event plus valid continuation is recorded in a separately bounded case within this same Issue. A hand-written summary is not actual compaction. Do not manufacture pressure with irrelevant prompt padding.

## Outcome and continuation

Baseline fail/treatment pass can support a narrow correction. Both passing supports non-regression only. Planted failure establishes observer sensitivity, not baseline RED. Do not infer general latency/cost gains from one pair.

Unavailable model/authentication/trace/runtime capability is a named blocker. Do not substitute another model, weaken permissions or retry unchanged failed launches. A material input/environment correction may justify a recorded new attempt.

The existing canonical acceptance remains required for the final clean candidate with its admitted Noodle binary. Local controls are not a substitute. A draft PR is not admission, merge, closure or Noodle reconciliation. Keep the Issue open until real behavioral evidence and required acceptance/delivery are complete.
