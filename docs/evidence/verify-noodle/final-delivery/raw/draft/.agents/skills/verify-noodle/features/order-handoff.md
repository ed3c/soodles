# Genuine original order and Session handoff

## Sub-features

Observe an externally admitted original Noodle order created before its writer;
bind the actual Session, worktree, selected Skill and tool trace; read the
worker's own typed outcome and external process wait/exit. Observe quiescence
without conflating it with order completion, provider delivery or local cleanup.

## How to get to it (user POV)

The supervisor supplies the existing admitted Issue/envelope, original order,
absolute project/worktree, measured Noodle and Session carrier, original Session
binding, raw trace location and selected external recorder. Noodle owns dispatch
and worktrees. Use a genuine admitted task; a missing subject remains blocked
with the supervisor as supplier and the existing admission entry as continuation.
Do not create an empty, post-hoc or second order for coverage, or start another
model session from this recipe.

## Driving it with the Noodle CLI

1. Doctor the supplied binary and source. Run
   `"$NOODLE_BIN" --project-dir "$NOODLE_PROJECT" status` as a compact readback.
   Read the supplied canonical snapshot/order and original Session's `spawn.json`,
   `process.json`, prompt and raw tool logs. Match Issue/envelope, order/stage,
   worktree, actual carrier argv, selected Skill and creation-before-writer timing.
   Status text alone cannot establish this binding or kernel process absence.
2. Observe the admitted worker performing its exact task. Preserve raw Session
   and tool evidence externally, including actual selected-file reads/digests.
   A completed authoring handoff may still leave application, live verification
   and delivery with the supervisor; label those scopes explicitly.
3. The worker itself obtains `event emit --help` from the measured binary and
   reads `event/types.go:StageMessagePayload` and `loop/stage_outcome.go` from the
   selected source. The measured CLI's `schema list` exposes mise/orders/status,
   not an event target. Use the real event invocation as an argv array:
   `[binary, "--project-dir", project, "event", "emit", "stage_message",
   "--session", actual_session_id, "--payload", serialized_payload]`.
   Payload fields are `message`, Boolean `blocking`, `outcome`, `order_id`, and
   integer `stage_index`. Bind actual `NOODLE_SESSION_ID`, `NOODLE_ORDER_ID` and
   `NOODLE_STAGE_INDEX` to the original owner readback. Completed bounded work
   uses `outcome: completed, blocking: false`; concrete inability uses
   `outcome: blocked, blocking: true`; an actual failed task uses failed/true.
   Emit one final typed outcome, then return naturally. No `stage_yield`, parent
   substitute, duplicate terminal message or invented child exit.
4. The coordinator reads the actual event from
   `.noodle/sessions/<actual session id>/events.ndjson` and matches raw worker
   tool evidence and canonical attempt. The existing owner rejects missing,
   foreign, duplicate or contradictory typed outcomes; do not work around it.
5. After the worker exits, consume the external recorder's actual `launch.json`,
   raw stdout and `exit.json` with `waited`, returncode, PID/PGID and timestamps.
   The selected recorder interface is
   `python3 "$PROCESS_RECORDER" "$PROCESS_EVIDENCE" -- COMMAND [ARGS...]`;
   COMMAND is the supervisor's already admitted carrier argv, never a command
   this recipe invents or relaunches. The recorder observes exit, not semantic
   outcome. Verify the original process and group are absent using the existing
   owner/observer kernel readback; unknown/permission-denied is not absence.
6. Read the original order through Noodle's owner after reconciliation. Record
   separately: bounded stage outcome, actual process exit/quiescence, original
   order status, provider merge/Issue closure and Noodle-owned worktree cleanup.
   Keep evidence outside the worktree and verify it survives any owner cleanup.

Source: `cmd_status.go`, `cmd_event.go`, `event/types.go`, `event/paths.go`,
`loop/stage_outcome.go`, `loop/cook_completion.go`, `loop/cook_spawn.go`.
Nearest controls: `cmd_event_test.go`, `loop/typed_outcome_test.go`,
`loop/reconcile_test.go`. The supervisor-selected external process recorder
supplies independent wait/exit observations, not a replacement lifecycle owner.

## Gotchas

A running worker cannot attest its own future exit. Missing recorder exit evidence
remains pending; a semantic completed event, terminal metadata or exit-zero CLI
call cannot substitute for the actual carrier wait result. Do not synthesize
zero exit from final prose. An expected blocked outcome may correctly hand off
unfinished work without making the Issue RESOLVED.

Noodle's `loop/cook_spawn.go:resetWorktreeState` can discard uncommitted tracked
and untracked work on reuse. Before an authorized owner requeue, preserve actual
complete draft bytes/digests externally or a real permitted commit; never invent
an interim checkpoint or claim an unsaved patch survived. Preserve original
order identity and unknown writes for owner readback.

Provider delivery stays with the existing external landing owner and connector.
Its current next/request and exact-head readbacks govern that work. Neither this
recipe, event emission, clean local tests nor `next: null` grants landing authority.
