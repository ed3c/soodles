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
5. Stop on an unsupported repository, repository mismatch, wrong head, draft
   PR, missing registered job/step or unknown write outcome. Report the exact
   invalid field and use the returned help/readback route.

The Ops profile requires both repository-owned `runtime` and `postgres`
jobs and their named runtime, owner, browser, mapping and PostgreSQL steps.
Their success proves that exact candidate's repository acceptance. It does not
prove a live model call, business accuracy, dependency satisfaction or landing
authority.

## Evidence boundary

The cross-repository observer uses provider fixtures and the exact Ops
candidate/run identity from PR 22. It emits no provider write. A draft PR is a
legal refusal. Merge and closure still require a separately authorized,
non-draft target Issue atom and fresh provider readback through the existing
landing owner.
