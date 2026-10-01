# Owner base advancement — observed failure and correction

The normal #204 / PR #205 runtime 36814876267 failed at candidate evidence
validation (`candidate.missing_required_paths=[AGENTS.md]`), before acceptance.
Its acceptance step was skipped. Candidate 806a3360a8182ebbb49c4ae695758191b278d889
remains the failed publication. While correction was prepared, provider main
advanced from 4acda3aba67e1c3bcca2cb35f36146137148bde4 to
a5498498c7079a329b567e1a03ed43685d94093c. The owner correctly refused stale base
but offered no executable path to update the same Issue contract.

The product gap is repaired in the existing fresh-root prior-publication route:
owner-bound Issue base/pin rebind, durable single-write/readback semantics,
completed failed runtime with skipped acceptance, and instruction selection from
the fresh base. Same-root Noodle correction and its original-base checks remain.
This avoids rewriting old Noodle orders, attempts or immutable authorizations.
The original loop was stopped with exact process evidence and its artifacts
are retained. No unknown write is retried and no repair budget is replenished.

The P-class correction names which of the two existing admissions applies,
assigns the Issue PATCH to its executable owner and keeps normal CI scope with
Test Manager. This document is an N-class explanation, not behavioral evidence.
No local tests, full regression, benchmark or fresh model comparison were run.
New controls are authored for the normal changed-head CI; their outcome is not
claimed in advance. Normal CI and live owner receipts supply subsequent evidence.
