# soodles

An evidence-first migration from noodles, with Noodle retaining runtime and worktree ownership.

Current scope: one pinned Linux amd64 Noodle binary, local admission, and real worktree controls. This bootstrap does not yet run an autonomous Issue-to-closure lifecycle.

## Run

Obtain the release asset named in `policy/runtime.lock.json` from [ed3c/noodle releases](https://github.com/ed3c/noodle/releases), verify its archive digest, and extract its binary outside the source tree. The Actions workflow automates release/tag/archive/binary readback before execution.

```sh
./soodles runtime check /absolute/path/to/noodle
./soodles acceptance verify /absolute/path/to/noodle > /tmp/soodles-acceptance.json
```

Acceptance requires a clean committed candidate. While editing, use `python3 -B -m unittest discover -s tests -v`; after the final commit, run canonical acceptance once for that head. Receipts belong outside the source tree.

## Data flow

Exact lock → host/digest/version admission → focused refusal controls → real Noodle worktree fixture → Git residue/head readback → non-authorizing JSON receipt.

`runtime.yml` runs that acceptance on the exact PR head without secrets or write permissions and uploads the evidence. It does not authorize merge. Trusted provider admission, protection, Issue closure and production reconciliation remain uninstalled.

Start with [Issue #1](https://github.com/ed3c/soodles/issues/1), the executable boundary in `soodles.py`, and `tests/test_admission.py`. `docs/` records N-class observations; it is not correctness authority.
