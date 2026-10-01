---
name: issue-atom
description: Advance one externally authorized local Soodles plus Noodle Issue through one resumable lifecycle command.
---

# Local Issue atom

Use the immutable schema-2 or schema-3 authorization selected by the external
supervisor. Here, external means outside the candidate's authority, not a
cloud service: the authorized local Session may select the host capabilities,
authorization and independently pinned landing owner on the same Mac. No cloud
Session, token handoff or separate supervisor daemon is required.
Before an authorization has been selected, the authorized local Session acts
as supervisor. Select the exact Issue/task, control root, measured carrier and
independent external landing owner within the user's scope. Put those explicit
inputs in the selection described by the
[authorization recipe](../verify-soodles/features/local-supervisor-admission.md),
then run:

```sh
python3 -B ./supervisor-admission authorize /absolute/selection.json SELECTED_SHA256 /absolute/new-output
```

On `status=prepared`, hand off the receipt's `authorization` and `next`
unchanged; its digest and executable argv/environment are the validated result.
Do not reconstruct a second continuation or guess internal authorization fields.
For lifecycle execution, consume `next.argv` and `next.environment` unchanged.
The CLI derives the committed base, instruction pins and host config identity,
validates them through the existing authorization owner, and returns the one
`issue-atom run` continuation. Do not hand-assemble derived authorization fields
or ask the user to calculate hashes/create an unprepared authorization file.
Missing selected identity/capability is still a typed refusal to its owner;
the command never discovers another identity or selects a judge for a writer.
After selection, preserve that authorization on handoff/resume: recover its
exact bytes instead of using `authorize` to replace a missing selected file.
This preparation role does not belong to the candidate writer.
It pins an external landing implementation; never select the
candidate's own verifier. The supervisor also supplies its SHA-256 in
`SOODLES_AUTHORIZATION_SHA256`. The host entry uses an explicit nonblank
`NOODLES_TOKEN_COMMAND` unchanged; otherwise it consumes the host owner's fixed
registration at `$XDG_CONFIG_HOME/soodles/provider.json` or
`$HOME/.config/soodles/provider.json`. Registration supplies capability, not
Issue authorization. The entry requests an installation token scoped to the
authorized repository. Do not ask a person or another session
to carry a `GH_TOKEN`, discover App keys, or prepare a checkpoint, envelope
or phase launcher. The entry materializes that execution state itself. The
authorization fixes the repository, exact base, Issue contract, control root,
task, Noodle and worker binaries, and required exact-head workflow evidence.
It also pins the original host `.noodle.toml` digest (or explicit absence).
An existing Issue is adopted only when its exact number, title and body are
authorized; it is never replaced with a newly created Issue on mismatch.

After authorization preparation, the lifecycle uses only:

```bash
./issue-atom run /absolute/authorization.json
```

If the selected authorization cannot be opened on this host, consume the
`authorization.path` refusal and its same-command continuation. The external
supervisor makes that exact selected file readable; do not reconstruct an
authorization from Issue prose, substitute another atom or transfer credentials.

The foreground entry observes normal waits for up to five minutes. A refusal
stops immediately; it is not retried. A nonzero publication-claim exit returns
`next.kind=input`, owned by Noodle, with the exact control root/order/subject.
Preserve that receipt across handoff. Obtain the named fresh owner readback
before re-entering the returned same command; elapsed time alone is no change.
Do not infer retryability from stderr or treat claim failure as a running worker.
Consume the JSON result. If bounded waiting
ends with `next` non-null, wait for the named material
owner/provider state change and execute only its returned `next.argv`, which
is the same command. Never use `./noodles issue handoff`. Do not choose issue automatic.
Do not choose landing dispatch, construct a phase-specific command, or retry
an ambiguous provider write.

A shared control root may be blocked by its current Noodle owner or another
atom entry. Consume the returned `next.owner`, exact required readback and
confirmed blocking order IDs; missing identity remains unknown. Re-enter only
the same `next.argv` after that material owner input changes. Elapsed time,
deleting a lock file or matching config does not grant ownership. Do not stop
another owner or construct its continuation. A verified exact owner may still
be observed through this entry.

