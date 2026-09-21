# Local provider-readback shortest path result

Classification: **IN PROGRESS** until exact-head candidate verification,
canonical runtime acceptance and quality complete.

Bounded target:

```text
current next.kind=provider_readback
→ provider-readback consume
→ exact owner-emitted GETs
→ typed readback/frontier
→ exact transition-owner re-entry argv
```

The adapter is read-only. It may add only the explicitly owner-declared
merge-commit dependency and provider Link pagination. It performs no provider
write and grants no landing authority.

The P-class correction routes local Noodle/Soodles provider-readback through one
executable entry. No quantified model-behavior improvement is claimed without a
fresh matched independent comparison.
