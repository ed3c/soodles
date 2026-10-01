## RUNTIME.ADMISSION.001

The target lock selects an exact Linux amd64 Noodle release. `runtime_check` validates host, lock fields, file existence, executable permission and binary digest before version execution. A mismatch fails without worktree effects and names the owning command and help entry. Release/tag/archive correspondence is additionally read back by the Actions download step; the local command does not claim a live provider read.

## ACCEPTANCE.BOOTSTRAP.001

`acceptance_verify` requires a clean source root, captures its head/tree, selects affected unit and physical controls against the provider base; selected worktree controls exercise the pinned Noodle commands in an isolated temporary repository, and checks source identity again. The physical oracle checks exact worktree path and HEAD, missing-worktree refusal before a sentinel effect, and cleanup with Git branch/worktree/head readback. Fixture environment excludes provider credentials and live Noodle identities.

`tests/test_admission.py` holds the nearest refusal controls. The actual binary oracle lives in `worktree_probe`, called by canonical acceptance rather than replaced with a mocked Noodle. Unit fixtures with synthetic executables are identified as such; they do not prove release-runtime behavior.


Routine acceptance covers current executable behavior: each distinct refusal,
effect boundary and recovery control remains testable against the candidate.
The Test Manager Skill is the single P-class scope owner; `test_manager.py`
resolves its request for local and canonical callers and runs unit controls.
No caller predicts or automatically escalates to full coverage. The manager
consumes a concrete full request or selects named controls from traced changed
behavior/consumers. Shared filenames, selector changes, removed tests, unknown
inputs, failures and missing CI bases are not full-coverage requests.
`./soodles test` compares local changes against HEAD; `--base EXACT_SHA` includes
committed changes. `--module` and `--control` name on-demand local coverage with
`--reason`; `--plan` describes it without execution. `--full` explicitly requests
all coverage supported by that entry. Missing/empty requested modules refuse.
Canonical acceptance uses the same manager; it requires the admitted base or an
explicit coverage request. Omitting base no longer means full acceptance. Actions
supplies the provider base; missing base requires readback. Unknown paths or
removed tests produce `needs_scope` before execution. The supervising Agent
traces the impact and supplies named controls or corrects the existing reusable
map; this is not a second approval or reason to ask the user to build an input.
Prose-only changes require review, with no runtime behavior claim. Changed scope,
base, paths, reasons and unresolved inputs are preserved in the manager result.
Selected test modules run in up to four independent processes, checking executed
test identities against discovery. Failure, skip, missing/empty selected modules
or incomplete execution refuses. An explicitly empty plan says `not_required`,
not all-tests-passed. Unexecuted physical controls have no success/residue claim.
The local test command covers unit tests only; its plan also names physical
controls that remain with canonical acceptance. Release download and binary
admission occur only when physical controls require them.
There is no fixed 120-second suite deadline; external operations retain their
own deadlines and the Actions job retains its overall budget. Normal execution
emits `soodles.timing` records, with candidate head on acceptance/native checks,
and Actions retains the acceptance log. These are cost observations, not gates.
The Issue-atom foreground entry also logs each owner observation and each wait,
including phase/status and the named pending dependency. Compare those actual
runs to distinguish processing cost from Noodle, Actions and provider waiting;
test-suite elapsed time alone is not end-to-end delivery latency.
Historical implementation reruns and archived report comparisons are not routine
regression requirements. Keep their evidence unchanged under `docs/`, and carry
unique behavior checks into small current-source fixtures before removing a
replay. Test maintenance does not select or replace the external verifier.
The runtime workflow runs selected canonical acceptance and verifies the locked
release whenever selected physical controls require it;
building a separate historical Noodle source for a portable evidence packet is
an explicitly requested evidence-production operation, not a prerequisite of
every Soodles candidate.
