# Issue 199: committed system-v1 context selection

The fixed external product observer reports **PASS** at implementation head
`9d2c6a8df6b3296a995d478293e0f24c14a31143`. Its complete JSON stdout, including
actual subprocess argv, exit codes and output, is in `product-results.json`.
It was invoked with the externally supplied `product_oracle.py` and
`frozen-files.json`, not the candidate copy of the observer. All 15 frozen
paths in the admitted Issue contract match their selected SHA-256 values.
The later evidence commit binds these unchanged implementation bytes; this
receipt does not claim execution against that later head or Linux acceptance.

The baseline is `0977f2513130e8a38c53665f71c8e90f3ac9c614`. The old resolver's
actual whole-file projection is archived in `behavior.tar.gz` as
`baseline-projection.json`: 45,657 UTF-8 bytes, SHA-256
`554564a5ab10ba9be434baccd4528f700096424470d3022352f77bde76759ab7`.
Selecting `contracts/system-v1/instruction-context.md` now supplies just
`common.md` and `instruction-context.md`, totaling **3,450 content bytes**.
The frozen behavior packets concatenate those exact files with one additional
newline, so their recorded context size is **3,451 bytes**. These are byte
measurements of supplied content; neither measures tokens, model cost, hidden
context loading, or general Agent efficiency.

## Product boundary and controls

`system-context` reads routes and instruction files from one captured committed
HEAD. It validates the fixed filename vocabulary and the entire prerequisite
graph, computes a deterministic dependency-first AND closure, derives actual
Git-byte digests, and delegates regular-file, UTF-8, bounds and digest checks
to `issue_admission.resolve_instruction_context`. Shared prerequisites appear
once. Refusals contain invalid field/value and an owning input; they emit no
ready context or guessed continuation argv. No authorization/envelope/provider
schema or runtime transition owner changed.

The final eleven focused unittest cases passed in 17.045 seconds using disposable committed Git fixtures and
the actual wrapper. They cover exact source identity/content/pins, independent
and shared roots, input-order stability, dirty route/content non-consumption,
traversal/unknown/empty roots, whole-graph cycles and dangling edges, duplicate
JSON keys at each object depth, malformed graph records, committed symlinks,
directories, missing/non-UTF-8 files, and changed committed digests versus stale
pins, non-JSON numeric constants and deeply nested JSON. Every CLI observation compares Git status before and after, including
untracked files. Existing frozen history tests were left unchanged.

The first full run executed 526 tests in 272.592 seconds and returned
`FAILED (failures=10, errors=4)`. All failures were in
`test_candidate_publication`, `test_context_recording`,
`test_landing_continuation`, and `test_quality`. Their fixtures compared
unresolved `/var/folders/...` temporary paths with canonical
`/private/var/folders/...` paths. One isolated publication test reproduced the
same assertion. Re-running these four modules with `TMPDIR` set to
`str(Path(tempfile.gettempdir()).resolve())` passed all 29 tests in 10.399 seconds.
No test or product source was changed to hide these failures.

Eval-audit of this additional observation distinguishes fixture/carrier identity
from selector behavior: the traceback records path-key/equality failures,
canonical-path controls pass, and the same fixed product observer passes.
The frozen Agent evidence is unchanged; these test-environment observations
supply no new Agent-behavior or routing-improvement claim. The combined
context claim remains bounded by the archived confirmation and its limitations.

The second complete run used the same canonical TMPDIR and passed **526 tests
in 250.750 seconds**. Its full log is `/tmp/soodles-199-canonical-unit-tests.log`,
SHA-256 `5e8973e1a33ab4645285ec72292a69acda13a2d4f775086d29f047b047fd8ac7`. The full suite had already discovered its 526
tests when the defensive JSON guard was added; the final focused run separately
passed all **11** selector tests, including that additional portable refusal
control. The fixed external product observer then passed on the committed final
implementation head. The unit runs used macOS; Linux canonical acceptance was
not launched. These checks confer no publication or landing authority.

## Frozen consumer evidence

The supervisor supplied `protocol.md`, `oracle.py`, `frozen-files.json`,
`behavior.tar.gz`, and `behavior-summary.json`; they were copied unchanged.
The archive includes initial read requests/results/stdout/stderr, consumer
packets and answers, the original whole-file resolver capture, qualified
objective decision controls, expected decisions, protocol pins and the scoped
eval audit. The packet tasks are identical within each baseline/treatment pair.

