# Cross-repository delivery

Use this recipe only when the installed supervisor supplies an envelope or
landing claim for a repository present in `repository_binding.PROFILES`.
Repository registration and acceptance requirements are source-owned controls;
there is no Agent flag for adding or changing them.

## Current shortest path

1. Read the externally pinned envelope or claim. Its repository is the subject.
2. For an authenticated Issue read, execute the owner form exactly:
   `./soodles github issue OWNER/REPOSITORY NUMBER`.
3. For admission and worker execution, use the existing `issue automatic`,
   `issue supervised` and Noodle-dispatched `issue worker` entries. They
   derive provider URLs, order title and Git origin from that same envelope.
4. For delivery, obtain every GET named by `landing.next.requests`, save one
   readback, then execute the current `landing.next.argv` unchanged.
   A supervisor-bound dependency appears in that same request map with
   indexed `dependency_N_*` keys; it is not a separate command or
   Agent-selected gate.
5. Stop on an unsupported repository, repository mismatch, wrong head, draft
   PR, missing registered job/step or unknown write outcome. Report the exact
   invalid field and use the returned help/readback route.

The Ops profile requires both repository-owned `runtime` and `postgres`
jobs and their named runtime, owner, browser, mapping and PostgreSQL steps.
Their success proves that exact candidate's repository acceptance. It does not
prove a live model call, business accuracy or landing authority.

The installed supervisor binds each admitted DAG edge in the immutable landing
claim, including the exact producer Issue, PR, base, candidate, tree, merged
revision, runtime and required steps. Soodles does not keep a source edge
registry. Issue closure alone, resource cleanup, an order or a different
successful revision is insufficient. Once every selected result is eligible,
the same invocation validates the consumer candidate and continues through its
existing owner. A claim without dependencies remains independent; landing does
not discover or invent an edge. Copy all returned GETs and the current
continuation argv; there is no dependency flag or correction guess.

## Evidence boundary

The cross-repository observer uses provider fixtures and the exact Ops
candidate/run identity from PR 22. It emits no provider write. A draft PR is a
legal refusal. Merge and closure still require a separately authorized,
non-draft target Issue atom and fresh provider readback through the existing
landing owner.
