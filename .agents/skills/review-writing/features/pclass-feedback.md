# P-class behavior feedback

## Scope and method

Use this procedure for every P-class writing result in the requested scope.
Review the saved prose first. Name the behavior that its consumer must preserve.
Select cases for the affected decisions and their distinct failure boundaries.
Group files that govern the same behavior. Do not launch one eval per file.
An unchanged instruction and covered task may reuse its bound observations.
A changed instruction needs evidence for its saved bytes.

Load the applicable installed evals skill. Use `eval-audit` to inspect an existing
pipeline. Use `error-discovery` for unclassified traces. Use `evals-start` when
the needed method is unknown. Record the actual method files and their digests.
Use objective checks for structured decisions. If a judgment requires semantic
interpretation, use `write-judge-prompt` and `validate-evaluator`. Missing human
labels or judge calibration remain evidence gaps. Do not invent ground truth.

This procedure verifies observed behavior for selected tasks. It does not claim
that wording caused an improvement. A comparative claim needs the selected
[comparison procedure](../../verify-soodles/features/pclass-context.md).
The Test Manager retains software test scope. No full suite is implied.

## Prepare the evidence

The supervising Agent prepares the files. Do not ask the user to create hashes.
Keep them in the existing external task evidence directory.
A file reference has exactly two fields:

```json
{"path": "/absolute/path/to/file", "sha256": "64 lowercase hexadecimal characters"}
```

Schema 1 remains a read-only comparison format. It has no condition-review claim.
For an admitted writer, use schema 2 as described below.
Before observing consumers, save a protocol with these fields:

| Field | Value |
| --- | --- |
| `schema` | Integer `1`. |
| `subject` | The scoped behavior claim. |
| `instructions` | Nonempty list of file references for the saved P-class instructions. |
| `methods` | Nonempty list of file references for the applied evals methods. |
| `cases` | Nonempty list of objects with `id`, `input`, and `expected`. |

Each case ID uses letters, digits, underscores, or hyphens. It must be unique.
`input` references the task file. `expected` maps output field names to expected
JSON values. Schema Manager compares these values exactly, including their types.
Keep the protocol and expected values with the supervisor. Give each consumer
only its task, selected instructions, required inputs, and its output location.

Within existing delegation authorization, use fresh native consumers without
inherited conversation. Each consumer writes only to its own evidence directory.
Record actual requests, results, available carrier identity, and elapsed time.
If the carrier cannot expose a complete transcript, record that limit.
Do not replace the selected carrier to hide a missing capability.

For each case, preserve a consumer report with these fields:

| Field | Value |
| --- | --- |
| `schema` | Integer `1`. |
| `case_id` | The selected case ID. |
| `instructions` | Object mapping each selected instruction path to its SHA-256. |
| `input_sha256` | SHA-256 of the selected task file. |
| `output` | The consumer's actual structured response. |

Also retain the raw response or available execution capture in a separate file.
Do not replace an incorrect response with the expected value.
The supervisor binds each observation with `case_id`, `report`, and `trace`.
The last two fields are file references.

Save a selection with exactly `schema`, `protocol`, and `observations`.
Use integer `1` for `schema`, a file reference for `protocol`, and a list for
`observations`. An empty list represents missing observations. Compute the
selection's SHA-256 after saving it.

## Submit and read back

Use the existing public CLI:

```text
./soodles schema pclass-feedback /absolute/selection.json EXPECTED_SHA256
```

Preserve stdout, stderr, exit code, and timing from this normal invocation.
Read `evidence_validity` before `behavior`.

| Response | Required action |
| --- | --- |
| `VALID` and `PASS`, exit `0` | The task owner consumes `next.operation=consume_verified_behavior`. Record the covered result and remaining limits. No additional eval is required for the same claim and evidence. |
| `VALID` and `FAIL`, exit `1` | `review-writing` examines the failed fields and actual capture. Correct the demonstrated instruction defect. If the protocol is wrong, preserve that result and select a corrected protocol before new observations. |
| `INCONCLUSIVE`, exit `2` | Supply the evidence named by `next.required`. Keep behavior unknown. Continue independent work. |
| `INVALID`, exit `2` | Repair the named identity or format problem. Preserve the refused input and response. Do not score invalid evidence. |

After a correction, re-read the saved instructions. Bind the new bytes and obtain
observations for the affected decisions. Submit them and consume the new response.
Do not replay an unchanged failed observation or expand to a full test suite.
If a required capability is missing, record the prerequisite and keep that claim
incomplete. Do not turn missing evidence into a pass or a product failure.

The response includes source references, per-field checks, a dependency graph,
and the next responsible owner. `elapsed_ms` measures reading, validation, and
projection inside Schema Manager. `projection_ms` measures the decision projection.
These values exclude model time and process startup. Keep those costs separate.
The existing CLI timing log records the operation. Do not add benchmark loops.

