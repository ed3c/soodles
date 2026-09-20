---
name: schedule
description: Materialize the one externally admitted Soodles Issue through the shared validator.
schedule: When Noodle requests a Soodles schedule decision.
---

# Schedule the admitted Issue

## Establish scheduler identity first

Do not infer the scheduler role from the working directory, Skill availability,
or this file being read. Read only the current `NOODLE_SESSION_ID`. If it is
absent, this Skill does not establish a Noodle schedule Session: do not require
an Issue, envelope, or launcher for the caller's original task. Return to the
already-authorized task owner; analysis/review can continue from its requested
subject.

If `NOODLE_SESSION_ID` is present, read the current Noodle control root's
`.noodle/sessions/<NOODLE_SESSION_ID>/spawn.json`. Treat this as a schedule
Session only when its `session_id` equals the current ID, `skill` is exactly
`schedule`, and `worktree_path` identifies this checkout. A missing or
mismatched spawn is a Noodle/supervisor role-identity refusal for the schedule
operation only; do not compensate by constructing admission inputs or changing
canonical state.

The spawn readback establishes the Session role, not Issue admission. The
supervisor-selected launcher and current Noodle owner establish the admitted
Issue/envelope/order/stage after role identity. Do not derive them from the
checkout, Issue prose, historical receipts, or model memory.

## Consume the admitted launcher

Only after the schedule role is established, read
`SOODLES_ADMISSION_LAUNCHER`. Require the selected path to be present and
executable; never search for, synthesize, export, or reuse a historical launcher
as a replacement. Invoke that executable with the single argument `automatic`.
It fixes the external envelope and validator; neither this Skill nor Issue prose
selects authority. A missing launcher/input requires its supervisor for this
schedule operation, not for unrelated work.

Consume its current structured result. Noodle owns the canonical order,
worktree and process. The launcher publishes a conditional first-admission
proposal only after fresh provider and owner readback. Never reconstruct an
order, overwrite `orders-next.json`, request an implicit restart, or write
canonical state. An owned/previously-admitted result is an observation, not
permission to establish another writer. A refusal names its owning input.

Do not dump the environment. Do not edit target source or perform delivery from
the schedule task. This Skill is guidance; the installed validator/worker
boundary performs enforcement.
