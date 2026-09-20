# Issue #89 — candidate evidence binding

## Decision

The bounded delivery decision barrier decreased from **2 to 0**.

The base entry admitted both invalid candidates:

- required evidence absent;
- manifest treatment digest different from candidate prompt bytes.

The proposed entry refuses them as
`candidate.missing_required_paths` and
`candidate.instruction.treatment_sha256`. The complete candidate passes.
Legacy schema 1 also passes as a scoped compatibility non-case.

## Frozen identities

- base: `de7b07b99e7879d54fda99e8166cc2aa782e04cc`
- observer SHA-256: `19c01cb1b4de51c20c3d9d0275e40633ae2a801d78d4d20f0e027c24be452ae7`
- baseline prompt SHA-256: `dd8fb2ef1f296655f7f79cf8581a1129a6543e6bbc7afe0205db1b1732533498`
- treatment prompt SHA-256: `55c600b7b2bc5627f3d46897bdffff7793fe0ae95ca44304f002d0a16a0a2a05`
- baseline raw SHA-256: `5d70253733fbabd8d4a99710303b7f505e5c6f99a7129e8bf548e4b43bd572a6`
- treatment raw SHA-256: `323256fc1d5ce036476644fde26cf35118a1b479b890f83922ccbda92afc56f5`
- schema 1 non-case SHA-256: `0931c270427e4a454f3ce52173fb0857db81e5f362bb9cc420b0070701a07501`

## Scope

This establishes candidate completeness and byte binding at
`issue_admission.validate_delivery_paths`. It does not prove hidden instruction
reads, general prompt quality, every N/P/L/R atom, or provider policy. The
P-class change and all listed N-class evidence must appear in one PR diff. The
manifest binds content; exact-head CI and provider readback bind the terminal
candidate.
