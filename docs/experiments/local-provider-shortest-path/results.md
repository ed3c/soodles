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
