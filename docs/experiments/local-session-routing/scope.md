# 目前唯一 atom：Local Session 進入既有 authorization owner 的路由

使用者最新限制：pstack／evals 只評 Soodles system design 與 hill climb；不在 Soodles 建通用 eval engine。

根據 `discovery/owner-boundary-review.md`，選定最小原因：根 `AGENTS.md` 已列 cloud 和 already-admitted local child，卻漏掉已獲使用者授權、authorization 尚未選定的 Local Session。正確 owner／CLI 已存在於 `issue-atom` skill 和 `supervisor-admission authorize`，需要讓根入口直接可達。

此前 `design-a.md`／`design-b.md`／`synthesis.md` 的產品 `eval experiment` 方案只保留為未實作的設計歷史，不能據此新增產品 command/schema。`discovery/reproduction.json` 的 recovery family 誤用重現不是此次產品 defect，也不是實際 Agent baseline。

## 有界承諾

| 狀態 | 正確 owner 與操作 | 必須保留的反例 |
| --- | --- | --- |
| 已授權 Local Session；authorization 尚未選出；選定 task/host inputs 齊備 | Session 擔任外部 supervisor，走既有 `supervisor-admission authorize`；保留 prepared receipt 與原樣 next | 不叫人手算 hash 或製作 Session 能推導的 authorization；不越過本次指定效果範圍 |
| authorization 已選定，但該 exact file 不可讀 | 既有 `issue-atom run` 回 exact owner recovery；恢復原檔案後才續行 | 不產生替代 authorization，不換 Issue、judge 或 digest |
| authorization 可讀，但 host provider capability 缺失 | 既有 lifecycle 回 host capability owner 的 typed refusal | 不猜 credentials、不更換 carrier/identity、不因使用者授權就假造可用能力 |

根入口／P-class 是實際修改候選，CLI 是受 regression gates 保護的既有 executable path。若 source review 及重現沒有 CLI bug，就不修改 CLI code，也不把 P-only 結果宣稱為 combined code improvement。

## 外部實驗與持續閉環

使用 pstack How／Architect 做 source/owner grounding，pstack Hillclimb 做一輪一假設與 keep/revert，evals-start 導向 eval-audit 檢查量測可信度；客觀 oracle 判實際 receipts、檔案／狀態與捕捉到的 actions。方法路由和 pins 留在 recipe／protocol，執行交回 Noodle。

正式 protocol 尚待 factory 與 oracle controls 驗證後固定。之後才開始 fresh baseline、optimizer 與 confirmation。Host smoke 只證明所需能力，不計入行為改善樣本。實際 score、budget、stop rule 在 baseline 前固定；不能用本文件預先宣告有改善。

產物以外部原始記錄、既有 feature recipe、可持續重跑 controls 及同一新 Issue/PR 的 terminal evidence 延續；不依賴舊對話記憶。範圍是所選三種 Local 狀態與可觀測 carrier，不能宣稱所有未來 Agent 永不退化、完整 feature-map maintenance 或未知 provider model snapshot 已固定。
