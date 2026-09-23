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
