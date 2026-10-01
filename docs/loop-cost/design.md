# Issue 215 cost evidence

## Method and phase record

One writer; no arena, delegation, provider research, comparison or experiment.
This adapts the supervisor-selected pstack methods as explicitly admitted.
Ground: complete. Sketch: two structural alternatives complete. Agree: default
no checkpoint, selected A. Implement: complete; CI unexecuted locally. Scrap: reviewed; no redesign needed; subtract
per-phase accumulators and any inferred spending/budget policy before coding.

## Ground and rationale

`soodles.measured → acceptance` emits stderr timing but treats returned pending
and refused dictionaries as passed. `test_manager.run_modules` measures discovery,
modules and cases: module workers overlap, case durations are nested; their sums
cannot be wall latency. `quality/provider.py.collect` is a precedent for independent
readback with pending/partial coverage, not an authority source or a new scheduler.
`issue_atom.run → _run → _run_owned` owns authorization/atom locks and artifacts;
`drive` waits between invocations. `finish_host → schema_manager.Manager` consumes
fixed host facts without taking effect custody. `atom_repair.Controller.perform`
reserves intent before effect; `check/report` preserve exclusive lineage and limits.
Repair seconds mean elapsed time since first repair, not whole-Issue compute.

Direct rationale: admitted #215 forbids new effects, thresholds and experiments;
contract issue-atom bounded repair and fixed-host sections require source pins,
unknown-effect readback and original cleanup. Git anchors: d05886e introduced fixed
host finalization; 7b8aa9e requires explicit extra CI demand; a3356c9 preserves original
cleanup. These support preserving owners. Wider historical motives are unknown;
external categories were intentionally not searched under this task's cost constraint.

## Usage and two shapes

A (selected): `cost_telemetry.report(AUTH, MANIFEST)` validates original bytes and
normalizes records; `schema_manager.project_cost(facts, gate)` is data-only. Normal
`issue_atom.run` records under its authorization lock and attaches the same projection.
CLI: `./soodles atom cost-report /absolute/authorization.json /absolute/evidence.json`.
B: each phase stores counters and exposes its own reporting adapter, with Schema
Manager combining them. It hides less: callers must coordinate replay, nesting,
coverage and source validation. Rejected as information leakage and temporal
partitioning; it would also require checkpoint migration of old immutable owners.

A hides source formats, identity validation, idempotence and overlap arithmetic
behind one evidence boundary. Raw observations stay in the existing artifact
directory, separate from authority state. No generic callbacks, second database,
new lock or policy flag. Schema projection cannot authorize or schedule effects.
The module's own timing is observed only for subsequent normal executions.

## Tradeoffs and limits

Read-only reports verify digests and subject links, not the truth of a supervisor's
assertions. Observer identity attests origin only. Old owner bytes remain immutable:
new reports do not claim it emitted new spans. Missing intervals, tokens, price,
API accounting and human attribution are unknown. Observed foreground elapsed is
inclusive of internal I/O; it is not CPU time. Provider job/worker sums overlap.
No fixture result is live budget exhaustion. CI controls are authored, not run locally.

## Evidence input

See the concrete manifest and coverage contract below after implementation.

## Concrete read-only input contract

The supervisor writes schema 1 JSON. `REF` below always means exactly
`{"path":"/absolute/original-or-snapshot-file","sha256":"64 lowercase hex"}`.
Paths are data; no file is imported as Python and no argv is executed. A source
SHA attests matching bytes, not independent truth. Preserve original observer
receipts; do not rewrite them into candidate-authored accounting.

```json
{
  "schema": 1,
  "authorization_sha256": "SHA256_OF_ORIGINAL_AUTHORIZATION_BYTES",
  "subject": {
    "authorization": "SHA256_OF_ORIGINAL_AUTHORIZATION_BYTES",
    "repository": "ed3c/soodles",
    "issue": null,
    "base_head": "8c6f872620c97cca203b7f325b6bd714ef8cbb45"
  },
  "head": "EXACT_CANDIDATE_HEAD_FROM_ORIGINAL_PUBLICATION",
  "state": "REF_TO_ORIGINAL_AUTHORIZATION.state.json_OR_EXACT_SNAPSHOT",
  "claim": "REF_TO_ORIGINAL_publication-claim.json",
  "owner_result": "OPTIONAL_REF_TO_ORIGINAL_ATOM_RESULT",
  "processes": [
    {
      "process": "REF_TO_observe.py_PROCESS_JSON",
      "input": "REF_TO_THAT_PROCESS_INPUT_RECEIPT",
      "stdout": "REF_TO_THAT_PROCESS_STDOUT_JSON",
      "stderr": "REF_TO_THAT_PROCESS_STDERR_LOG",
      "observer": "REF_TO_PINNED_observe.py"
    }
  ],
  "provider": [
    {
      "run": "REF_TO_EXACT_GITHUB_RUN_OBJECT",
      "jobs": "REF_TO_ITS_ATTEMPT_JOBS_RESPONSE",
      "log": "OPTIONAL_REF_TO_NORMAL_ACCEPTANCE_LOG"
    }
  ],
  "native": [
    {
      "file": "REF_TO_ORIGINAL_NATIVE_PROCESS_META_OR_RAW_LOG",
      "session_id": "EXACT_CLAIM_SESSION_ID",
      "order_id": "EXACT_CLAIM_ORDER_ID"
    }
  ]
}
```

