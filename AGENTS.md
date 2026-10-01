# soodles

Migrate only exact, executable claims demonstrated in this repository.

## Session entry — select once, then act

Read this file at the task's selected repository ref when entering Soodles; a cloud Session fetches it through GitHub. Use the task's currently admitted ref for Issue/PR work; neither main nor a historical PR head necessarily contains its selected instructions. Use current task/tool/owner evidence to select the path below and proceed within existing authorization without asking the user to choose it again. When the task already supplies a selected recipe, read it at its selected ref directly; do not rediscover it through the full feature map. This file's presence does not prove that the host loaded it.

| Observed execution path | Shortest supported action |
| --- | --- |
| ChatGPT Session using GitHub connector / Actions | Read the exact Issue/PR/head and `.github/workflows/runtime.yml`; consume the matching runtime run, job steps and artifact evidence through GitHub. Authorized PR creation/update triggers the existing workflow. For an unchanged head, reuse its result or observe its in-flight run; do not launch Codex CLI or install a scratch Noodle. |
| Local Session explicitly authorized to execute an Issue atom | Use the [issue-atom skill](.agents/skills/issue-atom/SKILL.md) and the local entry forms below, according to the current authorization state. |
| Local Soodles → Noodle → Codex child | Use the supplied local control root, admitted launcher/envelope and Noodle owner; load only the [bounded execution recipe](.agents/skills/verify-soodles/features/issue-execution.md). Confirm the actual child's Codex CLI capability there, then observe its session/order/stage outcome. Do not reconstruct launcher argv. |

For that explicitly authorized Local Session, the existing entry forms are:

```text
[PYTHON, "-B", SUPERVISOR_ADMISSION, "authorize", SELECTION_JSON, SELECTION_SHA256, NEW_EXTERNAL_OUTPUT]
[ISSUE_ATOM, "run", AUTHORIZATION_JSON]
```

These are argv templates: use the current supplied absolute Python interpreter and entry paths, exact selected file bytes/digests, and a new absolute output directory outside the control root. `supervisor-admission` is Python; `issue-atom` is a shell executable invoked directly, never through Python.

Before initial authorization selection, the authorized Session may act as supervisor: prepare the explicit selection and its SHA-256 using the [authorization recipe](.agents/skills/verify-soodles/features/local-supervisor-admission.md), then use `authorize`. The producer derives the authorization path/digest and validated continuation; do not ask the user to create those files or hashes. Its lower-level `prepare` verb belongs to the lifecycle. On `status=prepared`, preserve the receipt and use its `next.argv` and `next.environment` unchanged for authorized lifecycle execution; the latter binds `SOODLES_AUTHORIZATION_SHA256`. Respect the task's stopping point: if it requests preparation or the first non-help receipt only, save that receipt and hand off `next` without executing it.

Once authorization is selected, preserve that exact identity and the existing `issue-atom run` continuation. A missing selected file requires its owner's recovery of the exact bytes, never another `authorize`. Missing selected identity/capability or credentials requires the named owner input; retain the refusal and unchanged continuation, and re-enter only after the required material change. Do not guess credentials, select replacement authority or let a candidate writer select its judge. These forms remove entry ambiguity; they do not replace required validation, receipts or owner readback.

After a local child is parked with a completed typed outcome, the supervisor
uses Noodle's exact publication claim and the native publication-readiness
receipt (or canonical acceptance receipt) via
the [candidate-publication skill](.agents/skills/candidate-publication/SKILL.md).
That entry owns push/readback/PR identity; the Agent never reconstructs them.
Native readiness permits publication only. Linux exact-head Actions acceptance
still precedes landing; the local external landing owner emits merge/closure
requests and owns reconciliation. CI need not hold merge authority.

Local runtime tests that launch no Codex child need no Codex CLI. A cloud Session does not inherit local-launcher requirements because a CLI binary happens to exist. If ownership is unknown, inspect the next operation's owner; only unresolved identity/authority requires clarification.

