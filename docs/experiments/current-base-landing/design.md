# Local landing 的目前 base

本文件記錄 ed3c/soodles#256 的 source 整合設計。它是 N-class 說明，不授予 publication 或 landing 權限。

## 問題與證據

原判斷要求未合併 PR 的 `base.sha`、目前 branch SHA 與 admitted base 全部相同。
這個判斷假設 PR 內嵌的 base commit 會同步反映 branch tip。

既有 #229 provider snapshot 反駁了這個假設。
Branch 與 native claim 的 base 都是 `3ef2436e9cd824144cd3ffe5bd4a0152eb5283f1`。
PR #244 的 head 是 `b9d3e03c78d87732c63e343504687312efee0b67`。
Exact-head run `37137498698` 已成功。
PR 的 `base.ref` 是 `main`，但內嵌 `base.sha` 仍是 `5b0a73eae31fb414deeed4ffdf8082a71aee4e3d`。
舊 landing owner 因 `base.head` 拒絕，當時尚未建立 checkpoint 或 offer write。

這份 snapshot 支持移除 local route 的額外 SHA 相等要求。
它沒有證明 GitHub 所有 PR metadata 的更新規律。
本次 writer 重用已保存的 criterion review 與 source review，沒有再次操作 #229。
證據位置與識別值記錄在 [results.md](results.md)。

## 修正與選擇理由

本次從 accepted generic factory `2fdc87afdb21d1512dab67da93bfea41939dc530` 合併外部 source `d5cf7f7585f7eb76b4538827e4f389b5cad26dc1`。
Merge 保留兩邊歷史。
它也保留先前 `351224b24054e11887edd5ba2de19f199845cb7c` 的 cloud 範圍錯誤及後續修正。

Local route 已有固定的 native publication claim。
因此 `landing_supervisor._derive_claim` 可以從 fresh branch readback 讀取 base，再要求該值等於 native claim 的 base。
Cloud route 沒有這份 native pin。
因此 cloud producer 仍從 PR `base.sha` 建立 claim，並要求 branch SHA 相同。
將 local 推論套用到 cloud，會把真正的 branch drift 當成新的 base admission。

資料仍使用既有 route、claim、target binding 與 checkpoint。
修正只改變 base 值的來源與兩個消費端的比較。
這符合 Laziness Protocol。移除錯誤比較即可，不需要增加 schema、provider request 或 scheduler。
只改 `landing.start` 不足以修正問題，因為 producer 與後續 `observe_base` 也消費相同的錯誤前提。

## Runtime 行為

Supervisor producer 接收 provider snapshot、固定的 publisher descriptor 與 route。
Local route 另含 control root、execution envelope reference 及 native publication claim reference。
Generic route 保留外部 `target_binding`，由原 `repository_binding.selected` 驗證 repository、base ref 與 CI 設定。

Producer 先檢查 snapshot 的 Issue、PR、head、tree、run 與 jobs。
Local producer 檢查 native claim 的 digest、repository、head、tree、base 及 worktree 身分。
它將 execution envelope reference 傳給原 publisher。
Publisher 的 `landing.start` 再驗證 envelope、target repository/ref、candidate 與 CI。
Branch SHA 必須等於 admitted claim 的 base。
檢查通過後，owner 才建立 `admitted` checkpoint。
Producer 保存原 snapshot 資料，不改寫 PR 的歷史 SHA。

`landing.advance` 與 `landing.dispatch` 透過 `observe_base` 比較目前 branch 與 admitted base。
相等時，它們繼續原身分與 CI 檢查。
不同時，它們使用原 comparison 與 readmission 流程。
修正沒有自動承認新的 base。

`advance` 準備 intent。
`dispatch` 在 fresh readback 通過後，先持久化已 offer 的狀態，再返回一次 provider request。
Landing owner 本身不發送 provider write。
已 offer 但結果未知的 write 仍需原 owner readback，不會因歷史 PR SHA 而重送。
Merged parents/tree、Issue closure 與 local reconciliation 檢查保持原樣。

## 接受、拒絕與未知

Local positive case 具有相同的 native、admitted 與 branch base，但 PR 內嵌 base 是歷史值。
只有其他 target、candidate、envelope 與 CI 條件也通過，owner 才接受它。
Generic integration control 必須同時保留 target binding 與這個歷史值。

錯 repository、ref、native base、head、tree、run 或必要 CI step 仍須拒絕。
Cloud producer 遇到 PR base 與 branch 不同時仍須拒絕。
真正 branch drift 需要原 comparison 或 readmission 證據。
缺少證據不代表可以重選 authority。

本次 fixture 結果只驗證選定的 source 行為。
它不證明本 Issue 的 exact-head Linux CI、merge、closure 或 Git/Noodle reconciliation 已完成。
這些效果由原 publication 與 landing owners 接續。
本次 writer 不修改外部 frozen publisher、舊 authorization、raw provider evidence 或 medium target。
