# 原 owner 的後續工作

本工程 writer 屬於 ed3c/soodles#237。
Order 為 `soodles-237-92e049f919db`。
Carrier 是原 Noodle 管理的本機 isolated worktree。
原 admission base 是 `5e2cd1b0f11de685dab26c5370c566b508062857`。
Criteria correction 選定的目前 base 是 `a2e6f36bdffa893c6d9d31ad31b4880551634d80`。
本候選以 merge 保留原提交 `8f3b3a6d53b951cc4d4cb1eb22cd044eec256f25`。
本階段只交付 source、必要 controls、原來源 identity 證據與這份 handoff。

Publication owner 接收原 stage outcome 與 candidate。
既有 CI 驗證 exact candidate head。
Landing 與本機 reconciliation 仍屬於原 owners。
本紀錄不選擇新的 judge，也不替任何 owner 組合 effect command。

原 #232 的後續 activation 尚未執行。
Supervisor 從已接受的工程 source 固定新 runtime 後，才由既有 owner 接續原 resume 與 run。
原拒絕保留在 `backlog-resume-accepted/stdout.txt`。
原 authorization 保留在
`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/backlog-prepared/authorization.json`。
原 checkpoint 是同路徑的 `authorization.json.state.json`。
這些路徑是原證據身份，不是重播歷史 command 的授權。
Supervisor 仍須讀取 owner 當下返回的 continuation。

原 host record 的 sequence 是 4，且 `stop_offered=true`。
下一個 owner 必須取得原 process 的 readback，才能判定 stop 是否完成。
本工程的只讀檢查不提供該 readback，不授權重送 stop 或 restore。

原 #229 與跨 repository 的整體要求仍為 pending。
#237 的 writer completed 或後續 resolved 都不能替代那些結果。

## Criteria correction 與保留的失敗歷史

前一輪回報把 `candidate.missing_required_paths` 歸因於 validator 的錯誤假設。
該推論的前提是 required path 可以只作為未修改的 reference。
實際 validator 要求 required path 出現在 net diff 中。
原任務卻明確要求 contract reference 不變。
因此錯誤是 supervisor 的選項，不是 validator 對該選項的拒絕。
原 commit、stage failure 與 `/tmp/soodles-237-ohkgmap9/candidate-refusal.json` 保留前一輪證據。

Supervisor 的 `criteria-237-context.json` 修正這個前提。
修訂從 required paths 移除未修改的 contract，並把實際修改的 `issue_atom.py` 固定到指定 base。
新 envelope SHA-256 是 `349ca5c6f5d24acc9c4d8dda810b0a8c2dc51fe2b175e4025c3c1eb0a5711c82`。
原 instruction source 仍是 `5e2cd1b0f11de685dab26c5370c566b508062857`。
本候選沒有修改 validator，也沒有為了通過驗收製造 P-class diff。
Manifest 的既有 `instructions` 欄位現在記錄 `issue_atom.py` 的 baseline 與 treatment hashes。
這是 source bytes 的驗證資料，不是新增 Agent 指令或行為改善證據。

本 writer 使用外部 `SOODLES_ADMISSION_LAUNCHER` 的 stage-outcome entry。
Publication、exact-head CI、landing 與 reconciliation 仍由原 owners 接續。
原 #232 activation 與 #229 整體結果仍未完成。
