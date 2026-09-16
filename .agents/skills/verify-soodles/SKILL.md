---
name: verify-soodles
description: Drive Soodles runtime admission through its real CLI, inspect skill resolution and refusal-before-execution evidence, and preserve a scoped verification receipt. Use when verifying this feature or maintaining its verification recipe.
---

# Verify Soodles

This is a CLI application. The initial map covers **runtime admission only**; delivery, reconciliation and quality reporting remain outside this skill's proven coverage. For this feature, read [runtime admission](features/runtime-admission.md) directly. Consult [the feature index](features/README.md) when auditing map coverage. The normal route is AGENTS → this skill → the feature, with no mandatory index hop.

## Launch

Run from the Soodles checkout in a Noodle-owned worktree. Use a clean committed candidate and the absolute path to the binary admitted by `policy/runtime.lock.json`. The application is short-lived and noninteractive: existing subprocess driving is sufficient; no daemon, PTY or server is needed. Obtain the pinned runtime through the repository's existing runtime setup; do not install a guessed release or start `noodle start`.

## Doctor

The driver's first application operation is `./soodles runtime check` on the supplied binary. Its receipt must match the lock before Noodle is used to resolve this skill. This doctor doubles as the positive feature drive. A refusal ends this run; use its field and supported help to identify a materially changed input before retrying.

## Drive and Helpers

Use the shipped executable from the repository root:

```sh
.agents/skills/verify-soodles/scripts/verify_runtime.py /absolute/path/to/noodle /tmp/fresh-soodles-verification
```

Both arguments are supplied by the current execution environment: the already-admitted binary and a fresh evidence destination. The driver checks source identity, performs doctor/positive admission, resolves this skill through `noodle skills list`, and drives a wrong-digest executable sentinel through the same CLI. It then checks cleanup and unchanged source identity. It never sends provider writes or runs full acceptance.

Noodle resolves `.agents/skills` by default. Resolution must name this checkout's exact `verify-soodles` directory; requesting a name is not proof of loading it. The captured digest map identifies the actual skill files. Noodle may emit missing-backlog-adapter diagnostics: they disclose that production scheduling is unavailable, not a request to repair unrelated adapters during verification.

## Evidence

Require `receipt.json` in the selected output directory with `classification: VERIFIED`, the exact candidate head/tree, observed runtime identity, local skill resolution, rejected sentinel, and successful cleanup. The trace contains actual commands, stdout/stderr, exit codes and elapsed time. Counts distinguish expected control refusals from unexpected command failures and include mandatory repeated identity readbacks. They cover driver commands, not Agent thoughts, earlier discovery, or internal subprocesses.

This receipt has `authorizes_landing: false`. It is not Issue closure or proof of lower decision cost. Canonical acceptance still runs once for each final candidate through its existing owner; do not repeat it just because this skill was used. A verification receipt obtained before a candidate change does not verify the changed candidate.

## Cleanup

The driver owns only its temporary sentinel directory and waits for each short-lived command. Teardown runs on failed drives too. Evidence lives outside that directory and survives cleanup. Noodle owns the task worktree; this skill does not remove it. A failed receipt is evidence, not permission for an unchanged retry.

## Maintenance

Creation follows pstack `create-verification-skill` at `ed3c/plugins@68836ddaf5697224520f1847d90cdb90ca8babaa`, adapted to this carrier and one-feature scope. Later use `maintain-verification-skill` when auditing this map or repairing demonstrated recipe/harness drift. Its full maintenance pass needs source and live coverage of every mapped feature. Ordinary feature use does not invoke either authoring method. Product regressions retain their failing evidence and follow the admitted Issue's owner/write boundary; changing the map must not hide them. Neither method selects this candidate's effective external judge.
