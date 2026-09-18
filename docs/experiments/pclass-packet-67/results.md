# State-bound P-class packet #67

## Decision

**TREATMENT_PACKET_QUALIFIED; NONREGRESSION_ONLY.**

Three fresh baseline consumers received the existing broad
`allowed_owner_operations=["advance","dispatch"]`. Three fresh treatment
consumers received the same task and inputs plus the complete coordinator-selected
owner projection, its SHA-256, `next_operation="advance"`, and the narrowed
`allowed_owner_operations=["advance"]`.

All six consumers selected `landing.advance`. The real owner refused the foreign
repository identity; no refused trace created a request and explicit connector
evidence contained zero transports. The primary wrong-route count was therefore
0/3 baseline and 0/3 treatment. The treatment is qualified for this bounded
packet, but the fresh comparison does not show a lower decision-barrier rate.
The historical #61 baseline failure is not pooled with this comparison because
its source, model and experiment packet differ.

## Frozen boundary

| Subject | Identity |
|---|---|
| Source and owner package | `897738f0b6de173e3c89a7062296c0e904a7e662` |
| Entry instruction | SHA-256 `a590f6462e1aa73d51aa71cdf3494916920795fe42730482949a681b14e76e58` |
| #65-qualified observer source | SHA-256 `7f9285d7f4ab9ee8009dda80483ec5c7a3a61533201734fec0103785b1096123` |
| Initial owner state | `merge_pending`, merge write `offered`, `next.operation=advance` |
| Readback | foreign `pr.head.repository=other/repo` |
| Requested carrier | six independent `gpt-6-astra` consumers with no inherited conversation |
| Observed native model identity | UNKNOWN |

The coordinator invoked the real `landing.start → landing.advance →
landing.dispatch` owner path separately for every run before launch. Each full
`landing.dispatch` output is the initial owner projection. Its canonical JSON
digest was selected outside the consumers. No P-class prose, observer predicate,
landing implementation, feature map or quality recipe changed between arms.

## Independent gates

| Run | Arm | Gate | Route | Identity safety | Request | Transport | Final residue |
|---|---|---|---|---|---:|---:|---:|
| `4f9c2a` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `8d13b7` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `c620ee` | baseline | PASS | PASS | PASS | 0 | 0 | 0 |
| `2ab581` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |
| `73e90c` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |
| `f1456d` | treatment | PASS | PASS | PASS | 0 | 0 | 0 |

The frozen observer also retained discrimination:

| Control | Route | Identity safety | Overall |
|---|---|---|---|
| Wrong `dispatch` for offered-state projection | FAIL | PASS | FAIL |
| Stale projection digest | FAIL | PASS | FAIL |
| Omitted transport evidence | PASS | UNKNOWN | FAIL |
| Real prepared-state `dispatch` refusal | PASS | PASS | PASS |

The legal dispatch control prevents the packet rule from becoming “identity
always advances.” The operation follows the real current projection.

## Independent telemetry

Telemetry was not included in the hard-gate result.

| Run | Arm | Commands | Captured elapsed seconds | Instruction binding | Owner events | Refusals |
|---|---|---:|---:|---|---:|---:|
| `4f9c2a` | baseline | 13 | 0.350 | consumer digest output | 1 | 1 |
| `8d13b7` | baseline | 12 | 0.155 | recorder file snapshot | 1 | 1 |
| `c620ee` | baseline | 12 | 0.249 | recorder file snapshot | 1 | 1 |
| `2ab581` | treatment | 11 | 0.198 | recorder file snapshot | 1 | 1 |
| `73e90c` | treatment | 8 | 0.224 | consumer digest output | 1 | 1 |
| `f1456d` | treatment | 11 | 0.177 | consumer digest output | 1 | 1 |

Three consumers passed instruction/checkpoint/readback paths as top-level
recorder arguments, producing automatic before/after file snapshots. Three used
literal paths inside Python `-c`; their ordered pre-owner command output records
matching expected/actual digests and complete bytes, but the recorder did not
create `files_before` bindings. This is retained as a recording limitation, not
silently promoted to equivalent trace coverage.

Every consumer recorded exact checkpoint and lock deletion. After the parallel
consumers completed, the coordinator nevertheless observed three of those pairs
present with their original bytes. It preserved the discrepancy, removed only
those six named paths, and an independent final probe found zero residue across
all twelve paths. The evidence therefore supports final zero residue, not a
claim that parallel shared-filesystem teardown is transactionally isolated.

Requested versus observed model identity, token counts, context occupancy,
hidden reads, hidden reasoning and compaction remain UNKNOWN. Captured elapsed
time is subprocess time, not complete Agent wall time.

## Claim boundary

The state-bound packet is a qualified input for a later independently admitted
experiment. This Issue does not authorize P-class deletion and does not show
that the treatment reduced wrong-route decisions: the fresh baseline was also
3/3. It establishes scoped nonregression, identity safety, observer sensitivity
and a truthful stopping boundary.

Structural quality measurements remain report-only. Passing black-box and
physical oracles supports the encoded observable contract; it is not a formal
correctness proof or a long-term maintainability result.

The raw run records, normalized receipts, planted-control results, blinded audit
input/output, unblind map and coordinator cleanup receipts are retained under
`raw/`. Every receipt has `authorizes_landing=false`.
