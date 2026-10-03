# Issue 229 的 writer 結果與重建方式

本記錄只涵蓋 `ed3c/soodles#229` 的候選程式、指引與本機 fixtures。
下列先保存歷次結果。最新 writer 的範圍與未完成工作見「Fresh-root writer 整合」一節。
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

目前預期結果是全部 18 個 generic controls 成功。原有 15 個 controls 核對以下邊界，新增 3 個 controls 見下方 base integration 記錄：

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

## 指定 base 的整合記錄

本次保留原 candidate `847e8637ddd97f0aae0de911236512766066b3cb`。
原 admission owner 選定 `5b0a73eae31fb414deeed4ffdf8082a71aee4e3d` 為整合 base。
Writer 在同一 Noodle worktree 建立 merge。它沒有重套 generic patch。
原 instruction source、judge、interruption 與 failed session 歷史都保留。
此段補充前面的原始執行記錄，不把舊結果改標為新 source。

初次整合通過 565 個 controls。獨立 source review 仍發現三項缺口。
新加入的 base recovery 與 interruption producer 沒有傳遞 target binding。
Generic revision 產生新 runtime 路徑，但原 validator 要求 execution 完全相等。
Original repair source 只讀 legacy closure，導致 generic history 的 binding hash 改變。
因此，「兩側 controls 都通過」不足以證明兩側 producer 和 consumer 已接合。
Writer 修正這三個交界，並加入三個最小 fixture controls。

Recovery producer 現在傳遞原 target reference。
Producer 保留原 task、instructions、owner lineage，再將 runtime argv 綁至新的 admission bundle。
Loader 要求 outcome 和 test argv 都指向目前 envelope 所在目錄的固定入口。
Recovery 與 revision 比對仍拒絕原要求或 target reference 改變。
若只保留舊 argv，consumer 會讀到舊 envelope，無法接受新 session 的 binding。
若任意略過 runtime identity，foreign entry 可能被接受。因此 loader 另核對新 bundle 路徑。

Repair reader 使用 AST 讀取外部固定原始碼的完整 closure。
AST 是 Python 語法樹。Reader 只接受 literal `LIFECYCLE_FILES` 與它加上 literal generic tuple 的運算。
它不執行或 import 歷史 Python。非法 expression、缺少檔案或 bytes 不符都拒絕。
使用目前 runtime 的常數比較簡單，但會改變原 repair history 的身分，所以不採用。

新 controls 核對新 bundle argv、舊 argv 拒絕、revision readback idempotency、target reference 竄改拒絕。
它們也核對原 generic closure 不受目前常數漂移影響，以及 generic-only bytes 的竄改拒絕。
既有相鄰 controls 保留 legacy history、counters 與 unknown effects 的原規則。
獨立 reviewer 再次讀取修正與 controls，沒有提出未處理缺陷。
這是 source review 與本機 fixture 證據，不是 provider acceptance。

本次 normal Test Manager 執行如下。各列有重疊，不相加作為 unique coverage。

| Log | Cases | Exit | Manager seconds |
| --- | ---: | ---: | ---: |
| `test-round-1.log` | 565 | 0 | 125.452 |
| `generic-round-2.log` | 18 | 0 | 19.677 |
| `affected-round-2.log` | 130 | 0 | 82.294 |
| `generic-replay.log` | 18 | 0 | 32.174 |

初次選擇使用 `./soodles test --base 5b0a73eae31fb414deeed4ffdf8082a71aee4e3d`。
修正後只執行 `test_generic_repository_binding` 與 9 個相鄰 modules。
完整 selection、reason、case timing 與 stdout 保存在各 log。
最後 replay 仍由 Test Manager 選 `test_generic_repository_binding`，共 18 cases。
Replay 使用相同 fixture inputs 與程式行為。期間只移除一個未使用 import，沒有改變執行邏輯。
這是原可重建需求的實際 replay，沒有啟動模型或 provider。

目前 13 份 P-class saved bytes 由一個 fresh native consumer 處理原三個 cases。
Test Manager 先要求這三個 observations，沒有要求 software suite。
原 launcher 在本次 revision session 記錄 schema-2 feedback。
Schema Manager 回傳 `VALID/PASS`，writer 已消費 `consume_verified_behavior`。
Consumer capture 不是完整平台 transcript。它不支持 wording improvement 或整體正確率。
Hypothetical input 未提供 carrier origin/HEAD，故該輸入的 admission 合法性仍未知。
這個缺口不允許將選定 stable 改成 main，也不影響缺少 job 時拒絕 landing 的結論。

本次外部證據目錄是：

`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/writer-229-base`

