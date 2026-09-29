# Local supervisor admission

The authorized local Session may act as supervisor before initial authorization
selection. Use the existing `supervisor-admission authorize` producer to
materialize explicit selected inputs; after preparation use only the
[issue-atom entry](../../issue-atom/SKILL.md). The candidate writer cannot select
its judge. An already selected but missing authorization must be recovered by
its owner, not replaced through initial preparation.

## Initial authorization preparation

The supervisor supplies an absolute regular UTF-8 JSON file with these exact
schema-1 fields: `schema`, `repository`, `control_root`, `issue`, `task`,
`carrier`, `landing_owner`, `instruction_paths`. `issue` has `title`, `body`,
and an optional exact existing `number`. `carrier` is the measured
`platform`/`noodle`/`codex` descriptor already consumed by this producer;
`landing_owner` is the independently selected external
`path`/`sha256`/`verifier_sha256` descriptor. Keep those selected pins unchanged.
`instruction_paths` explicitly selects committed repository paths; an empty
list preserves schema-2 authorization, a nonempty list produces schema 3.
This file contains no credentials or alternative workflow selector.

```sh
python3 -B ./supervisor-admission authorize /absolute/selection.json SELECTED_SHA256 /absolute/new-output
```

The command validates the selection digest, exact clean Git toplevel/origin and executable continuation entry, Issue
base, executable carrier and external publisher through existing validators.
It derives committed instruction digests and host configuration identity. The
canonical runtime workflow remains fixed. It publishes `authorization.json`
and `prepared.json` outside the control root, with the receipt published last.
Existing output is never overwritten. `prepared.next` contains both the exact
lifecycle argv and `SOODLES_AUTHORIZATION_SHA256` environment binding; consume
both unchanged. Preparation creates no Issue, Noodle session or provider effect.
Do not ask the user to prepare files that the authorized Session can derive.
Unknown repository identity, unavailable capability or changed selected pins
requires the named owner input; it is not an automatic fallback.

Verify the commitment chain: explicit supervisor selection → existing
validator → saved authorization digest → exact lifecycle continuation.
Controls must cover schema 2/3, nearest legal numbered Issue/config cases,
changed pins, dirty/wrong root, invalid instructions, output collision and
publication failure. Observe raw argv, exit/stdout/stderr and filesystem
residue independently. A deterministic pass does not prove model improvement;
use the bounded P-class recipe for fresh behavior comparisons.

## Existing admitted execution producer

The lower-level `prepare` producer below remains owned by the lifecycle;
Agents do not run it as an alternative path or request its generated
envelope/checkpoint/launcher from the user.

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
`NOODLES_TOKEN_COMMAND` and App configuration from the child environment and execs Noodle.
The shared supplier consumer fixes repository `soodles` and permission
`issues:read`, ignoring wider inherited scope requests. It never
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
