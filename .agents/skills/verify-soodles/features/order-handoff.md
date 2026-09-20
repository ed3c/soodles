# Landing current-next and order handoff

Use this recipe for the bounded local claim that a completed original Noodle
order can be reconciled and cleaned before the next Issue order starts.

Run `./soodles runtime check ABSOLUTE_NOODLE` first. Then run canonical
`./soodles acceptance verify ABSOLUTE_NOODLE` once on the final clean candidate.
Read `physical.order_handoff` from its receipt and require:

- `classification: VERIFIED` and `sequence: [A, cleanup, B]`;
- current `next.argv` actions `dispatch, merge, readback` with exactly one
  offered write and no reconstructed operation;
- A and B each have one original Session, a completed nonblocking typed outcome,
  an externally waited zero process exit and the pinned binary digest;
- A completion comes from the retained projection and its cleanup owner is Noodle;
- B records `issue.automatic` admission and starts after A cleanup;
- `zero_residue: true`, `provider_fixture: true`, and
  `authorizes_landing: false`.

Preserve the supervisor-selected external `handoff_oracle.py` bytes and digest.
Run those same bytes against the admitted baseline and candidate; the repository
copy participates in acceptance but cannot select itself. A missing current row
alone never proves completion. Do not replace missing Session, outcome, exit,
effect or kernel readback with prose or a fabricated order. Provider merge and
Issue closure remain with supervised delivery.

## Interrupted after A cleanup, before B admission

The supervisor supplies the existing A landing checkpoint and B external
envelope/digest in a complete invocation of
`./soodles issue resume A_CHECKPOINT B_ENVELOPE SHA256`. Consume that invocation
verbatim from the control root. This one entry reads A's resolved cleanup and
original-order evidence, checks that its path, branch and registration remain
absent, then reads B through the existing admission owner. Do not infer cleanup
from a missing order row or compose a second admission writer.

If the prior publication result is unknown, re-enter this guarded boundary with
the supervisor's same inputs to obtain fresh owner readback. `proposal_pending`
with `published: false`, `owned`, or `previously_admitted` requires the named
Noodle readback; none authorizes another publication or restart. A refusal names
the owner/input needed before continuation. The entry neither cleans A nor
selects B, and adds no durable ledger, retry loop or concurrent exactly-once claim.

Read `physical.interruption_resume` from canonical acceptance. Require two
externally waited SIGKILL exits (before admission and after publication before
response), a fresh CLI readback preserving the pending mailbox identity/bytes,
a retained-owner readback without publication, one original B session in the
real Noodle lifecycle, and zero residue. Preserve the supervisor-pinned
`resume_oracle.py` and task bytes, baseline missing-entry and planted duplicate
controls. Provider data remains a fixture; this is sequential local recovery,
not cross-host recovery or authority to merge. P-class comparisons use the
[bounded context recipe](pclass-context.md) and report equal legal arms as
nonregression.
