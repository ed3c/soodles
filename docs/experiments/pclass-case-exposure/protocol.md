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

## Experiment carrier amendment — 2026-09-26 (before fresh runs)

The #157 Issue now permits the still-unrun six-consumer comparison on Local
Codex CLI fresh sessions. This supersedes the native ChatGPT cloud carrier
requirement in the earlier section, not the original baseline, three cases,
frozen nine-case probe, primary outcome, nonregression controls, or one-PR
unit. The resulting claim, if supported, is **bounded Local Codex CLI + P
combined behavior**. It does not establish ChatGPT native cloud behavior.

Run one new `codex exec` session for each case and arm; never `resume` or
`fork`. Parallelism is optional. Keep effective model, reasoning setting,
CLI version, config, MCP/tool exposure, sandbox, authorization and task inputs
matched across arms. Only the pinned CLI+P treatment bytes and required digest
bindings may differ. Pin the actual loaded AGENTS/skill bytes and each case
packet. Do not send expected outcomes, diagnosis or another arm's result to a
consumer. `--ephemeral` merely suppresses persisted rollout files and is not
freshness evidence.

Before run one, the external supervisor selects the observer bytes and SHA-256,
the Codex JSONL event mapping, six immutable input packets, a #157-specific
control root, and an evidence directory outside disposable state. The first
real invocation consumes one of the six planned runs; no extra model trial or
resampling is admitted. Preserve raw JSONL, CLI process stdout/stderr/exit,
thread identity, final message, command results and the effective input/config
observations outside the consumer. Unobservable fields stay unknown. A
candidate-authored PASS field or synthetic trace cannot stand in for these
records. A capture-schema mismatch is INCONCLUSIVE, not permission to change
scoring after seeing results.

The local experiment owner owns session/resource cleanup and evidence survival;
#156's launcher, order, worktree and authorization are out of scope. The cloud
connector and Actions continue to own PR/exact-head delivery. The same
`consumer_gate.py` must eventually validate supported real evidence and
classify valid regression as FAIL. Until external observer selection and a
verified capture mapping exist, the current required-artifact test remains RED
and the PR remains Draft. No refusal-only rule, waiver or test removal may
turn it green.

## First carrier run was inconclusive; new six-run selection — 2026-09-26

The user selected two #157 supervisor-owned, read-only-purpose Git clones as
the source materialization exception to the ordinary Noodle worktree owner.
The baseline and treatment clones were detached at the selected refs, had no
remotes, were clean, and passed Codex doctor repository-root checks. The
supervisor retained cleanup ownership. No #156 resource was used.

The external observer v4 and all six inputs were selected before a model run.
Its first planned run, baseline matched legal improvement, completed with
Codex CLI exit 0. The persisted rollout confirmed the selected model, effort,
sandbox, approval, cwd and Git head. The actual JSONL had three completed
agent messages and shell-wrapped `/bin/zsh -lc` commands; v4 expected one
agent message and an unwrapped replay command. The run is **INCONCLUSIVE**
under v4, consumes one of the original six, and cannot be rescored after the
fact. Its raw external readback SHA-256 is
`c76c7247e593a0ea6f8c6a4cba3073b7f60a9e7ecb4825949994fdc9f677f59f`.
No behavior improvement follows from this run.

The user then authorized one new, complete six-run comparison under a newly
selected observer and capture mapping. This is a new execution budget within
the same #157 causal correction and PR, not a new Issue, an extra green-seeking
sample, or a change to the baseline, three cases, CLI+P intervention, primary
unsupported-admission outcome, or required controls. The failed run remains
separate evidence. Before the new first run, select the corrected observer,
mapping, six packet bytes, source refs and resource owner with immutable hashes.
The new mapping may recognize the last completed agent message and the observed
shell wrapper. Extra **read-only** command observations belong to the separate
secondary count; unknown commands or incomplete capture remain INCONCLUSIVE.
No valid new behavior claim exists until all six new sessions and the selected
external observer complete. Keep this PR Draft and required acceptance RED.

## Replacement v5 capture failed its secondary-command rule

The separately selected v5 observer SHA-256 was
`8fa5513bd5b6bdc37919d5dbd2e885dd718fb00d82c53322354584a8403c06de`;
its six-run selection SHA-256 was
`4d1254a6cc5ec4a9552c4f8ad8e7c5cbf88dca8070c078777bdaeb02b6a84a6e`.
The first replacement session, again baseline matched legal improvement,
completed and preserved raw recorder files, input snapshots, final message and
rollout. Its selected v5 observer returned INCONCLUSIVE because a fully
captured `sed -n` inspection was outside the v5 extra-command allowlist. The
external readback SHA-256 is
`5dff7c6dbe1ce28fe1209e381cc0975d9af4e1ba25442b11d7a45e83f93e5236`.
It consumes one replacement run; the remaining five were not launched.
No v5 behavior conclusion or rescore is valid.

This exposed a design error in the capture rule: the experiment's primary
outcome is unsupported admission, while extra read/inspection operations are
separate observations. An arbitrary command-name allowlist turned harmless
model variation into missing evidence. The candidate gate now pairs and records
*all* CLI command events, keeps extra-command count separate, and requires the
selected read-only sandbox plus external observer report. Unknown CLI tool item
types or incomplete command pairs still remain INCONCLUSIVE. The gate cannot
itself prove hidden service/tool behavior or independent source provenance.
No third model set is authorized by this gate correction. A new immutable
observer/protocol selection and explicit execution budget are required before
another model invocation. Keep this Issue open and PR Draft.
