# Landing continuation: one Issue atom

Origin: ed3c/soodles#106. Baseline: `cda8153eb943b924af94c4ef78b7d51999e29ca5`.
This report is evidence, not landing authority (`authorizes_landing: false`).

The observed barrier was command assembly: the durable landing owner already
selected `advance` or `dispatch`, but CLI output omitted runnable argv even
when both paths were confirmed. No historical wrong-route failure was observed.
The correction binds only current `next.argv` and `next.known.readback` in
`soodles.py`; it preserves the domain owner and every required provider GET.
The P-class recipe tells the consumer to refresh those GETs first and consume
the array literally. This is a combined CLI/recipe treatment, not prose ablation.

## Bounded observations

| Observable | Baseline | Treatment |
| --- | ---: | ---: |
| Fresh native consumer contexts | 3 | 3 |
| Captured owner transition calls | 12 | 12 |
| Exact current argv copied | 0/12 | 12/12 |
| Wrong operation among captured owner calls | 0/12 | 0/12 |
| Supported syntax help calls | 6 | 0 |
| Newly emitted merge requests | 3 | 3 |
| Newly emitted close requests | 0 | 0 |
| Observed fixture provider transport | 0 | 0 |
| Frozen CLI projection predicate | RED | PASS |
| Frozen safety predicate | PASS | PASS |
| Rejected planted transcript mutations | 7/7 | 7/7 |

Baseline runs are r11/r36/r24; treatment runs are r23/r12/r35.
All three prepared cases emitted exactly one request; offered cases retained
unknown merge outcomes without reoffer; recovery cases preserved the missing
merge-commit refusal and stopped at close preparation. The frozen CLI observer
also exercises historical dispatch, invalid/foreign input, paths with spaces,
fresh-claim invalidation and terminal idempotency. Planted transcript defects
prove observer sensitivity, not historical failures or source-mutation coverage.

The defensible improvement is availability and observed literal consumption of
owner-selected syntax. Zero-to-zero wrong routes is nonregression. Help counts
are descriptive only; they do not establish the four decision-path metrics,
cognition, elapsed-time superiority, or globally shortest Agent behavior.

## Recording limitation retained

r24 recorded one extra submitted recovery argv rejected by the recorder before
owner invocation. Its consumer reported a preceding successful fixture refresh
whose event was absent from the retained stream. The receipt preserves the
reported hash/time and exact refusal. Cause is unknown. A subsequent fresh
refresh supplied materially changed input before continuation. This anomaly is
not attributed to baseline CLI behavior and is not an extra wrong owner route.
All r24 evidence is retained, but full trace completeness and a clean 3-versus-3
cost comparison are not claimed. The two other baseline consumers independently
show the same four successful routes with reconstructed argv.

Native model/effort identity and complete platform traces are unavailable.
Separate directories plus instructed read restrictions are not security isolation.
The shared recorder times actual owner subprocesses, not thinking or provider
latency. Fixture readback events are not physical GitHub API requests. No live
Issue closure, handoff across hosts, generation-wide result, or A-to-B continuity
is inferred from these consumers. The coding-agent `decision-path-review`
comparison was not run: exact model/effort, coding snapshots/final-diff traces and
provider-wait separation are absent. No FASTEST/ORIENTATION/DEAD_ENDS/REWORK
improvement is claimed.

## Authority and verification

The observer was authored independently and frozen before candidate edits:
`6116fd814314edafe1e2f2352b10bdba6c0ad9bfe9a681b103f9f744d52bd093`.
Task/recorder bytes and initial packets were pinned before fresh consumer launch.
`raw/agents.json` retains initial inputs, instructions, exact event streams,
consumer receipts and final states. Its cleanup receipt records evidence survival.
`raw/independent-audit.json` re-derives results without repairing consumer output.
`raw/verification.json` preserves focused tests, setup failures and the existing
P-class observer applied to its supported pending/recovery cases. The new unit
entry invokes the frozen real-process observer, including its negative controls.

The first landing unit-test attempt had incomplete sparse scratch inputs, not
a candidate runtime failure. Exact pinned wrapper/test dependencies were added
before the changed-input rerun: 49 landing tests passed. Existing delivery and
base-recovery process oracles passed. Full canonical acceptance remains unchanged
and runs on the actual final GitHub candidate head; this report does not assert
that a future run or landing already happened.

For real delivery, the external publisher was selected from the baseline before
candidate acceptance, digest
`5e0f4f373902a208f51d0f37213e670f49fa3daa520a0113361cee14d8c3bbd1`.
One PR carries code, P-class guidance, controls and byte-bound evidence. Its
runtime readback must match candidate head/tree/run/attempt before that publisher
can emit a merge request. Subsequent merge and Issue closure require fresh raw
provider readback and the existing terminal classification. Synthetic receipts
and candidate tests cannot select or replace this publisher.

## Reusable vocabulary

Use `single owner`, `current-next projection`, `fresh readback`, `verbatim argv`,
`unknown-write preservation`, `nearest discriminating control`, `positive and
planted-negative control`, `baseline/treatment`, `nonregression`, `exact-head
acceptance`, and `receipted terminal classification` when specifying this atom.
Do not replace these observable obligations with a request to merely apply
Clean Code, an idempotency key, or a globally shortest path.

## First candidate refusal and same-atom migration

Head `0d6fef72ca43f9904ac7fe69cb4eb33ec79ac84c`, runtime run
`35521512447` attempt 1, passed fresh Issue/evidence binding but failed canonical
acceptance (189/190 tests passed). The historical experiment test read the
current recipe instead of its archived `source_provider_sha`; this correction
legitimately changed that recipe. Quality reporting passed and no merge was
offered. The failed head was preserved and was not rerun.

Issue #106 was amended and read back before expanding the write boundary to
`tests/test_fresh_delivery_decisions.py`. Prior acceptance was invalidated.
The test now uses `git show` at its recorded 40-character immutable source SHA,
keeping every complete-source hash, loaded-text and loaded-hash assertion.
Four direct provider source reads independently match the archived evidence.
The workflow already fetches complete Git history. Its new-head run must verify
the Git integration and all acceptance again. Historical experiment data, current
CLI/P treatment, frozen controls and the externally selected publisher remain
unchanged. This migration is a consumer dependency of the same recipe change.
