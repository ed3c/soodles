# Bootstrap observations

Class: N. Atom: [ed3c/soodles#1](https://github.com/ed3c/soodles/issues/1).

At initial head `ef929f126dcfda5894547f031d5ca9f0ca3baea3`, soodles contained only README.md, no Issues or workflows, and main read back unprotected. The initial bootstrap Issue therefore records its scope directly; there was no existing soodles authoring path to invoke.

Pre-implementation Linux experiment: the published Noodle v0.1.19 archive and extracted binary matched the digests subsequently recorded in `policy/runtime.lock.json`. The binary returned v0.1.19, created a worktree, executed Git path/head readback inside it, refused execution in an absent worktree and cleaned its worktree/branch. This ran in ChatGPT Work Linux, not GitHub Actions or a Codex generation.

An additional probe returned outer exit 1 for a child exiting 23, with `process exited with code 23` on stderr. No exact child-exit propagation claim is made. Default Noodle adapter diagnostics also appear in a bare fixture; they are retained in transcripts and do not prove daemon readiness.

The current candidate's evidence must be obtained from `runtime-evidence-<exact head>` in its actual Actions run and the local acceptance JSON. No future run is represented here as already passing. JSON contains source head/tree, observed binary/version, command exits, worktree cleanup readbacks and explicit non-claims.

Issue #3 was withdrawn as not planned after the owner corrected the assumption that Administration access/classic protection is a prerequisite for all automation. Those permissions are dependencies of noodles' current protection reader, not requirements of every supervised carrier.

Issue #4 adds a single-Issue supervised landing boundary. Initial trust comes from the supervising session's pinned implementation and exact claim outside the candidate. Unit controls exercise refusal and lost-response transitions; the actual provider run and Noodle cleanup must be read from the Issue's execution receipt. A proposed implementation or a passing unit fixture is not recorded here as future provider success. This does not establish an unattended Actions lander, independent default-branch verifier or full production generation loop.

Issue #6 reproduced an interrupted-cleanup deadlock at main `4ab2206`: a fixture Git shim delivered SIGKILL to the actual pinned Noodle process after real worktree removal and before branch deletion. The old soodles CLI refused `worktree.branch`; Noodle's existing missing-directory cleanup could finish the same remaining branch. The candidate's focused oracle passed recovery and all planted controls, while the old implementation failed the same recovery discriminator. Final acceptance and provider landing evidence belong to the Issue/run receipts; this observation is not a production generation claim.

Issue #8 reproduced another failure at `09e6e12`: after real SIGKILL and a fixture-owned ref lock, removing the lock did not change the existing cleanup fingerprint, so reconcile refused while Noodle could finish. A standalone external oracle was frozen before implementation at SHA256 `da40093a1d3f180920dccdc9d562d95e64e2c2ece53a3490bd75c45e99c4f7ff`. The same oracle fails on that baseline and passes the candidate's four local lock controls. The atom changes the producer, consumer and optional checkpoint field together; no helper/file split or new scheduler is involved.

Local separate-UID isolation was unavailable: this carrier mapped only UID 0, rejected chown to 65534, denied namespace creation and did not implement Landlock. Local results therefore do not establish isolation. A supervisor-owned Actions experiment can supply the missing evidence without selecting its judge from the candidate or default branch. Exact candidate/experiment commits, actual run results and terminal provider receipts must be read from Issue #8; this N-class note grants no authority and predicts no successful run.
