# Local supervisor admission: bounded physical atom

Question: can one externally selected local Soodles Issue/carrier use the same
provider-identity ownership model as cloud execution without asking the Agent to
discover a launcher, mint credentials or receive supervisor credential material?

Cloud is the compatibility reference: connector/Actions owns provider identity
outside the Agent. Local treatment mirrors that boundary with the existing
machine-local `NOODLES_TOKEN_COMMAND`.

Baseline is the existing production behavior: a matching schedule Session with
no `SOODLES_ADMISSION_LAUNCHER` refuses as supervisor-owned input and creates no
`orders-next.json`.

Treatment adds one local host bootstrap:

1. explicit fresh Issue readback + carrier + control root + new external output;
2. require host `NOODLES_TOKEN_COMMAND` before output creation;
3. materialize runtime bytes from committed Git objects while unrelated dirty
   working-tree bytes remain excluded;
4. return only one external `start-noodle` argv;
5. wrapper obtains one fake installation token, overwrites stale parent provider
   tokens, injects launcher, removes supplier from child;
6. existing `issue inspect` returns exactly `[launcher, automatic]`;
7. one launcher execution reaches existing `proposal_pending`.

Predetermined negatives: missing supplier before output; failing supplier before
child/proposal; one-byte envelope/runtime tamper before proposal; historical
unselected launcher ignored; existing output not overwritten; wrong origin and
carrier digest rejected.

The provider reader, supplier and carrier are local fixtures. No live token mint,
macOS daemon restart, provider write, merge, Issue closure or stale-schedule
recovery is claimed. Token bytes and supplier commands must not appear in argv,
bundle files or evidence. All receipts are non-authorizing.
