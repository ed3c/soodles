# Local supervisor admission

Before initial authorization selection, the authorized local Session may act
as supervisor. Use the existing `supervisor-admission authorize` producer to
materialize explicit selected inputs. After preparation, use only the
[issue-atom entry](../../issue-atom/SKILL.md). The candidate writer cannot select
its judge. An already selected but missing authorization must be recovered by
its owner, not replaced through initial preparation.

## Initial authorization preparation

Before serializing selection, apply the issue-atom
[scope and completion guidance](../../issue-atom/SKILL.md#preserve-the-request-through-admission-and-delivery).
The producer validates selected inputs. It cannot determine whether the supervisor
omitted a user requirement. Before pinning the task and contract, preserve that
requirement in them. Do not admit a smaller task and treat its success as completion.
Carry writer outcomes and later owner work in those existing inputs. Publication
can follow writer completion without returning control to the supervisor.

The supervisor supplies an absolute regular UTF-8 JSON file with these exact
schema-1 fields: `schema`, `repository`, `control_root`, `issue`, `task`,
`carrier`, `landing_owner`, `instruction_paths`. `issue` has `title`, `body`,
and an optional exact existing `number`. `carrier` is the measured
`platform`/`noodle`/`codex` descriptor already consumed by this producer;
`landing_owner` is the independently selected external
`path`/`sha256`/`verifier_sha256` descriptor. Keep those selected pins unchanged.
`instruction_paths` explicitly selects committed repository paths; an empty
list preserves schema-2 authorization, a nonempty list produces schema 3.
A supervisor may additionally select `lifecycle_owner` with the absolute external
`issue-atom` path, its `sha256`, and the aggregate `source_sha256` over the fixed
runtime file set. It remains separate from `landing_owner` and the control root.
The producer returns that exact executable; the runtime checks selected files
and its own execution location before creating lifecycle state or effects.
Committed preparation readback preserves the selection even when runtime files
are unavailable; execution still requires fresh byte validation. This is a
supervisor selection input, never a candidate-selected judge or a CLI policy flag.
This file contains no credentials or alternative workflow selector.

```sh
python3 -B ./supervisor-admission authorize /absolute/selection.json SELECTED_SHA256 /absolute/new-output
```

The command uses existing validators to check the selection digest, exact clean
Git toplevel and origin, executable continuation entry, Issue base, executable
carrier and external publisher. It derives committed instruction digests and
host configuration identity. The canonical runtime workflow remains fixed.
The command writes complete `authorization.json`, `prepared.json` and
`selection-binding.json` files in unique private staging. All receipt paths name
the original final output. It fsyncs the files and staging before publishing the
directory atomically without replacement. That publication is the sole identity
commit. The command then fsyncs the parent directory. If Darwin or Linux lacks
exclusive rename capability, the command refuses. An existing empty directory
is foreign, never a reservation. A catchable precommit failure removes only the
invocation's staging. SIGKILL may leave private staging residue. That residue
is never a continuation. A postcommit failure or lost response must preserve the
entire final bundle.

For preparation readback, use the existing authorize entry. Supply the current
selection path and SHA and the same original output directory. A prior invocation
or stdout is evidence, not a current input selector. The executable
compares that selection with the immutable committed binding and refuses changes.
Do not recompute a digest, create a replacement selection, pick a new output or
bypass a refusal. Missing, unreadable or malformed committed components return
an `authorization.*` input refusal naming the damaged component and its path.
Preserve all artifacts for the named owner. Strict regular-file,
schema, raw digest, selection, final path and expected continuation validation
must succeed. Readback does not require checks of current host config, base,
instruction, carrier or clean head. Missing authorization, receipt or binding
causes a refusal without repair. Corrupt, partial, foreign or symlink output and
a changed selection also cause that refusal.
Concurrent publishers may read a matching winner only after these same checks.
Readback proves preparation provenance, not current runtime readiness.
`prepared.next` contains both the exact lifecycle argv and
`SOODLES_AUTHORIZATION_SHA256` environment binding; consume both unchanged at the
existing Issue-atom owner, which checks current readiness before effects.
Legacy complete prepared receipts retain their original trusted handoff; legacy
bundles without a binding cannot be adopted by authorize. Preparation creates no
Issue, Noodle session or provider effect. Do not ask the user to prepare files
that the authorized Session can derive. Unknown identity or missing capability
requires its named owner, not a replacement authorization.

The following controls apply when Test Manager selects verification of changed
admission production, atomic publication or readback behavior. Ordinary authorize
and continuation use their returned receipts; they do not run fault injection.
For a selected control, verify that the selection passes through the existing
validator to an atomic bundle and its exact continuation.
Keep nearest schema 2/3, numbered Issue/config, pins, dirty/wrong root and invalid
instruction controls. Kill real child processes during actual receipt writes
and immediately after final publication. Before commit, require the final output
to be absent. After commit, require a complete, readable final output with the
same argv and unchanged identity. Require observed SIGKILL, not simulated success.
Test missing/corrupt
files, rehashed arbitrary argv, foreign empty/nonempty/symlink output including
publication races, and concurrent same/different selection. Preserve refused
evidence and record exit/stdout/stderr and filesystem residue independently.
A deterministic pass does not prove model improvement. Use the bounded P-class
recipe only when the admitted task selects that comparison.

## Same-Issue failed-head correction

For an exact failed runtime on an open PR, the authorized local Session derives
`prior_publication` and `prior_atom` from current provider readback and the
original immutable authorization. Select both in the same schema-1 selection;
never ask the user to reconstruct those known identities. The current Issue
contract must cover the correction. Preparation retains the original control
root, Noodle order/worktree and PR branch; it does not activate unselected
lifecycle implementation bytes.

Consume the prepared `issue-atom run` continuation. Its owner restores the old
host, starts the selected replacement bundle with a process hold, requests
changes on the original review, observes canonical failed state, publishes one
revised proposal and observes its exact promotion before releasing the hold.
The original failed attempt remains historical evidence. A control ack alone
cannot prove transition; a lost control/proposal response permits readback only.
Do not choose mode/control commands, edit checkpoints or repeat historical writes.

The discriminating controls are in `tests/test_issue_atom.py` and
`tests/test_issue_execution.py`: wrong review/promotion identity, foreign
control, missing process hold, ack without transition and lost responses must
refuse or wait without another effect. These product controls do not establish
Agent improvement; a separately selected P-class comparison needs fresh isolated
consumers and independently fixed scoring. A missing supported owner activation remains
an explicit capability gap, not a request for the user to recreate authorization.

## Same Issue after provider base advancement

When fresh provider readback shows a descendant base, use a fresh clean control
root at that exact base with the same numbered Issue and `prior_publication`.
Omit `prior_atom`: its existing contract keeps the old order and old base intact.
Retain the quiescent old owner, failed attempt, authorization and publication
receipts. This fresh admission has no renewed automatic repair budget.

Select a schema-3 body with only `base_head` and existing base-revision frozen
hashes updated from the old/new Git bytes. Keep head pins, scope, outside prose
and marker unchanged. Select instruction paths from the new base. The prepared
same-command owner validates the exact current provider base and failed open
PR, records its Issue-update intent before PATCH, and adopts only exact readback.
A lost result cannot offer a second PATCH. Do not edit the Issue, migrate Noodle
state or replay unknown publication effects from the supervising Agent.

A completed failed runtime includes failure before acceptance with the named
acceptance step completed/skipped. Queued, running, cancelled, absent, ambiguous
or successful runtime does not authorize this failed-head continuation. Use the
normal changed-head PR CI and its Test Manager scope; no extra local regression
or model experiment is implied. See `tests/test_base_readmission.py` for the
provider-effect and instruction-binding controls.

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
Execute that argv once and consume the existing admission owner's result.
Before calling the existing automatic boundary, the launcher revalidates the
envelope and runtime digests.

When Test Manager selects verification of this producer, use the affected
directions below. These are behavior controls, not steps for every admission:

- If the baseline launcher is missing, require a supervisor-owned refusal and zero proposals.
- With a valid supplier, require the start wrapper child to receive the exact
  token in `GH_TOKEN/GITHUB_TOKEN` and the launcher. It must not receive the supplier.
- Require a stale inherited provider token to be overwritten.
- Require the token value and supplier command to be absent from returned argv
  and persisted bundle bytes.
- In treatment, require schedule inspect to reach launcher automatic and then `proposal_pending`.
- If the supplier is missing, require refusal before bundle creation.
- If the supplier fails, require refusal before child start or proposal.
- Require envelope or runtime tamper, a historical unselected launcher, a foreign
  origin, a carrier digest mismatch and existing output to fail closed.

These receipts are local and `authorizes_landing=false`. Do not use this recipe
for stale schedule recovery, dead-PID recovery, unknown writes or request-changes.
Those remain with their current Noodle/landing owners. A local credential
capability gap blocks this local operation only; it does not add prerequisites
to the independent cloud connector/Actions route.
