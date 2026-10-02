# Issue #109 — interruption after cleanup

This atom adds `issue resume A_CHECKPOINT B_ENVELOPE SHA256` to the existing
Issue execution owner. The supervisor selects A and B and supplies the complete
invocation. The entry validates resolved original A cleanup, fresh absence of
the worktree, branch, and registration, and retained original completion.
It then delegates to the existing admission owner. It writes no checkpoint,
private ledger, or cleanup state. Existing automatic proposal bytes, mailbox
ownership, current orders, and retained effects still prevent duplicates.

## Fixed subjects and observed controls

Baseline: `2384e68244e3bfb48ec9d1205b7572e2ce9c9703`.
The supervisor froze `resume_oracle.py`, `observer.py` and `task.md` before the
formal comparison; their exact hashes are in Issue #109 and the manifest.
The external publisher is the baseline checkout, with landing identity
`fbdf70d8f8deea5d316bd52cb1e3019703fe51db3e4d03f7868d1fb450ce6d5b`.
It is distinct from the candidate and was selected before acceptance.

| Observation | Result |
| --- | --- |
| Same external physical observer on baseline | RED: missing `issue resume` entry |
| Candidate | GREEN: A, cleanup, SIGKILL, resume, publication, SIGKILL, readback, B, retained readback |
| Planted `publish_once` unlinking an existing mailbox | RED: unknown publication repeated or owner state changed |
| Consumer processes | Externally waited exits `-9, -9, 0, 0` |
| Unknown publication readback | Existing mailbox bytes, inode and mtime preserved; `published: false` |
| Retained B readback | `previously_admitted`, no mailbox creation or snapshot mutation |
| Real Noodle lifecycle | One original A and B session; completed nonblocking outcomes; waited runtime exits; Noodle cleanup and zero residue |
| Unit suite before exact-head Actions acceptance | 200 tests passed |

The physical experiment uses the pinned real Noodle binary and a deterministic
Codex protocol fixture. It launches no actual Codex model and writes nothing
to GitHub. The parent observer stays alive while the consumer process is killed.
This proves consumer interruption, not whole-machine failure. Noodle is stopped
during the guarded admission/readback interval. This claim excludes concurrent
scheduler/writer races, retained-history garbage collection, and cross-host
recovery. Source labels the legacy lifecycle driver's synthetic `{published: true}`
adapter return. Actual admission evidence comes from the killed CLI process
and preserved mailbox/readbacks, not that adapter return.

## P-class consumption

Two native consumers started with `fork_turns: none`. One received the baseline
recipe and the other received the treatment. Each drove three independent
fixture subjects: absent, pending, and retained B. Both used the same frozen
candidate implementation, neutral task, and complete supervisor-supplied
invocation. Only recipe bytes changed between arms. This measures consumption
of supplied commands. It does not measure unsupervised command discovery or
compare baseline and candidate runtime behavior.

Both arms executed all three supplied invocations literally and legally: 3/3
versus 3/3. Both preserved pending/retained effects and stopped for the named
Noodle readback. This supports scoped nonregression only. There is no observed
error-rate reduction, command-count reduction, token saving or statistically
established decision-cost improvement.

`raw/pclass.json` preserves initial instruction/input reads, recorder requests,
stdout/stderr, exits, file digests, timings and consumer handoffs. It is
consumer-recorded subprocess evidence, not a complete platform transcript.
Observed model, tokens, context window and compaction remain unknown. Source
hashes were checked by the supervisor after the drive; consumers only read the
provided identity manifest. The candidate unit suite replays the fixed evidence
predicates; neither that replay nor this report authorizes landing.

## Delivery

All producer and consumer changes, controls, instruction bytes, and evidence
share one Issue #109 and one PR. The canonical manifest binds every required
artifact and both instruction digests. The existing candidate-evidence and
canonical-runtime workflow verifies the final exact candidate. The externally
selected cloud landing owner then consumes provider readback. Final merge,
closure, and the RESOLVED receipt belong to that owner. This report does not
fabricate them before those effects occur.

Independent read-only review found no blocking issues; its raw receipt is retained
in `raw/pclass.json`. It reviewed working-tree code and recorded evidence and did
not rerun physical acceptance or perform provider writes.
