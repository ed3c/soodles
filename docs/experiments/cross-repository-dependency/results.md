# Cross-repository dependency result

## Subject

- Producer: `ed3c/soodles#111`, PR 112, candidate
  `498f384337609fc2a76c1cb293aa100e5d639b0d`, merged revision
  `b7dd55ab1074d28afe83dae3a469fc5e6f5ad36d`, tree
  `85fb13afdf603baccf1ee7644b209e40dfd25d88`, runtime run
  `35541786068` attempt 1.
- Consumer: `ed3c/ops-reconciliation-copilot#21`, draft PR 22,
  candidate `e3c530340aa8d8070206b0a893b9a9aef5e462d0`, runtime run
  `35217009263` attempt 1.
- Atom: `ed3c/soodles#113` at base
  `b7dd55ab1074d28afe83dae3a469fc5e6f5ad36d`.

## Executable comparison

The observer was frozen before implementation. On the base source, the legal
case and all five invalid dependency cases entered landing, so the baseline is
`RED`. On the candidate, the complete result enters the existing Ops owner;
closure-only, foreign repository, wrong revision, stale ancestry and missing
producer acceptance refuse before a checkpoint. Treatment is `VERIFIED`, and
all five planted result mutations are rejected.

The positive case checks both layers. Producer eligibility requires the exact
merge artifact, successful runtime step and current-main ancestry. The existing
Ops validator then checks PR 22's own exact head, tree, run, jobs and steps.
Forward Soodles main ancestry remains eligible, while divergence refuses.

## Fresh P-class consumers

Six native consumers used fresh context and distinct outputs. Every consumer
read the same frozen task and one owner transcript; only the assigned
cross-repository instruction and matching baseline/treatment transcript varied.
The coordinator counted a non-`stop`, `supported=true` decision for any of the
five invalid cases as one decision barrier crossing.

| Measure | Baseline | Treatment |
| --- | ---: | ---: |
| Legal route selected | 3/3 | 3/3 |
| Invalid dependency routes selected | 10/15 | 0/15 |
| Repository guesses | 0 | 0 |
| Recorded instruction reads | 9 | 9 |

This supports a bounded behavior hill climb: the legal route is preserved and
the observed invalid-route barrier falls from ten selections to zero. It does
not claim lower global context cost, fewer instruction reads, complete model
traces or provider correctness.

## Shortest path and authority

The Agent-facing path remains `landing start CLAIM READBACK CHECKPOINT`. Its
owner output now supplies both consumer GETs and source-owned `dependency_*`
GETs in one `next.requests`, followed by one bound continuation argv. There is
no dependency/repository/revision policy flag and no separate checkpoint.

The observer, tests and consumers are local non-authorizing evidence. They
perform no Vercel deployment, Jev live call, secret access, Ops merge or Issue
closure. Exact-head Actions and the supervised Soodles landing owner retain
delivery authority.
