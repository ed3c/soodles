# #157 bounded results

## Actual deterministic result

Pinned baseline decider: 6/9 controls passed; three invalid comparisons admitted.
Corrected decider: 9/9 controls passed with the identical frozen probe.
The correction adds per-case exposure equality in the existing validator.
No other production module, CLI verb, provider route or authority is changed.

| Fixture | Baseline | Treatment |
| --- | --- | --- |
| Different case sets | ADMIT_IMPROVEMENT (wrong) | REJECT |
| Different case counts | ADMIT_IMPROVEMENT (wrong) | REJECT |
| Unmatched 0-to-0 | ADMIT_NONREGRESSION (wrong) | REJECT |
| Matched legal improvement | ADMIT_IMPROVEMENT | ADMIT_IMPROVEMENT |
| Matched legal nonregression | ADMIT_NONREGRESSION | ADMIT_NONREGRESSION |
| Four existing refusal controls | REJECT | REJECT |

The nine-case assertion was executed against the copied, byte-verified source
and the corrected source. The added public replay integration test is present;
its execution and full repository acceptance require exact-head Actions evidence.
Do not report these pending checks as passed. Fixture projection/gate values are
synthetic test inputs, not real owner readbacks or independent Agent telemetry.

## P-class and closure: NOT COMPLETE

The recipe delegates exposure eligibility to the existing decider and consumes
its rejection; no model-side counting procedure is added. This is guidance, not
proof of actual adherence. Fresh isolated consumers were NOT run. Behavior counts
and independent telemetry remain unknown; `consumer-comparison.json` is BLOCKED.

The supported result is an executable evaluator-defect correction, not a measured
Agent decision-cost reduction. The Issue must remain OPEN and the PR DRAFT until
its fresh comparison and exact-head supervised cloud delivery are complete.
No merge, closure, production transport or local #156 work is authorized by these
receipts. Historical experiments and their selected judges remain unchanged.

## Method

Scoped `eval-audit` on evaluator design/pipeline hygiene at
ai-evals-course/evals-skills@2edbc5b1b0dc91f74fcfa8fd8f7eaeb302e052ab.
The observed objective mismatch is checked by code. No new LLM judge, forced
error-discovery pass, dashboard or general eval platform was installed.

## Typed refusal follow-up on the same unmerged PR

Predecessor head: 467454d3c3086c7298cf460ab3e6e1d15d25cb49.
The original results above and treatment.json's original fields are historical,
not new executions of the revised candidate. The appended typed_next_followup
record contains the new actual before/after process evidence.

Only three production lines add an input descriptor for the existing exposure
refusal. P now consumes `decision.next` from the unchanged replay envelope. No
new CLI, replayer, carrier, scheduler, write permission or state store is added.

The same four focused unit tests ran on both sources. Before: exit 1, six
assertion failure records across three new tests; the old nine-case probe still
passed. After: exit 0, all four tests passed, including the unchanged nine-case
probe. Checks cover the exact descriptor, legal and unrelated output stability,
mixed-error preservation, unchanged inputs, rejection of caller-supplied next,
no executable argv/request, and independent returned descriptor objects.
These are deterministic fixture controls, not fresh Agent observations.
The strengthened public replay test is committed but is not claimed executed
in this scratch process; exact-head Actions must verify it.

The scratch helper download failed with DNS resolution before public replay
could run. No substituted replayer, scratch Noodle or alternate carrier was
installed. Byte-verified archive source sufficed for the four focused controls.

The previous exact-head runtime run 35864011049 remains a recorded failure:
369 tests, one comparison-gate temporary .git cleanup failure. It was not rerun
or waived; this is a real new source head, not an empty change to seek green.
The cleanup root cause has not been established or changed by this refinement.
Fresh acceptance for the new head is pending at commit construction. Provider
results will be recorded in the same Issue/PR, not invented in these artifacts.

consumer-comparison.json remains byte-identical: BLOCKED / INCONCLUSIVE, no
fresh runs and null behavior counts. The planned six-run comparison, external
observer selection, exact-head acceptance and supervised landing remain required.
Keep #157 OPEN / #158 DRAFT. #156, frozen probe, historical judges, workflows,
provider transport and all local admission/lifecycle files are unchanged.


