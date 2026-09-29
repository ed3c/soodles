# #185 — bounded own-start continuation

Origin: `ed3c/soodles#185`; admitted base `12fb0a6ab8660fc1d7f0e0822e3b0fd28089d5dd`.
Measured clean source: `8f3fe5f9e17135a0bec16f2a0a63d312af274e47`.
The final evidence-only commit preserves that source and both instruction files.
All local observations have `authorizes_landing: false`.

## Supported result

| Observation | Baseline | Measured treatment |
| --- | --- | --- |
| Fixed external oracle | 16/18 | 18/18 |
| Own pending / own running | Both refused | Both bounded pending, same command |
| Sixteen foreign / missing / contradictory cases | Refused | Refused |
| Fresh consumer own-start external-input barrier | 1 | 0 |
| Fresh consumer foreign-owner result | Refused | Refused |
| Consumer legal interpretation | Legal | Legal |

The CLI mechanically removes the unnecessary intervention barrier for positively
identified own startup. Both fresh consumers correctly interpret their actual
outputs and do not claim lifecycle completion. This is scoped legal nonregression,
not measured behavioral improvement. The intervention combines code and selected
Skill changes; a prompt-only causal effect is not isolated. The paired consumers
saw one neutral task and two invocations each, without inherited conversation,
expected answers, another arm's result, or resampling, as recorded by the supervisor.

`raw/treatment-oracle.json` and `raw/fresh-consumers.json` are unchanged copies of
the supervisor-root results. The latter contains 30 raw records, including packets,
instruction reads, invocation outputs, reports and actual native final messages;
the writer verified each retained source file's digest and embedded content.

## Boundary and downstream behavior

`require_available_owner` proves exact started loop, held existing native lock,
pinned envelope/launcher/config, own admitted order projection, and bound scheduler
and live execute session/process metadata. Pending execute may have no attempt.
The early response precedes credential resolution, supplier, provider, start,
claim and lifecycle checkpoint effects. Existing `drive` owns bounded observation;
there is no new scheduler, retry engine, verb or authority flag.

Rereads compare session identity/status/alive and all canonical orders except their
`updated_at`. Session cost/timestamp telemetry does not invalidate custody; process,
spawn and immutable launcher/config bytes still must match. Canonical JSON comparison
preserves scalar types, so `alive: 1` cannot replace `alive: true`.

Focused tests cover no effects, unchanged fixture bytes, pending/running wait,
dispatch/attempt consistency, deadline, telemetry-only churn, session identity and
status drift, wrong scalar types, immutable pins and malformed active scheduler
negatives. A subsequent idle scheduler reaches the existing credential gate;
a subsequent foreign order refuses immediately without a retry. That transition
control proves re-entry to the normal gate, not successful provider delivery.
Unknown/offered/stopped startup, missing admitted order, foreign identity/config,
missing metadata and malformed attempts remain refusals. Existing unknown-write
readback and downstream publication/landing owners remain in force.

## Same-Issue correction and evidence preservation

`raw/first-attempt.json` retains the withdrawn writer's typed blocked outcome and
actual RED receipts. Its clean head `5be0db089219525838918ad86a2396d695dcdbd5`
was withdrawn before any treatment consumer launched: the 451-test suite had one
historical #181 replay failure, and pre-measurement review found a telemetry-only
refusal. The supervisor explicitly admitted this correction and selected the new
clean source before the single treatment consumer. Old raw outputs are preserved;
new runs use `corrected-*` filenames externally.

Following the unchanged `frozen/migration.md`, the #181 test adapter extracts exact
historical commit `12fb0a6ab8660fc1d7f0e0822e3b0fd28089d5dd` through `git archive`.
A missing object fails diagnostically. It compares current historical evidence bytes
to the archive, replays the original observer/manifest/raw records, and retains
both legal-owner-prose and planted-wrong-continuation discriminators. No historical
pins, observer or replay source changed. Separate current-source oracle/tests
qualify #185. All eight externally frozen file hashes remain unchanged.

## Scoped eval audit

