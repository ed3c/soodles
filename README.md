# soodles

Soodles coordinates admitted Issue work and delivery. Noodle owns runtime processes and worktrees.
Test Manager selects tests from the requested behavior and affected consumers.

## Start here

Read [AGENTS.md — Session entry](AGENTS.md#session-entry--select-once-then-act) at the task's selected ref.
Use the existing owner and continuation for an active task.
Local file changes do not update a pinned admission bundle or a running Session.

## Test on demand

The [Test Manager](.agents/skills/test-manager/SKILL.md) owns scope for local commands and CI.
Start with the changed behavior, its callers, and existing evidence.

```sh
./soodles test --plan
./soodles test --base EXACT_SHA --plan
```

The first command describes uncommitted changes. The second includes changes since the selected base.
Remove `--plan` only when test execution is authorized.
For a named behavior, use the manager's module or physical-control request with a reason.
Use `--full` only for explicit full-coverage demand.
Missing scope or a missing base does not request full coverage.

Normal PR CI consumes the same manager decision for the exact candidate head.
It downloads and checks the locked runtime only when selected physical controls need it.
Merge does not request another test run or a full quality scan.
An empty test selection is not an all-tests-passed result.
Candidate test results do not grant landing authority.

For a requested standalone runtime check, use the executable named by `policy/runtime.lock.json`:

```sh
./soodles runtime check /absolute/path/to/noodle
```

Use the [runtime recipe](.agents/skills/verify-soodles/features/runtime-admission.md) for selected admission/refusal verification.
Do not add that driver to an ordinary read or delivery.

## Execute and deliver

For a local Issue atom, follow [issue-atom](.agents/skills/issue-atom/SKILL.md).
The authorized supervisor prepares admission through its existing producer.
After selection, consume the returned command and environment unchanged.
Do not choose a lower-level admission, publication or landing command from phase names.

For an exact terminal candidate without an active atom, use the
[terminal delivery entry](AGENTS.md#terminal-candidate-delivery-entry) with the supplied immutable publisher and provider inputs.
For existing delivery, follow [supervised delivery](.agents/skills/verify-soodles/features/supervised-delivery.md).
Local provider reads use [provider-readback](.agents/skills/provider-readback/SKILL.md).
Cloud delivery uses its selected connector.

The owner preserves unknown writes and requests fresh readback.
Do not repeat a write or replace a checkpoint because its response is missing.
Noodle retains local cleanup and original-order ownership.
Keep evidence outside disposable worktrees.

Owner `resolved` confirms that owner's terminal state.
Check the user's requested outcomes before declaring the whole task complete.
For corrections, retain the current owner and its returned recovery requirements.
Keep the selected external judge fixed for its acceptance.

Read the relevant [system contract](contracts/system-v1.md) for behavior and authority boundaries.
`docs/` retains observations and historical evidence. It does not define current operating authority.
Use the [historical record guide](docs/experiments/README.md) to distinguish revised explanations from fixed evidence and find the original bytes.
