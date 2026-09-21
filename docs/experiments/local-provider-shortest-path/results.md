# Local provider shortest path result

Classification: **IN PROGRESS**.

## Candidate attempt

- Issue: `ed3c/soodles#120`
- PR: `ed3c/soodles#121`
- Base: `cf204ed40050198b5dfe3b1848baaab9e729ada9`
- This file records the first PR-bound candidate attempt. Its exact head must earn
  its own runtime and quality results; no earlier branch state is accepted as
  provider delivery evidence.

## Bounded claim under test

```text
local landing owner request
→ exact provider-execute argv
→ one merge/close mutation
→ fresh provider readback
→ exact landing advance argv
→ envelope-derived Noodle reconcile argv when available
```

Hard controls cover local merge/close cardinality, replay after provider-observed
completion, unknown mutation response, cloud connector non-case, request/claim
drift, missing provider credential and envelope-derived Noodle identity.

The P-class correction removes provider mutation and binary reconstruction from
the consumer: `next.kind=executable` means execute current `next.argv` exactly
once. No generic `gh`/REST mutation command is introduced.

Cloud connector transport remains unchanged. New-Issue creation is out of scope.
All experiment/candidate evidence is non-authorizing.

## Evidence authority correction

The first PR-bound runtime attempts are preserved:

- `e8ff36ee93cadb490b19c32b7754f74956758fd5`: candidate verification refused the
  still-schema-1 Issue contract.
- `0417e150f7c8711f9ec4efe908d8b5e795e408b9`: the workflow fetched the Issue at
  07:08:55Z, two seconds before the schema-3 Issue update completed at 07:08:57Z,
  and therefore preserved the same schema-1 refusal.

No unchanged head is rerun. The current Issue now binds schema 3,
`required_paths`, the manifest and frozen treatment bytes; the next candidate
head must consume that current provider readback.