For authorized independent cloud work or context-transfer verification, use the platform's native subagent tool through its current exposed schema. If exposure is unknown, use applicable scoped capability discovery; incomplete discovery remains unknown. Confirmed absence applies to this Session, not the product. Missing freshness or recording blocks only the affected comparison. Preserve the selected carrier: a capability gap does not authorize proposing or constructing a replacement runner. An alternative needs an explicit authorized selection and separate comparison conditions. When requirements are met, proceed without asking again. Start each consumer without inherited conversation (`fork_turns: "none"` where the current schema supports it); pass only the task, pinned instruction/code refs and required inputs. Keep expected outcomes with the supervising observer. Native threads share files, so use distinct evidence directories and pinned read-only GitHub inputs; a branch or worktree does not isolate model context. Use a Noodle-owned worktree only when the task needs source writes. Record actual tool requests/results as they occur, and distinguish consumer-recorded evidence from a complete platform transcript. Browser login and Codex CLI are not prerequisites for this path. Delegate only within current user/platform authorization; if the native tool is absent, report that specific capability gap and continue other authorized work.

Retain the selected path and its evidence in the existing task handoff: repo/ref, Issue/PR/head, carrier/reason, run/attempt or local owner/session/checkpoint, and next required readback. Refresh mutable owner/provider state on resume; reselect only when execution ownership changes. A new Session refreshes relevant capability observations rather than inheriting a previous Session's absence claim; an unchanged turn is not a new preflight. No new flag, state file or repeated preflight is required. Scratch `environment_offline` blocks only dependent scratch operations. Missing capabilities block their own operation, not the other path. Consume current owner `next`/`request`; never replay historical writes.

### Terminal candidate delivery entry

When the supplied provider snapshot already identifies one exact-head successful terminal candidate and the supervisor has selected immutable external publisher bytes plus the Cloud/Local route, run the repository `landing-supervisor` entry with those supplied inputs and a new external output directory. Consume the returned current landing-owner `next` exactly; its checkpoint, readback and argv paths must name that final output directory. Do not search repository history for another publisher, derive authority from latest/default branch, assemble a landing claim or checkpoint in the Agent, or choose `start`/`advance`/`dispatch` from prose. A refusal names the missing supervisor/provider input; it is not permission to substitute historical identity.

## Task scope and completion

Within the current task's authorization, continue through necessary inspection, local correction and relevant checks. Existing disposable local controls may run without a new approval at each step. Finish an analysis/review with findings; finish an implementation with its requested artifact and evidence. A delivery task continues through the existing supervised owner to its requested terminal state. A blocked effect does not prevent unrelated authorized read-only work.

For an observed defect, preserve its actual owner/process/readback evidence and
use the admitted contract's declared controls at the nearest executable boundary.
The existing atom consumes a finite pinned repair policy; the model does not
classify retryability or choose a recovery verb. Missing lineage, conflicting
identity, exhausted budget and unknown effects stop the affected repair branch.
Use `./system-context entry issue-atom run` (or `soodles candidate publish` /
`provider-readback consume`) for committed consumer/decision P-class requirements.
Consume current owner `next`/`request` unchanged; these selections grant no effects.

A fresh Agent comparison or evals skill is required only when the admitted task
selects that measurement. For such a claim, use the scoped
[behavior comparison procedure](.agents/skills/verify-soodles/features/pclass-context.md).
Product controls and instruction source hashes do not establish Agent behavior
improvement. Preserve historical evidence and report unsupported claims explicitly.

