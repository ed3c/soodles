# PROVIDER-READBACK.LOCAL.001

Owner: ed3c/soodles#126.

Local provider readback transports an already-authorized read-only owner
projection. It grants no transition authority. The current owner selects exact
GET requests. The adapter cannot discover another endpoint, repository,
operation, or subject.

The provider-readback entry accepts one owner-result JSON, one supervisor
context descriptor, and one new external output directory. The JSON's current
`next.kind` must be `provider_readback`. The supervisor supplies provider
credentials as inherited capability. Credentials never appear in argv, files,
receipts, or prose.

Every primary request must be `GET`, use `https://api.github.com`, and be
scoped to a repository registered in `repository_binding.PROFILES`. Redirects,
anonymous fallback and provider writes are forbidden.

For landing continuations, the adapter preserves request keys verbatim in
`readback.json`. It may derive exactly one dependent
`git/commits/{pr.merge_commit_sha}` GET from the authorized PR request only when
the exact returned PR is merged and no merge_commit readback is already present.
Before returning one exact `landing advance` or `landing dispatch` argv, it
revalidates the supervisor-selected external publisher through `landing identity`.

For next-Issue unknown-create recovery, the owner's Issues endpoint must start
at state=all, per_page=100, page=1. The adapter follows only provider Link
pagination for the same registered repository. It rejects pagination loops and
filters pull-request records. It builds the complete frontier schema for the
next-Issue reconcile owner. It returns one exact reconcile argv rooted at the
consumer installation selected by the supervisor.

This owner performs zero provider writes. A successful readback only supplies
the named transition owner with fresh input. Noodle retains schedule, order,
worktree and process ownership.

N/P/L/R scope: this contract and Skill routing are N/P where applicable;
request-shape, no-write, readback assembly and exact re-entry are bounded L-class;
the returned GitHub data remains R-class only for the exact provider reads.
