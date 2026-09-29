# Selected design: atomic complete publication, same-command readback

Status: design selected, not implemented or accepted. Source 51821b935424a4697e2534a9f15b068620510025; fresh provider main matched this source. No product file modified, no Issue created.

## Promise and commit point
The supported final output is the only publication/identity commit point. Build and validate the complete authorization, exact prepared receipt (final paths) and selection binding in one private staging directory. Fsync files and directory, then publish the directory with an OS no-replace atomic rename and sync its parent. Never provide or consume staging continuation paths. Precommit bytes are uncommitted proposals, not selected execution identity; the Issue contract already fixes the base. A completed publication fixes host-config/instruction/carrier/owner bytes. Reentry never rederives them from current state.

The existing authorize public argv remains unchanged. Target absent means no committed output at this selected location; prepare the originally selected operation there. Complete matching target means immutable readback only. Foreign, corrupt, partial, legacy-without-binding, symlink or selection-mismatched target means preserve and refuse. No new output fallback, cleanup of unknown paths, lifecycle call, authority flag or scheduler. Missing authorization from an already committed bundle is a refusal; do not reconstruct it from current selection.

## Why B-prime
A creates a binding before authorization and can repair later receipt publication, but binding-only/empty-directory crashes reproduce the same need for manual recovery earlier. It does not fulfill the stronger complete process-crash boundary. B's original sibling full record fixes more points but adds a second commitment/retention surface. B-prime combines identity commit and namespace publication, removing both the visible partial state and sibling record. Native exclusive rename is necessary because ordinary rename can replace a foreign empty directory. Actual Mac capability probe confirms absent target success and empty/nonempty/symlink target EEXIST with preserved inode; Linux remains a required actual acceptance test, not proved by this probe.

## Boundary and compatibility
Readback proves the stored preparation, not live execution readiness. The next fresh consumer follows exact issue-atom argv/environment and lets that owner recheck mutable head/config/capability/checkpoint/provider state. Do not extend producer into an effect owner or return a fabricated terminal state.
Legacy partial output remains a named original-owner recovery requirement: this atom prevents new reachable partial publication; it cannot invent missing past commitments. Existing legacy complete receipt handoffs remain usable via their original trusted next. This limitation must remain in cases/results rather than be counted as repaired.

## Minimal implementation
- supervisor_admission.py: private no-replace publish helper (Darwin/Linux only, precise refusal on unsupported primitive), complete staging publication and strict matching-bundle readback; preserve existing authorization schema and exact prepared next.
- tests/test_supervisor_authorization.py: real child process kills across staging/final publication, complete readback, foreign race, changed selection/auth/receipt/binding, missing committed file, supported-platform refusal, source validation and downstream current-owner controls. Replace only controls whose documented semantics change.
- Relevant contract paragraph and local-supervisor-admission recipe: define commit, legacy limitations, same argv, no effects, cleanup responsibility.
- Root P routing: only if the fresh comparison demonstrates an additional navigation barrier; prefer direct current original argv over model interpretation of publication stage. No expanding AGENTS into a manual.
- One new atom's method/protocol/evaluator/raw/rounds/confirmation/decision/delivery evidence, through existing Noodle writer and final acceptance/landing.

## Before candidate work
Freeze a version-independent semantic fault harness: pre-publication interruptions must observe final target absent in a fixed atomic producer, whereas baseline leaves partial final output; post-publication interruption must observe complete final bundle. Record actual kill, not simulated exception. Do not measure all changed code against the old exact-line fault hook if that hook no longer fires. If an injected fault does not occur, mark invalid; do not silently call it a treatment success.

Validate external oracle and controls, define grouped train/selection/confirmation and neutral tasks, and then fresh baseline. Training run is excluded from scores. Two single-hypothesis attempts / max three rounds / once-only confirmation persist. Successful-task cost is only comparable after behavior gates pass; failing baseline cost never yields an improvement denominator. Full objective also requires cost accounting, next-session handoff proof, and actual terminal delivery. No completion claim now.
