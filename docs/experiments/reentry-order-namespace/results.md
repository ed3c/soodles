# Root-scoped Noodle order on repeated Issue admission, #168

The second pristine #156 root reached the normal Noodle loop, which created its native `schedule` order. Dispatch then stopped because the prior, unmerged Noodle worktree still owned `soodles-156-0-execute`. The failed root and old branch remained untouched (`raw/baseline.json`).

The admission producer now derives the order ID from the exact control-root path and derives the predicted worktree name from that ID. The shared envelope gate recomputes both values for new IDs while retaining historical static-ID envelopes. Publication claim uses the admitted ID. While its own bound order is live, the Issue-atom skill and owner recognize only an idle native `schedule` with the exact expected shape. They still refuse an active or changed scheduler, or an unrelated order.

A disposable real Noodle run kept an older unmerged branch occupied and dispatched the new bound order to a distinct worktree without removing the old one (`raw/positive.json`). The focused 74 tests and full 376 tests passed (`raw/tests.txt`). These local controls do not authorize landing; exact-head Linux runtime and the selected external owner remain required.
