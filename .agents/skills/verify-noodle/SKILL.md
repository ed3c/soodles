---
name: verify-noodle
description: Verify Noodle CLI identity and skill resolution, stopped initial-proposal recovery, or an admitted order/session handoff through existing owners and external evidence.
---

# Verify Noodle

Use this independent map when Noodle itself is the app under examination. Soodles
runtime-lock acceptance, provider delivery and P-class comparisons retain their
[existing verification route](../verify-soodles/SKILL.md). This skill supplies
P guidance and an N inventory; existing owner checks supply L evidence and exact
provider readbacks supply R truth. It grants no execution or landing authority.

## Launch

The supervisor supplies absolute paths for the measured Noodle binary, pinned
source checkout, project/control root, admitted subject and Noodle-owned worktree
(or an explicitly disposable rejected-proposal copy), and evidence destination
outside all disposable directories and the task worktree. The packet also names
binary SHA-256, full source revision/clean state, OS/architecture, Session carrier
and its measurement, permitted drive, and existing owner/continuation. Recovery
needs selected external observers/fixtures; handoff needs the original admission,
Session binding and external process recorder. Report a missing field, who must
supply it, and the existing continuation; do not infer permissions or state.

Below, `NOODLE_BIN`, `NOODLE_SOURCE`, `NOODLE_PROJECT`, `NOODLE_WORKTREE` and
`NOODLE_EVIDENCE` denote these supplied paths, not new Noodle configuration flags.
Use explicit `--project-dir`: inherited `NOODLE_PROJECT_DIR` can select another
configuration even while cwd is the intended worktree.

The mapped CLI drives are short-lived and noninteractive. Start each command as
a fresh subprocess, capture its output and wait for its actual exit. Launch is
`"$NOODLE_BIN" --help` followed by Doctor; no daemon or port is needed. A zero
exit and the expected command surface establish readiness for these CLI reads.
The genuine-order feature observes an already admitted Noodle lifecycle; this
skill does not start a replacement scheduler, writer or model session.

## Doctor

In every fresh drive, run `"$NOODLE_BIN" version`, read its build metadata with
`go version -m "$NOODLE_BIN"`, measure its SHA-256 with
`python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$NOODLE_BIN"`, and compare with the supervisor
selection and `git -C "$NOODLE_SOURCE" rev-parse HEAD` plus
`git -C "$NOODLE_SOURCE" status --porcelain`. Check exact `vcs.revision`,
`vcs.modified`, GOOS and GOARCH, not just the displayed version or filename.
Use the identity recipe for resolved Skill paths. Re-do Doctor after surprising
output or an environment change; preserve the failure before any correction.
A mismatch goes to the supervisor's binary/source selection, not an automatic
rebuild or override. Native macOS observations cannot satisfy Soodles' Linux
`policy/runtime.lock.json` acceptance.

## Drive

Read only the selected feature recipe for ordinary use:

- [Identity and skill resolution](features/identity-skills.md): measured executable and exact resolved files.
- [Initial admission recovery](features/admission-recovery.md): stopped-owner retirement in supplied disposable fixtures and legal refusals.
- [Original order/session handoff](features/order-handoff.md): genuine prior admission, own typed outcome, external wait/exit and quiescent readback.

The [independent index](features/README.md) defines full maintenance coverage.
Consume the current owner's JSON, including `owner`, `status`, `invalid` and
`next`. Pass current `next.argv` directly as an argv array after matching its
binary/project/subject to the supplied selection; never shell-join, reconstruct,
or replay a historical command. When the current local Soodles continuation is
`next.kind=provider_readback` with owner GitHub, use the dedicated
[provider-readback Skill](../provider-readback/SKILL.md) and its exact
`./provider-readback consume` entry; do not translate GETs, pagination,
snapshot keys or owner re-entry in the Agent. Refusal names `next.required` and
`next.provided_by`; after that owner resolves it, use its `next.readback_argv`.
An empty argv is not permission to invent an operation. `no_proposal` ends
recovery, not the Issue or original order.

