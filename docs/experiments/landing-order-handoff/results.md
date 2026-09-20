# Landing order-handoff results

The frozen observer digest is `d9a3830d30f7789067328db7b7aafff236bd7b2738979da0a9c1d261090d7b51`. Main baseline exited 1 because it could not prove a projected-away original order. The candidate exited 0 and observed `A → cleanup → B` with the pinned Noodle v0.1.19 binary. A had one completed typed outcome, an exited process, paired projection/ack effects, and Noodle-owned cleanup. B was admitted only after cleanup through `issue.automatic`, then produced its own completed typed outcome. The planted reversed current-next dispatcher exited 1 at the admitted checkpoint.

The current-next fixture produced `dispatch → merge → readback` while persisting one merge offer. Provider objects were local fixtures; Sessions, processes, worktrees, Noodle effects, cleanup, and residue checks were physical. This is local L-class evidence with `authorizes_landing: false`; provider merge and Issue closure require their existing owner.

Six fresh consumers ran without inherited conversation. All three baseline consumers invented an unsupported `reconcile --checkpoint/--readback` command; all three treatment consumers selected the supported positional `landing consume CHECKPOINT READBACK` entry. The independent audit recorded errors `3 → 0`. This supports reduced decision error only for the three frozen current-readback cases.