## Readiness veto follow-up — 2026-09-26 (not native completion)

Origin remains #157 / PR #158. Parent candidate is
`e1061c80b97706b5784f63a7c2cdd87c80fa1ed1`. Its recorded successful runtime
`36160092262` coexisted with the byte-valid BLOCKED consumer artifact. This
follow-up makes that unmet requirement visible in existing acceptance discovery.

The experiment-local `consumer_gate.py` is a conservative read-only veto, NOT
a complete native consumer evaluator. It verifies the supplied file digest,
rejects absent/foreign/malformed evidence, and emits a typed supervisor input
request. It has no positive native-capture adapter and cannot yet admit a real
completed comparison. Six dictionaries or a self-labelled PASS are not proof
of execution. No native launch schema, carrier or external authority is invented.

The existing test module adds seven veto-control tests and one actual-artifact
acceptance requirement. The seven controls plus four existing focused tests
passed (11 total). The actual-artifact requirement ran separately and FAILED
because no fresh runs exist. This RED result is required, not waived: do not
use skip/expectedFailure or count a passing refusal control as completion.
The existing public replay test and full repository suite were not run in this
scratch subset; a new exact-head Actions run must report their own outcomes.

The P recipe, production decider, frozen probe, baseline, protocol, treatment
record and BLOCKED consumer artifact remain byte-identical to the parent. The
new veto runs through existing acceptance instead of adding another P procedure.
The issue scope was amended before repository source publication.

A native-capable supervisor still must pin the actual capture mapping/observer,
execute the fixed six-run protocol, add truthful raw evidence, and implement
controlled positive validation in this same gate/PR. No current claim of native
evidence ingestion, P behavior improvement, terminal readiness or landing is made.
Historical #39 `trace`/`calls` records explicitly disclose incomplete capture;
they are design evidence only, not replacement #157 consumers.

### Raw focused execution records

The following are actual captured scratch processes, not model traces or an
independent external judge. Input/control SHA-256 values were recorded before
the processes and checked unchanged afterward. The required-evidence failure
is deliberately preserved separately from passing unit controls.

