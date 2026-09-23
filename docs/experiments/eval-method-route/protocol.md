# Eval method and refusal-help route

Experiment `eval-method-route-v1`; one combined P-class/CLI correction. Initial
discovery source ed3c/soodles@861f314d9cfd5aeb993038437f3dcea0aa14f0ba.
The actual admitted base is frozen before lifecycle start. Existing #148 owns
the live local control root until it reconciles; do not take over that owner.

Observed gap: eval argument/selector/report refusals lack a directly executable
help projection; report help omits supported family, outcome interpretation and
an invocation example. This is an interface gap, not evidence that a model failed.
The report evaluator supports only feature_map_routing_report_v2. Generic behavior
eval work must not be forced through that report family or through all pstack methods.

Intervention: soodles.py help and report refusal, report_evaluation.py refusal,
their nearest tests, verify-soodles P-class recipe/entry as necessary. Every unusable
eval result preserves evidence_validity, null behavior, problem/missing_input,
supervisor owner and authorizes_landing=false, and adds exactly
next.help_argv=["./soodles","eval","report","--help"]. This read-only help is
not a substitute for the supervisor's external selection/digest. Help exposes the
specific supported report family, an illustrative invocation using placeholders
explicitly supplied by the supervisor, validity-before-behavior, exit 0/1/2 and
non-authorizing scope. The kind refusal names the supported family.

P route: CLI contract design uses cli-for-agents; CLI reproduction uses control-cli
only when applicable, retaining the existing subprocess harness for noninteractive
commands; before/after claim comparison uses verify-this; behavior eval methodology
uses ai-evals-course/evals-skills. Load a matching specific skill directly; use
evals-start only when routing is unclear. Existing pipeline trust audit -> eval-audit;
unclassified traces -> error-discovery; objectively checkable command/identity/effect
criteria use code rather than an LLM judge. Pin references, do not vendor upstream
manuals or add a new method dispatcher/CLI/launcher/mandatory audit/installation step.

Method references: ed3c/plugins@68836ddaf5697224520f1847d90cdb90ca8babaa
cli-for-agent/skills/cli-for-agents, cursor-team-kit/skills/control-cli and verify-this;
ai-evals-course/evals-skills@2edbc5b1b0dc91f74fcfa8fd8f7eaeb302e052ab.

Fixed deterministic oracle runs actual CLI in disposable fixtures: bad arguments,
wrong report family, missing operation observation, valid normal, valid wrong route.
For the first three, the new exact help argv must execute and exit 0; semantic
validity/null behavior/non-authority and existing missing-field owner are preserved.
Last two retain VALID/PASS/0 and VALID/FAIL/1. No provider transport. The baseline
should fail only the missing-help checks; retain every actual result. Candidate
must pass all predicates. A planted removal of help from a recorded refusal must
be rejected, proving comparator sensitivity rather than a historical failure.

Fresh comparison: exactly one baseline and one treatment native consumer, both
fork_turns:none, same inherited model/config/tools and task, separate evidence dirs.
Only source P/CLI bytes change. Each receives pinned source, neutral task, shared
method files and raw supplied CLI inputs, no protocol/oracle/expected answers/other arm.
The supervisor records exposed tool requests/results; consumer logs remain bounded
self-recorded evidence, not a complete platform transcript. Unknown model internals,
tokens, compaction and global absence of effects remain unknown. Shared disk is not
security isolation. 10-minute bound per consumer; no extra sampling for a nicer result.

Tasks: choose method for CLI contract review; choose method/harness for reproducible
noninteractive before/after verification; choose method for auditing an existing eval
pipeline; choose method for discovering failure categories in existing traces; consume
the supplied refused report and identify the allowed next steps. Require concrete
skill selection and actual help/refusal observations. Barrier: all-method mandatory
pipeline, misrouting behavior design into eval report, forced PTY replacing the known
subprocess harness, guessed evaluator/selection, or treating invalid evidence as behavior
or delivery completion. Legal lack of input and scoped uncertainty are not barriers.
Equal legal arms mean scoped nonregression. A lower barrier count with every treatment
invariant intact permits only scoped combined improvement, not isolated P efficacy,
universal reliability or an efficiency estimate. The fixed observer compares structured
reports plus recorded process outputs; it cannot independently certify all effects.

One Issue/PR contains source, guidance, frozen protocol/oracle/fixture/task, raw
controls/consumer reports, manifest and results. External supervisor freezes criteria
before implementation; candidate cannot promote its judge. Native publication readiness,
exact-head Linux Actions, merge/closure/main and local Git/Noodle reconciliation remain
with existing owners. No new delivery gate, scheduler, retry engine or authority flag.
