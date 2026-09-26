# Matched transitive-helper binding comparison

Frozen after the initial qualification control exposed the defect, and before
any candidate source exists. The first `protocol.md`/`observe.py`/`run/` packet
is preserved as a valid baseline-only deterministic observation. It is not the
matched evaluator because that observer bound its source head internally and
could not accept a future candidate. This correction parameterizes only source
root, expected clean head and fresh output directory. It does not change the
two cases, invariant, score or allowed effects.

Run exactly once on baseline and, only after a source correction, exactly once
on the candidate. Both runs use the same `compare.py` bytes, Python executable,
matching-helper case and planted byte-different candidate-helper case.

Hard invariants:

- source root is a clean Git worktree at the externally supplied exact head;
- the matching case imports the externally copied matching helper and stops on
  the deliberately absent next dependency, without writing a marker;
- the planted mismatch must not execute candidate helper bytes or write its
  marker; it may stop on the same absent next dependency;
- source remains clean and at the same head; no external operation occurs.

If the planted marker appears, classify `OBSERVED_BARRIER`. If both cases reach
the missing next dependency and neither marker appears, classify
`NO_OBSERVED_BARRIER`; otherwise `INCONCLUSIVE`. Required behavior precedes the
metric: any source drift or unexpected process result is inconclusive, never a
green. This is a deterministic executable discriminator, not model behavior,
instruction efficiency, provider truth or landing authority.

