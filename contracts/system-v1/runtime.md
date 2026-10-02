## RUNTIME.ADMISSION.001

The target lock selects an exact Linux amd64 Noodle release. Before version
execution, `runtime_check` validates the host, lock fields, file existence,
executable permission, and binary digest. A mismatch fails without worktree
effects. The failure names the owning command and help entry. The Actions
download step also reads back release, tag, and archive correspondence.
The local command does not claim a live provider read.

## ACCEPTANCE.BOOTSTRAP.001

`acceptance_verify` requires a clean source root and captures its head and tree.
It selects affected unit and physical controls against the provider base.
Selected worktree controls exercise the pinned Noodle commands in an isolated
temporary repository. Acceptance then checks source identity again.
The physical oracle checks the exact worktree path and HEAD. It also checks
missing-worktree refusal before a sentinel effect, and cleanup with Git branch,
worktree, and head readback. The fixture environment excludes provider credentials
and live Noodle identities.

`tests/test_admission.py` holds the nearest refusal controls. The actual binary
oracle lives in `worktree_probe`. Canonical acceptance calls that oracle rather
than a mocked Noodle. Unit fixtures with synthetic executables are labeled as
such. They do not prove release-runtime behavior.

Routine acceptance covers current executable behavior. Each distinct refusal,
effect boundary, and recovery control remains testable against the candidate.
The Test Manager Skill is the single P-class scope owner. `test_manager.py`
resolves its request for local and canonical callers and runs unit controls.
No caller predicts full coverage or automatically escalates to it.
The manager consumes a concrete full request or selects named controls from
traced changed behavior and consumers. Shared filenames, selector changes,
removed tests, unknown inputs, failures, and missing CI bases do not request
full coverage.

`./soodles test` compares local changes against HEAD. `--base EXACT_SHA` includes
committed changes. `--module` and `--control` name on-demand local coverage
with `--reason`. `--plan` describes that coverage without execution. `--full`
explicitly requests all coverage supported by the entry. Missing or empty
requested modules cause refusal. Canonical acceptance uses the same manager.
It requires the admitted base or an explicit coverage request. Omitting the
base no longer means full acceptance. Actions supplies the provider base.
If the base is missing, readback is required.

Unknown paths or removed tests produce `needs_scope` before execution.
The supervising Agent traces the impact and supplies named controls or corrects
the existing reusable map. This requires no second approval. It is not a reason
to ask the user to build an input. Prose-only changes require review and make
no runtime behavior claim. The manager result preserves changed scope, base,
paths, reasons, and unresolved inputs.
Selected test modules run in up to four independent processes. The manager
checks executed test identities against discovery. Failure, skip, missing or
empty selected modules, or incomplete execution causes refusal. An explicitly
empty plan says `not_required`. It does not report all tests passed.
Unexecuted physical controls have no success or residue claim. The local test
command covers unit tests only. Its plan also names physical controls that
remain with canonical acceptance. Release download and binary admission occur
only when physical controls require them.

There is no fixed 120-second suite deadline. External operations retain their
own deadlines, and the Actions job retains its overall budget. Normal execution
emits `soodles.timing` records. Acceptance and native checks include the candidate
head. Actions retains the acceptance log. These records are cost observations,
not gates. The Issue-atom foreground entry also logs each owner observation
and each wait, including phase/status and the named pending dependency.
Compare those actual runs to distinguish processing cost from time spent waiting
for Noodle, Actions, and the provider. Test-suite elapsed time alone does not
measure end-to-end delivery latency.

Historical implementation reruns and archived report comparisons are not routine
regression requirements. Keep their evidence unchanged under `docs/`. Before
removing a replay, carry its unique behavior checks into small current-source
fixtures. Test maintenance does not select or replace the external verifier.
The runtime workflow runs selected canonical acceptance. It verifies the locked
release whenever selected physical controls require it. Building a separate
historical Noodle source for a portable evidence packet requires an explicit
evidence-production request. It is not a prerequisite for every Soodles candidate.

PR updates automatically request runtime acceptance. The existing landing owner
verifies merge parents, the accepted candidate tree, and provider-main readback.
A main push does not automatically repeat candidate tests. To request additional
verification of a selected ref, explicitly dispatch the runtime workflow with
an exact base and reason. Test Manager resolves that request. A PR result does
not become a main-head acceptance receipt. Direct main changes require their
own requested verification and cannot claim PR acceptance.

Full-repository quality measurement is an optional manual workflow dispatch.
It requires an exact base and a decision question. The same Test Manager admits
it before analyzer installation. The selected workflow ref fixes its head.
Ordinary PRs do not request this observation. The completed-runtime collector
continues to read normal-run cost. It does not execute the subject or measure
repository code.

Test fixture dependencies follow Python imports, not text mentions. Computed
imports that cannot be resolved require scope correction. They never request
full fallback. Normal test logs include discovery time and each case's setup,
body, teardown, and cleanup duration. Module timing also includes process,
import, and class-fixture costs. Parallel worker durations are not added together
as wall time.

Cost observations preserve returned status. A zero exit never turns refused,
pending, or unknown into passed. New normal timing includes span identity and
observed wall bounds. Original raw logs remain evidence, including legacy logs
with missing bounds. Cost reporting validates finite nonnegative durations and
source/subject correlation.
Wall interval unions, inclusive foreground processing, explicit waits, provider
job seconds, and parallel module seconds are distinct measures. Nested cases
are not added to module costs. Tokens, price, API calls, CPU, and human
attribution remain unknown without supported accounting. Every metric family
reports partial/unknown or an explicit not-required observation, with evidence
and a reason. Measured spans do not assert complete lifecycle coverage.
Existing Test Manager scope and exact-head PR demand remain unchanged.
Missing telemetry never launches another test run.