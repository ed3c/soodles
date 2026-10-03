# Issue 229 的 writer 結果與重建方式

本記錄只涵蓋 `ed3c/soodles#229` 的候選程式、指引與本機 fixtures。
基線是 `069e866949c268efee3d529f4d9ae7a4fdf8c106`。
包含本檔的 Git commit 固定最終 source。`manifest.json` 固定 required artifacts 的 bytes。
它不授予 publication 或 landing 權限。

## 已實作的行為

Supervisor 在 initial authorization 前固定一份外部 target binding。
Admission、worker、Test Manager、publication、CI selection、landing、provider readback 與 next-Issue 使用同一 reference。
Generic runtime 使用外部固定 closure。Target 不需包含 Soodles 程式、tests 或 skills。
Legacy selection 保留原 profile 路徑。不同 targets 可以使用不同 repository、instructions、base 與多 job scope。

恢復時的自審發現一個遺漏。Legacy consumer 若依賴 generic producer，landing next 未攜帶 producer binding。
Provider readback 因而拒絕未註冊 repository 的 GET。現在只要 consumer 或任一 dependency 是 generic，next 就攜帶相關 bindings。
新增 control 經實際 `landing.provider_next` 與 `provider_readback.consume` 核對 GET、保存的 response 與原 owner continuation。
它不新增 provider authority，也不改動 dependency revision。

## 可重建的 fixture

使用包含本檔的 commit，在獨立 checkout 執行下列命令。
不要在 active atom 的 control root 重播 lifecycle。
Tests 自己建立並清除暫存 target Git repositories。
本次環境是 macOS 26.6.2 arm64、CPython 3.14.6、Git 2.50.1。
Python 只使用標準函式庫。所有 fixture source、輸入與斷言位於 `tests/test_generic_repository_binding.py`。
既有相鄰 controls 由 Test Manager 選定。

Fixture 的 `setUp` 從這個 source revision 複製 `GENERIC_LIFECYCLE_FILES` 與 `OWNER_FILES` 宣告的 closure。
它建立 synthetic carrier。它不啟動真實 Codex 模型或 Noodle daemon。
`target` 固定 Git 作者、時間、target source、workflow、contract 與 binding。
兩個 cases 使用 `example/first-target` 的 `trunk` 與 `other/second-target` 的 `stable`。
兩者的 workflow 都要求 `unit` 與 `lint`，各有一個具名必要 step。
驗證命令使用本次 Python interpreter 執行 `target.py`。
不同 interpreter 路徑與暫存目錄會改變 reference bytes；重播比較行為斷言，不比較這些路徑。

預期結果是全部 15 個 generic controls 成功。它們核對以下邊界：

- 兩個 target 不含 Soodles 程式，仍能 authorize、prepare 及讀回同一 admission。
- 外部 worker test/outcome entries 核對原 session、worktree 與 owner。Foreign lineage 被拒絕。
- Binding、runtime bytes、origin、base 或 target scope 不符時，在相關 effect 前拒絕。
- Publication 保留 target identity。重入已發佈 fixture 時，不再 push 或 create。
- CI 必須包含完整 jobs/steps、正確 head 與 attempt。Correction 使用固定 base_ref。
- Landing 的 unknown write 保留 checkpoint，等待 readback。Merge、closure、tree 與 producer revision controls 保留。
- Generic producer 的 readback 能回到 legacy consumer 的原 landing owner。
- Next-Issue create 先保存 offer。Unknown result 只要求 readback，不再次 POST。

Provider GET、push、PR create、merge 與 close 都由本機 fixture 資料或 callbacks 代替。
Generic delivery fixture 以 Git 建立 merge，再人工清除自己的 fixture worktree，最後檢查 `cleanup_mode=no_op` 的 reconciliation。
它 mock fetch 並核對選定 base。這不證明真實 Noodle cleanup、network 或 provider delivery 已執行。
既有相鄰 controls 另覆蓋 cleanup、host restore、owner lineage 與拒絕邊界。

## 實際執行與重播

下表保留原執行順序。各列有自己的 source hashes，不把早期通過結果標成最後 source 的執行。
最後的 dependency run 與 replay 使用相同 generic fixture bytes。
兩次都通過全部 15 個 generic controls。重播沒有再呼叫模型。

| Receipt | Test cases | Exit | Process wall seconds | Manager seconds |
| --- | ---: | ---: | ---: | ---: |
| `manager-final` | 493 | 0 | 72.273437 | 71.541 |
| `admission-final` | 66 | 0 | 16.594649 | 16.206 |
| `delivery-final` | 87 | 0 | 13.784272 | 13.43 |
| `recovery-dependency` | 81 | 1 | 15.515398 | 15.078 |
| `recovery-dependency-final` | 81 | 0 | 14.890377 | 14.521 |
| `recovery-replay` | 15 | 0 | 15.916834 | 15.52 |

