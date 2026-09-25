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
