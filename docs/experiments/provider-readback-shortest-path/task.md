# Local provider-readback shortest path — bounded atom

Question: when a local Soodles owner returns next.kind=provider_readback, can the
consumer reach the exact owner re-entry without the Agent translating GitHub GET
requests, pagination, snapshot keys or CLI syntax?

Treatment:

1. current owner result remains the sole request authority;
2. provider-readback accepts only owner=GitHub, kind=provider_readback and GET;
3. primary URLs must be api.github.com/repositories registered by Soodles;
4. landing request keys are materialized verbatim in readback.json;
5. a merged PR may add exactly one dependent merge-commit GET from its confirmed
   merge_commit_sha;
6. next-Issue Issues readback follows only same-repository provider Link
   pagination on the same endpoint and filters pull-request records;
7. selected landing publisher identity is revalidated before composing exact
   advance/dispatch argv;
8. next-Issue returns exact reconcile argv;
9. credentials remain inherited and never appear in files/argv/evidence.

No provider mutation is performed. The atom ends at one executable transition
owner re-entry. Noodle retains schedule/order/worktree/process ownership.

CLI behavior is bounded L-class evidence. The P-class route cannot authorize a
provider read or prove reduced model decision cost by itself.