| 相對檔名 | SHA-256 |
| --- | --- |
| `test-round-1.log` | `e68c1191d255c5fe439822165e4f067f8b02e0cb18ba8377529a356506804fa5` |
| `generic-round-2.log` | `f9f9dee0c8737bc5195f44b227cccf6cd92a84339b436c3f9d393f64e898e61c` |
| `affected-round-2.log` | `68735ed2762af4d9e0414372b6ca2eea816b8cfd6a529a7d5ad853be0ba3d244` |
| `generic-replay.log` | `3171b90fc88e202db8a8fcd1bc1fb053fafe073696b790f4c0c2672a1566b4ea` |
| `work-record.json` | `7a9961a6c71215293c650aa8eb599acb68c9bef6928c804757e30b9fed7f6f1e` |
| `writing-review.json` | `d7f9dd405d28b24e4b221ab2e9306aa79e761f0d429844ab19be36a4ad97a09c` |
| `feedback/protocol.json` | `2e3e0e2018e5a3d0637364080924530e49208382e2a5e91776fe0c2fb297c6db` |
| `feedback/selection-observed.json` | `dfce2124f447c7e9f90687e8d6e24ef78f5c1d2fba60d4b0039cfb535510d19a` |
| `feedback/observed-response.json` | `0392bc1a06db5e314ad86faded9e80d4ee2b3de07e54290b1471ca896607ce63` |

這些本機 custody references 需要另外交付 raw files 才能跨機器核對。
Manifest 綁定本次保存的 required artifacts。Writer 未執行 publication 或 provider mutation。
Factory delivery、Linux exact-head CI、reconciliation，以及各 target 的真實正常生產與並行結果仍由原 owners 接續。
整體使用者需求尚未完成。

## Fresh-root writer 整合

本次 order 是 `soodles-229-ee4f5b2b9bed`。本次 admission 的固定 base 是
`4b60629a44a503637c93207a03cc81717148a076`。
Writer 使用 Git merge 整合 `f1d7ed9f68fe611394d4055b75c261c85789e633`，保留兩側歷史。
合併沒有文字衝突。独立 native reviewer 檢查了新 base 與 generic consumers 的接合。
它沒有發現未處理的 source blocker。審查不是跨模型比較，也不授予 provider effects。

原 Linux CI run `37126477091`、job `111212654260` 的失敗仍保留。
`acceptance.base_recovery` 通過。`acceptance.order_handoff` 報告以下錯誤。

```text
handoff_probe.<locals>.<lambda>() takes 1 positional argument but 2 were given
```

Source tracing 確認 legacy callback 只收一個參數。
本次修正讓沒有 binding 的 claim 恢復 `fetch_main(root)`。
Generic claim 仍傳入固定 `base_ref`。沒有修改 frozen oracle 或忽略例外。
兩個既有 generic delivery cases 使用嚴格雙參數 callback，核對 `trunk` 與 `stable`。
Legacy detached-control case 使用嚴格單參數 callback，核對完成狀態與未切換 branch。

Test Manager 從 admitted base 選出 37 modules，共 572 cases。
第一輪有 1 個失敗。Legacy cloud-cleanup test 還期待兩參數呼叫。
Writer 依原相容性要求將該斷言改回一參數，保留原 cleanup 與 checkpoint 斷言。
第二輪只選 `test_landing` 與 `test_generic_repository_binding`，69 cases 全通過。
Generic 的 18 cases 在兩輪都通過，構成本次合併後的實際 fixture replay。
第一輪其餘 36 modules 均通過。其中 generic 已 replay，另外 35 modules 沿用原結果。
沒有重跑完整 suite，也沒有將初次失敗改標為成功。

| Receipt | Cases | Exit | Process seconds | Manager seconds |
| --- | ---: | ---: | ---: | ---: |
| `test-round-1` | 572 | 1 | 182.549969 | 181.203 |
| `affected` | 69 | 0 | 29.919811 | 29.366 |

實際 argv 保存在各 receipt。可重建命令如下。

```sh
./soodles test --base 4b60629a44a503637c93207a03cc81717148a076
./soodles test --module test_landing --module test_generic_repository_binding --reason 'Verify legacy one-argument fetch with generic fixed-base callbacks and replay generic fixtures after exact base merge'
```

另以 Test Manager 選定的 `order_handoff` 執行未修改的 `handoff_oracle.py`。
它使用本次已選定的 macOS Noodle binary，其 SHA-256 為
`347dc64b9d98bc7f290ab6e6e4a54866a11f8a5bcb653b91122becb59c31acc5`。
首次 fixture 繼承目前 writer 的環境，12.670747 秒後在 A projection 前逾時。
第二次只在 fixture process 移除 `NOODLE_` 與 `SOODLES_` 開頭的變數。
同一 oracle 與 binary 在 4.947003 秒後回傳 `VERIFIED`。
Receipt 記錄 A typed outcome、process exit、Noodle cleanup、B admission 與零殘留。
這個結果支持環境隔離後的本機 fixture，不表示已取得 Linux exact-head acceptance。
原失敗與隔離後結果都保留。沒有更換 binary、延長 timeout 或修改 oracle。