- Error analysis: observed #183 own-start refusals and fresh fixtures identify a
  concrete owner-classification failure; later snapshots do not reconstruct every
  historical process detail.
- Evaluator design: exact code predicates check status, same-command continuation,
  identity, fixture effects and residue. Always-refuse fails the two positives;
  always-wait fails the sixteen negatives. No subjective LLM judge is used.
- Judge validity: binary discriminators support these selected cases only. The
  supervisor's independent source/pre-measurement reviews remain separate from
  writer self-review and the fixed oracle.
- Human review: supervisor inspected the retained first consumer reports and fixture
  outputs. Consumer-recorded traces are not complete platform transcripts.
- Data coverage: one fresh pair, two cases each. No population failure-rate,
  model-efficacy, total decision-cost or token savings estimate is supported.
- Pipeline hygiene: criteria were frozen externally before the candidate; the old
  failed selection was preserved and explicitly withdrawn before treatment launch.
  Measurement bytes remain unchanged through final evidence packaging.

This P-class update covers only the demonstrated issue-atom/issue-execution route.
Tokens, actual model identity, compaction, complete transcript and independently
established live transport absence remain unknown. Invocation latency is descriptive.
Mocked PID/command/context evidence supports bounded wait, not OS generation-proof
identity or live process attestation. This is not full feature-map maintenance,
global behavior nonregression or a delivery-completion claim.

## Native verification and remaining owner

Final focused run: 69 tests passed. Full native suite: 453 tests passed in 143.706s
(test process elapsed 144.003s), using test-only removal of inherited `NOODLE_*`
and `TMPDIR=/private/tmp`. The independent telemetry probe now returns pending,
with canonical state/config unchanged and only the fixture process read recorded.
The complete source/contract manifest binds both instruction baseline/treatment
digests and every required nonmanifest artifact. Linux canonical exact-head Actions
acceptance, publication, merge/closure and Git/Noodle reconciliation remain with the
external supervisor; this writer performs no provider writes and does not claim
RESOLVED. The local downstream gate tests cannot replace those checks.

The following records preserve actual corrected control outputs. Paths identify
external evidence storage, not executable continuation authority.

### corrected-focused-controls.json

SHA-256: `45f7fb0adc5fb4be26ac3ee99c54c13f33659d0e14399fe277d22561caf92ef0`.

```json
{
  "argv": [
    "python3",
    "-B",
    "-m",
    "unittest",
    "test_issue_atom",
    "test_local_continuation",
    "test_owner_continuation",
    "test_issue181_handoff_evidence"
  ],
  "cwd": "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/control-corrected/.worktrees/soodles-185-aa89b37b557a-0-execute",
  "exit_status": 0,
  "elapsed_seconds": 34.29963237512857,
  "environment": "NOODLE_* removed; TMPDIR=/private/tmp; PYTHONPATH=tests",
  "authorizes_landing": false
}
```

### corrected-focused-controls-2.json

SHA-256: `df36a021a6f92f5fc462e0626b7bf2d13ed496ddad3e0e4f61e9ba253674c933`.

```json
{
  "argv": [
    "python3",
    "-B",
    "-m",
    "unittest",
    "test_issue_atom",
    "test_local_continuation",
    "test_owner_continuation",
    "test_issue181_handoff_evidence"
  ],
  "cwd": "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/control-corrected/.worktrees/soodles-185-aa89b37b557a-0-execute",
  "exit_status": 0,
  "elapsed_seconds": 34.00057083298452,
  "environment": "NOODLE_* removed; TMPDIR=/private/tmp; PYTHONPATH=tests",
  "authorizes_landing": false
}
```

### corrected-treatment-oracle-process.json

SHA-256: `85a25757a0750806f965f7c3504e41df6a32f698018712ec3f5f4409f5e91e3b`.

