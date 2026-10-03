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
| Zero context | Each algorithm or design choice follows from explicit problem constraints. The reader can trace what happens at runtime. | The text names a choice without explaining its cause, or describes an outcome without actors and state changes. |
| Acceptance boundary | Acceptance, rejection, and unknown conditions follow from the original requirement and evidence. | The reviewer invents a condition, weakens the outcome, or calls ambiguity subjective without examining its premises. |
| Preservation | The change keeps the required outcomes, facts, conditions, and authority boundaries. | Simpler wording changes a requirement, certainty, actor, or permitted effect. |

Sentence length is a review cue, not a verdict.
For English, inspect instructions over about 20 words and other sentences over about 25 words.
These are practical pstack writing guidelines, not a formal compliance test.
For other languages, review clause structure instead of applying English word counts.
Keep a necessary longer sentence if splitting it makes its meaning less clear.

## Explain a decision with zero context

For each algorithm or design choice in the reviewed scope, explain these links:

1. State the required outcome and the constraints that affect this choice.
2. Identify the supporting source or observation. Name any unverified premise.
3. Explain why the choice meets the constraints. Compare a relevant simpler
   alternative when one exists. If it meets the same constraints, prefer it.
4. Trace the runtime actor, input, check, state change, effect, and failure path.
   Mark a proposed path as proposed. Source inspection does not prove execution.
5. Derive observable acceptance, rejection, and unknown conditions from the requirement.

Scale this explanation to the decision. A short paragraph can cover a simple choice.
Do not create an exhaustive alternatives survey, a new form, or a runtime check.
Zero context requires the causal explanation. It does not mean removing necessary
inputs or merely summarizing the conversation.

If semantic acceptance appears to require a product decision, first clarify the
requirement, ambiguous term, premise, and conflicting interpretations in writing.
Use existing evidence to determine which interpretation the constraints support.
Do not use "subjective" as a substitute for this work or as a reason for handoff.
If the evidence resolves the issue, make the authorized correction and continue.
Otherwise, identify the exact conflict or missing premise and its responsible owner.
Do not invent a fact, alter the requested outcome, or infer new authority.

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
Follow the saved explanation from constraints through the choice to runtime behavior.
Check that each acceptance condition follows from that chain. Look for a counterexample
that satisfies the stated premises but invalidates the conclusion.
If the text claims an actual effect, check its source-bound execution evidence.
An Agent's report alone does not prove an external effect.
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