```json
{
  "pre-test-control-pins": {
    "scope": "candidate unit controls fixed before execution, not external native judge",
    "files": {
      "docs/experiments/pclass-case-exposure/consumer_gate.py": "a70af335f97b439ba60c4e54a4cfacdfb479cea0d730d53bddd78c6eb4f32efc",
      "tests/test_pclass_case_exposure.py": "b75fc61fdbaf3eab30d1e7436714346f4fc111b4e1395899dd9b21e7b4ad5168"
    }
  },
  "unit-controls": {
    "argv": [
      "/opt/pyvenv/bin/python",
      "-B",
      "-m",
      "unittest",
      "-v",
      "test_pclass_case_exposure.ConsumerReadinessControls",
      "test_pclass_case_exposure.TypedNextTests",
      "test_pclass_case_exposure.CaseExposureTests.test_frozen_nine_case_probe"
    ],
    "cwd": "/mnt/data/soodles157-consumer-gate/candidate/tests",
    "exit_code": 0,
    "stdout": "",
    "stderr": "test_file_binding_json_and_paths_fail_closed_without_writes (test_pclass_case_exposure.ConsumerReadinessControls.test_file_binding_json_and_paths_fail_closed_without_writes) ... ok\ntest_invalid_identity_schema_and_authority_are_rejected (test_pclass_case_exposure.ConsumerReadinessControls.test_invalid_identity_schema_and_authority_are_rejected) ... ok\ntest_missing_null_and_partial_runs_do_not_become_zero (test_pclass_case_exposure.ConsumerReadinessControls.test_missing_null_and_partial_runs_do_not_become_zero) ... ok\ntest_readonly_cli_returns_typed_block_without_traceback (test_pclass_case_exposure.ConsumerReadinessControls.test_readonly_cli_returns_typed_block_without_traceback) ... ok\ntest_real_blocked_artifact_is_not_zero_or_success (test_pclass_case_exposure.ConsumerReadinessControls.test_real_blocked_artifact_is_not_zero_or_success) ... ok\ntest_returned_descriptors_are_independent (test_pclass_case_exposure.ConsumerReadinessControls.test_returned_descriptors_are_independent) ... ok\ntest_self_labelled_completion_cannot_manufacture_native_evidence (test_pclass_case_exposure.ConsumerReadinessControls.test_self_labelled_completion_cannot_manufacture_native_evidence) ... ok\ntest_mixed_failures_and_inputs_are_preserved (test_pclass_case_exposure.TypedNextTests.test_mixed_failures_and_inputs_are_preserved) ... ok\ntest_mutating_a_receipt_cannot_change_the_next_refusal (test_pclass_case_exposure.TypedNextTests.test_mutating_a_receipt_cannot_change_the_next_refusal) ... ok\ntest_refusal_next_is_scoped_and_non_executable (test_pclass_case_exposure.TypedNextTests.test_refusal_next_is_scoped_and_non_executable) ... ok\ntest_frozen_nine_case_probe (test_pclass_case_exposure.CaseExposureTests.test_frozen_nine_case_probe) ... ok\n\n----------------------------------------------------------------------\nRan 11 tests in 2.508s\n\nOK\n",
    "elapsed_seconds": 3.289343,
    "scope": "actual Python process; no native consumer or provider transport"
  },
  "required-artifact": {
    "argv": [
      "/opt/pyvenv/bin/python",
      "-B",
      "-m",
      "unittest",
      "-v",
      "test_pclass_case_exposure.RequiredConsumerEvidenceTests"
    ],
    "cwd": "/mnt/data/soodles157-consumer-gate/candidate/tests",
    "exit_code": 1,
    "stdout": "",
    "stderr": "test_required_fresh_consumer_evidence_is_ready (test_pclass_case_exposure.RequiredConsumerEvidenceTests.test_required_fresh_consumer_evidence_is_ready) ... FAIL\n\n======================================================================\nFAIL: test_required_fresh_consumer_evidence_is_ready (test_pclass_case_exposure.RequiredConsumerEvidenceTests.test_required_fresh_consumer_evidence_is_ready)\n----------------------------------------------------------------------\nTraceback (most recent call last):\n  File \"/mnt/data/soodles157-consumer-gate/candidate/tests/test_pclass_case_exposure.py\", line 296, in test_required_fresh_consumer_evidence_is_ready\n    self.assertTrue(receipt[\"terminal_ready\"], json.dumps(receipt, sort_keys=True))\n    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nAssertionError: False is not true : {\"authorizes_landing\": false, \"behavior\": null, \"evidence_sha256\": \"35fe05d404141de46ea87d6ce076ac62c92c4d9a9751d2be795c7a55e04f1396\", \"evidence_validity\": \"INCONCLUSIVE\", \"issue\": {\"number\": 157, \"repository\": \"ed3c/soodles\"}, \"next\": {\"kind\": \"input\", \"owner\": \"supervisor\", \"required\": [\"native_consumer_evidence\"]}, \"owner\": \"pclass.consumer_evidence\", \"problem\": {\"field\": \"fresh_runs\", \"reason\": \"six planned fresh consumer runs have not been supplied\"}, \"schema\": 1, \"scope\": \"required-consumer-evidence readiness veto only\", \"terminal_ready\": false}\n\n----------------------------------------------------------------------\nRan 1 test in 0.002s\n\nFAILED (failures=1)\n",
    "elapsed_seconds": 0.768381,
    "scope": "actual Python process; no native consumer or provider transport"
  },
  "actual-cli": {
    "argv": [
      "/opt/pyvenv/bin/python",
      "-B",
      "/mnt/data/soodles157-consumer-gate/candidate/docs/experiments/pclass-case-exposure/consumer_gate.py",
      "/mnt/data/soodles157-consumer-gate/candidate/docs/experiments/pclass-case-exposure/consumer-comparison.json",
      "35fe05d404141de46ea87d6ce076ac62c92c4d9a9751d2be795c7a55e04f1396"
    ],
    "cwd": "/mnt/data/soodles157-consumer-gate/candidate/tests",
    "exit_code": 1,
    "stdout": "{\n  \"schema\": 1,\n  \"owner\": \"pclass.consumer_evidence\",\n  \"issue\": {\n    \"repository\": \"ed3c/soodles\",\n    \"number\": 157\n  },\n  \"scope\": \"required-consumer-evidence readiness veto only\",\n  \"evidence_validity\": \"INCONCLUSIVE\",\n  \"behavior\": null,\n  \"terminal_ready\": false,\n  \"authorizes_landing\": false,\n  \"problem\": {\n    \"field\": \"fresh_runs\",\n    \"reason\": \"six planned fresh consumer runs have not been supplied\"\n  },\n  \"next\": {\n    \"kind\": \"input\",\n    \"owner\": \"supervisor\",\n    \"required\": [\n      \"native_consumer_evidence\"\n    ]\n  },\n  \"evidence_sha256\": \"35fe05d404141de46ea87d6ce076ac62c92c4d9a9751d2be795c7a55e04f1396\"\n}\n",
    "stderr": "",
    "elapsed_seconds": 0.798994,
    "scope": "actual Python process; no native consumer or provider transport"
  }
}
```

