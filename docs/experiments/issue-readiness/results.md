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

The P-class claim remains pending until fresh baseline and treatment consumers
reach the boundary before run 1 with actual command/read/clarification capture.
The fixed observer must report `avoidable_dependency_reconstruction`; missing
telemetry is INCONCLUSIVE and 0-to-0 is nonregression, not improvement. This
candidate has not been published or accepted on a new exact head.
