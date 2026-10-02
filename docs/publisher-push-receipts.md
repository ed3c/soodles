# Publisher push process receipts

Observed production failure: #204 / PR #205 selected candidate
7147b289de6708601305c784c37839b521f96baf after successful descendant-base
continuation. The owner recorded candidate_amendment before invoking Git, then
provider readback still returned 806a3360a8182ebbb49c4ae695758191b278d889.
No new-head Actions run existed. authenticated_push captured process output but
publish_amendment discarded it. The exact failure cause is therefore unknown.

The selected remote was SSH while the wrapper supplied an HTTPS-only header.
That is a transport mismatch, not proof of the historical failure cause. Use the
same validated repository over HTTPS without changing the stored remote. Request
workflow capability only for an admission whose declared write paths include
workflow files. Do not inspect, copy or persist credentials.

The existing atom checkpoint now retains process receipts for the start and result.
It returns these receipts with its same-command refusal.
A later exact provider readback resolves process uncertainty.
After the supervisor corrects the named capability, one further owner invocation
is permitted only for a complete rejection of a single matching ref.
An unknown result never permits that invocation.
Two rejected attempts stop without resetting history.
Standalone publication journals its original effects beside external readiness.

Git's documented porcelain ref status distinguishes rejected / remote rejected
from remote failure: https://git-scm.com/docs/git-push#_output . Only the former
complete exact-ref statuses discriminate this bounded continuation. No free-text
stderr heuristic establishes permission or success.

No local tests, benchmark or model experiment were executed. Authored controls
cover redaction, pre-spawn persistence, timeout/spawn failure, exact-ref rejection,
old unknown offers, bounded continuation and same-PR adoption. Test Manager owns
normal changed-head CI scope. This N-class note does not claim behavioral gains
or that the unrecorded #205 process has been recovered.

Static patch review also corrected interruption handling.
The process saves an unknown terminal receipt before propagating KeyboardInterrupt/SystemExit.
The correction disables Git core.askPass and credential helpers to prevent credential fallback.
Hard termination still leaves the durable started receipt and remains unknown.
Added controls are authored for PR CI; they were not run on this host.
