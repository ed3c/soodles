---
name: test-manager
description: Own on-demand test scope and normal CI cost review for Soodles; trace necessary controls and optional observations without speculative full-suite runs.
---

# Test Manager

This is the single P-class owner of test scope. CLI, CI, verification and delivery
skills consume its decision. They do not add their own full-suite requirement.
[`test_manager.py`](../../../test_manager.py) resolves that scope and runs unit
controls; canonical acceptance executes only the named physical controls.
Neither the skill nor a selection receipt grants publication or landing authority.

Normal CI runs runtime acceptance for PR updates only. The landing owner already
checks exact merge parents/tree and provider-main readback; merging does not
request a second runtime run. An additional runtime check uses the `runtime`
workflow's manual dispatch with the exact base SHA and the observed behavior as
its reason. This is a new requested run, never a relabeled PR result.

For full-repository quality analysis, use `quality-report` manual dispatch.
Supply an exact base SHA and the question the analysis should answer.
The selected workflow ref fixes the head. Before executing requested work, both
workflows consume `test_manager.ci_request`. A push, completed workflow or
ordinary PR does not implicitly request a full quality report.
The completed-runtime cost collector remains read-only.

## Decide from the present need

Read the actual diff, changed behavior, callers and existing evidence. Apply the
pstack `architect` method of tracing ownership and consumers before changing the
boundary map; do not start a multi-model design exercise on every update.
The smallest sufficient verification scope must still cover the requested changed
behavior. Test selection does not reduce the user's delivery scope, and a passing
module selection does not establish that every contained case is necessary.

- Request the smallest existing controls that discriminate the changed behavior
  and its affected consumers. A shared filename, a large diff, a release stage,
  a failed test, a missing base or uncertainty does not require a full suite.
- Full coverage requires a concrete full-coverage request from the task or an
  explicitly selected acceptance requirement. Record that reason. Never invoke
  `--full` as a precaution, to discover impact, or to get around `needs_scope`.
  A model-written contract cannot create that demand merely by listing full coverage.
- Prose-only changes require review of changed meaning, not a runtime pass.
  Executable/evidence inputs under docs are not prose-only. Do not claim model
  behavior from a Markdown diff. P-class writing follows
  [review-writing](../review-writing/SKILL.md) for scoped evals and Schema Manager
  feedback. That requirement does not demand software tests or a full suite.
- Keep unique current behavior/refusal controls. Remove redundant historical
  reruns and duplicate runs through different entrypoints. A failure prompts
  diagnosis and affected controls, not automatic expansion to the full suite.

The user may request no test execution. Honor that limit while continuing the
authorized implementation, static review, normal-log readback and delivery.
Do not reduce the task to code preparation or infer permission for a test run.
Distinguish prohibited tests from separately authorized normal CI, and report
unexecuted checks without calling an unmet outcome complete.

Before initial admission, review the contract's required paths with Test Manager.
The declared candidate manifest uses the existing candidate-verification controls.
A new manifest filename does not require a new boundary-map entry.
For an unmapped required behavior, include its necessary scope consumer in the
admitted write paths. The writer must resolve that mapping before publication.
A scope plan does not certify the future artifact or authorize its effects.

During an admitted task, a scope omission is a known owner input.
Do not run an eval to discover that deterministic omission. Preserve the original
candidate and route it to the original admission owner's scope amendment.
Use scoped evals only when source and normal readback leave an Agent behavior
question unanswered. Missing evidence and unknown write outcomes are separate
conditions. An unknown write always needs its original owner's readback.

## Request once, consume everywhere

```sh
./soodles test --plan
./soodles test --base EXACT_SHA --plan
./soodles test --module test_provider_readback --reason 'Changed readback handling' --plan
```

Omit `--plan` only when execution is authorized. Local `test` covers unit controls;
the returned physical list is pending canonical acceptance, not already passed.
A clean working tree with no base only describes changes since HEAD; it does not
verify earlier commits. Obtain the admitted base from the current task/provider
for those commits, rather than guessing a historical ref.

Canonical acceptance uses the same manager and requires a base or an explicit
scope request. To verify an unchanged feature on demand, name its actual control:

```sh
./soodles acceptance verify ABSOLUTE_NOODLE --base EXACT_SHA
./soodles acceptance verify ABSOLUTE_NOODLE --control order_handoff --reason 'Requested order handoff verification'
```

`--module` and `--control` are repeatable and can be combined for local scope.
`--full` explicitly requests all controls supported by that entry: unit tests
for `test`, unit plus physical controls for `acceptance verify`. Do not combine
full with named local controls. Scope requests describe coverage, not authority.

## Resolve scope gaps without a human relay

`status=needs_scope` names unresolved changed paths. This is work for the current
supervising Agent: inspect the changed behavior and its callers, then supply
named controls with `--reason`. If the change establishes a reusable boundary,
correct the existing map in `test_manager.py` so CI consumes the same decision.
Do not create a second map, scheduler, report gate or policy file. Do not ask the
user to decide scope when the code and task already contain the answer.

If the provider base is missing, obtain its exact readback. Do not request full testing.
If tests were removed, identify their replacements or remaining coverage.
That removal does not require a full run. Ask for clarification only when evidence
or capability is unavailable, or the requested behavior is ambiguous.
Preserve the gap. Do not report unexecuted controls as green.

Reuse actual results only for the same verified source/input identity and covered
behavior. Additional changes or newly observed failures justify another affected
run; merely entering another skill or publishing does not. Record selection
reasons and normal-run timing logs. Do not add benchmark rounds to routine work.

## Audit necessity and normal CI cost

