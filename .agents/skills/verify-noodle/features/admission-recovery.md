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
`19e18b0ab048b17db26aeb3c31147d3bb605e6971205d7ef992876c6f800e84b`
and refusal observer SHA-256
`b0029229f2794b283d8ab30faba8a621e0cd7035d83edcc6001a1a994229662b`.
Their adjacent `preserved-input-selection.json` and `preserved-soodles-input`
remain external inputs. The recovery observer contains a bounded idempotence
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
