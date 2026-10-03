### Complete admitted child contract — ed3c/soodles#135

Soodles Issue admission validates the structured Issue contract and full body digest.
`issue_execution.projection` supplies the complete `binding['contract']` and
`binding['issue_body']` with the existing exact identity and bounded task.
Both automatic and supervised stage prompts receive them. The body preserves
task information outside the structured contract, including the six Issue sections.
It does not grant authority or establish a separate routing schema.
The implementation child consumes these inputs
without a mandatory duplicate GitHub read. If the contract is missing, the
existing admission owner handles the missing input. An amended body requires
the supervisor's fresh envelope.

The installed entry still enforces provider freshness and exact worker and
owner prompt comparisons. If the contract or body is omitted or altered, the entry
refuses before worker execution. The live observer also rejects that changed prompt.
Existing orders retain their selected immutable runtime. Do not treat a missing
body under the new runtime as a legacy prompt or silently reconstruct it.
`tests/test_issue_execution.py` uses local
provider and owner fixtures to check full delivery, prompt tampering, stale
provider refusal, and legal unchanged execution. Those controls do not prove
child behavior. The externally prepared bounded comparison supports only its
observed scope. Missing behavior evidence remains INCONCLUSIVE.
Publication readiness, exact-head Linux acceptance, landing readbacks, and
reconciliation retain their existing owners and authority.

## Local selected-instruction activation

The external supervisor may require exact task instructions through schema-3
Issue-atom authorization. Its nonempty `instruction_pins` list selects only
`{path, sha256}` regular UTF-8 files from the authorized `base_head`.
Before creating the Issue, Soodles validates the selection. When producing
admission, it resolves the committed bytes again.
Schema-2 execution envelopes carry
`execution.instruction_context = {source_head, files}`. Each file carries
`path`, `sha256`, and `content`. The source_head equals execution.source_head.
The complete context enters the canonical stage prompt unchanged. The owner
checks it before worker launch.

Missing, duplicate, traversing, wrong-version, or tampered selected input fails
before its dependent effects. The failure retains the existing owning continuation.
Schema-2 authorization and schema-1 envelopes remain legal. They do not claim
selected-instruction activation. This adds no scheduler, policy flag, or provider
route. This L boundary proves exact context supply and refusal. P-class adherence
needs a separate fresh-consumer observation. The boundary does not infer all
P-class changes or give instructions landing authority.
