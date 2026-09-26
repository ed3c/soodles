# #159 cloud Session activation: scoped Host acceptance

Status: SCOPED_HOST_ACCEPTANCE.
Base: 00a5909941a632537dc6992b5354cd37614ea4a8.
One Issue / one PR; #170 local evidence remains independent.

## Revised terminal claim

#159 now closes only the Host Session-entry behavior that can be observed and
owned from ChatGPT cloud:

- consume an already-selected recipe directly at its selected ref;
- distinguish unknown capability exposure from confirmed Session-local absence;
- preserve the selected carrier when a capability is missing instead of
  proposing or constructing an unsupported replacement runner;
- let unrelated authorized work continue when only one dependent operation is
  blocked; and
- refresh Session-specific capability facts on a new Session without repeating
  unchanged-turn preflight.

This is a P-class correction plus Host deployment/readback claim. It is not a
claim of causal behavior improvement, universal native availability, complete
platform telemetry or repository CLI enforcement of ChatGPT Host behavior.

## Evidence actually observed

1. The original author Session produced the concrete failure that triggered
   #159: it generalized a Session-local native gap into a replacement-runner
   proposal. This is trigger evidence, not a blinded fresh baseline.
2. The Soodles Project Instructions were saved and later reopened with the #159
   bootstrap and the explicit run-level carrier-independence rule intact.
3. A fresh uncounted Soodles Project conversation read current provider state
   and kept #159 cloud work separate from #170 local work. Because it also read
   repository instructions, this is a scoped observation, not causal isolation.
4. A second uncounted routing check covered both directions of the dependency
   boundary: cloud blocked/local ready and local blocked/cloud ready. It allowed
   the ready route to proceed and named the blocked route's prerequisite.
5. One uncounted native Work pilot invoked `collaboration.spawn_agent` with
   `fork_turns: "none"` and completed. The parent could read its spawn request,
   child identity/status and returned text, but not an independent raw child
   GitHub event stream or complete child input identity.
6. This closing Session performed scoped capability discovery and exposes no
   native subagent action. That fact is Session-local and does not contradict
   the earlier Work pilot.

The missing raw child event transcript therefore remains an explicit telemetry
limitation. It no longer blocks this revised claim because #159 no longer uses
independent child telemetry as its correctness oracle.

## Why no Host CLI gate is added

The repository has no existing executable caller that can mechanically force a
ChatGPT Host to load Project Instructions or expose a native subagent. Adding an
always-refusing checker or alternate runner would recreate the decision barrier
this Issue is correcting. The revised claim therefore keeps enforcement in the
actual Host setting plus provider/readback evidence and does not invent a CLI.

The existing GitHub Actions runtime remains the exact-head repository acceptance
for the candidate. It verifies repository integrity, not model comprehension.

## Delivery boundary

The candidate may proceed to exact-head Actions and cloud landing when this
scoped evidence is recorded on the PR and the current Issue body carries the
same revised claim. Green CI grants no authority by itself. Final resolution
still requires exact PR merge, Issue closure and provider-main readback through
GitHub. No Local Codex/Noodle run is reused as #159 cloud evidence.

The following are intentionally not claimed at closure: matched baseline versus
treatment behavior improvement, an independent complete child transcript,
universal Project-instruction injection, a Host CLI discriminator, or any
result derived from #170's local six-run comparison.
