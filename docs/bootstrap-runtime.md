# Bootstrap observations

Class: N. Atom: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).

At initial head `ef929f126dcfda5894547f031d5ca9f0ca3baea3`, soodles contained only README.md, no Issues or workflows, and main read back unprotected. The initial bootstrap Issue therefore records its scope directly; there was no existing soodles authoring path to invoke.

Pre-implementation Linux experiment: the published Noodle v0.1.19 archive and extracted binary matched the digests subsequently recorded in `policy/runtime.lock.json`. The binary returned v0.1.19, created a worktree, executed Git path/head readback inside it, refused execution in an absent worktree and cleaned its worktree/branch. This ran in ChatGPT Work Linux, not GitHub Actions or a Codex generation.

An additional probe returned outer exit 1 for a child exiting 23, with `process exited with code 23` on stderr. No exact child-exit propagation claim is made. Default Noodle adapter diagnostics also appear in a bare fixture; they are retained in transcripts and do not prove daemon readiness.

The current candidate's evidence must be obtained from `runtime-evidence-<exact head>` in its actual Actions run and the local acceptance JSON. No future run is represented here as already passing. JSON contains source head/tree, observed binary/version, command exits, worktree cleanup readbacks and explicit non-claims.

Issue #3 was withdrawn as not planned after the owner corrected the assumption that Administration access/classic protection is a prerequisite for all automation. Those permissions are dependencies of noodles' current protection reader, not requirements of every supervised carrier.

Issue #4 adds a single-Issue supervised landing boundary. Initial trust comes from the supervising session's pinned implementation and exact claim outside the candidate. Unit controls exercise refusal and lost-response transitions; the actual provider run and Noodle cleanup must be read from the Issue's execution receipt. A proposed implementation or a passing unit fixture is not recorded here as future provider success. This does not establish an unattended Actions lander, independent default-branch verifier or full production generation loop.
