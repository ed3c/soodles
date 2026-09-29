# 實際量測修正與新版 baseline

這份更新取代 audit.md 中「尚未有真模型 capture」的時點狀態；保留原文以供追溯。

- Error analysis：歷史問題是 Local Session 將可自行準備的 authorization 路徑／SHA 交回人。Source 顯示 root AGENTS 缺 pre-selection 入口，而既有 issue-atom skill 和 authorize 已提供它。v01 B 真 trace 另暴露把 shell issue-atom 用 Python 啟動而失敗。這些不是每次必然發生；v02 baseline 五次全通過。
- Evaluator design：v01 不接受同 owner 的 soodles.py atom 入口，誤判 C；另 analysis 將 baseline B/C 歷史失敗當成全面禁比，違反事先 protocol。boundaries/v01/closure.json 已結束該比較，原 raw/results 不改。R02 的 31 oracle controls 和 8 aggregation controls 通過，v02 用全新五次 baseline，沒有回收舊分數。
- Judge validation：此次是 receipt/identity/state/side-effect 的 code oracle；無 LLM judge，也無人類 labels。TPR/TNR 和 judge train/dev/test 不適用。Optimizer 的分組與未見 confirmation 仍必須遵守。
- Human review：supervisor 讀實際 action、raw CLI、state/artifact 與 oracle controls。沒有把 Agent 自述當 ground truth，也沒有用模型冒充 domain expert 人標。
- Data：selection 為一個 A group 三次重複，B/C 各一個 group；不是五個獨立生產樣本。v02 A 為 11/13/12 完成命令，中位數 12。小樣本不支持全域 failure-rate 或未來永不退化。
- Pipeline hygiene：真 Noodle/Codex carrier 每次有外部 stdout/stderr capture、exit/EOF receipt、實際私有檔拒讀、typed outcome、PID/group 結束與自有資源 cleanup。Optimizer 採同樣 isolation 邊界；待實跑確認其產物。完整 OS/IPC 活動與 provider-resolved model snapshot 仍 unknown。

改善尚未成立：下一步是 bounded rounds，再固定 winner、執行未見 confirmation。任何 decision 都不授權 landing。
