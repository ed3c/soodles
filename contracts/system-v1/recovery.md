### Interrupted cleanup — ed3c/soodles#6

A reconciling checkpoint may retain its exact admitted branch after Noodle
removes the worktree directory. Before another cleanup request, confirm that
the branch remains at the admitted head and has no checkout at another path.
Noodle's existing missing-directory cleanup owns the remaining deletion.
A moved branch or foreign checkout causes refusal before deletion.
A resolved checkpoint cannot authorize deletion of a newly appearing branch.

A local control root may be a clean, registered detached Git worktree.
Its exact execution envelope must bind the root, and its initial HEAD must
equal the admitted base. During interrupted reconciliation, its HEAD must remain
a descendant of that base and an ancestor of provider main. The landing owner
fast-forwards that detached HEAD. It does not switch the shared main checkout
or create another worktree. Foreign, dirty, or unregistered detached roots
cause refusal before synchronization or Noodle cleanup.

Before calling Noodle, persist `cleanup_intent`. It binds observed path
presence, branch and main heads, Git executable path and digest, Noodle digest,
and verifier digest. The same observation cannot issue another cleanup request.
A changed owner readback or executable capability is required.
Existing reconciling checkpoints without this field use the prior schema.
All identity checks still apply. RESOLVED still requires absent path, branch,
and registration, plus clean main.

For a legacy local-shaped delivery, the candidate path, branch, and worktree
registration may never have been created. Before local Git synchronization,
that delivery records all three absences as `cleanup_intent.mode=no_op`.
It never creates a synthetic worktree or asks Noodle to delete one.
Any matching branch or registration causes refusal of this compatibility path.
A native cloud claim never enters local reconcile.

The nearest local-cleanup oracle is `cleanup_oracle.cleanup_recovery_probe`.
Canonical acceptance calls it only when Test Manager selects that control.
The control kills the pinned Noodle process between worktree removal and branch deletion.
It checks recovery, identity refusals, unchanged attempts and checkpoint compatibility.
It also checks verifier migration and no-op cleanup compatibility.
Provider closure and Git fetch transport use local fixtures.
Native cloud resolution uses the landing/provider boundary.

### Observed Git lock recovery — ed3c/soodles#8

This atom includes the lock readback producer, retry consumer, checkpoint
compatibility, and runtime controls. `landing reconcile` asks Git for the
absolute target ref-lock path. If the lock exists, the owner produces
`cleanup.ref_lock` before Noodle cleanup. It records `cleanup_blocked`, bound
to the existing cleanup observation and that path. It does not delete the lock
or replace the prior cleanup intent. Repeated blocked readback changes neither
deletion state nor checkpoint contents.

If that same lock disappears in the same cleanup context, the observation
permits one recovery attempt. Consume `cleanup_blocked` and durably save the
new intent before calling Noodle. Another interruption with unchanged context
requires new material evidence. Existing checkpoint records without a blocked-lock
observation remain unknown. Field absence alone cannot authorize a retry.
Existing changed-path and executable-capability rules remain in force, as do
moved-branch and foreign-checkout controls. This covers the observed target ref
lock. It does not establish recovery for every filesystem, packed-ref lock, or race.

The standalone `cleanup_lock_oracle.py` imports no candidate verdict logic.
Its four cases exercise actual Noodle SIGKILL, present and absent locks, legacy
unknown state, consumed recovery, and changed ownership. Canonical acceptance
runs it only when Test Manager selects the cleanup lock recovery control.
This recipe does not request all prior tests or other runtime controls.
A candidate copy remains non-authorizing. The supervisor may select and freeze
an external copy. The supervisor may evaluate the candidate only as a subject
and independently read Git state to reject false success. Process isolation
and external Actions execution require their exact receipts to support those claims.

The existing externally selected publishing verifier remains unchanged for
this Issue. Neither a changed default-branch tip nor merged verifier source
changes that selection. `landing resume` cannot supply its own initial trust.
New code and tests can be corrected in the same causal atom without replacing
the active judge. Promoting a new judge requires separate authorization.

### Interrupted delivery preparation — ed3c/soodles#10

The same landing owner contains the intent producer, CLI dispatch consumer,
and schema migration. Schema 2 distinguishes `delivery.status=prepared` from
`offered`. Preparation produces no provider request and does not append
`writes_offered`. A restarted supervisor can consume the original prepared
intent through `landing dispatch`. The checkpoint lock serializes concurrent
consumers. Before consumption, fresh repository, head, base, and run readback
must still agree. After the offered state is durable, another dispatch refuses.
Only provider readback can advance. Merge or closure readbacks cannot be adopted
without this checkpoint's matching offered write.

Schema 1 pending states migrate conservatively to offered. Migration preserves
identities and existing evidence. A missing delivery field in schema 2 or
inconsistent `writes_offered` causes refusal. Migration grants no authority to
change an old verifier digest. The supervising claim still binds the selected
implementation. Existing schema 1 cleanup and reconciliation records remain
supported.

`delivery_oracle.py` is the nearest standalone discriminator. Canonical
acceptance calls it only when Test Manager selects the delivery recovery control. It kills real child processes after actual durable
saves and observes merge and close preparation recovery. It models lost replies
with a supervisor-owned provider fixture. It checks concurrent first consumption,
legacy unknown states, and head drift. Only the fault-injected child imports
candidate code. The observing process never imports it. The candidate copy
is non-authorizing. A supervisor-selected external copy can judge baseline,
treatment, and planted-negative candidates.

