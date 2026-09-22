---
name: provider-readback
description: Materialize one current Soodles owner's local GitHub readback into its exact re-entry continuation.
---

# Provider Readback

Use this Skill only when the current local Soodles owner returns
`next.kind=provider_readback` with `next.owner=GitHub`.

The supervisor supplies:
- the current owner-result JSON;
- one context descriptor naming the already-selected landing publisher or
  next-Issue consumer root; and
- one fresh absolute external output directory.

Run exactly:

```sh
./provider-readback consume CURRENT.json CONTEXT.json /absolute/external/output
```

Then consume the returned current next exactly.

The executable adapter owns the read-only mechanics:
- executes only owner-emitted `GET` requests to supported GitHub repository API
  URLs;
- preserves every owner request key in landing `readback.json`;
- when the returned PR is merged, obtains the one dependent merge-commit GET
  from its confirmed `merge_commit_sha`;
- for next-Issue recovery, follows provider `Link rel="next"` pagination,
  filters pull-request records from the Issues endpoint, and writes the complete
  `frontier.json`;
- verifies the selected external landing publisher before composing a landing
  re-entry argv; and
- returns one exact executable re-entry argv.

Do not use curl, gh, browser, handwritten REST URLs, manual pagination or
hand-built snapshot/frontier JSON. Do not derive another repository, provider
host, operation, checkpoint, intent or publisher from history.

A missing credential or rejected provider read is a blocked input, not permission
for anonymous fallback or identity change. Redirects are refused. This Skill
never performs provider writes.

This Skill is P-class guidance only. The adapter provides bounded L-class
readback/materialization evidence; GitHub responses remain R-class truth for
their exact provider subjects. Neither grants merge or Issue-creation authority.
