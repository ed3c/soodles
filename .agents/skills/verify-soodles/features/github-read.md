# Authenticated GitHub Issue readback

The Session uses `./soodles github issue OWNER/REPOSITORY NUMBER` for one Issue.
Use the externally selected repository and Issue number. Do not infer identity
from the current checkout.
The same reader supplies automatic, supervised and worker admission. Consume
`issue` and the response `observation`. This read does not select an envelope,
change Noodle state, authorize delivery or resume a paused comparison.

The supervisor supplies one repository-scoped GitHub App installation token in
`GH_TOKEN` to the actual child process. Minimum permission is `issues: read`
with implicit `metadata: read`. The reader never finds credentials, mints or
rotates tokens, invokes another identity, or falls back to anonymous requests.
Session's GitHub connector is a separate carrier; availability there does not
supply credentials to a CLI child. A token's spelling is not proof of App origin.
Keep the provider's mint scope readback outside the candidate acceptance.

The existing host credential owner selects the supplier and repository scope.
For atom execution, its registered supplier injects the child's read token.
The standalone reader still requires a supervisor-supplied `GH_TOKEN`; it does
not load the atom's host profile itself. A historical supplier path is not a
current capability selection. Do not reconstruct App configuration or transfer
tokens by hand. Never print credentials, save them as evidence or put them in argv.
Missing supplier or installation access returns to the current credential owner.

A successful read has `status: read`, exact Issue JSON, observed HTTP status and
rate headers. A repeated read sends its ETag and returns saved bytes only after
an authenticated server 304. Cache and request serialization are scoped by credential and exact
URL under `XDG_CACHE_HOME/soodles/github` (default `~/.cache/soodles/github`).
No separate rate-limit poll is needed. No stale-success fallback is available.

On `status: refused`, consume `invalid` and `next.owner/required/help_argv`.
Malformed read arguments exit 2 before transport and name the caller with
`required: ["valid_read_arguments"]`. Use the returned reader help, correct
the argv using the already selected identity, and re-enter the reader.
This argument recovery requires no execution envelope.
Missing or unsupported repository identity and missing/expired credentials
remain supervisor inputs. GitHub supplies exact provider readback.
On `status: wait`, exit code is 75 and `next.not_before` is the provider-derived
Unix time. The caller may re-enter this same boundary after that time.
The reader does not sleep, retry, refresh credentials or start work.
Unknown provider failures without a usable deadline remain refusals. Existing
admission keeps its envelope and mailbox; a worker must still be dispatched by
Noodle. An adapter/daemon's interpretation of exit 75 belongs to that owner;
this feature does not certify Noodle fail-soft scheduling or recover #39.

When Test Manager selects reader verification, use its affected controls in
`tests/test_github_reader.py` and `tests/test_issue_execution.py`.
An ordinary Issue read does not request tests or a second read for cache evidence.
For selected live cache verification, preserve mint scope,
actual CLI exits, exact Issue, HTTP 200 → 304 headers and unchanged bytes;
record cleanup/revocation separately. Label any local owner fixture explicitly.
Do not infer a new live worker, model trace, or global network prohibition.

This recipe is P; receipt descriptions and request counts are N. Tested gates
in `github_reader.py` and real admission consumers are L. Provider token scope
and observed HTTP facts are R within their exact subject. Each added gate needs
defect RED, corrected same control GREEN and legal non-case GREEN; a proper
refusal is GREEN. Canonical acceptance and external landing remain separate.
