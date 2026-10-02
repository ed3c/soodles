# Issue 199: context supply and worker-owned outcome follow-up

The fresh comparison selected implementation `e963c132d688f40dec543474b2cc0bf674d59f72`.
Self-review found that malformed admitted `carrier.codex` could raise an
unstructured exception. The first readiness head
`f2a15539e8febf8bed417b779fd0984405203383` was therefore explicitly superseded.
The replacement adds the type discriminator and its subprocess control.
The external supervisor preserves readiness revisions. These are experiment
handoffs, not lifecycle state or landing authority.

## Product evidence

The fixed external actual-Noodle oracle passed against this implementation.
`product-results.json` preserves its complete stdout. This includes completed,
blocked and failed effects, exact readbacks, duplicate refusals, and controls for
invalid identity, admission and binary. Separate unit controls cover foreign or
missing role, missing context, malformed carrier, empty message, and unknown
outcome. They also cover committed completion, process failure, contradictory or
duplicated readback, and malformed event logs. No provider writes occur in these controls.

The original fixed system-context product observer also passed at the selected
implementation head. It selected exactly common plus instruction-context, with
3,450 selected bytes. It checked ten frozen files and left candidate state
unchanged. Its raw result is preserved below. Original comparison files and
frozen source bytes remain unchanged, including original selection baseline
truncation. That baseline remains INCONCLUSIVE, not PASS.

### Retained failed product attempt

The first follow-up product invocation failed because the adapter refused a
missing `events.ndjson` before the first event. Evaluation of the actual Noodle
writer established that this is a legal first-append case after session identity
validation. The correction allows an absent log only before the effect.
Post-effect readback must exist and match. This was one failed attempt, followed
by PASS under the unchanged oracle. The exact stderr is retained below.
`baseline-refusal.json` separately preserves the earlier stopped writer's
missing-stage_message failure. No event was fabricated into that session.

## Measurement and attribution

The eval-audit found a routing and capability mismatch. Binary help did not
provide the typed payload schema. Product assessment uses executable identity
and effect discriminators and the fixed actual writer. Agent assessment uses
separately supplied fresh consumer operations and independent confirmation.
Code-based outcomes need no subjective LLM judge. The small scoped pairs do not
establish general efficiency, token savings or universal nonregression.
Recorded operations are not a complete native platform transcript. Unavailable
telemetry stays unknown. The change combines supplied execute instructions and
the executable interface. Any supported improvement therefore cannot be attributed
to either component alone.

## Provider boundary

All observations have `authorizes_landing=false`. The worker's eventual typed outcome reports this bounded implementation/evidence task only. Native publication readiness, exact-head Linux Actions acceptance, publication/merge/Issue closure and Git/Noodle reconciliation remain with the existing lifecycle and fixed external owners. No Issue resolution is claimed here.

## First product failure (raw stderr)

```text
Traceback (most recent call last):
  File "/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/outcome_oracle.py", line 118, in <module>
    print(json.dumps(verify(sys.argv[1], sys.argv[2]), indent=2))
                     ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/outcome_oracle.py", line 97, in verify
    assert result['exit_status'] == 0 and value['status'] == 'recorded', (label, result)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('completed', {'argv': ['/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/stage-outcome', 'completed', 'fixture observation'], 'exit_status': 1, 'stdout': '{"status": "refused", "invalid": {"field": "worker.events", "value": "[Errno 2] No such file or directory: \'/private/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/tmpxlyylp0k/control/.noodle/sessions/soodles-18-0-execute-session/events.ndjson\'"}, "next": {"kind": "input", "owner": "Noodle", "required": ["current_session_event_readback"]}, "authorizes_landing": false}\n', 'stderr': ''})
```

## Current system-context observer (raw stdout)