## Local carrier qualification and amendment — 2026-09-26

The Issue contract now permits a separately supervised Local Codex CLI
comparison while cloud PR delivery stays on this same atom. This entry is a
qualification record, not one of the six consumer runs. On the local host,
`codex-cli 0.156.1` exposes plain `codex exec`, distinct `resume` and
`fork`, `--json` JSONL and final-message output. `codex login status`
reported ChatGPT login. The visible config requests `gpt-6-sol` at high
reasoning effort with approval_policy=never; an effective child model/tool
receipt has not been observed. Existing persisted rollout shapes are from
other sessions, not #157 `codex exec --json` captures. No extra model trial
was run. The local worktree inventory did not identify a #157 owner/root; #156
resources are excluded. The external supervisor must still select observer
bytes, exact inputs, capture mapping, evidence destination and local resource
owner before run one. The existing gate has no successful exit and the actual
required-evidence test remains RED. No behavior improvement is claimed.

## First selected Local Codex run and mapping failure — 2026-09-26

The user authorized #157 supervisor-owned exact-ref source clones. Baseline
`00a5909941a632537dc6992b5354cd37614ea4a8` and then-current treatment
`7764df9f9b9e17b498ac58b31bc9df205ba6323f` were clean detached clones
without remotes; `codex -C PATH doctor --json` identified each clone's cwd and
repo root. The selected v4 observer SHA-256 was
`4a3d34206e8889141e341bd5e9e9c5c0bb233f3151b656eb9a8266eb4db9c5bf`;
the immutable execution selection SHA-256 was
`ebfefc5e1f1fc4fc3d72370488141ae6e1dee8060e39258f30145cd81ea5d480`.
Twenty-one synthetic controls passed; those controls were not model evidence.

One planned baseline legal-case Codex session ran with the selected recorder.
The process exited 0 without timeout, yielding 27,309 bytes of raw JSONL,
a final response and a persisted rollout. The session thread was
`01a0dd19-dcb2-76b0-962b-60a8132c7588`. The external readback SHA-256 is
`c76c7247e593a0ea6f8c6a4cba3073b7f60a9e7ecb4825949994fdc9f677f59f`;
raw stdout SHA-256 is `22bc66e574718fb3bde764f99ec68c48473aa0f09ae3c903da4ffd5f3164826b`;
rollout SHA-256 is `f28b3213e7ff51f5abe1579dff3d294d82cf7146e43c7d`.
The source clone remained clean. The rollout's selected model, effort, CLI,
cwd, Git head, sandbox and approval fields matched the request. The CLI emitted
three completed agent messages and five shell-wrapped commands; v4's pinned
mapping expected exactly one message and an unwrapped replay command.
Therefore the run is INCONCLUSIVE under v4. The observed final text and replay
receipt cannot be rescored into a valid v4 result. It used one original run;
the remaining five were not launched because they could not complete a valid
six-run comparison under that mapping.

