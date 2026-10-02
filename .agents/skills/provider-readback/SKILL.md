---
name: provider-readback
description: Materialize one current Soodles owner's local GitHub readback into its exact re-entry continuation.
---

# Provider Readback

Use this Skill only when the current local Soodles owner returns
`next.kind=provider_readback` with `next.owner=GitHub`.

The supervisor supplies these inputs:

- the current owner-result JSON;
- one context descriptor naming the already-selected landing publisher or
  next-Issue consumer root; and
- one fresh absolute external output directory.

Run exactly:

```sh
./provider-readback consume CURRENT.json CONTEXT.json /absolute/external/output
```

Then consume the returned current next exactly.

The executable adapter owns these read-only operations:

- It executes only owner-emitted `GET` requests to supported GitHub repository API URLs.
- It preserves every owner request key in landing `readback.json`.
- If the returned PR is merged, it obtains the dependent merge-commit GET from the confirmed `merge_commit_sha`.
- For next-Issue recovery, it follows provider `Link rel="next"` pagination.
  It excludes pull-request records from the Issues endpoint. It writes the complete `frontier.json`.
- It checks the selected external landing publisher before it constructs the landing re-entry argv.
- It returns one exact executable re-entry argv.

Do not use curl, gh, a browser, handwritten REST URLs or manual pagination.
Do not hand-build snapshot or frontier JSON. Do not derive another repository, provider
host, operation, checkpoint, intent or publisher from history.

A missing credential or rejected provider read blocks the operation.
Neither condition permits anonymous access or an identity change.
The adapter refuses redirects. This Skill never performs provider writes.

This Skill is P-class guidance only. The adapter provides bounded L-class
evidence for readback and file creation. GitHub responses remain R-class truth for
their exact provider subjects. Neither grants merge or Issue-creation authority.
