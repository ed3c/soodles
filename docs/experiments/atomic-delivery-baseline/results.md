# Issue #97 — P0/P1 atomic delivery

## Decision

The bounded P0 fixture barrier decreased from **1 to 0**, and the preserved P1
delivery-split barrier decreased from **2 to 0** for Issue #97.

The historical #92 runtime artifact has SHA-256
`04585341f1611492d9a7f46a64f2be4edc75e6767504f0ab9f8f814904a59ebd`.
Its refusal observer exited 1: all four assigned target cases were masked by the
captured session identity while both newly created live controls passed. The
historical delivery then required PRs #92, #94 and #96 for one originating gap.

## Treatment observation

PR #98 head `90a2b33b71cf51e0a633501ff5fc2da7016bd5b7` ran runtime
`35507779444`, job `106070388595`, and quality `35507779440`. Its candidate
tree was `7c136849eaa9b318e82aefe058e08a313012ba76`; candidate verification
bound all 16 required paths and the two frozen inputs to committed bytes.

The runtime artifact `10604906292` has SHA-256
`fb989ea8112ec9adbfe957a6f31ffe0d731228b97cce27a812937694c645fa34`.
Its refusal observer exited 0. Each of wrong digest, wrong revision, admitted
ledger and valid proposal reached its assigned predicate after nine historical
process identities were replaced in the disposable copy. The live-session and
orphan-live-group controls still refused for the live process-group predicate.
The source fixture digest map was identical before and after execution.

The fixed observer independently replays the committed treatment as `PASS`.
The legal non-case also passes: failed candidate heads may be replaced by new
heads on one unmerged PR, while a defect discovered after merge starts a new
Issue and PR because the rollback boundary changed.

## Delivery gate

This evidence update remains on PR #98. Its terminal head must independently
repeat candidate verification, runtime and quality before merge; the prior
GREEN run is evidence for the unchanged P0/P1 instruction bytes, not authority
to skip the final exact-head checks. After merge, main requires a fresh runtime
and provider readback before Issue closure.

## Claim boundary

P0 is a physical nonzero hill climb for the six pinned refusal cases. P1 proves
the bounded one-Issue/one-PR shape for #97 and machine binding of its committed
evidence. It does not prove model-wide prompt correctness, every N/P/L/R atom,
or a fresh probabilistic agent behavior improvement. All receipts are
non-authorizing.
