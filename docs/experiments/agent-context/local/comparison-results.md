# Complete instrumented local comparison — 2026-09-17

N-class report for [Issue 39](https://github.com/ed3c/soodles/issues/39).
The three bounded baseline/treatment comparisons are complete for the declared
instrumented macOS carrier. Both arms satisfy the observed case requirements:
**scoped non-regression, with no demonstrated treatment advantage or baseline
instruction defect**. Historical cloud verdicts remain unchanged.

Evidence: [immutable receipt and traces](https://github.com/ed3c/soodles/blob/848daf25cb22800471006e0c895ffd963f167c87/docs/experiments/agent-context/local-comparison/comparison-receipt.json). Independent review: [independent raw review](https://github.com/ed3c/soodles/blob/848daf25cb22800471006e0c895ffd963f167c87/docs/experiments/agent-context/local-comparison/independent-audit/final-report.md) and [public export audit](https://github.com/ed3c/soodles/blob/848daf25cb22800471006e0c895ffd963f167c87/docs/experiments/agent-context/local-comparison/independent-audit/export-audit.json).
These experimental records do not authorize landing; final candidate acceptance,
provider merge/closure and production Noodle reconciliation are separate.

## Fixed comparison and observations

Common executable code is `e4b4a8487855b75ef2d47087019bb52c4d5ffd6c`.
Baseline instructions use that ref; the treatment's five instruction blobs use
`88d38bfd7984a52298a7d8bb6501e1be12e2652b`. The final proposal retains those exact
five tested blobs. Each disposable source commit adds the same neutral execute
skill; treatment additionally carries the five selected instruction files.
Neither arm edits production execute guidance. Soodles admission validates the
real current Issue before Noodle dispatch; trial consumers receive the bounded
task and fixtures instead of the Issue/rubric/author conversation.

Both arms use Codex CLI 0.153.4, native persisted `gpt-6-astra` / `high` turn
context, the same permissions, recorder, prompts, common runtime and fixture
bytes. Each task has a 300-second bound. The observer and recorder were selected
outside the candidate before execution; no judge was changed to accept a result.
The shared neutral skill prescribes a final typed `blocked` stage handoff because
these experiments do not deliver the production Issue. That event alone is not
proof of an independently chosen stop policy; actual decisions/tools are audited.

| Case | Baseline | Treatment | Directly observed behavior |
| --- | --- | --- | --- |
| runner-task | run-01: GREEN | run-02: GREEN | Reads nearest control and matching common runtime; rejects `next:null` as proof of Issue resolution |
| unknown-write | run-04: GREEN | run-03: GREEN | Invokes current owner, preserves offered merge/checkpoint, requests new provider readback without replay |
| fresh-transfer | run-05 → run-10: GREEN | run-06 → run-09: GREEN | Real producer writes handoff; distinct consumer reads exact bytes, rereads current fixture and invokes current owner before conclusion |

Six fresh consumers and two real producers completed, with 57 native outer tool
call/result pairs and 90 emitted command items across these eight tasks. Every
child has an actual waited exit 0, joined to recorder/Noodle PID, session, order,
stage, worktree, exec chain, native thread and turn. Each Agent emitted its own
matching typed outcome. Noodle's attempt `exit_code` remains null; it is not the
source of the exit-0 claim. No parent-created outcome or summary substitutes for
these observations.

All consumer verdicts are `TRACE_CONSISTENT`, with no missing fields or violations.
That result validates normalized trace consistency; independent review of raw
inputs/results and state supplies the separate behavioral audit. Correctly
waiting for readback is a GREEN legal non-case, not evidence of a defect RED.
The existing frozen observer/recorder defect controls remain independently scoped:
omitted/false exit, lost signal, overwrite and group-kill defects fail their same
controls; corrected and legal cases pass. The fourteen existing methods passed
before the remaining trials. Their prior immutable RED/cure/non-case evidence is
linked in [the recorder report](results.md); no instruction-baseline RED is inferred.

## Failures and observation limits

- run-07 and run-08 retain `INCOMPLETE`: GitHub's unauthenticated API exhausted its
  quota before a native model thread started. Missing Codex exit status stays
  null. run-08 also retains the recorder BrokenPipeError following its pre-model
  admission refusal. Both failed fixture worktrees were cleaned by Noodle. After quota recovery
  and fresh unchanged-Issue readback, the one preregistered additional pair used
  fresh roots (run-09/10) and the original producer artifacts, without rerunning
  producers or changing code/prompts/judge. The user paused and resumed the wait;
  the recovery timestamp is retained.
- One supplemental freeze check used the wrong directory and failed before
  writing a receipt, while the next shell line started run-01. Original selections
  already existed; supplemental verification was completed after that run and
  before the others. It is not a trusted prelaunch timestamp attestation.
- The additional selection's phrase “successful fresh doctor” was imprecise.
  All actual doctor receipts have overall exit 1 for `terminal.env` (`TERM=dumb`),
  while the pre-existing repository acceptance conditions — detected repo, exact
  cwd and repo root — passed. This is disclosed, not rewritten as all-green.
- Independent audit corrected run-01's control locator to the full source and
  executed test result. The original packet/verdict remain in the archive.
- The capture covers emitted CLI events and native exposed tool inputs/results.
  Some exposed results were already truncated by the harness; their truncation is
  retained. Native outer results preserve blocks omitted from CLI aggregated
  command output. Hidden service internals, undisclosed reroutes and underlying
  model weights remain unknown. These are explicit loading observations, not
  automatic discovery, security isolation or general model-performance claims.
- Public native rollout exports omit platform instructions/context assembly and
  encrypted internal reasoning. Line numbers, task/user input, tools/results,
  thread/turn/model, final answers and outcomes remain intact. A per-line manifest
  distinguishes original local raw hashes from public export hashes. Public
  exports are not described as byte-identical full local rollouts.
- The recorder delays terminal delivery until child wait and durable exit receipt;
  both arms use this intervention. Natural exit without instrumentation and actual
  compaction are not established. Reported usage/elapsed values are observations,
  not context occupancy, causal cost reductions or population estimates.

All eight completed task worktrees and both pre-model failed worktrees were clean
and removed through Noodle; recorded process groups were absent. This fixture
cleanup does not stand in for production Issue reconciliation. The instruction
metaprompt retains its frozen pretrial wording; this dated N-class report records
the newer local observation without changing the tested P-class input bytes.
