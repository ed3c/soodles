---
name: schedule
description: Materialize the one externally admitted Soodles Issue through the shared validator.
schedule: When Noodle requests a Soodles schedule decision.
---

# Schedule the admitted Issue

From the current checkout, run `./soodles issue inspect`. This read-only entry
reads the current Noodle role before checking the supervisor-selected launcher.
Consume its result:

- `action: not_applicable`: return to the caller's original task; no schedule
  prerequisite or completion is implied by `next: null`.
- `next.kind: input` / refusal: report the named owner and required input for
  this operation. Continue unrelated authorized work; do not retry unchanged
  input or use help as a capability probe.
- `next.kind: executable`: execute the current `next.argv` array exactly once,
  without shell reconstruction, then consume the launcher's structured result.

Inspection does not admit an Issue, execute the launcher, or grant authority.
The selected launcher revalidates its external envelope and current Noodle and
provider state before effects. Never search for, synthesize, export, or reuse a
historical launcher; do not dump the environment.

Noodle owns the canonical order, worktree and process. An owned or previously
admitted result is an observation, not permission to establish another writer.
Never reconstruct an order, overwrite `orders-next.json`, request an implicit
restart, or write canonical state. Do not edit target source or perform delivery
from the schedule task. This Skill is guidance; the installed validator/worker
boundary performs enforcement.
