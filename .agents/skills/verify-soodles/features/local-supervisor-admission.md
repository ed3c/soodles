# Local supervisor admission

Use this recipe only when a local Soodles task already has an externally selected
fresh Issue readback, measured carrier and control root, but a Noodle schedule
session has no `SOODLES_ADMISSION_LAUNCHER`.

The supervisor, not the Agent, selects the four inputs. From a committed Soodles
checkout run:

```sh
python3 -B ./supervisor-admission prepare \
  /absolute/fresh-issue-readback.json \
  /absolute/carrier.json \
  /absolute/soodles-control-root \
  /absolute/new-external-admission-directory
```

Consume the structured result. `next.kind=executable` returns the one fresh
Noodle start argv carrying the selected launcher path. Execute that argv exactly;
do not reconstruct the environment or search for another launcher. The producer
does not start Noodle itself.

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

Verification for this feature requires: missing-launcher baseline with zero
proposal; treatment reaching `proposal_pending` in the bounded provider fixture;
dirty working-tree bytes excluded from the bundle; envelope/runtime tamper
refused before proposal; historical unselected launcher ignored; existing
output refused. Receipts are local and `authorizes_landing=false`.

Do not use this recipe to recover a stale schedule, dead PID, historical order,
unknown provider write or request-changes state. Those remain with their current
Noodle/landing owners. Do not put credentials in argv or evidence.
