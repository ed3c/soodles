# Issue 101 — schedule role before launcher admission

## Physical baseline

The preserved Noodle session `schedule-20260916-170423-d53732` is a real
`process` Session whose `spawn.json` binds the same `session_id`,
`skill: schedule`, and the Soodles worktree. Its preserved `meta.json` records
the actual command refusing because `SOODLES_ADMISSION_LAUNCHER` was unset and
exiting 64. That refusal remains a valid schedule-operation refusal.

The old schedule Skill did not first establish that role. It named the launcher
immediately and stated that a missing launcher/input required the supervisor.
That wording allowed a generic local analysis/review Session that merely read
the Skill to overgeneralize a schedule-only prerequisite.

Current Noodle main `98d845608d64a78b1c116a8f0be6a6de47c8b2b2`
already builds process child environment from `os.Environ()` in
`dispatcher/command.go:buildDispatchEnv` (apart from the explicit
`CLAUDECODE` removal), so this atom does not change Noodle environment
propagation.

## Correction

The schedule Skill now orders decisions as:

`current NOODLE_SESSION_ID → current Noodle spawn.json identity → launcher capability → automatic admission`

The identity readback consumes only `session_id`, `skill`, and
`worktree_path`. It does not dump environment variables and does not recover a
launcher from historical evidence.

A missing `NOODLE_SESSION_ID` means the Skill has not established scheduler
role and therefore cannot make the launcher a prerequisite for the caller's
original task. A present ID with missing/mismatched spawn refuses the schedule
operation as role identity. Only a matching schedule spawn reaches launcher
admission; at that point a missing launcher still belongs to the supervisor.

## Focused controls

`tests/test_schedule_role.py` reuses the preserved real session as the positive
identity control and rejects:

- absent current Noodle Session identity;
- missing spawn metadata;
- foreign `session_id`;
- non-`schedule` skill;
- foreign worktree.

It also asserts that the retained Skill places role readback before launcher
admission and preserves the no-environment-dump / no-historical-launcher
constraints.

This proves the role/capability distinction is mechanically decidable from
existing owner state and that the repository guidance no longer declares the
launcher prerequisite before that decision. It does not claim model-wide
instruction compliance, create admission authority, or authorize landing.
