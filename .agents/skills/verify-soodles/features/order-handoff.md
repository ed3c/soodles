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
