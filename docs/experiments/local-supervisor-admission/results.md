# Local supervisor admission result

Classification: **VERIFIED** for the bounded local/cloud-compatible supervisor
bootstrap on exact candidate `db270035fa4bb3a13b22d49a36d38d0fbac064ac`.
This evidence is non-authorizing.

## Exact candidate

- head: `db270035fa4bb3a13b22d49a36d38d0fbac064ac`
- runtime run: `35558257475` — success
- quality run: `35558257476` — success
- runtime artifact: `10621183817`
- artifact digest:
  `sha256:13efb1e194f767de83e76ca67bc908c6ec8e1ee8b991bef941e2136e7520f230`

The exact-head runtime job passed fresh Issue candidate verification, pinned
runtime identity, canonical acceptance, admission-recovery preservation and
non-authorizing evidence upload.

## Demonstrated local/cloud parity

Cloud remains unchanged: connector/Actions own provider identity outside the
Agent.

The bounded local treatment mirrors that ownership model:

1. supervisor prepare requires machine-local `NOODLES_TOKEN_COMMAND` before
   creating an external bundle;
2. returned executable argv contains only the generated `start-noodle` path;
3. the wrapper obtains exactly one fake installation token immediately before
   child start, overwrites stale inherited `GH_TOKEN/GITHUB_TOKEN`, injects the
   selected admission launcher and removes `NOODLES_TOKEN_COMMAND` from the
   child environment;
4. token bytes and supplier command are absent from argv and persisted bundle;
5. existing `issue inspect -> [launcher, automatic]` remains unchanged and the
   launcher reaches the existing `proposal_pending` boundary.

The committed-byte control also preserves a deliberate dirty working-tree
`soodles.py` sentinel and proves those dirty bytes do not enter the external
runtime bundle.

## Fail-closed controls

- missing supplier refuses before bundle creation;
- failing supplier refuses before Noodle child/proposal;
- stale parent provider tokens are overwritten by the supervisor-owned token;
- envelope/runtime tamper refuses before proposal;
- historical unselected launcher is ignored;
- foreign repository origin, carrier digest mismatch and existing output refuse
  before effects.

## Scope

This does not prove a live macOS App-token mint, daemon restart or stale Noodle
lifecycle recovery. It adds no App private key/client/installation ID, PAT,
fallback identity, scheduler, Noodle source change or provider-write adapter.
Issue #117 owner paths and `.agents/skills/schedule/SKILL.md` remain unchanged.

All local/candidate receipts have `authorizes_landing=false`. Provider merge,
Issue closure and provider-main reconciliation remain with the existing external
landing owner.
