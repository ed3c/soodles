# NEXT-ISSUE.AUTHORITY.001

Owner: ed3c/soodles#124.

After a landing lifecycle completes, it may propose another causal atom only
from an externally supplied finite candidate set. The supervisor owns semantic
proposal. The repository may qualify candidates against a complete, fresh
provider frontier. If more than one candidate remains legal, the repository
MUST NOT choose product priority.

The `next-issue prepare` entry accepts exactly five inputs: a terminal RESOLVED
landing receipt, finite semantic candidate packet, complete provider Issue
frontier, route descriptor, and new external output directory. Repository,
Issue title/body, causal fingerprint and create subject are not independent CLI
arguments.

For each candidate, the gate validates the schema-1 semantic Issue contract,
the registered repository, and the exact dependency closures. It also checks
causal-fingerprint duplicates and overlapping open write boundaries.
The gate reports exact reasons for each invalid or blocked candidate.
If no candidate is eligible, it stops without an intent. If multiple candidates
are eligible, the supervisor must select one explicitly. The gate may persist
one create intent for the sole eligible candidate or the supervisor's selected
eligible candidate.

The causal fingerprint binds the repository, normalized trigger, semantic
owner, sorted write paths, and exact dependencies. The owner writes it into the
Issue body as a stable marker. Before admitting a create intent, the owner checks
that marker against the complete provider frontier. Title similarity does not
establish duplicate identity.

The cloud route exposes the exact persisted provider-write request to the
existing connector. The local route exposes one executable continuation.
That continuation consumes only the persisted intent and the credential injected
by the supervisor. Neither route adds a generic provider mutation interface.

If the provider create response is unknown, the owner cannot retry automatically.
It can continue only with fresh provider Issue readback. Reconciliation adopts
exactly one Issue with a matching causal fingerprint and exact body. If no Issue
matches, readback remains required. If multiple Issues match, reconciliation
refuses the ambiguous result.

This owner reaches terminal success with one exact open GitHub Issue identity.
It creates no Noodle order, worktree, session, PR, merge, or closure. The existing
Noodle backlog, completeness, and schedule owners start only after this provider
boundary.

N/P/L/R scope: candidate prose and this contract are N/P where applicable;
local qualification/refusal and intent integrity are L-class; actual GitHub
Issue creation/readback is R-class only for that provider identity.
