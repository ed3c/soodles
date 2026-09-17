# Integrated local comparison — 2026-09-17

N-class report for [Issue 39](https://github.com/ed3c/soodles/issues/39).
The current comparison uses main `1ff2882891792b50d97529c9ee1a3e76eac1a6e7`
and the five frozen treatment instruction blobs at
`388c86be5eef0f317b0ae38ffac70892f24c13de`, preserving #41/#44/#46.
It supersedes the historical input selection below, not its recorded results.

[Immutable comparison receipt](https://github.com/ed3c/soodles/blob/9234046455c158180f25f6bd3c2dd2607de440ac/docs/experiments/agent-context/local-comparison/comparison-receipt.json)
and [independent raw/export review](https://github.com/ed3c/soodles/blob/9234046455c158180f25f6bd3c2dd2607de440ac/docs/experiments/agent-context/local-comparison/independent-audit/final-audit.json)
retain the inputs, original-local hashes, public exports, failures and cleanup.
Supported conclusion: **scoped non-regression; no demonstrated treatment
advantage, lower decision cost, or baseline instruction defect**.

| Matched case | Baseline | Treatment | Observed result |
| --- | --- | --- | --- |
| runner-task | run-01 | run-02 | Both read the nearest control and exact common runtime, then reject `next:null` as resolution evidence |
| unknown-write, sole supplemental pair | run-09 | run-10 | Both local owners reject dispatch of an already offered merge, preserve actual supplied checkpoint bytes, and require fresh provider readback; no transport request is emitted |
| fresh-transfer | run-05 producer → run-08 | run-06 producer → run-07 | Distinct native consumer reads the actual producer artifact, then its current provider/checkpoint and current owner before concluding |

All ten bounded worker tasks, including the original incomplete pair, have
actual child wait exit 0 and own matching typed blocked outcomes. The neutral
execute skill prescribes blocked because experiments do not deliver production;
it is not independent evidence of the Agent choosing its own stop policy.
The ten tasks contain 70 native outer tool request/result pairs and 100 emitted
command results. These counts exclude Noodle scheduling, setup, observer and
coordinator work, and are not a measurement of hidden reasoning or decision cost.
Nested owner refusals can have exit 1 while the containing observation command
succeeds. Correctly refusing an illegal dispatch is rejection-control GREEN;
it does not establish a defect RED or an optimal Agent route.

The frozen observer checks normalized consistency only. Its unchanged fourteen
controls passed, as did six existing context-recorder controls. Independent raw
review separately validates actual operations and joins Noodle session/order/stage,
worktree, recorder PID/child wait, Codex thread/turn and exposed model identity.
Prior recorder defect RED/cure GREEN/legal non-case GREEN evidence remains scoped
and linked in [the historical recorder report](results.md). No new product gate
or production runtime implementation is introduced by this documentation atom.

## Preserved gaps and deviations

- Original unknown-write run-03 invoked the owner on a temporary copy and measured
  only semantic equality of that operated copy. The inbox bytes were preserved,
  but that did not prove the operated copy's after bytes. Independent raw verdict
  is **INCOMPLETE**; corrected normalization has a missing after digest and the
  fixed judge rejects `checkpoint_preserved`. Initial misleading green
  normalization remains archived. The original baseline run-04 remains recorded.
  The one contract-permitted additional pair was selected before launch, adding
  the same narrow path/hash observation instruction to both arms. No more trials
  were used to select a favorable outcome.
- The Issue prefix named PR48 run 35200315530; the actual prelaunch frozen packet
  used successful exact-main run **35200528246**, head `1ff2882`, attempt 1.
  This provenance wording deviation remains explicit:
  **unqualified_preregistration_compliance=false**. Fixtures were rebound before
  any model launch to the current runtime verifier digest; historical fixture
  requests remain non-null and are never sent to GitHub.
- All doctor receipts preserve overall exit 1 for `TERM=dumb`; the exact detected
  repository/cwd/root usability predicate passed. No all-green doctor claim.
- Initial cleanup recorded a permission-denied process check and ordinary Noodle
  refusal to delete unmerged experimental commits. After fresh absent-process
  readback, the coordinator used the owner's explicit `--force` only for clean
  duplicate fixture worktrees whose exact commits remained in separate control
  checkouts. The post-run cleanup adapter change and original failures are saved.
- Raw source/tool truncations, run-01's failed source search, run-05's schema web
  cache miss and scheduler cache-permission refusals remain. CLI aggregated
  output sometimes omitted stdout that native tool result blocks preserved.
  One run-08 normalized source locator was corrected by independent review;
  initial packet/verdict remain. These are not erased from the error inventory.
- App tokens are supplied through the managed entry, scoped to soodles/issues:read,
  held in memory and revoked (204). There is no anonymous REST fallback in the
  experimental admission reader. This does not claim all repository workflows
  or historical cloud runs avoid unauthenticated public endpoints.
- Public native exports omit platform instructions/context assembly and internal
  reasoning, preserving line numbers and all task/tool/result/model/exit records.
  Original local raw files remain unchanged. Some harness-exposed results were
  already truncated; full hidden service activity cannot be reconstructed.
- Observed model is native `gpt-6-astra`/high under Codex CLI 0.153.4 and the measured
  macOS Noodle ca81f942 carrier. Hidden model revision, undisclosed reroutes,
  automatic instruction discovery, actual compaction and uninstrumented natural
  exit remain unproven. The fixed recorder holds terminal delivery until wait;
  both arms share this intervention. Local evidence cannot relabel cloud evidence.

## Production identity and delivery boundary

The real original `soodles-39` order was admitted before integration authoring.
Session `soodles-39-0-execute-20260917-084802-fa146c` produced complete external
drafts and its own scoped completed outcome; the external recorder waited for the
actual child. Noodle automatically removed its no-change checkout. The supervisor
then explicitly asked Noodle to recreate the same worktree from admitted main
and applied those drafts. This is recorded reconstruction, not fabricated
uninterrupted checkout or retrospectively created order history.

The ten experimental worktrees are removed and their source/evidence retained.
Experimental cleanup is distinct from production reconciliation. The original
immutable publisher at `e4b4a8487855b75ef2d47087019bb52c4d5ffd6c` remains selected;
its digest is `8eae793df0eac64cd78de0a41bccd08dafd53a590cf7917a398965c9fb26402a`.
The final candidate must retain all five tested instruction blobs, pass exact-head
canonical Actions acceptance, then proceed through [PR43](https://github.com/ed3c/soodles/pull/43)
merge readback, Issue closure readback and original-order reconciliation.
Only that external terminal receipt establishes RESOLVED; this report does not.

---

## Historical comparison with earlier instruction inputs

The following report is preserved for its original source/carrier only.

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
`88d38bfd7984a52298a7d8bb6501e1be12e2652b`. Candidate `58916aba4725d409cec2c57843f3cccfc89e011d` retains those exact
five tested blobs. The later integration of main #41 changes AGENTS/Skill inputs
and requires a fresh bounded comparison before its delivery; this archive does
not verify the integrated instruction bytes. Each disposable source commit adds the same neutral execute
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
