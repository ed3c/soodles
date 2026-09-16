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
