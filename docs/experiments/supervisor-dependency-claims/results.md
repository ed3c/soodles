# Supervisor-bound dependency result

## Subject

- Baseline: Soodles main `bea629a5be6017326e35d60e0a3fd7d6b19301de`.
- Source-fixed edge removed: Ops Issue 21 depended on Soodles Issue 111 through
  the `dependency_binding.EDGES` registry.
- Dynamic fixture: an external supervisor claim binds the already delivered
  Soodles Issue 113 / PR 114 result to a different Ops consumer Issue. Provider
  objects remain fixtures; their pinned Soodles identities are real.
- Atom: `ed3c/soodles#115`.

## Executable comparison

The frozen observer is `RED` on baseline: the new supervisor dependency claim
is rejected at `claim.fields`, so source editing is the only way to select a
different edge. The independent claim remains legal.

Treatment is `VERIFIED`. The same landing command accepts the supervisor-bound
edge, projects seven indexed `dependency_0_*` GETs and continues through the
existing owner. A malformed repository refuses during claim validation; a
wrong revision and a missing result refuse before checkpoint and return exact
read-only recovery requests. The independent claim gets no invented edge.
Three planted outcomes are all rejected: dynamic-route refusal, wrong-revision
acceptance and a missing dependency request.

## Fresh P-class consumers

Six native consumers used fresh decision context and distinct outputs. Every
consumer read the same frozen task, one pinned instruction and one owner
transcript. A later evidence-shape pass normalized only its own receipt; it did
not change decisions.

| Measure | Baseline | Treatment |
| --- | ---: | ---: |
| Dynamic legal route selected | 0/3 | 3/3 |
| Independent route selected | 3/3 | 3/3 |
| Exact recovery readbacks selected | 0/6 | 6/6 |
| Effect routes selected after refusal | 0 | 0 |
| Repository/revision guesses | 0 | 0 |
| Recorded instruction reads | 9 | 9 |

Wrong-revision and missing-result cases are refusal recovery, not effect
eligibility. Selecting their owner-provided fresh GETs is correct; an unchanged
write or inferred correction would be a barrier crossing. The first discarded
consumer batch exposed this distinction and is not part of final evidence.

This supports a bounded behavior hill climb: a new admitted edge becomes
routable without source selection, independent work is preserved, and refused
provider evidence follows only read-only owner recovery. It does not establish
lower global context cost, DAG completeness, provider correctness or a general
scheduler.

## Shortest path and authority

The Agent-facing command remains `landing start CLAIM READBACK CHECKPOINT`.
Dependency identity is immutable supervisor input, not an Agent CLI choice.
The owner returns indexed requests and one bound continuation argv. Soodles
owns validation semantics but does not choose or discover DAG edges.

Completeness of `claim.dependencies` remains the external supervisor/admission
owner's responsibility. An empty list means the admitted Issue is independent;
landing cannot infer that a missing edge was intentional. All experiment
receipts are local and non-authorizing. Exact-head Actions and supervised
landing retain delivery authority.
