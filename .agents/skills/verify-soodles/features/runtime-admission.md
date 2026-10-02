# Runtime admission

A user supplies a Noodle executable to Soodles. Soodles accepts the pinned executable and rejects an unadmitted binary before executing it.

## Sub-features

- `pinned-runtime`: observed version and binary digest agree with the repository lock.
- `refusal-before-execution`: a wrong-digest executable cannot create its sentinel.
- `actionable-refusal`: the diagnostic names `binary.sha256` and `./soodles runtime check --help`.

## How to get to it (user POV)

Run `./soodles runtime check /absolute/path/to/noodle`. This map covers that
standalone CLI entry. The larger acceptance workflow has its own owner and controls.

## Driving it with verify_runtime.py

Use this driver only for Test Manager-selected admission/refusal verification.
A normal runtime check does not request sentinel injection or skill-resolution tests.

Preconditions: Linux amd64, Python 3, Git, a clean committed Soodles checkout, the locked Noodle binary, and a fresh evidence directory outside the checkout.

- Invoke `.agents/skills/verify-soodles/scripts/verify_runtime.py` with the admitted binary path and evidence directory.
- For the positive control, require the actual runtime-check command to exit 0. It must emit the locked digest and version, with no landing authority.
- Require `noodle skills list` to name this checkout's `verify-soodles` directory. Retain the selected path and file digests.
- For the negative control, pass a temporary executable with a wrong digest to the same runtime-check command. Require exit 1, the owning field and help, and an absent sentinel.
- Require `receipt.json` to record `VERIFIED`, both CLI observations and command counts. It must also record unchanged source head and tree across the run.
- After cleanup, require an absent temporary executable directory, unchanged source identity and status, and a surviving receipt. The driver does not inspect Noodle worktree ownership or remove the task worktree. Lifecycle ownership requires its separate owner readback.

## Gotchas

The intended negative invocation is an expected refusal, not an Agent mistake.
Repeated identity readbacks protect the before and after boundary, so the driver
records them. No matched baseline/treatment experiment has established reduced
Agent cost. If skill resolution is missing or foreign, this recipe fails even if
runtime admission passes. Missing backlog-adapter diagnostics do not admit
production scheduling. `VERIFIED` is scoped feature evidence. An Issue reaches
`RESOLVED` only through its existing delivery owner.
