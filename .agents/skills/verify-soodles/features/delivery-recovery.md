# Delivery recovery

Exercise interruption, readmission and cleanup behavior through existing executable oracles. They drive actual processes and, for cleanup, the locked Noodle binary. Their GitHub-shaped fields are local fixtures; no result here proves live provider merge/closure or authorizes landing.

## Preconditions and drive

Use a clean committed candidate in a Noodle worktree, a fresh evidence destination outside it, and the admitted absolute Noodle path. Begin with `./soodles runtime check` and `noodle skills list`; verify this checkout's exact skill path/digests. Record source head/tree and clean status before the drive. Do not start `noodle start` or repair missing scheduling adapters.

From that checkout, use the existing entrypoints (replace the binary path only with the already-confirmed path):

```sh
python3 -B delivery_oracle.py .
python3 -B base_recovery_oracle.py .
python3 -B cleanup_lock_oracle.py /absolute/path/to/noodle .
python3 -B -c 'import json,sys; from cleanup_oracle import cleanup_recovery_probe; print(json.dumps(cleanup_recovery_probe(sys.argv[1])))' /absolute/path/to/noodle
```

Capture each command's actual argv, stdout/stderr, exit and elapsed time in surviving evidence. These focused controls are useful during maintenance; they do not replace or repeatedly invoke canonical acceptance. The optional isolated observer carrier belongs to supervisor-selected evidence, not a skill policy choice.

## Required observations

| Existing oracle | Behavior to discriminate |
| --- | --- |
| `delivery_oracle.py` | Prepared-intent SIGKILL recovery, lost responses and dispatch gaps, one concurrent offer, legacy unknown writes, head drift, structured owner refusal and terminal projection without checkpoint rewrite |
| `base_recovery_oracle.py` | Base drift and interrupted readmission, exact subject/ancestry guards, same-base supervisor amendment of unoffered acceptance, fresh evidence requirements, offered/legacy unknown preservation |
| `cleanup_lock_oracle.py` | Lock refusal before deletion, consumed recovery, released-lock progress, moved-branch protection and no residue using real Noodle |
| `cleanup_recovery_probe` | Interrupted cleanup, moved/foreign worktree protection, unchanged-attempt refusal and legacy checkpoint recovery using real Noodle |

All selected commands must succeed and contain their actual case results. A zero exit with absent evidence is not a successful pass. For cleanup lock treatment, also require `lock_refusal_before_deletion: true` in each case: its baseline compatibility can otherwise accept an older refusal after deletion. Preserve fault signals, refused side effects/reoffers and before/after observations. Only the fixture creator removes its planted lock; never copy that operation onto a production lock. Do not freeze test count or help wording as the behavior contract. The fixed external #21 experiment additionally rejected wrong `dispatch` guidance, terminal polling and a candidate fake GREEN oracle; refer to its receipt as historical independent evidence, not a fresh run by this skill.

## Completion, cleanup and boundaries

Require unchanged candidate head/tree and clean status after the drive, fixture cleanup observations, and no remaining fixture process/worktree residue. Keep the real task worktree until its delivery owner reconciles it. A recovery pass may report scoped `VERIFIED` only with `authorizes_landing: false`; fixture `RESOLVED` fields remain fixture observations. A real Issue's terminal evidence belongs to [supervised delivery](supervised-delivery.md).

On failure, keep the nearest discriminator and classify the pass blocked. Use a fresh doctor before continuing after a material input/environment correction. Fix recipe drift within this skill's admitted boundary; a product regression stays visible and goes to the causal owner. Never remove/skip a failing case to get green. Record top-level verification invocations separately from internal child commands, intentional faults and expected refusals; do not report unmeasured counts as zero. Delivery/base success outputs contain case summaries rather than complete child CLI traces; preserve exactly the evidence available and disclose that limit.
