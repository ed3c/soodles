# Local supervisor admission

Use this recipe only for the local Soodles → Noodle carrier after the supervisor
has selected a fresh Issue readback, measured carrier and control root. Cloud
connector/Actions work keeps its existing provider identity and does not use
this bootstrap.

The local bootstrap has two inseparable supervisor-owned inputs:

1. immutable Soodles admission identity: external envelope + committed runtime
   bundle + launcher;
2. provider identity: the existing machine-local `NOODLES_TOKEN_COMMAND`.

Do not ask the Agent to discover either input. The command string and its token
output are host capabilities and must remain outside Git, argv, receipts and
candidate evidence.

From a committed Soodles checkout run:

```sh
python3 -B ./supervisor-admission prepare \
  /absolute/fresh-issue-readback.json \
  /absolute/carrier.json \
  /absolute/soodles-control-root \
  /absolute/new-external-admission-directory
```

`prepare` refuses before creating the output directory when
`NOODLES_TOKEN_COMMAND` is absent. A ready result returns one executable
`next.argv=[/external/.../start-noodle]`; execute that array unchanged. The
wrapper validates the pinned bundle and measured Noodle binary, executes the
host supplier exactly once immediately before child start, overwrites inherited
`GH_TOKEN` and `GITHUB_TOKEN`, injects `SOODLES_ADMISSION_LAUNCHER`, removes
`NOODLES_TOKEN_COMMAND` from the child environment and execs Noodle. It never
persists token bytes.

A supplier failure is a supervisor-owned refusal before Noodle child start.
Do not repair App client/installation/key configuration inside Soodles and do
not fall back to PAT, SSH, anonymous GitHub access or another identity. Those
machine-local inputs remain with the existing host credential owner.

The producer requires a registered Soodles origin and executable measured
carrier. For schema-3 Issues, the control-root committed `HEAD` must equal the
Issue `base_head`; legacy schema-1/2 Issues use that exact committed `HEAD`.
Bundle bytes come from `git show HEAD:path`, never dirty working-tree bytes.
The output directory must be new and outside the control root; existing output
is a refusal, never an overwrite/retry target.

After Noodle starts, the existing schedule entry is unchanged:

```sh
./soodles issue inspect
```

A ready schedule result returns exactly `[selected_launcher, "automatic"]`.
Execute that argv once and consume the existing admission owner's result. The
launcher revalidates envelope/runtime digests before calling the existing
automatic boundary.

Verification requires all of these directions:

- baseline missing launcher → supervisor-owned refusal, zero proposal;
- valid supplier → start wrapper child receives exact token in
  `GH_TOKEN/GITHUB_TOKEN`, receives launcher, and does not receive the supplier;
- stale inherited provider token is overwritten;
- token value and supplier command are absent from returned argv and persisted
  bundle bytes;
- treatment schedule inspect → launcher automatic → `proposal_pending`;
- missing supplier refuses before bundle creation;
- failing supplier refuses before child/proposal;
- envelope/runtime tamper, historical unselected launcher, foreign origin,
  carrier digest mismatch and existing output all fail closed.

These receipts are local and `authorizes_landing=false`. Do not use this recipe
for stale schedule recovery, dead-PID recovery, unknown writes or request-changes.
Those remain with their current Noodle/landing owners. A local credential
capability gap blocks this local operation only; it does not add prerequisites
to the independent cloud connector/Actions route.
