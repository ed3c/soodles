---
name: test-manager
description: Own on-demand test scope and normal CI cost review for Soodles; trace necessary controls and optional observations without speculative full-suite runs.
---

# Test Manager

This is the single P-class owner of test scope. CLI, CI, verification and delivery
skills consume its decision; they do not add their own full-suite requirement.
[`test_manager.py`](../../../test_manager.py) resolves that scope and runs unit
controls; canonical acceptance executes only the named physical controls.
Neither the skill nor a selection receipt grants publication or landing authority.

Normal CI runs runtime acceptance for PR updates only. The landing owner already
checks exact merge parents/tree and provider-main readback; merging does not
request a second runtime run. An additional runtime check uses the `runtime`
workflow's manual dispatch with the exact base SHA and the observed behavior as
its reason. This is a new requested run, never a relabeled PR result.

Full-repository quality analysis uses `quality-report` manual dispatch with an
exact base SHA and the question it should answer. Its selected workflow ref fixes
the head. Both workflows consume `test_manager.ci_request` before executing
requested work; no push, completed workflow or ordinary PR implicitly requests
a full quality report. The completed-runtime cost collector remains read-only.

## Decide from the present need

Read the actual diff, changed behavior, callers and existing evidence. Apply the
pstack `architect` method of tracing ownership and consumers before changing the
boundary map; do not start a multi-model design exercise on every update.

- Request the smallest existing controls that discriminate the changed behavior
  and its affected consumers. A shared filename, a large diff, a release stage,
  a failed test, a missing base or uncertainty does not require a full suite.
- Full coverage requires a concrete full-coverage request from the task or an
  explicitly selected acceptance requirement. Record that reason. Never invoke
  `--full` as a precaution, to discover impact, or to get around `needs_scope`.
- Prose-only changes require review of changed meaning, not a runtime pass.
  Executable/evidence inputs under docs are not prose-only. Do not claim model
  behavior from a Markdown diff or add an unrequested behavioral experiment.
- Keep unique current behavior/refusal controls. Remove redundant historical
  reruns and duplicate runs through different entrypoints. A failure prompts
  diagnosis and affected controls, not automatic expansion to the full suite.

The user may request no test execution. In that case prepare/review the decision
and code only; do not reinterpret a full-coverage requirement as permission to
run it now. Clearly report what remains unexecuted.

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

A missing provider base requires its exact readback, not full testing. Removed
tests require identifying the replacement or remaining coverage, not a full run.
Only unavailable evidence/capability or genuinely ambiguous requested behavior
needs clarification. Preserve the gap; do not report unexecuted controls as green.

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

Classify costs separately: exact-subject/provider admission, affected behavior
controls, fixture/process overhead, requested physical controls, optional quality
observations, and repeated execution across PR/main/publication. Report job/phase
wall time separately from overlapping worker seconds. Missing case/setup timing
is unknown, not zero; do not attribute fixture costs from names alone.

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
literal dynamic imports, and ignores prose mentions. Unresolved computed imports
need a scope correction. Imported modules remain the unit of coverage; do not
claim method-level selection or skip real consumers just because their fixture
method text stayed unchanged. Normal logs record discovery, every case including
its setup/teardown/cleanups, and each module; class fixtures/process import remain
part of the module cost rather than an individual case.

Prioritize measured avoidable work over minor runner tuning. Record whether a
reduction is implemented or only proposed, and whether it reduces delivery
latency, background runner time, or both. Add missing timing only to subsequent
authorized normal execution. For the observed scope inflation, repeat-run and
quality-report costs, consult the [2026-10-01 CI audit](../../../docs/test-manager-ci-cost-audit.md)
when working on those boundaries; its measurements are N-class, not policy or
an acceptance receipt.

## Original atom cost evidence

For cost review use `./soodles atom cost-report AUTHORIZATION MANIFEST` on
original source-bound receipts; the [manifest contract](../../../docs/loop-cost/design.md)
specifies local process/provider files. This is read-only and consumes the same
Schema Manager projection as normal atom responses. It performs no tests or
network calls and grants no effects. Telemetry absent, partial or slow is never
new test demand. Keep the existing normal exact-head CI selection.

Distinguish observed wall/foreground time, explicit waits, provider job time and
parallel module worker time. Cases are nested in modules; parent timing is not
additional worker time. A pending/refused/unknown span is not successful work,
even when its elapsed duration is measured. Incomplete starts and uninstrumented
old owners retain unknown coverage. Tokens, price, API-call accounting and human
attribution remain unknown without their own supported evidence. Repair seconds
remain elapsed since first repair; no cost projection creates new thresholds or
resets/reserves counters. Fixture gate observations are CI product controls,
never measurements of live exhaustion or independent acceptance authority.
