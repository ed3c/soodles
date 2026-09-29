# 一個因果修正

既有 admission 已以 running/proposal_pending 表示合法等待。隨後 claim 的非零退出沒有可證明的 retryable 語义，卻被 caller 統一當成 pending，造成 drive 重試。

沿用 AtomRefusal 的 input continuation，明列 Noodle、control root/order/subject、fresh_noodle_claim；保留現有 process capture 與 execution checkpoint。這移除錯誤轉移，不增加狀態、scheduler、retry flag 或 authority。

外部oracle先凍結，53個既有/新增issue-atom控制通過。定義與跨process/consumer實證見後續results，不預設Agent改善。