## Evidence

Use the external evidence destination from the packet. Preserve actual argv
arrays, cwd, relevant non-secret selection/binding, raw stdout/stderr, observed
exit or timeout, timestamps, binary/source/carrier and resolved-file digests,
subject readbacks, before/after state and cleanup observations. Separate local
fixtures, live process observations and provider claims. Capture actions and
resulting state; a final summary or status line alone is insufficient.

For downloaded admission-recovery evidence, use the selected feature recipe's
`./soodles packet verify` route. The same format binds Linux and macOS evidence
to distinct carriers; executable continuation always requires fresh Noodle
`admission inspect` on the selected carrier. Packaging grants no landing authority.

A receipt states covered feature, classification and unresolved limits with
`authorizes_landing: false`. Correct refusal of valid, admitted, unknown or live
proposals is GREEN when preservation is observed. Missing input remains blocked;
unknown measurements stay unknown. Keep external #84 RED/fixed GREEN/legal
non-case GREEN controls attributable to their own subject and observer. No new
product gate is introduced here. Counts, successful commands and shorter guidance
do not prove reduced Agent decision cost.

## Cleanup

Wait for every short-lived command. Remove only scratch residue this drive owns,
using the supplied observer's cleanup for its fixtures; never remove the admitted
worktree, canonical checkpoint or evidence. On failed drives, preserve evidence
and clean owned residue before considering a corrected attempt. Verify evidence
files still exist and their recorded digests match after teardown. Noodle owns
runtime/worktree reconciliation; an external recorder and kernel process/group
readback establish quiescence for the genuine order. Preserve actual draft or
committed work outside retry residue before any owner requeue.

## Helpers

This skill ships no helper scripts. For short CLI records, the existing Soodles
recorder is `.agents/skills/verify-soodles/scripts/record_context.py` in the
supplied skill checkout. Invoke it as
`python3 /absolute/skill-checkout/.agents/skills/verify-soodles/scripts/record_context.py "$NOODLE_EVIDENCE" fresh-label "$NOODLE_BIN" --project-dir "$NOODLE_PROJECT" version`,
with the actual checkout and a fresh label. It records one subprocess, not a
native Agent trace or verdict. Reuse the supervisor-selected #84 observers
and process recorder as specified in the feature recipes. Their bytes, input
selection, invocation and receipts remain attributable to the supervisor selection
(the admission-recovery recipe maps the portable fixture copy); do not copy their recovery
algorithm, rewrite the active judge or create a retry engine. Missing tools or
observer inputs are supplied by the supervisor through the existing selection.

## Maintenance

Creation follows fixed pstack `ed3c/plugins@68836ddaf5697224520f1847d90cdb90ca8babaa`
`create-verification-skill`, adapted to `.agents/skills`. After application, the
coordinator must physically follow Launch → Doctor → one mapped Drive → Evidence
→ Cleanup and verify evidence survives. Authoring/help interviews alone remain
a draft until that proof exists.

Use that same pinned pstack `maintain-verification-skill` for an explicit audit
or observed drift, not every Issue. Audit index/sibling links, then launch one
read-only source reviewer per feature concurrently. Each returns feature summary,
source entry points, drift or none, and one concise live recipe; children neither
drive nor edit. The coordinator reconciles reviews and concrete source churn,
then live-drives all three features with Doctor and cleanup after each drive,
including failures. Existing genuine subjects supply lifecycle coverage; never
create a second order for coverage. Missing prerequisites make full coverage
blocked even if other features pass.

Report clean, changed or blocked with feature coverage. Clean/blocked passes do
not create a maintenance PR. Changed maintenance edits only this skill directory,
re-drives corrections and uses the admitted delivery boundary. Product defects
remain with their transition owner. Issue completion separately requires final
clean-head Linux canonical acceptance, exact-head provider checks, supervised
merge/closure, original-order completion and Noodle cleanup. A new source head
needs its own evidence; old receipts cannot be relabeled.
