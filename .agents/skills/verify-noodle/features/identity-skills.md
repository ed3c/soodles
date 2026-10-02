# CLI identity and resolved skills

## Sub-features

Observe the version string, embedded build provenance, binary digest and selected
source. Use the real CLI to resolve Skill names to exact files. Distinguish
configured resolution from a worker that actually reads or loads those bytes.

## How to get to it (user POV)

Use the selected executable. `version` reports its version. For `skills list`,
supply the absolute target project path. It reports that project's resolution. A source
checkout is required only for a source/build correspondence claim. Neither read
needs an admitted worktree, daemon, credentials or model session. The supervisor
resolves available inputs; unknown executable/project identity remains with its owner.

## Driving it with the Noodle CLI

1. Select the needed observation, not every item in this recipe. For version,
   run `"$NOODLE_BIN" version`. For source/build correspondence, additionally
   read `go version -m "$NOODLE_BIN"`, the binary SHA-256 and selected source
   revision and clean state. Compare exact `vcs.revision`, `vcs.modified`, GOOS,
   GOARCH and digest with the selection. A version string alone cannot prove
   that stronger claim. Reuse applicable observations under the owning skill's
   [Doctor conditions](../SKILL.md#doctor).
2. For resolution, run `"$NOODLE_BIN" --project-dir "$NOODLE_PROJECT" skills list`
   and capture both streams and exit. Match the requested skill to its intended
   resolved path. If exact file identity is required, measure the selected files
   and resolve symlinks; do not hash every recipe or unrelated skill by default.
3. For resolution/activation verification, compare the returned path and any
   required file digests with the selected candidate. An absent
   new Skill in an unapplied draft is pending application, not a pass. Wrong-path
   resolution belongs to the supervisor/project configuration owner; report the
   actual path and continue through that owner's correction. Do not change
   global configuration or substitute another directory.
4. Retain the observed command results and any required digest map in the existing
   task record or selected external evidence destination. For a
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
checkout does not establish binary provenance. If the revision, clean state or
digest does not match, stop and retain the failing build evidence.
Do not repair the mismatch by assertion.
Native evidence is separate from Soodles' Linux runtime lock.

Adapter repair diagnostics may accompany an exit-zero skills listing. Preserve
them; this feature does not authorize adapter repairs or `start`. The generated
repair prompt is diagnostic output, not new task authority. A correct listing
proves resolution only, not scheduling health.
