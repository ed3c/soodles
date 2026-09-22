# Issue #141: reap owned handoff processes on failure

Baseline: `c14774b72a0c667fc6333d52b31fddb4da737d35`. Measured source candidate: `9c1851134e30772aaf4312168514e3dcd70742a5`.
The following evidence-only commit leaves measured executable/instruction bytes unchanged.

The frozen external observer calls the actual handoff_probe, substitutes a real
harmless Python child at _start, and injects a fixed first projection failure.
Baseline removed its fixture while PID 55713 remained alive. Its exact
child was stopped/reaped by emergency external cleanup, not subject success.
Candidate had already stopped/reaped PID 60670 before returning the
same original failure. Both controls confirm no process residue afterwards.
The observer/protocol bytes and criteria were frozen before any candidate edit.

This RED→GREEN proves this deterministic failed-wait cleanup boundary, not a
fresh-model hill climb. No model baseline/treatment is claimed for this atom.
The separate delivery-routing fresh baseline stopped at 1/0 NO_OBSERVED_BARRIER;
its result is not reused as efficacy evidence for this correction. The candidate
also includes portable nearest controls; unchanged full baseline and candidate
unit suites pass on macOS with TMPDIR=/private/tmp. No gate/test was disabled.

The test substitutes initialization and never runs Noodle, providers or models.
Actual Noodle A→cleanup→B, current-next and interruption behavior still require
the independently selected Linux canonical acceptance. Native readiness cannot
substitute for it. Forced/nonzero process termination cannot claim VERIFIED.

Decode raw.json's archive and verify member hashes for source, argv, stdout,
stderr, exits, exceptions, process observations, side effects and cleanup.
Baseline terminal-command metadata beyond the retained tool record is unknown;
raw baseline observer results and source hash are retained unchanged.
Issue creation was initially unknown and exactly matched by fresh readback,
without a repeated POST. No provider writes occur inside the fault controls.

This report precedes publication/landing. One exact PR, native readiness,
exact-head Linux CI, externally owned protected landing and Git/Noodle terminal
reconciliation remain required. Other feature-map gaps remain open.
