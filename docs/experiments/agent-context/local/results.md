# Corrected child-exit observation, 2026-09-17

Current local result (2026-09-17): [three complete matched cases](comparison-results.md), both arms GREEN with disclosed limits and no superiority claim. The capability/prospective history below remains unchanged.

Status: **CAPABILITY_OBSERVED** for the explicitly instrumented local carrier.
[Immutable receipt, both attempts and raw evidence](https://github.com/ed3c/soodles/blob/397e9efd4824b3bde3976081b169b452ff423e7c/docs/experiments/agent-context/exit-recorder/receipt.json).
The capability judge has exactly the original bytes. Its verdict has no missing
fields and no violations. Historical INCOMPLETE observations below remain intact.

## What changed and what actually ran

The initial child-wait recorder preserved the scheduler exit but still lost the
worker exit. Pinned Noodle source `loop/session_meta_repair.go` calls ForceKill on
the whole process group after terminal metadata appears; the actual log reported
that terminal-meta completion. This identifies a recorder race. No historical
kernel trace is available to certify which signal terminated that first worker.
A real owner-like group-kill control makes the previous recorder RED.

The correction captures native stdout bytes immediately, forwards nonterminal
lines, and defers the first terminal event plus subsequent lines until the actual
child exits and its wait receipt is durable. It then forwards those exact bytes.
The recorder retains Noodle's group, stdin and stderr; it writes no Agent outcome
or canonical state. This changes terminal delivery timing and therefore proves
an instrumented observation, not natural exit of the uninstrumented carrier.
Noodle downstream timestamps describe delivery; they are not original emission
timestamps. No hidden service model or routing claim follows.

The new 180-second bounded drive reached the typed blocked handoff in 79.08
seconds from loop start, using clean source
`7323aea7f5a7dc1da34c64fdb61f3145c8e2f3ff`:

- Noodle session: `soodles-39-0-execute-20260916-195611-b68cd5`.
- Recorder PID/group: `30271`; waited Soodles → Codex child PID: `30272`.
- Actual child wait return code: **0**, recorded before terminal delivery.
- Native thread: `01a0abca-8a6d-7d81-89c6-c7ffc987a940`.
- Native turn: `01a0abca-8b1b-7c90-935d-2aa700eb1be6`.
- Persisted native turn model: **gpt-6-astra**, effort **high**.
- Agent executed the marker and itself emitted one matching `blocked` outcome
  for order `soodles-39`, stage 0. This was the requested bounded handoff.

The external audit joins recorder PID to Noodle process metadata, child/session/
order/stage/cwd/argv to the admitted exec chain, and the native thread/turn to the
raw tools. All 15 binding checks pass. Original stdout byte count/digest match the
receipt; every captured native event equals the downstream event after excluding
Noodle's added delivery timestamp. Every started native item has one result.
Noodle's attempt exit_code remains null; it was not edited or used as a substitute.

## Controls, limitations and cleanup

Fourteen unittest methods pass. Omitted receipts, fabricated zero, lost signal
status and old-record overwriting each make their controls RED. Restoration and
legal success/nonzero/signal controls are GREEN. The same physical group-kill
control is RED with the previous recorder and GREEN with the correction. These
are recorder controls, not claims of a baseline-instruction defect.

Both fresh probe worktrees were clean and removed by Noodle without force or
merge. Recorded loop, recorder, child and read-only App Server process groups
were observed absent. The first read-only App Server cleanup check briefly saw
its group still present; the later absent readback is preserved. A setup admission
from the archive directory correctly refused envelope.path; invoking from the
supplied control root then succeeded before any model task. Doctor verified the
worktree cwd/root and repo detection; its overall exit 1 was TERM=dumb, retained
as such rather than called an overall doctor PASS.

The narrower exit/model/tool capability gate is now satisfied. Full matched
baseline/treatment cases remain **NOT_RUN**, actual compaction is unproven and
cloud verdicts are unchanged. #39 stays open and PR #40 draft. Final-head canonical
acceptance and existing delivery/reconciliation remain separate; all experimental
receipts have authorizes_landing=false.

---

# Local capability observation, 2026-09-17

Class N report over the captured L discriminator result. Status: **INCOMPLETE**.
This is a new `local_macos_noodle_codex_exec` carrier; no cloud verdict changes.
[Immutable receipt and raw archive](https://github.com/ed3c/soodles/blob/1ad24148dfb44104dfa3c5071988114ca2966fe5/docs/experiments/agent-context/local-capability/receipt.json)
include the preselected judge, recorder, actual Issue body/envelope, controls,
Noodle runtime files, CLI JSONL, native thread readback and native rollout.

## Actual run

Soodles admitted the current Issue into a separate disposable Noodle control root.
Noodle launched the real local Codex 0.153.4 worker from clean candidate
`5a5229c3a92d3a0183dce9b9f7bf46f072943f4a`. This did not resume Issue 18.
The 180-second bounded drive reached review after 73.31 seconds; the worker itself
ran for approximately 47 seconds. Its single Agent-produced typed outcome was
`blocked`, matching order `soodles-39`, stage 0 and the actual Noodle session.
That expected handoff is not a runtime failure or an Issue completion.

- Noodle session: `soodles-39-0-execute-20260916-192945-2432f9`.
- Native thread: `01a0abb2-5644-7763-bf4a-5f49de416b41`.
- Native turn: `01a0abb2-56c7-7463-98eb-5933a6f21877`.
- CLI capture: one thread start, one turn start/completion, five paired shell
  commands and one paired GitHub Issue read. The marker command exited 0 and
  printed `SOODLES39_NATIVE_CAPTURE_V1`; the Agent then emitted the typed outcome.
- A read-only App Server `thread/read` returned that completed turn. Its exact
  native rollout has matching session metadata and turn context with
  `model=gpt-6-astra`, `effort=high`. No model turn was started by this readback.

This proves the harness's persisted model selection for that turn. It does not
prove hidden service model versions or unexposed rerouting. `thread.model` and the
launch model argument alone were not accepted as turn evidence. The CLI emitted
a hook-timeout-clamping warning item; it is preserved in the raw audit.

## Fixed gate and remaining gap

The fixed observer returned `INCOMPLETE`, with only
`successful_process_exit` missing and no violations. Noodle persisted the
attempt's exit code as `null`. The recorder captured loop exit 0, native turn
completion and exited metadata, but did not persist the actual OS exit status of
the Codex child. Neither the marker's exit 0 nor the loop/readback process exit 0
can fill this field. The packet therefore supplies `exit_code: null`.

Full local baseline/treatment cases are **NOT_RUN**. There was no unchanged retry,
no relabeling of cloud records and no landing authorization. Before a new probe,
the external recorder must wait for the actual Soodles worker/Codex child and
persist its real exit status outside the task. Bind that changed recorder to a
new prospective observation; retain this result. This is a recorder gap, not
proof that Codex failed or that a model turn never ran.

## Controls and cleanup

Nine unittest methods pass. Four pre-run planted discriminator defects—missing
native model requirement, missing thread binding, omitted tool-result matching,
and omitted model match—each made the same control RED; restoration and legal
non-cases were GREEN. A first weak tool-result mutation control was strengthened
before the live run; its original failure logs are retained. These mutations do
not prove a defect in the baseline instructions.

After the live run, an added test verifies unknown/nonzero/signal exit statuses
stay incomplete. Removing the existing exit requirement makes that same control
RED; restoration and valid/legal non-cases are GREEN. The live judge's executable
bytes were not changed. Correct refusal of incomplete evidence is GREEN control
behavior even though the observed task remains INCOMPLETE.

Noodle removed the clean disposable worker worktree without force or merge.
The loop, scheduler, worker and read-only App Server PIDs/process groups were
observed absent. This fixture cleanup does not resolve production Issue 39.
The implementation remains on draft PR 40; final-head runtime acceptance is
separate from these experimental controls and cannot authorize landing.
