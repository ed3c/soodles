# Issue #118: local supplier integration — incomplete delivery

One causal correction: the already configured host credential supplier is now
consumed by the shipped `issue-atom run` entry and the pending supervisor
bootstrap, with matching P guidance. No new lifecycle, broker or cloud handoff
mechanism. This is combined CLI/P treatment, not P-only evidence.

## Identity and preserved state

- Repository: ed3c/soodles; existing Issue #118 and PR #119, no new Issue/PR.
- Provider base: `d6315be0d3005746077b52995d4126b0615c8f77`.
- Previous PR head: `64638f5549c678f9797f0ebddcd8445a60caf4d0`.
- Exact merged baseline: `29c82b71560ec312728953f9fe30f607c2735453`.
- Pre-publication observation: uncommitted changes on that baseline in the
  Noodle-created `issue-118-local-supervisor-admission` worktree.
  The immutable publication head is recorded separately by the supervisor;
  `raw/identity.json` retains this earlier content observation unchanged.
- Eight source/instruction/test content digest map: `raw/identity.json`;
  canonical map digest `5a872a5a1308b44d792aa5a6a5cf1812f6cc62f3f8aeba58de8b7c799e72dd7e`.
- Baseline retained in separate Noodle-created `issue-118-supplier-baseline`.
  Main remains clean at provider base; pre-existing stash is untouched.
- Frozen protocol, observer and baseline fixture were selected outside the
  candidate before source edits. Their bytes are copied here without change.
  Earlier `local-supervisor-admission/` receipts remain historical evidence
  for PR #119's prior implementation, not validation of this new treatment.

## Results and scope

| Check | Baseline | Treatment |
| --- | --- | --- |
| Frozen six-case supplier observer | 5 failures, exit 1 | 0 failures, exit 0 |
| Full local suite | 229 tests; 9 failures, 2 errors | 236 tests; same 9 failures, 2 errors |
| Fresh consumer behavior | NOT_RUN | NOT_RUN |

The baseline fails configured-supplier consumption, stale-parent selection,
refusal-before-checkpoint, and child capability isolation. Invalid authorization
already refuses legally. The same external observer passes all six treatment
controls using synthetic supplier/provider/Noodle boundaries. These are not
naturally occurring Agent mistakes and do not establish reduced decision cost.

One planted in-process regression makes `clean_child_env` return the inherited
environment. The unchanged observer rejects it (one failure, exit 1). Subject
files were not changed. This establishes observer sensitivity only.

New helper tests (5), Issue-atom tests (8), and existing supervisor tests (3)
passed locally. Skill frontmatter validation and `git diff --check` passed.
Supplier requests fix the admitted repository and operation permissions; there
is no inherited-token fallback. Error text contains only a safe type/status,
not command/stdout/stderr. App/supplier inputs do not enter candidate children.
The legacy read bootstrap receives only its issues-read token and launcher.

## Full-suite failures are not waived

Raw suite stderr preserves the exact names, stacks and exit statuses; the
ordered lists in `raw/identity.json` match. Four failures/errors arise at the
Linux-only runtime platform gate. Seven arise in publication, context recording,
landing continuation and quality controls with native macOS path behavior.
None of their source/test paths is changed by this correction. This is a fresh
observed count of eleven failing/erroring cases, not the historical claim of six.
Equal failures do not authorize acceptance or landing. Linux canonical acceptance
and exact-head provider CI remain outstanding; there is no acceptance waiver.

## Fresh context and owner blocker

Overall requested P-class result: **INCONCLUSIVE**. Exactly one baseline and one
treatment were planned; neither was launched. No substitute model run or extra
sample was used. Consumer reads, tool calls, argv mistakes, owner mistakes,
unnecessary envelope requests, extra calls and outcomes are unknown, not zero.

The measured Noodle v0.1.19 (`ac0885fa41c78608a49b916deede79b44ea73801`,
binary SHA-256 `8cf02b4bf28d15a5c9701aa7ad20a3423256516a6ab14637bc148d706671e13c`)
owns both worktree creations. Its fresh `admission inspect` reports
`no_proposal`, revision `9ab8365b24c51fcf2889b43fc86cecf9`, and no executable
recovery next. It requires a separately admitted intent and fresh INITIAL
proposal through the scheduling owner. There is no supplied current fresh
consumer launcher. `worktree exec` alone is not an admitted session/order.

Codex 0.153.4 doctor confirms repo detected and matching worktree cwd/root;
overall doctor exit 1 includes TERM=dumb. No model session was launched by that
diagnostic. The measured Noodle lacks the newer publication surface required
by the shipped lifecycle; no substitute executable was built or installed.

The missing capability is not a request to transport credentials from cloud.
Host App identity and a repository-scoped read token were separately verified
before this correction, with the test token revoked. Persistent host setup and
external task/carrier authorization are distinct from derived checkpoints.

## Effects, evidence and continuation

Effects: existing Issue #118 title/body amended under user authorization;
two Noodle-owned local worktrees; candidate file edits; disposable fixture
state and evidence. No production scheduler start, Issue creation, branch/PR
publication, merge, closure or cleanup. Pending worktrees remain for their owner.
The recorder captures top-level argv, outputs, exit status and selected file
snapshots; it is not a full OS audit of nested calls. Unknown telemetry stays
unknown. Synthetic token strings in control traces are not live credentials.

Raw originals are retained outside the worktree at
`/tmp/soodles118-supplier.ZGUqA8`, with copies and digests here.
Publication is blocked by absent canonical acceptance and matching Noodle
publication claim. The candidate-publication skill prohibits direct push or a
connector PR mutation as a substitute. Continue only when the existing owner
supplies the current admitted execution/publication inputs and the required
verification succeeds. No terminal receipt exists; this atom is not closed.

## Subsequent native bootstrap and publication authorization

The user subsequently authorized a bounded bootstrap from merged Noodle
`3732a02f9994c23bbb2be30c31801b7a2da586af`. Its clean native macOS build has
SHA-256 `965cfd6f985e207551d0664e728ae9fae10ae0cc8cd2885a816415823d9d103d`
and includes the publication command. This changes executable availability,
not the earlier experiment's results or its unexecuted consumer comparison.

With the same explicit physical TMPDIR for both subjects, the full local
baseline (229 tests) and candidate (236 tests) each have 3 failures and 1 error,
all at the Linux-only runtime gate. The seven alias-sensitive path cases pass
without source/test changes. Noodle publication-focused controls pass with
that same TMPDIR. None of this is canonical Linux acceptance.

Raw follow-up requests, streams, statuses and hashes remain externally at
`/Users/neon/.codex/experiments/soodles133-bootstrap.QpepPK/evidence/` in
`baseline-canonical-temp`, `candidate-canonical-temp`, `publication-controls`,
`publication-controls-canonical-temp`, `native-identity` and
`native-lock-readback`. These host-local locators are not portable artifacts;
the original raw experiment copied in this PR remains unchanged.

The user explicitly authorized one bootstrap update of existing PR #119 before
canonical acceptance, to trigger its existing Linux Actions verification.
This is a one-time supervisor publication boundary, not a fabricated Noodle
claim or a change to product acceptance rules. No new Issue/PR, direct merge,
test exemption, or unknown-write retry is authorized. The externally selected
landing implementation is from Soodles
`d6315be0d3005746077b52995d4126b0615c8f77`, verifier digest
`34f8df4a321893366306e078b6a2d30373b5f44c81a49496baeae8fbf069a1b1`.
Exact-head Linux success is required before landing admission. Fresh P-class
behavior remains INCONCLUSIVE; publication is not proof of local automation.

All these receipts have `authorizes_landing: false`.
