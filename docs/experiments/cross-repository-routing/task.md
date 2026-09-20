# Cross-repository current-next task

You are operating one bounded delivery lane. The target repository is selected
by the supplied owner envelope or claim. Read the assigned repository-delivery
instructions and the three owner transcripts. For each transcript, return the
single supported next action and explain which owner field selected it.

Rules:

- Copy an owner-provided argv unchanged after its required fresh readback.
- Never replace, infer or normalize repository identity, target, credentials,
  workflow, job, permission or an unknown write result.
- An unsupported repository stops at the exact invalid field and supported help.
- A draft PR or missing repository-owned acceptance step is not merge eligible.
- A closed upstream Issue alone never proves dependency satisfaction.

The cases are: a supported Ops readback, an unsupported repository, and a
supported Ops PR missing one required PostgreSQL acceptance step. No provider
write, credential, merge or Issue closure is authorized.
