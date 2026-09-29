# Qualification eval audit (not a scored comparison)

## Error analysis — demonstrated process fault; behavior observation pending sealing
The real producer is killed after authorization write, after temporary receipt write, and after receipt publication. Source owner bytes are unchanged. Each same-path invocation returns authorization.output with a new-output input request, even where exact valid authorization remains. This is evidence of missing supported partial-publication recovery, not evidence that output-collision rejection itself is incorrect. Historical unnecessary requests for authorization path/SHA remain separate and are not newly reproduced by this fixture.
Fix: score identity-preserving preparation/handoff completion and its nearest refusal controls, never lower command counts on incomplete tasks.

## Evaluator design — current stage is diagnostic, no adopted score
No current candidate or formal baseline exists. Use objective checks against actual command stdout, preserved authorization identity, handoff, filesystem residue and downstream current owner. Code oracle must reject model-authored receipts without matching captured owner output. A safe blocked baseline may pass safety but fail preparation completion; do not collapse these into one PASS.
Fix: freeze independently validated oracle and controls before candidate scoring. Partial capture is INCONCLUSIVE, never an easy zero-cost win.

## Human review — full diagnostic trace
Supervisor has full source, fault boundaries and subprocess output. A fresh Noodle/Codex consumer receives neutral facts/previous invocation and current instructions, not expected outcomes or this report. This is a deterministic operational criterion; no semantic judge or synthetic human labels.

## Labeled data — bounded process-fault workload
These are real executions of injected local process faults, not claimed production incidents or representative user-frequency data. Repeats estimate model variation within one case group; they are not independent origins. Separate train/selection/confirmation by fault publication phase and schema/identity situation before tuning.

## Pipeline hygiene — new comparison boundary required
Prior #191 source/method/harness are references; no old scores enter this comparison. Freeze actual host/task/observer bytes again. Existing pinned capture adapter is reused, including EOF/process sealing, actual worktree doctor and same-profile file denial. New fixture logic must be pinned too. R3 requires a fresh supervisor to reconstruct the next fresh run from saved handoff; archived replay alone is insufficient.

## Cost accounting — no savings claim yet
Report completed command events and all exposed input/cache/output tokens, whole-turn elapsed, local control elapsed, canonical acceptance elapsed, and any human intervention independently. The absence of a successful baseline prevents a valid successful-task cost ratio. Do not claim 20% cost improvement by counting a refused task as cheap.
