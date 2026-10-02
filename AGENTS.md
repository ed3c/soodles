# soodles

Migrate only exact, executable claims demonstrated in this repository.

When writing or revising documents, use ASD-STE100 principles as a writing aid.
Use short sentences, explicit actors, consistent terms, and conditions before actions.
Preserve exact commands, identifiers, facts, and raw evidence.
These principles do not add a verification gate or establish formal compliance.

## Session entry — select once, then act

When entering Soodles, read this file at the task's selected repository ref.
A cloud Session fetches it through GitHub. For Issue/PR work, use the task's
currently admitted ref. Neither main nor a historical PR head necessarily
contains the selected instructions. Use current task, tool, and owner evidence
to select a path below. Proceed within existing authorization without asking
the user to select it again. If the task supplies a selected recipe, read that
recipe directly at its selected ref. Do not rediscover it through the full
feature map. This file's presence does not prove that the host loaded it.

| Observed execution path | Shortest supported action |
| --- | --- |
| ChatGPT Session using GitHub connector / Actions | Read the exact Issue/PR/head and `.github/workflows/runtime.yml`. Consume the matching runtime run, job steps, and artifact evidence through GitHub. Authorized PR creation or update triggers the existing workflow. For an unchanged head, reuse its result or observe its in-flight run. Do not launch Codex CLI or install a scratch Noodle. |
| Local Session explicitly authorized to execute an Issue atom | Use the [issue-atom skill](.agents/skills/issue-atom/SKILL.md) and the local entry forms below, according to the current authorization state. |
| Local Soodles → Noodle → Codex child | The writer follows its selected [execute skill](.agents/skills/execute/SKILL.md) and supplied instruction context. A supervisor observing that child uses the [bounded execution recipe](.agents/skills/verify-soodles/features/issue-execution.md). Use the admitted control root, envelope and owner. Do not reconstruct launcher argv. |

For that explicitly authorized Local Session, the existing entry forms are:

```text
[PYTHON, "-B", SUPERVISOR_ADMISSION, "authorize", SELECTION_JSON, SELECTION_SHA256, NEW_EXTERNAL_OUTPUT]
[ISSUE_ATOM, "run", AUTHORIZATION_JSON]
```

These are argv templates. Use the supplied absolute Python interpreter and
entry paths, the exact selected file bytes and digests, and a new absolute
output directory outside the control root. `supervisor-admission` is Python.
Invoke the shell executable `issue-atom` directly, never through Python.

Before initial authorization selection, the authorized Session may act as
supervisor. Prepare the explicit selection and its SHA-256 with the
[authorization recipe](.agents/skills/verify-soodles/features/local-supervisor-admission.md),
then use `authorize`. The producer derives the authorization path, digest, and
validated continuation. Do not ask the user to create those files or hashes.
The lower-level `prepare` verb belongs to the lifecycle.

On `status=prepared`, preserve the receipt. For authorized lifecycle execution,
use its `next.argv` and `next.environment` unchanged. The environment binds
`SOODLES_AUTHORIZATION_SHA256`. Respect the task's stopping point. If the task
requests only preparation or the first non-help receipt, save that receipt and
hand off `next` without executing it.

Once authorization is selected, preserve that exact identity and the existing
`issue-atom run` continuation. If a selected file is missing, its owner must
recover the exact bytes. Never run another `authorize` to replace it.
If selected identity, capability, or credentials are missing, obtain the named
owner input. Retain the refusal and unchanged continuation. Re-enter only after
the required material change. Do not guess credentials, select replacement
authority, or let a candidate writer select its judge. These entry forms remove
entry ambiguity. They do not replace required validation, receipts, or owner
readback.

For an active atom, its continuation obtains the parked child's publication
claim and readiness receipt, then calls the publication owner. The supervising
Agent must not also publish. For a separately admitted standalone publication,
use the [candidate-publication skill](.agents/skills/candidate-publication/SKILL.md)
with the supplied exact claim and readiness or acceptance receipt.
The publication owner handles push, readback, and PR identity. The Agent never
reconstructs them. Native readiness permits publication only. Linux exact-head
Actions acceptance must still precede landing. The local external landing owner
emits merge and closure requests and owns reconciliation. CI need not hold merge
authority.

Local runtime tests that launch no Codex child need no Codex CLI. The presence
of a CLI binary does not impose local-launcher requirements on a cloud Session.
If ownership is unknown, inspect the next operation's owner. Ask for clarification
only if identity or authority remains unresolved.

