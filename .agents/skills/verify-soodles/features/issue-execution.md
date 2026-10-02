# Bounded Issue execution and supervised handoff

For a supervisor-selected repository other than Soodles, first use the
[cross-repository delivery](cross-repository-delivery.md) recipe. Repository
identity comes from the external envelope; do not reconstruct it from the
current checkout, conversation or Issue prose.

The supervisor selects one real Issue and an external execution envelope. A real
Noodle-launched scheduler consumes the shared admission entry. Noodle owns the
order and worktree and dispatches the actual Codex worker. This recipe covers the
bounded task and quiescent handoff. It does not declare provider delivery or
Issue resolution, general scheduling, DAG execution or cross-platform support.

For normal atom execution, consume the original `issue-atom run` continuation.
The observations below describe its boundaries, not additional calls or controls
to run on each handoff. Test Manager selects any requested fault/takeover controls.

## Preconditions and preflight

Use only the supervisor-supplied control root, existing worktree, fixed launcher,
envelope path/digest, measured Noodle/Codex executables and bounded task. The
envelope binds the current provider Issue/body, owner, allowed paths and actual
starting source head. The child receives an explicit task, selected Skill and
the complete validated structured Issue contract alongside the exact binding
in its stage prompt; it does not inherit this Session's conversation or authority.

The observed carrier is native macOS; the separate Linux runtime lock remains
unchanged. The installed entry checks platform and executable digests, current
Issue readback and Noodle canonical state. Worker entry additionally checks
session/order/stage, spawn readback, exact argv and clean starting worktree.
The writer uses the existing [execute](../../execute/SKILL.md) stage-outcome
entry; event-schema discovery and payload construction belong to that executable.

Before starting the loop, read its canonical state and previous process groups.
An unchanged failed scheduler is not permission to reset state. After a material
input correction, use the actual Noodle owner's supported recovery entry and
read its acknowledgement. Do not create another scheduler, order ledger or
worktree. Missing launcher/envelope/carrier comes from the supervisor; missing
order/session state comes from Noodle; provider readback comes from GitHub.


## Experiment readiness handoff

For a supervisor-selected local behavior experiment, consume the complete
`./soodles issue readiness HANDOFF.json HANDOFF_SHA256 LOCAL.json LOCAL_SHA256`
invocation. This operation stays inside the existing issue-execution owner: it
does not launch Codex, create a worktree, choose an observer/ref/model, score the
experiment, retry, or grant landing authority.

The portable handoff fixes experiment identity, three cases, baseline/treatment
refs, task/input bytes and capture identity. The scoring observer stays with the
external supervisor and is not included in the consumer-visible handoff. The
byte-bound host-local binding fixes the selected carrier, exact clean workdirs,
executable identity, and external evidence and materialization roots.
Readiness only projects packets. The supervisor separately owns any consumer
launch authorization. A refusal names the
exact missing input and owner. Do not search history, borrow another Issue's resources,
select refs, create workdirs, construct packets or reconstruct argv.

`READY` means exactly six immutable run packets and replay argv were materialized
and the next consumer needs no operational inference before its assigned run.
The supervisor launches the fresh consumer using the supplied packet; the Agent
must not alter run membership, refs, inputs, argv or evidence
destination. Deterministic readiness is not behavior improvement evidence.

## Drive and observe

For the existing local `issue-atom run` entry, a proven own active scheduler with
an exact pending/running admitted execute stage returns read-only
`execution.action=own_start_wait`, `waiting_on=Noodle` and the same `next.argv`.
Its existing bounded foreground drive refreshes identity each observation;
at its deadline, retain `wait_exhausted` and wait for material owner change.
It does not reach credentials, provider/start/claim or checkpoint writes.
An idle scheduler resumes the normal gates; identity drift or missing metadata
refuses immediately. Do not reinterpret a refusal as waiting or repair another
owner. The loop/lock/config/session evidence supports this bounded wait only,
not generation-proof process identity or delivery authority.

- The installed schedule Skill calls the supervisor-provided launcher with
  `automatic`. Preserve its actual tool trace and normalized binding. Noodle
  consumes the conditional first-admission proposal; a fixture promotion is not
  evidence for this step.
