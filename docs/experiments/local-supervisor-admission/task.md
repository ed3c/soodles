# Local supervisor admission: bounded physical atom

Question: can one externally selected local Soodles Issue/carrier be turned into
a single executable admission capability without asking the Agent to discover,
synthesize or reuse a launcher?

Baseline is the existing production behavior: a matching schedule Session with
no `SOODLES_ADMISSION_LAUNCHER` refuses as supervisor-owned input and creates no
`orders-next.json`.

Treatment adds only the supervisor producer. The matched fixture must show:

1. explicit Issue readback + carrier + control root + new external output;
2. bundle bytes copied from committed Git objects while an unrelated working-tree
   byte remains dirty and excluded;
3. producer returns one `start_noodle` argv carrying the selected launcher;
4. existing `issue inspect` returns exactly `[launcher, automatic]`;
5. one launcher execution reaches existing `proposal_pending`.

Predetermined sensitivity controls: one-byte envelope tamper and one-byte
runtime tamper refuse before proposal; an unselected historical launcher is
ignored; an existing output directory is never overwritten.

The provider reader and carrier are local fixtures. No live provider write,
daemon restart, merge, Issue closure, App-token injection or stale-schedule
recovery is claimed. All evidence is non-authorizing.
