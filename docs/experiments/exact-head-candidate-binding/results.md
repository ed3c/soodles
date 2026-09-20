# Issue #91 — exact-head candidate binding

## Decision

The bounded exact-head delivery barrier decreased from **2 to 0**.

The baseline had no candidate-verification entry, so both invalid candidates
remained admitted:

- committed instruction bytes differed from the manifest treatment digest;
- observer bytes and their candidate manifest digest changed together but
  differed from the externally frozen Issue digest.

The treatment refuses them as

- `candidate.instruction.treatment_sha256`; and
- `candidate.frozen_path.sha256`.

The complete schema 3 candidate passes. Schema 1 and schema 2 parsing remain
legal, and the existing P-class replay owner is unchanged. The focused tests
and the full 174-test suite pass locally.

The first exact head `84584ac61474c3ac1354ad8f70efb2fea3e29807`
remains an immutable failed attempt. Its candidate-verification step, canonical
acceptance and quality report passed, but runtime run `35502602979` exposed a
stale direct-consumer assertion: the admission-recovery fixture correctly
preserved the planted `refusal` process as exit 1 while the shell assertion
required exit 0 for both `recovery` and `refusal`. The terminal candidate fixes
only that declared control interpretation to require `recovery=0` and
`refusal=1`; it does not rerun or relabel the failed head.

## PR #90 regression

Replaying the historical PR #90 candidate directly from Git objects exposes a
preserved historical mismatch. Its manifest records baseline prompt SHA-256
`dd8fb2ef1f296655f7f79cf8581a1129a6543e6bbc7afe0205db1b1732533498`,
while base commit `de7b07b99e7879d54fda99e8166cc2aa782e04cc` contains SHA-256
`84e3c7dc8f985e16797b307bdc5b5571eafeda5b967a71079f4ce3e2674b2098`.
The treatment prompt and all manifest-listed artifacts match their committed
digests. The new entry therefore correctly refuses the historical candidate at
`candidate.instruction.baseline_sha256`; this failed historical head remains
immutable and is not relabelled green.

## Scope

This establishes direct byte binding between a fresh Issue contract and the
actual PR base/head before canonical runtime acceptance. It does not rerun or
reclaim P-class model behavior. `replay_pclass.py` remains the semantic P-class
evaluator, and every receipt here has `authorizes_landing: false`.