```json
{
  "classification": "PASS",
  "source_head": "e963c132d688f40dec543474b2cc0bf674d59f72",
  "selected_bytes": 3450,
  "selected_paths": [
    "contracts/system-v1/common.md",
    "contracts/system-v1/instruction-context.md"
  ],
  "all_frozen_files": 10,
  "processes": [
    {
      "argv": [
        "/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/system-context",
        "contracts/system-v1/instruction-context.md"
      ],
      "exit": 0,
      "stdout": "{\n  \"owner\": \"soodles.system-context\",\n  \"status\": \"ready\",\n  \"source_head\": \"e963c132d688f40dec543474b2cc0bf674d59f72\",\n  \"paths\": {\n    \"contracts/system-v1/common.md\": {\n      \"requires\": []\n    },\n    \"contracts/system-v1/instruction-context.md\": {\n      \"requires\": [\n        \"contracts/system-v1/common.md\"\n      ]\n    }\n  },\n  \"instruction_paths\": [\n    \"contracts/system-v1/common.md\",\n    \"contracts/system-v1/instruction-context.md\"\n  ],\n  \"instruction_pins\": [\n    {\n      \"path\": \"contracts/system-v1/common.md\",\n      \"sha256\": \"b672753179d25e6b7699b5c5f6792ce02f6262f191452ce92ab02d49fb07ccfe\"\n    },\n    {\n      \"path\": \"contracts/system-v1/instruction-context.md\",\n      \"sha256\": \"ae18e977b72d3a3336c79bb9cd85fa04166fcf5ed4695fba8f22b1a073877b14\"\n    }\n  ],\n  \"instruction_context\": {\n    \"source_head\": \"e963c132d688f40dec543474b2cc0bf674d59f72\",\n    \"files\": [\n      {\n        \"path\": \"contracts/system-v1/common.md\",\n        \"sha256\": \"b672753179d25e6b7699b5c5f6792ce02f6262f191452ce92ab02d49fb07ccfe\",\n        \"content\": \"# system-v1: bootstrap claim only\\n\\nOwner: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).\\n\\nThis file specifies behavior, owning transitions and discriminating evidence; prose alone is not an L/R guarantee. `AGENTS.md` routes task execution and skills describe conditional procedures. Only when designing those context surfaces, read [agent-context-design.md](../agent-context-design.md) (P-class, experimental under #39). Existing executable requirements below retain their scope and authority.\\n\\n## Authority limits\\n\\nThese are local rejection and runtime evidence boundaries. Every receipt denies landing authority. `runtime.yml` executes candidate code without secrets or write permissions; it is a self-test carrier, not a trusted default-branch verifier. No schedulable Issue ABI, provider lander, Codex generation, recovery transition or generation-closure claim is admitted by this bootstrap.\\n\\nA candidate cannot approve itself. Initial installation is the owner-requested supervised process in [landing.md](landing.md), not a claim that candidate self-tests are an independent trusted verifier.\\n\\n\"\n      },\n      {\n        \"path\": \"contracts/system-v1/instruction-context.md\",\n        \"sha256\": \"ae18e977b72d3a3336c79bb9cd85fa04166fcf5ed4695fba8f22b1a073877b14\",\n        \"content\": \"### Complete admitted child contract \\u2014 ed3c/soodles#135\\n\\nSoodles Issue admission validates the structured Issue contract.\\n`issue_execution.projection` delivers that complete `binding['contract']`\\nalongside the existing exact identity and bounded task in both automatic and\\nsupervised stage prompts. The implementation child consumes it without a\\nmandatory duplicate GitHub read. Missing contract returns to the existing\\nadmission owner; an amended body requires the supervisor's fresh envelope.\\n\\nInstalled-entry provider freshness and exact worker/owner prompt comparisons\\nremain enforced: an omitted or altered contract refuses before worker execution.\\n`tests/test_issue_execution.py` checks full delivery, prompt tampering, stale\\nprovider refusal and legal unchanged execution using local provider/owner fixtures.\\nThose controls do not prove child behavior; the externally prepared bounded\\ncomparison supplies only its observed scope, with missing behavior evidence\\nremaining INCONCLUSIVE. Publication readiness, exact-head Linux acceptance,\\nlanding readbacks and reconciliation retain their existing owners and authority.\\n\\n## Local selected-instruction activation\\n\\nThe external supervisor may require exact task instructions through schema-3\\nIssue-atom authorization. Its nonempty `instruction_pins` list selects only\\n`{path, sha256}` regular UTF-8 files from the authorized `base_head`. Soodles\\nvalidates the selection before creating the Issue and resolves committed bytes\\nagain when producing admission. Schema-2 execution envelopes carry\\n`execution.instruction_context = {source_head, files}`; each file carries\\n`path`, `sha256`, and `content`, and source_head equals execution.source_head.\\nThe complete context is projected unchanged into the canonical stage prompt and\\nchecked before worker launch. Missing, duplicate, traversing, wrong-version or\\ntampered selected input fails before its dependent effects, with the existing\\nowning continuation. Schema-2 authorization and schema-1 envelopes remain legal\\nwithout claiming selected-instruction activation. No new scheduler, policy flag\\nor provider route is introduced. This L boundary proves exact context supply\\nand refusal; P-class adherence needs a separate fresh-consumer observation. It\\ndoes not infer all P-class changes or promote instructions into landing authority.\\n\"\n      }\n    ]\n  },\n  \"authorizes_landing\": false\n}\n",
      "stderr": ""
    },
    {
      "argv": [
        "/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/system-context",
        "contracts/system-v1/missing.md"
      ],
      "exit": 1,
      "stdout": "{\n  \"owner\": \"soodles.system-context\",\n  \"status\": \"refused\",\n  \"invalid\": {\n    \"field\": \"roots.path\",\n    \"value\": \"contracts/system-v1/missing.md\"\n  },\n  \"next\": {\n    \"kind\": \"input\",\n    \"owner\": \"Soodles Issue admission\",\n    \"required\": [\n      \"valid_committed_system_context_selection\"\n    ]\n  },\n  \"authorizes_landing\": false\n}\n",
      "stderr": ""
    },
    {
      "argv": [
        "/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/system-context",
        "../contracts/system-v1.md"
      ],
      "exit": 1,
      "stdout": "{\n  \"owner\": \"soodles.system-context\",\n  \"status\": \"refused\",\n  \"invalid\": {\n    \"field\": \"roots.path\",\n    \"value\": \"../contracts/system-v1.md\"\n  },\n  \"next\": {\n    \"kind\": \"input\",\n    \"owner\": \"Soodles Issue admission\",\n    \"required\": [\n      \"valid_committed_system_context_selection\"\n    ]\n  },\n  \"authorizes_landing\": false\n}\n",
      "stderr": ""
    },
    {
      "argv": [
        "/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/system-context",
        "/etc/passwd"
      ],
      "exit": 1,
      "stdout": "{\n  \"owner\": \"soodles.system-context\",\n  \"status\": \"refused\",\n  \"invalid\": {\n    \"field\": \"roots.path\",\n    \"value\": \"/etc/passwd\"\n  },\n  \"next\": {\n    \"kind\": \"input\",\n    \"owner\": \"Soodles Issue admission\",\n    \"required\": [\n      \"valid_committed_system_context_selection\"\n    ]\n  },\n  \"authorizes_landing\": false\n}\n",
      "stderr": ""
    },
    {
      "argv": [
        "/Users/neon/.codex/worktrees/context-outcome/soodles/.worktrees/soodles-199-0dae70bd34ea-0-execute/system-context",
        "contracts/system-v1/recovery.md",
        "contracts/system-v1/instruction-context.md"
      ],
      "exit": 0,
      "stdout": "{\n  \"owner\": \"soodles.system-context\",\n  \"status\": \"ready\",\n  \"source_head\": \"e963c132d688f40dec543474b2cc0bf674d59f72\",\n  \"paths\": {\n    \"contracts/system-v1/common.md\": {\n      \"requires\": []\n    },\n    \"contracts/system-v1/instruction-context.md\": {\n      \"requires\": [\n        \"contracts/system-v1/common.md\"\n      ]\n    },\n    \"contracts/system-v1/landing.md\": {\n      \"requires\": [\n        \"contracts/system-v1/common.md\"\n      ]\n    },\n    \"contracts/system-v1/recovery.md\": {\n      \"requires\": [\n        \"contracts/system-v1/common.md\",\n        \"contracts/system-v1/landing.md\"\n      ]\n    }\n  },\n  \"instruction_paths\": [\n    \"contracts/system-v1/common.md\",\n    \"contracts/system-v1/instruction-context.md\",\n    \"contracts/system-v1/landing.md\",\n    \"contracts/system-v1/recovery.md\"\n  ],\n  \"instruction_pins\": [\n    {\n      \"path\": \"contracts/system-v1/common.md\",\n      \"sha256\": \"b672753179d25e6b7699b5c5f6792ce02f6262f191452ce92ab02d49fb07ccfe\"\n    },\n    {\n      \"path\": \"contracts/system-v1/instruction-context.md\",\n      \"sha256\": \"ae18e977b72d3a3336c79bb9cd85fa04166fcf5ed4695fba8f22b1a073877b14\"\n    },\n    {\n      \"path\": \"contracts/system-v1/landing.md\",\n      \"sha256\": \"fbfacc853a222bc08817d744b278e9dd8184fe93264c4ea8ca2bf76b19fb34ff\"\n    },\n    {\n      \"path\": \"contracts/system-v1/recovery.md\",\n      \"sha256\": \"7e83ad5331e8383717d7809920ed3528fe82f3309b8a9a0f91e188a9785f0917\"\n    }\n  ],\n  \"instruction_context\": {\n    \"source_head\": \"e963c132d688f40dec543474b2cc0bf674d59f72\",\n    \"files\": [\n      {\n        \"path\": \"contracts/system-v1/common.md\",\n        \"sha256\": \"b672753179d25e6b7699b5c5f6792ce02f6262f191452ce92ab02d49fb07ccfe\",\n        \"content\": \"# system-v1: bootstrap claim only\\n\\nOwner: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).\\n\\nThis file specifies behavior, owning transitions and discriminating evidence; prose alone is not an L/R guarantee. `AGENTS.md` routes task execution and skills describe conditional procedures. Only when designing those context surfaces, read [agent-context-design.md](../agent-context-design.md) (P-class, experimental under #39). Existing executable requirements below retain their scope and authority.\\n\\n## Authority limits\\n\\nThese are local rejection and runtime evidence boundaries. Every receipt denies landing authority. `runtime.yml` executes candidate code without secrets or write permissions; it is a self-test carrier, not a trusted default-branch verifier. No schedulable Issue ABI, provider lander, Codex generation, recovery transition or generation-closure claim is admitted by this bootstrap.\\n\\nA candidate cannot approve itself. Initial installation is the owner-requested supervised process in [landing.md](landing.md), not a claim that candidate self-tests are an independent trusted verifier.\\n\\n\"\n      },\n      {\n        \"path\": \"contracts/system-v1/instruction-context.md\",\n        \"sha256\": \"ae18e977b72d3a3336c79bb9cd85fa04166fcf5ed4695fba8f22b1a073877b14\",\n        \"content\": \"### Complete admitted child contract \\u2014 ed3c/soodles#135\\n\\nSoodles Issue admission validates the structured Issue contract.\\n`issue_execution.projection` delivers that complete `binding['contract']`\\nalongside the existing exact identity and bounded task in both automatic and\\nsupervised stage prompts. The implementation child consumes it without a\\nmandatory duplicate GitHub read. Missing contract returns to the existing\\nadmission owner; an amended body requires the supervisor's fresh envelope.\\n\\nInstalled-entry provider freshness and exact worker/owner prompt comparisons\\nremain enforced: an omitted or altered contract refuses before worker execution.\\n`tests/test_issue_execution.py` checks full delivery, prompt tampering, stale\\nprovider refusal and legal unchanged execution using local provider/owner fixtures.\\nThose controls do not prove child behavior; the externally prepared bounded\\ncomparison supplies only its observed scope, with missing behavior evidence\\nremaining INCONCLUSIVE. Publication readiness, exact-head Linux acceptance,\\nlanding readbacks and reconciliation retain their existing owners and authority.\\n\\n## Local selected-instruction activation\\n\\nThe external supervisor may require exact task instructions through schema-3\\nIssue-atom authorization. Its nonempty `instruction_pins` list selects only\\n`{path, sha256}` regular UTF-8 files from the authorized `base_head`. Soodles\\nvalidates the selection before creating the Issue and resolves committed bytes\\nagain when producing admission. Schema-2 execution envelopes carry\\n`execution.instruction_context = {source_head, files}`; each file carries\\n`path`, `sha256`, and `content`, and source_head equals execution.source_head.\\nThe complete context is projected unchanged into the canonical stage prompt and\\nchecked before worker launch. Missing, duplicate, traversing, wrong-version or\\ntampered selected input fails before its dependent effects, with the existing\\nowning continuation. Schema-2 authorization and schema-1 envelopes remain legal\\nwithout claiming selected-instruction activation. No new scheduler, policy flag\\nor provider route is introduced. This L boundary proves exact context supply\\nand refusal; P-class adherence needs a separate fresh-consumer observation. It\\ndoes not infer all P-class changes or promote instructions into landing authority.\\n\"\n      },\n      {\n        \"path\": \"contracts/system-v1/landing.md\",\n        \"sha256\": \"fbfacc853a222bc08817d744b278e9dd8184fe93264c4ea8ca2bf76b19fb34ff\",\n        \"content\": \"## LANDING.SUPERVISED.001\\n\\nOwner: ed3c/soodles#4. `landing.py` and `tests/test_landing.py` own this boundary. The supervisor selects a verifier implementation outside the candidate and pins its SHA-256 in an exact single-Issue claim. Every claim binds repository, Issue, PR, head ref, head, tree, base head and successful runtime run/attempt. A local claim additionally binds `control_root`; a cloud claim omits it. Claim shape carries the Session-selected route without another mutable flag. A digest binds bytes; the supervising session supplies initial trust. It is not a signature or an independent correctness oracle.\\n\\n`landing start` rejects mismatched provider identity before admission. `landing advance` prepares an expected-head merge or exact-Issue closure intent in the checkpoint. `landing dispatch` revalidates the provider snapshot and durably consumes that intent before emitting the request once. Landing itself still performs no provider write. Cloud claims use the GitHub connector transport; local claims may project the repository's narrow `provider-execute` continuation, which can execute only the exact persisted offered request with the supervisor-injected credential and returns fresh provider readback. Existing GitHub rules apply; no bypass or permission mutation is offered. Raw snapshots are trusted only as provider readbacks transported by that supervisor, never as candidate-supplied evidence.\\n\\n### Terminal candidate owner activation \\u2014 ed3c/soodles#122\\n\\nAn exact-head GREEN candidate does not select its own landing authority. The installed supervisor supplies one immutable external publisher descriptor and one Cloud/Local route descriptor. The repository `landing-supervisor` entry verifies the publisher through its existing `landing identity`, derives repository/Issue/PR/head/tree/base/run/worktree only from one fresh provider snapshot, creates a new external claim/checkpoint package, and invokes that selected publisher's existing `landing start` exactly once. It performs no provider mutation and never resolves publisher authority from latest/default branch or Git history.\\n\\nCloud route carries no local execution identity. Local route requires supervisor-supplied `control_root` and exact `execution_envelope` reference; the entry neither discovers nor repairs them. Wrong/stale runtime identity, publisher digest mismatch, route-shape mismatch, candidate self-selection, or existing output refuses before checkpoint creation. The returned owner `next` remains a projection of the existing landing state machine; downstream connector/local-provider transport and reconciliation retain their current owners.\\n\\nFor a Cloud PR whose provider branch cannot be a worktree slug, the entry derives a safe cloud-only `worktree` label from the Issue number and binds the exact provider branch in the existing `publication_branch` claim field. The landing owner checks that field against fresh PR readback. Local publication branches retain their canonical Noodle-derived shape; neither route accepts a candidate-chosen branch in place of provider identity.\\n\\nMerged state must agree with the expected parent pair and candidate tree before closure can be offered. For a cloud claim, completed Issue and provider-main readback permits `landing advance` to write RESOLVED: main must equal the merge commit or a complete provider comparison must prove the merge is its ancestor. No control root, shell Git, binary or Noodle call is legal on this route. For a local claim, completed Issue readback instead permits `landing reconcile`: validate local origin/clean source/exact candidate, fast-forward main, ask Noodle to remove the worktree, then read back main and worktree/branch absence. Interrupted local reconciliation can resume from its persisted intent; dirty or divergent local state refuses before cleanup. Retained other worktrees belong to their own admitted Issues.\\n\\nThere is at most one merge request and one closure request per checkpoint, no automatic retries, and no polling loop. Pending unknown outcomes remain pending for owner-specific readback. No production generation closure, autonomous scheduling, crash-safe remote transaction, or independent default-branch verification is claimed. The supervisor must not delete/recreate a checkpoint to repeat an unknown write.\\n\\nAfter provider closure, a corrected verifier can resume an `awaiting_reconcile` or interrupted `reconciling` checkpoint through `landing resume`. Same-route recovery changes only the verifier digest. The local Issue-atom continuation consumes an externally pinned corrected owner only after its original checkpoint has both confirmed write offers and provider closure; it persists the resume intent before invoking the owner, and an unknown outcome permits checkpoint readback only. An externally selected local-to-cloud correction may additionally remove `control_root` while every common identity remains fixed, only when there is no execution envelope and any persisted cleanup intent is absent or the exact no-op observation. It records the prior route and returns a fresh provider-readback operation; cloud-to-local migration is forbidden. Both writes must already have matching offered/readback evidence. No migration emits a provider write or itself resolves the checkpoint.\\n\\n\"\n      },\n      {\n        \"path\": \"contracts/system-v1/recovery.md\",\n        \"sha256\": \"7e83ad5331e8383717d7809920ed3528fe82f3309b8a9a0f91e188a9785f0917\",\n        \"content\": \"### Interrupted cleanup \\u2014 ed3c/soodles#6\\n\\nA reconciling checkpoint may retain its exact admitted branch after Noodle has removed the worktree directory. Before another cleanup request, require that branch to remain at the admitted head and have no checkout at another path. Noodle's existing missing-directory cleanup owns the remaining deletion. A moved branch or foreign checkout refuses before deletion. A resolved checkpoint cannot authorize deletion of a newly appearing branch.\\n\\nA local control root may itself be a clean, registered detached Git worktree when its exact execution envelope binds the root and the initial HEAD equals the admitted base. During interrupted reconciliation, its HEAD must remain a descendant of that base and an ancestor of provider main. The landing owner fast-forwards that detached HEAD without switching the shared main checkout or inventing another worktree. Foreign, dirty or unregistered detached roots refuse before synchronization or Noodle cleanup.\\n\\nPersist `cleanup_intent` before calling Noodle. It binds observed path presence, branch/main heads, Git executable path/digest, Noodle digest and verifier digest. The same observation cannot issue another cleanup request; changed owner readback or executable capability is required. Existing reconciling checkpoints without this field are read as the prior schema, with all identity checks still required. Path/branch/registration absence and clean main remain prerequisites for RESOLVED.\\n\\nA legacy local-shaped delivery whose candidate path, branch and worktree registration were never created records that three-way absence as `cleanup_intent.mode=no_op` before local Git synchronization. It never creates or asks Noodle to delete a synthetic worktree. Any matching branch or registration refuses this compatibility path; a native cloud claim never enters local reconcile.\\n\\nThe nearest local-cleanup oracle is `cleanup_oracle.cleanup_recovery_probe`, called by canonical acceptance after the original runtime oracle. It physically kills the pinned Noodle process between worktree removal and branch deletion, exercises the real CLI, and checks positive recovery, moved-branch/foreign-checkout refusals, unchanged-attempt refusal, old-checkpoint compatibility, plus verifier migration and no-op cleanup compatibility. Provider closure fields and the Git fetch transport are local fixture data; native cloud resolution is instead discriminated at the landing/provider boundary.\\n\\n### Observed Git lock recovery \\u2014 ed3c/soodles#8\\n\\nThis one atom includes the lock readback producer, retry consumer, checkpoint compatibility and runtime controls. `landing reconcile` asks Git for the absolute target ref-lock path; an existing lock produces `cleanup.ref_lock` before Noodle cleanup. It records `cleanup_blocked` bound to the existing cleanup observation and that path, without deleting the lock or replacing the prior cleanup intent. Repeated blocked readback changes neither deletion state nor checkpoint contents.\\n\\nAn observed disappearance of that same lock for the same cleanup context permits one recovery attempt. Consume `cleanup_blocked` and durably save the new intent before invoking Noodle. Another interruption with unchanged context requires new material evidence. Existing checkpoint records with no blocked-lock observation remain unknown; field absence alone cannot authorize a retry. Existing changed-path/executable capability rules and moved-branch/foreign-checkout controls remain in force. This covers the observed target ref lock; it does not claim every filesystem, packed-ref lock or race is recoverable.\\n\\nThe standalone `cleanup_lock_oracle.py` imports no candidate verdict logic. Its four cases exercise actual Noodle SIGKILL, present/absent locks, legacy unknown state, consumed recovery and changed ownership. Canonical acceptance includes it alongside all prior tests and runtime controls. A candidate copy is still non-authorizing. The supervisor may select and freeze an external copy, evaluate the candidate only as a subject, and independently read Git state to reject false success. Process isolation and external Actions execution are claims only when supported by their exact receipts.\\n\\nThe existing externally selected publishing verifier remains unchanged for this Issue. A changed default-branch tip or merged verifier source does not change that selection. `landing resume` cannot supply its own initial trust. New code and tests can be corrected in the same causal atom without replacing the active judge; a separate authorization is needed to promote a new judge.\\n\\n### Interrupted delivery preparation \\u2014 ed3c/soodles#10\\n\\nThe same landing owner contains the intent producer, CLI dispatch consumer and schema migration. Schema 2 distinguishes `delivery.status=prepared` from `offered`. Preparing produces no provider request and does not append `writes_offered`. A restarted supervisor can consume that original prepared intent through `landing dispatch`; its checkpoint lock serializes concurrent consumers. Fresh repository/head/base/run readback must still agree before consumption. After the durable offered state, another dispatch refuses and only provider readback can advance. Merge/closure readbacks without this checkpoint's matching offered write cannot be adopted.\\n\\nSchema 1 pending states migrate conservatively to offered, preserving identities and existing evidence. A missing delivery field in schema 2 or inconsistent `writes_offered` refuses. Migration grants no authority to change an old verifier digest; the supervising claim still binds the selected implementation. Existing schema 1 cleanup and reconciliation records remain supported.\\n\\n`delivery_oracle.py` is the nearest standalone discriminator, also called by canonical acceptance. It kills real child processes after actual durable saves, observes merge/close preparation recovery, models lost replies with a supervisor-owned provider fixture, checks concurrent first consumption, legacy unknown states and head drift. It imports candidate code only inside the fault-injected child, never into the observing process. The candidate copy is non-authorizing; a supervisor-selected external copy can judge baseline, treatment and planted-negative candidates.\\n\\nThe gap after dispatch persistence but before emission/network execution remains unknown: this atom never guesses non-delivery from a timeout or an unmerged PR. There is no remote exactly-once transaction, automatic retry, separate ledger or bounded-generation completion claim. Checkpoint locking is local and per checkpoint. This Issue's publishing verifier remains the externally frozen pre-candidate implementation; no default-branch tip or newly merged verifier selects itself.\\n\\n### Base advancement before delivery \\u2014 ed3c/soodles#16\\n\\nThe existing delivery owner recognizes a coherent forward base change through `landing advance` or the first `landing dispatch`. Original subject, target and runtime identities remain required. A complete supervisor-transported GitHub `base_comparison` must establish old base as the merge base and new base as the final commit. Inconsistent, divergent or truncated readbacks refuse. Before any offered write, persist `readmission_pending` with the observed base and snapshot fingerprint. The old claim remains present but can no longer dispatch, including when an old base readback reappears. The result names `base.head`, its actual/expected values, the landing owner and one supported next help entry. Identical recovery readback does not rewrite the checkpoint.\\n\\n`landing readmit CHECKPOINT CLAIM READBACK` consumes an explicit fresh supervisor claim under the same checkpoint lock. Repository, Issue, PR, worktree, control root and verifier digest must remain identical. Head, base and runtime run ID must change; the existing exact-head successful CI checks remain mandatory. `base_comparison` proves forward movement from the original base; `candidate_comparison` proves the fresh head contains its new base. If main advanced again after the recorded recovery, `recovery_comparison` must prove forward ancestry from that observed base too. These are complete raw compare responses provided by the supervisor, not candidate declarations. This entry executes neither Git rebase nor provider writes.\\n\\nOne atomic save appends the old claim, prepared delivery and invalidation receipt to `prior_admissions` with classification `SUPERSEDED`, then admits the fresh claim. This classification belongs to the replaced admission, not the Issue. A crash after that save resumes through `advance`; duplicate or concurrent readmission cannot replace it again. Overall resource limits remain external; the command contains no retry or generation loop.\\n\\nSchema 1 admitted records with an explicit empty offered-write list can follow this path; legacy pending records remain conservatively offered. A base change cannot turn an unknown request into a known rejection. Offered writes continue to require owner readback, and identity/reconciliation checks remain intact. No post-offer retarget, remote exactly-once transaction, live parallel Issues experiment or autonomous scheduler is claimed.\\n\\n`base_recovery_oracle.py` is the nearest standalone process observer and is included in canonical acceptance. It observes ordinary CLI output, actual SIGKILL after durable invalidation/admission, concurrent consumers and legacy unknown controls using local provider fixtures. Its candidate copy remains non-authorizing. For this atom the supervisor freezes an external observer before candidate acceptance; the active publishing verifier stays unchanged and is never loaded from default-branch tips.\\n\\n### Supervised correction before an offer \\u2014 ed3c/soodles#19\\n\\n`landing invalidate CHECKPOINT` durably withdraws an admitted or prepared, known-unoffered acceptance under the existing checkpoint lock. It consumes no CI verdict or provider snapshot because it only removes permission to dispatch. Preserve the prior claim and prepared intent; repeated invalidation does not rewrite them. Existing base-drift recovery stays intact. The owner returns `landing readmit --help` as the supported next action. A pending explicit amendment cannot dispatch using old green evidence, including after process interruption.\\n\\nThe supervisor amends the same causal Issue and obtains its fresh execution boundary before source changes. Implementations, tests and erroneous candidate gates may be corrected or deleted together. Replace false assertions with discriminating positive/negative behavior controls; do not preserve wrong behavior for test-count stability or erase an unresolved failure to obtain green. This command does not author Issue bodies, inspect every source write, or change required-check policy.\\n\\n`landing readmit` accepts a changed head and fresh successful exact-head run at the same base after explicit invalidation. Changed bases still require complete forward ancestry; every new candidate must contain its admitted base. Repository, Issue, PR, worktree, control root and external verifier stay identical. Archive the old claim, evidence and intent as SUPERSEDED in the same atomic save. Schema 1 known-empty admissions and existing schema 2 base-drift records remain supported. Offered or legacy-unknown writes require owner readback and cannot enter this path.\\n\\nThe selected external judge is fixed for this acceptance, not a permanent freeze of repository source. Changing its source in this Issue does not promote it into authority. A defect in the active external judge needs an explicit supervisor authority decision and fresh acceptance; the candidate cannot bless its replacement or bypass a required check.\\n\\nThe extended `base_recovery_oracle.py` observes actual child SIGKILL after invalidation/readmission saves, same-base recovery, old/failed/unchanged evidence refusal and unchanged-verifier enforcement. It uses labeled provider fixtures. Green admission, fresh readmission and an emitted merge request all retain null Issue classification. RESOLVED remains route-specific: exact provider completion for cloud, and provider completion plus Git/Noodle reconciliation for local. Actual provider delivery is evidenced separately.\\n\\n\"\n      }\n    ]\n  },\n  \"authorizes_landing\": false\n}\n",
      "stderr": ""
    }
  ],
  "source_status_unchanged": true,
  "authorizes_landing": false
}
```

