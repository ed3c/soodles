# #133 implementation checkpoint — not delivery acceptance

Status: IN_PROGRESS. The one fixed fresh pair observed a scoped CLI-induced
continuation barrier in baseline and none in treatment. Combined CLI/P only;
no #133 provider merge/closure or local terminal receipt is claimed.

## Fresh local pair — CI queue continuation only

Exactly one independent Noodle/Codex consumer per arm ran the frozen neutral
task, with a disposable already-published CI-phase subject. Its exact-head run
was queued with no jobs yet. The fixture supplied provider transport only;
subject authorization, route, refusal and waiting logic were not patched.
It did not inject a wrong argv or tell either consumer the expected result.
The synthetic checkpoint is not proof of prior live execution/publication.

| Observation | Baseline | Treatment |
| --- | --- | --- |
| Exact subject revision | d6315be0d3005746077b52995d4126b0615c8f77 | c4fc909b21225748b097e19d3795959a0ddce292 |
| Fresh execution session | soodles-118-0-execute-20260922-081533-a173fe | soodles-118-0-execute-20260922-081814-0b1a1e |
| Issue-atom invocations | 1 | 1 |
| Entry exit | 1 | 0 |
| Entry result | refused: github.workflow_job.count=0 | pending: GitHub Actions, wait_exhausted=true |
| Unnecessary external-input handoff | 1: one_exact_runtime_job | 0: await material state change, same entry |
| Wrong atom argv / wrong consumer owner / requested execution envelope | 0 / 0 / 0 | 0 / 0 / 0 |
| Observed completed shell commands | 15 | 19 |
| Ancillary failed source-search commands | 1 | 1 |
| Fixture provider reads | 4 | 236 |
| Whole carrier observation seconds | 172.968 | 396.864 |
| Subject checkout changes | none | none |

Both consumers correctly obeyed their current owner's output. The baseline
barrier is the CLI-induced unnecessary request for an external job while CI is
normally queued, not a consumer's bad argv or failure to obey a refusal.
Classification: baseline OBSERVED_BARRIER; treatment NO_OBSERVED_BARRIER in
this bounded case. This supports scoped combined CLI/P continuation improvement,
not P-only causality, statistical generalization, or lower total execution cost.
Treatment made more calls and took longer while observing the bounded wait.
No additional samples will be drawn from this comparison.

