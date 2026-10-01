---
name: test-manager
description: Own on-demand test scope for Soodles changes and requested verification; choose named local controls or explicitly requested full coverage without speculative suite runs.
---

# Test Manager

This is the single P-class owner of test scope. CLI, CI, verification and delivery
skills consume its decision; they do not add their own full-suite requirement.
[`test_manager.py`](../../../test_manager.py) resolves that scope and runs unit
controls; canonical acceptance executes only the named physical controls.
Neither the skill nor a selection receipt grants publication or landing authority.

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
