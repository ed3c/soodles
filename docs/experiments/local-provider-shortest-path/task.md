# Local provider shortest path — bounded atom

Question: after the landing owner has already selected an exact local merge/close
transition, can a local Noodle consumer follow only typed `next` output through
provider mutation, fresh readback and reconciliation without choosing GitHub
mutation syntax, provider subject identity, credential source or Noodle binary?

Baseline on main `cf204ed40050198b5dfe3b1848baaab9e729ada9`:

- local `landing.dispatch` persists offered state and emits an exact `request`,
  but its `next` is provider readback, so local mutation transport remains an
  external consumer decision;
- after provider closure, local `landing.advance` asks for `binary` even when
  a claim already carries an external execution envelope.

Treatment:

1. persist the exact request inside the existing delivery record;
2. local dispatch projects only `provider-execute CHECKPOINT` as executable
   continuation; cloud dispatch remains connector-backed;
3. provider-execute accepts no repository/PR/Issue/head/method flags, uses only
   the persisted request and inherited supervisor credential, performs at most
   one mutation, saves fresh provider readback and returns exact
   `landing advance` argv;
4. unknown mutation result never causes an automatic retry;
5. an envelope-bound local reconciliation projects exact `landing reconcile`
   argv using the measured Noodle binary;
6. P-class tells the consumer to execute current owner argv and never reconstruct
   provider or binary choices.

This experiment does not create Issues, select next tasks, modify Noodle or claim
remote exactly-once delivery. New-Issue authority remains a later atom.
