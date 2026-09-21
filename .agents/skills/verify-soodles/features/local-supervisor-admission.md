# Local supervisor admission

Use this recipe only when a local Soodles task already has an externally selected
fresh Issue readback, measured carrier and control root. The local host
supervisor must also already own a provider credential supplier through
`NOODLES_TOKEN_COMMAND`; the Agent never receives that command as task input and
never reconstructs GitHub App identity.

From a committed Soodles checkout run:

```sh
python3 -B ./supervisor-admission prepare \
  /absolute/fresh-issue-readback.json \
  /absolute/carrier.json \
  /absolute/soodles-control-root \
  /absolute/new-external-admission-directory
```

`prepare` is a supervisor preflight. It refuses before creating output when
`NOODLES_TOKEN_COMMAND` is absent. A ready result returns one
`next.kind=executable` whose argv contains only the generated external
`start-noodle` wrapper path. Execute that argv exactly; do not add environment
assignments, copy a token into argv, search for another launcher or mint
credentials inside the candidate.

The start wrapper is the local equivalent of cloud-owned provider identity
injection. Immediately before Noodle starts it executes the configured
`NOODLES_TOKEN_COMMAND`, requires exactly one non-whitespace credential,
overwrites inherited `GH_TOKEN`/`GITHUB_TOKEN`, injects the selected
`SOODLES_ADMISSION_LAUNCHER`, removes `NOODLES_TOKEN_COMMAND` from the child
environment, and execs the measured Noodle binary. Token bytes are never written
to the admission bundle or returned in structured output. Supplier failure is a
supervisor refusal before Noodle starts.

The producer requires a registered Soodles origin and an executable measured
carrier. For schema-3 Issues, `base_head` must equal the control root's committed
`HEAD`; legacy schema-1/2 Issues use that exact supervisor-selected committed
`HEAD` as the external envelope base. It materializes envelope/runtime bytes
from `git show HEAD:path`, not from working-tree bytes. The output directory
must be new and outside the control root. Existing output is a refusal; never
overwrite or reuse it.

When the resulting Noodle schedule session runs, follow the existing schedule
entry unchanged:

```sh
./soodles issue inspect
```

A ready result must return exactly `[selected_launcher, "automatic"]`. Execute
that argv once and consume the existing admission owner's result. The launcher
rechecks the external envelope/runtime digests before calling the existing
automatic boundary.

Verification requires: missing-launcher baseline with zero proposal; missing
credential supplier refusing before bundle creation; treatment proving the
start wrapper injects fake provider credentials and launcher while removing the
supplier; no token/supplier in argv or bundle; treatment reaching
`proposal_pending`; dirty working-tree bytes excluded from the bundle;
envelope/runtime tamper refused before proposal; historical unselected launcher
ignored; existing output refused. Receipts are local and
`authorizes_landing=false`.

Do not use this recipe to recover a stale schedule, dead PID, historical order,
unknown provider write or request-changes state. Those remain with their current
Noodle/landing owners. Do not add App client IDs, installation IDs, private keys,
PATs or fallback identities to repository state. The host's configured supplier
remains the only local credential owner.
