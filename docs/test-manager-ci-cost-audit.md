# 正常 CI 必要性與成本審視（2026-10-01）

後續實作已按本文優先順序準備：品質分析改為明確 workflow dispatch；
移除合併後重複 runtime 觸發並沿用既有落地 parent/tree/main 判別；
fixture 選擇改查 Python import，新增逐案例與 discovery log。
下文保留原始分析當時的量測與狀態，不代表後續部署結果。
實際效果只能由新版本正常 CI 證據確認，不能沿用原始秒數宣稱已節省。

Test Manager 管理本次分類；本文件是 N-class 觀察，不是第二份測試選擇表。
P-class 原則在 `.agents/skills/test-manager/SKILL.md`；可執行選擇仍由
`test_manager.py` 擁有。本次只讀正常執行紀錄與原始碼，沒有重跑測試、
benchmark 或模型實驗，也沒有修改 CI 執行碼。

## 結論與量測邊界

「已按需選到 345 項」不等於「345 項都必要」。目前只做到模組級選擇，
還有全庫品質觀察、PR/main 重複測試、fixture 相依擴散與個別案例內重複
啟動 CLI 的成本。最快的改善順序是先處理可避免的工作，再優化執行速度。

| 正常執行 | 可追溯證據 | 實測時間 | 意義 |
| --- | --- | ---: | --- |
| PR runtime | [36811565013](https://github.com/ed3c/soodles/actions/runs/36811565013) | job 28 秒；acceptance 16 秒；unit phase 14.879 秒 | 23 模組、345 案例、無 physical controls |
| PR quality-report | [36811565127](https://github.com/ed3c/soodles/actions/runs/36811565127) | job 285 秒；安裝 8 秒；全 scope 分析 268 秒 | 全庫結構指標觀察，不是 runtime 驗收 |
| main runtime | [36811628386](https://github.com/ed3c/soodles/actions/runs/36811628386) | job 36 秒；acceptance 20 秒；unit phase 18.991 秒 | 再選同樣 23 模組、345 案例，無 physical controls |

PR head `19288c09cb7856781259a8d51b2b36442bd46520`；merge head
`4acda3aba67e1c3bcca2cb35f36146137148bde4`。兩者 tree 都是
`dddc0983a3f665ddb6dc06a17a12c3a798f77165`。相同 tree 是重用審查的起點，
不是省略新 provider 身分驗證的充分條件。

三個已觀察 job 共 349 runner-job 秒，其中品質報告占 81.7%；它們有重疊，
不能相加當作交付等待時間，也不含其他 collector job 或排隊時間。
PR 在 03:40:52 UTC 合併，品質 job 到 03:44:54 才結束，故這次 285 秒
是背景成本，不能聲稱刪掉它會讓這次合併提早 285 秒。步驟時戳只有秒精度。

## Test Manager 的必要性分類

| 類別 | 必要觸發與保護行為 | 本次判斷／後續處置 |
| --- | --- | --- |
| 當前候選與 provider 身分 | 防止讀錯 Issue、head、base 或落地錯誤候選 | 保留当前交付需要的 readback；不是每次重跑完整 regression 的理由 |
| 變更行為的局部控制 | 變更影響實際呼叫者；案例能區分正確／錯誤輸出或副作用 | 按方法、分支、資料輸入審視，不能只用檔案名稱推論全模組必要 |
| 測試器自己的拒絕控制 | runner/selector 改變時，防止失敗、skip、提早 exit 被當作成功 | `test_test_suite` 的 5 項有不同判別目的；只在此邊界受影響時執行 |
| fixture 與 process 成本 | 只有涉及真實 Git、檔案權限、signal、鎖或 CLI 邊界時需要真實效果 | 先拆清建置、啟動與判別成本；不要把所有測試都換成 mock |
| Noodle physical controls | 受影響的 runtime/worktree/cleanup 等實際行為 | 本次 0 項，無下載／執行成本；維持按需，不補跑 |
| 全庫品質指標 | 有明確結構分析問題、指定比較範圍與結果使用者 | 改為按需執行的首要候選；一般 PR 不應因為「有更新」就做全 scope 分析 |
| 跨入口重複執行 | 新 head 或新環境真正帶來尚未覆蓋的行為 | 審查 PR→main 可重用的控制；保留 merge/provider 差異控制，不能直接刪 main 驗證 |
| 歷史／重複案例 | 已有另一個現行控制覆蓋同一可觀察失敗 | 可替換或刪除，但先指出留下的控制；單憑慢或名稱相似不足以刪除 |

## 23 個模組的觀測與觸發分類

下列是工作程序秒數，四個 worker 會重疊；合計 **47.150 秒**，不是 elapsed。
「直接」表示本次來源邊界或測試檔改變，仍不證明每個案例必要。
「相依」表示經測試檔 fixture／文字參照選入，必須再追到實際變更符號。
每個模組所有案例的執行 ID 已從正常 log 取出；只記錄到 105 項慢案例時間，
其餘 240 項沒有個別時間，不能當作零。

| 模組（省略 test_） | 案例 | 秒 | 本次選擇依據／必要性待辦 |
| --- | ---: | ---: | --- |
| issue_atom | 68 | 6.105 | 直接：閉環／修正行為改變；逐項分離受影響分支與通用 setup |
| supervisor_authorization | 16 | 5.939 | 相依：借用 issue_atom fixture；檢查 bundle 輸入及授權行為，不預設整模組必要 |
| comparison_gate | 11 | 4.762 | 直接：publication 消費端及 fixture 改變；保留比對成功／拒絕与 effect 前驗證 |
| stage_outcome | 13 | 4.371 | 相依：issue_execution fixture；event outcome/身分拒絕要追到受影響輸入 |
| candidate_publication | 13 | 3.166 | 直接：native readiness schema 與執行範圍改變；正反向 receipt 必要 |
| landing | 51 | 2.991 | 相依：admission/execution fixture；落地判別範圍是否受影響待逐項縮小 |
| report_evaluation | 13 | 1.985 | 直接：測試檔改變；報告與身分判別，非重新跑模型實驗 |
| candidate_verification | 3 | 1.950 | 直接：manifest、替代歷史 replay；綁定 Git bytes 與缺件拒絕 |
| landing_bootstrap | 13 | 1.890 | 相依：publication/landing fixture；確認 custody 真受此次修改影響的部分 |
| context_recording | 10 | 1.705 | 直接：測試檔改變；保留 instruction metadata 正反控制 |
| issue_execution | 25 | 1.700 | 相依：issue_admission fixture；自身程式／測試檔未變不代表資料輸入未變 |
| test_suite | 5 | 1.590 | 直接：manager/runner 改變；完整執行、失敗／skip／提早 exit／空 suite／scope 拒絕 |
| issue_resume | 10 | 1.536 | 直接：移除歷史證據 replay；仍需現在的綁定與恢復拒絕控制 |
| landing_continuation | 1 | 1.530 | 直接：現在 CLI continuation，單項內含多次流程，不等於廉價 unit |
| instruction_context | 8 | 1.490 | 直接：producer CLI 正例與欄位拒絕；fixture 相依只是一部分 |
| lifecycle_activation | 5 | 0.946 | 相依：supervisor_authorization fixture；確認實際 bundle activation 受影響面 |
| portable_packet | 14 | 0.945 | 直接：測試檔改變；封包完整性控制，不能推論需要 build Noodle |
| admission | 12 | 0.691 | 直接：acceptance/CLI/workflow 改變；收斂選擇及身分控制 |
| local_continuation | 23 | 0.672 | 直接：issue_atom 消費端；wait/refusal/continuation 的可觀察分支 |
| provider_credential | 13 | 0.398 | 直接：測試檔改變；supplier 身分與拒絕；不表示要活體 GitHub 寫入 |
| quality | 5 | 0.323 | 直接：測試檔改變；量測工具的局部控制，與 285 秒全庫報告分開 |
| delivery_refs | 1 | 0.257 | 直接：soodles/workflow 邊界；文件引用的局部檢查 |
| issue_admission | 12 | 0.208 | 直接：測試檔改變；契約驗證與供其他測試使用的 fixture 分开追蹤 |

前四個模組共 21.177 worker 秒，占 44.9%。六個未改動且只經相依擴散
選入的模組共 17.837 worker 秒；這是值得審視的工作量，**不是已證明可刪的量**。

## 微觀發現

1. `test_manager.select` 對改動的 `test_*.py` 做全文正則搜尋，再遞迴擴散。
   它不能區分 import、字串／註解或實際使用的 helper。這是現有選擇方式的
   過度選取風險；本次未證明有純註解造成的誤選，不能虛報已找到那種案例。
   `test_issue_atom` 的 fixture `setUp` AST 未改，卻把借用它的 authorization
   測試選入，進一步帶入 lifecycle activation。fixture 也會讀改動的
   `soodles.py` 和其他 bundle bytes，所以不能只看 helper AST 就刪掉消費端。
   最小下一步是分開測試方法改動與共享 fixture／輸入改動，再改原有選擇器，
   不另造一份 CI 專用政策。

2. `test_committed_damage_and_legacy_bundle_are_never_repaired` 單項 **3.043 秒**，
   其中有 3 個 bundle 元件 × 7 種損壞的迴圈。每個組合都重新產生授權、
   啟动 CLI，再比對 refusal、inode 與未被覆寫的 bytes。
   缺件、symlink、directory、權限、JSON 重複鍵等是不同拒絕面，不能一概删除。
   可縮小的是跨層重複：資料／檔案拒絕留在最近的 owner，CLI 只保留需要
   證明 transport、exit、輸出和副作用的代表；signal/concurrency 控制仍使用
   真實 process。現有 log 未分離 setup 與 CLI 秒數，尚不能量化此項節省。

3. comparison 篡改案例 **1.438 秒**：四種情境各自建 Git fixture，再證明
   analyzer 不曾執行。必要的是「驗證失敗早於執行」；重複建置是否可共享
   不變資料要保留各情境隔離，不能用較少斷言冒充加速。
   landing continuation **1.264 秒**則測真實 CLI 回傳 argv、fresh readback
   與 unknown-write 不重送，和直接呼叫函式不同，不能因案例只有一項就刪除。

4. worker 固定最多 4 個、按模組名稱排隊；`supervisor_authorization` 在排序
   後段且耗時 5.939 秒，存在尾端排程成本。模組時間含 process/import，
   unit phase 還含 discovery。先縮小不必要工作，再考慮利用已存在的正常
   時間安排長工作，不先增加 worker、跑 benchmark 或建立持久化排程系統。

5. quality `measure` 對 base/head 逐檔呼叫 Git，再逐 scope 分析，最後另掃
   `all_python`。全域 clone 檢查有跨 scope 意義，不能直接宣稱重掃都無用；
   但那是特定全庫問題的觀察需求，和日常候選是否正確無關。先讓全 scope
   成為有明確問題的按需工作，比替它快取／平行化更直接。將來若做增量指標，
   要標明無法推論全庫 clone 與全庫分母，不能沿用全庫報告的名義。

6. main 與 PR 相同 tree、相同選擇，仍實際跑了兩遍；main phase 18.991 秒。
   本次只能確認重複執行，還不能把它全算作可避免：Git history、base/diff、
   runner、recipe、provider head 是重用時必須比對的輸入。重用的是相符的
   行為證據，main 當前身分／整合差異仍有自己的判別，不能假造 main 測試成功。

## 管理決策與實作狀態

| 優先次序 | 決策 | 真正減少的成本 | 本次狀態 |
| --- | --- | --- | --- |
| 1 | 全庫品質報告交由明確分析需求觸發；局部 recipe 控制維持局部 | 最多避免本次同類的 285 秒背景 job；尚非未來節省保證 | 已加入 Test Manager 指導；workflow 尚未改 |
| 2 | 審查 PR→main 可重用覆蓋並保留整合差異控制 | 重複測試的部分 runner／main 完成時間 | 已確認 36 秒 job 與相同 tree；未實作重用 |
| 3 | fixture 依賴追到符號及輸入，收窄模組與案例 | 受影響控制以外的工作 | 找到擴散鏈；尚未證明具體可刪案例集合 |
| 4 | 在後續正常執行 log 分離 case、setup、import/discovery 時間 | 支持下一次有依據的 fixture／CLI 縮減 | 此次未加 runtime logger，沒有另跑來補數字 |

本次交付是成本／必要性分析與 Test Manager 的管理規則修改，尚未部署。
不能把本文件的「應改為按需」解讀為 CI 已經改完；目前自動全庫品質報告、
模組級選擇及 main 重跑依然存在。此前已上線的全套→按需 runtime 選擇仍有效。
本次也不處理先前落地後的 Noodle 本機 reconciliation 失敗。

原始本機證據保存在 `/Users/neon/.codex/soodles-test-manager-delivery-kqmttf0t/`：
`final-runtime.log`、`micro-main-runtime.log`、`micro-ci-provider-readback.json`、
`micro-test-inventory.json`（345 個 case ID、105 個已報時長、23 個 module 時長）。
這些是本次只讀分析產物，不是新測試執行或落地許可。