## Local verification

The single full unittest discovery ran 539 tests in 288.390 seconds with exit 0
and no skips. It started after the first readiness head. The subsequent two-line
carrier type correction and added test received separate verification before
replacement readiness. That verification used 13 focused adapter tests and the
unchanged external actual-Noodle oracle. The original selector focused suite
passed all 11 tests. This is local test evidence, not canonical Linux acceptance.

Full-suite raw log: `/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/full-suite.log`; SHA-256 `58f1e832e79dd852d871b894cf47bb102f9c5e858c46689565c3735b7480d37b`.

```json
{
  "exit_status": 0,
  "elapsed_seconds": 288.7562117576599,
  "log": "/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/full-suite.log"
}
```

Self-review: all source changes stay within the admitted write paths. Diff whitespace notices are confined to the exact frozen contract section endings; these bytes are retained to preserve the required lossless extraction and frozen hashes. No hook or test was bypassed.

## Fresh observed behavior and independent confirmation

Supervisor readiness binds the archived comparison to implementation head `e963c132d688f40dec543474b2cc0bf674d59f72`. Both supplied artifact digests were checked before copying. The selection-v3 completed treatment and independently predefined confirmation-v3 blocked treatment each recorded exactly one correct typed event through one recorded process operation. Each baseline made five recorded help/schema operations but could not obtain the typed event schema and emitted no typed event. These are bounded reporting failures despite appropriately avoiding guessed payloads. The external controls report two positives and ten planted negatives PASS, and source bytes unchanged.

