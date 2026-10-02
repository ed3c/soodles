---
name: next-issue
description: Consume one resolved Soodles atom into at most one exact next-Issue provider identity.
---

# Next Issue

Use this Skill only after the current landing owner has returned an exact
`classification=RESOLVED`, `phase=resolved`, `next=null` receipt.

The supervisor supplies these inputs:

- that resolved receipt;
- one finite semantic candidate packet;
- one complete fresh provider Issue frontier;
- the selected Cloud/Local create route; and
- one new external output directory.

Run exactly:

```sh
./next-issue prepare RESOLVED.json CANDIDATES.json FRONTIER.json ROUTE.json /absolute/external/output
```

Then consume the current next exactly.

- `action=stop`: no mechanically eligible candidate exists. Create nothing.
- `next.kind=input`: obtain the named input from its owner. The authorized
  supervisor supplies inputs that it can derive. An owner label does not require a
  human handoff. When multiple candidates are eligible, only the supervisor may
  supply `selected_candidate`.
- `next.kind=provider_write`: Cloud transport consumes the exact persisted create
  request once through the existing provider connector. Preserve the result and
  obtain the requested fresh Issue readback.
- `next.kind=executable`: execute that argv exactly once. Local provider identity
  comes from the supervisor environment, not from task text.
- `next.kind=provider_readback`: obtain only the emitted fresh provider readback
  and run the supported reconcile entry with that material. An unknown create
  outcome is never permission for another create mutation.

Do not discover a broader backlog or invent another candidate.
Do not infer product priority. Do not reconstruct the repository, title or body from prose.
Do not select transport from tool availability. Do not reuse historical create output.
The supervisor packet defines each candidate.
Provider truth and the executable gate determine eligibility.

Terminal success is one exact GitHub Issue identity matching the persisted
causal fingerprint. End this skill's effects and return that identity to the
supervisor. For an already-authorized larger task, the supervisor continues
through the existing Noodle owner for completeness, scheduling and admission.
This skill's terminal result does not complete the larger user request or grant new effects.

This Skill is P-class guidance only. The executable discriminator and GitHub
readback support their respective L and R claims.
Neither this text nor a local receipt authorizes landing.