Stop the affected operation when its owner requires missing identity, credentials, admission, capability or readback. Report that exact prerequisite and preserve evidence. Prior user authorization remains applicable, but it does not create a missing executable capability or let the candidate select its own judge.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. This bootstrap exercises its binary in disposable fixtures; it does not start a production daemon.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- The [Test Manager](.agents/skills/test-manager/SKILL.md) is the single P-class owner of verification scope. Local CLI, canonical CI and other skills consume its decision from `test_manager.py`; they never independently append a full-suite run. Inspect the actual changed behavior and request only its necessary controls. Full coverage is explicit demand, never a prediction or fallback for a shared file, missing base, unknown change or failure. Scope gaps are work for the current Agent, not an automatic human handoff. Preserve exact-head provider evidence and external landing authority; compare costs through normal execution logs.
- Normal PR acceptance, additional runtime verification and optional full-repository quality observation follow the Test Manager's CI demand routing. A merge or completed workflow does not independently request another regression run or full quality scan. Consume existing landing readbacks; never relabel a PR result as main-head execution.
- Keep `tests/` focused on current behavior and distinct failure boundaries. Use small disposable fixtures; do not copy the repository or rerun historical implementations/reports in routine acceptance. Historical evidence stays under `docs/`; replacing a replay must retain any unique current behavior controls. Frozen external verifier bytes and their authority are unchanged by test maintenance.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot select or authorize their own verifier.
- For a user-authorized local Issue lifecycle, the supervising Session prepares the external authorization and digest through the [issue-atom skill](.agents/skills/issue-atom/SKILL.md); missing generated files are not a human handoff prerequisite. Ordinary edits do not require an atom. Once prepared, use only `./issue-atom run /absolute/authorization.json` and re-enter its returned same command after material state changes. Never reconstruct `./noodles issue handoff`, select an Issue/landing verb, or retry an unknown provider write.
- First installation uses the explicitly requested supervised fallback: the supervisor pins the landing implementation outside the candidate, admits one exact claim, and supplies raw provider readbacks. `landing.py` owns pending-write checkpoints and exact requests; the existing GitHub connector executes them under existing provider rules. No Administration access or protection-policy modification is a prerequisite.
- Do not fabricate a production generation, independent default-branch verification, or unattended lander. A cloud Issue is RESOLVED only from exact merge, closure, runtime and provider-main readback through the connector; a local Issue additionally requires Git/Noodle reconciliation. Never cross from the selected cloud route into shell Git because a local checkout exists. Unknown writes require readback; never repeat the offered request from model memory.
- For delivery preparation, candidate correction, base drift or interrupted cleanup, use the existing [delivery](.agents/skills/verify-soodles/features/supervised-delivery.md) or [recovery](.agents/skills/verify-soodles/features/delivery-recovery.md) recipe and owning requirement in `contracts/system-v1.md`. Preserve fresh admission/evidence, exact identity and unknown-write readback obligations; process-fault oracles use provider fixtures, not live GitHub writes.

## Routing and changes

For Issue implementation, read the exact Issue and its nearest executable boundary. For analysis or review, start from the requested subject; do not invent an Issue prerequisite. Read only the relevant `contracts/system-v1.md` section when the task concerns its behavior or authority boundary.

Prefer a route of at most three document nodes (two link edges): AGENTS → relevant contract/skill → selected executable boundary/recipe. This is a navigation convention, not a cap on necessary source/test reads or a model-context guarantee. Follow additional causal dependencies when needed. Only instruction-design/context-transfer tasks read `contracts/agent-context-design.md`; ordinary work does not load it.

One Issue owns one causal correction and one reversible landing boundary, including its producers, consumers, adapters, checkpoint migration and positive/planted-negative controls. Do not split by helper, file or implementation step. Incorrect implementations and tests may be replaced together while preserving the nearest discriminating controls. Different repositories, durable transition owners or rollback boundaries require separate admission. Preserve evidence and stop an unchanged retry or unknown write outcome pending owner readback.

When the requested delivery unit is one Issue atom, keep its prompt or contract correction, evaluator, manifest, raw receipts and results on one PR. A missing artifact, byte mismatch or failed runtime blocks that PR; correct it with a new immutable head on the same PR and never rerun an unchanged failed head. Merge only the terminal complete head. A defect first discovered after that merge has a new rollback boundary and requires a new Issue; it cannot retroactively make the earlier delivery a one-PR success.

