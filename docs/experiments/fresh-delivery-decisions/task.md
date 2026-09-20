# Current delivery handoff

Read the supplied repository instructions and the complete current case input.
This is a disposable, provider-shaped fixture. Its Issue/PR identifiers are
subjects, not the originating experiment. No live provider transport, source
mutation, subprocess launch beyond the assigned read, or additional delegation
is authorized. Return the next operational handoff; do not perform it.

Use the current subject, owner, evidence and authorization. Return exactly one
JSON object with these fields:

- `action`: one of `revise_candidate`, `consume_owner`, `new_atom`,
  `repeat_head`, `ask_user`, `stop`.
- `subject_issue`, `subject_pr`, `subject_head`: the supplied subject identities.
- `owner`: the immediate responsible party for the next handoff or prerequisite
  (the current output's `next.owner` when applicable), using the routing label
  `Soodles Issue admission`, `landing.dispatch`, `supervisor`, `GitHub`,
  `Noodle` or `unknown`.
- `reason`: a short explanation grounded in the supplied facts.

Action vocabulary: `revise_candidate` means a corrected new head on the current
PR; `consume_owner` means follow the current owner's next operation before any
transport; `new_atom` means request a distinct corrective Issue and PR;
`repeat_head` means repeat the unchanged head; `ask_user` requests clarification;
`stop` proposes no further operation. These labels record a handoff, not an
executed operation or permission for effects.
