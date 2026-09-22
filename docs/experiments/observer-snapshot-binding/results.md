# Issue #139: failed snapshots cannot satisfy instruction binding

Baseline: `150e21844db2fa7dca8ba2975ba9c68931cb1a1f`. Measured source candidate: `95ac986391a6d4e49f82298d34f6d68a8a037f04`.
The following evidence-only commit does not change measured executable/instruction bytes.

The old public observer returned PASS after an actual denied `cat` whose recorder
request contained only PermissionError for AGENTS.md. Shell-wrapped failure was
silently omitted. The correction preserves shell errors and filters invalid
observations out of valid instruction bindings. Raw requests remain intact;
route, transport, identity and landing authority are unchanged.

The externally frozen public-CLI oracle improves from
7/14 to
14/14 checks. Both readable
and zero-byte legal cases remain accepted; a separate valid read remains usable.
Actual denied direct/shell reads and malformed metadata cannot establish a binding.
The fixed owner projections come from the real disposable pending owner, not a
candidate-selected judge. Original diagnostic raw files and its /var versus
/private summary-lookup limitation are preserved, not silently rewritten.

These are planted fault controls: deterministic eval validity, NOT naturally
occurring Agent errors, fresh behavioral hill climb, or isolated P-only efficacy.
No model baseline/treatment was run for this evaluator correction. The independent
entry-routing consumer already stopped with zero barriers and was not resampled.
New behavior experiments must select this observer independently before launch.

Full unit suites passed for both pinned subjects on macOS with the same physical
TMPDIR=/private/tmp. No test or gate was disabled. The real denied-file controls
ran outside the repository and restored permissions only for scoped fixture cleanup.
Provider writes are excluded from the experiments. Issue creation was initially
unknown, then exactly matched by fresh readback without repeating its POST.

The manifest binds corrected guidance, source, tests and the immutable oracle/raw
evidence. Decode raw.json's archive and verify all member hashes to inspect actual
argv, stdout/stderr, exits and snapshots. Unknown hidden reads remain unknown.
This report precedes delivery: native readiness, exact-head Linux acceptance,
protected provider landing and Git/Noodle terminal reconciliation remain required.
This one correction does not close the broader nine-feature maintenance goal.
