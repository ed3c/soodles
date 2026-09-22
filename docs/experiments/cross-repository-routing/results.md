# Cross-repository routing result

## Claim

For the frozen Ops candidate, repository-owned routing and acceptance make the
legal next owner action executable without repository guessing. The result is
limited to this Soodles-to-Ops edge and the four observed cases.

## Frozen subject

- Repository: `ed3c/ops-reconciliation-copilot`
- Issue: `21`
- PR: `22`
- Candidate: `e3c530340aa8d8070206b0a893b9a9aef5e462d0`
- Tree: `f0a2032ef3f4f1195a8deaf35175b94e211607c3`
- Base: `24a56d18661630b0dba97dcb0b057dce07b0ab32`
- Run: `35217009263`, attempt `1`

PR 22 is currently draft. That live condition is represented as a positive
refusal; this experiment does not authorize its merge or Issue closure.

## Deterministic observer

The same subprocess observer ran against the baseline and treatment source.
The baseline rejected the otherwise legal Ops claim at `claim.repository`.
The treatment admitted that claim, returned six exact Ops GET requests and a
checkpoint-bound `landing advance` argv. It rejected the draft, missing
PostgreSQL step and unsupported repository cases before a checkpoint was
created.

| Measure | Baseline | Treatment |
|---|---:|---:|
| Legal Ops route available | 0 | 1 |
| Exact repository GETs returned | 0 | 6 |
| Negative cases rejected at discriminating field | 1/3 | 3/3 |
| Sensitivity plants rejected | n/a | 5/5 |
| Provider requests executed | 0 | 0 |
| Provider writes executed | 0 | 0 |

## Independent consumers

Three fresh consumers per arm selected a next action only from the frozen task,
arm-specific instructions and raw observer output.

| Measure | Baseline | Treatment |
|---|---:|---:|
| Legal route available | 0/3 | 3/3 |
| Wrong routes | 0 | 0 |
| Repository guesses | 0 | 0 |
| Median instruction reads | 3 | 2 |

The baseline consumers safely stopped, so wrong-route count did not improve.
The measured hill climb is the removal of the deterministic legal-route
barrier while preserving refusal behavior. These receipts do not establish a
general reduction in Agent decision cost, provider latency or dependency
satisfaction.

## Boundary

The correction owns repository identity propagation, source-owned acceptance
profiles, exact readback URLs and executable continuation. Cross-repository
dependency satisfaction remains a separate atom: Issue closure or released
resources do not prove that a required revision, artifact or migration is
available to a consumer.