| Pair | Baseline | Treatment | Supported interpretation |
| --- | --- | --- | --- |
| Selection | INCONCLUSIVE | PASS | Baseline consumer reported truncation; no matched improvement verdict |
| Independent confirmation | PASS | PASS | Scoped nonregression on the supplied-versus-followed distinction and body amendment/full-contract rules |

The original selection baseline remains **INCONCLUSIVE** even though its raw
subprocess stdout was complete. The outer tool-output budget was default and
the consumer explicitly reported truncation. The separate confirmation pair
used the archived 22,000 output budget. A complete local subprocess capture
does not prove all bytes reached the consumer's model context.

Fresh consumers were recorded by the supervisor with no inherited conversation.
The archive supports only its scoped initial read and response; it is not a
complete platform transcript or proof of storage-access isolation. Observed
model identity and token telemetry are null/unknown. Neither fresh threads nor
smaller packets prove hidden isolation, universal nonregression, or adherence
beyond the concrete observed answers. Exact context supply remains distinct
from behavior. The complete admitted structured contract remains required, and
an amended Issue body still requires the supervisor's fresh envelope.

## Eval audit and causal assessment

Method: the installed `eval-audit/SKILL.md`, SHA-256
`c11338900d88d114c353a8865d9b7a4780d972bf740b80d5eb4e38357b1bf133`, matching
the supervisor's archived `protocol-pins.json`. This assessment inspected the
fixed product observer, raw packets/answers, original projection, qualification
controls and summary, without editing or rescoring the supervisor evidence.

- **Error analysis — observed:** the existing whole-file resolver faithfully
  supplies 45,657 bytes for this boundary; the selection consumer reported a
  truncated initial read. File granularity is the reproduced product condition.
  It does not establish a historical Agent failure rate.
- **Evaluator design — bounded:** frozen section hashes and real subprocess
  checks measure exact supply and selection. Disposable Git tests discriminate
  invalid graphs/types and dirty checkout reads. Byte reduction cannot serve
  as a behavior score; retain the separate confirmation result.
- **Judge validation — objective:** no LLM judge is used. Archived qualification
  plants negatives for the eleven concrete decision fields across two groups.
  This supports those fields only, not general semantic correctness.
- **Human review — limited capture:** raw reads and answers permit inspection,
  but the archive is not a full platform transcript or a blinded study. Retain
  the missing-capture limits instead of upgrading the selection baseline.
- **Labeled data — limited:** four consumers support a smoke comparison and a
  separate confirmation pair, not a population estimate. Do not infer broad
  effectiveness or token savings from these observations.
- **Pipeline hygiene — fixed:** protocol, treatment, oracle and raw evidence
  predate this writer and retain their supplied digests. No new sampling,
  replacement authority or changed scores were introduced by the candidate.

The shortest P-class path is the frozen contract index to the explicit boundary
and its prerequisites. The CLI owns committed identity, graph validation and
refusal. The existing admission resolver remains unchanged, supported by its
exact-byte/digest controls and the frozen product observation; the fresh
confirmation supports only the named instruction decisions. This combined
document/selector correction does not attribute general Agent improvement to
either component.

## Typed stage outcome capability

The actual running parent process identifies the selected binary as
`/Users/neon/.codex/experiments/soodles133-bootstrap.QpepPK/noodle-source/bin/noodle`.
The PATH binary at `/Users/neon/.local/bin/noodle` is different and was not
selected for emitting an outcome. The selected binary's `event emit --help`
exposes only generic `event emit <type>`, `--payload`, and `--session`.
Its `schema list` exposes only `mise`, `orders`, and `status`; inspecting the
public status/orders schemas provides no typed outcome payload. Consequently
no completed or blocked event has been guessed or emitted. The admission/runtime
owner must supply the selected typed outcome schema or its formal read-only
query entry before this writer can perform that stage effect.

The actual runtime identity is session
`soodles-199-a017ded6cee8-0-execute-20260930-144905-41f649`, order
`soodles-199-a017ded6cee8`, stage `0`. The identity and candidate are preserved.
This is a stage-reporting capability gap, separate from product verification
and publication/landing readiness.

## Review and remaining owners

The complete baseline-to-candidate `git diff --check` flags trailing blank
lines in the frozen index and seven extracted files: candidate, common,
issue-atom, landing, readback, recovery and runtime. These bytes are retained
to preserve the externally selected exact file digests. No authored-code
whitespace errors were reported.

Native publication readiness, exact-head Linux Actions acceptance, provider
publication/merge/closure/main readback and Git/Noodle reconciliation remain
with their existing owners. None is claimed here. No push, publication, merge,
Issue closure or control-root source modification was performed by this writer.
All experiment receipts have `authorizes_landing: false`.