```json
{
  "argv": [
    "python3",
    "-B",
    "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/frozen/oracle.py",
    "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/control-corrected/.worktrees/soodles-185-aa89b37b557a-0-execute",
    "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/treatment-oracle.json"
  ],
  "head": "8f3fe5f9e17135a0bec16f2a0a63d312af274e47",
  "exit_status": 0,
  "elapsed_seconds": 9.864360624924302,
  "stdout": "{\"classification\": \"PASS\", \"passed\": 18, \"total\": 18}\n",
  "stderr": "",
  "environment": "test-only removes NOODLE_*; TMPDIR=/private/tmp",
  "authorizes_landing": false
}
```

### corrected-native-unittest.json

SHA-256: `b1066e2e0a98da7ebc93bf0b6d0172038eac38b94c15671ec442232fe9c8a658`.

```json
{
  "argv": [
    "python3",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tests"
  ],
  "head": "8f3fe5f9e17135a0bec16f2a0a63d312af274e47",
  "exit_status": 0,
  "elapsed_seconds": 144.00297395908274,
  "stdout_stderr": "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/corrected-native-unittest.log",
  "environment": "test-only removes NOODLE_*; TMPDIR=/private/tmp",
  "authorizes_landing": false
}
```

### corrected-telemetry-probe.json

SHA-256: `71a7e34104bafa412248e789155406b43ba17f0bfb0a76b7841f80bdeaa6fac5`.

```json
{
  "case": "own_pending",
  "result": {
    "owner": "soodles.issue-atom",
    "status": "pending",
    "phase": "execution",
    "issue": {
      "number": 131
    },
    "publication": null,
    "next": {
      "kind": "executable",
      "owner": "soodles.issue-atom",
      "required": [
        "material_owner_or_provider_state_change"
      ],
      "argv": [
        "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/control-corrected/.worktrees/soodles-185-aa89b37b557a-0-execute/issue-atom",
        "run",
        "/private/tmp/tmp_aild12b/authorization.json"
      ],
      "reason": "Re-enter the same command; do not select a phase-specific Issue, publication, or landing verb."
    },
    "authorizes_landing": false,
    "waiting_on": "Noodle",
    "execution": {
      "action": "own_start_wait",
      "order_id": "soodles-131-6add6f4dc63e",
      "sessions": {
        "schedule": "fixture-scheduler"
      },
      "execute_status": "pending"
    },
    "wait_exhausted": true
  },
  "calls": [
    {
      "fixture_process_read": [
        "ps",
        "-p",
        "424242",
        "-o",
        "command="
      ]
    }
  ],
  "canonical_state_config_unchanged": true,
  "authorizes_landing": false
}
```

### corrected-focused-controls.log

SHA-256: `80de144417d24cf9545b18f9e946f39d515e7cbbd1af05f29a205060a3e96994`.

```text
.....................................................................
----------------------------------------------------------------------
Ran 69 tests in 34.086s

OK
```

### corrected-focused-controls-2.log

SHA-256: `93d3cef6f7470c43eb23567447eec155ed4a64b842319a96ea914e6bf60e727e`.

```text
.....................................................................
----------------------------------------------------------------------
Ran 69 tests in 33.794s

OK
```

### corrected-native-unittest.log

SHA-256: `1576cb35a7e9faeaa99dd5c10ad9cb13362482c750086ce6ffe3089fe736d078`.

```text
.....................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 453 tests in 143.706s

OK
```

### Measurement binding

```json
{
  "worktree": "/Users/neon/.codex/experiments/pclass-owner-continuation-w192sw1i/control-corrected/.worktrees/soodles-185-aa89b37b557a-0-execute",
  "head": "8f3fe5f9e17135a0bec16f2a0a63d312af274e47",
  "sha256": {
    "issue_atom.py": "6f86667d00e6ba56aa25dc028e322169d2d34c9f4c8dd8087cfe980fed20a889",
    ".agents/skills/issue-atom/SKILL.md": "c2be68318b2323e4ab228bc47345aebddcf3d27db0fa8115a820128ef93105d8",
    ".agents/skills/verify-soodles/features/issue-execution.md": "bb807b50e17f131e43bee03ec7c9b54c80ce24888539655a476483c9c1f2a139"
  },
  "created_at": "2026-09-29T08:20:40.400056+00:00",
  "authorizes_landing": false
}
```
