# Issue #97 — P0/P1 atomic delivery

## Current decision

**BLOCKED.** The provisional candidate records the historical baseline and the
minimal correction, but no terminal exact-head runtime has been observed yet.
This head must remain an immutable attempt on the single PR.

The historical #92 runtime artifact has SHA-256
`04585341f1611492d9a7f46a64f2be4edc75e6767504f0ab9f8f814904a59ebd`.
Its refusal observer exited 1: all four assigned target cases were masked by the
captured session identity while both newly created live controls passed. The
historical delivery then required PRs #92, #94 and #96 for one originating gap.

## Treatment

The corrected observer replaces captured PIDs only in each disposable copy,
records the adjustments and creates its two live controls after isolation. The
preserved source is hashed before and after execution. The delivery rules now
keep missing evidence, byte mismatch and runtime failures on new immutable
heads of the same PR until one terminal head is complete.

## Remaining gate

The exact-head runtime must execute the full six-case observer with exit 0 and
the candidate verifier must bind every required file to committed bytes. After
that provider readback, this same PR may replace the provisional treatment,
replay and results with the observed terminal receipt. It may not merge while
this section remains BLOCKED.

## Claim boundary

P0 can support a scoped nonzero hill climb only if four masked target cases
become four correctly discriminated cases while both live controls remain
GREEN. P1 proves the bounded delivery shape only for #97. It does not prove
model-wide prompt correctness, every N/P/L/R atom or a fresh probabilistic
agent behavior improvement. All receipts are non-authorizing.
