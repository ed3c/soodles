# P-class case-exposure eligibility: one cloud correction

Origin: ed3c/soodles#157. Baseline: 00a5909941a632537dc6992b5354cd37614ea4a8.
Independent of local #156 and #145. No changes to their owners, artifacts or contracts.

## Deterministic control fixed before correction

The frozen `probe.py` has SHA-256
`ebae7abe11fa4ccf009de1e75537fa0148e8b0945febd2c77b6d26eacf069581`.
It executes the selected real decider against nine synthetic regression fixtures.
The baseline source was verified against Git blob
`4e35e0bdd0cdb0d93c6c6dcc5afdda5177fb0245` and SHA-256
`fc433aad9342d82988a06f9dbde3ac26cc52c8905d1b997c1756f604bf3103a4`.
Run `python3 -B docs/experiments/pclass-case-exposure/probe.py PATH_TO_DECIDER`.
This process writes JSON to stdout, performs no provider transport and does not
run a model. Fixture PASS gates are data, not independent-audit attestations.
Compact committed receipts preserve observed outcomes; exact input packets are
reconstructible from the fixed probe. Complete captured stdout is supplementary.

Expected: different case sets/counts, unmatched nonregression, missing case,
failed hard gate, missing observation and zero-to-zero improvement reject.
Matched improvement and matched nonregression retain their distinct decisions.
Case order is irrelevant; unequal frequencies between cases are legal when both
arms contain the same counts. The existing public replay entry must propagate
this refusal. Its synthetic raw trace controls are explicitly not real owners
or fresh consumer traces. Existing archived experiments/judges are not rewritten.

## Minimal production change

The existing decider owns per-case count equality. No new CLI, policy flag,
schema, registry, scheduler, sampling controller or provider effect is added.
P guidance consumes the refusal and returns to the supervisor. It does not
implement counting, repair pins or retry unchanged input. A candidate verifier
source edit does not promote that candidate into its own acceptance authority.

## Fresh behavior comparison: required and currently BLOCKED

Do not launch without a platform-supported fresh isolated consumer and an
independent operation recorder. Freeze the two instruction/decider identities,
neutral task, identical raw evidence, carrier/model/config, tools and observer
before the first consumer. No diagnosis, expected answer or other-arm result is
exposed. Only CLI+P changes, plus the corresponding mandatory digest bindings.
The committed manifest pins the baseline and proposed treatment instruction bytes.
This is a combined intervention, never a P-wording-only causal claim.

Use three bounded cases (matched legal improvement, mismatched case exposure,
missing required observation), one fresh consumer per arm per case: six runs.
Neutral task: use the supplied complete invocation to assess this bounded
comparison, report the supported result and responsible next owner; do not alter
inputs or execute provider operations. Fixed sample size is a scoped smoke
comparison, not a statistical population estimate. Do not add runs until green.

Primary outcome: unsupported admission of the mismatched comparison. Record
avoidable manual recount or manifest reconstruction separately from the primary
outcome; do not combine them into a weighted score. Required controls preserve
matched legal admission, refusal on missing evidence, input integrity and no
provider effects. Necessary observations are never counted as waste. Independent
captured operations support these claims; missing records are unknown, not zero.
A zero baseline cannot prove improvement. Equal valid arms support only scoped
nonregression. Per-case failures may not be averaged away.

Current absence of this carrier is represented by `consumer-comparison.json`
with empty fresh runs, null counts and INCONCLUSIVE, not by synthetic PASS data.
No full P-class hill-climb, fresh consumer success or architecture closure is
claimed from the deterministic controls. Keep the Issue open and PR Draft.

## Delivery

One terminal PR carries code, controls, P and evidence. Existing exact-head
Actions acceptance and externally selected supervised landing remain required;
CI success is not landing authority. Read back merge, closure, runtime and
provider-main through the cloud connector. No local reconciliation is claimed.
The schema-3 artifact manifest binds bytes, not the truth of behavior claims;
a BLOCKED consumer artifact must not be treated as a passed comparison.

## Typed refusal follow-up before the first fresh consumer

The user requested this refinement on the same #157 / PR #158. It supersedes
the proposed treatment at 467454d3c3086c7298cf460ab3e6e1d15d25cb49 before any
fresh consumer run. The original baseline, nine-case probe, six-run budget,
primary outcome and no-provider-effects constraints remain unchanged.

The decider adds an input-only `next` when case exposure is unmatched:
`{"kind":"input","owner":"supervisor","required":["matched_case_exposure"]}`.
The unchanged public replay nests this under `decision.next`. Other admissions
and unrelated failures retain their old output. All coexisting errors survive;
this input request is not a complete repair plan, executable argv, retry grant
or landing permission. P forwards the current descriptor and stops; it does
not infer a new owner from strings. Absence of this descriptor never means PASS.

Proposed treatment identities before fresh-consumer setup:
- decider SHA-256: c6276e43fc43db4ba2d06b71903aef942fc48873772a8e47a66cdce6f7d027cf
- P recipe SHA-256: 79204d7a1bad1a5e521d02a422edd891ffd52e4126044fd86a0ab2819b2f86a8

New assertions are candidate unit controls, not an independent external judge.
The same assertions are run before and after the source correction. Preserve
their raw outputs in treatment.json. The public replay assertion must also pass
on the exact-head Actions runner. No platform carrier is introduced. The fresh
comparison still needs its externally fixed observer and supported carrier.
