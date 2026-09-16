# Soodles quality observation: interpretation
Report-only observation of #10, before ca3bfffb → after 817a603b.

[Actions run](https://github.com/ed3c/soodles/actions/runs/35043629761) completed successfully. The job took 19 seconds; dependency installation took 9 seconds and controls/analysis took 3 seconds. These are measurement-job costs, not Soodles acceptance or delivery speedups.

## What the measurements show
- All tracked Python source SLOC: 989 → 1241 (+252). Production +48; tests +66; runtime oracles +138. Physical Python lines +282; whole-repository Git net lines +295 including documentation.
- Production article-formula V: 30/428 → 28/476 (7.01% → 5.88%). Native tool V, including trivial wrappers: 9.58% → 8.19%.
- Production E over all callable definitions: 51.63% → 54.92%. Native tool E: 52.44% → 55.69%.
- advance CC 9 → 11 while SLOC 37 → 32. It crosses CC>10; its entire new mass 62.23 enters the high-complexity numerator. Other pre-existing production high-CC functions did not change CC/SLOC. This accounts for the entire increase of production high-CC mass.
- Tests' flagged lines stay at 10, but V drops because SLOC grows from 288 to 354. That ratio decrease is not removal of flagged code.
- Oracle E drops slightly (93.00% → 92.17%) even while high-CC mass rises from 623.25 to 889.43. Keep numerator and denominator.

## Findings worth inspecting, not automatic refactoring orders
- landing.validate_snapshot: CC 27, SLOC 39. Concentrated provider identity/authority checks.
- landing.reconcile: CC 13, SLOC 66. Local/remote identity and cleanup safety checks.
- landing.advance: CC 11, SLOC 32. Observe future change effort at the durable transition owner.
- delivery_oracle.delivery_probe: CC 24, SLOC 123; cleanup oracles also concentrate scenario setup and fault assertions. Long scenarios warrant observation, but the score alone does not justify splitting or deleting controls.
- Under the pinned three-SLOC normalized-subtree detector, production clone coverage is zero. Two repeated assertion blocks in test_admission.py cover 8 SLOC. cleanup_oracle.py and delivery_oracle.py each contain a three-line require helper; their standalone oracle role matters before considering a shared dependency.

## A physically checked unsafe rule suggestion
The tool flags landing.py:75 (`type(claim[key]) is int`) and suggests isinstance. A local disposable-copy experiment used the existing provider fixture with `claim.run_attempt=True`:
- Current source rejects `claim.run_attempt=True` before creating a checkpoint.
- Changing only that expression to `isinstance(claim[key], int)` admits the boolean and creates a checkpoint.
Python bool is an int subclass. This is a concrete reason not to auto-apply or gate on this rule. No product source was changed. The provider readback in the counterexample is a fixture, not a live GitHub call.
The first attempted counterexample reused the broad existing Issue-boolean test; another downstream identity check still rejected it, so that test did not discriminate this specific predicate. The run_attempt case isolates the owning input boundary.

## Definition and provenance limits
scb-check 0.1.3 has 197 bundled rules, not the paper's historical 137. It adds trivial wrappers to native V and misses some definitions nested inside with/control blocks (one production and twelve oracle callables at this head). The report retains native scores and separately applies the article formula with complete callable enumeration cross-checked against Python AST, using the same per-function CC/SLOC counting rules. Nested spans remain inclusive; do not interpret masses as disjoint lines or Radon-equivalent path counts.

The analyst wrapper fails if AST-Grep fails, parsed files disappear, function identities are ambiguous, or positive/negative measurement controls fail. It does not fail because the measured repository has a high score. It executes no measured repository code during the Actions scan.

No structural or behavioral correction was made from these scores. Main remains 817a603b, existing acceptance and the fixed external judge remain unchanged. There is no quality required check and no claim of improved Agent decision cost or next-task maintenance time.

[Exact report](report.md) · [Actions metadata and summary](run.json) · [Local rule counterexample](rule-counterexample.json)
