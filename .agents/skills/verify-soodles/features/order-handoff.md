# Landing current-next and order handoff

Use this recipe for the bounded local claim that a completed original Noodle
order can be reconciled and cleaned before the next Issue order starts.

Ask the [Test Manager](../../test-manager/SKILL.md) for the requested order-handoff
control. Use a matching existing receipt when available; otherwise, when execution
is authorized, run the named control through the existing acceptance entry:

```sh
./soodles acceptance verify ABSOLUTE_NOODLE --control order_handoff --reason 'Requested order handoff verification'
```

Acceptance performs required binary admission for this control; do not add a
separate doctor or full-suite run. Read `physical.order_handoff` and require:

- `classification: VERIFIED` and `sequence: [A, cleanup, B]`;
- current `next.argv` actions `dispatch, merge, readback` with exactly one
  offered write and no reconstructed operation;
- A and B each have one original Session, a completed nonblocking typed outcome,
  an externally waited zero process exit and the pinned binary digest;
- A completion comes from the retained projection and its cleanup owner is Noodle;
- B records `issue.automatic` admission and starts after A cleanup;
- `zero_residue: true`, `provider_fixture: true`, and
  `authorizes_landing: false`.

Preserve the selected external judge's bytes and digest. Only a task-selected
baseline/candidate comparison runs the supervisor-pinned `handoff_oracle.py`
against both subjects; normal acceptance does not request that comparison.
The repository copy cannot select itself as the external judge. A missing current row
alone never proves completion. Do not replace missing Session, outcome, exit,
effect or kernel readback with prose or a fabricated order. Provider merge and
Issue closure remain with supervised delivery.

If an A or B projection fails, require the oracle to stop and reap its child
before removing its fixture. Require it to retain the original failure and expose any cleanup failure.
If graceful stop times out, require the oracle to force bounded process group
cleanup and still report failure. Forced termination cannot produce `VERIFIED`.
Preserve the fixed external failed-projection control and portable cleanup test
results separately from canonical Linux positive handoff evidence. This fault
control is not a fresh model comparison.

## Interrupted after A cleanup, before B admission

The supervisor supplies the existing A landing checkpoint and B external
envelope and digest in a complete invocation of
`./soodles issue resume A_CHECKPOINT B_ENVELOPE SHA256`. Consume that invocation
verbatim from the control root. This entry reads A's resolved cleanup and
original-order evidence. It checks that A's path, branch and registration remain
absent. It then reads B through the existing admission owner. Do not infer cleanup
from a missing order row or compose a second admission writer.

If the prior publication result is unknown, re-enter this guarded boundary with
the supervisor's same inputs to obtain fresh owner readback. `proposal_pending`
with `published: false`, `owned`, or `previously_admitted` requires the named
Noodle readback; none authorizes another publication or restart. A refusal names
the owner/input needed before continuation. The entry neither cleans A nor
selects B, and adds no durable ledger, retry loop or concurrent exactly-once claim.

When Test Manager selects interruption verification, read
`physical.interruption_resume` from canonical acceptance. Its controls require two
externally waited SIGKILL exits (before admission and after publication before
response), a fresh CLI readback preserving the pending mailbox identity/bytes,
a retained-owner readback without publication, one original B session in the
real Noodle lifecycle, and zero residue. Preserve the supervisor-pinned
`resume_oracle.py` and `handoff_oracle.py` together in the same external directory,
recording each file's SHA-256. Execution against both baseline and candidate
applies only to an explicitly selected comparison, not ordinary resume.
The resume observer loads that sibling helper under a private module identity;
candidate source and existing module-cache entries cannot select either judge.
Candidate source still supplies production modules such as `issue_execution`.
Preserve task bytes, baseline missing-entry and planted duplicate controls.
Provider data remains a fixture; this is sequential local recovery,
not cross-host recovery or authority to merge. P-class comparisons use the
[bounded context recipe](pclass-context.md) and report equal legal arms as
nonregression.
