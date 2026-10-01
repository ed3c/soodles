---
name: candidate-publication
description: Publish one verified local Soodles candidate from its exact Noodle claim and publication-readiness receipt to one exact GitHub PR.
---

# Candidate publication

Use only after native publication readiness (or canonical acceptance) produced
a receipt for the current clean candidate and the Noodle supervisor produced
the matching publication claim. Native readiness binds actual platform,
executable, capability checks and head/tree; it is not Linux canonical acceptance.
Schema-2 readiness leaves behavior regressions to the
[Test Manager](../test-manager/SKILL.md) decision consumed by exact-head Actions;
publication adds neither the legacy fixed tests nor a full-suite requirement. On the
local macOS route, publish first, then observe the existing Linux exact-head
Actions acceptance before landing. Do not install a local Linux runner.
Do not rediscover or rewrite repository, subject, worktree, branch, base, HEAD,
tree, remote, PR title, PR body, or provider identity.

Run the owner entry once with the two supervisor-supplied files:

```bash
./candidate-publish /absolute/acceptance.json /absolute/noodle-claim.json
```

Consume its JSON result. `status=created` and `status=reused` both name the one
exact provider branch, head, tree and PR. Neither authorizes landing.

On refusal, follow only `next.owner` and `next.required`. A failed or lost push
or PR-create response is not permission to repeat the command: this owner has
already performed the allowed fresh readback and will report the missing exact
provider state. Never run `git push`, `gh pr create`, a connector PR mutation,
or the legacy Noodles handoff as a substitute.

## Push receipts and continuation

The lifecycle checkpoint retains a push record before process start and replaces
that attempt with its completed, timed-out, interrupted or not-started result. It binds exact
argv, worktree, single ref/lease, elapsed time, exit status and credential-redacted
stdout/stderr. Installation credentials are used over the validated repository's
HTTPS endpoint even when the selected origin uses SSH; global remote configuration
is unchanged. Credential helpers and askpass fallback are disabled for this
invocation. Workflow-writing admissions request the workflows write capability
from the existing registered supplier. Missing capability is its owner's input,
never permission to fall back to another credential.

Exact provider branch/PR readback still decides success, including a lost process
response whose effect is later visible. Exit zero alone proves no publication.
Only completed nonzero Git porcelain output containing exactly one matching ref
with `[rejected]` or `[remote rejected]` establishes a known rejected offer.
Do not classify retryability from free-form stderr. After correcting that named
provider capability, the supervisor may re-enter the same atom command once.
The owner rechecks all publication inputs and preserves the original lease and
PR. At most two push processes exist for the same offer; it never retries inside
the foreground wait loop. Re-entry after material correction is the supervisor's
P-class obligation; the executable bound is the receipt, exact identity and limit.

A timeout, incomplete status, missing legacy receipt or crash remains unknown;
re-entry can adopt fresh exact effect readback but cannot reoffer. Do not create a
new authorization to reset the offer. The existing #205 attempt has no saved
process result and is not retroactively classified as rejected. Standalone
candidate-publish retains a locked external journal beside its readiness receipt
and continues by readback only. These receipts grant no landing authority.
