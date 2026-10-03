# 真實交付資料的可證範圍

後續使用者已將「最短路徑」明確定義為 Agent 決策數量。本文的耗時分析保留為歷史輔助資料；主指標改以[決策量測定義](decision-metric.md)為準。下文關於完整成本的需求，不再作為決策數量比較的前提。

本輪使用既有 Test Manager 與 Schema Manager 消費真實歷史資料。來源是 Issue #215、PR #216 的原始 authorization、process receipt、Noodle session、CI 及 landing readback。沒有啟動新 worker、重跑驗證或重送 provider 寫入。

## 既有入口與實際回饋

本輪對 initial 和 correction 的原始 manifest 分別執行 `soodles atom cost-report`。入口檢查來源雜湊、authorization、head 與 session 關係。兩份報告都回傳 `reported`。Test Manager 的 `review_cost` 記錄實測成本、歷史失敗與缺失量測，再把結果交給 Schema Manager 的 `project_cost`。

兩份成本審查都回傳 `needs_owner_readback`。因此本輪繼續讀取各自的原始 owner receipt，交給 `project_owner_feedback`。initial receipt 保留失敗 head 所需的原 continuation。correction receipt 是同一 Issue 的後續 `resolved` 回報。Schema Manager 對此回傳 `history_retained`、`next=null`、`effects=[]`。它沒有把舊失敗當成目前仍需重播的工作，`effectiveness` 仍為 `unknown`。

本輪消費的是歷史終態，沒有主張目前 provider 狀態已被重新查詢。完整輸入、CLI stdout、stderr、時間、程式雜湊與投影存於 `/Users/neon/soodles-audits/real-path-evidence-ngpdcpdq/`。

## 可以支持的結論

Issue #215 的初次 exact-head CI 失敗。原 head 是 `e8ffb08b5022045d10a917195fbc4a254e87a270`。修正 head 是 `aca931d0f41f00ad83a79684ef20648a30b610af`，其 CI run `36881013815` 成功。修正沿用 PR #216 與 Noodle order `soodles-215-6c708f8e1f03`。

原 owner 終態記錄 merge `f5df50628e5289788f4185fb9f10a8b15dd23c69`、Issue 關閉、Noodle order 完成、session 停止與 host finalization。原始 `readback.json` 同時包含 merged PR、closed Issue、成功 CI 及 provider main 的 commit。其 canonical JSON 雜湊為 `38450f3bda5dfd54814fbc29cab8926f3800141dd1d186f4ff56c14c4d47095b`，與 landing owner 的 `observations` 記錄吻合。

所以這批資料支持「這顆 Issue 在修正後，經既有 owner 完成交付與本機 reconciliation」。這是原始 receipt 的一致性與所記錄執行的證據。離線檔案不能取代一次新的 provider 查詢，也不是對所有任務的保證。

恢復範圍也有界限。correction run-2 曾因 Noodle cleanup 的三個 unmerged commits 而拒絕，run-3 才到達 resolved。現有 process receipts 未記錄兩者之間的全部修正動作。因此只能證明拒絕後續行成功，不能宣稱全自動修復，或證明未知 PR 寫入後的 crash recovery。

## 不能把這兩段當成速度比較

| 實測資料 | 初次完整實作 | 後續故障修正 |
| --- | ---: | ---: |
| observer 首尾時間範圍 | 1783.16 秒 | 397.06 秒 |
| 已觀察 foreground interval union | 116.90 秒 | 302.67 秒 |
| CI job elapsed | 31 秒，失敗 | 34 秒，成功 |

各列不能相加當成總成本。foreground 包含 I/O，worker 與 job 時間也可能重疊。首尾時間之間有未歸因間隔。

兩段工作的 task、authorization、head、session 與工作量不同。後段只修正已定位的 CI 故障，並非從相同起始狀態再做一次完整任務。因此 `1783→397` 不能證明加速。token 差異也不能歸因於 mode 或架構改善。

報告把 startup、publication、landing、cleanup 與 telemetry 的完整成本保留為 unknown。這表示成本記錄不完整，不表示那些動作沒有執行。歷史 owner 也早於目前六區塊與 poteto-mode 整合變更，不能替新指令證明載入、委派或交付行為。

## 最短路徑需要的資料

現有 Manager 能檢查證據身分、保留未知及投影原 owner 的下一步。它們不會從一條成功 trace 推導出全域最短路徑。本輪沒有新增 shortest-path gate、scheduler 或比較分數。

要比較一個有界方案集合，資料至少需要同一 required outcome、起始狀態、停止點、必要 controls 與成本目標。每條入選路徑都必須完成合法交付。若主張含恢復，還需指定故障邊界及其實際觀察。最後才能比較完整成本，或提出涵蓋允許路徑的必要步驟下界。

目前沒有這樣的可比成功路徑，也缺完整成本。`evidence-assessment.json` 將歷史交付標為 scoped support，將新 mode 整合標為 unknown，將全域最短標為 not established。這是 N-class 證據結論，不是新的產品狀態或效應授權。

本輪已消費 Test Manager 要求的原 owner readback，並保留 Schema Manager 的終態投影。沒有把缺少效率證據轉成新測試需求，也沒有重播已完成的交付。
