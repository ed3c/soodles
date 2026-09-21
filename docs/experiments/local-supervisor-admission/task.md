# Local supervisor admission: bounded physical atom

Question: can one externally selected local Soodles Issue/carrier be turned into
a single executable admission capability whose provider identity is already
supervisor-owned before Noodle starts, without asking the Agent to discover a
launcher or recover a missing `GH_TOKEN` later?

Baseline is the existing production behavior: a matching schedule Session with
no `SOODLES_ADMISSION_LAUNCHER` refuses as supervisor-owned input and creates no
`orders-next.json`. The retained #117 handoff adds the same causal seam's second
downstream symptom: when provider identity is not injected before the child,
the Issue read reaches a missing-credential refusal.

Treatment adds only the supervisor producer/start wrapper. The matched fixture
must show:

1. explicit Issue readback + carrier + control root + new external output;
2. `NOODLES_TOKEN_COMMAND` is required at the supervisor boundary before output;
3. bundle bytes are copied from committed Git objects while an unrelated
   working-tree byte remains dirty and excluded;
4. producer returns one `start_noodle` argv containing only the external start
   wrapper path, with no token or token-supplier command in argv;
5. that wrapper obtains one fake installation token from the host supplier,
   overwrites stale parent provider credentials, injects `GH_TOKEN`,
   `GITHUB_TOKEN` and the selected launcher into the Noodle child, and removes
   `NOODLES_TOKEN_COMMAND` from the child environment;
6. no token bytes are persisted in the admission bundle;
7. existing `issue inspect` returns exactly `[launcher, automatic]`;
8. one launcher execution reaches existing `proposal_pending`.

Predetermined sensitivity controls: missing supplier refuses before bundle
creation; supplier failure refuses before the Noodle child/proposal; one-byte
envelope tamper and one-byte runtime tamper refuse before proposal; an unselected
historical launcher is ignored; an existing output directory is never
overwritten.

Cloud parity is ownership, not transport identity: GitHub connector/Actions own
provider identity on the cloud path; the local host supervisor owns the
installation-token supplier and child injection. The Agent selects neither.

The provider reader, token and carrier are local fixtures. No live provider
write, real token value, daemon restart, merge, Issue closure or stale-schedule
recovery is claimed. All evidence is non-authorizing.
