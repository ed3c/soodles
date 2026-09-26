# Root-scoped Noodle order on repeated Issue admission, #168

The second pristine #156 root reached the normal Noodle loop, which created its native `schedule` order. Dispatch then stopped because the prior, unmerged Noodle worktree still owns `soodles-156-0-execute`; the failed root and old branch remain untouched (`raw/baseline.json`).

The admission producer now derives the order ID from the exact control-root path and derives the predicted worktree name from that ID. The shared envelope gate recomputes both values for new IDs while retaining historical static-ID envelopes. Publication claim uses the admitted ID. The Issue-atom skill and owner recognize only an idle, exact-shaped native `schedule` while its own bound order is live; an active/changed scheduler or unrelated order remains a refusal.

A disposable real Noodle run kept an older unmerged branch occupied and dispatched the new bound order to a distinct worktree without removing the old one (`raw/positive.json`). The focused 74 tests and full 376 tests passed (`raw/tests.txt`). These local controls do not authorize landing; exact-head Linux runtime and the selected external owner remain required.