Replace explanatory strings with REF objects (and real SHA/head values). Only
schema, authorization_sha256, subject, head and state are required. Omit optional
keys rather than using these explanatory placeholders. Head is null before any
publication/claim; an adopted authorization without a selected Issue number uses
subject.issue=null, preserving that original subject identity across admission.
The actual state still retains the created Issue. Lists may be empty; absent
coverage is unknown, never zero. One provider snapshot per run/attempt is allowed;
conflicting snapshots in an external manifest refuse instead of selecting one.
Normal owner history may retain multiple observations of a progressing job;
completed job duration conflicts refuse and identical completed spans count once.

For the already pinned supervisor collector, retain its exact `process.json`,
`input_receipt` file, `.stdout.json`, `.stderr.log` and `observe.py`. The importer
compares input path/hash and next.argv (including the original authorization path),
observer hash, output hashes, available Issue/head identity and finite wall/monotonic
durations. Non-JSON stdout retains unknown status (or failed process exit), never
passed. Stderr's old wrongly passed pending/refused timing is normalized from its
actual returned status. Missing old wall bounds are not reconstructed. An optional `intents` list accepts `{intent: REF, input: REF, observer: REF}`
for collector starts without completed process receipts. They retain unknown
status and duration; list only genuinely incomplete invocations there. Native raw files are retained under exact claim
order/session linkage. Optional `kind: "meta"` additionally cross-checks the JSON
session_id and exposes a finite nonnegative total_cost_usd as reported_cost_usd in
native_usage, never a billed price or independently verified total. `kind: "codex_raw"` reads a single terminal Codex turn.completed usage record.
Multiple-turn totals remain unknown because cumulative versus incremental accounting
is unspecified. Cached/reasoning counters are subsets, never added to token totals;
reported usage is not a billing authority.

Provider run repository/head/workflow and job run_id/run_attempt/head must match.
Log lines come from the explicitly supplied run entry, retain their source hash,
and cross-check any embedded head. Offline files cannot independently prove API
origin or complete pagination/history; this limitation keeps their coverage partial.
Test module names/counts are retained as observed scope. Case timings are nested
and excluded from module totals. Provider job seconds are reported separately from
module worker seconds. API file observations do not equal API request counts.

The command emits `status`, subject, source hashes, all metric-family coverage,
summary, `schema_projection`, evidence refs and artifacts pointer. It never reads
credentials, runs Git or validates/publishes a candidate. A corrupt input returns a
non-authorizing refused report. The original runtime/landing owner is not replaced.

## Normal integration and projection

The normal atom records an unknown start, then replaces only that observation with
its finished result under the original authorization lock. Completed spans include
status/phase, duration, wall bounds, source and available head/session. Waits have
independent spans and authorization/observation correlation in stderr. The normal
owner retains already-returned run/jobs bytes and normalizes them through the same
external-evidence adapter without another provider GET. An external manifest at
`AUTHORIZATION.d/cost-evidence.json` automatically supplements normal projections.
Once the original publication claim exists, normal reports also read its original
Noodle session raw log for available terminal Codex usage. Raw source and record
files stay under the existing artifact directory. Reporting
reads history linearly; it adds no checkpoint migration or second authority store.

Coverage includes end-to-end, processing, waits, writer/model, API observations,
verification, retries, startup, publication, landing, cleanup and telemetry. Recorded
spans are measured; family coverage is partial until whole-family accounting exists.
End-to-end is only the observed envelope; gaps are not attributed to people. Normal
foreground ending in a phase is explicitly inclusive, not exclusive phase cost.
Unknown/unavailable spans retain null durations. Available single-turn Codex token usage is exposed; price/CPU/API counts/human
waiting without an accounting source remain null. Telemetry records its
record/report overhead for the next projection, excluding its final evidence flush.

Schema Manager receives finite numeric summary, source refs, coverage and the
existing owner's refusal/repair budget/history basis. It projects no effects and no
test demand. Unknown write and host-finalization facts remain with their owner.
`Controller.cost_status` reads `check()` and existing limits; it neither performs a
repair nor decides a new retry. Missing trusted lineage remains unavailable.

## Verification and remaining work

