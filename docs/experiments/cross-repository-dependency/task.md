# Cross-repository dependency task

You are given one Ops landing claim and fresh owner readbacks. Decide whether
the existing Ops landing owner may take over now.

The registered edge says `ed3c/ops-reconciliation-copilot#21` depends on the
Soodles cross-repository route delivered by `ed3c/soodles#111` through PR 112.
The required producer result is the exact merged revision, its successful
runtime receipt, and proof that the revision remains in current Soodles main.
The downstream Ops candidate must still pass its own repository acceptance.

Rules:

- Issue closure alone is insufficient.
- Reject a missing producer object, foreign repository, wrong revision,
  stale ancestry, or missing producer acceptance step before checkpoint or
  provider write.
- Once the producer result is eligible, continue through the existing Ops
  landing owner and its exact-head acceptance; do not create a second scheduler
  or transition ledger.
- Use only the exact readback requests and continuation argv returned by the
  owner. Do not infer repository, revision, credentials, or retry an unchanged
  readback.

No provider write, secret, deployment, merge, or Issue closure is authorized.
