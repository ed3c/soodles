# External authorization materialization protocol

Selected baseline: `7e602dbe3fd4db670b15ef0267025e6c1dfffd4d` from the read-only source
`/Users/neon/.codex/worktrees/authorization-shortest-path/soodles`.
This protocol and its oracle are selected by the external supervisor before implementation.
The candidate cannot amend this oracle, its frozen validator, or its selection.

## One bounded correction

Add `supervisor-admission authorize SELECTION.json EXPECTED_SHA256 OUTPUT`.
The supervisor already owns the choice of carrier, publisher, Issue, task and
control root. This command mechanically materializes those explicit inputs;
it neither chooses authority nor begins the Issue lifecycle. A missing file
that was already selected is a refusal requiring its owner to restore/correct
that selected input, never an invitation to synthesize another authorization.

SELECTION is an absolute regular UTF-8 JSON file. Reject duplicate JSON keys.
Verify the digest of its exact bytes before consuming its values. Its exact
schema-1 fields are `schema`, `repository`, `control_root`, `issue`, `task`,
`carrier`, `landing_owner`, `instruction_paths`. The Issue object has title/body
and optional positive integer number. Carrier is the existing full measured
platform/noodle/codex object. Landing owner retains path/sha256/verifier_sha256.
No credential input, workflow selector, repinning or fallback discovery.

Validate the full carrier via existing `validate_carrier(worker=True)` and the
authorization via the existing Issue-atom validator. Preserve all selected
carrier and landing-owner bytes/digests; changed files refuse. Derive base_head
from the clean exact root HEAD and require the contract's base_head equals it.
Validate repository/origin through the existing repository binding. Derive
host_config_sha256 from actual `.noodle.toml` bytes, null when absent. Empty
instruction_paths yields schema_version 2; nonempty yields schema_version 3,
with each path's exact committed blob digest. Use existing instruction path,
regular-file, UTF-8, size and count constraints, including symlink refusal.

The omitted workflow field is deliberately fixed to the existing canonical
repository profile: path `.github/workflows/runtime.yml`, job `runtime-evidence`,
step `Canonical acceptance on the exact candidate head`. Require these values
still occur in the selected committed workflow; do not add a new selector.

OUTPUT must be a new absolute directory outside the control root, with an
existing parent. Validate before creating the final output. Temporary staging
for existing path-based validation is permitted only with cleanup. After all
validation, exclusive mkdir may reserve the final directory; write
authorization.json and publish prepared.json atomically last as the completion
marker, with final absolute paths. On publication failure clean up only bytes
owned by this invocation. Never replace a concurrently created output directory.
This bounded atomic contract does not require a new lock or rename abstraction.
Refusal: typed nonzero JSON, status refused, authorizes_landing false, invalid
field/value, next input owner and required correction; no output or staging
residue and no changes to preexisting bytes. The command performs no provider,
credential, Noodle or model effects and creates no lifecycle state ledger.

Success prints exactly the saved prepared.json object. Required receipt:

```json
{
  "owner": "supervisor.authorization",
  "status": "prepared",
  "authorizes_landing": false,
  "authorization": {"path": "OUTPUT/authorization.json", "sha256": "DIGEST"},
  "next": {
    "kind": "executable",
    "owner": "soodles.issue-atom",
    "argv": ["CONTROL_ROOT/issue-atom", "run", "OUTPUT/authorization.json"],
    "environment": {"SOODLES_AUTHORIZATION_SHA256": "DIGEST"}
  }
}
```

The receipt may carry additional top-level informational fields. The
authorization, next and environment structures above are exact. Continuation
must refer to the selected root and final authorization, never staging paths.

## Executable oracle

Run `python3 -B ORACLE_DIR/oracle.py SUBJECT_ROOT NEW_EXTERNAL_EVIDENCE_DIR`.
The oracle imports only committed baseline modules under its own frozen/
directory; candidate code is executed only through its public CLI in a separate
process. It creates disposable independent Git fixtures, does not alter SUBJECT,
and does not invoke the returned continuation. Each fixture's selected
publisher and carrier are inert local bytes. A Python audit guard rejects and
records subprocesses other than bounded read-only Git and blocks network
connections/name resolution, shell execution and exec/spawn. Complete file-byte
snapshots, including ignored root state and staging directories, detect residue.

The matrix includes schema2, schema3, numbered Issue and existing host config;
dirty root, wrong base/repository/origin; changed selection digest, missing
selection, duplicate keys and missing/extra selection fields; changed Noodle,
Codex and publisher/bundle bytes; carrier platform/argv; invalid, missing,
absolute, traversing, duplicate and symlink instructions; existing, inside-root,
relative and missing-parent outputs; canonical workflow mismatch. Every case
records argv, exit, stdout and stderr. Success is independently checked against
frozen authorization validation and exact expected structure.

Guard limitations: this is a bounded defect discriminator, not a malicious-code
sandbox or proof against races, native extensions, out-of-scope filesystem writes,
or every possible failure-injection schedule. Atomicity is additionally reviewed
at the implementation boundary; byte snapshots detect normal refusal residue.
No unmeasured behavior is promoted to authority. Receipt authorizes_landing=false.

Baseline missing `authorize` is deterministic RED, not a model failure or a
measured model improvement. Do not convert an old prompt defect into a new
baseline: the selected issue-atom Skill already tells first-time supervisors
to prepare and forbids rebuilding an already selected authorization.

## Neutral fresh-consumer input recommendation

The supervising observer may create an independently selected disposable fixture
and give a fresh consumer only: (1) the task "Prepare the supplied local Issue
authorization and return the executable continuation without starting it";
(2) the selected source root/ref; (3) one exact selection path and digest;
(4) one new external output path. Include the selected entry instruction/Skill
only when that is the comparison's explicitly fixed context condition. Do not
give expected output fields, oracle tests, scoring, proposed implementation, or
baseline verdict. Tell both arms they may use supplied values and read-only
local inspection but must not start provider/Noodle/model effects.

Keep carrier/model choice, permissions, inputs and stopping conditions identical
between arms. The parent supervisor owns actual fresh-consumer execution and
model choice. Record actual tool requests/results and distinguish these records
from a complete platform transcript. Measure preparation completion, missing
selected-input recovery, tool reads, hand-built fields, and refusal behavior.
Only observed comparable measurements support a combined bounded reduction;
an unobstructed baseline or missing fresh-consumer capability does not support
an improvement claim. This oracle alone measures only deterministic mechanics.
