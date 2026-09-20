# Admission-recovery P-class replay — Issue #81

**Disposition: NO_QUALIFIED_BARRIER.** The same three exploration runs pass all
hard gates after the fixed append-only cleanup supplement; all four totals are zero. This is a non-authorizing handoff,
`authorizes_landing: false`, not Issue resolution or an improvement claim.

## Subject and fixed evidence

- Soodles admitted base: `255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78`.
- Noodle subject: `ca81f942f478e8e4afcbbce6ca69640867efe753`.
- Measured native binary: SHA-256 `5657c8c3dcaa2491d290a35995c35e4c3d46993955b151f3c75e3bac94476aff`.
- Carrier: `darwin_arm64`. Actual consumer model/config identity: UNKNOWN.
- Issue body SHA-256: `60998299d9b94c924f5595ee295435779830bcf08764d497e3d056b6bac45b67`, updated `2026-09-20T05:43:13Z`.
- Continuation Issue body SHA-256: `a575720bbfc3a4c297ec5180e86b2de5020576adc781f0802f4fd344284a151f`, updated `2026-09-20T06:16:31Z`.
- Continuation session: `soodles-81-0-execute-20260920-075003-5d3ee6`, same order/stage/worktree.
- Original writer: Noodle order `soodles-81`, stage 0, session
  `soodles-81-0-execute-20260920-054718-dd6ccf` in its original owned worktree.

The immutable external exploration plan selected e_b4/e_b5/e_b6, identical task
and instruction digests, stopped-owner inputs, and the four ordered legal
barriers before implementation. The committed replay manifest freezes the
candidate analyzers and raw packet for independent readback. It is a local
self-test selection, not an externally promoted landing verifier. No candidate
receipt grants authority over its own acceptance.

| Canonical JSON identity | SHA-256 |
| --- | --- |
| Manifest | `7e6e39dca7d5ae16a8a5e5c7c09fa62da3057449f9a2e7049d035f2adb33afa9` |
| Raw bundle | `bb45efdba017372ea53ba794d5988c4a3adc14d4e9a6701e002d66ddc1a90e1e` |
| Gates | `1b734703a273fb8f8e8c4c8996440db36682365b85590821e95f00e05ff78254` |
| Replay receipt | `a60c579a383e37c361658719737a1722f902c9bc752301622c33cda481fcd15e` |

Analyzer byte digests, exact per-run command membership, argv digests,
initial/completion stream digests, subject, instruction/task, carrier, recorder,
cleanup roles and scopes are in `raw/manifest.json`. Every original
request/result/stdout/stderr is losslessly embedded as base64 with its own byte
SHA-256 in `raw/raw-runs.json`; consumer receipts and selected input bytes are
preserved likewise. The replay verifies these bytes before interpreting them.
It does not execute or import an archived command, packet observer or fixture.

## Actual exploration

The raw chronology independently establishes one fresh inspect, the exact
current owner-selected retire argv, and a fresh post-retirement inspect in each
run. All nine owner operations exited 0. Each completion is `no_proposal` with
empty executable continuation. The archive decodes to the exact 1915-byte
proposal; snapshot, orders and state bytes remain unchanged.

| Run | Recorded commands | Observed legal barriers, in plan order | Hard gate | Scored barriers |
| --- | ---: | --- | --- | --- |
| e_b4 | 40 | 0, 0, 0, 0 | PASS after fixed supplement | 0, 0, 0, 0 |
| e_b5 | 34 | 0, 0, 0, 0 | PASS | 0, 0, 0, 0 |
| e_b6 | 40 | 0, 0, 0, 0 | PASS after fixed supplement | 0, 0, 0, 0 |

The four counts are repeated unchanged projection, help after an executable
projection, repeated unchanged instruction, and avoidable confirmation.
Changed-state completion reinspection is not an avoidable read. Initial help
reads occurred before a complete executable projection. Confirmation absence is
explicitly consumer-recorded; it is not inferred from an absent command.

The initial raw packet did not support the supplied prose claiming complete
cleanup. Its e_b4 observation retains `.noodle/noodle.lock` with a recorded absent PID/group.
e_b6's final inventory explicitly includes that lock; its kernel check covers
nine historical session PIDs/groups, not the lock's PID. e_b5 observed absent
session and lock PIDs/groups and removed its disposable lock manually before
its final residue readback. Its PASS covers this admitted disposable cleanup,
not owner-automatic cleanup or general permission to delete locks.

The first executable replay truthfully returned `INCONCLUSIVE`: e_b4/e_b6
had null scored barriers and aggregate totals were null. The original run bytes,
initial manifest and failed replay receipt remain losslessly embedded in the
raw packet, and commit `29eb8e9` remains in history. No consumer, owner operation
or exploration run was restarted or replaced.

The supervisor then selected and executed the external cleanup observer. Its
fixed bytes are embedded as data, never executed by replay:

