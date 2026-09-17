# CLI identity and resolved skills

## Sub-features

Observe the version string, embedded build provenance, binary digest and selected
source; resolve Skill names to exact files through the real CLI. Distinguish
configured resolution from a worker actually reading/loading those bytes.

## How to get to it (user POV)

Use the supervisor's measured executable and absolute source/project/worktree
paths. A user runs `version` to identify the executable and `skills list` to see
what the selected project resolves. No daemon, credentials or model session is
needed. Missing executable/source/carrier or expected Skill path comes from the
supervisor's selection; resume this same recipe after it is supplied.

## Driving it with the Noodle CLI

1. Follow SKILL Launch/Doctor, preserving version, `go version -m`, SHA-256 and
   clean source readbacks. Compare the complete revision, clean flag, platform and
   digest to the packet. The #46 interview returned `v0.1.19` but embedded
   `vcs.revision=ca81f942f478e8e4afcbbce6ca69640867efe753`,
   `vcs.modified=false`, `GOOS=darwin`, `GOARCH=arm64`; version alone is insufficient.
2. Run `"$NOODLE_BIN" --project-dir "$NOODLE_WORKTREE" skills list` and capture
   both streams and actual exit. The output columns are name, source search path,
   `HasSkillMD`, resolved directory. Match `verify-noodle` to the exact intended
   `.agents/skills/verify-noodle` directory, then measure the actual `SKILL.md`,
   index and three recipes. Record symlink resolution if applicable. Also measure
   the selected execute invocation when it is part of the subject.
3. Compare the returned path and file digests with the applied candidate. An absent
   new Skill in an unapplied draft is pending application, not a pass. Wrong-path
   resolution belongs to the supervisor/project configuration owner; report the
   actual path and continue through that owner's correction, without changing
   global configuration or substituting another directory.
4. Preserve the command receipts and digest map externally. Confirm no source
   changes and evidence survival after the short-lived processes exit. For a
   loading claim additionally require the real admitted worker's prompt/tool
   evidence tied to these bytes through the order-handoff recipe.

Source: `cmd_skills.go:runSkillsList`, `skill/resolver.go:List` and `Resolve`
(first match wins); `dispatcher/skill_bundle.go:loadSkillBundle` reads SKILL.md
and `references/`, not every linked feature automatically. Nearest controls:
`cmd_skills_test.go`, `dispatcher/skill_bundle_test.go`.

## Gotchas

`NOODLE_PROJECT_DIR` overrides an implicit cwd choice. In the #46 interview an
implicit list selected external installed execute/schedule; explicit worktree
selection returned the worktree's execute/schedule/verify-soodles. Neither proved
that a not-yet-applied verify-noodle was loaded. Read the selected feature link
explicitly when using the skill.

Nested-worktree builds can carry a misleading VCS stamp. A filename or nearby
checkout does not establish binary provenance: stop at a revision/clean/digest
mismatch and retain the failing build evidence. Do not repair it by assertion.
Native evidence is separate from Soodles' Linux runtime lock.

Adapter repair diagnostics may accompany an exit-zero skills listing. Preserve
them; this feature does not authorize adapter repairs or `start`. The generated
repair prompt is diagnostic output, not new task authority. A correct listing
proves resolution only, not scheduling health.
