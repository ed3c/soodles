# Local provider shortest path result

Classification: **VERIFIED** for the bounded local provider continuation on
implementation head `a912aee37195d9567bfeba804dbfc2b1ebebe0d1`. This evidence is
non-authorizing; the terminal evidence-bound head must still earn its own
exact-head gates.

## Preserved attempts

- `e8ff36ee93cadb490b19c32b7754f74956758fd5`: candidate verification refused
  the then-schema-1 Issue contract.
- `0417e150f7c8711f9ec4efe908d8b5e795e408b9`: the runtime fetched the Issue two
  seconds before the schema-3 update completed and preserved the same refusal.
- `87e0aceb77fb661aefdc3cce91701ff713697a21`: candidate evidence and runtime
  identity passed; canonical acceptance exposed the old landing projection
  assertion that still required local `advance` after dispatch. The new #120
  controls themselves were green. That obsolete assertion was corrected on a
  new head; the failed head was not rerun.

## Verified implementation head

- head: `a912aee37195d9567bfeba804dbfc2b1ebebe0d1`
- tree: `6f8f2ccff8a1e6b9a7d17b472358bc1cd74f5974`
- runtime run: `35571930103` — success
- runtime job: `106245178519` — success
- quality run: `35571930081` — success
- runtime artifact: `10626595940`
- artifact digest:
  `sha256:8a19ac0d8b0bc066d30d288699b2d25bb6f04f734d412d144fe04d617fc31e89`
- canonical acceptance: 218 tests in 14.298s, `OK`
- acceptance: `zero_residue=true`, `authorizes_landing=false`

The focused controls passed:

- `test_local_merge_close_are_exact_executable_continuations`
- `test_cloud_route_keeps_connector_request_and_no_local_executable`
- `test_missing_token_request_drift_and_cloud_checkpoint_refuse_before_mutation`
- `test_unknown_merge_outcome_reads_back_without_second_mutation`
- `test_envelope_bound_reconcile_projects_measured_noodle_binary`
- updated existing owner projection control
  `test_owner_projection_names_missing_input_without_executable_placeholder`

## Bounded behavior

For a local claim the landing owner now persists the exact offered merge/close
request and projects one narrow `provider-execute CHECKPOINT` argv. The local
transport accepts no repository, PR, Issue, expected-head or merge-method flags.
It consumes only that persisted request, uses the supervisor-injected provider
credential, performs at most one mutation, obtains fresh provider readback and
returns exact `landing advance` argv.

An unknown mutation response never triggers an automatic mutation retry. Fresh
provider readback determines whether the effect happened; an unobserved outcome
remains readback-only.

After provider closure, an envelope-bound local claim derives the measured
Noodle binary and projects exact `landing reconcile` argv. A claim without an
execution envelope remains the legal binary-input non-case.

The P-class consumer path is correspondingly smaller: execute current
`next.argv` exactly once. It does not instruct the Agent to choose `gh`/REST
mutation syntax, provider subject identity, credential source, merge method or
Noodle binary.

## Scope

Cloud connector transport is unchanged. No Noodle scheduler/order/worktree
state-machine change was introduced. No generic provider mutation CLI or retry
framework was added. **New-Issue creation and next-task authority are not proven
by this atom and remain a later boundary.**

All candidate and experiment receipts remain `authorizes_landing=false`.
Provider merge/closure of #120 itself remains with the existing external landing
owner.
