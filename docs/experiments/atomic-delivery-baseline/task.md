# P0/P1 atomic delivery task

Measure two coupled delivery defects under one Issue and one PR.

1. P0: a copied historical process identity must not mask the refusal case that
   the observer is assigned to measure. Isolation applies only to the disposable
   copy; the observer's own live-process and orphan-process-group controls remain
   live and must still refuse.
2. P1: one causal Issue uses one PR. Failed candidate heads remain immutable
   attempts on that PR. Missing evidence, byte mismatch, or runtime RED blocks
   merge. The next corrected head stays on the same PR. A second PR is legal only
   after the first PR has merged and a distinct corrective Issue owns the new
   rollback boundary.

The baseline is the preserved #91/#92/#94/#95/#96 history and runtime receipts.
The treatment is this Issue's one-PR delivery plus the corrected refusal
observer. The observer reports the fixture barrier and delivery-split barrier
separately. Zero-to-zero is nonregression; only a positive barrier that reaches
zero supports a scoped hill-climb claim.

Every receipt is non-authorizing. Candidate verification, runtime acceptance,
provider merge, Issue closure, and main readback retain their existing owners.
