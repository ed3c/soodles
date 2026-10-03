# 未發布 receipt 的 typed revision 修正

本紀錄屬於 `ed3c/soodles#254`。Admission base 是 `cc0d235d0248947dd117a31c37f0a1d62924b4de`。
本紀錄只描述 writer 的修正及其觀察。它不授權 publication 或 landing。

## 原故障與證據

原 owner 在 Issue 251 保存 claim 與 native readiness 後，拒絕 `github.base_head`。
保存的 `run-3.stdout` 回傳 `push_receipts: []`。
隨後 `revision-adopt.stdout` 因 `scope.phase=execution` 拒絕 typed revision。
兩份原始輸出保留在 `/Users/neon/soodles-audits/manager-coverage-loops/host-plan-recovery/`。
本次 writer 沒有重跑原 251，也沒有操作原 248。

原 `scope_custody` 假設 receipt 存在就表示 publication 已開始。
Source 顯示 `_run_owned` 先保存 receipt，`candidate_publication.publish` 才檢查 base。
Publisher 在 base 檢查通過後才保存 branch push 或 PR create intent。
因此原 gate 把本機證據誤認為 provider effect。
單純刪掉 gate 仍不足。原 `scope_projection` 會讓 successor 沿用舊路徑。

## 資料與執行邊界

修正沿用既有 `scope_amendment.prior` 與 `scope_history`。
Retained receipts 表示採納前的完成紀錄。Current receipts 表示目前 successor 的證據。
Owner 固定歷史 snapshot 與 session events，並保存各檔案的 path 和 SHA-256。
Owner 從 revision output 推導 current receipt 目錄。
新 receipt 尚未存在時，consumer 必須保留缺少狀態。

新增另一份 receipt registry 會重複 scope history 的所有權及持久化狀態。
本次選擇由原 projection 與 receipt view 提供資料。
Repair、cost、publication、postwrite 和 reconciliation 必須使用同一有效路徑。
歷史驗證使用固定來源。Fresh publication 保留原 live custody 檢查。

Owner 必須先拒絕已有 publication intent、push process、landing 或 publisher journal 的狀態。
有 receipts 時，只接收完整且符合原 completed custody 的 pair。
Partial pair、foreign identity 或來源改動必須在 durable adoption 前拒絕。
寫固定副本後若中斷，重入只能接受相同 bytes。
原 authorization、judge、repair ledger 和 cost subject 保持原身分。

## Writer 方法與驗證

Writer 使用 selected `execute` 與 Poteto Mode Bug fix。
本次沿用 saved runtime evidence，沒有對原 atom 做 fault injection。
Native subagents 分開處理 receipt owner、cost consumer 及消費端控制。
`/Users/neon/.cursor/rules/pstack-models.mdc` 選擇 inherit-parent。
本次沒有使用上游 Poteto wrapper，也沒有跨模型比較。

Test Manager 選定七個 module，沒有 full suite 或 physical control。
223 個不同案例有通過結果。下表分開列出可重用的結果與最後重跑結果。

| Module | 通過案例 | 保存結果 |
| --- | ---: | --- |
| test_admission_revision | 23 | core/run-4.stdout |
| test_cleanup_continuation | 10 | integration.stdout |
| test_correction_preparation | 28 | integration.stdout |
| test_cost_telemetry | 32 | integration.stdout |
| test_lifecycle_activation | 22 | integration.stdout |
| test_scope_amendment | 12 | integration.stdout |
| test_issue_atom | 96 | issue-atom-final-2.stdout |

上述路徑位於 `/Users/neon/soodles-audits/manager-coverage-loops/issue254-writer/`。
整合執行共有 200 個案例，其中 routing fixture 的一個案例失敗。
該 fixture 缺少完整 admission history。修正後，test_issue_atom 的 96 個案例全部通過。
其他五個整合 module 的 104 個通過結果符合目前 source，故保留使用。
Routing fixture 固定 admission-history view，並使用真實 projection 路徑。
Core 的組合控制另行驗證真實 history view、兩次 released revision、各自 base 與 session 成本。
兩者都不能當作完整 provider-cost 執行證據。

Core 最後執行為 46.22 秒，整合執行為 104.546 秒，最後 test_issue_atom 為 81.87 秒。
這些是各次正常 invocation 的測量。它們不是互斥工作成本，也不證明效能改善。

先前失敗與中斷均保留。Core 曾因 fixture 覆寫 envelope、production 未傳入 issue_body，
以及 fixture 未按已保存 selection 的 bytes 計算 body hash 而失敗。各原因均已修正。
Cost 初次執行曾發現 NDJSON fixture 與 malformed/base_recovery 邊界問題，後續 32 個案例通過。
Consumer 控制曾缺少 revision fixture，另一次執行因並行 source 改動而拒絕。
後續整合前已固定 source。第一次最後重跑以 exit 143 結束，沒有終端 test receipt。
原因仍未知。該次不計為通過；第二次最後重跑才提供 96 個通過結果。

Native 獨立 reviewer 檢查 source、consumer coverage、註解及重複碼。
Reviewer 發現 retained-publication symlink 可讓 owner 在拒絕前寫入 control root。
修正增加寫入前的目錄與 receipt 路徑檢查。
獨立 disposable readback 確認拒絕後 control 目錄沒有新增檔案。
Reviewer 最後沒有未處理 blocker。
審查使用同模型 native agent，沒有完整平台 transcript，也沒有 wrapper 或跨模型比較。

P-class 文件沒有改動。本次不宣稱 Agent 決策改善。
Manifest 沿用 schema 1。其 instructions 欄固定 issue_atom.py 的 baseline 與 treatment bytes。
該欄不表示本次改動 P-class guidance。

## 證據定位與限制

外部證據根目錄包含 work-record.json、decisions.tsv、design-decision.md 及 source-evidence.json。
它們分別保存方法 pins、選擇理由、資料設計比較及原故障來源 hashes。
review/final-accepted-source-and-readback.json 保存最終 source 與原始測試輸出的 hashes。
review/final-readback.md 保存獨立審查的結論與限制。

Fixtures 驗證本機 owner 的接收、拒絕、retention、current path 與 consumer 行為。
部分 fixture 提供 admission、release、provider 或 readiness 資料。
因此它們不證明完整 Noodle 實體執行或真實 provider 結果。
本次沒有重置原 repair ledger、替換授權、重放 provider write 或復原 live atom。

## 後續 owner 工作

Supervisor 仍須取得本 Issue 的 exact-head CI、publication、landing 及本機 reconciliation。
修正接受後，supervisor 才能固定 corrected lifecycle 與 fresh target，讓原 251 的 owner 接續。
原 251 交付後，原 248 才能走自己的 postwrite recovery。
Fixtures 不建立這些真實交付結果。

Parent 的 CLI contract coverage、既有 lifecycle cost consumers、owner decisions 及 matched decision measurement 仍未完成。
本修正不處理 issue-create readback policy、initial lifecycle source 或 provider-only cost feedback。
Parent 的完整狀態仍在 `/Users/neon/soodles-audits/manager-coverage-loops/plan.md` 與 `handoff.json`。

保存的最終審查引用如下。

- `review/final-readback.md`，SHA-256 `b54eb038f915b619ea147f5c8916fda63c77332d69748f88a5c8ba2f781c82c6`。
- `review/final-accepted-source-and-readback.json`，SHA-256 `12ae6baa38fb27d990d77dfbcfd4f4160628b0df463f666daec2f493c74efae2`。
- `source-evidence.json`，SHA-256 `49d0d200f4a9718bd62006c292a46aefe5ec045e76abab3ab61c3ab653c2f45b`。
