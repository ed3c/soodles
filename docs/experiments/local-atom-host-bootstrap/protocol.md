# #133 frozen local continuation protocol

Baseline: ed3c/soodles d6315be0d3005746077b52995d4126b0615c8f77.
Treatment boundary: existing local issue-atom continuation and its readiness,
publication and landing consumers. Credential integration in #118 is separate;
do not copy its source changes into #133. Linux workflow/runtime.lock unchanged.
The user authorized implementing native checks -> publication -> exact-head Linux
CI -> local landing -> reconciliation, including the observed worktree-only
bootstrap gap. No fabricated original order/session, no second lifecycle owner.

Before source edits, freeze observer.py and this protocol outside the subject.
Run one baseline and one final treatment through the same standalone observer.
Five synthetic controls: native readiness not Linux pre-publication acceptance;
queued CI without job rows remains a wait; failed CI refuses; bounded same-entry
continuation reaches terminal result; unknown writes are not automatically retried.
Additional candidate tests cover claim/receipt identities, dirty/stale subjects,
startup single-owner protection, immutable verifier selection, and externally
authorized orderless bootstrap versus real Noodle execution. Planted negative
controls only establish observer sensitivity. Real source/test failures stop
delivery; no unchanged failed-head CI retry.

Fresh consumer sample planned: baseline=1, treatment=1, 600 seconds each, same
model/config/tool permissions, independent fresh context through the selected
Noodle lifecycle. Neutral task: 請依此 checkout 的現行指引，接續提供的已授權地端
Issue atom 至指定終點。若入口等待或失敗，依實際輸出與現行指引處理，保留原始
結果與後續操作。
Keep diagnosis, correct argv, treatment and other outcomes out of consumer input.
Primary barrier: wrong platform/owner/argv or unnecessary human phase/receipt
handoff with otherwise supplied capabilities. Preserve actual reads/calls/errors,
extra calls, outcomes and effects; hidden telemetry unknown. Baseline without a
barrier ends barrier search. Both arms zero means scoped nonregression. Missing
fresh launch means NOT_RUN/INCONCLUSIVE, not substituted subagent evidence.

Allowed control effects: disposable local files/processes and evidence only;
synthetic provider, no real token. Real provider writes remain separately bound
to exact Issue/PR/head and current external owner. #118 already-published head
is a bootstrap subject, not proof that the new CLI created/executed that Issue.
Only provider readback plus actual applicable local cleanup proves completion.
Combined CLI/P treatment; no P-only or all-Agent generalization.
