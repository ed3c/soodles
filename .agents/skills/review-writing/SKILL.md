---
name: review-writing
description: Own writing style for all Soodles P-class guidance. Review prose, verify covered Agent behavior with evals skills, and consume Schema Manager feedback. Also review requested N-class documents.
---

# Review writing

Use this skill whenever you write or revise P-class guidance.
This includes AGENTS, contracts, skills, recipes, and routing text.
For N-class documents, use it for a requested review or an observed writing defect.
Apply the writing principles in [AGENTS.md](../../../AGENTS.md).
This is an ASD-STE100-inspired review, not a formal compliance assessment.
Do not calculate a compliance percentage.

## Launch

Use the existing editor and file tools. The document is the review subject.
The prose review needs no application process or software test suite.
P-class completion also needs the scoped behavior feedback below.
Use the selected carrier within current authorization. Missing capability blocks
that measurement, not independent prose corrections.
Keep the user's requested language and editing scope.
For a review-only request, report findings without editing.

## Doctor

Read the selected file and its relevant instructions.
Check the diff for existing edits before changing a repository document.
Save the original text in an external task evidence directory before editing.
Identify commands, identifiers, links, quotations, facts, and fixed evidence.
If an input is missing, name it and continue independent review work.
Repeat an input check only when its bytes change or an observation contradicts it.

## Drive

Use the [writing review procedure](features/writing-review.md).
Review the requested passage and the nearby text needed to interpret it.
Do not expand a local review into a repository-wide rewrite.
Correct authorized defects, then re-read the saved file and its diff.
For a P-class result, follow the [behavior feedback procedure](features/pclass-feedback.md).
Use the applicable installed evals skill. Submit bound evidence to Schema Manager.
Consume its next action and record the result. Do not infer behavior from prose quality.
For a Noodle-admitted writer, use the existing stage-outcome feedback entry.
Continue the scoped repair in the same running session. Keep original requirements fixed.
Review disputed conditions against those requirements and actual observations.
The current Agent handles a supported correction without another user prompt.

## Evidence

Record the file, reviewed scope, original bytes, and saved result in the task record.
For each material finding, record the location, failed criterion, and reader impact.
After a correction, record its readback result and any remaining evidence gap.
Keep these records outside the repository unless the task requires committed evidence.

Report one outcome for the reviewed scope:

- `clean`: review and readback found no remaining supported defect.
- `changed`: authorized corrections passed review and readback.
- `incomplete`: a defect or required check remains unresolved. Name each one.

For P-class work, also record the covered behavior, selected evidence, Schema
Manager response, and action taken from that response. A clean prose review
alone leaves the P-class result incomplete. Missing or invalid evidence is not
a behavior failure. A valid failed observation requires correction.

An outcome covers only the named files and criteria.
It does not prove that another Agent will follow the instructions.
`git diff --check` checks whitespace. It does not check meaning or writing quality.

## Cleanup

Remove only temporary files created for this review that no longer serve a purpose.
Retain the original text, findings, and final readback.
Confirm that the retained evidence is readable before reporting completion.
This procedure starts no persistent process.

## Helpers

This skill ships no scripts. Use existing file tools and Git diff commands.
Do not replace semantic review with a sentence-length score or a keyword check.

## Maintenance

The [feature index](features/README.md) defines this skill's review scope.
When actual use exposes a gap, correct the affected instruction and repeat that review step.
Use the installed pstack maintenance skill when a maintenance pass is requested.
Its live subjects are the saved document, consumer behavior, and feedback response.
Reuse bound evidence when it still covers the saved result and requested claim.
A maintenance pass does not request every feature or a new comparative experiment.
Do not start Soodles runtime to verify prose.
The [Test Manager](../test-manager/SKILL.md) retains ownership of any requested software tests.
