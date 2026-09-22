# Instruction-snapshot evidence integrity

Origin: system-v1 P-class/CLI hill-climb qualification goal. Source baseline:
150e21844db2fa7dca8ba2975ba9c68931cb1a1f. A new Issue owns this one correction,
not the resolved reader-recovery Issue and not the independent entry decision.

Observed problem: the real recorder preserves PermissionError for a direct
unreadable AGENTS.md argument; observe_pclass counts that failed snapshot as an
instruction document and returns PASS. The same failure inside shell -c is
silently omitted. Original diagnostic packets remain immutable outside the repo.

One reversible correction boundary: preserve failed literal shell observations
and prevent invalid snapshots from satisfying the existing instruction-binding
gate. Update only record_context.py, observe_pclass.py, nearest context-recording
tests and the bounded P-class recipe, plus this atom's frozen evidence. No new
CLI schema, scheduler, registry, authority or general telemetry framework.

The external Session freezes observer.py before candidate creation. Its checks
drive the actual subject CLIs; the judge is not imported from the candidate.
Owner projection/events are frozen disposable-provider inputs. Actual processes,
argv, stdout/stderr, exit and source hashes are preserved. Live provider writes
are allowed only through the existing issue-atom delivery owner for this Issue;
all observer controls remain disposable and provider-free.

Fixed controls: readable direct instruction passes; denied direct and shell
reads fail to establish an instruction binding and preserve PermissionError;
error-only, empty metadata and malformed digest records cannot pass; zero-byte
valid snapshots remain legal. An independently valid read may satisfy the gate
even if a separate snapshot fails, but the failed snapshot is never counted as
valid. Preserve all raw errors instead of changing transport/route scoring.

One baseline control suite and one final-candidate control suite. No fresh model
sample is claimed for these planted fault controls; they establish deterministic
observer sensitivity, not a naturally occurring Agent barrier or hill climb.
The completed fresh entry-routing case remains NO_OBSERVED_BARRIER (1/0) under
its original manual observer; do not change it or repeat it for this correction.
Future behavioral experiments independently select the corrected observer.

Candidate must pass nearest portable unit tests, full native publication gate,
exact-head Linux canonical acceptance and existing protected landing/reconcile.
Use one PR for code, guidance, fixed oracle, raw evidence and results. A failed
required gate stops delivery; no unchanged failed-head rerun or gate waiver.
Freeze before/after source identities and diff digest. P-class wording here
explains evidence limits; do not claim isolated P-only behavior improvement.
