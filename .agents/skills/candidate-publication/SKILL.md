---
name: candidate-publication
description: Publish one verified local Soodles candidate from its exact Noodle claim and publication-readiness receipt to one exact GitHub PR.
---

# Candidate publication

An active Issue atom calls this owner through its existing continuation.
Do not invoke standalone publication in parallel or after that same atom call.
The entry below is for a separately admitted standalone publication.

Before using this entry, obtain two matching records. Native publication
readiness (or canonical acceptance) must provide a receipt for the current clean
candidate. The Noodle supervisor must provide its publication claim.
Native readiness binds the actual platform, executable, capability checks, head
and tree. It does not establish Linux canonical acceptance.
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

On refusal, follow only `next.owner` and `next.required`. If a push or PR-create
response fails or is lost, do not repeat the command. The owner has already
performed the allowed fresh readback. It reports the exact provider state that
is missing. Never run `git push`, `gh pr create`, a connector PR mutation,
or the legacy Noodles handoff as a substitute.

## Push receipts and continuation

Before the push process starts, the lifecycle checkpoint saves its record.
The checkpoint then replaces that attempt with its completed, timed-out,
interrupted or not-started result. The record binds the exact argv, worktree,
single ref and lease, elapsed time, exit status, and credential-redacted output
from stdout and stderr. The process uses installation credentials over the
validated repository's HTTPS endpoint, even when the selected origin uses SSH.
It leaves global remote configuration unchanged. This invocation disables
credential helpers and askpass fallback. Workflow-writing admissions request
the workflows write capability from the existing registered supplier.
If that capability is missing, obtain it from its owner. Do not use another credential.

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

A timeout, incomplete status, missing legacy receipt or crash leaves the outcome
unknown. Re-entry can adopt fresh exact effect readback but cannot reoffer. Do not create a
new authorization to reset the offer. The existing #205 attempt has no saved
process result and is not retroactively classified as rejected. Standalone
candidate-publish retains a locked external journal beside its readiness receipt
and continues by readback only. These receipts grant no landing authority.