Both consumers visibly read assigned AGENTS.md and the bounded execution recipe.
Neither visibly read the issue-atom skill; the same-host supervisor clarification
must not be credited with the improvement. Their common neutral execute skill
contained no diagnosis or correct Issue-atom argv. Baseline used its valid
schema-1 authorization and treatment its valid schema-2 authorization; both
passed their own executable validators before either consumer launched.
The common carrier was separate from each unmodified subject checkout. Its
fixture Issue118/order identity is not a live #118 operation or the experiment
owner (#133). No production state was synthesized.

Both requested gpt-6-astra/high with the same measured Codex 0.153.4, native
Noodle and normalized flags/permissions. Actual server model provenance and
hidden reads/context/compaction are unknown. Native JSONL preserves observed
commands, output, exits and usage, not a complete kernel or platform transcript.
Raw input/output usage was 335475/2326 versus 660518/3623; these are aggregate
billed counters, not context occupancy or evidence of efficiency improvement.
Both emitted and read back their own typed blocked observation handoff; both
loops exited zero and all recorded process groups were absent before disposable
fixture teardown. Raw records survived outside the removed fixtures.

Raw evidence is at
`/Users/neon/.codex/experiments/soodles133-implementation.8JptD5/fresh133-pair/`.
The predeclared task endpoint, scoring/stop rules, driver/transport digests,
selected inputs, doctors, raw sessions, before/after fixture state and process
readbacks are embedded losslessly in raw.json. The evidence manifest's baseline
instruction hash refers to delivery base b184c43, as its existing schema requires;
raw.json separately binds experimental baseline d6315be. Neither is relabelled.

## Local supervisor clarification

The issue-atom skill and owning contract now clarify that external authority
may be selected by the authorized local Session on the same Mac. No cloud
Session, separate supervisor daemon or token handoff is required. This addresses
the user's observed ambiguity; it is not a fresh consumer improvement result.
Executable code and the frozen observer/protocol remain unchanged.

The local host supplier successfully served the exact read-only CLI
`./soodles github issue ed3c/soodles 133`; the installation token was revoked
(HTTP 204), without an Issue/PR mutation. Raw stdout, stderr, argv, source head
and exit status are preserved outside the checkout at
`/Users/neon/.codex/experiments/soodles133-implementation.8JptD5/local-read133-20260922/`.
`local-capability-selection133.json` in that packet pins control root/main,
native Noodle/Codex identities, explicit worker argv/model and the previously
qualified owner. Existing carrier/producer/owner validators passed without
installing config or starting an owner. Status is
CAPABILITIES_SELECTED_NOT_ADMITTED; a selected model is not an observed run.

Baseline is d6315be0d3005746077b52995d4126b0615c8f77. Noodle created the isolated
`issue-133-local-continuation` worktree from that exact commit. The #118 candidate
122871c8c84e5d69ed1fabc2d99ac4f5feb301bb was subsequently landed through its
explicitly authorized bootstrap; this does not change the frozen baseline.
The frozen protocol and observer copies retain their externally selected bytes.

## Implemented and locally tested

- Native publication readiness replaces the incorrect pre-publication call to
  Linux-only acceptance. It validates clean candidate/claim custody before and
  after checks, records actual platform, binary digest, argv, output and status,
  and cannot authorize landing. Post-publication Linux acceptance is unchanged.
- Queued CI with no job/step is a normal wait. Failed or incomplete completed-run
  evidence refuses. A bounded foreground continuation uses the same entry and
  does not catch/retry refusals.
- Authorization pins an external landing implementation; the candidate cannot
  select itself as the judge. Actual external process evidence is retained.
- Provider publication branch and local Noodle worktree are distinct bindings.
  The new optional branch binding accepts only the existing publisher derivation;
  it does not select an arbitrary branch or alter cleanup identity.
- P instructions state native readiness -> publication -> Linux exact-head CI
  -> external landing. Skill validation is structural, not behavioral evidence.
- The foreground continuation can observe an exact live Noodle order without
  calling stopped-writer takeover or requesting publication prematurely.
  Explicit takeover still refuses a live writer. This is canonical-state
  observation, not proof of process health or permission to restart a dead PID.
- Explicit external bootstrap custody now binds exact subject/Git/native identity
  without fabricating an execution. Thirteen fixture controls reject missing or
  malformed custody, original history, live owner/process, pending proposal,
  changed identity/body/platform, dirty worktree and unknown cleanup repetition.
  A separate disposable fixture completed reconciliation using the selected real
  native Noodle cleanup executable; its provider data were synthetic, not live R.

## Evidence separation

The one frozen baseline observer ran five synthetic controls: one passed,
one failed, three errored (missing continuation and platform/queued-CI defects).
This is designated-input CLI evidence, not a fresh consumer's natural barrier.
The one final treatment observer ran against code candidate
8cd860bd9c6e4f13a634a49406a13f0b8de843ac (tree
e6c43e2363efe4bfe2e39d72a5653812542484a1): all five fixed controls passed.
This is designated-input CLI RED-to-GREEN only. It is not a fresh consumer's
natural decision barrier. Later report-only commits do not change those subject
code or instruction bytes; a changed executable needs a newly identified result.

Full native development tests used an explicit physical TMPDIR in both arms:

| Run | Tests | Result |
| --- | ---: | --- |
| Unmodified baseline | 226 | 3 failures, 1 error |
| Candidate before test-host correction | 245 | Same 3 failures, 1 error |
| Candidate with explicit Linux-host sentinel fixtures | 245 | Passed |
| Candidate with bootstrap custody controls | 258 | Passed |
| After integrating landed #118 dependency | 268 | Passed |
| Canonical live-owner observation correction | 272 | Passed |
| Host producer/start/continuation wiring | 286 | Passed |

The four matching failures are test_admission's binary version, digest and path
controls. Their shell sentinel fixtures formerly inherited the macOS host,
therefore hit the Linux-lock platform refusal before the intended assertion.
The candidate fixes those four fixture platforms explicitly. The unsupported
Darwin-host refusal remains tested; no test is skipped and no production platform
gate changes. This passing native suite is not actual Linux Noodle acceptance.
All raw requests/results and full stdout/stderr remain at the locators in
raw.json, with digests. Earlier failed development runs remain preserved.

## Outstanding — do not publish this as completed

1. Automatic startup/adoption, exact existing-Issue selection and host restoration
   are now implemented and tested, including a disposable real native Noodle
   drive. The live control root still retains its old #39 config; it has not been
   replaced or started for #133. No live original order/session was fabricated.
2. The #118 worktree-only bootstrap is now RESOLVED (details below). It is not
   an original Noodle execution or the new Issue-atom CLI's live completion.
3. User explicitly authorized one external owner qualification. Immutable
   2bbe408 was tested outside the candidate with 75 frozen positive/negative/
   adjacent controls, then selected for #133 only. The verifier digest is
   5c75d37f29732f51962b67cbddf1b2910adfe3524a3a8cda06114726228cd813.
   This removes the prior owner-selection gap, not the remaining acceptance gates.
4. The one fresh pair above is complete for the synthetic CI-queue case only.
   No P-only effect or full fresh end-to-end delivery is claimed.
5. The manifest binds the committed evidence without authorizing landing.
   #133 PR/Linux acceptance, provider verification and local RESOLVED receipt
   remain required. No new Issue was created.

This checkpoint is reversible local work, not a claim of full automation or
terminal acceptance. Preserve the existing owner and unknown-write guards when
continuing the remaining implementation; do not erase these gaps to pass a gate.

## Host continuation control scope

The producer now binds the exact task, immutable runtime bytes, worker/backlog
and native config. Existing-Issue adoption cannot create a replacement on drift.
The entry persists start intent before installing configuration and invoking
the producer's returned argv. The existing Noodle instance lock, not a second
lifecycle, protects adoption/start. Unknown start cannot be repeated. Host config
is externally pinned and preserved; only this entry's own process is stopped.
Provider completion remains necessary before the original order's Noodle
control-mailbox approval. A refused acknowledgement cannot be turned into success.

`native-continuation-control` used the actual selected darwin Noodle binary in
a disposable Git/provider/worker fixture. It observed one execution attempt,
completed/nonblocking typed outcome, exact-owner adoption, an actual Noodle
merge acknowledgement, completed original order, absent worker process/group,
own-loop shutdown and restored absent host config. Its synthetic Issue number
118 is fixture identity, not a second live #118 operation; experiment owner is
#133. No model consumer or live provider participated. It proves this native
composition only, not P-class improvement, live R-class or terminal #133 delivery.

The first `native-start-control` process returned zero but its raw trace showed
the synthetic worker incorrectly writing from the scheduler role, changing the
fixture base, then receiving worker.git.head refusal. That control is explicitly
INVALID_CONTROL_NOT_GREEN. The fixture was corrected to leave scheduler source
untouched and require actual typed outcome plus absence of worker refusal.
The old raw result remains in raw.json. This developmental control correction
does not change the frozen comparison observer/protocol or consume a fresh sample.

Qualification records, command requests/results and full new control stdout/
stderr are embedded in raw.json as well as preserved outside the worktree.
The skill update only describes the bound host/config and read-token distinction;
its structural validation does not supply missing behavioral evidence.

Additional raw evidence under
`/Users/neon/.codex/experiments/soodles133-implementation.8JptD5/evidence/`:
`bootstrap118-readonly-control` (actual #118 custody read, no landing admission),
`bootstrap-controls` (first 12 fixture controls), `candidate-bootstrap-full`
(258 tests, exit 0, stderr SHA-256
`4efb83d24c3ee16d55505fff61a186ba5c60a010dce12a28ceee8a06d936650a`),
and `native-bootstrap-cleanup` (real Noodle, synthetic provider, exit 0).
Each retains request argv/cwd, exit status and full stdout/stderr with digests.
These development controls do not consume the frozen final treatment run.

## #118 dependency bootstrap — live terminal evidence

The supervisor selected immutable source 2bbe408875a190a794a049c910d9cd679c966ffe
outside the #118 candidate, solely as #118's corrected landing owner. Selection
was recorded before fresh owner admission; the prior owner had refused without
creating a checkpoint or offering a write. Verifier SHA-256:
`5c75d37f29732f51962b67cbddf1b2910adfe3524a3a8cda06114726228cd813`.
This does not promote #133 candidate code to its own landing authority.

Fresh readback reused #118 exact-head runtime 35689469368 attempt 1 and successful
quality observation. The quality workflow's `completed-runtime-cost` job is
inapplicable to the pull_request event and was skipped by its existing condition;
it was not represented as a passed check. No workflow or runtime lock changed.
The local host supplier issued separate repo-scoped App tokens for the owner's
merge and close requests. Each request was transported once and each token was
revoked (204). Neither token nor App private key was persisted in evidence.

- PR119 merge: b184c43de6d3ba37d2a73fbab387fda0c9bdaac5.
- Issue118: closed/completed, 2026-09-22T06:33:51Z.
- Provider/local main tree: 908ed65365c586ef6c90a90b38f09ba2bf7f1a93.
- Actual landing.reconcile: RESOLVED; main fast-forwarded and Noodle removed
  `issue-118-local-supervisor-admission` worktree and its local branch.
  Git commits remain reachable on main; the #118 baseline worktree and existing
  main stash were untouched.
- Merged-main Linux runtime 35695310927: completed/success. Artifact 10679962668,
  digest `sha256:42616108a620cf2847da4c44a55758968edaabbf01a776d6fe9267b6ee485d02`.
  Artifact metadata was read; archive contents were not inspected in this turn.

The surviving external packet contains `landing118-selection.json`, the pinned
owner, exact claim/custody, numbered raw provider snapshots, token-free transport
results, `landing118-checkpoint.json`, `landing118-main-runtime.json`, and
`evidence/landing118-reconcile/{request.json,result.json,stdout.bin,stderr.bin}`.
The #133 worktree integrated this landed dependency in merge commit
2e0c85968cf8377bd6c205449880d31926d908aa, without copying supplier source changes.
Its actual new delivery base must be freshly rebound before #133 publication;
the experiment baseline remains d6315be and is not silently rewritten.

Self-review caught a candidate fixture incorrectly retaining proposal `do/with`
instead of canonical `skill/provider`. The first 271-test green run is retained
as `live-owner-observation-full`, but cannot demonstrate canonical compatibility.
The pre-correction diff is preserved externally. Both the fixture and consumer
were corrected against the selected Noodle StageNode source, with an explicit
negative control for proposal-shaped state; see `canonical-owner-observation-full`.
