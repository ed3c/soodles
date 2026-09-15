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

`landing start` rejects mismatched provider identity before admission. `landing advance` prepares an expected-head merge or exact-Issue closure intent in the checkpoint. `landing dispatch` revalidates the provider snapshot and durably consumes that intent before emitting the request once. Neither command performs provider writes. The GitHub connector is the transport in the supervised fallback. Existing GitHub rules apply; no bypass or permission mutation is offered. Raw snapshots are trusted only as provider readbacks transported by that supervisor, never as candidate-supplied evidence.

Merged state must agree with the expected parent pair and candidate tree before closure can be offered. A completed Issue readback permits `landing reconcile`: validate local origin/clean source/exact candidate, fast-forward main, ask Noodle to remove the worktree, then read back main and worktree/branch absence. Only this writes classification RESOLVED. Interrupted reconciliation can resume from its persisted intent; dirty or divergent local state refuses before cleanup. Retained other worktrees belong to their own admitted Issues.

There is at most one merge request and one closure request per checkpoint, no automatic retries, and no polling loop. Pending unknown outcomes remain pending for owner-specific readback. No production generation closure, autonomous scheduling, crash-safe remote transaction, or independent default-branch verification is claimed. The supervisor must not delete/recreate a checkpoint to repeat an unknown write.

After provider closure, a corrected verifier can resume an interrupted reconciliation through `landing resume`: only the verifier digest may change under a fresh supervisor claim; preserve prior digest and all provider/local identities and write intents. This emits no provider write. The real bootstrap reconciliation exposed missing proxy transport in the fixture-only environment; network fetch therefore retains standard proxy variables while excluding provider credentials and Git environment overrides.

### Interrupted cleanup — ed3c/soodles#6

A reconciling checkpoint may retain its exact admitted branch after Noodle has removed the worktree directory. Before another cleanup request, require that branch to remain at the admitted head and have no checkout at another path. Noodle's existing missing-directory cleanup owns the remaining deletion. A moved branch or foreign checkout refuses before deletion. A resolved checkpoint cannot authorize deletion of a newly appearing branch.

Persist `cleanup_intent` before calling Noodle. It binds observed path presence, branch/main heads, Git executable path/digest, Noodle digest and verifier digest. The same observation cannot issue another cleanup request; changed owner readback or executable capability is required. Existing reconciling checkpoints without this field are read as the prior schema, with all identity checks still required. Path/branch/registration absence and clean main remain prerequisites for RESOLVED.

The nearest oracle is `cleanup_oracle.cleanup_recovery_probe`, called by canonical acceptance after the original runtime oracle. It physically kills the pinned Noodle process between worktree removal and branch deletion, exercises the real CLI, and checks positive recovery, moved-branch/foreign-checkout refusals, unchanged-attempt refusal, and old-checkpoint compatibility. Provider closure fields and the Git fetch transport are local fixture data; it makes no provider requests and does not claim production provider-crash recovery.

### Observed Git lock recovery — ed3c/soodles#8

This one atom includes the lock readback producer, retry consumer, checkpoint compatibility and runtime controls. `landing reconcile` asks Git for the absolute target ref-lock path; an existing lock produces `cleanup.ref_lock` before Noodle cleanup. It records `cleanup_blocked` bound to the existing cleanup observation and that path, without deleting the lock or replacing the prior cleanup intent. Repeated blocked readback changes neither deletion state nor checkpoint contents.

An observed disappearance of that same lock for the same cleanup context permits one recovery attempt. Consume `cleanup_blocked` and durably save the new intent before invoking Noodle. Another interruption with unchanged context requires new material evidence. Existing checkpoint records with no blocked-lock observation remain unknown; field absence alone cannot authorize a retry. Existing changed-path/executable capability rules and moved-branch/foreign-checkout controls remain in force. This covers the observed target ref lock; it does not claim every filesystem, packed-ref lock or race is recoverable.

The standalone `cleanup_lock_oracle.py` imports no candidate verdict logic. Its four cases exercise actual Noodle SIGKILL, present/absent locks, legacy unknown state, consumed recovery and changed ownership. Canonical acceptance includes it alongside all prior tests and runtime controls. A candidate copy is still non-authorizing. The supervisor may select and freeze an external copy, evaluate the candidate only as a subject, and independently read Git state to reject false success. Process isolation and external Actions execution are claims only when supported by their exact receipts.

The existing externally selected publishing verifier remains unchanged for this Issue. A changed default-branch tip or merged verifier source does not change that selection. `landing resume` cannot supply its own initial trust. New code and tests can be corrected in the same causal atom without replacing the active judge; a separate authorization is needed to promote a new judge.

### Interrupted delivery preparation — ed3c/soodles#10

The same landing owner contains the intent producer, CLI dispatch consumer and schema migration. Schema 2 distinguishes `delivery.status=prepared` from `offered`. Preparing produces no provider request and does not append `writes_offered`. A restarted supervisor can consume that original prepared intent through `landing dispatch`; its checkpoint lock serializes concurrent consumers. Fresh repository/head/base/run readback must still agree before consumption. After the durable offered state, another dispatch refuses and only provider readback can advance. Merge/closure readbacks without this checkpoint's matching offered write cannot be adopted.

Schema 1 pending states migrate conservatively to offered, preserving identities and existing evidence. A missing delivery field in schema 2 or inconsistent `writes_offered` refuses. Migration grants no authority to change an old verifier digest; the supervising claim still binds the selected implementation. Existing schema 1 cleanup and reconciliation records remain supported.

`delivery_oracle.py` is the nearest standalone discriminator, also called by canonical acceptance. It kills real child processes after actual durable saves, observes merge/close preparation recovery, models lost replies with a supervisor-owned provider fixture, checks concurrent first consumption, legacy unknown states and head drift. It imports candidate code only inside the fault-injected child, never into the observing process. The candidate copy is non-authorizing; a supervisor-selected external copy can judge baseline, treatment and planted-negative candidates.

The gap after dispatch persistence but before emission/network execution remains unknown: this atom never guesses non-delivery from a timeout or an unmerged PR. There is no remote exactly-once transaction, automatic retry, separate ledger or bounded-generation completion claim. Checkpoint locking is local and per checkpoint. This Issue's publishing verifier remains the externally frozen pre-candidate implementation; no default-branch tip or newly merged verifier selects itself.