The task owner records the response file and digest, the returned action, the
action taken, and unresolved gaps in the review record. This readback completes
the feedback path. A report that no owner consumes leaves the path incomplete.

## Limits and controls

Schema Manager checks file identity and reported output fields. Digests do not
prove independence, full trace capture, or absence of unobserved effects.
Its `observation_scope` is `consumer_report`. A pass supports only that scope.
The observer must review the capture for contradictions before using the result.
A style review remains necessary. Structured response checks do not judge all prose.

The command reads data. It does not launch models, execute tests, repair files,
change runtime, or call a provider. `authorizes_landing` is always `false`.
`effects` stays empty and `test_demand` stays null. Existing owners retain authority.
Do not register arbitrary evaluator code or a second scheduler here.

The nearest controls are in `tests/test_pclass_feedback.py`. They exercise the
public CLI with small files. They cover passing and failed behavior, missing
observations, changed identities, duplicate cases, malformed input, and typed
value comparison. They do not provide fresh Agent behavior evidence.


## Continue inside the original Noodle session

Use this route when Noodle has admitted the writer and its session is running.
It uses the same worktree, admission, order, session, and Noodle event writer.
It does not dispatch a second writer or migrate a stopped session.

Use schema 2 for both protocol and selection. Keep the schema-1 fields above.
Add `requirements` to the protocol. It references a JSON file with exactly
`task` and `contract`, copied from the validated stage prompt without alteration.
The adapter compares these values with the original admitted values.
Add `criteria_review` to the selection. Use null while its evidence is missing.
Otherwise, reference a review with exactly these fields:

- `schema`: integer `1`.
- `protocol_sha256`: digest of the selected protocol bytes.
- `reviewer`: the actual reviewing Agent or observer identity.
- `checks`: case IDs mapped to their expected output fields.

Each field check has `status`, `requirement_quote`, and `reason`.
Status is `supported`, `unsupported`, or `unknown`.
A supported condition needs an exact quote from the requirement file.
Its reason explains why the task input makes that expected result necessary.
The reviewing Agent reads the requirement, case, and available raw observations.
It checks omitted outcomes, contradictory inputs, and expectations with no premise.
Do not use a successful score as evidence that the condition is correct.
A quote and an Agent verdict provide scoped reasoning evidence, not formal proof.
For independent review claims, retain the actual fresh reviewer request and response.
A self-declared reviewer name does not prove independence.

If a condition lacks support, Schema Manager returns `review_criteria` without
scoring behavior. Preserve the original result. Correct a demonstrated protocol
error within the original requirement, then obtain a review bound to the new protocol.
Do not lower the user's requirement or replace a selected external acceptance judge.
If the requirement itself is ambiguous, retain that gap. Continue unrelated work.

Submit each prepared selection from the admitted worktree:

```text
./stage-outcome feedback /absolute/selection.json SHA256
```

The adapter derives owner identity. It does not accept an owner or budget flag.
It saves nonterminal feedback through Noodle's existing `stage_message` writer.
The event links its previous round, current source identities, Schema response,
Test Manager scope, and measured projection cost. The original event log owns history.
No additional mutable checkpoint or retry engine is created.

Read `next` and `feedback.test_scope` together. When criteria need review, obtain
that review first. When behavior fails, correct the demonstrated instruction defect.
When evidence is missing, supply the named observation. Test Manager lists matching
passed cases under `reuse`; carry their original report and capture references into
the next selection. It lists already passed current cases under `verified`.
Only `cases` requests further consumer observations. None requests a full software suite.
Schema Manager still requires complete selected evidence before PASS.

Continue these steps within the same authorized task. Do not wait for another
user prompt for an ordinary correction. An identical submission returns readback.
It does not append an event, consume another round, or request another model call.
Changed evidence may advance the next round. Replaying an earlier state refuses.
After three failed corrections, reassess the root cause in the same task.
An unsupported condition or a behavior FAIL counts as a failure.
Missing evidence and repeated readback do not consume a correction attempt.
The adapter can still read new passing evidence. It retains the failure history.
Do not reset that history, start a replacement writer, or rename inputs
merely to obtain another budget. Missing identity, authority, or capability remains
an owner prerequisite. A failed or unknown event write requires Noodle readback.

Before emitting `completed`, the adapter checks the latest result against current
file bytes and changed P-class paths. The result must have supported conditions
and valid passing behavior. `blocked` and `failed` remain available for actual stops.
Feedback events have no terminal outcome. Only the final stage outcome completes
this stage. Existing publication and landing owners retain their own requirements.
Legacy contracts retain their existing completion boundary unless they use feedback.

Normal CLI logs separate total adapter time from Schema validation and projection.
Test Manager includes the current projection cost in its decision. Missing model
usage remains unknown. Do not add benchmark rounds or sum nested durations.
The nearest owner controls are `tests/test_feedback_owner.py` and the existing
stage-outcome controls. Disposable owners establish local behavior only.
They do not establish live Issue delivery or restart of a stopped writer.