For authorized independent cloud work or context-transfer verification, use
the platform's native subagent tool through its current exposed schema. If tool
exposure is unknown, use the applicable scoped capability discovery. Incomplete
discovery leaves exposure unknown. Confirmed absence applies to this Session,
not the product. Missing freshness or recording blocks only the affected
comparison.

Preserve the selected carrier. A capability gap does not authorize a proposed
or constructed replacement runner. An alternative needs an explicit authorized
selection and separate comparison conditions. When requirements are met,
proceed without asking again. Start each consumer without inherited conversation
(`fork_turns: "none"` where the current schema supports it). Pass only the task,
pinned instruction and code refs, and required inputs. Keep expected outcomes
with the supervising observer.

Native threads share files. Use distinct evidence directories and pinned
read-only GitHub inputs. A branch or worktree does not isolate model context.
Use a Noodle-owned worktree only when the task needs source writes. Record
actual tool requests and results as they occur. Distinguish consumer-recorded
evidence from a complete platform transcript. Browser login and Codex CLI are
not prerequisites for this path. Delegate only within current user and platform
authorization. If the native tool is absent, report that specific capability
gap and continue other authorized work.

Retain the selected path and its evidence in the existing task handoff.
Include repo/ref, Issue/PR/head, carrier/reason, run/attempt or local
owner/session/checkpoint, and the next required readback. On resume, refresh
mutable owner and provider state. Reselect only when execution ownership changes.
A new Session refreshes relevant capability observations. It must not inherit
a previous Session's absence claim. An unchanged turn is not a new preflight.
No new flag, state file, or repeated preflight is required.

Scratch `environment_offline` blocks only dependent scratch operations. Missing
capabilities block their own operation, not the other path. Consume current
owner `next`/`request`. Never replay historical writes.

### Terminal candidate delivery entry

Use the repository `landing-supervisor` entry when both conditions are met:
the supplied provider snapshot identifies one successful exact-head terminal
candidate, and the supervisor has selected immutable external publisher bytes
and the Cloud/Local route. Run the entry with those supplied inputs and a new
external output directory. Consume the returned current landing-owner `next`
exactly. Its checkpoint, readback, and argv paths must name that final output
directory.

Do not search repository history for another publisher or derive authority from
the latest or default branch. Do not assemble a landing claim or checkpoint in
the Agent, or choose `start`/`advance`/`dispatch` from prose. A refusal names the
missing supervisor or provider input. It does not permit a historical identity
as a substitute.

## Task scope and completion

Use the user's requested outcomes and stopping point to judge task completion.
A generated Issue contract or acceptance plan must preserve them. It cannot
silently narrow them. Within current authorization, continue necessary inspection,
correction, and relevant checks. Finish an analysis or review with findings.
Finish an implementation with the requested behavior and evidence.

