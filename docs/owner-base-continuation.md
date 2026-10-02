# Owner base advancement — observed failure and correction

The normal #204 / PR #205 runtime 36814876267 failed at candidate evidence
validation (`candidate.missing_required_paths=[AGENTS.md]`), before acceptance.
Its acceptance step was skipped. Candidate 806a3360a8182ebbb49c4ae695758191b278d889
remains the failed publication. While correction was prepared, provider main
advanced from 4acda3aba67e1c3bcca2cb35f36146137148bde4 to
a5498498c7079a329b567e1a03ed43685d94093c. The owner correctly refused stale base
but offered no executable path to update the same Issue contract.

The correction uses the existing fresh-root prior-publication route.
The owner rebinds the Issue base and pins, then selects instructions from the fresh base.
The route records each write and its readback durably. It accepts a completed,
failed runtime whose acceptance step was skipped.
Same-root Noodle correction retains its original-base checks.
This avoids rewriting old Noodle orders, attempts or immutable authorizations.
The original loop was stopped with exact process evidence and its artifacts
are retained. No unknown write is retried and no repair budget is replenished.

The P-class correction identifies which of the two existing admissions applies.
It assigns the Issue PATCH to its executable owner. Test Manager retains control
of normal CI scope. This document is an N-class explanation, not behavioral evidence.
No local tests, full regression, benchmark or fresh model comparison were run.
New controls are authored for the normal changed-head CI; their outcome is not
claimed in advance. Normal CI and live owner receipts supply subsequent evidence.
