# soodles

Migrate only exact, executable claims demonstrated in this repository.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. This bootstrap exercises its binary in disposable fixtures; it does not start a production daemon.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- `./soodles acceptance verify /absolute/path/to/noodle` is the canonical local acceptance. Run focused controls while editing, then acceptance once for each final clean candidate head.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot select or authorize their own verifier.
- First installation uses the explicitly requested supervised fallback: the supervisor pins the landing implementation outside the candidate, admits one exact claim, and supplies raw provider readbacks. `landing.py` owns pending-write checkpoints and exact requests; the existing GitHub connector executes them under existing provider rules. No Administration access or protection-policy modification is a prerequisite.
- Do not fabricate a production generation, independent default-branch verification, or unattended lander. An Issue is RESOLVED only after merge and closure readback plus Noodle reconciliation. Unknown writes require readback; never repeat the offered request from model memory.
- Consume the invoked landing owner's `next` projection. Missing claim/readback/binary inputs are explicit; never invent argv or replay a historical next command. Dispatch returns an exact connector payload in `request`; only that payload is transported. Terminal `next` is null.
- `landing advance` prepares delivery; `landing dispatch` consumes it once using fresh owner readback before emitting the connector request. Resume prepared work through that same entry; offered/legacy-unknown writes stay pending. The process-fault oracle uses provider fixtures, not live GitHub writes.
- Before correcting an admitted but unoffered candidate, the supervisor uses `landing invalidate CHECKPOINT`. Amend the same causal Issue and its write boundary before further edits; replace or delete incorrect tests/gates with the nearest meaningful controls. Re-admit a changed head with fresh exact-head evidence through `landing readmit`, even when base is unchanged. Green CI is evidence for that admission only; it never means merge, closure or reconciliation. Offered/legacy unknown writes cannot be invalidated into another attempt.
- Coherent forward base drift before an offer produces a durable `readmission_pending` checkpoint and `landing readmit --help` next action. Supply an explicit fresh supervisor claim, exact-head successful runtime evidence and complete provider ancestry comparisons. Preserve the same owner/Issue/PR/worktree/verifier. Old acceptance stays invalidated; offered/legacy unknown writes cannot use this recovery to retry.

## Routing and changes

Read the exact Issue, then its nearest executable test. Read `contracts/system-v1.md` only for the claim/authority boundary. At most three document nodes: AGENTS → system contract when needed → Issue-selected executable boundary.

One Issue owns one causal correction and one reversible landing boundary, including its producers, consumers, adapters, checkpoint migration and positive/planted-negative controls. Do not split by helper, file or implementation step. Incorrect implementations and tests may be replaced together while preserving the nearest discriminating controls. Different repositories, durable transition owners or rollback boundaries require separate admission. Preserve evidence and stop an unchanged retry or unknown write outcome pending owner readback.

`docs/` is N-class: observations, plans and receipts described in prose, never correctness authority. Update this file and the system contract only to the atom's demonstrated scope. Do not copy upstream architecture wholesale.

Never add a second scheduler, worktree manager, retry engine, or Agent-facing authority/policy flag. Repository identity and credentials are not auto-correctable inputs.

The supervisor selects immutable external verifier/oracle bytes before candidate acceptance. Never load the active judge from default-branch tips or candidate imports. Editing verifier source does not promote it into authority for its own Issue; `landing resume` is an identity-preserving operation under external supervision, not self-authorization. Separate authority changes only when they are independently owned or reversible.

For runtime/delivery verification or a bounded P-class behavior/context comparison, use `.agents/skills/verify-soodles/SKILL.md` and its feature recipe. Its receipt is non-authorizing. Create a verification skill when that capability is missing; run maintenance for an explicit map audit or observed recipe drift, not on every Issue. Canonical acceptance and delivery remain owned by the existing entries above.

For verification of Noodle itself (CLI identity/skill resolution, stopped initial-proposal recovery, or original order/session handoff), use [.agents/skills/verify-noodle/SKILL.md](.agents/skills/verify-noodle/SKILL.md) and its independent feature map; existing Noodle owners and Soodles acceptance/delivery retain authority.

## Guarantee classes

Classes describe authority of a claim, not confidence or file type (Noodles reference: `d4fa0da322cbb7a581328398906a4f04deaf0a69`). N describes inventory/prose/metrics and proves nothing. P guides model reasoning, skill use and routing; it cannot grant correctness authority. L is a tested executable local discriminator bound to its subject/readback/residue; it may reject locally. R is provider-enforced check/merge/closure truth for the exact provider claim. A run's success does not prove full behavior or local reconciliation. Guidance or repeated green results cannot promote N/P into L/R. The selected external judge remains fixed for this acceptance; its source and erroneous controls remain correctable under a fresh supervisor boundary.

For authenticated Issue reads, use `./soodles github issue NUMBER` and the
verify-soodles [GitHub read recipe](.agents/skills/verify-soodles/features/github-read.md).
The supervisor supplies the scoped installation credential; the shared reader
never falls back to anonymous API. Provider wait is exit 75 with a deadline,
not permission to change identity or restart a writer. This boundary does not
certify the daemon response to adapter failure or resume a paused comparison.
