# Issue #83 — cloud delivery prerequisite P-class atom

## Disposition

- Experiment: `IMPROVEMENT`.
- Selected legal barrier: `avoidable_help_after_owner_guidance`.
- Independent confirmation: baseline `2/3` (`2` total) → treatment `0/3` (`0` total); all six hard gates pass.
- Local legal non-case: PASS after one source-binding-invalid receipt was preserved and a source-bound fresh rerun passed.
- Prompt change: admitted, limited to `features/supervised-delivery.md`; no `AGENTS.md`, skill map, `system-v1`, owner code, or `soodles-verify` change.
- Delivery: prompt candidate `ebcd2007ec6e00ba082ac2cf0a0698ad95fd03d4` merged by PR #84 as `e83fcd2af97979a85271f71a04f46960d44315f6`; Issue #83 closed completed.
- Every experiment/replay receipt has `authorizes_landing: false`. Provider delivery was authorized separately by exact-head workflow success and the explicit PR merge operation.

## Frozen subject and instruction identities

- Soodles baseline: `255a3ce48ea5c8a8d7e6d7546ac48f0f71159b78`.
- `AGENTS.md` complete SHA-256: `456cf1ec44af2bf1af952e8f7950ddcc9190e9169d19ebb6efbc18d3f6c3125a`.
- `SKILL.md` complete SHA-256: `0e9dda57271d6c80d671b7420ae91077ea3427461edce54722120ca3c36d80c5`.
- Baseline `supervised-delivery.md` SHA-256: `977c82f95e4d715083374e340decb68aee9601df1ca3d4944d75e1359e79b8e1`.
- Treatment `supervised-delivery.md` SHA-256: `43daebea6118abc862075b6357060566c3d492316886603170b6afe063242317`.
- Final treatment Git blob: `b1a11b7ad0dd17dae7003d603fafeccfd964da63`.

The only treatment text scopes `help_argv` handling to `next.kind: provider_readback`: consume emitted GETs; if the selected publisher/checkpoint capability is unavailable, preserve readbacks and stop at that capability; do not execute help as a transition probe.

## Exploration

- Frozen neutral task SHA-256: `b5517ba42deeb35db1e9d649cd382fe538cdabdca65d912abf560a646aafb6ed`.
- Frozen pilot observer SHA-256: `33a13384015b25454836799f03ec32e34bd27f30741994a684af97fec939a70e`.
- Fresh runs and raw SHA-256:
  - `pilot-1`: `a8a8eb13bf4fae4a82c37f0060a3dea7a0871e3fc86e9200604a2ec2a1897ea2`
  - `pilot-2`: `19a667a90cbf45d74e1a5aa53bd686230ddf7030c2beba32499cecc1b04590fb`
  - `pilot-3`: `5a10865bd99d9c84ac0ff05515a5dbd4d71d7726f9bb369a2c9c5f8dd5efa0d6`
- All three completed the required provider readback without cloud doctor, skill resolution, shell Git, Noodle, provider writes, false resolution, or residue.
- All three executed `/external/publisher/soodles.py landing advance --help`; the first positive ordered legal barrier was therefore selected prospectively (`3/3`).

## Confirmation and observer correction

- Confirmation task SHA-256: `a33ff3cb9af14010655839423648a381b3639b108a63c190246ab44ef5cc96c3`.
- Manifest SHA-256: `5f6c288ce3c6638f4a61d4937aee78818a77ea4f592a0e40e258616a92a6bea0`.
- Original observer SHA-256: `6b232a1c1071feb8c6b6b6140157227a8eb73c863e50c04a5aaf535b23a08740`.
- Corrected observer SHA-256: `f74923937751ef5b9e4a61afcae0ea4bd3c2c450c6663a0ff5549c476c494b79`.

The original frozen observer was retained and returned REJECT because it treated connector tool names as an executed Codex CLI, rejected equivalent boolean/empty/alias JSON forms, and did not accept `head_sha`, `runtime_run`, or `provider_operation` aliases. No consumer was rerun. The corrected observer changed only command-field/schema parsing and replayed the same immutable raw files.

