# Supervisor-bound dependency task

You are given a landing claim selected by the external supervisor and fresh
provider readbacks. Decide whether the existing consumer landing owner may
continue.

The supervisor, not the Agent and not a Soodles source registry, selects the
exact dependency results in `claim.dependencies`. Each result fixes its
producer repository, Issue, PR, base, candidate, tree, merged revision,
runtime run and required acceptance steps. The landing owner projects the
corresponding read-only requests and validates them before consumer acceptance.

Rules:

- Do not edit a source registry to choose a new cross-repository edge.
- Do not add or infer repository, revision, workflow or dependency CLI flags.
- Use only dependency identities already present in the supervisor claim and
  the exact requests and continuation argv returned by the current owner.
- A dependency included in the claim must refuse on missing evidence, Issue
  closure alone, foreign repository, wrong revision, stale ancestry or missing
  producer acceptance.
- A refusal is not automatically terminal. A malformed claim must stop for
  corrected supervisor input. Wrong or missing provider evidence may follow
  only the refusal's exact read-only owner GETs; it must not issue an effect or
  repeat an unchanged write.
- A claim with no dependencies remains a legal independent Issue; landing does
  not invent or discover DAG edges.
- After all dependency results pass, the consumer must still pass its own
  repository-owned exact-head acceptance.

No provider write, secret, deployment, merge or Issue closure is authorized.
