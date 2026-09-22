---
name: next-issue
description: Consume one resolved Soodles atom into at most one exact next-Issue provider identity.
---

# Next Issue

Use this Skill only after the current landing owner has returned an exact
`classification=RESOLVED`, `phase=resolved`, `next=null` receipt.

The supervisor supplies:
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
- `next.kind=input`: return the named input to its owner. When multiple candidates
  are eligible, only the supervisor may supply `selected_candidate`.
- `next.kind=provider_write`: Cloud transport consumes the exact persisted create
  request once through the existing provider connector. Preserve the result and
  obtain the requested fresh Issue readback.
- `next.kind=executable`: execute that argv exactly once. Local provider identity
  comes from the supervisor environment, not from task text.
- `next.kind=provider_readback`: obtain only the emitted fresh provider readback
  and run the supported reconcile entry with that material. An unknown create
  outcome is never permission for another create mutation.

Do not discover a broader backlog, invent another candidate, infer product
priority, reconstruct repository/title/body from prose, choose transport from
tool availability, or reuse historical create output. Candidate semantics come
from the supervisor packet; eligibility comes from provider truth and the
executable gate.

Terminal success is one exact GitHub Issue identity matching the persisted
causal fingerprint. Stop there. Noodle completeness/scheduling/admission is a
separate downstream owner and is not part of this Skill.

This Skill is P-class guidance only. The executable discriminator and GitHub
readback own their narrower L/R claims; neither this text nor a local receipt
authorizes landing.
