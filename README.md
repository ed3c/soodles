# soodles

An evidence-first migration from noodles, with Noodle retaining runtime and worktree ownership.

Current scope: a pinned Linux amd64 Noodle runtime plus a supervised single-Issue landing checkpoint. Runtime works locally and in Actions; the Codex supervisor transports landing requests through the existing GitHub connector.

## Run

Obtain the release asset named in `policy/runtime.lock.json` from [ed3c/noodle releases](https://github.com/ed3c/noodle/releases), verify its archive digest, and extract its binary outside the source tree. The Actions workflow automates release/tag/archive/binary readback before execution.

```sh
./soodles runtime check /absolute/path/to/noodle
./soodles acceptance verify /absolute/path/to/noodle > /tmp/soodles-acceptance.json
```

Acceptance requires a clean committed candidate. While editing, use `python3 -B -m unittest discover -s tests -v`; after the final commit, run canonical acceptance once for that head. Receipts belong outside the source tree.

## Data flow

Exact lock → host/digest/version admission → focused refusal controls → real Noodle worktree fixture → Git residue/head readback → non-authorizing JSON receipt.

`runtime.yml` runs that acceptance on the exact PR head without secrets or write permissions and uploads the evidence. The supervisor selects the verifier outside the candidate and admits the exact candidate separately. Candidate self-test success cannot choose its own landing authority.

## Supervised landing

The supervisor pins `./soodles landing identity` (covering landing.py, soodles.py and the runtime lock), reviews the exact Issue/PR and acceptance evidence, and supplies a claim JSON with exactly: `repository`, `issue`, `pr`, `head`, `tree`, `base_head`, `run_id`, `run_attempt`, `worktree`, `control_root`, `verifier_sha256`. The repository is fixed to `ed3c/soodles`; paths and identities are never auto-corrected. Store claims, raw readbacks and checkpoints outside the source/worktree lifecycle.

The readback JSON contains raw GitHub responses under `pr`, `issue`, `run`, `jobs`, `commit` (Git commit API), and `branch`. After merge, include `merge_commit` from the Git commit API. Capture these through the provider adapter; do not accept files from the candidate as provider truth.

```sh
./soodles landing start /tmp/claim.json /tmp/readback.json /tmp/checkpoint.json
./soodles landing advance /tmp/checkpoint.json /tmp/readback.json
```

The CLI returns either an exact merge/close request, `readback`, or `reconcile`. Execute an offered provider request once through the existing connector. Then refresh provider readbacks and call `advance`. No credentials are passed into candidate code. A pending checkpoint prevents duplicate writes even if the previous response was lost. Do not reset it to retry.

When `reconcile` is offered:

```sh
./soodles landing reconcile /tmp/checkpoint.json /absolute/path/to/noodle
```

The checkpoint becomes RESOLVED only after the provider merge, completed Issue, local main and Noodle cleanup have been read back. This is a supervised fallback, not an installed unattended Actions lander or a production generation scheduler. Administration permissions and classic-protection configuration are not universal prerequisites; all existing GitHub rules still apply.

If a source fix changes the pinned verifier during interrupted local reconciliation, the supervisor can use `landing resume CHECKPOINT FRESH_CLAIM`. It accepts only a changed verifier digest with identical provider/local identities after merge and closure readback; it preserves both offered writes and emits no provider request. Network Git retains the carrier's proxy route while excluding provider credentials and Git environment injection.

If Noodle stops after removing the worktree directory, `landing reconcile` can finish the remaining exact branch through Noodle. It refuses a moved branch, another checkout, or an unchanged failed cleanup observation. Canonical acceptance includes five real SIGKILL/recovery controls in `cleanup_oracle.py`; these use local provider fixtures and retain their transcripts in the runtime receipt.

Start with [Issue #1](https://github.com/ed3c/soodles/issues/1), the executable boundary in `soodles.py`, and `tests/test_admission.py`. `docs/` records N-class observations; it is not correctness authority.

Issue #8 adds observed target-ref-lock recovery to that same CLI: a present lock returns `cleanup.ref_lock` and preserves the lock; after its owner removes it, matching persisted blocked readback permits one cleanup attempt. Old checkpoint field absence does not imply a lock transition. No force flag or lock-deletion command is added. The four-case standalone `cleanup_lock_oracle.py` runs in canonical acceptance in addition to the five earlier cleanup controls.

For supervised verification, select an immutable external oracle before evaluating the candidate and observe real Git state outside candidate verdict code. Keep the current publishing verifier fixed; neither a merge nor `landing resume` authorizes a new judge. A producer/consumer/checkpoint/test correction is one Issue when cause, owner and rollback boundary match. Actual baseline, treatment, isolation and provider evidence belongs to Issue #8 and its exact Actions runs.