The blocked confirmation preserves the missing externally supplied dependency delivery receipt and the dependency owner; it does not infer completion from successful reporting. The original context-supply confirmation remains separate from this outcome comparison. Exact supplied instruction bytes alone do not establish Agent behavior, and neither comparison relaxes full-contract delivery or the fresh-envelope requirement for body amendments.

Superseded follow-up measurements remain archived. Initial selection baseline
is INCONCLUSIVE because its packet omitted the complete admitted contract.
Selection-v2 treatment is INCONCLUSIVE for exact-code exposure because the
candidate changed during that measurement. Its actual recorded event remains
evidence but receives no final-head credit. The independent v3 pair supports
the final scoped conclusion. The original context-selection baseline truncation
also remains INCONCLUSIVE. No earlier failure or incomplete capture was rewritten as PASS.

The follow-up archive and summary are unchanged copies from the supervisor. Reported operations cover the initial read and declared process interface, not a complete platform transcript. Actual native model/token telemetry and storage isolation remain unknown. Product PASS, observed behavior PASS and pending provider resolution are separate findings.

Artifact bindings:

```json
{
  "head": "e963c132d688f40dec543474b2cc0bf674d59f72",
  "archive": {
    "path": "/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/behavior-final.tar.gz",
    "sha256": "68412c959a9e260740fa53bf223db961de2c3c8d5a011de80dadf5ffe943cb9d"
  },
  "summary": {
    "path": "/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/behavior-final-summary.json",
    "sha256": "ede82c7bcb728222cc3da40b64cbc34de446062fce10144735b8c706c43b2b43"
  },
  "verdict": "PASS"
}
```