The user authorized a separate new set of six sessions after an explicit
protocol and observer amendment. A v5 observer draft recognizes the observed
CLI wrapper and last completed agent message, reads commands directly from
raw JSONL, and keeps extra read-only commands as a secondary count. Twenty-one
synthetic controls pass. A parser check against the failed run's real raw
bytes used **synthetic before/after input timestamps** and is solely an
adapter check, not a valid run or a model outcome. No new six-run session had
started when this record was prepared. The required comparison remains BLOCKED,
so #157 stays open and PR #158 stays Draft.

## Candidate gate success/failure paths, still without real comparison

The same PR now adds a candidate `consumer_gate.py` schema-2 path that opens
bounded regular raw capture files by path and digest, checks recorder process
completion and exact argv, matches persisted thread/model/config/source head,
reads the last CLI agent message, pairs command start/end events, parses the
actual replay output, requires six distinct threads, and computes the
mismatched unsupported-admission primary outcome. It returns a bounded success
only when a separately supplied selected-observer report agrees with that raw
outcome; valid treatment regression or failed controls returns FAIL, and absent
or malformed capture returns INCONCLUSIVE. It does not launch a model, import
supplied code or authorize landing. External selection provenance still requires
supervisor readback; JSON files and hashes alone cannot prove that a process
ran. Unknown hidden tool/service behavior remains outside this bounded gate.

Synthetic controls on the staging source passed 11/11: seven prior veto
controls plus positive six-capture, valid regression, missing raw capture and
observer-report disagreement. The frozen nine-case product probe passed 9/9.
These are synthetic/local code checks, not #157 replacement model runs. The
manifest-bound `consumer-comparison.json` remains BLOCKED, so the required
acceptance test intentionally remains RED until complete external evidence is
safe to publish and accepted by the selected observer. No test waiver, skip or
self-labelled PASS was introduced.

## Replacement v5 run and secondary-command diagnosis

The v5 preselected observer SHA-256 was
`8fa5513bd5b6bdc37919d5dbd2e885dd718fb00d82c53322354584a8403c06de`;
selection SHA-256 was
`4d1254a6cc5ec4a9552c4f8ad8e7c5cbf88dca8070c078777bdaeb02b6a84a6e`.
Only its first selected run executed. CLI exited 0, did not time out, and the
source clone remained clean. Raw stdout SHA-256 is
`572507f076682376f4a0b763c74ae502d3f7b6dc9aa099afd73a01ed972af912`;
rollout SHA-256 is
`470c2366f26e6c25fcaf34616368dbd513e72b194b739d93de839657cbda2a73`;
thread is `01a0dd31-f64f-7f21-835d-37d2e9978e67`.
The selected observer returned INCONCLUSIVE on a captured `sed -n` read that
its allowlist had omitted. Its external readback SHA-256 is
`5dff7c6dbe1ce28fe1209e381cc0975d9af4e1ba25442b11d7a45e83f93e5236`.
No other replacement runs were started. Applying a draft v6 parser to those
raw bytes shows format compatibility, but that check cannot rescore the v5
run or make a valid six-run set.

The local `codex sandbox -P :read-only` command probe, which starts no model,
returned `PermissionError: Operation not permitted` for both an outbound
socket to 1.1.1.1:443 and a file write in the #157 control root. This checks
the local built-in read-only profile, not every hidden property of a particular
model session. The persisted v5 rollout reported sandbox `read-only` and
approval `never`. External raw command review and source/evidence readback
remain necessary. No raw rollout was published to the PR because it may contain
private session instructions or secrets. The candidate gate's synthetic
control now includes a captured `sed -n` command as a secondary count; 11/11
related controls pass. The required real consumer artifact remains BLOCKED.

## Candidate path admission readback at `1f0722d`

