# 已接納 backlog 的固定投影

本次修正屬於 `ed3c/soodles#232`。
基準是 `192f772923213f4d9be7e7886b589b502f6f5af6`。
Noodle 保留原 order、session 與 worktree。
Soodles supervisor admission producer 只修正它產生的 backlog adapter。

## 問題與必要條件

原任務提供的 normal stderr 診斷指出，#229 的 backlog sync GET 收到 401 後，Noodle loop 退出。
本 writer 沒有重新讀取 #229 的憑證，也沒有重演 live provider failure。
本次可直接觀察的 source 證據是 `supervisor_admission._entry_text`。
基準實作讓 `sync` 與 exact-order `done` 共用 `fetch_issue`。
因此 sync 在投影固定 order 與 task 之前，必須先取得 provider 回應。
本次 disposable subprocess 也重現無 token 與 401 的拒絕。
這些 fixture 結果證明 adapter 的依賴，不證明 #229 daemon 的全部退出流程。

原實作隱含的前提是，backlog 每次更新都需要目前 Issue 狀態。
但本 admission 只允許一個已固定的 repository、Issue、order 與 task。
Noodle 的 sync consumer 需要該項資料，不負責重新接納或判定完成。
worker 與 admission 已有自己的 fresh provider 驗證。
`done` 也必須在它自己的邊界確認完成。
因此每次 sync 的 GET 不是這項固定投影的必要輸入。

延長 token 只能延後相同故障。
快取 provider 回應會增加到期與來源判定，仍容易把舊狀態稱為目前狀態。
直接投影已驗證 envelope 符合同一需求，也不需要新 credential service。
這個選擇只移除 backlog 輪詢的 provider 依賴。
它不修復其他需要長期 fresh provider access 的操作。

## 執行與資料形狀

producer 保持既有 bundle 生成與 pin 機制。
產生的 adapter 每次先核對 runtime 與 envelope 的原始 SHA-256。
它再呼叫 `load_external_envelope` 驗證已接納資料。
若原始 bytes 改變，adapter 在輸出 backlog 前拒絕。

對 `sync`，adapter 回傳一行 JSON。
`id` 與 `title` 都使用原 order。
`plan` 使用原 task。
`repository` 與 `issue` 使用 envelope 的固定身分。
`source` 固定為 `admission_snapshot`。
它不輸出 provider `status`，也不呼叫 transport。
這項輸出不修改 provider 或建立新 order。

Noodle 的 source 契約來自 runtime lock 指定的
`391f3154c680fc6724b8cdabf6bcec831b61065d`。
`adapter/sync.go` 要求非空 `id` 與 `title`，所以不能省略 title。
`adapter/types.go` 將 `status` 定義為選填欄位，並保留其他 JSON 欄位。
`mise/builder.go` 只排除 `status == "done"` 的項目。
因此 order title 與省略 status 符合這個 consumer 的資料形狀。
這是 pinned source 追蹤，不是新 bundle 的正常使用觀察。

## 接受、拒絕與未知

當原 hashes 與 envelope 驗證通過時，sync 必須輸出同一 admitted identity。
無 token 或 poll 期間 token 失效都不改變這個結果。
Issue 後來 closed 或 body 改變時，sync 仍投影原 admission。
成功的 snapshot 不提供目前 open、closed 或 completed 的證據。

對 exact-order `done`，adapter 仍 fresh GET Issue。
`validate_issue` 仍要求原身分、body 與有效的 `closed/completed`。
仍 open、非 completed closure、401、wrong Issue 或改動 body 都拒絕。
worker 與 admission 仍 fresh GET，並拒絕不符合 open-Issue admission 的讀回。
`add`、`edit` 與 foreign-order `done` 仍拒絕。
既有 `done schedule` 是排程控制 no-op，不是另一個 Issue order 的完成操作。
本次不改這個既有分支。

本次測試在 nearest generated-adapter subprocess 觀察這些界線。
Test Manager 選 `test_supervisor_admission`，並選實際 import fixture 的
`test_instruction_context`。
本次沒有改變通用檔案級 mapping，也沒有執行 full suite 或 Noodle daemon。
recipe 的文字行為另由已綁定 saved bytes 的 native consumer 觀察與 Schema Manager 回饋驗證。
這兩種證據回答不同問題，不能互相替代。

## 後續 owner 與 activation

writer 交付 source、focused controls、recipe、證據與 commit。
原 publication owner 處理候選發布。
原 owners 接續 exact-head CI、landing 與本 Issue 的 Git/Noodle reconciliation。
後續新 admission 必須實際讀取修正 bundle，才有 activation 證據。
候選 commit 不會替換既有 session 的 immutable bundle。
#229 的恢復、Noodle#101 與跨 repo 正常使用仍是未完成的總需求。
它們由各自 owner 處理。本次沒有修改、啟動或宣稱恢復 #229。