If the external Issue selects a schema-4 comparison, consume the same owner's
current `next` for missing supervisor inputs. Do not construct replay commands,
substitute comparison evidence or remove the requirement. Candidate verification
and matching comparison receipts remain non-authorizing; this lifecycle entry
still owns continuation.

The owner persists its checkpoint before mutation, creates or adopts only the
Issue bearing the authorization marker (or the explicitly selected existing
Issue), always uses supervised Noodle
admission, obtains the exact Noodle publication claim, runs native publication
readiness once per immutable head, delegates PR publication to its existing
owner, requires exact-head CI, then delegates merge/closure/reconciliation to
the externally pinned landing owner. The existing admission producer binds the
task, worker, backlog and native config; the entry preserves the original host
config and starts the long-running Noodle loop once. A pristine root without a canonical
Noodle snapshot first receives one pinned Noodle `start --once` through this
same entry, with the producer-emitted bootstrap config that has no Issue backlog
adapter. Only its recorded zero exit and empty owner readback permit admission;
the full Issue backlog config belongs to the later admitted Noodle start.
An unknown exit or partial runtime refuses without replay. An existing matching owner is
observed, not restarted. Lost start results require owner readback.
For a fresh control root re-entering the same Issue, admission derives a stable
root-scoped Noodle order and worktree name. Retain earlier unmerged Noodle
worktrees; do not rename or clean them to make the new writer fit. A native
idle `schedule` order can coexist with the admitted order in the running loop;
the owner recognizes its exact pending shape. During execution, an active
scheduler can instead produce a read-only `own_start_wait` with `waiting_on=Noodle`
when the original started loop, held native lock, pinned launcher/config,
exact admitted order and scheduler session/process metadata all agree. Own
execute pending without attempts or a matching live execute attempt remains a
bounded wait through the same command, before credentials or provider effects.
Missing or contradictory identity, unknown/offered/stopped start and foreign
orders still refuse immediately; never retry an unchanged refusal. This
composite process evidence grants no effect custody or OS birth-identity proof.
Write credentials and host App/supplier configuration never enter Noodle or
candidate children. The existing start wrapper obtains only an Issue-read token
from the host supplier for those children; no person or session carries it.

Publication uses the clean native candidate's `native publication readiness`
receipt, not Linux runtime-lock acceptance on macOS. Linux canonical acceptance
runs after publication in the existing exact-head Actions workflow. A native
receipt cannot authorize merge or replace that gate. CI supplies evidence; the
landing owner, not the CI runner, emits merge and closure requests.

A `provider_credential_profile.*` refusal names the exact registered prerequisite
for the host credential owner to correct. Consume the returned `next` and use
the same invocation after correction; do not assemble App environment, search
for keys/tokens, register a candidate-selected capability or select another route.
Profile autoload is host-only and refuses Noodle child context.
A missing or failing supplier is a host credential owner's refusal, before a
new lifecycle checkpoint or provider write. An inherited `GH_TOKEN` is not a
fallback. External authorization still selects identity and capabilities;
having an App key does not authorize an Issue or select a Noodle/worker binary.
The cloud connector route keeps its own credential source and does not need
this local supplier or any token transfer.

An unchanged failed candidate head is terminal evidence, not retry authority.
An unknown Issue-create, branch, PR, merge, or closure outcome permits only
fresh exact readback. A competing marker or identity is a refusal.

