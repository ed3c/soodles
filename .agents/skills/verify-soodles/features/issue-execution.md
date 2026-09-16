# Bounded Issue execution and supervised handoff

The supervisor selects one real Issue and an external execution envelope. A real
Noodle-launched scheduler consumes the shared admission entry; Noodle owns the
order/worktree and dispatches the actual Codex worker. This recipe covers the
bounded task and quiescent handoff. It does not declare provider delivery or
Issue resolution, general scheduling, DAG execution or cross-platform support.

## Preconditions and preflight

Use only the supervisor-supplied control root, existing worktree, fixed launcher,
envelope path/digest, measured Noodle/Codex executables and bounded task. The
envelope binds the current provider Issue/body, owner, allowed paths and actual
starting source head. The child receives an explicit task and selected Skill;
it does not inherit this Session's conversation or authority.

The observed carrier is native macOS; the separate Linux runtime lock remains
unchanged. The installed entry checks platform and executable digests, current
Issue readback and Noodle canonical state. Worker entry additionally checks
session/order/stage, spawn readback, exact argv and clean starting worktree.
Supply the exact event-schema source locator with the task to avoid repository
search; this guidance is not a measured reduction in Agent cost.

Before starting the loop, read its canonical state and previous process groups.
An unchanged failed scheduler is not permission to reset state. After a material
input correction, use the actual Noodle owner's supported recovery entry and
read its acknowledgement. Do not create another scheduler, order ledger or
worktree. Missing launcher/envelope/carrier comes from the supervisor; missing
order/session state comes from Noodle; provider readback comes from GitHub.

## Drive and observe

- The installed schedule Skill calls the supervisor-provided launcher with
  `automatic`. Preserve its actual tool trace and normalized binding. Noodle
  consumes the conditional first-admission proposal; a fixture promotion is not
  evidence for this step.
- Observe the actual worker loading its selected Skill, reading the current
  Issue and executing the bounded task. Preserve code/Skill identities, actual
  commands, results and unexpected failures. A scheduler start alone is not a
  worker success.
- The Agent itself uses the admitted Noodle event interface to emit its typed
  outcome with actual session/order/stage identity. Read that event back and
  match it to canonical attempts and the worker tool trace. The parent must not
  substitute an event or interpret final prose as an outcome.
- During a live writer, the `supervised` entry must refuse takeover. After the
  owner parks the task and all recorded prior process groups are absent, invoke
  the same fixed launcher's `supervised` entry. Require `owned`, no new proposal,
  preserved canonical state and the original order/worktree.
- Consume the returned owner/input/operation/help. Help grants no retry or new
  writer. Changed Issue bytes require the supervisor's fresh binding before
  further effects; unknown provider writes require owner readback.

The demonstrated task ran the focused admission/execution and landing controls, then
emitted `blocked` because provider delivery remained with the supervisor.
That outcome was a successful bounded handoff, not a completed Issue. Existing
fixed defect controls supply RED → cure GREEN and legal non-case GREEN evidence;
the live refusal itself is GREEN. Preserve each control's fixture/live scope.

## Stop, evidence and delivery

Use a bounded observation deadline. On unexpected refusal or timeout preserve the last
boundary and raw traces, stop through the existing owner and read back process
groups. A missing outcome remains incomplete. Keep evidence outside the task
worktree, which stays available while provider delivery is unfinished.

Receipt contents include source/carrier/envelope/Skill identities, scheduler and
worker traces, exact typed event, live-writer refusal, quiescent takeover,
canonical-state comparison and residue. It has `authorizes_landing: false`.
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
