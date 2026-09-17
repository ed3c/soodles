---
name: verify-soodles
description: Verify Soodles runtime admission, supervised delivery and recovery through existing owners. Consume structured next actions, preserve scoped receipts, and maintain the demonstrated feature map.
---

# Verify Soodles

This is a CLI application with an external supervised publisher and GitHub transport. Read the relevant recipe directly: [runtime admission](features/runtime-admission.md), [bounded Issue execution](features/issue-execution.md), [supervised delivery](features/supervised-delivery.md), or [delivery recovery](features/delivery-recovery.md). Consult [the feature index](features/README.md) for a full maintenance pass. Quality reporting, general production scheduling and Issue DAG execution remain outside this map. The normal route is AGENTS → this skill → the feature, with no mandatory index hop.

## Launch

Runtime admission and delivery-recovery fixtures run from a clean committed Soodles checkout with the absolute binary admitted by `policy/runtime.lock.json`. These CLI drives are short-lived and noninteractive; do not start `noodle start` for them. Bounded Issue execution instead uses the supervisor's separately measured carrier and existing Noodle lifecycle, as its recipe specifies. Neither route substitutes its binary or platform evidence for the other.

## Doctor

For the lock-bound recipes, start each fresh driving session with `./soodles runtime check` on the supplied binary. Its receipt must match the lock before Noodle is used. The runtime driver's doctor doubles as its positive feature drive. For bounded Issue execution, use that recipe's carrier/envelope and canonical-state preflight instead; the Linux lock does not certify a native macOS executable. Recheck after an unexpected failed drive or changed environment before continuing; preserve the failure first. Doctor is not permission to retry unchanged input. A refusal names the invalid field and supported help; a missing prerequisite remains blocked until its owner supplies it.

## Drive and Helpers

Use the shipped executable from the repository root:

```sh
.agents/skills/verify-soodles/scripts/verify_runtime.py /absolute/path/to/noodle /tmp/fresh-soodles-verification
```

Both arguments are supplied by the current execution environment: the already-admitted binary and a fresh evidence destination. This runtime driver checks source identity, performs doctor/positive admission, resolves this skill through `noodle skills list`, and drives a wrong-digest executable sentinel through the same CLI. It then checks cleanup and unchanged source identity. It never sends provider writes or runs full acceptance. Other recipes reuse existing owner entries and recovery oracles; do not route them through a new scheduler or copy their transition logic into a skill helper.

For landing, consume the invoked owner's current `owner`, `action`, `next`, `invalid` and, when emitted, `request`. Missing input and provider readback are not executable commands. Follow the returned operation/help using confirmed inputs; never derive an operation by splitting a field name. A historical next action is trace evidence only. The owning action rechecks the current claim, head, checkpoint, provider state and write eligibility before an effect.

Noodle resolves `.agents/skills` by default. Resolution must name this checkout's exact `verify-soodles` directory; requesting a name is not proof of loading it. The captured digest map identifies the actual skill files. Noodle may emit missing-backlog-adapter diagnostics: they disclose that production scheduling is unavailable, not a request to repair unrelated adapters during verification.

## Evidence

For runtime admission, require the driver's `receipt.json` with `classification: VERIFIED`, exact candidate head/tree, observed runtime identity, local skill resolution, rejected sentinel and successful cleanup. Other recipes specify their own receipts. Preserve actual argv/provider operations, subjects, output, exit codes and elapsed time where observed. Record skill resolution path/digests, unexpected command failures, expected control refusals, repeated readbacks and verification invocations; label top-level versus child-command scope. Missing measurements are unknown, not zero. These records do not establish a matched baseline/treatment experiment or reduced Agent decision cost.

Local feature receipts have `authorizes_landing: false`; `VERIFIED` is not Issue closure. Only the externally selected delivery owner can produce the admitted Issue's `RESOLVED` receipt after provider merge/closure readback and Noodle reconciliation. `next: null` alone is not resolution (identity also returns it). Canonical acceptance still runs once for each final candidate through its existing owner; do not repeat it just because this skill was used. A pre-change receipt does not verify a changed candidate. Shorter instructions, lower structural scores or fewer commands do not establish reduced Agent decision cost.

## Cleanup

The runtime driver owns its temporary sentinel directory; recovery oracles own disposable fixtures and wait for their child processes. Preserve evidence outside those directories through teardown, including on failure. Noodle owns the task worktree; only the existing delivery reconciliation may remove it. If that removal is expected, verify the reported merged identity in the surviving control root instead of invoking a deleted candidate path. A failed receipt is evidence, not permission for an unchanged retry.

## Maintenance

This existing skill was created using pstack at `ed3c/plugins@68836ddaf5697224520f1847d90cdb90ca8babaa`. Use its `maintain-verification-skill` for a map audit or observed recipe drift; do not repeat create. A full pass audits the index, runs one read-only source review per feature concurrently, reconciles source/churn drift, and has the coordinator live-drive every mapped feature with doctor, receipts and teardown. Outcome is clean, changed or blocked; clean/blocked passes do not manufacture a PR. Only demonstrated skill corrections belong in a changed maintenance PR. Ordinary feature use does not invoke either authoring method.

This guidance is P-class; the index, counts and prose are N-class. Executable local discriminators provide L-class evidence; actual provider-enforced identity and merge/closure readback provide R-class evidence. None is interchangeable. Product regressions retain their failing evidence and follow the admitted Issue's owner/write boundary; changing a recipe must not hide them. Supervisor correction remains available through the existing owning action before an unoffered admission is reused. Preserve unknown writes for owner readback. Neither maintenance nor a candidate-edited test selects its effective external judge.
