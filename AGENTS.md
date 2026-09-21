# soodles

Migrate only exact, executable claims demonstrated in this repository.

## Session entry — select once, then act

Read this file at the task's selected repository ref when entering Soodles; a cloud Session fetches it through GitHub. Use the task's currently admitted ref for Issue/PR work; neither main nor a historical PR head necessarily contains its selected instructions. Use current task/tool/owner evidence to select the path below and proceed within existing authorization without asking the user to choose it again.

| Observed execution path | Shortest supported action |
| --- | --- |
| ChatGPT Session using GitHub connector / Actions | Read the exact Issue/PR/head and `.github/workflows/runtime.yml`; consume the matching runtime run, job steps and artifact evidence through GitHub. Authorized PR creation/update triggers the existing workflow. For an unchanged head, reuse its result or observe its in-flight run; do not launch Codex CLI or install a scratch Noodle. |
| Local Soodles → Noodle → Codex child | Use the supplied local control root, admitted launcher/envelope and Noodle owner; load only the [bounded execution recipe](.agents/skills/verify-soodles/features/issue-execution.md). Confirm the actual child's Codex CLI capability there, then observe its session/order/stage outcome. Do not reconstruct launcher argv. |

Local runtime tests that launch no Codex child need no Codex CLI. A cloud Session does not inherit local-launcher requirements because a CLI binary happens to exist. If ownership is unknown, inspect the next operation's owner; only unresolved identity/authority requires clarification.

For a cloud task requiring independent Agent work or context-transfer verification, use the platform's native subagent tool when available. Start each consumer without inherited conversation (`fork_turns: "none"` on the current tool); pass only the task, pinned instruction/code refs and required inputs. Keep expected outcomes with the supervising observer. Native threads share files, so use distinct evidence directories and pinned read-only GitHub inputs; a branch or worktree does not isolate model context. Use a Noodle-owned worktree only when the task needs source writes. Record actual tool requests/results as they occur, and distinguish consumer-recorded evidence from a complete platform transcript. Browser login and Codex CLI are not prerequisites for this path. Delegate only within current user/platform authorization; if the native tool is absent, report that specific capability gap and continue other authorized work.

Retain the selected path and its evidence in the existing task handoff: repo/ref, Issue/PR/head, carrier/reason, run/attempt or local owner/session/checkpoint, and next required readback. Refresh mutable owner/provider state on resume; reselect only when execution ownership changes. No new flag, state file or repeated preflight is required. Scratch `environment_offline` blocks only dependent scratch operations. Missing capabilities block their own operation, not the other path. Consume current owner `next`/`request`; never replay historical writes.

## Task scope and completion

Within the current task's authorization, continue through necessary inspection, local correction and relevant checks. Existing disposable local controls may run without a new approval at each step. Finish an analysis/review with findings; finish an implementation with its requested artifact and evidence. A delivery task continues through the existing supervised owner to its requested terminal state. A blocked effect does not prevent unrelated authorized read-only work.

Stop the affected operation when its owner requires missing identity, credentials, admission, capability or readback. Report that exact prerequisite and preserve evidence. Prior user authorization remains applicable, but it does not create a missing executable capability or let the candidate select its own judge.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. This bootstrap exercises its binary in disposable fixtures; it does not start a production daemon.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- `./soodles acceptance verify /absolute/path/to/noodle` is the canonical acceptance on the selected runner. Run focused controls while editing, then acceptance once for each final clean candidate head.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot select or authorize their own verifier.
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