## New admitted correction attempt (Issue 199 / existing PR 200)

This is actual order `soodles-199-5236d5ae903f`, session
`soodles-199-5236d5ae903f-0-execute-20260930-165742-db76ce`. Its clean Noodle-owned
worktree began at admitted base `0977f2513130e8a38c53665f71c8e90f3ac9c614`.
It was explicitly fast-forwarded to `c9577fda90ebc910492599d88428f94a5f469869`.
The seven SHA-256-verified files selected by the supervisor's
`followup/fresh-attempt/fixed-files.json` were applied after that fast-forward.
The read-only worker adapter confirmed the current envelope, binary, order,
stage, session and worktree binding. No original-order restoration or event
fabrication occurred.

The supervisor reports that c957's Linux runtime run `36741329249` failed on
deep JSON. Earlier recovery attempts failed, and the original order was archived.
The user explicitly rejected restoring that order as a prerequisite. This fresh
admission preserves Issue 199, PR 200, failed immutable heads and old evidence.
The failed `prewrite_recovery` experiment is excluded.
No archived-order recovery API is introduced.

Scoped eval-audit uses method SHA-256
`c11338900d88d114c353a8865d9b7a4780d972bf740b80d5eb4e38357b1bf133`.
It separates three observed owner faults: unbounded recursion diagnostics,
inconsistent idle-scheduler recognition, and proposal intent persisted before
validation. Existing controls also exposed unnecessary coupling of prior
publication to prior-order continuation. The selected owner correction catches
recursion around parsing, validation, diagnostic rendering and output. It shares
the exact idle-scheduler predicate and validates before recording an offered
proposal. It also admits a fresh order while retaining the prior publication
identity. Unknown effect outcomes still require readback and are never
automatically reoffered. Existing same-order correction and publication, CI and
landing gates remain required.

