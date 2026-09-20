# Issue #97 — P0/P1 atomic delivery

## Decision

Correction owned by [Issue #99](https://github.com/ed3c/soodles/issues/99):
the bounded P0 fixture observation remains supported, but the former P1
**2 to 0** inference is withdrawn. Counting PRs across #91/#93/#95 does not
establish when each defect was discovered relative to merge, nor a matched
fresh-consumer comparison. The historical P1 behavior delta is **not established**,
not retroactively zero. Historical raw files and observer remain unchanged;
the original report and manifest remain available at immutable commit
`a2e46631b59b1f304391bfcd49615cdd9f6124e7`.

The historical #92 runtime artifact has SHA-256
`04585341f1611492d9a7f46a64f2be4edc75e6767504f0ab9f8f814904a59ebd`.
Its refusal observer exited 1: all four assigned target cases were masked by the
captured session identity while both newly created live controls passed. The
related history contains PRs #92, #94 and #96. That inventory alone cannot
classify them as one eligible pre-merge correction boundary.

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

The historical observer returns `PASS` for the committed summary packet. It
consumes supplied booleans and PR counts, not an independently captured fresh
consumer trace; this is deterministic summary replay, not independent behavioral
telemetry. The supplied non-case packet also returns `PASS`, but the observer
does not inspect its post-merge discovery field. It therefore did not demonstrate
the semantic distinction between same-PR correction before merge and a newly
discovered defect after merge.

## Delivery gate

This evidence update remains on PR #98. Its terminal head must independently
repeat candidate verification, runtime and quality before merge; the prior
GREEN run is evidence for the unchanged P0/P1 instruction bytes, not authority
to skip the final exact-head checks. After merge, main requires a fresh runtime
and provider readback before Issue closure.

## Claim boundary

P0 is a bounded fixture reliability improvement for the six pinned refusal
cases, not a model behavior improvement. Provider records establish that #97
was delivered by PR #98, and candidate verification binds its evidence bytes.
Neither fact validates the semantic contents of the summary packet. P1 did not
establish fresh decision improvement, new/old prompt compatibility, all N/P/L/R
atoms or per-line correctness. All experiment receipts are non-authorizing.

The current-context observations and their limitations are recorded separately
in [Issue #99's results](../fresh-delivery-decisions/results.md). This correction
changes no P-class instruction and does not replace the historical active judge.
