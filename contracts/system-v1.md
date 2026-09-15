# system-v1: bootstrap claim only

Owner: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).

## RUNTIME.ADMISSION.001

The target lock selects an exact Linux amd64 Noodle release. `runtime_check` validates host, lock fields, file existence, executable permission and binary digest before version execution. A mismatch fails without worktree effects and names the owning command and help entry. Release/tag/archive correspondence is additionally read back by the Actions download step; the local command does not claim a live provider read.

## ACCEPTANCE.BOOTSTRAP.001

`acceptance_verify` requires a clean source root, captures its head/tree, discovers all local unit tests, exercises the actual pinned Noodle worktree commands in an isolated temporary repository, and checks source identity again. The physical oracle checks exact worktree path and HEAD, missing-worktree refusal before a sentinel effect, and cleanup with Git branch/worktree/head readback. Fixture environment excludes provider credentials and live Noodle identities.

`tests/test_admission.py` holds the nearest refusal controls. The actual binary oracle lives in `worktree_probe`, called by canonical acceptance rather than replaced with a mocked Noodle. Unit fixtures with synthetic executables are identified as such; they do not prove release-runtime behavior.

## Authority limits

These are local rejection and runtime evidence boundaries. Every receipt denies landing authority. `runtime.yml` executes candidate code without secrets or write permissions; it is a self-test carrier, not a trusted default-branch verifier. No schedulable Issue ABI, provider lander, Codex generation, recovery transition or generation-closure claim is admitted by this bootstrap.

A candidate cannot approve itself. Initial installation is the owner-requested supervised process below, not a claim that candidate self-tests are an independent trusted verifier.

## LANDING.SUPERVISED.001

Owner: ed3c/soodles#4. `landing.py` and `tests/test_landing.py` own this boundary. The supervisor selects a verifier implementation outside the candidate and pins its SHA-256 in an exact single-Issue claim. The claim binds repository, Issue, PR, head, tree, base head, successful runtime run/attempt, and local worktree. A digest binds bytes; the supervising session supplies initial trust. It is not a signature or an independent correctness oracle.

`landing start` rejects mismatched provider identity before admission. `landing advance` locks and durably replaces a checkpoint before offering an expected-head merge or exact-Issue closure request. It never performs provider writes and never offers either write twice. The GitHub connector is the transport in the supervised fallback. Existing GitHub rules apply; no bypass or permission mutation is offered. Raw snapshots are trusted only as provider readbacks transported by that supervisor, never as candidate-supplied evidence.

Merged state must agree with the expected parent pair and candidate tree before closure can be offered. A completed Issue readback permits `landing reconcile`: validate local origin/clean source/exact candidate, fast-forward main, ask Noodle to remove the worktree, then read back main and worktree/branch absence. Only this writes classification RESOLVED. Interrupted reconciliation can resume from its persisted intent; dirty or divergent local state refuses before cleanup. Retained other worktrees belong to their own admitted Issues.

There is at most one merge request and one closure request per checkpoint, no automatic retries, and no polling loop. Pending unknown outcomes remain pending for owner-specific readback. No production generation closure, autonomous scheduling, crash-safe remote transaction, or independent default-branch verification is claimed. The supervisor must not delete/recreate a checkpoint to repeat an unknown write.