- Observe the actual worker loading its selected Skill, consuming the complete
  admitted contract from its stage prompt and executing the bounded task. No
  duplicate GitHub read is required from the child; the installed entry retains
  its fresh provider readback and exact prompt guards. Missing contract returns
  to the existing admission owner; amendments require a fresh supervisor envelope.
  Preserve code/Skill identities, actual
  commands, results and unexpected failures. A scheduler start alone is not a
  worker success.
- The writer uses `./stage-outcome OUTCOME MESSAGE` under its admitted execute
  instructions. The entry binds session/order/stage identity. Read the event back and
  match it to canonical attempts and the worker tool trace. The parent must not
  substitute an event or interpret final prose as an outcome.
- A selected takeover control checks that the direct `supervised` entry refuses
  a live writer and returns `owned` for the exact quiescent original order without
  another proposal. Normal atom execution uses its same-command observation path;
  do not invoke the lower-level launcher to reproduce that control during delivery.
- Consume the returned owner/input/operation/help. Help grants no retry or new
  writer. Changed Issue bytes require the supervisor's fresh binding before
  further effects; unknown provider writes require owner readback.

Historical evidence includes a task that emitted `blocked` while delivery remained
with the supervisor. That is not the current outcome rule: a writer that completes
its admitted work reports `completed`; later delivery alone is not a blocker.
Use the execute skill for current outcome selection and preserve historical
receipts without relabeling them. Fixture/control results retain their own scope.

## Stop, evidence and delivery

An observation deadline ends foreground waiting, not the writer's work. Preserve
`wait_exhausted`, the last readback and same-command continuation; observe the named
owner change before re-entry. A refusal stops only the affected operation pending
its required input. Neither condition authorizes stopping or restarting a writer.
An actual child timeout retains its unknown outcome for owner readback. Terminate
only when the existing owner or an explicitly selected fixture cleanup requires it.
A missing outcome remains incomplete. Keep evidence outside the task worktree.

Record source/carrier/envelope/Skill identities, observed scheduler/worker traces,
typed event and relevant owner readbacks. Include live-writer refusal, takeover
and residue evidence only for controls actually selected and exercised; a normal
handoff need not manufacture those situations. The receipt has `authorizes_landing: false`.
It proves the specifically observed execution/handoff only. Source changes after
that worker must retain the original execution identity and obtain fresh final
candidate verification; do not relabel an old worker as a new-head execution.

The existing landing owner separately owns merge/closure requests and final
reconciliation. Only its exact subject readbacks and terminal receipt establish
delivery. Do not delete a pending worktree from this recipe or treat `next: null`
as completion.

Sources: `issue_admission.py` owns the shared binding, `issue_execution.py` owns
consumer/worker/takeover gates, and `tests/test_issue_execution.py` contains local
provider/owner fixture controls. Those fixtures are not live runtime evidence.

## Publication-claim handoff

After a parked worker, a nonzero Noodle publication-claim exit is a typed
Noodle-owned input refusal, never evidence of a running worker. Preserve its
receipt and obtain the named owner input through the unchanged continuation.

Only when Test Manager selects claim-failure verification, drive the Issue-atom
boundary with a failed claim process in a fixture. Require one claim attempt,
no wait, no readiness or publication effect, and a preserved execution checkpoint.
Require a same-command continuation that names the exact control root, order and subject.
Contrast a genuinely running owner (pending, no claim) and a successful claim
(existing readiness/publication path). Across fresh processes, retain the same
authorization and refresh material owner state before re-entry. Fixture effects
prove this transition only; actual delivery still requires its terminal receipt.
For a task-selected model behavior comparison, use the P-class recipe with fresh
consumers and external observations; a code-level retry reduction is not token cost.

## Selected instruction activation

For schema-3 local atom authorization, the supervisor supplies nonempty
`instruction_pins` at its exact admitted base. The existing owner materializes
a schema-2 envelope with `execution.instruction_context`: `source_head` plus
`files` entries containing `path`, `sha256`, and exact UTF-8 `content`. The stage
prompt carries that context unchanged. Consume the supplied contents; do not
choose a second recipe or fetch a newer revision. Missing or altered context is
a pre-launch refusal through the same admission owner. Legacy schema-1 envelopes
remain valid without a selected-context guarantee. Record the projection and
process refusal separately from fresh-consumer behavior: supplied bytes do not
establish reading, adherence, model memory or a global hill-climb result.
