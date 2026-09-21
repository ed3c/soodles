# Local supervisor admission result

Classification: **VERIFIED** for the bounded local fixture and exact-head
repository acceptance. This receipt is non-authorizing.

## Exact candidate

- Candidate head: `324bdbfeafd7a23ac24041e42473622c74f98096`
- Candidate tree: `cbaf64ab63029ca357cd4dd45996a98f00b270c5`
- Runtime run: `35557078066`
- Runtime job: `106202669187` / `runtime-evidence` — success
- Quality run: `35557078041` — success
- Runtime artifact: `10620947403`
  `runtime-evidence-324bdbfeafd7a23ac24041e42473622c74f98096`
- Artifact digest:
  `sha256:cd9bd40d45f271f8a1af266fe4624ab0da9a81a5a3306714b25b98586c070873`

The exact-head candidate-evidence step, pinned release identity, canonical
acceptance, existing admission-recovery preservation and artifact upload all
completed successfully.

## Physical controls

Canonical acceptance ran 216 tests in 14.296 seconds and reported `OK`. The
three new controls passed:

- `test_baseline_to_exact_launcher_automatic_closes_capability_gap`
- `test_tamper_historical_and_overwrite_controls_refuse_before_proposal`
- `test_wrong_origin_and_carrier_digest_refuse_before_output`

The acceptance receipt reported `zero_residue=true` and
`authorizes_landing=false`.

These controls establish the bounded claim: the pre-existing missing-launcher
case remains a supervisor-owned zero-proposal refusal; the producer materializes
committed Git bytes into one external bundle, existing `issue inspect` returns
the selected `[launcher, automatic]`, and one launcher execution reaches the
existing `proposal_pending` boundary. Envelope/runtime tamper, unselected
historical launcher, invalid carrier/repository identity and output overwrite
remain fail-closed.

## Scope

No live macOS daemon restart, GitHub App-token injection, provider write, merge,
Issue closure, stale-schedule recovery or Noodle lifecycle repair is claimed by
this fixture. The old 2026-09-17 failed schedule remains historical evidence and
is not replayed. Issue #117 owner paths and `.agents/skills/schedule/SKILL.md`
are unchanged by this candidate.
