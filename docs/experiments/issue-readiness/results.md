# Issue #170 implementation-stage results

Candidate implementation adds one readiness operation under the existing
`soodles issue` family and no scheduler/runner/landing authority.

At commit construction time, provider exact-head Actions and the required fresh
consumer behavior comparison have not yet been observed. Deterministic controls
are carried in `tests/test_issue_readiness.py`; their provider execution must be
read back before any test-success claim.

The intended L-class result is:
- invalid/missing/foreign dependencies refuse before materialization;
- a complete fixture produces exactly six immutable packets/argv;
- no model or provider operation occurs in readiness.

The P-class claim remains pending until a fresh treatment consumer reaches the
first-runnable-run boundary without reconstructing owner/ref/workdir/packet/argv
and the frozen observer reports the predeclared barrier. No 0->0 result may be
reported as improvement.
