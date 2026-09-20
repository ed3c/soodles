# Issue 103 — schedule entry owned by CLI

## Supported result

The new read-only `./soodles issue inspect` owns the deterministic decision:
current Noodle Session and matching scheduler spawn → selected launcher capability
→ one exact `next.argv`. The schedule Skill consumes that projection instead of
implementing identity checks in model reasoning. Existing launcher admission,
canonical order ownership, worker revalidation and provider delivery remain the
effect boundaries. Inspection does not execute the launcher or admit work.

The current Noodle scheduler supplies `NOODLE_SESSION_ID` and
`NOODLE_WORKTREE`. It does not promise worker-only `NOODLE_PROJECT_DIR`.
The final implementation has no such extra prerequisite. Missing role evidence
belongs to Noodle; a confirmed scheduler's missing launcher belongs to the
supervisor. Ordinary Sessions return to their original task.

## Frozen executable controls

Baseline: Soodles `9c8f22c98c42b0fa4cc912007dc2fde2b5a65381`.
External observer v2 SHA-256:
`72316f85f29612d2d39435483efe46095da8027936830eda73831e53c152460d`.

The old CLI lacks the inspect operation and fails all 13 new interface controls.
The candidate passes all 13, including the exact fixture-launcher handoff.
This is an executable interface gap/cure, not evidence that 13 historical
scheduler actions were unsafe. Each inspect leaves the fixture unchanged and
does not execute its launcher; all disposable CLI directories are removed.

The frozen classifier rejects five planted evidence defects: wrong argv, false
completion, mutation, absent execution observation and execution during inspect.
These controls test observation sensitivity, not a live provider incident.

## Fresh P-class/CLI consumer comparison

Six final native consumers were requested with `fork_turns=none`, three per arm.
Each received one matched case and the same neutral task. Only the assigned
Skill/CLI bundle differed, apart from fresh per-run fixture paths. The fixture
environment contains no worker-only project variable. Consumers received no
expected answer, sibling result or experiment report.

| Case | Baseline | Treatment | Launcher effects |
| --- | --- | --- | --- |
| Ordinary Session | original task | not_applicable / original task | 0 / 0 |
| Scheduler missing launcher | supervisor prerequisite | supervisor prerequisite | 0 / 0 |
| Scheduler with selected launcher | owned | owned | exactly one automatic / one automatic |

Final wrong decisions: **0 → 0**. All six preserve canonical fixture bytes and
have final fixture cleanup observations. This supports **scoped nonregression**
for the combined CLI/P-class treatment, not lower error probability or a prose
ablation claim. Treatment consumers use the actual inspect entry and its result.

Recorded subprocess calls are 6 → 4 across these three cases. That is bounded
telemetry only: it does not measure hidden reasoning, tokens, complete native
tool activity or general Agent cost. Model/config provenance and a complete
platform transcript are unavailable. Native contexts share storage; separate
directories and task restrictions are not security isolation.

## Preserved corrections

All 18 original consumer records are retained in `raw/agents.json`:

1. First six: unscored setup wave. The treatment fixture wrapper named an
   absent `/usr/local/bin/python3`, so it failed before entering the CLI.
   The whole wave is excluded; no selective successful pooling.
2. Second six: exploratory, superseded producer assumption. The wrapper was
   fixed, but review found the unnecessary `NOODLE_PROJECT_DIR` requirement.
   These observations are not final-candidate behavior evidence.
3. Final six: matched current-producer fixtures with the final Skill/CLI bytes.

The initial observer, source bytes and CLI results remain preserved. Supervisor
readback of Noodle `98d845608d64a78b1c116a8f0be6a6de47c8b2b2` distinguishes
`spawnSchedule` from `spawnCook`; it caused the external observer correction
before final acceptance. No Noodle source or production environment was changed.

## Validation and delivery boundary

Five production schedule-entry tests and 28 existing Issue admission/execution
tests pass locally. A broader snapshot-only run executes 189 tests with two
Git-context failures: the PR90 historical-object regression and quality HEAD
test need a real Git checkout/history. Those failures are retained as a local
carrier limitation, not reclassified as PASS. Exact-head Actions perform the
canonical acceptance in the proper checkout and must pass before delivery.

The generic skill frontmatter validator rejects the pre-existing `schedule`
field; it was retained because Noodle consumes that field. This is not a reason
to remove the scheduler's supported metadata.

Independent source review found no correctness change needed in the final
implementation and verified the required scheduler fields against pinned Noodle
producer source. The independent evidence audit is recorded separately.

All candidate evidence is non-authorizing. One PR owns this correction and all
listed artifacts. The supervisor pins the unchanged external cloud landing
owner from the baseline before acceptance; exact-head candidate/runtime/quality
results and provider readbacks govern its merge/closure requests. This report
does not preclaim those future provider effects.

No live macOS scheduler dispatch, launcher installation, daemon restart,
cross-host ownership migration, automatic A → cleanup → B, or production
admission is established by this bounded atom.
