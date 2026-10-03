# 跨 repository 交付

Supervisor 在 initial authorization 前選定 target。新的 selection 使用
`target_binding: {path, sha256}`，指向 control root 外的固定 JSON bytes。
Binding 的 schema 1 包含 `repository`、`base_ref`、`workflow_path`、`jobs` 與
`verification`。`jobs` 對應 provider job 名称與必要 step 名称。
`verification` 包含 scope `owner`、覆蓋的 `paths` 與 target `commands` argv。

沒有 `target_binding` 的既有 authorization 繼續使用 `repository_binding.PROFILES`。
不要加入新的 source profile，也不要用缺少 reference 來選擇 legacy route。
Supervisor 必須在 admission 前選好格式。Writer 不改自己的 authority。

## 消費同一份 binding

1. 讀取原 supervisor 的 selection 與 immutable lifecycle owner。
   使用 [admission recipe](local-supervisor-admission.md) 的 producer。
   Target 不需要 `issue-atom`、`soodles.py`、`stage-outcome` 或 Soodles tests。
2. 原 atom 的 `next.argv` 與 `next.environment` 選定外部 runtime。
   Admission 將同一 binding reference 帶入 envelope、readiness 與 landing claim。
   Worker 使用 stage prompt 的 `runtime.stage_outcome_argv` 與 `runtime.test_argv`。
   Schedule 使用已提供的 `SOODLES_ADMISSION_LAUNCHER`，參數為 `inspect`。
3. Test Manager 驗證 target 自己選定的 scope。缺少 path 覆蓋時，取得具名 scope owner input。
   不要改跑 Soodles tests 或 full suite。
4. Publication 核對原 Noodle claim、target origin、base 與 candidate。
   Exact-head acceptance 核對完整 selected jobs、steps、run attempt 與 head。
   Landing 保留原 provider effect 與 checkpoint。未知寫入只要求原 owner readback。
5. Local reconciliation fetch 同一 `base_ref`，核對 merge、closure、provider branch、
   原 Noodle order 與 worktree cleanup。Resolved 後才由既有 next-Issue owner 消費下一個候選。
   Readback 使用 [provider-readback](../../provider-readback/SKILL.md) 與 owner 回傳的 bindings。

目前 Noodle carrier 的 publication claim 與 cleanup 使用 `origin/HEAD`。
因此 initial admission 要求 binding 的 `base_ref` 等於該 carrier 的 integration branch。
兩個 target 可以各自使用 `trunk` 與 `stable`。任意非 default branch 不在此支援範圍。
不符合時，owner 在啟動 writer 前拒絕。不要改寫 Noodle claim 或 origin/HEAD 來通過。

## 保留原本的 authority

Supervisor 分別固定 lifecycle runtime 與 landing publisher 的完整檔案集合及 digest。
這兩個來源都在 target 外。Lifecycle runtime 不因 target 的 candidate 變更而更新。
必要 dependency 缺失或 bytes 改變時，停止相依操作並保留原 continuation。
其他 CLI 的 packet 或額外 physical verification 不屬於這份 lifecycle closure。

依賴的 producer revision、Issue、PR、base、tree、merge 與必要 jobs 仍由原外部 claim 指定。
Generic dependency edge 使用自己的 `target_binding` reference。Legacy edge 保留原格式。
`landing.next.requests` 回傳全部 `dependency_N_*` GET。不要從 Issue closure 推論 edge 已成立。
缺少第三個 repository 的 binding 是 supervisor input，不能由 Agent 猜 profile。

## 可重建的證據與限制

[設計](../../../../docs/experiments/cross-repo-factory/design.md) 記錄方案與 runtime 行為。
[結果](../../../../docs/experiments/cross-repo-factory/results.md) 記錄 source、命令與 fixture 範圍。
Fixture 的 provider、carrier 與 target 都是測試輸入。Factory fixture 通過不代表真實 target 已交付。
文章與 manifest 記錄可核對的資料，但不能證明 Agent 已遵守指引。
P-class 結果仍須使用 saved-byte feedback，並由原 session 消費 Schema Manager next。
原 supervisor 在 factory 交付後，仍須以獨立 target admission 取得正常生產、replay 與並行證據。
