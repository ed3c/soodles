# Selected design: atomic complete publication, same-command readback

Status: design selected, not implemented or accepted. Source 51821b935424a4697e2534a9f15b068620510025; fresh provider main matched this source. No product file modified, no Issue created.

## Promise and commit point
The supported final output is the only publication and identity commit point.
Build and validate the complete authorization, exact prepared receipt with final
paths, and selection binding in one private staging directory. Fsync the files
and directory. Then publish the directory with an OS no-replace atomic rename
and sync its parent. Never provide or consume staging continuation paths.
Precommit bytes are uncommitted proposals, not selected execution identity.
The Issue contract already fixes the base. Completed publication fixes host-config,
instruction, carrier, and owner bytes. Reentry never derives them again from
current state.

The existing authorize public argv remains unchanged. If the target is absent,
there is no committed output at this selected location. Prepare the originally
selected operation there. If the target is complete and matches, permit only
immutable readback. If the target is foreign, corrupt, partial, legacy without
binding, a symlink, or selection-mismatched, preserve it and refuse.
There is no new-output fallback, cleanup of unknown paths, lifecycle call,
authority flag, or scheduler. Missing authorization from an already committed
bundle causes refusal. Do not reconstruct it from current selection.

## Why B-prime
A creates a binding before authorization and can repair later receipt publication.
However, a crash with only the binding or an empty directory still needs manual
recovery. A therefore does not meet the stronger complete process-crash boundary.
B's original sibling full record fixes more points but adds a second commitment
and retention location. B-prime combines identity commit with namespace publication.
That removes both the visible partial state and the sibling record.
Native exclusive rename is necessary because ordinary rename can replace a foreign
empty directory. The actual Mac capability probe confirms success for an absent
target. Empty, nonempty, and symlink targets return EEXIST with the inode preserved.
Linux still requires an actual acceptance test. This probe does not prove Linux behavior.

## Boundary and compatibility
Readback proves the stored preparation, not live execution readiness.
The next fresh consumer follows the exact issue-atom argv/environment.
That owner rechecks mutable head, config, capability, checkpoint, and provider
state. Do not turn the producer into an effect owner or return a fabricated
terminal state.
Legacy partial output remains a named original-owner recovery requirement.
This atom prevents new reachable partial publication. It cannot invent missing
past commitments. Existing legacy complete receipt handoffs remain usable through
their original trusted next. Keep this limit in the cases and results. Do not
count it as repaired.

## Minimal implementation
- supervisor_admission.py: private no-replace publish helper (Darwin/Linux only, precise refusal on unsupported primitive), complete staging publication and strict matching-bundle readback; preserve existing authorization schema and exact prepared next.
- tests/test_supervisor_authorization.py: real child process kills across staging/final publication, complete readback, foreign race, changed selection/auth/receipt/binding, missing committed file, supported-platform refusal, source validation and downstream current-owner controls. Replace only controls whose documented semantics change.
- Relevant contract paragraph and local-supervisor-admission recipe: define commit, legacy limitations, same argv, no effects, cleanup responsibility.
- Root P routing: only if the fresh comparison demonstrates an additional navigation barrier; prefer direct current original argv over model interpretation of publication stage. No expanding AGENTS into a manual.
- One new atom's method/protocol/evaluator/raw/rounds/confirmation/decision/delivery evidence, through existing Noodle writer and final acceptance/landing.

## Before candidate work
Freeze a version-independent semantic fault harness. For pre-publication
interruptions, the fixed atomic producer must leave the final target absent.
The baseline leaves partial final output. For post-publication interruption,
the harness must observe a complete final bundle. Record an actual kill,
not a simulated exception. If the old exact-line fault hook no longer fires,
do not use it to measure all changed code. If an injected fault does not occur,
mark the result invalid. Do not silently count it as treatment success.

Validate the external oracle and controls. Define grouped train, selection,
and confirmation sets and neutral tasks. Then run a fresh baseline.
Exclude the training run from scores. Retain the limits of two single-hypothesis
attempts / max three rounds / once-only confirmation. Compare successful-task
cost only after behavior gates pass. A failing baseline cost never supplies an
improvement denominator. The full objective also requires cost accounting,
next-session handoff proof, and actual terminal delivery. No completion is
claimed now.