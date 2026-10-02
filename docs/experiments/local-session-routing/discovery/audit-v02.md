# 實際量測修正與新版 baseline

這份更新取代 audit.md 中「尚未有真模型 capture」的時點狀態；保留原文以供追溯。

- Error analysis：歷史問題是 Local Session 要求人提供本可自行準備的 authorization 路徑／SHA。Source 顯示 root AGENTS 缺少 pre-selection 入口，但既有 issue-atom skill 和 authorize 已提供這個入口。v01 B 的真實 trace 另顯示 consumer 用 Python 啟動 shell issue-atom，因而失敗。這些失敗並非每次都發生。v02 baseline 五次全通過。
- Evaluator design：v01 不接受同 owner 的 soodles.py atom 入口，因而誤判 C。analysis 也將 baseline B/C 的歷史失敗解讀為全面禁止比較，違反事先 protocol。boundaries/v01/closure.json 已結束該比較，原 raw/results 不變。R02 的 31 oracle controls 和 8 aggregation controls 通過。v02 使用全新五次 baseline，沒有沿用舊分數。
- Judge validation：此次 code oracle 檢查 receipt/identity/state/side-effect，沒有使用 LLM judge 或人類 labels。TPR/TNR 和 judge train/dev/test 不適用。Optimizer 仍須遵守分組與未見 confirmation 的限制。
- Human review：supervisor 讀實際 action、raw CLI、state/artifact 與 oracle controls。沒有把 Agent 自述當 ground truth，也沒有用模型冒充 domain expert 人標。
- Data：selection 為一個 A group 三次重複，B/C 各一個 group；不是五個獨立生產樣本。v02 A 為 11/13/12 完成命令，中位數 12。小樣本不支持全域 failure-rate 或未來永不退化。
- Pipeline hygiene：每次真 Noodle/Codex 執行都有外部 stdout/stderr capture 與 exit/EOF receipt。紀錄也包含實際私有檔拒讀、typed outcome、PID/group 結束與自有資源 cleanup。Optimizer 使用相同 isolation 邊界，其產物仍待實際執行確認。完整 OS/IPC 活動與 provider-resolved model snapshot 仍 unknown。

當時尚未證明改善。下一步是執行 bounded rounds，再固定 winner，最後執行未見 confirmation。任何 decision 都不授權 landing。