Local verification is syntax parsing, diff review and hash checks only. Authored
controls in test_cost_telemetry cover source/status/replay/numeric semantics,
partial old logs, parallel/nested accounting, original observer/provider import,
read-only behavior and normal refusal/continuation preservation. Existing repair
reserve-before-effect/unknown-write controls remain; the added cost-status case
reads synthetic history without spending it. Lifecycle controls cover new pins
and legacy exact descriptor compatibility. Test Manager maps the new evidence
boundary to these consumers and candidate evidence validation; it does not request
full coverage. No tests, benchmark, fault experiment, model comparison, arena or
fresh provider measurement were run locally. Normal exact-head CI remains pending.

The supervisor independently records this actual #215 atom and, after acceptance
and merge, runs the command against original receipts. No live numeric savings,
live budget exhaustion, Agent behavior improvement or terminal delivery is claimed
by this candidate. External acceptance/landing and original Noodle cleanup remain
unfinished at writer-stage completion.

## Actual selected method hashes
Source commit: `68836ddaf5697224520f1847d90cdb90ca8babaa`. All five method byte hashes match the supplied pins.
- `pstack/skills/architect/SKILL.md`: `585d7a9e03c0cced84c80d4b60c09c8dc76010bb36c579f92d9e4deafec53df7`
- `pstack/skills/architect/references/rationale-template.md`: `6645a0e5f68c003298ec95b85a23262bdda0c79f998b926060169b54d9f23fbb`
- `pstack/skills/architect/references/design-red-flags.md`: `905066f9bbac81c573c2b325be47751d2c0f9325e0a0772bd4384e82dafe9336`
- `pstack/skills/how/SKILL.md`: `fe503e7a9b2a3a7ad2622a2de6124cb06c466922fb44bc61817b49b52042b885`
- `pstack/skills/why/SKILL.md`: `dc8f2d8a7dbef7d0467cca8e6d055a4dbde027db6e2cbbfb18aa9071d8f20b6c`
- `pins.json`: `cf58a00d0a881f5dca2a4545909c03ac72d04adb9ddafebc15c0f5a8150f5fa0`

New lifecycle pins include cost_telemetry.py. The supervisor worker bundle still
serves issue/worker entrypoints and needs no cost import: soodles.measured uses
only the standard library. The independent landing OWNER_FILES closure is unchanged.
Wait controls now permit only cost-artifact writes; their original lifecycle/config/
provider no-effect and unchanged-byte assertions remain intact.

## Supervisor review before publication

The actual new-Issue authorization has no Issue number. Its stable cost subject
keeps null, while external process/claim readbacks bind the created number through
the original state authorization, body-marker digest and exact Issue URL. This does
not rewrite authorization or observations. Nonzero process exits retain typed
refused/pending/unknown results, separately from the raw exit evidence.

Schema Manager receives per-phase inclusive observed durations and legacy logged
wait seconds; nested phases must not be summed into wall latency. Provider job
bounds are separate from foreground bounds. Historical write offers are labeled
history, with current required readback taken only from the owner response.

The installed pstack provider was updated during this atom to cursor/plugins
2eb7ed4613cfc8f098dfe464a23680ea44d84c5e (0.15.5). The dispatched writer used
the original pinned 0.14.5 snapshot above; supervisor review read the new architect
method. No arena or model experiments were added.

## Correction after the first normal CI attempt

Normal exact-head run 36880034418, job 110429169809, failed at
`e8ffb08b5022045d10a917195fbc4a254e87a270`. Its original raw log remains at
`/Users/neon/.codex/soodles-loop-cost-um4agqox/fresh-control/ci-first/job-110429169809.log`.
The original native report at
`/Users/neon/.codex/soodles-loop-cost-um4agqox/fresh-control/native-report/report.json`
also refused with `cost.native_fields`. These failed receipts remain unchanged.

The correction admits the already implemented `codex_raw` format in the native
kind whitelist. Unsupported raw usage remains unknown. The existing
`test_codex_terminal_usage_and_nested_schema_numbers` control covers the parser.

`issue_atom.run` still records unknown starts and finished observations, but only
adds `cost` to responses with a string status. Opaque owner responses pass through
unchanged; their projection or refusal diagnostic uses the existing `soodles.cost`
stderr event. Pending, refused and resolved responses retain their cost field.
The added focused control checks opaque payload preservation, stderr projection,
visible cost refusal and persisted unknown observations. Existing typed-response
controls and `test_cleanup_continuation.py` remain unchanged.

This correction applies pstack 0.15.5 architect's subtract-first principle by
removing unconditional payload mutation without adding an adapter or redesign.
Local checks are syntax, diff and hashes only. No local tests or reporting runs
were executed; corrected behavior awaits normal exact-head CI on the same PR.
The supervisor retains original reporting, publication and landing ownership.
