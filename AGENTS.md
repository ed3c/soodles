# soodles

Migrate only exact, executable claims demonstrated in this repository.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. This bootstrap exercises its binary in disposable fixtures; it does not start a production daemon.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- `./soodles acceptance verify /absolute/path/to/noodle` is the canonical local acceptance. Run focused controls while editing, then acceptance once for each final clean candidate head.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot select or authorize their own verifier.
- First installation uses the explicitly requested supervised fallback: the supervisor pins the landing implementation outside the candidate, admits one exact claim, and supplies raw provider readbacks. `landing.py` owns pending-write checkpoints and exact requests; the existing GitHub connector executes them under existing provider rules. No Administration access or protection-policy modification is a prerequisite.
- Do not fabricate a production generation, independent default-branch verification, or unattended lander. An Issue is RESOLVED only after merge and closure readback plus Noodle reconciliation. Unknown writes require readback; never repeat the offered request from model memory.

## Routing and changes

Read the exact Issue, then its nearest executable test. Read `contracts/system-v1.md` only for the claim/authority boundary. At most three document nodes: AGENTS → system contract when needed → Issue-selected executable boundary.

One Issue owns one causal correction and one reversible landing boundary, including its producers, consumers, adapters, checkpoint migration and positive/planted-negative controls. Do not split by helper, file or implementation step. Incorrect implementations and tests may be replaced together while preserving the nearest discriminating controls. Different repositories, durable transition owners or rollback boundaries require separate admission. Preserve evidence and stop an unchanged retry or unknown write outcome pending owner readback.

`docs/` is N-class: observations, plans and receipts described in prose, never correctness authority. Update this file and the system contract only to the atom's demonstrated scope. Do not copy upstream architecture wholesale.

Never add a second scheduler, worktree manager, retry engine, or Agent-facing authority/policy flag. Repository identity and credentials are not auto-correctable inputs.

The supervisor selects immutable external verifier/oracle bytes before candidate acceptance. Never load the active judge from default-branch tips or candidate imports. Editing verifier source does not promote it into authority for its own Issue; `landing resume` is an identity-preserving operation under external supervision, not self-authorization. Separate authority changes only when they are independently owned or reversible.
