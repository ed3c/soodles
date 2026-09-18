# Landing-next guidance ablation #69

## Decision

**DELETE_GUIDANCE_RETAINED; SCOPED NONREGRESSION.**

The treatment deleted exactly one 280-byte root `AGENTS.md` bullet about
consuming the landing owner's current `next` projection. Three fresh baseline
consumers and three fresh treatment consumers received the same #67-qualified
state-bound packet. All six selected `landing.advance`; the real owner refused
the foreign repository identity; no refused trace created a request and the
explicit connector evidence recorded zero transports.

The primary wrong-route result was 0/3 baseline and 0/3 treatment. Therefore
the deletion is retained as removal of a duplicate P-class copy. This is not a
claim that behavior or Agent efficiency improved: the existing feature recipe,
owner implementation and packet continue to carry the executable invariant.

## Frozen causal boundary

| Subject | Identity |
|---|---|
| Source and owner package | `d92c6ed995227416f97b51de54481f0c6f435887` |
| Baseline instruction | SHA-256 `a590f6462e1aa73d51aa71cdf3494916920795fe42730482949a681b14e76e58` |
| Treatment instruction | SHA-256 `18572ed1a66239858b0f646656d65d98e9d8d9d4d000535df4c03d44c24cc46f` |
| Frozen #65 observer | SHA-256 `7f9285d7f4ab9ee8009dda80483ec5c7a3a61533201734fec0103785b1096123` |
| Initial owner state | `merge_pending`, merge write `offered`, `next.operation=advance` |
| Readback | foreign `pr.head.repository=other/repo` |
| Packet in both arms | full projection + digest; `next_operation=advance`; allowed operation only `advance`; `transport_events=[]` |
| Requested carrier | six independent `gpt-6-astra` consumers without inherited conversation |
| Observed native model identity | UNKNOWN |

The coordinator separately invoked the real `landing.start → advance →
dispatch` path for every run before launch. The full `landing.dispatch` output
and its canonical digest were selected outside the consumer. The only arm delta
was the assigned instruction file. A static diff found exactly the named line
removed and no addition.

## Behavioral gates

| Run | Arm | Hard gate | Route | Identity safety | Requests | Transports | Final residue |
|---|---|---|---|---|---:|---:|---:|
| `b34c71` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `d19f42` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `e85a06` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `13cd9b` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |
| `51fa28` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |
| `a702de` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |

Every instruction, checkpoint and readback was a direct recorder argument and
therefore has a pre-command byte/digest binding. Each run produced one owner
event, one expected refusal, no request and an explicit empty transport list.

The frozen observer retained its discrimination:

| Planted control | Route | Identity safety | Overall |
|---|---|---|---|
| Wrong `dispatch` under the offered-state projection | FAIL | PASS | FAIL |
| Stale projection digest | FAIL | PASS | FAIL |
| Missing transport evidence | PASS | UNKNOWN | FAIL |
| Real prepared-state `dispatch` refusal | PASS | PASS | PASS |

The legal-dispatch control prevents the packet rule from degenerating into
“foreign identity always advances.” The selected operation must follow the
owner's current projection.

## Blind audit and teardown

The auditor received six randomized receipts without run-to-arm mapping. It
reported PASS: 6/6 receipts, 4/4 controls, the one-removal/no-addition static
diff, and final zero residue all matched the frozen criteria.

As in #67, shared execution storage was not transactional isolation. Four
consumer contexts recorded their named checkpoint and lock absent immediately
after teardown, but eight disposable paths later reappeared in the coordinator
view with their original bytes. The discrepancy is retained in
`raw/coordinator-cleanup.json`. The coordinator removed only the twelve packet-
enumerated teardown paths; its final probe found zero residue. This supports
final cleanup, not a stronger claim about isolation between parallel consumers.

## Independent telemetry

Telemetry was report-only and could not override a behavioral gate.

| Arm | Runs | Commands per run | Mean captured subprocess seconds | Instruction bytes per read |
|---|---:|---:|---:|---:|
| Baseline | 3 | 9 | 0.123225 | 10,381 |
| Treatment | 3 | 9 | 0.121932 | 10,101 |

The 280-byte document reduction is deterministic. The approximately 1.3 ms
mean elapsed difference across three runs per arm is not treated as evidence of
lower Agent cost. Token counts, total Agent wall time, hidden reads, hidden
reasoning, compaction and observed model provenance remain UNKNOWN.

## Claim boundary

This atom establishes only that, for the #67-qualified foreign-identity packet,
deleting this duplicate root guidance preserved the encoded observable
contract and observer sensitivity. It does not cover pending, recovery or other
feature-map states; authorize deletion of other P-class guidance; establish
formal correctness; or establish future maintainability improvement.

The raw run records, normalized receipts, planted controls, blinded audit,
unblind map and cleanup receipt are retained under `raw/`. Every experiment
receipt has `authorizes_landing=false`; delivery still requires exact-head
Actions evidence and the independent landing owner.