`manager-final` 是 Test Manager 依 admitted base 選的 35 modules，共 493 cases，使用 4 workers。
它不是 full suite。後續程式修正只重跑受影響的 named modules。
`recovery-dependency` 的失敗來自新增 test 傳給零參數 `verifier_digest()` 一個參數。
修正該 fixture 呼叫後，`recovery-dependency-final` 的 81 cases 全通過。
失敗紀錄保留，沒有刪除 control 或跳過 hook。
各次 cases 有重疊，不能相加當作 unique coverage。

以下是實際 argv。若只需重建 generic 行為，使用最後一條 replay 命令。
完整 scope 與各 case timing 保存在對應 log。

`manager-final`：

```sh
./soodles test --base 069e866949c268efee3d529f4d9ae7a4fdf8c106
```

`admission-final`：

```sh
./soodles test --module test_generic_repository_binding --module test_supervisor_authorization --module test_supervisor_admission --module test_correction_preparation --reason 'Verify final generic correction/readback and missing-runtime refusal with legacy authorization controls'
```

`delivery-final`：

```sh
./soodles test --module test_generic_repository_binding --module test_candidate_publication --module test_landing --module test_cross_repository_dependency --reason 'Replay fixed generic fixtures and verify external binding location and encoded base readbacks'
```

`recovery-dependency`：

```sh
./soodles test --module test_generic_repository_binding --module test_provider_readback --module test_cross_repository_dependency --module test_landing --reason 'Cover legacy consumer with generic dependency bindings through provider readback and preserve existing landing refusals'
```

`recovery-dependency-final`：

```sh
./soodles test --module test_generic_repository_binding --module test_provider_readback --module test_cross_repository_dependency --module test_landing --reason 'Cover legacy consumer with generic dependency bindings through provider readback and preserve existing landing refusals'
```

`recovery-replay`：

```sh
./soodles test --module test_generic_repository_binding --reason 'Replay the final saved generic fixture inputs for the admitted reproducibility requirement'
```

## P-class 寫作與行為 feedback

`review-writing` 完成 13 份 saved guidance 的語意與 source-consumer 審查。
原始 bytes、修改理由與讀回存於外部 `original-guidance` 及 `writing-review.json`。
`eval-audit` 核對條件來自原 task/contract，並讀取 consumer reports 與 traces。
三個 cases 分別涵蓋 external entries、scope/多 job acceptance、unknown-write/schedule continuation。
這些 observations 來自一個 consumer session。它們不是三次獨立試驗。
Traces 是 consumer 自己記錄的摘要，不是完整平台 transcript。

恢復後，writer 核對 13 份 saved instruction hashes、原 requirements 與 inputs 均未變動。
Writer 透過 supervisor 提供的 `SOODLES_ADMISSION_LAUNCHER` 提交原 selection。
既有 stage-outcome owner 在恢復 session 記錄 round 1。
Schema Manager 回傳 `evidence_validity=VALID`、`behavior=PASS`、`criteria=SUPPORTED`。
Test Manager 的 `verified` 包含三個 cases；`cases=[]`，沒有要求新增觀察。
Writer 已消費 `next.operation=consume_verified_behavior`，繼續本次修正、artifact 核對與提交。
這個 receipt 的 `authorizes_landing=false`。它只支持這些 reported decisions。
它不能證明通用 Agent 正確率、改善幅度或未觀測的 provider effects。

Schema Manager 本次 projection 為 0.072417 ms，完整 feedback evaluation 為 4.878541 ms。
兩者是該次本機讀回的測量，不是未來延遲承諾。
原 consumer capture 記錄 117.656763 秒，未涵蓋最初讀取。
不能將同一 session 的時間分別相加。模型 tokens、價格與完整模型時間仍是 unknown。
本次沒有 benchmark 或比較實驗。測試 wall time 不等於整體交付時間。

## 證據保存與限制

原始證據保存在本機外部目錄：

`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/writer-229`

下列 SHA-256 綁定該目錄中的檔案。這些是 custody references，不是跨機器下載位置。
要核對原 raw log，接收者仍需取得這些檔案。上面的 fixtures 可從 source 重新執行。
新觀測須保留新的 result。模型重跑不保證相同 bytes。