## Preserved initial suite diagnostics

Full original log: `/tmp/soodles-199-unit-tests.log`, SHA-256
`a86ae1f947d7740afd74ac3de62dc66fb11c7114f756986cda63e2080db8ad0e`.
The following error/failure diagnostics and aggregate result are copied verbatim.

<details>
<summary>Initial macOS temporary-path failures</summary>

```text
======================================================================
ERROR: test_instruction_bindings_require_valid_metadata (test_context_recording.ContextRecordingTests.test_instruction_bindings_require_valid_metadata)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_context_recording.py", line 148, in test_instruction_bindings_require_valid_metadata
    valid = request['files_before'][str(instruction)]
            ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
KeyError: '/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/tmp27fjuo3b/AGENTS.md'

======================================================================
ERROR: test_records_real_nonzero_and_file_change_without_inventing_success (test_context_recording.ContextRecordingTests.test_records_real_nonzero_and_file_change_without_inventing_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_context_recording.py", line 51, in test_records_real_nonzero_and_file_change_without_inventing_success
    self.assertNotEqual(before[str(path)]['sha256'], result['files_after'][str(path)]['sha256'])
                        ~~~~~~^^^^^^^^^^^
KeyError: '/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/tmpq8g8qhd0/state'

======================================================================
ERROR: test_snapshot_error_after_effect_preserves_result (test_context_recording.ContextRecordingTests.test_snapshot_error_after_effect_preserves_result) (shell=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_context_recording.py", line 103, in test_snapshot_error_after_effect_preserves_result
    self.assertEqual(request['files_before'][str(path)]['bytes'], len(b'before'))
                     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
KeyError: '/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/tmpgphiz5qq/state'

======================================================================
ERROR: test_snapshot_error_after_effect_preserves_result (test_context_recording.ContextRecordingTests.test_snapshot_error_after_effect_preserves_result) (shell=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_context_recording.py", line 103, in test_snapshot_error_after_effect_preserves_result
    self.assertEqual(request['files_before'][str(path)]['bytes'], len(b'before'))
                     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
KeyError: '/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/tmpdjdezxk6/state'

======================================================================
FAIL: test_amendment_keeps_exact_pr_and_uses_old_head_lease (test_candidate_publication.CandidatePublicationTests.test_amendment_keeps_exact_pr_and_uses_old_head_lease)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 158, in test_amendment_keeps_exact_pr_and_uses_old_head_lease
    prior, acceptance, claim = self.amended_candidate()
                               ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 146, in amended_candidate
    prior = publication.publish(self.root, self.acceptance, self.claim,
                                self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_amendment_refuses_foreign_branch_and_pr_before_push (test_candidate_publication.CandidatePublicationTests.test_amendment_refuses_foreign_branch_and_pr_before_push)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 215, in test_amendment_refuses_foreign_branch_and_pr_before_push
    prior, acceptance, claim = self.amended_candidate()
                               ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 146, in amended_candidate
    prior = publication.publish(self.root, self.acceptance, self.claim,
                                self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_amendment_refuses_unoffered_or_unknown_write_without_retry (test_candidate_publication.CandidatePublicationTests.test_amendment_refuses_unoffered_or_unknown_write_without_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 202, in test_amendment_refuses_unoffered_or_unknown_write_without_retry
    prior, acceptance, claim = self.amended_candidate()
                               ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 146, in amended_candidate
    prior = publication.publish(self.root, self.acceptance, self.claim,
                                self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_creates_exact_branch_and_pr (test_candidate_publication.CandidatePublicationTests.test_creates_exact_branch_and_pr)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 129, in test_creates_exact_branch_and_pr
    result = publication.publish(self.root, self.acceptance, self.claim,
                                 self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_failed_push_is_adopted_only_after_exact_readback (test_candidate_publication.CandidatePublicationTests.test_failed_push_is_adopted_only_after_exact_readback)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 247, in test_failed_push_is_adopted_only_after_exact_readback
    result = publication.publish(self.root, self.acceptance, self.claim,
                                 self.provider, push=self.push(result=1))
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_lost_create_response_adopts_only_fresh_exact_readback (test_candidate_publication.CandidatePublicationTests.test_lost_create_response_adopts_only_fresh_exact_readback)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 233, in test_lost_create_response_adopts_only_fresh_exact_readback
    result = publication.publish(self.root, self.acceptance, self.claim,
                                 self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_native_readiness_can_publish_but_never_authorizes_landing (test_candidate_publication.CandidatePublicationTests.test_native_readiness_can_publish_but_never_authorizes_landing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 288, in test_native_readiness_can_publish_but_never_authorizes_landing
    result = publication.publish(self.root, self.native_receipt(), self.claim,
                                 self.provider, push=self.push())
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_unknown_create_without_effect_refuses_without_retry (test_candidate_publication.CandidatePublicationTests.test_unknown_create_without_effect_refuses_without_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 242, in test_unknown_create_without_effect_refuses_without_retry
    publication.publish(self.root, self.acceptance, self.claim,
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        self.provider, push=self.push())
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/candidate_publication.py", line 363, in publish
    result = push(root, "push", "--porcelain",
                  "--force-with-lease=refs/heads/" + branch + ":",
                  claim["push_remote"], claim["head"] + ":refs/heads/" + branch,
                  check=False)
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_candidate_publication.py", line 122, in operation
    self.assertEqual(Path(root), self.root)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[52 chars]ate') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[44 chars]ate')

======================================================================
FAIL: test_current_argv_is_executable_without_weakening_readback_guards (test_landing_continuation.LandingContinuationTests.test_current_argv_is_executable_without_weakening_readback_guards)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_landing_continuation.py", line 17, in test_current_argv_is_executable_without_weakening_readback_guards
    self.assertEqual(report['evaluation']['safety'], 'PASS', report['evaluation'])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'FAIL' != 'PASS'
- FAIL
+ PASS
 : {'safety': 'FAIL', 'safety_failures': ['start:checkpoint_binding', 'prepare:checkpoint_binding', 'merge_offer:checkpoint_binding', 'unknown_merge:checkpoint_binding', 'stale_dispatch:checkpoint_binding', 'missing_merge_commit:checkpoint_binding', 'repair_merge_commit:checkpoint_binding', 'close_offer:checkpoint_binding', 'unknown_close:checkpoint_binding'], 'projection': 'RED', 'projection_failures': ['start:readback_binding', 'start:argv', 'prepare:readback_binding', 'prepare:argv', 'merge_offer:readback_binding', 'merge_offer:argv', 'unknown_merge:readback_binding', 'unknown_merge:argv', 'stale_dispatch:readback_binding', 'stale_dispatch:argv', 'missing_merge_commit:readback_binding', 'missing_merge_commit:argv', 'repair_merge_commit:readback_binding', 'repair_merge_commit:argv', 'close_offer:readback_binding', 'close_offer:argv', 'unknown_close:readback_binding', 'unknown_close:argv'], 'bound_continuation_available': False}

======================================================================
FAIL: test_exact_same_head_allowed_but_output_inside_subject_refused (test_quality.QualityTests.test_exact_same_head_allowed_but_output_inside_subject_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_quality.py", line 30, in test_exact_same_head_allowed_but_output_inside_subject_refused
    self.assertEqual(measure.preflight(ROOT, head, head, out), out)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PosixPath('/private/var/folders/l6/44bf7nvs64j60f1mpy[30 chars]ort') != PosixPath('/var/folders/l6/44bf7nvs64j60f1mpyy88hdm00[22 chars]ort')

----------------------------------------------------------------------
Ran 526 tests in 272.592s

FAILED (failures=10, errors=4)
```