If the pinned landing owner refuses a terminal local candidate before creating
its checkpoint or offering a provider write, retain the original authorization
and refusal receipt. The external supervisor may select compatible immutable
publisher bytes and use `landing-supervisor` with fresh provider readback, the
exact Noodle publication claim and execution envelope to create one pre-write
local activation outside the candidate. The route must pin the native claim's
path and SHA-256; PR head ref is the publication branch, not the Noodle
worktree. To adopt that activation, the supervisor supplies
`SOODLES_LANDING_ACTIVATION` as its absolute `manifest.json` path and
`SOODLES_LANDING_ACTIVATION_SHA256` as its exact digest, then runs the same
`./issue-atom run /absolute/authorization.json`. The entry binds the selected
publisher, candidate, order, PR, runtime and checkpoint before persisting the
continuation. Later re-entry needs only the original command; a changed
activation, offered write or unknown write refuses. Do not change the original
authorization or construct a landing claim or checkpoint in the Agent.

After confirmed merge and closure, a local reconciliation refusal may require
a corrected external publisher. The supervisor selects independently accepted
publisher bytes in an external descriptor with exact `path`, `sha256` and
`verifier_sha256`, then supplies its absolute path through
`SOODLES_LANDING_RESUME_OWNER` and its file digest through
`SOODLES_LANDING_RESUME_OWNER_SHA256`. Re-enter the same original command.
The entry permits this only for the original activation's confirmed post-write
checkpoint, persists the resume intent before invoking `landing resume`, and
changes only the verifier identity. An unknown result requires checkpoint
readback; never replay that resume, merge or closure from a prior trace.
For a Codex-managed detached control root, the corrected publisher must prove
its exact Git worktree registration, clean source and admitted ancestry before
ff-only synchronization. It does not switch the shared main checkout's branch.

`status=resolved` is legal only after the landing owner reports
`classification=RESOLVED` and local reconciliation has completed. Earlier
receipts retain `authorizes_landing=false`.
After confirmed provider closure and local fast-forward, the entry asks the
existing Noodle review owner to complete the original order, then reads its
acknowledgement. It never substitutes completion state. Only its own started
loop is shut down; unchanged installed config is restored to the pinned bytes.

Issue #131 is the bootstrap deployment: its Issue was created by the existing
external cloud supervisor. Its frozen P-class comparison and provider fixtures
prove the new local route; its own delivery still uses the pre-existing
external landing authority. The first live R-class use of this new Issue-create
entry belongs to the next atom and must not be backfilled into this receipt.

For a task requiring pinned instruction activation, the external supervisor uses
schema-3 authorization with a nonempty `instruction_pins` list of exact
`{path, sha256}` entries at the authorized `base_head`, or the exact
`prior_publication.head` for a same-Issue correction. The control base remains
unchanged; the published candidate owns the correction's instruction input. Use the same `issue-atom
run` command. The owner validates those committed UTF-8 regular-file bytes before
Issue mutation and seals their contents into the admission envelope and Noodle
stage prompt. Missing files, mismatched digests or invalid selection require a
corrected external authorization; never fill them from a guessed recipe or tip.
Schema 2 remains supported without this activation claim. Selecting the right
recipes and observing model behavior remain supervisor responsibilities.

## On-demand test scope

Use the [Test Manager](../test-manager/SKILL.md) as the sole scope owner. Native
publication readiness checks custody and CLI capabilities once per clean head;
it adds no fixed regression suite. Exact-head Linux Actions consumes the manager's
selected controls. Never infer full coverage, add a precautionary full run, or
repeat historical behavior experiments. Measure normal execution and waits from
logs. A supervising Session resolves available owner inputs itself under existing
authorization; an owner label alone is no reason for another human handoff.

For bounded repair, use `./system-context entry issue-atom run` to read committed
consumer/decision requirements. The same atom command consumes its fixed policy,
reserves repair intent under its existing locks and returns typed classification,
missing fact/producer, remaining budget and stop/wake condition. Only an exact
stale PR beside confirmed branch readback and a disposable publication projection
have automatic repairs. Unknown effects never grant write replay. Missing trusted
lineage leaves ordinary lifecycle available without invented zero counters.
`bounded_patch_capability_required` means no bounded patch-only model carrier is
installed; it launches zero models. Use current owner readback for continuation,
not a fresh authorization to reset repair history. This does not require an evals
skill or Agent comparison unless the admitted Issue selects that measurement.
