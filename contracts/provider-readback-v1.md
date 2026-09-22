# PROVIDER-READBACK.LOCAL.001

Owner: ed3c/soodles#126.

Local provider readback is transport of an already-authorized read-only owner
projection, not transition authority. A current owner selects exact GET requests;
the adapter may not discover another endpoint, repository, operation or subject.

The provider-readback entry accepts one owner-result JSON whose current
`next.kind` is `provider_readback`, one supervisor context descriptor and one
new external output directory. Provider credentials are inherited supervisor
capability and never appear in argv, files, receipts or prose.

Every primary request must be `GET`, use `https://api.github.com`, and be
scoped to a repository registered in `repository_binding.PROFILES`. Redirects,
anonymous fallback and provider writes are forbidden.

For landing continuations, request keys are preserved verbatim in
`readback.json`. If the exact returned PR is merged and no merge_commit
readback is already present, the adapter may derive exactly one dependent
`git/commits/{pr.merge_commit_sha}` GET from the already-authorized PR request.
The supervisor-selected external publisher is revalidated through
`landing identity` before one exact `landing advance` or `landing dispatch`
argv is returned.

For next-Issue unknown-create recovery, the owner-emitted Issues endpoint must
start at state=all, per_page=100, page=1. The adapter follows only provider Link
pagination for the same registered repository, rejects pagination loops, filters
pull-request records, and materializes the complete frontier schema consumed by
the next-Issue reconcile owner. It returns one exact reconcile argv rooted at the
supervisor-selected consumer installation.

This owner performs zero provider writes. A successful readback only supplies
the named transition owner with fresh input. Noodle retains schedule, order,
worktree and process ownership.

N/P/L/R scope: this contract and Skill routing are N/P where applicable;
request-shape, no-write, readback assembly and exact re-entry are bounded L-class;
the returned GitHub data remains R-class only for the exact provider reads.
