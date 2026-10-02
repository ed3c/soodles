# Original cleanup continuation — Issue #213

The observed incident is
`/Users/neon/.codex/soodles-owner-recovery-wtmpxwte/ci-current-base/result.json`.
It records #204 closed, PR #205 merged, candidate
`7b8aa9e52137e0e2b6de4523f13ea3c23face24f`, merge/main
`3c40138ec205db9c254bce8a4adb73bd8c32ab29`, and original order
`soodles-204-c4b0157d5b77` completed. At that observation, its worktree remained. The original lifecycle phase was landing,
with a refusal at `cleanup.observation`. The incident's successful
run 36837614425 (29 tests, five modules) is historical #204 evidence, not #213
acceptance. No live recovery, cleanup or provider write was performed for this
implementation.

The original landing checkpoint retains merge/close offers and a cleanup intent
whose `main_head` is the detached control HEAD. The selected Noodle source at
`/Users/neon/.codex/experiments/soodles133-bootstrap.QpepPK/noodle-source/`
shows `worktree/app.go` calling `discoverBaseBranch` when IntegrationBranch is
empty, `worktree/diff.go` reading origin/HEAD's branch name with fallback main,
and `worktree/commands_cleanup.go` checking that integration branch. Its
`cmd_worktree.go` does not set IntegrationBranch. Consequently advancing the
actual local main ref did not change the old Soodles observation.

The correction observes `refs/heads/<discovered branch>`.
It rejects a branch outside the repository profile or a missing local ref.
It retains the detached control HEAD separately. Repeated identical cleanup inputs refuse. Control HEAD movement alone
does not permit an offer. Actual local integration movement can permit the same
continuation. Existing ancestry, clean tree, exact candidate, lock release, unknown
cleanup and no-op behavior remain. Soodles neither modifies Noodle nor forces
cleanup nor advances shared main on behalf of its owner.

Normal and activated landing checkpoints can consume a separately accepted,
externally selected publisher after confirmed merge and closure, retaining all
provider and cleanup history. The existing landing resume changes only verifier
identity. An interrupted offer requires checkpoint readback, never replay.

The #204 lifecycle-v2 bundle is immutable and has no lifecycle_resume record.
The selected replacement runtime therefore owns a bounded `issue-atom resume`
entry. Before recording from/to/auth binding, the entry validates the original
authorization bytes/digest and claim/envelope/order. It also checks confirmed
landing, stopped sessions and free locks. Its original command continues under the selected runtime. No unresolved
amendment is required. An advanced control root retains ancestry validation; the
exact idle schedule shape is accepted without changing canonical prompt/history.
The same selection permits readback. A different second selection refuses.

The actual #204 host-finalization record has sequence 6 and retained stop/absence
facts. Its plan identity includes issue_atom.py, so simply changing the runtime
would otherwise refuse at host finalization. Resume validates the old pinned plan and subject. It requires unchanged rules/context
and retains the whole prior record. It carries facts/sequence to the selected plan identity. This is a source identity
migration within the original owner, not a new cleanup or repair allowance.

Focused controls cover detached vs local integration, unchanged input, missing or
unsupported refs, actual reconciliation, normal/activated resume, preservation of
history, unknown resume readback, missing merge/closure, canonical identity drift,
live processes, locks and runtime/host projection binding. The existing Test Manager
maps these changes to normal exact-head CI, including its existing affected landing
physical controls. These are authored controls, not local passing results. Local
validation is Python syntax and diff review only; no tests, full suite, benchmarks
or model experiments were executed. This design and its hash manifest are
non-authorizing evidence and make no Agent behavior improvement claim.

The local plan-only readback on the admitted base returned `ready`, `focused`,
no unresolved paths and `authorizes_landing: false`. Its unit modules are
`test_admission`, `test_base_readmission`, `test_candidate_verification`,
`test_cleanup_continuation`, `test_comparison_gate`, `test_cross_repository_delivery`,
`test_cross_repository_dependency`, `test_delivery_refs`, `test_instruction_context`,
`test_issue_atom`, `test_landing`, `test_landing_bootstrap`, `test_landing_continuation`,
`test_landing_supervisor`, `test_lifecycle_activation`, `test_local_continuation`,
`test_local_provider_transport`, `test_publisher_receipts`, and `test_test_suite`.
Its physical controls are `cleanup_recovery`, `cleanup_lock_recovery`,
`delivery_recovery`, and `base_recovery`; all execution remains pending normal CI.
