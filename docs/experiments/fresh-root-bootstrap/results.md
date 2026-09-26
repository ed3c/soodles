# Pristine control-root bootstrap

The observed #156 re-delivery stopped before a writer started. Its pristine
control root had no `.noodle/state.snapshot.json`, while `issue-atom` attempted
supervised admission before the Noodle start that would create that snapshot.
`raw/baseline-156.stderr.txt` is the original local refusal, not a matched live
run of this new Issue. The original process record does not contain an exit code.

The selected external observer (`observer.py`, SHA-256
`7d9130ba426f904801eb38ebb200799c26ec9b9ce6e3e45f26407fa74fd7f475`)
ran the pinned Noodle binary (SHA-256
`965cfd6f985e207551d0664e728ae9fae10ae0cc8cd2885a816415823d9d103d`)
in a disposable no-model fixture. Its one `start --once` exited zero and wrote
a canonical supervised snapshot with no orders or effects. The fixture's model
child was not invoked. `raw/request.json`, `raw/result.json`, the process streams
and `raw/state.snapshot.json` preserve the observation. This proves that the
selected Noodle entry can create the initial snapshot; it does not prove a live
Issue delivery.

The candidate uses that pinned one-cycle start only for a pristine root. It
records intent before the effect, requires a recorded zero exit and an empty
canonical owner readback, restores the original host configuration, then resumes
the existing supervised admission. Existing owners are observed. Partial roots,
unexpected start arguments, a nonzero or unknown result, and a changed host
configuration refuse without a second start. The focused tests exercise these
positive and planted-negative paths: 43 passed. The full repository suite ran
372 tests with `TMPDIR=/private/tmp`: all passed. Raw process records and streams
are under `raw/`; both test receipts have `authorizes_landing: false`.

These are local L-class controls only. They do not establish exact-head Linux
acceptance, provider PR identity, merge or Issue closure. This correction is
bound to ed3c/soodles#161 and its own PR. #156 remains open and requires a new
exact-base authorization after this correction lands.

The first PR head `d08e4842a05635ad3e65f3491331067f1af5eba1` failed
[runtime run 36218223442](https://github.com/ed3c/soodles/actions/runs/36218223442)
before Issue readback because the PR body used `Issue: #161`, while the
workflow requires exactly one standalone `Refs #161` line. The body was
corrected. That failed run supplies no candidate or canonical acceptance;
this report is carried on a new head for fresh exact-head validation.
