# Stopped initial-proposal retirement

## Sub-features

Inspect a rejected INITIAL proposal; retire only the exact unchanged subject
through the stopped owner; observe archival, canonical preservation and legal
refusals. Consume independently accepted Noodle #84 controls without implementing
another recovery algorithm.

## How to get to it (user POV)

The operator supplies a stopped-owner project with original session/process
evidence, selected binary/source, and an explicitly disposable copy of preserved
rejected input. Use disposable fixtures unless the exact canonical mutation is
explicitly authorized. A help/source interview alone does not exercise recovery.
The coordinator performs this live drive. Never stop or repair
production simply to make the feature reachable.

Missing checkpoint, sessions, observer/fixture selection or process absence is
reported to the Noodle operator named by the readback. Preserve unknown or
inconsistent evidence. A `status` summary alone does not prove a stopped owner.

## Driving it with the Noodle CLI

1. Doctor the selected binary. Record fixture selection and before bytes/digests
   of `.noodle/orders-next.json`, `state.snapshot.json`, `orders.json`, and relevant
   original session evidence, with the preserved production source kept unchanged.
2. In the supplied disposable project run
   `"$NOODLE_BIN" --project-dir "$NOODLE_PROJECT" admission inspect`. Capture raw
   JSON, stderr and actual exit. `owner`, `subject.proposal_sha256`,
   `current_order_revision`, `invalid` and `next` bind the continuation.
3. For `recoverable`, verify that current `next.argv` still names the selected
   binary and this disposable project, and pass that array directly to the process
   runner. It carries `admission retire`, the exact digest and revision; never
   substitute hand-typed arguments or replay an earlier receipt. Capture the
   result. After `retired`, consume its current `next.argv` once for fresh readback.
4. Require the original proposal bytes preserved losslessly in the owner's
   `.noodle/admission-retirements` receipt, the retired mailbox absent, and canonical
   checkpoint/orders unchanged. Preserve the archive outside scratch before
   cleanup. `no_proposal` has no executable recovery continuation: report its
   named scheduling owner/required separately admitted intent and stop this drive.
5. Reuse the supervisor's fixed #84 recovery/refusal observers and selected
   fixtures for defect and non-case evidence. Their measured interface is
   `python3 "$RECOVERY_OBSERVER" "$NOODLE_BIN" "$RECOVERY_EVIDENCE"` and
   `python3 "$REFUSAL_OBSERVER" "$NOODLE_BIN" "$REFUSAL_EVIDENCE"`, with absolute
   observer paths and fresh external destinations supplied by the supervisor.
   These external observers own scratch copies and cleanup. Check their receipts,
   actual exits and evidence survival; historical GREEN is not this live pass.

The #46 selection pins recovery observer SHA-256
`1f22ebd63786e032f92d51c455cfd35dff9f0660acd969db70d2f3e5deda5b6f`
and refusal observer SHA-256
`b0029229f2794b283d8ab30faba8a621e0cd7035d83edcc6001a1a994229662b`.
Their adjacent `preserved-input-selection.json` and `preserved-soodles-input`
remain supervisor-selected inputs; the #79 portable fixture copy preserves their bytes. After verifying those original bytes, the recovery observer replaces captured historical PIDs only in its disposable execution copy with an out-of-range sentinel and records every adjustment. This prevents an unrelated carrier process from impersonating a captured session. The refusal observer still creates its own live PID and orphan-process-group controls and is unchanged. The recovery observer contains a bounded idempotence
control; it is not a general instruction to replay old argv. The coordinator's
normal drive always consumes fresh next and includes the post-retirement readback.
The fixed refusal observer covers wrong digest/revision, admitted ledger, valid
proposal, live process and orphan live group. It preserves mailbox/snapshot but
does not measure orders bytes, continuation fields or final group absence. Its
GREEN cannot claim those observations or live unknown/ambiguous coverage. The
coordinator separately records normal-drive orders preservation and cleanup;
unknown/ambiguous refusal coverage remains attributable to the source controls
unless explicitly driven and observed in the current run.

Source: `cmd_admission.go`; `loop/admission_recovery.go:InspectAdmission`,
`RetireAdmission`, `admissionRetirementNext`; `loop/admission_evidence.go`.
Nearest controls: `loop/admission_recovery_test.go` exact-byte retirement,
refusal gates, legal non-cases and physical crash controls.

## Portable evidence (Soodles #79)

For the selected `ed3c/noodle@ca81f942f478e8e4afcbbce6ca69640867efe753`
subject, `./soodles packet --help` owns packaging and verification. The fixed
observer bytes and input selection now also live in
`tests/fixtures/admission-recovery-portable`; their digests above remain the
selection, not candidate-granted authority. The preserved input selection digest
is `9b5c6505bcd023fb1a872d44d8a33880e862046883349bd032c4b830ccf18e14`.

Actions builds that exact source separately from the runtime-lock release,
runs both observers in disposable scratch directories with a credential-free
environment, waits for their actual exits, and packages `admission-recovery.tar`
beside the existing acceptance/release JSON. Download the exact-head artifact
through the existing provider owner and run:

```sh
./soodles packet verify /download/admission-recovery.tar --expected-carrier linux_amd64
```

This reads tar members without extracting or executing them. A local unpacked
packet uses the same command. For existing native macOS evidence, use
`--expected-carrier darwin_arm64`; it must refuse the Linux claim. Verification
checks evidence integrity and preserves nonzero exits, including legal refusals;
it does not turn an observer's failure into behavioral success. Actions separately
requires successful observer exits. The receipt is always non-authorizing.

To produce a new evidence set, use `packet observe BINARY SOURCE OUTPUT` with the
supplied exact source build, then `packet create OUTPUT ARCHIVE --carrier ID`.
The producer selects only its fixed relative file list: measured `subject.json`
and `build.txt`, both fixed observers, preserved selection/input, and each
observer's `process.json`, `stdout.bin`, `stderr.bin`, `receipt.json` and
`cleanup.json`. Process records require actual integer exit, `waited`, timeout
status and stream digests. Existing evidence can be mapped to those names while
preserving raw stream/receipt bytes and the original measurements; never invent
an unobserved wait or cleanup. `cleanup.json` identifies the observed scope;
Actions measures scratch filesystem absence after wait. The fixed refusal
observer's process-group limitation above remains unchanged. Extra ambient files
are not included; packet.json contains no executable argv or host paths.

The packet states `continuation.portable=false`, `owner=Noodle`,
`entry=admission inspect`. Historical absolute paths inside raw receipts are
observations only. A downloaded packet never authorizes replay of their argv.
For a new carrier-specific continuation, obtain the existing supervisor selection
and fresh Noodle `admission inspect` readback on that carrier; consume only that
owner's current continuation. Carrier mismatch, missing role/file, changed bytes,
false cleanup, traversal or any portable continuation is a refusal with the
field and existing inspect entry. No production proposal or runtime-lock identity
is migrated by this format.

## Gotchas

Correct refusal of a valid, already admitted/owned, unknown/ambiguous or live
proposal is GREEN when mailbox and canonical bytes remain preserved. CLI refusal
returns structured JSON plus a nonzero exit; neither exit-zero alone nor a generic
failure label describes the control. For `refused`, report `next.required` to
`next.provided_by`; only after owner resolution use `next.readback_argv`.

The owner checks lock, canonical revision, projection, ledger and session/process
evidence. Do not fill absent fields, forge a checkpoint, delete a lock, change
identity or turn an unknown write into a retry. Retirement neither admits work,
restarts a loop, completes an order nor authorizes provider writes. Keep #39's
paused comparison and all production state outside these fixtures.