</details>

## Additional focused-control diagnostic

A new nesting control initially overconstrained the invalid field to
`routes.json`. Python 3.14 parsed that depth and correctly returned the
structured `routes.fields` refusal. The corrected portable control requires
a structured refusal in either case; it does not modify the fixed observer
or frozen consumer scores. Non-JSON numbers still require `routes.json`.

Original focused log SHA-256: `54ff1d7e0fa969b6d4471bafcc6547d46c3f9aa9ab71fa032b27e83722f0ab2e`.

```text
======================================================================
FAIL: test_non_json_numbers_and_excessive_nesting_refuse_as_json (test_system_context.SystemContextTests.test_non_json_numbers_and_excessive_nesting_refuse_as_json)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_system_context.py", line 192, in test_non_json_numbers_and_excessive_nesting_refuse_as_json
    self.refused(CONTEXT, field="routes.json")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/neon/.codex/worktrees/atom-context-slice/soodles/.worktrees/soodles-199-a017ded6cee8-0-execute/tests/test_system_context.py", line 79, in refused
    self.assertEqual(value["invalid"]["field"], field)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'routes.fields' != 'routes.json'
- routes.fields
+ routes.json


----------------------------------------------------------------------
Ran 11 tests in 17.801s

FAILED (failures=1)
```
