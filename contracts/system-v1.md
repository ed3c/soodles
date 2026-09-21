# system-v1: bootstrap claim only

Owner: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).

This file specifies behavior, owning transitions and discriminating evidence; prose alone is not an L/R guarantee. `AGENTS.md` routes task execution and skills describe conditional procedures. Only when designing those context surfaces, read [agent-context-design.md](agent-context-design.md) (P-class, experimental under #39). Existing executable requirements below retain their scope and authority.

## RUNTIME.ADMISSION.001

The target lock selects an exact Linux amd64 Noodle release. `runtime_check` validates host, lock fields, file existence, executable permission and binary digest before version execution. A mismatch fails without worktree effects and names the owning command and help entry. Release/tag/archive correspondence is additionally read back by the Actions download step; the local command does not claim a live provider read.

## ACCEPTANCE.BOOTSTRAP.001

`acceptance_verify` requires a clean source root, captures its head/tree, discovers all local unit tests, exercises the actual pinned Noodle worktree commands in an isolated temporary repository, and checks source identity again. The physical oracle checks exact worktree path and HEAD, missing-worktree refusal before a sentinel effect, and cleanup with Git branch/worktree/head readback. Fixture environment excludes provider credentials and live Noodle identities.

`tests/test_admission.py` holds the nearest refusal controls. The actual binary oracle lives in `worktree_probe`, called by canonical acceptance rather than replaced with a mocked Noodle. Unit fixtures with synthetic executables are identified as such; they do not prove release-runtime behavior.

## Authority limits

These are local rejection and runtime evidence boundaries. Every receipt denies landing authority. `runtime.yml` executes candidate code without secrets or write permissions; it is a self-test carrier, not a trusted default-branch verifier. No schedulable Issue ABI, provider lander, Codex generation, recovery transition or generation-closure claim is admitted by this bootstrap.

A candidate cannot approve itself. Initial installation is the owner-requested supervised process below, not a claim that candidate self-tests are an independent trusted verifier.

## LANDING.SUPERVISED.001

Owner: ed3c/soodles#4. `landing.py` and `tests/test_landing.py` own this boundary. The supervisor selects a verifier implementation outside the candidate and pins its SHA-256 in an exact single-Issue claim. Every claim binds repository, Issue, PR, head ref, head, tree, base head and successful runtime run/attempt. A local claim additionally binds `control_root`; a cloud claim omits it. Claim shape carries the Session-selected route without another mutable flag. A digest binds bytes; the supervising session supplies initial trust. It is not a signature or an independent correctness oracle.

`landing start` rejects mismatched provider identity before admission. `landing advance` prepares an expected-head merge or exact-Issue closure intent in the checkpoint. `landing dispatch` revalidates the provider snapshot and durably consumes that intent before emitting the request once. Neither command performs provider writes. The GitHub connector is the transport in the supervised fallback. Existing GitHub rules apply; no bypass or permission mutation is offered. Raw snapshots are trusted only as provider readbacks transported by that supervisor, never as candidate-supplied evidence.

Merged state must agree with the expected parent pair and candidate tree before closure can be offered. For a cloud claim, completed Issue and provider-main readback permits `landing advance` to write RESOLVED: main must equal the merge commit or a complete provider comparison must prove the merge is its ancestor. No control root, shell Git, binary or Noodle call is legal on this route. For a local claim, completed Issue readback instead permits `landing reconcile`: validate local origin/clean source/exact candidate, fast-forward main, ask Noodle to remove the worktree, then read back main and worktree/branch absence. Interrupted local reconciliation can resume from its persisted intent; dirty or divergent local state refuses before cleanup. Retained other worktrees belong to their own admitted Issues.

There is at most one merge request and one closure request per checkpoint, no automatic retries, and no polling loop. Pending unknown outcomes remain pending for owner-specific readback. No production generation closure, autonomous scheduling, crash-safe remote transaction, or independent default-branch verification is claimed. The supervisor must not delete/recreate a checkpoint to repeat an unknown write.

After provider closure, a corrected verifier can resume an `awaiting_reconcile` or interrupted `reconciling` checkpoint through `landing resume`. Same-route recovery changes only the verifier digest. An externally selected local-to-cloud correction may additionally remove `control_root` while every common identity remains fixed, only when there is no execution envelope and any persisted cleanup intent is absent or the exact no-op observation. It records the prior route and returns a fresh provider-readback operation; cloud-to-local migration is forbidden. Both writes must already have matching offered/readback evidence. No migration emits a provider write or itself resolves the checkpoint.

### Interrupted cleanup — ed3c/soodles#6

A reconciling checkpoint may retain its exact admitted branch after Noodle has removed the worktree directory. Before another cleanup request, require that branch to remain at the admitted head and have no checkout at another path. Noodle's existing missing-directory cleanup owns the remaining deletion. A moved branch or foreign checkout refuses before deletion. A resolved checkpoint cannot authorize deletion of a newly appearing branch.

Persist `cleanup_intent` before calling Noodle. It binds observed path presence, branch/main heads, Git executable path/digest, Noodle digest and verifier digest. The same observation cannot issue another cleanup request; changed owner readback or executable capability is required. Existing reconciling checkpoints without this field are read as the prior schema, with all identity checks still required. Path/branch/registration absence and clean main remain prerequisites for RESOLVED.

A legacy local-shaped delivery whose candidate path, branch and worktree registration were never created records that three-way absence as `cleanup_intent.mode=no_op` before local Git synchronization. It never creates or asks Noodle to delete a synthetic worktree. Any matching branch or registration refuses this compatibility path; a native cloud claim never enters local reconcile.

The nearest local-cleanup oracle is `cleanup_oracle.cleanup_recovery_probe`, called by canonical acceptance after the original runtime oracle. It physically kills the pinned Noodle process between worktree removal and branch deletion, exercises the real CLI, and checks positive recovery, moved-branch/foreign-checkout refusals, unchanged-attempt refusal, old-checkpoint compatibility, plus verifier migration and no-op cleanup compatibility. Provider closure fields and the Git fetch transport are local fixture data; native cloud resolution is instead discriminated at the landing/provider boundary.

### Observed Git lock recovery — ed3c/soodles#8

This one atom includes the lock readback producer, retry consumer, checkpoint compatibility and runtime controls. `landing reconcile` asks Git for the absolute target ref-lock path; an existing lock produces `cleanup.ref_lock` before Noodle cleanup. It records `cleanup_blocked` bound to the existing cleanup observation and that path, without deleting the lock or replacing the prior cleanup intent. Repeated blocked readback changes neither deletion state nor checkpoint contents.

An observed disappearance of that same lock for the same cleanup context permits one recovery attempt. Consume `cleanup_blocked` and durably save the new intent before invoking Noodle. Another interruption with unchanged context requires new material evidence. Existing checkpoint records with no blocked-lock observation remain unknown; field absence alone cannot authorize a retry. Existing changed-path/executable capability rules and moved-branch/foreign-checkout controls remain in force. This covers the observed target ref lock; it does not claim every filesystem, packed-ref lock or race is recoverable.

The standalone `cleanup_lock_oracle.py` imports no candidate verdict logic. Its four cases exercise actual Noodle SIGKILL, present/absent locks, legacy unknown state, consumed recovery and changed ownership. Canonical acceptance includes it alongside all prior tests and runtime controls. A candidate copy is still non-authorizing. The supervisor may select and freeze an external copy, evaluate the candidate only as a subject, and independently read Git state to reject false success. Process isolation and external Actions execution are claims only when supported by their exact receipts.

The existing externally selected publishing verifier remains unchanged for this Issue. A changed default-branch tip or merged verifier source does not change that selection. `landing resume` cannot supply its own initial trust. New code and tests can be corrected in the same causal atom without replacing the active judge; a separate authorization is needed to promote a new judge.

### Atomic candidate delivery — ed3c/soodles#97

One causal Issue atom carries its P-class correction and required N-class task, observer, manifest, raw receipts and results through one PR. Candidate heads are immutable attempts: missing evidence, an exact-byte mismatch or a failed runtime blocks merge and is corrected by a new head on that PR, never by rerunning the unchanged head. The terminal head alone may merge after its required exact-head runtime and quality checks pass. The merged main tree then requires its existing runtime and provider readback. A defect discovered after merge starts a new Issue and rollback boundary; it is not evidence that the completed delivery used one PR.

This rule changes no evaluator authority. Frozen external observers judge candidate behavior, the candidate verifier checks committed byte bindings, and provider checks/readback establish only their own R-class claims. One PR may contain P-class source and N-class evidence, but neither class authorizes its own landing.

### Interrupted delivery preparation — ed3c/soodles#10

The same landing owner contains the intent producer, CLI dispatch consumer and schema migration. Schema 2 distinguishes `delivery.status=prepared` from `offered`. Preparing produces no provider request and does not append `writes_offered`. A restarted supervisor can consume that original prepared intent through `landing dispatch`; its checkpoint lock serializes concurrent consumers. Fresh repository/head/base/run readback must still agree before consumption. After the durable offered state, another dispatch refuses and only provider readback can advance. Merge/closure readbacks without this checkpoint's matching offered write cannot be adopted.

Schema 1 pending states migrate conservatively to offered, preserving identities and existing evidence. A missing delivery field in schema 2 or inconsistent `writes_offered` refuses. Migration grants no authority to change an old verifier digest; the supervising claim still binds the selected implementation. Existing schema 1 cleanup and reconciliation records remain supported.

`delivery_oracle.py` is the nearest standalone discriminator, also called by canonical acceptance. It kills real child processes after actual durable saves, observes merge/close preparation recovery, models lost replies with a supervisor-owned provider fixture, checks concurrent first consumption, legacy unknown states and head drift. It imports candidate code only inside the fault-injected child, never into the observing process. The candidate copy is non-authorizing; a supervisor-selected external copy can judge baseline, treatment and planted-negative candidates.

The gap after dispatch persistence but before emission/network execution remains unknown: this atom never guesses non-delivery from a timeout or an unmerged PR. There is no remote exactly-once transaction, automatic retry, separate ledger or bounded-generation completion claim. Checkpoint locking is local and per checkpoint. This Issue's publishing verifier remains the externally frozen pre-candidate implementation; no default-branch tip or newly merged verifier selects itself.

### Base advancement before delivery — ed3c/soodles#16

The existing delivery owner recognizes a coherent forward base change through `landing advance` or the first `landing dispatch`. Original subject, target and runtime identities remain required. A complete supervisor-transported GitHub `base_comparison` must establish old base as the merge base and new base as the final commit. Inconsistent, divergent or truncated readbacks refuse. Before any offered write, persist `readmission_pending` with the observed base and snapshot fingerprint. The old claim remains present but can no longer dispatch, including when an old base readback reappears. The result names `base.head`, its actual/expected values, the landing owner and one supported next help entry. Identical recovery readback does not rewrite the checkpoint.

`landing readmit CHECKPOINT CLAIM READBACK` consumes an explicit fresh supervisor claim under the same checkpoint lock. Repository, Issue, PR, worktree, control root and verifier digest must remain identical. Head, base and runtime run ID must change; the existing exact-head successful CI checks remain mandatory. `base_comparison` proves forward movement from the original base; `candidate_comparison` proves the fresh head contains its new base. If main advanced again after the recorded recovery, `recovery_comparison` must prove forward ancestry from that observed base too. These are complete raw compare responses provided by the supervisor, not candidate declarations. This entry executes neither Git rebase nor provider writes.

One atomic save appends the old claim, prepared delivery and invalidation receipt to `prior_admissions` with classification `SUPERSEDED`, then admits the fresh claim. This classification belongs to the replaced admission, not the Issue. A crash after that save resumes through `advance`; duplicate or concurrent readmission cannot replace it again. Overall resource limits remain external; the command contains no retry or generation loop.

Schema 1 admitted records with an explicit empty offered-write list can follow this path; legacy pending records remain conservatively offered. A base change cannot turn an unknown request into a known rejection. Offered writes continue to require owner readback, and identity/reconciliation checks remain intact. No post-offer retarget, remote exactly-once transaction, live parallel Issues experiment or autonomous scheduler is claimed.

`base_recovery_oracle.py` is the nearest standalone process observer and is included in canonical acceptance. It observes ordinary CLI output, actual SIGKILL after durable invalidation/admission, concurrent consumers and legacy unknown controls using local provider fixtures. Its candidate copy remains non-authorizing. For this atom the supervisor freezes an external observer before candidate acceptance; the active publishing verifier stays unchanged and is never loaded from default-branch tips.

### Supervised correction before an offer — ed3c/soodles#19

`landing invalidate CHECKPOINT` durably withdraws an admitted or prepared, known-unoffered acceptance under the existing checkpoint lock. It consumes no CI verdict or provider snapshot because it only removes permission to dispatch. Preserve the prior claim and prepared intent; repeated invalidation does not rewrite them. Existing base-drift recovery stays intact. The owner returns `landing readmit --help` as the supported next action. A pending explicit amendment cannot dispatch using old green evidence, including after process interruption.

The supervisor amends the same causal Issue and obtains its fresh execution boundary before source changes. Implementations, tests and erroneous candidate gates may be corrected or deleted together. Replace false assertions with discriminating positive/negative behavior controls; do not preserve wrong behavior for test-count stability or erase an unresolved failure to obtain green. This command does not author Issue bodies, inspect every source write, or change required-check policy.

`landing readmit` accepts a changed head and fresh successful exact-head run at the same base after explicit invalidation. Changed bases still require complete forward ancestry; every new candidate must contain its admitted base. Repository, Issue, PR, worktree, control root and external verifier stay identical. Archive the old claim, evidence and intent as SUPERSEDED in the same atomic save. Schema 1 known-empty admissions and existing schema 2 base-drift records remain supported. Offered or legacy-unknown writes require owner readback and cannot enter this path.

The selected external judge is fixed for this acceptance, not a permanent freeze of repository source. Changing its source in this Issue does not promote it into authority. A defect in the active external judge needs an explicit supervisor authority decision and fresh acceptance; the candidate cannot bless its replacement or bypass a required check.

The extended `base_recovery_oracle.py` observes actual child SIGKILL after invalidation/readmission saves, same-base recovery, old/failed/unchanged evidence refusal and unchanged-verifier enforcement. It uses labeled provider fixtures. Green admission, fresh readmission and an emitted merge request all retain null Issue classification. RESOLVED remains route-specific: exact provider completion for cloud, and provider completion plus Git/Noodle reconciliation for local. Actual provider delivery is evidenced separately.

### Owner next-action output — ed3c/soodles#21

`landing.py` owns the `next` projection. Every transition response names the invoked owner, action, phase, classification and next step. A provider readback names GET operations against the admitted repository/Issue/PR/head/run; missing inputs and the resumed operation are explicit. A local input step names the supervisor, required inputs, known checkpoint and structured executable help argv. It never invents a readback path, binary, claim or authority. RESOLVED yields action=stop and next=null without rewriting the checkpoint. These fields are returned projections, not another durable state machine.

The existing connector write payload remains exact inside `request`; transport must consume that payload only. Dispatch persists its offered intent before returning it. All existing head/readback/phase/write guards still execute when the command runs; a previously printed next step confers no execution authority. Prepared delivery requires fresh provider readback; unknown offers lead only to owner readback. Awaiting or interrupted reconciliation names its missing binary input rather than requesting indefinite provider polling.

Structured refusals and human diagnostics derive from one invalid field/value and next action. The actually invoked CLI verb owns the refusal, rather than a substring of the invalid field. Explicit transition refusals can name a different legal recovery operation, with one help route. Parser/input failures are structured too. Old checkpoint schemas retain their existing interpretation; displayed next commands are never used as migration or retry authority.

`delivery_oracle.py` is the nearest standalone CLI/process observer. Alongside existing SIGKILL, concurrent dispatch and lost-response controls, it rejects conflicting next operations and terminal readback output. Its terminal checkpoint is explicitly a fixture, not a live reconciliation claim. Candidate copies remain non-authorizing; supervisor-selected external bytes judge baseline/treatment/planted regression. Existing base-recovery consumers read the same structured projection and unchanged nested connector payload.

N/P/L/R scope follows Noodles' authority classes, not its default-branch verifier topology. Skill guidance is P; inventory/prose/metrics are N; tested local transition refusal is L; actual provider-enforced checks and readbacks are R for their own claims. This contract does not make an owner output infallible. Use pre-offer invalidation for a same-atom correction, preserve unknown writes, and replace incorrect next-command tests with discriminating behavioral controls. A candidate cannot promote its own changed judge.

### Exact comparison readback guidance — ed3c/soodles#25

The existing comparison validator receives the invoked operation, current claim and checkpoint explicitly from its owning call site. Missing or malformed base/candidate/recovery comparisons preserve their exact invalid field/value and return GitHub GET requests keyed by the required readback field, with confirmed base...head SHAs in the admitted repository. Ordinary snapshot identity validation and endpoint SHA validation precede guidance construction; malformed or foreign identity cannot become an automatically corrected provider request. The same owner reason supplies human diagnostics and machine guidance. Re-enter only after the provider readback materially changes; no write retry is offered.

Readmission guidance retains the validated fresh claim in `next.known.claim` and the checkpoint path. It does not invent a claim-file path, binary, provider response or authority choice. Supplying the corrected comparison can reach the existing readmission transition; complete ancestry, exact-head runtime evidence, same-owner identity, unknown-offer and local reconciliation guards remain unchanged. These projections are not stored or replayed from checkpoint history; existing schemas require no migration.

The extended `base_recovery_oracle.py` observes all three comparison fields at actual CLI boundaries, changed-input recovery, malformed endpoint and foreign-repository refusal, checkpoint preservation and existing interruption/legacy controls. Its provider responses remain fixtures. An external copy frozen before implementation rejects baseline missing guidance and planted wrong compare subject/operation; candidate copies are non-authorizing. Skill guidance consumes delivered owner output only after this atom's real merge/closure/reconciliation receipt.

### Dependent merged-commit readback — ed3c/soodles#29

Snapshot validation receives its invoking operation and checkpoint from the existing landing call site. After the ordinary claim, PR, candidate and runtime identity checks, a merged PR requires a complete lowercase commit SHA before the owner constructs a dependent commit GET. Missing or malformed `pr.merge_commit_sha` names that exact field/value and requests fresh PR readback; it never supplies a guessed commit endpoint. Missing or malformed `merge_commit` returns its precise field/value, the invoking operation, known checkpoint and `next.requests.merge_commit` with the confirmed GET. Start/readmit guidance also retains the validated claim without inventing a claim-file path. The owner reason is shared by JSON and human diagnostics.

Corrected raw readback must still prove the exact merge SHA, ordered base/candidate parents and candidate tree. Refusals preserve checkpoint bytes and offered-write history; no write request or runnable transition argv is emitted. Re-enter only after material readback change. Valid data can reach the existing close preparation, but cannot adopt an unoffered merge, reopen an invalid admission, repeat an unknown write or claim Issue resolution. Existing schemas require no new fields or migration; next actions remain derived outputs.

The extended `delivery_oracle.py` drives the real CLI with supervisor-owned provider fixtures, including malformed merge objects, invalid PR SHA, foreign/stale subjects, advance/dispatch ownership, legacy offered history and changed-input recovery through the existing close/crash path. Local planted wrong subject, wrong operation and removed SHA validation are rejected by a frozen external observer. These controls do not prove a live GitHub failure or lower Agent decision cost. Actual provider delivery and isolation carry their own receipts; canonical acceptance and the selected external publisher remain unchanged.

### Cross-repository dependency satisfaction — ed3c/soodles#113, #115

The installed supervisor owns DAG edge selection and carries each exact result
in the immutable landing claim. `dependency_binding.py` validates that list and
projects the producer Issue, PR, merged commit, base branch, merge-to-main
comparison, runtime and jobs as indexed `dependency_N_*` GETs beside the
consumer GETs. Soodles contains no producer/consumer edge registry and exposes
no Agent-facing repository, revision, workflow or dependency policy flag.

Every landing transition validates all selected results before consumer
acceptance. A complete result proves completed Issue closure, merged PR
identity and ordered parents, exact tree, successful exact-head runtime and
that the merged artifact is identical to or an ancestor of current producer
main. Missing evidence, closure alone, foreign repository, wrong revision,
diverged ancestry or missing acceptance step refuses before checkpoint or
provider write and returns the same owner route with exact readbacks. Malformed
or duplicate dependency identities refuse during claim validation.

Eligibility creates no dependency checkpoint. After all selected results pass,
the existing repository profile and landing state machine remain the only
consumer acceptance and effect owners. A claim without dependencies stays
independent; landing never infers that omission proves DAG completeness. The
external supervisor/admission owner must supply the complete set. Route
migration preserves the list exactly. Provider fixtures are L-class
discrimination only; exact provider Issue/PR/run and final delivery readbacks
retain their own R-class scope.
