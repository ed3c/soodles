---
name: verify-soodles
description: Verify Soodles runtime, bounded execution, delivery, recovery or bounded P-class behavior/context using the active cloud Actions or local owner.
---

# Verify Soodles

Soodles has a runtime CLI and an external supervised publisher. Retain the path
selected by [root AGENTS](../../../AGENTS.md#session-entry--select-once-then-act).
If you enter through this skill, read that short entry first. Shell commands in
a recipe do not make an established cloud Session local.

For feature-specific execution or investigation, read the relevant recipe directly: [authenticated Issue readback](features/github-read.md), [runtime admission](features/runtime-admission.md), [bounded Issue execution](features/issue-execution.md), [supervised delivery](features/supervised-delivery.md), [delivery recovery](features/delivery-recovery.md), or [P-class behavior/context](features/pclass-context.md). After an exact landing RESOLVED receipt, use the dedicated [next-Issue Skill](../next-issue/SKILL.md) for bounded candidate qualification and provider Issue creation; it is not a scheduler or product-priority owner. Consult [the feature index](features/README.md) for a full maintenance pass. Quality reporting, general production scheduling and Issue DAG execution remain outside this map. The normal route is AGENTS → this skill → the feature, with no mandatory index hop.

For P-class behavior/context work, read its recipe before any runtime doctor.
Use the supplied carrier and the prerequisites for that operation. Native cloud
consumers require neither Codex CLI nor the Linux runtime binary. The coordinator
captures observations. Independent consumers receive only their assigned task,
instructions and inputs. A scoped feature check does not claim a full maintenance pass.

For an observed defect, preserve the actual owner/process/readback evidence and
use the admitted Issue's declared deterministic controls. The [P-class recipe](features/pclass-context.md#declared-defect-controls-and-optional-behavior-comparison)
selects scoped instruction maintenance or an optional behavior comparison only
when the task selects it. Unknown behavior first needs the relevant existing logs,
source and owner readback. Request offline evals only for a selected Agent behavior
measurement that needs them; uncertainty adds no test demand or runtime gate.
Product correctness and Agent improvement retain separate evidence requirements.

## Cloud Actions verification

For cloud candidate verification, use the current Session's GitHub connector.
Read the exact PR and head and the existing `runtime.yml` run. That workflow
already performs pinned Noodle setup and canonical acceptance on the runner.
Read the run, attempt, head, and acceptance job and step outcome. When accessible,
also read artifact identity and content. Distinguish metadata readback from
receipt inspection. Reuse a completed matching run, or observe the current run.
A prior head is historical evidence. This branch needs no scratch checkout,
binary doctor, `noodle skills list`, Codex CLI or API key.

On failure, inspect the owning failed step and report its actual input/capability gap; do not retry an unchanged write or invent a workflow dispatch. On success, return the requested evidence or continue the already-authorized delivery through its existing owner. CI success grants no landing authority. A targeted feature not covered by an existing workflow remains a named gap; do not pretend that the general runtime run exercised it. This cloud branch does not require reading the local Launch/Doctor/Drive sections.

## Local launch

Runtime admission and delivery-recovery fixtures run from a clean committed Soodles checkout with the absolute binary admitted by `policy/runtime.lock.json`. These CLI drives are short-lived and noninteractive; do not start `noodle start` for them. Bounded Issue execution instead uses the supervisor's separately measured carrier and existing Noodle lifecycle, as its recipe specifies. Neither route substitutes its binary or platform evidence for the other.

## Local doctor

For lock-bound recipes, start each fresh driving session with
`./soodles runtime check` on the supplied binary. Before using Noodle, require
its receipt to match the lock. The runtime driver's doctor also supplies its
positive feature drive. For bounded Issue execution, use that recipe's carrier,
envelope and canonical-state preflight. The Linux lock does not certify a native
macOS executable. Preserve a failure and inspect its owning step. Repeat doctor
only if a failure implicates runtime identity or health, or a change invalidates
the existing check. Expected control refusals and unrelated failures do not
invalidate it. Doctor does not permit a retry with unchanged input.
A refusal names the invalid field and supported help. If a prerequisite is
missing, the operation stays blocked until its owner supplies it.

## Test scope

Use the [Test Manager](../test-manager/SKILL.md) before requesting regression or
physical controls. Its decision applies to local work and canonical CI; this
skill and its feature recipes do not append a full-suite run. A feature receipt
needs the requested feature's controls, not every other mapped feature. Missing
base or scope goes back to the current Agent for readback/impact analysis.

## Local drive and shared owner outputs

Use the shipped executable from the repository root:

```sh
.agents/skills/verify-soodles/scripts/verify_runtime.py /absolute/path/to/noodle /tmp/fresh-soodles-verification
```

Both arguments are supplied by the current execution environment: the already-admitted binary and a fresh evidence destination. This runtime driver checks source identity, performs doctor/positive admission, resolves this skill through `noodle skills list`, and drives a wrong-digest executable sentinel through the same CLI. It then checks cleanup and unchanged source identity. It never sends provider writes or runs full acceptance. Other recipes reuse existing owner entries and recovery oracles; do not route them through a new scheduler or copy their transition logic into a skill helper.

For landing, consume the invoked owner's current `owner`, `action`, `next`,
`invalid` and, when emitted, `request`. Missing input and provider readback are
not executable commands. Use confirmed inputs with the returned operation or
help. Never derive an operation by splitting a field name. A historical next
action is trace evidence only. Before an effect, the owning action rechecks the
current claim, head, checkpoint, provider state and write eligibility.

Noodle resolves `.agents/skills` by default. Resolution must name this checkout's exact `verify-soodles` directory; requesting a name is not proof of loading it. The captured digest map identifies the actual skill files. Noodle may emit missing-backlog-adapter diagnostics: they disclose that production scheduling is unavailable, not a request to repair unrelated adapters during verification.

## Evidence

For a local runtime-admission drive, require the driver's `receipt.json` with `classification: VERIFIED`, exact candidate head/tree, observed runtime identity, local skill resolution, rejected sentinel and successful cleanup. Other recipes specify their own receipts. Preserve actual argv/provider operations, subjects, output, exit codes and elapsed time where observed. Record skill resolution path/digests, unexpected command failures, expected control refusals, repeated readbacks and verification invocations; label top-level versus child-command scope. Missing measurements are unknown, not zero. These records do not establish a matched baseline/treatment experiment or reduced Agent decision cost.

Local feature receipts have `authorizes_landing: false`; `VERIFIED` is not Issue closure. Only the externally selected delivery owner can produce the admitted Issue's `RESOLVED` receipt. Cloud claims require exact merge/closure/runtime/provider-main readback through GitHub; local claims additionally require Git/Noodle reconciliation. `next: null` alone is not resolution (identity also returns it). Canonical acceptance consumes Test Manager scope for the exact candidate through its existing owner; using this skill adds no full-suite requirement or duplicate run. A pre-change receipt does not verify a changed candidate. Shorter instructions, lower structural scores or fewer commands do not establish reduced Agent decision cost.

## Cleanup

For cloud Actions, preserve the run and artifact references; the workflow owns runner fixtures. A cloud landing continues through connector readback and never invokes local reconcile merely because a scratch checkout exists. Do not manufacture a scratch worktree for cloud cleanup. The following local cleanup rules apply only to resources actually created by that local drive.

The runtime driver owns its temporary sentinel directory; recovery oracles own disposable fixtures and wait for their child processes. Preserve evidence outside those directories through teardown, including on failure. Noodle owns the task worktree; only the existing delivery reconciliation may remove it. If that removal is expected, verify the reported merged identity in the surviving control root instead of invoking a deleted candidate path. A failed receipt is evidence, not permission for an unchanged retry.

## Maintenance

For observed recipe drift, compare the affected instructions with their source and
correct that scope. Test Manager selects any necessary executable verification;
a prose correction alone requests neither model comparisons nor a full-map drive.
Keep product regressions with their causal owner and preserve the active judge.

For an explicitly requested full verification-skill maintenance pass, use the
installed pstack `maintain-verification-skill` from
`/Users/neon/.local/share/pstack/skills/maintain-verification-skill/SKILL.md`.
Only such a pass claims full-map coverage; a scoped correction does not become
blocked because unrelated features were not exercised. Native skill symlinks
resolve to that sole source; do not download, copy or add a loader. Its original
creation at `ed3c/plugins@68836ddaf5697224520f1847d90cdb90ca8babaa` is historical
provenance, not the current method selection. Ordinary use does not repeat create
or maintain. User-selected scope and execution constraints still apply.

This guidance is P-class. The index, counts and prose are N-class. Executable
local discriminators provide L-class evidence. Actual provider-enforced identity,
merge readback and closure readback provide R-class evidence. These classes are
not interchangeable. Preserve failing evidence for product regressions and follow
the admitted Issue's owner and write boundary. A recipe change must not hide
regressions. Before reusing an unoffered admission, the supervisor can correct it
through the existing owning action. Preserve unknown writes for owner readback.
Neither maintenance nor a candidate-edited test selects its effective external judge.