重建 handoff 時，使用 receipt 的同一 argv 與 binary digest。
以下環境處理只影響建立的 fixture subprocess。

```python
fixture_env = {key: value for key, value in os.environ.items()
               if not key.startswith(("NOODLE_", "SOODLES_"))}
subprocess.run(receipt["argv"], env=fixture_env, check=True)
```

本次外部證據位於 `/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/writer-229-fresh`。
Source、fixture inputs、預期斷言與依賴仍固定在本 commit。
暫存路徑與模型輸出不保證相同 bytes。Python 使用標準函式庫。
Native physical fixture 使用真實 Noodle processes，但 provider 與模型輸入仍是 fixture。
它不代表 medium-compiler 正常生產或真實跨 repository 並行。

本次 13 份 P-class 指引以當前 saved bytes 重新綁定。
Writer 修正「沒有 binding 就使用 repository entry」的錯誤推論。
Task 明確固定 launcher 時，該 owner 選擇也適用於 legacy admission。
Test Manager 選四個情境。Fresh native consumer 只讀指定 instructions 與 inputs。
新增的 `legacy_launcher` 情境核對沒有 binding 時仍使用已固定 outcome entry。
原 launcher 在同一 Noodle session 記錄兩個 feedback rounds。
Round 1 的條件是 `SUPPORTED`，行為因缺少 observations 而保持未知。
Round 2 是 `SUPPORTED`、`VALID/PASS`。Writer 已讀 capture 並消費 `consume_verified_behavior`。
沒有重啟 writer，沒有聲稱跨模型比較，也沒有用舊 bytes 的 PASS 代替本次觀測。
Model tokens、費用及完整 platform transcript 仍未知。Schema projection cost 在原 response 中保留。

以下檔案均位於本次外部證據目錄。它們保留實際失敗、scope 與結果。

| 檔案 | SHA-256 |
| --- | --- |
| `test-plan.json` | `d612b322c235bf8e3968c461478bb43129f14c5682c6b4be5e69fd8d4940887e` |
| `test-round-1.receipt.json` | `7bf549fafded3902f0675860903f170f9b1fefd1c7584e67d248c370aafa3ccc` |
| `test-round-1.stderr.log` | `6c297a4f77afcc64442f08c3fc3c39d074ae985559a0916939696e2d2606ed2d` |
| `affected.receipt.json` | `7a467e5686d9ea1d94bd85307b1491b47038b4e538a007ea230114aaceec7667` |
| `affected.stderr.log` | `930cbb925af3a658d377dcf1abae779507b38d2b0d59822a7c0736c1c15a9c82` |
| `handoff.receipt.json` | `903648a961a27c56476703633a7d26793c8192f72713e2b5b768025eac4420fc` |
| `handoff.stderr.log` | `8f9bb28501d94df8477bc6b4fc88715bb5bc8358b44f33d88fb15f691c19ed3c` |
| `handoff-isolated.receipt.json` | `429a5cacae260912411a1ab06c67dc93188f18c437c7006f86ae3aad0ad25eee` |
| `handoff-isolated.stdout.json` | `8fff93cd023b4c92c53ec4401c5957175b8d7c817d839cb3783ce1d76c1b8c6d` |
| `integration-review.json` | `ff499223a231e595d4a0061ac63e7a896b36ae19ce5573621d0f3d0bb0328704` |
| `feedback/protocol.json` | `edf06a88e8119e4b9cbfb466f092d4367b6c5364a8c411a8f41781d00e12d352` |
| `feedback/selection-observed.json` | `1d27af57d20cf5a08e55557064f90c98bbb55db9ee87f6f326f1e8fc698e5ee9` |
| `feedback/observed-response.json` | `293c13365ab083e6a901b16a073ebe7b1e02ad0f8cd74f965612d43c0bc7de21` |

本次 writer 未修改原 quiescent atom、原 worktree、provider 或 frozen judge。
原 supervisor 接續 PR244 publication、新 candidate 的 Linux exact-head CI、external landing 與本次新 order reconciliation。
之後仍需為 medium-compiler 提供獨立 target admission，取得正常使用、replay、持久成果、Production 與真實跨 repo 並行證據。
本次 writer completion 不表示這些工作已執行，也不表示 full autopilot 已驗收。
