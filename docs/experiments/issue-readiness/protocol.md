# Issue #170: portable experiment handoff -> local readiness

This atom removes one observed operational decision barrier: a local consumer
must not reconstruct owner/authorization, refs/workdirs, run membership, packets
or replay argv from prose. The external supervisor selects two immutable inputs:
a portable experiment handoff and one host-local binding.

The existing `issue_execution` owner exposes `./soodles issue readiness`.
It validates byte bindings, Issue-scoped authorization, exact clean baseline and
treatment workdirs, selected observer/capture/task/case inputs, executable
identity and external evidence/output roots. It performs no network/model call
and creates no worktree.

A complete input materializes exactly three cases x two arms = six packet files.
Each packet contains an exact replay argv and immutable input/workspace bindings.
A refusal is typed and names the owning missing input. READY grants no model,
provider or landing authority; the supervisor still owns fresh-consumer launch.

P-class guidance consumes READY/BLOCKED unchanged. It must not search history,
borrow another Issue's resources, choose refs, create workdirs, construct
packets or reconstruct argv.

Deterministic controls cover legal six-run materialization, foreign/missing
authorization, wrong ref/dirty workdir, selected-input digest mismatch,
case-membership mismatch, unsafe external-state roots and malformed CLI input.

Behavior claim remains separate. A fresh consumer comparison must measure
`avoidable_dependency_reconstruction` at the boundary before run 1. Missing
telemetry is INCONCLUSIVE; unit tests do not establish model behavior improvement.
