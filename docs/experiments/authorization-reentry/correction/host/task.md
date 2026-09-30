The previous local Session left the current task facts in workspace/ inside your assigned output directory. Read workspace.json, work.md and the control root AGENTS.md, then perform the local task within its authorization. Preserve the actual result and handoff for the next Session.

For product CLI invocations use the transparent recorder as a standalone command:
ABS_PYTHON -B ABS_DRIVE WORKSPACE_JSON UNIQUE_LABEL -- PROGRAM ARG ...
ABS_DRIVE is drive.py in the public worktree. It applies the supplied host environment and executes your exact argv; it does not choose an owner or supply an answer. Save task output from actual CLI stdout. Keep carrier outcome reporting separate.
