# Supervised delivery

A supervisor admits one exact Issue/PR claim to an immutable external landing owner. That owner emits guarded intent and exact transport requests. GitHub remains the provider; Noodle owns local reconciliation. This feature does not start autonomous scheduling or a Codex Agent.

## Preconditions and entry

Use a legitimate admitted Issue, clean final candidate head/tree, canonical acceptance and exact-head runtime Actions evidence. A local execution retains its Noodle-owned worktree; a cloud execution preserves evidence that no local candidate path, branch or registration was created. The supervisor selects an external publisher from an explicit immutable commit/digest before this acceptance. Never resolve the active judge from a default-branch tip, candidate import or historical next command.

Run the session doctor and resolve this checkout's skill as described in SKILL.md. Read the selected publisher's `landing start --help`; supply its confirmed claim, raw provider readback and fresh checkpoint paths. Preserve publisher `landing identity`, candidate identity, skill path/digests and the subject-specific trace outside the worktree. The selected publisher path is supplied by the supervisor, not guessed by this recipe.

## Consume the current owner result

This is an output contract, not a phase-to-command table:

| Observed output | Consumer responsibility |
| --- | --- |
| `next.kind: input` | Obtain the named `required` inputs from `next.owner`; retain `known` confirmed paths. Use the returned `operation` and `help_argv` to invoke its supported entry. A help command does not perform the transition. |
| `next.kind: provider_readback` | Perform the explicit GET operations and subjects in `requests` through GitHub. Preserve each response under its emitted request key in the readback object. Comparison requests already contain their confirmed endpoint SHAs; do not reconstruct them from an invalid-field prefix or remembered state. For dependent merge-commit readback, first confirm the actual merge SHA from the returned PR. Supply raw results to the named operation; never fabricate a local readback command or missing SHA. |
| `request` | Transport that newly emitted request exactly once through its named connector action. Preserve expected head and subject. Re-enter the owner with fresh provider readback after success or unknown outcome; never resend from trace. |
| `invalid` / nonzero exit | Preserve exact field/value and owning action. Text and JSON must agree. Follow explicit missing-input/readback guidance or supported help; help alone may not identify a recovery action. Do not infer one from field prefixes. |
| `next: null` | No next operation is offered. Inspect the receipt's scope/classification; identity or a fixture is not Issue resolution. |

The current implementation emits input/provider guidance and executable `help_argv`; it does not emit a general runnable transition `argv`. Missing or malformed comparison readbacks now include an exact GitHub compare GET, original operation and known checkpoint. For `readmit`, `next.known.claim` retains the validated fresh claim: supply those same values through the existing claim-file argument, without changing identity or authority. The owner does not invent a claim-file path. Human diagnostics include the same owner reason and compare URL as the structured output.

Follow the returned GET, preserve its raw response under the returned key, and re-enter the named operation only after a material readback change. Keep the rest of the provider snapshot fresh as requested. An unchanged wrong comparison is still a refusal, not a retry instruction. Unconfirmed comparison endpoints or foreign repository identity cannot produce a guessed provider request; obtain corrected identity from its owner instead of filling it in. Every actual owning action revalidates its inputs; stored guidance is not a capability. A new refusal must not be bypassed by running a previously observed request.

For a merged PR, missing or malformed `merge_commit` returns the dependent GET under `next.requests.merge_commit`, using the PR's confirmed merge SHA. Consume that exact request and retain the returned operation/checkpoint; start/readmit guidance also retains the validated claim. A missing or malformed `pr.merge_commit_sha` instead requests fresh PR readback and withholds the dependent commit GET. Do not infer a SHA from the candidate head or a historical command. Corrected commit data must still prove the exact SHA, ordered base/candidate parents and candidate tree; a refusal leaves the checkpoint and offered-write history intact. These inputs do not authorize another merge offer.

## Observe completion and failures

Positive completion requires the admitted candidate's merge commit/tree, GitHub PR merged and Issue closed/completed readbacks, and the external owner's `classification: RESOLVED`, `phase: resolved`, `next: null`. For a cloud claim, also require provider-main equality or complete merge-to-main comparison and `provider_reconciliation.local_reconciliation_required: false`; do not inspect or synchronize a scratch checkout. For a local claim, independently inspect the surviving control root's merged head/tree, clean status, and absent task worktree/branch. Preserve checkpoint digest, provider subjects and exact-head run/attempt. Green tests, a prepared request, provider closure alone or `next: null` alone are insufficient.

For a native cloud claim, omit `control_root`; after closure the current owner consumes fresh connector readback through `advance` and never requests a binary. A corrected external verifier may migrate a completed legacy local-shaped cloud checkpoint by removing only `control_root` while common identity remains unchanged, no execution envelope or real cleanup intent exists, and both writes are already recorded. Migration emits no provider request, requires fresh provider readback before resolution, and must not create a synthetic worktree. Local claims retain the Noodle-owned cleanup boundary.

Record each owner command and provider operation, expected versus unexpected refusals, fresh versus repeated readbacks, verification invocations and terminal receipt. Keep counter scope explicit; timestamps not actually observed remain unknown. A connector write that returns no reliable result requires the specific owner readback before any further offer. Same input without a material change does not justify a retry.

For fault/refusal controls, use [delivery recovery](delivery-recovery.md). Never plant a destructive failure in the real provider merely to make maintenance look complete. If live provider execution is unavailable, retain a blocked result for this feature, even if every local control passed.

## Cleanup and authority

On the local route the delivery owner invokes Noodle reconciliation; the skill must not remove the task worktree itself. On the cloud route no local cleanup is applicable and the owner must not invoke shell Git/Noodle. Continue terminal observation from the selected owner, preserving evidence outside disposable state. A supervisor may correct or delete erroneous implementation, tests or guidance through the admitted owner/boundary, with fresh acceptance as required; this recipe cannot approve its own repair. Unknown offered writes retain their readback obligation.

Sources: `landing.py` owns output and durable transitions; `soodles.py` owns CLI parsing/rendering; their nearest behavioral oracle is `delivery_oracle.py`. These pointers locate behavior, not a second authority. #18 remains outside this feature.
