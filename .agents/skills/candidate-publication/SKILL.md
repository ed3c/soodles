---
name: candidate-publication
description: Publish one canonically accepted local Soodles candidate from an exact Noodle claim to one exact GitHub PR.
---

# Candidate publication

Use only after canonical acceptance produced a receipt for the current clean
candidate and the Noodle supervisor produced the matching publication claim.
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
