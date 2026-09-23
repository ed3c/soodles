# Shared-owner handoff: one combined correction

Origin: ed3c/soodles#154. Claim: **deterministic correction plus scoped combined nonregression**. Comparison evidence does not authorize landing.

## Actual gap and minimal correction

At baseline 0a28e7f279987e07c6fa548d43838026b8bb5d2d, a new atom encountering a foreign owner refused after one synthetic Issue-create and an admission proposal. Two independently valid authorizations could both enter synthetic Issue-create at the same control root. Existing owner/config bytes were preserved; this is not evidence of historical production overwrite or duplicate writes.

Candidate 0692ac5cb2a141a1ab7e856433ab4bbcad87cddb adds a nonblocking per-root process mutex and validates current Noodle custody before supplier/provider/new checkpoint/proposal. Exact checkpoint, envelope and order projection bind legitimate continuation; matching config alone does not. The existing CLI remains the single entry. Typed input names Noodle or the competing entry owner, confirmed blockers and the same argv. The Skill adds eight operational lines; the system contract records the ownership boundary. There is no Noodle code change, scheduler, queue, durable lease, automatic retry, forced shutdown or new Agent flag.

## Externally fixed controls

The protocol, fixture, CLI driver, concurrent driver and oracle were fixed before formal baseline. No judge bytes changed during implementation. The same eight cases ran on the candidate, all GREEN:

| Case | Baseline | Candidate |
| --- | --- | --- |
| Foreign live owner | Late refusal after synthetic write/proposal | Refused before effects |
| Foreign stopped nonterminal owner | Late refusal after synthetic write/proposal | Refused before effects |
| Prior checkpoint plus foreign owner | Late refusal after synthetic write/proposal | Refused before effects |
| Malformed canonical snapshot | Missing normalized result; desired gate failed | Typed refusal before effects |
| Concurrent entry lock held | Entry not blocked | Typed refusal before effects |
| Idle owner | Legal start boundary | Legal start boundary |
| Exact same owner | Legal running continuation | Legal running continuation |
| Distinct authorizations racing | A and B enter effects | Only A enters effects; B refuses |

All five negative candidate cases observed zero supplier, provider-read, provider-write and start calls, unchanged checkpoint/owner/config, and no proposal. The race retained no B checkpoint. Every disposable fixture was removed. Idle uses a sentinel at the existing start boundary; transport/supplier are synthetic, with real disposable Git and OS locks. Malformed baseline counts are unknown where the driver did not return a normalized result.

The earlier qualification at f4e80d6 is retained separately. Its first same-owner harness lacked the parsed contract required by the existing projection; the corrected harness was frozen before formal baseline. That setup error is not a product failure.

## Fresh observations

Exactly one independent native consumer per arm, fork_turns:none, with the same neutral task, tools/config and requested inherited model. Four exposures per arm: foreign live, foreign stopped, idle and same owner. Source and instruction digests were frozen before treatment. Actual unexposed model metadata, tokens and full native transcript remain unknown.

Observed consumer barrier exposures were **0/4 baseline and 0/4 treatment**. Both consumers respected valid refusal, preserved unknown continuation boundaries, did not retry and did not claim delivery completion. Treatment identifies the precise Noodle blocker in the owner output. This supports scoped combined nonregression, not reduced Agent error rate, general behavioral improvement or a P-only causal claim. No extra sampling was performed. Subprocess time is report-only in raw/consumer-runs.json.

Recorder requests/results/stdout/stderr bind the executed subprocesses and instruction reads; consumer action rationale and extra-action counters remain self-report. The supervision does not claim full platform trace completeness. Repository projections replace host home and per-user temporary prefixes with /HOST_HOME and /HOST_TMP. Each bundled item records both original and projected hashes; original bytes remain in external custody. Credentials and host registration identities are excluded.

## Validation and delivery boundary

Final source passed focused **33 tests** and full **367 tests**, zero skips. Additional controls preserve invalid-authorization precedence, matching-config foreign refusal, malformed dispatch refusal, historical resolved readback and original projected-order cleanup. Exact test receipts and source review are embedded in raw/selection.json. An initial focused process received SIGTERM; a subsequent new-test assertion expected the wrong existing refusal field and was corrected. These receipts are retained; later source-complete runs passed. Frozen fixture.py retains its pre-existing EOF blank line unchanged.

The worktree doctor detected the exact repository/cwd/root; its overall noninteractive result failed on TERM=dumb and reported a historical rollout warning. No model session was launched for doctor. These native checks do not replace Linux runtime-lock acceptance.

At packet assembly, delivery is pending. The original Noodle writer must apply only the evidence patch, rerun final tests and emit its own typed outcome. Native readiness, one PR, exact-head Linux Actions acceptance, the independently pinned external landing owner, provider merge/closure and Git/Noodle reconciliation remain required. Terminal receipts belong to that lifecycle after this packet is committed. The gate does not certify full parallel Issue delivery, out-of-band Noodle starts or general side-effect isolation.
