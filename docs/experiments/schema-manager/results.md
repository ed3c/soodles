# Issue 209 — fixed host finalization

Original candidate base: `f1de3f85bb02555bfaeae3290faece475e2ec3e1` (includes PR208). Frozen protocol SHA-256:
`0a6322cba76d5bc019b30cf8fb7776c81fb52a0f817846aa8bfd6d4bbcdbd48f`. The external original protocol and landing verifier were not changed.

The actual `issue_atom.finish_host` stop/restore execution and `_run_owned`
terminal response use the four-node, nine-fact Manager. The original owner
retains authorization, checkpoint, physical readback, Noodle lock and all effects.
The plan consumes the existing system-context `cleanup_residue` P closure;
source pins include the new module/data in the existing lifecycle bundle and
entry source closure. This is fixed host finalization, not a general workflow DSL.

Original candidate Test Manager controls: **173 passed**, across two disjoint
focused selections. `product-results.json` retains their complete raw logs,
selection receipts and runtime/control hashes. They cover missing AND inputs,
confirmation as output, replay/conflict, evidence invalidation, restart without
repair-budget reset, unknown stop/restore, real terminal caller wiring, unchanged
foreign/live/config/lock/group refusals and stopped exact native idle scheduling.
The recovery path already had the idle exception and process scan. Only the
normal stopped-owner custody site needed correction. Every session process is
still checked. Legacy absence of a projection does not create repair history.

One disposable process/config fixture (revalidated after the negative-readback
invalidation correction) traversed actual `finish_host` with no process, signal,
config, lock or Manager mocks. A tiny native fixture executable accepted the
original argv form and held the Noodle instance lock. The original loop received SIGTERM (exit -15). Restart readback observed that
the PID and process group were absent, restored the original bytes, and produced
terminal confirmation. Identical replay left the
checkpoint bytes unchanged. A separate foreign loop remained alive and its
configuration remained unchanged before fixture-owned cleanup. Both fixture
processes and the temporary root were removed. Raw argv, compilation/process
exits, timings, checkpoints and readbacks plus the reproducible fixture driver
are in `product-results.json`. The native compiler is a one-off evidence tool,
not a new runtime or recurring test dependency. Synthetic landing facts enter
at the existing caller seam; this fixture does not prove a real provider merge
or production Noodle behavior.

Historical bounded timing set (not rerun for baseline integration): 16 warmup events and 128 measured events; warm
apply+project P95 **0.013792 ms**, maximum **0.014375 ms**
(target <=1 ms). Measurement includes event/fact validation, identity/sequence
checks and affected-node recomputation. Cold compilation samples were
55.606, 45.712, 44.605 ms. Separate fresh Python CLI elapsed samples were
134.245, 132.046, 131.993 ms.
`timing.json` discloses the exact plan, initial event, deterministic event/history
recipe and every raw sample. Source validation, durable checkpoint I/O and
physical effects are outside the hot metric and remain enforced by the owner;
physical call durations are reported separately. No timing gate was added.

All evidence is local and non-authorizing. Native readiness, Linux exact-head
Actions, publication, landing and local reconciliation belong to the existing
supervisor; none is claimed complete by this candidate. No model repair
capability or Agent behavior improvement is claimed.

## Admitted baseline integration

The original candidate `d05886e390638b1f0abadf0e83bb636349a6470a` now incorporates
exact selected base `28f2ee2d6f916aeea521a084fe8a325f04f339d4`. The frozen protocol
retains its original base text and exact bytes; the current envelope selects
this integration base. Manifest baseline instruction digests were recomputed
from that exact base (the instruction bytes happen to be unchanged).

Current integrated-source Test Manager result: **181 passed**, 11 focused modules,
44.146 seconds (4 workers), including all 8 publisher receipt controls. No full
suite or model evaluation was requested or run.

Both Manager host finalization and the base's publisher process receipts are
preserved. The two additive Test Manager boundary entries caused the only textual merge
conflict. Both entries remain. No separate external lifecycle readmission
implementation was copied into the candidate.

The original 173 controls, physical observations and timing samples above remain
historical evidence for the original candidate. Current source/control hashes,
raw Test Manager receipt and new physical observations are recorded separately
under `product-results.json:baseline_integration`. The existing physical driver
was rerun against integrated source, with only its output path changed. It confirmed own-loop SIGTERM exit -15, PID/group absence, original config restore,
and terminal confirmation. Replay left the checkpoint unchanged, and the foreign
process and config were preserved. Fixture cleanup removed both processes and
the temporary root.

Manager, plan and context compilation inputs are unchanged, so no additional
benchmark was run. `timing.json` remains byte-identical historical hot/cold evidence;
new physical durations are distinct observations and do not replace those metrics.
Publication, native readiness, exact-head Linux Actions and host reconciliation
remain supervisor-owned and are not claimed complete here.
