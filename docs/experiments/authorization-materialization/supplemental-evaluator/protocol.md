# Supplemental root and lifecycle entry discriminator

This is a separately pinned supplement for the source review finding against
candidate `f6ac0fc22d1e66c676089a538ba49f6fd8a3807c`. It does not modify the original
external oracle, its manifest, or the behavioral comparison/adoption conditions.

The script verifies all original frozen dependencies against the pinned manifest
before loading only the original fixture/snapshot/hash/Git helpers. It executes
the candidate solely through the public `python3 -B supervisor-admission authorize`
CLI, under the original no-network/read-only-Git guard, and never runs continuation.

The three required refusals are:

1. An otherwise valid selection points control_root to an existing Git subdirectory.
2. The correct control_root has no issue-atom entry in its committed clean base.
3. The correct control_root has a committed, nonexecutable issue-atom entry.

Cases 2 and 3 create a fresh fixture commit and update only the selected Issue
contract base accordingly, so dirty-root rejection cannot satisfy the control.
Every case starts with a clean fixture and requires typed nonzero refusal,
invalid field, corrected-input continuation, authorizes_landing false, absent
output, no effect attempt, and byte-identical before/after snapshots.
Raw process argv/exit/stdout/stderr and differences are saved outside each fixture.

Run `python3 -B discriminator.py SUBJECT_ROOT NEW_EXTERNAL_EVIDENCE_DIR`.
The supervisor must receive this script's frozen digest before product edits.
The pre-correction r02 run should be RED: it currently accepts the invalid
selection and emits a prepared receipt with an unusable lifecycle continuation.
This RED is a deterministic source defect observation, not model behavior evidence.