Deterministic subprocess faults distinguish four recursion boundaries.
The old source fails three controls. Owner controls distinguish idle schedulers
from active or foreign schedulers, and preflight refusal from an unknown write
outcome. They also distinguish same-PR fresh admission from foreign identities
or a prior atom without publication. Binary criteria use executable checks, so
subjective judge calibration is not applicable. Raw logs support these local
product findings. The unchanged system-context observer alone does not measure
scheduler or admission behavior. Small historical consumer pairs and incomplete
platform telemetry support no broad efficiency claim.

Agent behavior for this new correction is **INCONCLUSIVE**. Archived fresh-consumer
and independent-confirmation evidence retains its original subject and verdict.
It is not relabeled as this session or a new-head comparison. The frozen execute
instructions and stage-outcome implementation remain byte-identical. Original
baseline truncation remains INCONCLUSIVE. This worker reports only its bounded
implementation and checks. It makes no new behavior-improvement or combined
defect-closure claim. Provider resolution and Linux exact-head acceptance remain
pending with the selected external owners.

### Preserved external offline receipts

These receipts predate this worker and are not this candidate's acceptance. Paths below are relative to `/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/minimal-review/`.

| Receipt | Scoped result | SHA-256 |
| --- | --- | --- |
| `suite.log` | 543 tests passed before publication/admission decoupling | `625731c6b761d1fbc62d0bb667d7c514b9fab125fb6bc2d3afea3b7264e2342a` |
| `owner-final.log` | Latest changed-owner controls: 109 tests passed | `d16e62199179e85ba9046dc3733b5a1c2d157b799b7ab510029dfa9af9593669` |
| `portable-312.log` | Four deterministic recursion faults pass on Python 3.12 | `1e0f2a88ebd45c86db66686efeeab74610c5610de47412894002b70d4c851002` |
| `portable-314.log` | Four deterministic recursion faults pass on Python 3.14 | `62a7a72bfb69d5f1d8e3e5dfe57ada1174dc0851edd042b4ebedeaba4cb93214` |
| `baseline-portable.log` | Old source fails three of four deterministic controls | `0cd7be650ca232f81705aaf110345c3a03aa788bf7cf72608ad10d519234eaad` |
| `oracle.log` | Unchanged external product observer PASS | `e8b30a5e89256eacfb7aa0086b100c1dd303a4d5ad526866ba5f483e8b57f672` |

