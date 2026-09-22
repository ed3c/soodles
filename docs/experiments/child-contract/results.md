# Issue #135: complete admitted child contract

The source defect is a missing projection: Soodles already validates the entire
structured Issue contract but previously omitted it from the stage prompt.
The correction adds that existing object to the exact prompt and tells the
ordinary execute consumer to use it. No new schema, context carrier, scheduler,
credential route or GitHub command is introduced. Provider freshness remains
the wrapper's responsibility and exact worker prompt equality is retained.

Baseline: `210d4056f9ca6916bac903db0684cfd9f5322aed`.
Measured source candidate: `bb3ba59fac66dcc63475839bb4424a73da107ca3`.
Evidence-only commit follows; raw.json binds candidate diff and instruction bytes.

## Observations

One new Noodle/Codex exec per arm, identical task, model/executable, workspace-write
sandbox, tools and disposable read-only provider. No inherited conversation,
diagnosis, expected command or other consumer result. Baseline and treatment
both changed only allowed.py, verified exact bytes/output and emitted their own
completed/nonblocking outcome. This is fixture task completion, not delivery.

| Measured item | Baseline | Treatment |
| --- | ---: | ---: |
| Duplicate contract-retrieval barrier | 1 | 0 |
| Model retrieval attempts | 2 | 0 |
| Successful model fixture-provider reads | 1 | 0 |
| Wrong argv / wrong owner / envelope request | 0 / 0 / 0 | 0 / 0 / 0 |
| Completed shell commands | 10 | 12 |
| Frozen deterministic controls passing | 3/6 | 6/6 |

Classification: **OBSERVED_BARRIER**, removed for this fixture pair by combined
CLI/P treatment. It is not isolated P-only efficacy or a universal hill climb.
Total tool-call reduction is expressly not claimed: shell calls increased.
Baseline actually loaded execute, AGENTS, execution and GitHub-read guidance;
treatment loaded the changed execute skill and common baseline execution recipe
and AGENTS. The final companion recipe/system-v1 correction is not independently
behavior-qualified. Never attribute behavior to an unread document.

The baseline selected a duplicate Issue read before it encountered an incomplete
fixture CLI (`landing` module absent); then the available Python fixture reader
returned the contract. That error is not a product bug and cannot prove recovery
cost improvement. Both arms retain the same fixture; no replacement sample was
run. The bounded redundant retrieval observation is supported, while live network
reliability, clean recovery-cost effects and broad behavior remain INCONCLUSIVE.

Both disposable loops exited 1 after successful worker review because the existing
backlog.done adapter refused to close an open synthetic Issue. This is retained
as an expected authority boundary, not relabelled as successful provider delivery.
Process groups were absent before fixture removal; raw records survived cleanup.
Generic skill validation rejects the unchanged Noodle `schedule` frontmatter in
both base and candidate; the project runtime gates remain required. Noninteractive
Codex doctor reports TERM=dumb but verifies the actual worktree cwd/root.

## Evidence and delivery boundary

`protocol.md` and `observer.py` are the fixed external inputs copied unchanged.
`raw.json` contains indexed, digest-bound, lossless compressed native traces,
actual argv/output/status, selected input/Skill bytes, original fixture/provider
readbacks, owner/session identity, cleanup and the frozen observer dependencies.
The raw archive contains synthetic credentials only, not host tokens or keys.
Hidden reads, full harness internals and observed model provenance remain unknown.

The supervising Session selected an unchanged external landing implementation
before effects. The existing issue-atom entry created the one live Issue #135;
an initially unknown response was resolved by exact fresh readback, not retry.
No experiment receipt authorizes landing. The one final PR still requires native
readiness, exact-head Linux acceptance, protected merge/closure and actual local
Noodle/Git reconciliation. Terminal receipts remain outside the removable worktree;
this pre-publication report does not claim they already happened.
