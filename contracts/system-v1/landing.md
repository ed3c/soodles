## LANDING.SUPERVISED.001

Owner: ed3c/soodles#4. `landing.py` and `tests/test_landing.py` own this boundary.
The supervisor selects a verifier implementation outside the candidate.
It pins the verifier's SHA-256 in an exact single-Issue claim. Every claim binds
repository, Issue, PR, head ref, head, tree, base head, and successful runtime
run/attempt. A local claim also binds `control_root`. A cloud claim omits it.
The claim shape carries the Session-selected route without another mutable flag.
A digest binds bytes. The supervising session supplies initial trust.
The digest is not a signature or an independent correctness oracle.

`landing start` rejects mismatched provider identity before admission.
`landing advance` prepares an expected-head merge intent or exact-Issue closure
intent in the checkpoint. `landing dispatch` revalidates the provider snapshot.
It durably consumes that intent before emitting the request once. Landing
itself performs no provider write.

Cloud claims use the GitHub connector transport. Local claims may project the
repository's narrow `provider-execute` continuation. That continuation can
execute only the exact persisted offered request, using the credential injected
by the supervisor. It returns fresh provider readback. Existing GitHub rules
apply. Neither route offers bypass or permission mutation. Raw snapshots are
trusted only as provider readbacks transported by that supervisor. Candidate-supplied
snapshots are not trusted evidence.

### Terminal candidate owner activation — ed3c/soodles#122

An exact-head GREEN candidate does not select its own landing authority.
The installed supervisor supplies one immutable external publisher descriptor
and one Cloud/Local route descriptor. The repository `landing-supervisor` entry
verifies the publisher through its existing `landing identity`. It derives the
repository, Issue, PR, head, tree, base, run, and worktree only from one fresh
provider snapshot. It creates a new external claim/checkpoint package and calls
the selected publisher's existing `landing start` exactly once.
The entry performs no provider mutation. It never resolves publisher authority
from the latest branch, default branch, or Git history.

The cloud route carries no local execution identity. The local route requires
supervisor-supplied `control_root` and an exact `execution_envelope` reference.
The entry neither discovers nor repairs them. Before checkpoint creation, it
refuses wrong or stale runtime identity, publisher digest mismatch, route-shape
mismatch, candidate self-selection, or existing output.
The returned owner `next` remains a projection of the existing landing state
machine. Downstream connector transport, local-provider transport, and
reconciliation retain their current owners.

If a Cloud PR's provider branch cannot be a worktree slug, the entry derives
a safe cloud-only `worktree` label from the Issue number. It binds the exact
provider branch in the existing `publication_branch` claim field. The landing
owner checks that field against fresh PR readback. Local publication branches
retain their canonical Noodle-derived shape. Neither route accepts a
candidate-chosen branch in place of provider identity.

Before closure can be offered, merged state must match the expected parent
pair and candidate tree. For a cloud claim, completed Issue and provider-main
readback permits `landing advance` to write RESOLVED. Main must equal the merge
commit, or a complete provider comparison must prove that the merge is its
ancestor. This route permits no control root, shell Git, binary, or Noodle call.

For a local claim, completed Issue readback instead permits `landing reconcile`.
Reconciliation validates the local origin, clean source, and exact candidate.
It fast-forwards main and asks Noodle to remove the worktree. It then reads back
main and confirms that the worktree and branch are absent. Interrupted local
reconciliation can resume from its persisted intent. Dirty or divergent local
state causes refusal before cleanup. Other retained worktrees belong to their
own admitted Issues.

Each checkpoint permits at most one merge request and one closure request.
There are no automatic retries or polling loop. Pending unknown outcomes remain
pending until owner-specific readback. This boundary claims no production
generation closure, autonomous scheduling, crash-safe remote transaction,
or independent default-branch verification. The supervisor must not delete
and recreate a checkpoint to repeat an unknown write.

After provider closure, a corrected verifier can resume an `awaiting_reconcile`
or interrupted `reconciling` checkpoint through `landing resume`. Same-route
recovery changes only the verifier digest. The local Issue-atom continuation
consumes an externally pinned corrected owner only after the original checkpoint
has confirmed write offers and provider closure. It persists the resume intent
before calling the owner. If the outcome is unknown, only checkpoint readback
is permitted.

An externally selected local-to-cloud correction may also remove `control_root`
while preserving every common identity.
This is permitted only when no execution envelope is present.
Any persisted cleanup intent must be absent or the exact no-op observation.
The correction records the prior route and returns a fresh provider-readback
operation. Cloud-to-local migration is forbidden. Both writes must already
have matching offered/readback evidence. No migration emits a provider write
or resolves the checkpoint by itself.