`docs/` is N-class: observations, plans and receipts described in prose, never correctness authority. Update this file and the system contract only to the atom's demonstrated scope. Do not copy upstream architecture wholesale.

Never add a second scheduler, worktree manager, retry engine, or Agent-facing authority/policy flag. Repository identity and credentials are not auto-correctable inputs.

The supervisor selects immutable external verifier/oracle bytes before candidate acceptance. Never load the active judge from default-branch tips or candidate imports. Editing verifier source does not promote it into authority for its own Issue; `landing resume` is an identity-preserving operation under external supervision, not self-authorization. Separate authority changes only when they are independently owned or reversible.

For runtime-admission, bounded-Issue-execution, supervised-delivery, delivery-recovery verification or a bounded P-class behavior/context comparison, use `.agents/skills/verify-soodles/SKILL.md` and only the relevant feature recipe. Its receipt is non-authorizing. Create a verification skill when that capability is missing; run maintenance for an explicit map audit or observed recipe drift, not on every Issue. Canonical acceptance and delivery remain owned by the existing entries above.

For verification of Noodle itself (CLI identity/skill resolution, stopped initial-proposal recovery, or original order/session handoff), use [.agents/skills/verify-noodle/SKILL.md](.agents/skills/verify-noodle/SKILL.md) and its independent feature map; existing Noodle owners and Soodles acceptance/delivery retain authority.

Downloaded admission-recovery artifacts use the verify-noodle
[packet route](.agents/skills/verify-noodle/features/admission-recovery.md):
`./soodles packet verify ARCHIVE --expected-carrier linux_amd64` (or
`darwin_arm64` for native macOS evidence). The deterministic tar preserves the
selected source, observers/input, actual process results and scoped cleanup.
This verifies evidence integrity only, with `authorizes_landing: false`;
carrier-specific execution requires fresh Noodle `admission inspect`, never
historical argv from a receipt. Runtime-lock acceptance remains Linux-only.

## Guarantee classes

Classes describe authority of a claim, not confidence or file type (Noodles reference: `d4fa0da322cbb7a581328398906a4f04deaf0a69`). N describes inventory/prose/metrics and proves nothing. P guides model reasoning, skill use and routing; it cannot grant correctness authority. L is a tested executable local discriminator bound to its subject/readback/residue; it may reject locally. R is provider-enforced check/merge/closure truth for the exact provider claim. A run's success does not prove full behavior or local reconciliation. Guidance or repeated green results cannot promote N/P into L/R. The selected external judge remains fixed for this acceptance; its source and erroneous controls remain correctable under a fresh supervisor boundary.

For authenticated Issue reads, use `./soodles github issue OWNER/REPOSITORY NUMBER`.
The envelope selects a repository registered by
[cross-repository delivery](.agents/skills/verify-soodles/features/cross-repository-delivery.md);
the [GitHub read recipe](.agents/skills/verify-soodles/features/github-read.md)
owns credential and quota behavior.
The supervisor supplies the scoped installation credential; the shared reader
never falls back to anonymous API. Provider wait is exit 75 with a deadline,
not permission to change identity or restart a writer. This boundary does not
certify the daemon response to adapter failure or resume a paused comparison.

For cross-repository dependencies, the external supervisor claim owns the
exact edge set. `landing next.requests` is the shortest path and includes the
consumer readbacks plus indexed `dependency_N_*` producer readbacks derived
from that immutable claim. Supply all returned GETs in one readback and execute
the returned argv unchanged. A closed producer Issue, cleanup or order is not
eligibility. Do not edit a source registry or add repository, revision,
workflow or dependency flags. Soodles owns validation semantics; it does not
choose, discover or complete the DAG.

Known deterministic faults use declared owner controls. Unknown behavior requests
scoped offline evals evidence; it does not add a runtime gate. New P-class routes
or demonstrated routing drift require scoped architecture/verification-skill
maintenance, not a prescribed Noodle/pstack reasoning DAG or full map audit.
