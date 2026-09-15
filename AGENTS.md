# soodles

Migrate only exact, executable claims demonstrated in this repository.

## Current boundary

- Noodle owns worktrees and runtime lifecycle. This bootstrap exercises its binary in disposable fixtures; it does not start a production daemon.
- `policy/runtime.lock.json` owns the selected release and digests. `./soodles --help` owns the command surface.
- `./soodles acceptance verify /absolute/path/to/noodle` is the canonical local acceptance. Run focused controls while editing, then acceptance once for each final clean candidate head.
- Local and PR self-test receipts have `authorizes_landing: false`. They cannot supply trusted provider admission, merge, Issue closure, or production reconciliation.
- This first bootstrap has no installed guarded Issue authoring, execution-envelope issuer, or trusted lander. Keep the exact Issue and PR open until their missing authority is established and read back. Never fabricate those capabilities or use a direct merge as a substitute.

## Routing and changes

Read the exact Issue, then its nearest executable test. Read `contracts/system-v1.md` only for the claim/authority boundary. At most three document nodes: AGENTS → system contract when needed → Issue-selected executable boundary.

One Issue owns one causal correction and one reversible landing boundary, including its producers, consumers, adapters and positive/planted-negative controls. Different repositories, durable transition owners or rollback boundaries require separate admission. Preserve evidence and stop an unchanged retry or unknown write outcome pending owner readback.

`docs/` is N-class: observations, plans and receipts described in prose, never correctness authority. Update this file and the system contract only to the atom's demonstrated scope. Do not copy upstream architecture wholesale.

Never add a second scheduler, worktree manager, retry engine, or Agent-facing authority/policy flag. Repository identity and credentials are not auto-correctable inputs.