Delivery also requires the existing owner's terminal state. Merge, cleanup,
and `resolved` alone do not establish fulfillment of the user's request.
Keep unmet outcomes in the existing task or handoff and continue authorized work.
A blocked effect stops only dependent work. For a local atom, use the
[scope and completion guidance](.agents/skills/issue-atom/SKILL.md#preserve-the-request-through-admission-and-delivery).

For an observed defect, preserve the actual owner, process, and readback
evidence. Use the admitted contract's declared controls at the nearest executable
boundary. The existing atom consumes a finite pinned repair policy. The model
does not classify retryability or choose a recovery verb. Missing lineage,
conflicting identity, exhausted budget, and unknown effects stop the affected
repair branch.
Use `./system-context entry issue-atom run` (or `soodles candidate publish` /
`provider-readback consume`) for committed consumer/decision P-class requirements.
Consume current owner `next`/`request` unchanged. These selections grant no effects.

A fresh Agent comparison or evals skill is required only when the admitted task
selects that measurement. For such a claim, use the scoped
[behavior comparison procedure](.agents/skills/verify-soodles/features/pclass-context.md).
Product controls and instruction source hashes do not establish Agent behavior
improvement. Preserve historical evidence and report unsupported claims explicitly.

Stop the affected operation when its owner requires missing identity, credentials, admission, capability or readback. Report that exact prerequisite and preserve evidence. Prior user authorization remains applicable, but it does not create a missing executable capability or let the candidate select its own judge.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. Runtime verification uses disposable fixtures. An admitted local atom may start its selected Noodle loop through the existing owner. Fixture verification alone grants no such authority.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- The [Test Manager](.agents/skills/test-manager/SKILL.md) is the single P-class owner of verification scope. Local CLI, canonical CI, and other skills consume its decision from `test_manager.py`. They never independently append a full-suite run. Inspect the actual changed behavior and request only its necessary controls. Full coverage requires explicit demand. A shared file, missing base, unknown change, or failure does not request it. The current Agent resolves scope gaps. They do not automatically require human handoff. Preserve exact-head provider evidence and external landing authority. Compare costs through normal execution logs.
- Normal PR acceptance, additional runtime verification and optional full-repository quality observation follow the Test Manager's CI demand routing. A merge or completed workflow does not independently request another regression run or full quality scan. Consume existing landing readbacks. Never relabel a PR result as main-head execution.
- Keep `tests/` focused on current behavior and distinct failure boundaries. Use small disposable fixtures. Do not copy the repository or rerun historical implementations or reports in routine acceptance. Historical evidence stays under `docs/`. When replacing a replay, retain any unique current behavior controls. Frozen external verifier bytes and their authority are unchanged by test maintenance.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot select or authorize their own verifier.
- For a user-authorized local Issue lifecycle, the supervising Session prepares the external authorization and digest through the [issue-atom skill](.agents/skills/issue-atom/SKILL.md). Missing generated files do not require human handoff. Ordinary edits do not require an atom. Once prepared, use only `./issue-atom run /absolute/authorization.json` and re-enter its returned same command after material state changes. Never reconstruct `./noodles issue handoff`, select an Issue/landing verb, or retry an unknown provider write.
- First installation uses the explicitly requested supervised fallback. The supervisor pins the landing implementation outside the candidate, admits one exact claim, and supplies raw provider readbacks. `landing.py` owns pending-write checkpoints and exact requests. The existing GitHub connector executes them under existing provider rules. No Administration access or protection-policy modification is a prerequisite.
- Do not fabricate a production generation, independent default-branch verification, or unattended lander. A cloud Issue is RESOLVED only from exact merge, closure, runtime, and provider-main readback through the connector. A local Issue also requires Git/Noodle reconciliation. Never cross from the selected cloud route into shell Git because a local checkout exists. Unknown writes require readback. Never repeat the offered request from model memory.
- For delivery preparation, candidate correction, base drift or interrupted cleanup, use the existing [delivery](.agents/skills/verify-soodles/features/supervised-delivery.md) or [recovery](.agents/skills/verify-soodles/features/delivery-recovery.md) recipe and owning requirement in `contracts/system-v1.md`. Preserve fresh admission and evidence, exact identity, and unknown-write readback obligations. Process-fault oracles use provider fixtures, not live GitHub writes.

## Routing and changes

For Issue implementation, read the exact Issue and its nearest executable
boundary. For analysis or review, start from the requested subject. Do not invent
an Issue prerequisite. When the task concerns behavior or an authority boundary
in `contracts/system-v1.md`, read only the relevant section.

Prefer at most three document nodes, or two link edges: AGENTS → relevant
contract/skill → selected executable boundary/recipe. This convention helps
navigation. It does not limit necessary source or test reads or guarantee model
context. Follow additional causal dependencies when needed. Read
`contracts/agent-context-design.md` only for instruction-design or context-transfer
tasks. Ordinary work does not load it.

One Issue owns one causal correction and one reversible landing boundary.
That scope includes the producers, consumers, adapters, checkpoint migration,
positive and planted-negative controls, and activation needed for the requested
outcome. It bounds ownership, not how much of the outcome to deliver. Do not
split an Issue by helper, file, or implementation step.

Incorrect implementations and tests may be replaced together. Preserve the nearest
controls that distinguish valid from invalid behavior. Different repositories,
durable transition owners, or rollback boundaries require separate admission.
Retain the overall user outcome across those units. Preserve evidence. Stop an
unchanged retry or an unknown write outcome until owner readback arrives.

When the requested delivery unit is one Issue atom, keep its causal correction
and required evidence on one PR. Include evaluator, manifest, and comparison
receipts only when that measurement is selected. One-PR delivery does not itself
request an experiment. A missing required artifact, byte mismatch, or failed
runtime blocks that PR. Correct the defect with a new immutable head on the same
PR. Never rerun an unchanged failed head. Merge only the terminal complete head.
A defect first found after that merge has a new rollback boundary and needs a
new Issue. It cannot retroactively make the earlier delivery a one-PR success.

`docs/` is N-class. It records observations, plans, and receipts in prose.
It never grants correctness authority. Update this file and the system contract
only to the atom's demonstrated scope. Do not copy upstream architecture wholesale.

Never add a second scheduler, worktree manager, retry engine, or Agent-facing authority/policy flag. Repository identity and credentials are not auto-correctable inputs.

Before candidate acceptance, the supervisor selects immutable external verifier
and oracle bytes. Never load the active judge from default-branch tips or candidate
imports. Editing verifier source does not give it authority for its own Issue.
`landing resume` preserves identity under external supervision. It is not
self-authorization. Separate authority changes only when they are independently
owned or reversible.

For runtime-admission, bounded-Issue-execution, supervised-delivery,
delivery-recovery verification, or a bounded P-class behavior/context comparison,
use `.agents/skills/verify-soodles/SKILL.md` and only the relevant feature recipe.
Its receipt is non-authorizing. If that capability is missing, create a verification
skill. Run maintenance only for an explicit map audit or observed recipe drift,
not on every Issue. The existing entries above still own canonical acceptance
and delivery.

To verify Noodle itself, use
[.agents/skills/verify-noodle/SKILL.md](.agents/skills/verify-noodle/SKILL.md) and
its independent feature map. Its scope covers CLI identity and skill resolution,
stopped initial-proposal recovery, and original order/session handoff. Existing
Noodle owners and Soodles acceptance and delivery retain authority.

For downloaded admission-recovery artifacts, use the verify-noodle
[packet route](.agents/skills/verify-noodle/features/admission-recovery.md):
`./soodles packet verify ARCHIVE --expected-carrier linux_amd64` (or
`darwin_arm64` for native macOS evidence). The deterministic tar preserves the
selected source, observers and input, actual process results, and scoped cleanup.
This verifies evidence integrity only, with `authorizes_landing: false`.
Carrier-specific execution requires fresh Noodle `admission inspect`. Never use
historical argv from a receipt. Runtime-lock acceptance remains Linux-only.

## Guarantee classes

Classes describe authority, not confidence or file type (Noodles reference: `d4fa0da322cbb7a581328398906a4f04deaf0a69`).
N records descriptions, inventory and measurements. Measurements support their observed scope. They grant no correctness or effect authority.
P guides reasoning, skill use and routing. An instruction does not prove that an Agent followed it.
L is a tested local discriminator bound to its subject, readback and residue. It may reject locally.
R records provider-enforced truth for the exact check, merge or closure claim.
A successful run does not prove full behavior or local reconciliation.
Guidance and repeated green results cannot promote N/P into L/R.
Keep the selected external judge fixed for its acceptance.
Correct its source or erroneous controls through a fresh supervisor boundary.

For authenticated Issue reads, use `./soodles github issue OWNER/REPOSITORY NUMBER`.
The envelope selects a repository registered by
[cross-repository delivery](.agents/skills/verify-soodles/features/cross-repository-delivery.md).
The [GitHub read recipe](.agents/skills/verify-soodles/features/github-read.md)
owns credential and quota behavior. The supervisor supplies the scoped
installation credential. The shared reader never falls back to anonymous API.
Provider wait is exit 75 with a deadline. It does not permit an identity change
or writer restart. This boundary does not certify the daemon response to adapter
failure or resume a paused comparison.

For cross-repository dependencies, the external supervisor claim owns the exact
edge set. `landing next.requests` is the shortest path. It includes the consumer
readbacks and indexed `dependency_N_*` producer readbacks from that immutable
claim. Supply all returned GETs in one readback. Execute the returned argv
unchanged. A closed producer Issue, cleanup, or order does not establish
eligibility. Do not edit a source registry or add repository, revision, workflow,
or dependency flags. Soodles owns validation semantics. It does not choose,
discover, or complete the DAG.

For known deterministic faults, use declared owner controls. For unknown
behavior, first inspect relevant existing logs, source, and owner readback.
Offline evals apply only to a task-selected Agent behavior measurement.
Uncertainty alone does not request them. New P-class routes or demonstrated
routing drift need scoped source and consumer review and correction. They do
not automatically request an experiment, a full verification-skill pass,
or another runtime gate.
