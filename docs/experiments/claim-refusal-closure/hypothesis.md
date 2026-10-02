# 一個因果修正

既有 admission 已以 running/proposal_pending 表示合法等待。後續 claim 的非零退出沒有可證明的 retryable 語義。caller 卻一律回傳 pending，導致 drive 重試。

沿用 AtomRefusal 的 input continuation，明列 Noodle、control root/order/subject、fresh_noodle_claim；保留現有 process capture 與 execution checkpoint。這移除錯誤轉移，不增加狀態、scheduler、retry flag 或 authority。

外部 oracle 在修正前固定。53 個既有及新增的 issue-atom 控制通過。後續 results 記錄定義及跨 process/consumer 的實證。這些結果不預設 Agent 行為改善。
