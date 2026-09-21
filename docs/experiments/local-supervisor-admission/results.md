# Local supervisor admission result

Classification: **IN PROGRESS** for the provider-identity correction on the same
#118 atom. The previously verified launcher-only candidate is retained as
historical evidence, not terminal evidence for the stronger local/cloud-parity
claim.

## Preserved prior candidate

- Prior exact head: `e351d4331ef0c2515a0fe7342fb59d729e9c9396`
- Prior runtime run: `35557242674` — success
- Prior quality run: `35557242607` — success
- Prior bounded result: committed-byte external bundle plus exact
  `issue inspect -> [launcher, automatic] -> proposal_pending`

That candidate explicitly did **not** prove App-token/provider-identity
injection. The retained #117 local handoff then showed the practical consequence:
a local consumer can still stop at missing `GH_TOKEN`/credential ownership after
the launcher seam is fixed.

## Current correction

The same supervisor bootstrap now owns provider identity before Noodle starts:

- `prepare` requires the host-owned `NOODLES_TOKEN_COMMAND` before creating an
  external bundle;
- returned `start_noodle` argv contains only the generated start-wrapper path;
- the start wrapper invokes the host supplier immediately before the generation,
  requires one token, overwrites inherited `GH_TOKEN`/`GITHUB_TOKEN`, injects the
  selected admission launcher, removes `NOODLES_TOKEN_COMMAND` from the child,
  and execs the measured Noodle binary;
- token bytes are neither argv nor bundle/receipt content;
- missing or failing supplier refuses before the Noodle process/proposal;
- cloud behavior remains unchanged: connector/Actions own cloud provider
  identity, while the local host supervisor owns local provider identity.

The existing schedule Skill, Issue #117 owner paths, Noodle source, stale failed
schedule and provider-write ownership remain unchanged.

## Acceptance state

Focused controls and exact-head runtime/quality must be rerun on the final
credential-injection head before this file can be treated as verified. All
candidate/local receipts remain `authorizes_landing=false`; provider merge and
Issue closure remain with the existing external landing owner.