| 相對檔名 | SHA-256 |
| --- | --- |
| `manager-final-invocation.json` | `76f72adbfb80d91cd4aab246ac0b51cf74de232c5d51311ef19c4ab408c20a0a` |
| `manager-final.log` | `a0429e3a2bd0a003d6cd71036b68c2a69a8a60239702b32653ea6168b63b3104` |
| `admission-final-invocation.json` | `68350365c55f9e9794fababaeba8a4bcec2383d8f48efec2298ee558fb2ade03` |
| `admission-final.log` | `f3330cf97218e773cb898bac25f4e7cb7b99b89dcf9f4349fbd6a389f19586d9` |
| `delivery-final-invocation.json` | `9d8a25f0719b649d984f8d3f0f73590667153830e0d80bf8c81f3e8c2c17ef65` |
| `delivery-final.log` | `c646ff7527f74c88b6c670aacc72db6e273ad373ad46e5c94ebaa856f84ae534` |
| `recovery-dependency-invocation.json` | `1aeec64ad30cb4e66a080102375a270e70fbd555d23ac54051fbd4b7dfc09100` |
| `recovery-dependency.log` | `f11e07f90546819a7a0f4af8f07418080a1a233d4952680933168ebbb5d9e8bb` |
| `recovery-dependency-final-invocation.json` | `8c933b56e11d3d472b47781d0473dcae6517caa34d1ccbedcfcae58a1a8989a6` |
| `recovery-dependency-final.log` | `540711dedf03147586139b3af3701449c6f8714c84cec646a72beb4034ff1cf9` |
| `recovery-replay-invocation.json` | `977cf770cb244f47eac4e6889a7e6b7dd5f42871e3ccdaff039af75d7657f787` |
| `recovery-replay.log` | `a746ba128985071e120fba3554587d0450106e414849e112efef5aa6b188ec2b` |
| `requirements.json` | `2d9da20b9c922a5f4ce9c4a4e61c9c7cc233f01e722e96cdab65e1f68a293384` |
| `writing-review.json` | `a09fc8ae6bcbfe0c1ded8545404cb93642c4fda3e004cbe315df27425222a469` |
| `feedback/protocol.json` | `9f20ee0cdd3fe80c255c1ccf3fe71c214a9dc75631c47a69a8aba57eb2a48eea` |
| `feedback/criteria-review.json` | `98b84a5a9ff0f3f335598dc453a87b6cd3ad3322650d712aed21ede5c037c991` |
| `feedback/selection.json` | `ded6463e36255ef129f57f521d083366306eb63b1d9938ab8de698148029eb86` |
| `feedback/recovery-owner-response.json` | `2ffe7f5ae2032c01ddf89b8c1628a5088ef1aa3d91963e5e1604f148fc5643e7` |
| `feedback/consumer/external_entries-report.json` | `632865d118aee0a24553ed4d2e184d6a7fcffcb9892b317d38eb669001bd28b6` |
| `feedback/consumer/external_entries-trace.txt` | `630dc7a36684d119ce8327f8e1198432493d3ba85f16f82a9f6d93c03a0f0d07` |
| `feedback/consumer/scope_and_acceptance-report.json` | `a29871ffbff375ba02e9874cd999823134a61b40a51a303a7ee3b8d9e70cb996` |
| `feedback/consumer/scope_and_acceptance-trace.txt` | `8f721a032c457303aefaf04a5aa4049c9a93027fa9ce4f41f5a758250c196b5e` |
| `feedback/consumer/unknown_write_schedule-report.json` | `b9c2f5caddff0e181060e01dbe430743a865f2913a833696684767d67b3f8cac` |
| `feedback/consumer/unknown_write_schedule-trace.txt` | `ae3f3f4b9f17ce1892a5754c887c7e10a7543a04ea532f7ba4aab5d4669d2dc2` |

## 後續 owner 與未完成需求

Writer completion 只交付這個 Soodles causal correction。
Publication owner、exact-head Linux canonical CI、external landing owner 與本機 reconciliation 仍須完成 factory delivery。
Test Manager 選出的 physical controls 是 `cleanup_recovery`、`cleanup_lock_recovery`、`delivery_recovery`、`base_recovery`、`order_handoff`、`interruption_resume`。
本 writer 沒有執行它們；它們保留給 canonical acceptance。

目前 Noodle carrier 使用 origin/HEAD。Generic admission 因此要求 base_ref 對應該 integration branch。
任意非 default base 仍不受支援；admission 在 effect 前拒絕該輸入。

原 supervisor 必須再以各 target 自己的 admission、owner 與 rollback boundary 完成真實生產。
它也須取得正常使用、實際 replay 與跨 target 並行證據。
本次沒有其他 target 的真實 source/provider mutation。
Factory fixture 通過或 factory PR 合併都不能代替這些 outcomes。整體使用者需求仍未完成。
