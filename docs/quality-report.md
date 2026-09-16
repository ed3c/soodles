# Per-PR quality observations — Issue #12

The `quality-report` workflow observes opened, updated, reopened and ready PRs. One entry measures every scope using the same recipe on both immutable event snapshots:

```sh
python3 -m venv /tmp/quality-env
/tmp/quality-env/bin/python -m pip install --only-binary=:all: -r quality/requirements.txt
/tmp/quality-env/bin/python -B quality/measure.py --base <40-character-base-sha> --head <40-character-head-sha> --output /tmp/fresh-quality-report
```

Output must be fresh and outside the checkout. No subject code is imported from exported snapshots. The optional analyzer is not part of the runtime acceptance dependency set. Actions publishes a summary and a 30-day artifact containing all hits, clone counterparts, absolute counts, callable CC/SLOC/mass, file digests, churn, scan duration, package versions and recipe fingerprint. Retain artifacts elsewhere before expiration if a longer trend is needed.

| Scope | Selection |
|---|---|
| production | landing.py, soodles.py |
| tests | tests/ Python files |
| oracles | cleanup_oracle.py, cleanup_lock_oracle.py, delivery_oracle.py |
| tooling | quality/ Python files |
| unclassified | Any other tracked Python source; visible pending owner assignment |
| all_python | Separate whole-Python scan; includes cross-scope clones |

Non-Python paths are listed with repository churn but have no Python CC/V/E claim. Empty cohorts are explicitly marked empty; displayed zero ratios do not establish quality. Scope labels identify source responsibility, not GitHub assignees. Do not silently add new source to production by filename guessing.

V uses the union of AST-flagged and clone SLOC; native V with wrappers is also retained. E uses CC × sqrt(SLOC), with the CC > 10 numerator and complete callable traversal. Native E and its omitted callables remain available. The pinned 197-rule release is not the historical paper's 137-rule evaluation. Different recipe hashes are not comparable historical scores without remeasuring both subjects under one recipe.

The report uses the candidate's versioned recipe on both snapshots and labels recipe changes. It has no acceptance authority. The fixed external landing publisher remains independently selected; this report never promotes a candidate judge. A broken analyzer makes this observation fail visibly; quality-report is not a required landing check, and scores never decide merge, deletion, splitting functions, or test removal. Existing runtime acceptance runs unchanged.

Provider cost is one bounded, read-only snapshot of exact-head runtime run IDs, observed attempts, jobs and steps. It does not poll for unfinished runs, rerun tests, or retry unavailable reads. `pending`, `partial`, and `unavailable` are distinct from zero cost. Raw timestamps and URLs support later owner readback. Earlier attempts, other heads and Agent active work are not claimed as measured; job durations are not billed runner-minutes. Shared job time cannot be assigned causally to one changed function. After a PR runtime run completes, a separate job in the same workflow reads the finished run through the immutable collector at f2b78f2b6e216bb1fdaccef1c7b5e0ce9f500b66. It publishes quality-cost-<head>-<run>-<attempt> without checking out or executing the subject, repeating analysis, or running acceptance. This completion event is a materially changed provider state, not a polling retry. The exact triggering run and attempt must be present and completed; otherwise cost remains unavailable. There is no permanent history store. GitHub activates workflow_run only once its workflow is present on the default branch; the admission PR therefore uses supervised completed-cost readback for bootstrap.

Use repeated observations to nominate a causal correction, then reproduce it. A lower score alone does not support refactoring or removing validation. In the prior physical probe, replacing strict `type(value) is int` with a rule-suggested `isinstance(value, int)` admitted `run_attempt=True`; that guard must not be removed merely to reduce V. Preserve positive, planted-negative and real integration controls when changing behavior.
