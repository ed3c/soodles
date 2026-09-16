# Soodles code-quality observation

Base `ca3bfffb4b4da6dad1c969723043e62099eb0ef1` → head `817a603bd85cafeb6048aa5a5a830566b9d88a1e`. Analyzer `scb-check==0.1.3`, AST-Grep `0.42.1`, 197 bundled rules.

Report only; not an acceptance gate or formal correctness proof.

| Scope | SLOC base → head | Article V base → head | Native V base → head | E all callables base → head |
|---|---:|---:|---:|---:|
| production | 428 → 476 | 0.0701 → 0.0588 | 0.0958 → 0.0819 | 0.5163 → 0.5492 |
| tests | 288 → 354 | 0.0347 → 0.0282 | 0.0417 → 0.0339 | 0.0000 → 0.0000 |
| oracles | 273 → 411 | 0.0147 → 0.0316 | 0.0440 → 0.0511 | 0.9300 → 0.9217 |
| all_python | 989 → 1241 | 0.0445 → 0.0411 | 0.0657 → 0.0580 | 0.6590 → 0.6925 |

Native scb-check E (before completing omitted callables): production 0.5244 → 0.5569; tests 0.0000 → 0.0000; oracles 0.9890 → 0.9885; all_python 0.6822 → 0.7214.

The complete-callable E is an explicitly documented reporting adaptation, not an unmodified benchmark score.

## Absolute complexity mass

| Scope | Total mass base → head | CC>10 mass base → head | Article flagged SLOC base → head |
|---|---:|---:|---:|
| production | 688.36 → 760.46 | 355.41 → 417.64 | 30 → 28 |
| tests | 126.62 → 162.06 | 0.00 → 0.00 | 10 → 10 |
| oracles | 670.19 → 965.03 | 623.25 → 889.43 | 4 → 13 |
| all_python | 1485.17 → 1887.55 | 978.67 → 1307.06 | 44 → 51 |

## Head function locations

| Scope | Function | CC | SLOC | Mass |
|---|---|---:|---:|---:|
| production | [landing.py:validate_snapshot](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/landing.py#L85) | 27 | 39 | 168.61 |
| production | [landing.py:reconcile](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/landing.py#L250) | 13 | 66 | 105.61 |
| production | [soodles.py:worktree_probe](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/soodles.py#L99) | 13 | 39 | 81.18 |
| production | [landing.py:advance](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/landing.py#L160) | 11 | 32 | 62.23 |
| production | [soodles.py:main](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/soodles.py#L204) | 10 | 27 | 51.96 |
| production | [soodles.py:load_lock](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/soodles.py#L51) | 9 | 16 | 36.00 |
| production | [landing.py:delivery_state](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/landing.py#L137) | 8 | 20 | 35.78 |
| production | [soodles.py:runtime_check](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/soodles.py#L69) | 8 | 18 | 33.94 |
| tests | [tests/test_landing.py:LandingTests.test_foreign_repository_tree_base_and_skipped_step_refuse](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L152) | 6 | 16 | 24.00 |
| tests | [tests/test_landing.py:LandingTests.test_missing_or_inconsistent_delivery_evidence_cannot_dispatch](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L72) | 5 | 20 | 22.36 |
| tests | [tests/test_landing.py:LandingTests.test_foreign_merge_parent_or_tree_cannot_close_issue](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L187) | 3 | 10 | 9.49 |
| tests | [tests/test_landing.py:LandingTests.test_wrong_provider_identities_fail_before_checkpoint](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L137) | 2 | 14 | 7.48 |
| tests | [tests/test_landing.py:LandingTests.test_cli_help_and_malformed_input_refuse_before_checkpoint](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L281) | 2 | 12 | 6.93 |
| tests | [tests/test_admission.py:AdmissionTests.test_wrong_repository_and_unknown_policy_fields_refuse](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_admission.py#L59) | 2 | 11 | 6.63 |
| tests | [tests/test_landing.py:LandingTests.test_wrong_claim_fields_identity_and_verifier_cannot_admit](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L169) | 2 | 7 | 5.29 |
| tests | [tests/test_landing.py:LandingTests.setUp](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/tests/test_landing.py#L14) | 1 | 22 | 4.69 |
| oracles | [cleanup_lock_oracle.py:lock_recovery_probe](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_lock_oracle.py#L12) | 33 | 143 | 394.62 |
| oracles | [delivery_oracle.py:delivery_probe](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/delivery_oracle.py#L12) | 24 | 123 | 266.17 |
| oracles | [cleanup_oracle.py:cleanup_recovery_probe](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_oracle.py#L13) | 22 | 108 | 228.63 |
| oracles | [delivery_oracle.py:delivery_probe.execute](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/delivery_oracle.py#L24) | 6 | 9 | 18.00 |
| oracles | [cleanup_lock_oracle.py:lock_recovery_probe.invoke](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_lock_oracle.py#L56) | 4 | 8 | 11.31 |
| oracles | [cleanup_oracle.py:cleanup_recovery_probe.invoke](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_oracle.py#L51) | 4 | 8 | 11.31 |
| oracles | [cleanup_lock_oracle.py:lock_recovery_probe.kill_cleanup](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_lock_oracle.py#L76) | 2 | 6 | 4.90 |
| oracles | [cleanup_lock_oracle.py:lock_recovery_probe.write_json](https://github.com/ed3c/soodles/blob/817a603bd85cafeb6048aa5a5a830566b9d88a1e/cleanup_lock_oracle.py#L71) | 2 | 4 | 4.00 |

## Interpretation limits

V_article=|AST SLOC union clone SLOC|/SLOC. V_native also includes trivial wrappers. E=sum(CC*sqrt(SLOC) where CC>10)/sum(CC*sqrt(SLOC)). CC/SLOC follow pinned scb-check, not Radon. E counts every function definition, including those nested under with/control blocks, cross-checked against Python AST; native tool E and omitted callables are retained separately.

All tracked .py at exact snapshots; production/tests/oracles disjoint. all_python is separately scanned and includes cross-scope clones.

- 197-rule tool release is not the paper historical 137-rule run; no human/agent ranking.
- Nested function spans include inner bodies, matching the pinned CC/SLOC convention; masses are not disjoint source ownership.
- scb-check 0.1.3 misses some nested definitions under with/control blocks. Head omits 1 production and 12 oracle callables. The E column uses complete callable traversal with identical per-function CC/SLOC rules; native E is retained.
- All metrics are structural signals, not correctness, authority, deletion permission or maintenance-time measurements.
- No production changes, execution of subject code, provider writes, gate changes or acceptance rerun.

The JSON artifacts retain every rule hit, clone counterpart, function, exact line set, file digest, and base/head delta. Original acceptance and fixed external verifier remain unchanged.

Sources: https://earendil.com/posts/measuring-code-sloppiness/ ; https://arxiv.org/html/2603.24755v1 ; https://pypi.org/project/scb-check/0.1.3/
