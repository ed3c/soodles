# 原 owner 的後續工作

本工程 writer 屬於 ed3c/soodles#237。
Order 為 `soodles-237-92e049f919db`。
Carrier 是原 Noodle 管理的本機 isolated worktree。
Admission base 是 `5e2cd1b0f11de685dab26c5370c566b508062857`。
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

## Candidate admission 的已知缺口

原 contract 把 `contracts/system-v1/issue-atom.md` 同時列為 required path 與 frozen base reference。
使用者明確要求保留原 bytes。
現有 `issue_admission.validate_delivery_paths` 只把 changed paths 傳給 evidence validator。
`validate_candidate_evidence` 則要求每個 required path 都出現在該清單。
因此未修改的 reference 會觸發 `candidate.missing_required_paths`。

本工程保留原文件。新增空白或改寫文件不能修正 validator 對 required reference 的錯誤假設。
`issue_admission.py` 不在本次 write paths。
原 admission owner 必須處理這個範圍缺口，並保留原 task、candidate、judge 與修正歷史。
本 writer 不自行更改 envelope，也不繞過 candidate validation。
