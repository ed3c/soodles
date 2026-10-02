# system-v1: common authority limits

Owner: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).

This file specifies behavior, transition owners, and evidence that distinguishes
valid from invalid results. Prose alone is not an L/R guarantee. `AGENTS.md`
routes task execution. Skills describe conditional procedures. Read
[agent-context-design.md](../agent-context-design.md) only when designing those
instructions. It is P-class and experimental under #39. Existing executable
requirements below retain their scope and authority.

## Authority limits

The original bootstrap established local rejection and runtime evidence only.
Its self-test receipts grant no landing authority. `runtime.yml` executes candidate
acceptance without write authority; it is not an independent default-branch verifier.
Later contracts define their own admitted execution, recovery and delivery boundaries.
Do not apply the original bootstrap's missing capabilities as a limit on those owners.

A candidate cannot approve itself. Initial installation uses the
owner-requested supervised process in [landing.md](landing.md). Candidate
self-tests do not establish an independent trusted verifier.