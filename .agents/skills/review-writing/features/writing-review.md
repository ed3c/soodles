# Writing review

## Sub-features

Review sentence clarity, instruction routing, reasoning, and preservation of meaning.
Apply these criteria to the requested passage:

| Criterion | Accept when | Report a defect when |
| --- | --- | --- |
| Purpose and scope | The reader can identify the task and its limits. | A rewrite omits an outcome or adds an unrequested obligation. |
| Actor and action | Each instruction names its actor or clearly addresses the reader. | The reader must guess who acts or what changes. |
| Sentence load | Each sentence gives one instruction or explains one idea. | Separate actions, conditions, or claims compete in one sentence. |
| Conditions | The condition appears before the affected action. | The reader must act before learning whether the step applies. |
| Terms and references | A concept uses one term. Necessary terms and pronouns have clear meanings. | A synonym, noun string, or unclear pronoun changes the possible interpretation. |
| Decision | Each applicable route states its trigger, input, and action. | The reader must infer a command or skill from vague routing language. |
| Reasoning | The claim follows from stated premises and available evidence. | An assumption becomes a fact, or the conclusion exceeds the evidence. |
| Preservation | The change keeps the required outcomes, facts, conditions, and authority boundaries. | Simpler wording changes a requirement, certainty, actor, or permitted effect. |

Sentence length is a review cue, not a verdict.
For English, inspect instructions over about 20 words and other sentences over about 25 words.
These are practical pstack writing guidelines, not a formal compliance test.
For other languages, review clause structure instead of applying English word counts.
Keep a necessary longer sentence if splitting it makes its meaning less clear.

## How to get to it (user POV)

The user names a document, passage, or writing defect.
For example, use `review-writing` to correct the new engineering principles in `AGENTS.md`.
If the passage is clear from the task, proceed without asking the user to select it again.

## Driving it with file tools

1. Read the current passage and the user's required outcome.
2. Save the original text and identify material that must remain exact.
3. Apply the criteria above. Record concrete findings before revising.
4. If editing is authorized, correct each supported defect within scope.
5. Read the saved file again. Do not rely on the replacement text in the edit request.
6. Compare the saved text with the original and the findings.
7. Review nearby references for contradictions introduced by the change.
8. Record the outcome and retain the evidence.

For an incorrect inference, state the original claim and its premise.
Identify the evidence and the point where the conclusion stops following from it.
Then state the supported conclusion and the required action.
If evidence is insufficient, record the gap instead of inventing a correction.

During readback, compare each actor, condition, negation, obligation, and uncertainty.
Check commands, identifiers, link targets, quotations, and factual values against the original.
Keep logs, receipts, and fixed snapshots unchanged.
If the task requires a factual correction, retain the original and cite the supporting source.
Do not preserve a false claim merely because its wording is unchanged.

The prose review is complete when each finding has a supported disposition and saved readback.
For P-class completion, also consume the [behavior feedback](pclass-feedback.md).
Unresolved defects produce `incomplete`, even when the text reads more smoothly.

## Gotchas

A short sentence can still contain an unsupported claim.
An explicit actor can still lack authority to perform the action.
A successful diff check does not establish either clarity or factual accuracy.
This review supplies no runtime, Agent-comparison, or landing evidence.
For N-class prose, an unclear sentence does not request evals.
For P-class writing, the behavior feedback procedure defines the required scope.
Use existing source and logs first when the question concerns product behavior.