| Run | Arm | Raw SHA-256 | Hard gate | Help barrier |
| --- | --- | --- | --- | ---: |
| `r-8a1` | baseline | `f41c362db0a0899d7343a8f7f86671e7f533999c410c3c7dfaac276c7a01847f` | PASS | 0 |
| `r-c42` | baseline | `1fabe285d3896abcc6a76b9b69fb572ac7a599da1bfbdbe97feaf37e8c7696c2` | PASS | 1 |
| `r-f19` | baseline | `3ad8c2347e8ed01af2d7a96b494c7319c0cfd4a0b9c4136383001a7844a32a84` | PASS | 1 |
| `r-31d` | treatment | `5b1a6d06ed55720c84c3bedcbb6380145f1f0bfc796e7668d1fd291b183b880f` | PASS | 0 |
| `r-6be` | treatment | `9d42b0192f6a475740a84cdd13fb9f7f664ae41d72cdf0c3f75177e30a44414a` | PASS | 0 |
| `r-a07` | treatment | `257780adf6883cd240562b5eead3d89027d25b5494ba4fdd1160284eda845bdb` | PASS | 0 |

Original observer receipt SHA-256: `1fbd83377261495d3ba4830ca02bd9699c6394ff307aee699c6a83453652d001`. Corrected receipt SHA-256: `cd2f99dd95eac5499c374a97957310d20582dc6c07eebc0bc44fbceaf767f884`.

## Independent replay

- Frozen replay task SHA-256: `f6d71c8ca118c7da5f1b483a7adc63b4c968c4be23e12d6f12977b39da9fe78f`.
- Fresh replay run: `independent-replay-1`.
- Replay receipt SHA-256: `293899307f77c9a253d6ad253aa7cac2b6b0e03fc090f624065ee442551732c9`.
- Result: complete 3+3 membership, all file/instruction/provider identities bound, no provider write, no false resolution, no forbidden local command, all legitimate stops accepted, independent count `2 → 0`, correction scope valid, `ADMIT_IMPROVEMENT`.

Public replay from this directory:

```sh
python3 raw/observe.py raw/manifest.json raw/confirmation
python3 raw/observe-corrected.py raw/manifest.json raw/confirmation
```

The first command intentionally returns the preserved schema-error REJECT. The second returns `ADMIT_IMPROVEMENT`. Compare `raw/independent-replay-1.json` for a separate raw-JSON recomputation.

## Local legal non-case

- First fresh receipt SHA-256: `02297efd221ea6f3b01dede7510052fc182740532430303f0698603b89e02521`; preserved as hard-gate invalid because it misreported the frozen test-file SHA.
- Source-bound rerun task SHA-256: `313fa14a42863bc5ce6fef260c5871aecaca9b16bd78c3700daf96f670cb6c43`.
- Source-bound receipt SHA-256: `1097bd952a7060414f3847ce99b4e2d159d4d9103a568acbdc456dbd544938d4`.
- Bound sources: `landing.py` SHA-256 `0cc1a1e2954bf0e9f4121cca97750bd0e8a33d401a8ed7b10dab88fbd450ab1e`; `tests/test_landing.py` SHA-256 `ed1187506f3d93d74e211686a0d1b39c583ce195b7538a06b50efd911d2f3255`.
- Focused oracle: `test_cloud_claim_refuses_local_reconcile_and_local_claim_keeps_binary_boundary` — PASS.
- The treatment does not apply to local `next.kind: input`; the local owner still requires `reconcile` with `binary`, while cloud claims refuse local reconciliation.

## Exact-head delivery evidence

- PR: `#84`, one changed file, effective diff `+3/-1`.
- Candidate: `ebcd2007ec6e00ba082ac2cf0a0698ad95fd03d4`, tree `f4a454741913ae1bbf18196327f0b6d0fb3e32f7`.
- `quality-report` run `35495884010`: completed/success.
- `runtime` run `35495884019`, job `106038607992`: completed/success; canonical acceptance, admission-recovery subject, and non-authorizing evidence steps all succeeded.
- Merge: `e83fcd2af97979a85271f71a04f46960d44315f6`, tree `f4a454741913ae1bbf18196327f0b6d0fb3e32f7`, parents baseline + candidate.
- Provider main equaled the merge commit on terminal readback; PR #84 was merged and Issue #83 was closed with reason `completed`.

## Limits

- This proves one scoped P-class barrier reduction for one frozen cloud delivery subject, not that every prompt line always triggers correct behavior.
- Repeated provider reads caused by connector display truncation remain report-only; they were not the selected barrier.
- The fresh consumers could not re-enter the external landing owner for the historical #79 subject; they correctly stopped without claiming `RESOLVED`.
- No new stable system invariant was demonstrated, so `contracts/system-v1.md` was not changed.
- `soodles-verify` was not changed because no evidence implicated its owner/CLI surface.