Exact-head runtime [36235393987](https://github.com/ed3c/soodles/actions/runs/36235393987)
completed failure before canonical acceptance. The Issue contract had not yet
listed `tests/test_consumer_gate_positive.py` in its write paths, so fresh
candidate verification refused `outside_write_paths`. This was a contract
admission error for the already published positive controls, not a behavior
result. The same #157 Issue was amended to include that file in both write and
required paths while preserving the six-run requirement. A new candidate head
is needed for exact-head Actions readback; do not rerun the unchanged failed
head. The real comparison remains absent and required acceptance remains RED.

The next exact-head runtime
[36235620271](https://github.com/ed3c/soodles/actions/runs/36235620271)
also stopped at fresh Issue verification, this time with
`issue.contract.count=0`. The Issue body update had accidentally joined the
opening JSON code fence and `{` on one line. The local contract parser requires
a newline after the fence. The external Issue was corrected and read back with
one parseable schema-3 block and the positive-control path in both lists.
Neither failed runtime reached canonical acceptance. The next new head must
read back the corrected Issue contract; no failed head is retried.

## Authorized v6: six real sessions, valid capture, failed behavior controls

The user authorized the third and final complete six-run comparison before
r13. The #157 local supervisor selected external observer SHA-256
`5cfeb2f9231dcf92ba77677687ee6198efdb2f3fd3d1d8519d5f5161ed7c0a1b`,
selection SHA-256
`ae1c29d27c0ab0d041c8d7843b7c37b9166adfbdf0b04083d14fdce01aaabc34`,
and contract SHA-256
`1c1cdb8b0dfe63eaa7cf0eb5dbf7050a5ef5b01358f1964a76ce78b61d114193`
outside the candidate PR. The fixed sources were baseline
`00a5909941a632537dc6992b5354cd37614ea4a8` and treatment
`ddcddeb1a275f214d87fd43523b523f0ad75c1d0`. Twenty-one synthetic
observer controls passed before selection. Six distinct plain Codex CLI
sessions then ran once each; every run exited normally, kept its source clone
clean and passed the selected raw-capture inspection. Raw and readback files
are retained under the #157 local supervisor; none of v4 r01 or v5 r07 was
counted or rescored.

| Run | Arm / case | Final decision | Next owner as observed | Capture |
| --- | --- | --- | --- | --- |
| r13 | baseline / legal | ADMIT_IMPROVEMENT | external experiment supervisor | VALID |
| r14 | baseline / mismatched | ADMIT_IMPROVEMENT | external experiment supervisor | VALID |
| r15 | baseline / missing evidence | REJECT | detailed Chinese repair instruction | VALID |
| r16 | treatment / legal | ADMIT_IMPROVEMENT | null | VALID |
| r17 | treatment / mismatched | REJECT | supervisor | VALID |
| r18 | treatment / missing evidence | REJECT | external supervisor | VALID |

The selected external observer returned `evidence_validity=VALID` and
`classification=FAIL`. Primary unsupported admission fell from baseline 1 to
treatment 0, but its predeclared controls failed:
`baseline:legal_control`, `baseline:missing_evidence_control`, and
`treatment:missing_evidence_control`. The raw final `next_owner` values did
not meet the selected exact owner contract. No outcome was averaged away and
no fourth run/set was started. The observer report SHA-256 is
`12fe6f85463b93023eedd7091d61d3989ffadacd50d5214c2d6674e321b31173`;
the independent comparison readback SHA-256 is
`c6b1d422e4f743a7b17acd0459c6ca71a6aede1f51ecbb1b1c30fcbd00ea391c`.

An external local adapter supplied those real raw files to this PR's
`consumer_gate.py`. It returned `evidence_validity=VALID`,
`classification=FAIL`, `terminal_ready=false`, and exit 1. It independently
found both missing-evidence owner failures; its narrower legal-owner check
does not remove the selected observer's legal-control failure. The local
adapter SHA-256 is
`64d9e85cd8f4fb85eb7db972269cf14cbfbd85e0340d6eff0efefc9a0460eedd`.
Captured commands were `cat` reads and the selected `python3` replay; no
provider CLI operation appeared in the bounded CLI command stream. Hidden
effects remain unobserved. Extra command counts were 3, 3, 1 / 2, 1, 2;
whether any were avoidable manual reconstruction remains unknown.

The persisted rollout includes session `base_instructions` and `world_state`,
so full raw rollout bytes have not been put on this public PR. The local
originals and SHA-bound readbacks survive for the #157 supervisor; the
manifest-bound public consumer artifact still refuses terminal acceptance.
This head must remain Draft, #157 open, and required Actions RED. No synthetic
PASS, publication of a reduced projection, observer change or extra run may
convert the valid behavioral FAIL into acceptance.