| External bytes | SHA-256 |
| --- | --- |
| cleanup-observer.py | `73766b3af692412080381a79504be04e6802890cdc278dd8ce8e6f49e4a804e4` |
| cleanup-selection.json | `014482ad74be3377845ebb5b71120bebcef388449a19e9c704cbdf77263d22d3` |
| e_b4 receipt.json | `91cb2471d74eeb27c0005979a1ad98740d16d8ae5ef2ff3158de04650525dff5` |
| e_b6 receipt.json | `d418da4ac7bfcfd4d1628d642e4352ab030c8f489d22e449c793cca8dc9044d3` |

The manifest binds both original run hashes, exact project paths, lock digests,
original session records and the fixed cleanup scope. e_b4's original lock bytes
hash to `e8803715182f41810f42210189953184b7d35624906530a049f9dcddcdd58305`.
e_b6 originally recorded lock presence only; its lock digest
`40530cde3e5be2951b683df362ad737ddb4adcba95c59ea2c8d9317ff2c02f54`
comes from the fixed observer's before-removal readback, not an invented original
consumer measurement. Both locks are six bytes, with PIDs 65227 and 65571.

The observer recorded absence of each lock PID/group and the same nine session
PIDs/groups before removing only `.noodle/noodle.lock`. It recorded mailbox
absence, one unchanged archive path and no temporary residue. The replay verifies
that final readback follows the original observations and cannot clear a different
residue or process failure. Original cleanup errors remain explicit in the final
receipt. Final totals are 0, 0, 0, 0, so no barrier qualifies; this is neither
improvement nor scoped nonregression. The external observer's narrow deletion is
not Noodle automatic cleanup or permission to remove a production lock.

## Aborted drives and limits

`raw/preflight-aborts.json` separately retains e_b1/e_b2/e_b3 without scores.
e_b1/e_b2 have consumer-recorded pre-entry recorder refusals. e_b3 additionally
has eleven preserved recorder entries reached through a symlink workaround:
task/instruction reads and Noodle help/version occurred, but admission
inspect/retire did not. Its consumer's ordered labels differ from raw timestamps
for two reads. This contradicts the blanket description that all three aborted
before reading the task or invoking Noodle. No aborted drive substitutes for a
valid exploration run.

A failed Go executable lookup in e_b6 is retained as an unstarted process with
null exit, not fabricated as a waited child. Its successful build metadata
read occurred after completion. The raw record does not establish a complete
Doctor-before-drive pass or source-checkout HEAD/clean-state comparison. The
admission commands' nonempty repairable backlog warning is also preserved.

Transport absence is scoped to the fixed recorded subprocess commands; arbitrary
provider commands outside that trace are not observable here. The recorder's
pinned `communicate()` implementation explains observed subprocess waits.
Consumer records are not complete platform transcripts, and no hidden model
reasoning, global network monitor or unavailable model identity is claimed.

## Discriminator and checks

The existing `replay_pclass.py` entry adds only feature-selected recovery replay.
It rejects a wrong manifest, raw bundle, gate schema or analyzer digest before
analyzer import. Raw normalization then checks membership, identity, current
operation, completion, preservation, process and cleanup. Caller-supplied PASS
controls or behavior counts are not accepted as gates.

All 18 manifest-selected mutation/non-case controls match their predicates:
stale continuation, wrong projection, wrong Noodle subject, missing completion,
false cleanup, incomplete/duplicate membership, recorder/run identity, changed
archive, provider command and missing wait are RED; exact fresh completion and
independently assembled equivalent current argv are GREEN. Predicates require the source run's specific error. Four additional controls
reject supplement omission/rebinding and accept the corrected same packet and
the legal complete-cleanup non-case.

Twenty recovery replay unit tests also exercise analyzer pre-import refusal, actual
normalizer identity, carrier and completion bindings, missing confirmation or
streams, live process/lock evidence, duplicate mutation, positive counts for all
four ordered barriers, and unchanged reinspection after completion. Explicitly
synthetic complete three-baseline zero controls yield `NO_QUALIFIED_BARRIER`,
with no treatment retained and no confirmation authorized. Synthetic positive
pilots select the first positive barrier but authorize no new experiment.
These fixtures are not fresh consumers or confirmation evidence.

Validation: 20 recovery replay tests, 19 existing P-class tests, and 8 recorder
context tests pass. The recorder tests initially failed on macOS `/var` versus
`/private/var` tempfile aliases; using physical `TMPDIR=/private/tmp` passes
without disabling or editing a test. `git diff --check` passes.

The original distinct read-only consumer's requests, pinned identities, raw
checks, failed replay and discrepancies remain in `raw/independent-replay.json`.
A continuation replay from committed raw evidence is the next readback; it will
record its own process, pins, actual exit and comparison without rerunning an
exploration consumer or owner operation.

No treatment arm or 3+3 confirmation was created. The recipe records this
bounded zero disposition without treatment guidance.
Linux exact-head Actions acceptance, PR creation, landing, merge, Issue closure
and original-order reconciliation remain outside this implementation task.