### This worker's local verification

Focused controls passed: 129 Issue-owner tests, 12 selector tests and 16 supervisor-authorization tests (157 total). One full unittest discovery then passed on clean implementation commit `9476bf507d10ca99ce7e4b4dcb303181eacad27e`; the summary was:

```text
Ran 544 tests in 293.973s

OK
```

The unchanged external `product_oracle.py` passed on that same implementation
commit. It covered 3,450 selected bytes, exactly common plus instruction-context,
ten frozen contract files, legal shared prerequisites, refusals of unknown or
traversing roots, and unchanged source state. Its fixed scope does not certify
the changed correction or admission owners. The focused and full suites cover
those owners. The following documentation-only evidence commit changes results
and their manifest hash. Executable, test and frozen instruction bytes remain
those tested above.

Python: `/opt/homebrew/Cellar/python@3.12/3.12.4/Frameworks/Python.framework/Versions/3.12/bin/python3.12`; the external evidence directory's `bin/python3` points to that same executable. `TMPDIR` was physically resolved before execution. Environment and exact argv/exit/duration receipts are preserved under:

`/Users/neon/.codex/experiments/system-context-atom-c8qd73l8/followup/fresh-attempt/worker-verification-5236d5ae903f/`

| Current receipt | SHA-256 |
| --- | --- |
| `environment.json` | `efebe289f2a22e079da25edf294e9e2afa0dea4e05b3c510bbc638e8d79763e2` |
| `focused.json` | `d88102056785390f99aff8d7b88ed04341057b24ca92cb2f76bae73c27b94455` |
| `focused-0.log` | `1325200a39fc2caa12917845c371700952effd0c1c77242db8160379afd56a19` |
| `focused-1.log` | `6bb7fe775ffcab92b5ed2b8b668c5ff4cbee5a0791fedb33a6ad2a5123d12d59` |
| `focused-2.log` | `2b6a7fc117be4875abf489da5859418d21dc68e696d863de22aede8f80525fb9` |
| `full-suite.json` | `606aca2d9cd99a3f13597856bb75d270a4169424da3446e62cc31cf3a2dd2732` |
| `full-suite.log` | `7d312a93613e0c2c8c5156af213dfb9cb70f3d05edcbdece5baa19192fc829f1` |
| `oracle.json` | `44adb75f8f9706371f8cf69f873e09cb545c006272cf714852a87a9488f49a78` |
| `oracle.log` | `8923a11ca5354b0c7e0bbb9282e559a0f79ad9422aa7fa104070447876db95ed` |

Self-review found no changes outside the admitted paths. It also found no
modification of the seven selected source and test bytes after their digest check.
All 22 frozen pins match. The manifest preserves both original instruction
identities and covers all 40 required paths: two instructions, 37 artifacts and
the manifest itself. `validate_delivery_paths` is run against the final clean
commit. Its non-authorizing receipt is retained in the same external evidence
directory. Local checks and the completed worker outcome do not authorize
landing. Exact-head Linux Actions acceptance, native publication readiness, and
provider and local reconciliation remain with their existing owners.
