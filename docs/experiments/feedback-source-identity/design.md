# 已註冊 worktree 的 feedback coverage

本文件記錄 #253 的局部來源判斷修正。它是 N-class 說明，不授予 publication 或 landing 權限。

## 原推論與證據

`require_feedback_completion` 原先只比較 instruction 的絕對路徑。
它的前提是 checkout 位置相同才代表同一份指引。
同一 Git repository 的 worktree 可以位於不同位置。此前提不足以判定 coverage。

原 #229 的四個觀測已取得 `SUPPORTED`、`VALID`、`PASS`。
提供的 `context.json` 記錄 13 個指引的原路徑、目前路徑與相同摘要。
原 completion 讀回仍以 `worker.feedback.coverage` 拒絕這 13 個路徑。
這些證據支持修正來源判斷。它們不要求模型重新回答原 cases。

相同 bytes 也不足以證明同源。
不同 repository 可以包含相同內容。不同相對路徑也可以包含同名檔案。
因此，搬移 coverage 必須同時保有 repository 身分、已註冊 worktree、相對路徑與目前 bytes。

## 既有 owner 與資料流

`stage_outcome.report` 先讀取 admission 與 Noodle session。
`worker_context` 核對目前 worktree、branch、origin 與 Git common directory。
Git common directory 是同一 repository 的 worktree 共用的 Git 資料目錄。
這是本機 repository 身分，不是 remote URL 或 commit SHA。

`feedback` 入口檢查 protocol 的 task 與 contract 等於 admission。
completion 重新讀取最後一筆 feedback selection。
`schema_manager.pclass_feedback` 檢查原 protocol、criteria、instruction、input、report 與 trace。
completion 要求 criteria 為 `SUPPORTED`、證據為 `VALID`、behavior 為 `PASS`。
completion 也要求目前 feedback identity 等於原 event identity。
只有這些檢查通過後，completion 才比較目前 changed P-class paths 的 coverage。

`stage_outcome.registered_worktree` 已使用 common directory 與 registration 檢查。
`issue_execution.validate_worktree` 使用相同的 Git 身分查詢。
`landing` 也會比較 control 與 worktree 的 common directory。
這次沿用這些本機 Git 慣例。Schema Manager 繼續驗證原觀測。

## 設計選擇與 runtime

獨立設計 A 使用 `(common directory, relative path, SHA-256)` 集合。
獨立設計 B 先建立 registered-root 索引，再把來源路徑投影到目前 worktree。
兩者都能保留原 evidence 身分。
本修正採 A，因為單一私有函式即可完成比較。
B 的最深前綴索引與快取沒有必要。
程式直接查詢 Git 所屬 root，不用前綴選出 root。
獨立評審也選 A，並建議採 B 的 NUL 分隔 registration 解析。

`_relocated_feedback_coverage(root, instructions, changed)` 回傳額外涵蓋的路徑集合。
caller 只在原絕對路徑 coverage 不足時呼叫它。
helper 先讀目前 repository 的 common directory 與 worktree registration。
`git worktree list --porcelain -z` 以 NUL 分隔欄位，避免把路徑中的換行誤讀成記錄。

helper 解析 source 的實體路徑，再從檔案父目錄查詢 Git top-level。
source 的 top-level 必須在 registration 中，且 common directory 必須相同。
helper 以該 root 計算 source 的相對路徑，並搭配已驗證的 reference 摘要。
target 的實體路徑必須仍在目前 root 內，且真正的 Git top-level 必須等於目前 root。
helper 讀 target bytes，計算摘要，再比對完整 tuple。
只有完整 tuple 相等的 changed path 才加入 coverage。

helper 不寫檔，也不建立持久狀態。
當所有 changed paths 都有 coverage 時，既有 owner 才可繼續寫 completion event。
Git 操作失敗會回傳 `worker.feedback.git`，並保留 stderr 或例外原因。
目前檔案讀取失敗會回傳 `worker.feedback.instruction`。
一般身分不符則不提供 coverage，交由既有 coverage refusal 列出未涵蓋檔案。

## 接受與拒絕邊界

原本相同絕對路徑的 coverage 保持原樣。
跨路徑 coverage 只適用於同一 Git repository 的已註冊 worktree。
來源與目前檔案必須使用相同 repository-relative path。
目前 bytes 的 SHA-256 必須等於已驗證 instruction reference 的摘要。
worktree 的 branch 可以不同。

Git 必須回報檔案真正所屬的 worktree root。
目錄前綴相同不代表同源。
已註冊 root 內的巢狀 foreign repository 不能沿用外層 root 身分。
複製 `.git` 指標也不會建立 worktree registration。

缺少 coverage 時，completion 仍回傳 `worker.feedback.coverage`。
原 instruction 遺失、report 被改寫或 input 身分不符時，原驗證先拒絕。
拒絕不會寫入 completed event。
所有觀測仍指向原路徑。程式不會改寫 protocol、report 或 trace。

## 限制與後續 owner

原始 instruction 與證據仍須可讀且符合摘要。
本修正不復原已刪除的 worktree，也不建立跨 clone 的 evidence alias。
路徑比較沿用既有 `Path.resolve()` 語意。
這不是檔案與 Git metadata 的原子快照，也不宣稱排除同步修改。
它驗證本機 coverage discriminator，不建立新的 Agent 行為或改善主張。
原 evidence 的 capture 完整性與 observer 獨立性限制仍然存在。

Writer 的完成範圍是 source、必要 controls、說明、manifest 與乾淨提交。
原 parent owner 仍負責精確 PR CI、landing 與 local reconciliation。
parent 之後才沿 #229 原 continuation 取得實際 completion 與交付讀回。
#229、#239、#245、#247 與 medium／Production 成果仍未由本文件證明完成。