After dispatch persistence but before emission or network execution, the outcome
remains unknown. This atom never infers non-delivery from a timeout or an unmerged
PR. It provides no remote exactly-once transaction, automatic retry, separate
ledger, or bounded-generation completion claim. Checkpoint locking is local
and per checkpoint. This Issue's publishing verifier remains the externally
frozen pre-candidate implementation. No default-branch tip or newly merged
verifier selects itself.

### Base advancement before delivery — ed3c/soodles#16

Through `landing advance` or the first `landing dispatch`, the existing
delivery owner recognizes a coherent forward base change. Original subject,
target, and runtime identities remain required. A complete GitHub
`base_comparison`, transported by the supervisor, must establish the old base
as the merge base and the new base as the final commit. Inconsistent, divergent,
or truncated readbacks cause refusal.

Before any offered write, persist `readmission_pending` with the observed base
and snapshot fingerprint. The old claim remains present but can no longer
dispatch, even if an old base readback reappears. The result names `base.head`,
its actual and expected values, the landing owner, and one supported next help
entry. Identical recovery readback does not rewrite the checkpoint.

`landing readmit CHECKPOINT CLAIM READBACK` consumes an explicit fresh
supervisor claim under the same checkpoint lock. Repository, Issue, PR,
worktree, control root, and verifier digest must remain identical. Head, base,
and runtime run ID must change. Existing exact-head successful CI checks remain
mandatory. `base_comparison` proves forward movement from the original base.
`candidate_comparison` proves that the fresh head contains its new base.
If main advanced again after the recorded recovery, `recovery_comparison` must
also prove forward ancestry from that observed base. The supervisor supplies
complete raw compare responses. Candidate declarations cannot replace them.
This entry executes neither Git rebase nor provider writes.

One atomic save appends the old claim, prepared delivery, and invalidation
receipt to `prior_admissions` with classification `SUPERSEDED`. That same save
admits the fresh claim. The classification belongs to the replaced admission,
not the Issue. After a crash following the save, execution resumes through
`advance`. Duplicate or concurrent readmission cannot replace the admission
again. Overall resource limits remain external. The command contains no retry
or generation loop.

Schema 1 admitted records may follow this path when they have an explicit
empty offered-write list. Legacy pending records remain conservatively offered.
A base change cannot turn an unknown request into a known rejection. Offered
writes still require owner readback. Identity and reconciliation checks remain
intact. This boundary claims no post-offer retarget, remote exactly-once
transaction, live parallel Issues experiment, or autonomous scheduler.

`base_recovery_oracle.py` is the nearest standalone process observer.
Canonical acceptance runs it only when Test Manager selects the base recovery control.
With local provider fixtures, it observes
ordinary CLI output, actual SIGKILL after durable invalidation and admission,
concurrent consumers, and legacy unknown controls. Its candidate copy remains
non-authorizing. For this atom, the supervisor freezes an external observer
before candidate acceptance. The active publishing verifier stays unchanged
and is never loaded from default-branch tips.

### Supervised correction before an offer — ed3c/soodles#19

Under the existing checkpoint lock, `landing invalidate CHECKPOINT` durably
withdraws an admitted or prepared acceptance known to be unoffered. It consumes
no CI verdict or provider snapshot because it only removes permission to dispatch.
Preserve the prior claim and prepared intent. Repeated invalidation does not
rewrite them. Existing base-drift recovery stays intact. The owner returns
`landing readmit --help` as the supported next action. A pending explicit
amendment cannot dispatch using old green evidence, even after process interruption.

Before source changes, the supervisor amends the same causal Issue and obtains
its fresh execution boundary. Implementations, tests, and erroneous candidate
gates may be corrected or deleted together. Replace false assertions with
positive and negative controls that distinguish behavior. Do not preserve wrong
behavior to keep a stable test count. Do not erase an unresolved failure to
obtain green. This command does not author Issue bodies, inspect every source
write, or change required-check policy.

After explicit invalidation, `landing readmit` accepts a changed head and
fresh successful exact-head run at the same base. Changed bases still require
complete forward ancestry. Every new candidate must contain its admitted base.
Repository, Issue, PR, worktree, control root, and external verifier stay
identical. Archive the old claim, evidence, and intent as SUPERSEDED in the same
atomic save. Schema 1 known-empty admissions and existing schema 2 base-drift
records remain supported. Offered or legacy-unknown writes require owner
readback and cannot enter this path.

The selected external judge is fixed for this acceptance. Repository source
is not permanently frozen. Changing that source in this Issue does not give it
authority. A defect in the active external judge needs an explicit supervisor
authority decision and fresh acceptance. The candidate cannot approve its
replacement or bypass a required check.

The extended `base_recovery_oracle.py` observes actual child SIGKILL after
invalidation and readmission saves. It checks same-base recovery, refusal of
old, failed, or unchanged evidence, and enforcement of the unchanged verifier.
It uses labeled provider fixtures. Green admission, fresh readmission, and an
emitted merge request all retain null Issue classification. RESOLVED remains
route-specific. Cloud resolution requires exact provider completion. Local
resolution requires provider completion plus Git/Noodle reconciliation.
Actual provider delivery has separate evidence.