When reviewing CI cost, use existing normal-run evidence first. A selected module
is a coverage candidate, not proof that every contained case is necessary. Trace
each proposed reduction to the changed behavior, its unique assertion and the
remaining discriminator. A text mention or fixture import alone does not show
that every consumer case is affected; inspect the imported helper and its data
inputs before narrowing the existing boundary map.

Normal logs can identify avoidable work and support a targeted correction.
Report measured differences with their subjects and conditions.
Missing matched experiments limit causal claims; they do not require another experiment before an authorized correction.

Classify costs separately. The categories are exact-subject and provider
admission, affected behavior controls, fixture and process overhead, requested
physical controls, optional quality observations, and repeated execution across
PR, main and publication. Report job and phase wall time separately from
overlapping worker seconds. If case or setup timing is missing, record it as
unknown, not zero. Do not attribute fixture costs from names alone.

Treat full-repository quality metrics as an on-demand observation with a named
decision consumer, not an implicit correctness requirement on every PR. Changing
the measurement recipe warrants its focused controls; it does not by itself
require measuring every repository scope. Keep these decisions here and consume
them through the existing manager; do not introduce a second scope policy.

Do not build a PR/main test-result cache to eliminate an unnecessary invocation.
The supported delivery route consumes exact PR acceptance and its existing
merge/provider controls. Direct main edits have no implied acceptance; request
their affected verification explicitly. If a future task actually needs result
reuse across contexts, verify source, base/diff, runner, recipe, inputs and
coverage first; never present a PR receipt as a new main-head execution.

The selector follows actual Python fixture imports transitively, including
literal dynamic imports. It ignores prose mentions. If computed imports remain
unresolved, correct the scope. The current selector uses imported modules as its
unit of coverage. This implementation limit does not prove that every imported
case is necessary. It also does not prevent better selection. Before changing
selection, trace measured scope inflation to fixture dependencies and distinct
behavior controls. Do not claim method-level selection. Do not skip real
consumers just because their fixture method text stayed unchanged. Normal logs
record discovery, each module, and every case with its setup, teardown and
cleanups. Class fixtures and process import remain part of the module cost.
They are not costs of an individual case.

Prioritize measured avoidable work over minor runner tuning. Record whether a
reduction is implemented or only proposed, and whether it reduces delivery
latency, background runner time, or both. Add missing timing only to subsequent
authorized normal execution. For the observed scope inflation, repeat-run and
quality-report costs, consult the [2026-10-01 CI audit](../../../docs/test-manager-ci-cost-audit.md)
when working on those boundaries; its measurements are N-class, not policy or
an acceptance receipt.

## Original atom cost evidence

For cost review, use `./soodles atom cost-report AUTHORIZATION MANIFEST` on
original source-bound receipts. The [manifest contract](../../../docs/loop-cost/design.md)
specifies local process and provider files. This read-only entry consumes the
same Schema Manager projection as normal atom responses. It performs no tests
or network calls and grants no effects. Absent, partial or slow telemetry does
not request new tests. Keep the existing normal exact-head CI selection.

Distinguish observed wall time, foreground time, explicit waits, provider job
time and parallel module worker time. Cases are nested in modules. Parent
timing is not additional worker time. A pending, refused or unknown span does
not establish successful work, even when its elapsed duration is measured.
Incomplete starts and uninstrumented old owners retain unknown coverage.
When evidence is unavailable, tokens, price, API-call accounting and human
attribution remain unknown. If a source contains a measurement that the
requested consumer lacks, treat that as an integration gap.
The source data is available. Review actual end-to-end costs, including
writer, waits, rework and collection overhead. CI duration alone does not
establish delivery speed. Use the issue-atom
[completion guidance](../issue-atom/SKILL.md#preserve-the-request-through-admission-and-delivery)
when reconciling cost observations with the requested outcome. Repair seconds
remain elapsed since first repair; no cost projection creates new thresholds or
resets/reserves counters. Fixture gate observations are CI product controls,
never measurements of live exhaustion or independent acceptance authority.

For shortest-path work, move fact-determined workflow choices into the existing
CLI owner. When the task requests a decision comparison, use observable workflow
choices as the primary measure. Compare the same task, inputs, authority and legal completion boundary.
Count an externally visible choice once at its declared boundary. Do not count
JSON fields, file reads or tool calls as choices. Following the owner's fixed
decision adds no choice. Keep necessary engineering judgment separate from
avoidable workflow choices. Incomplete capture leaves the total unknown.
An added response field does not itself establish fewer Agent decisions.

An ordinary correction does not require a counter or comparison run.
Inspect the existing CLI. When facts already determine
the operation or input identities, correct that owner's input/output contract.
The CLI must select the operation and provide those identities. Missing evidence
remains a named input. Engineering corrections remain work for the named owner.
Use scoped controls to check the legal and rejected transitions. Use consumer
observations only for the unresolved behavior claim. Send both results and their
limits to Schema Manager. The original owner retains its continuation and effects.


## P-class feedback scope

Normal lifecycle cost projections call `review_cost` before Schema Manager.
The review names measured phases, their sources, and unknown measurements.
Repeated module observations need input comparison before they count as waste.
Historical failures need current owner readback before they trigger a correction.
The atom exposes this review with its unchanged `next` in `feedback`.
A resolved owner retains the history without reopening delivery.
Long durations and missing timing alone request no repair, eval, or test.

For the existing stage-outcome feedback entry, `feedback_scope` selects consumer
observations from Schema Manager's current result and the prior recorded round.
Resolve unsupported conditions before requesting a consumer. Reuse only passed
cases with matching instruction, method, requirement, input, and expected-value
identities. Missing observations still need original evidence references before
Schema Manager can pass the complete selection. A reuse decision is not an observation.
The decision records current projection cost. It requests no software modules,
physical controls, or full suite. Existing software scope selection remains separate.
