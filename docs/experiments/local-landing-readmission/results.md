# Terminal local landing readmission — Issue #173

The accepted #156 PR #172 head `60fa3a84350c5f701f37976a511ac114a5a9cfc4` could not enter landing: its original publisher refused the root-scoped Noodle order before creating a checkpoint or offering a write. The old terminal activation also used the PR publication branch as `claim.worktree`. `raw/baseline.json` pins those observations and the original authorization/native claim.

This correction derives the Noodle worktree from a pinned native publication claim, leaves the PR ref in `publication_branch`, and lets the existing issue-atom command adopt one externally selected pre-write activation. It checks the original refusal, publisher bytes, candidate/run/order identity and admitted checkpoint before persisting the continuation. Historical #156 instruction hashes are checked against its delivered commit, while the frozen oracle still replays against current code; no old manifest is rewritten.

The compatible external publisher activated #156 and emitted the merge and closure requests. Fresh provider readback confirmed PR #172 merged and Issue #156 closed; the checkpoint records both offers and is `awaiting_reconcile` with no RESOLVED classification. Reconciliation then refused because the Codex-managed control root has detached HEAD. That new post-merge correction is [#175](https://github.com/ed3c/soodles/issues/175). This Issue's result is a verified activation and provider handoff, not local resolution.

`raw/positive.json` and `raw/tests.txt` record physical controls and all 390 repository tests passing on the rebased candidate. These local results and the earlier exact-head runtime are non-authorizing; the final head requires its own Linux Actions acceptance and external landing readback.
