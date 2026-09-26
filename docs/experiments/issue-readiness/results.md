# Issue #170 implementation-stage results

The original head `a342c1a53c880dfb24b3dcc7e30cec0ce87c6bb5` passed
exact-head runtime and quality Actions. Its positive readiness fixture mocked
`issue_atom.validate_authorization`. A direct call with that fixture instead
refused `authorization.fields` before materialization: the read-only operation
required a full local Issue lifecycle authorization that the portable handoff
did not supply. The old green test therefore did not prove its claimed positive
path.

The corrected local candidate consumes the externally byte-bound carrier in
`LOCAL.json` and leaves launch authorization with the supervisor. A real
`./soodles issue readiness` invocation reaches `READY` and emits six packets;
wrong local origin, missing/foreign carrier, wrong head, dirty workdir,
changed selected input, missing case, stale evidence destination and unsafe
output root refuse before materialization. Focused local controls passed 10/10
on macOS. These are deterministic L-class results, not behavioral improvement.

The first published integration head `bccc36e43d2dc29aa1771d1b86d15b3827916baa`
failed runtime candidate verification before acceptance: the manifest still
pinned the instruction baseline SHA-256 from the old base. The current main
instruction bytes have SHA-256
`a7414971e64640d6fd6ff948ed6331093d9dc741b705d3b274aba4c8bacf6a4f`.
The manifest now binds that actual base; the failed head is preserved and must
not be rerun.

The first baseline pilot at candidate `28bfccb7e517771cc52b6695507a4a44a4c5e167`
exposed the scoring observer and selection file to the consumer through the
handoff input directory. Its raw capture remains outside the repository, but
it is excluded from the comparison. Readiness now excludes the scoring
observer from consumer-visible handoff and packets. A new six-session selection
will be fixed before the behavior comparison begins.

The replacement selection has SHA-256
`6ed0f46a505a38c2921b8cc4741c11946788e99636102ced966bdd1d2ff1be27`;
the supervisor observer has SHA-256
`11db7ca52ce189293c31191c875f0bd5855fb95d107d9dcddc6673ee43e70b46`.
Six fresh Local Codex CLI JSONL sessions used the same executable, model and
sandbox with clean exact baseline `429eb5b5b814099bb7a631ad76e7c80fdffede2d`
and treatment `36e28da3fef5998fb5817aadd53e9b7f28ad5ac8` sources.
Distinct thread IDs, actual command results, process exits, final messages and
materialized packet files are preserved in `comparison-evidence.tar.gz`.

The frozen observer returned `VALID/BOUNDED_IMPROVEMENT`. For cases A/B/C,
baseline reconstruction burden was 43/31/22; treatment was 0/0/0. Each
treatment's first command invoked the exact supplied readiness CLI and produced
six packets. Every baseline stayed BLOCKED without a packet. The compact
machine-readable results are in `comparison-summary.json`. This supports the
bounded pre-run-1 `avoidable_dependency_reconstruction` claim for these six
Local Codex sessions. It does not establish a ChatGPT native cloud result,
general model reliability or completed replay behavior. The observer report is
non-authorizing. Final exact-head Actions and landing remain separate gates.
