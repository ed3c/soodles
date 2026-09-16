# Runtime admission

A user supplies a Noodle executable to Soodles. Soodles accepts the pinned executable and rejects an unadmitted binary before executing it.

## Sub-features

- `pinned-runtime`: observed version and binary digest agree with the repository lock.
- `refusal-before-execution`: a wrong-digest executable cannot create its sentinel.
- `actionable-refusal`: the diagnostic names `binary.sha256` and `./soodles runtime check --help`.

## How to get to it (user POV)

Run `./soodles runtime check /absolute/path/to/noodle`. This map covers that standalone CLI surface; the larger acceptance workflow has its own owner and controls.

## Driving it with verify_runtime.py

Preconditions: Linux amd64, Python 3, Git, a clean committed Soodles checkout, the locked Noodle binary, and a fresh evidence directory outside the checkout.

- **Drive:** invoke `.agents/skills/verify-soodles/scripts/verify_runtime.py` with the admitted binary path and evidence directory.
- **Positive:** the actual runtime-check command exits 0 and emits the locked digest/version with no landing authority.
- **Resolve:** `noodle skills list` names this checkout's `verify-soodles` directory; retain the selected path and file digests.
- **Negative:** the same runtime-check command receives a temporary executable with a wrong digest. It exits 1 with the owning field/help, and the sentinel is absent.
- **Observe:** `receipt.json` records `VERIFIED`, both CLI observations, command counts, and source head/tree unchanged across the run.
- **Cleanup:** the temporary executable directory is absent, the task worktree remains owned by Noodle, and the receipt still exists.

## Gotchas

The intended negative invocation is an expected refusal, not an Agent mistake. Repeated identity readbacks are recorded because they protect the before/after boundary. No matched baseline/treatment experiment has established reduced Agent cost. Missing or foreign skill resolution fails this recipe even if runtime admission passes. Missing backlog-adapter diagnostics do not admit production scheduling. `VERIFIED` is scoped feature evidence; an Issue reaches `RESOLVED` only through its existing delivery owner.
