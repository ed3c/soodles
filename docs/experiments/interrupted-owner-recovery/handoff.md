# #234 supervisor handoff

本工程 candidate 尚未完成。原 admission owner 必須先補足 stage-outcome
consumer／activation 範圍。建議納入 stage-outcome、stage_outcome.py 和其
必要 tests/test_stage_outcome.py、tests/test_feedback_owner.py controls。
這是缺少 scope 的具體 consumer，不是要求重做 authorize 或改選原 judge。
修正路徑必須讓保留的原 candidate 使用已選定的 outcome reader。
只更新新工程的 source 不會更新原 #229 worktree 的 shell entry。

保存本次原 authorization、session、task、contract 和 correction history。
使用原 lifecycle owner 回傳的 scope amendment continuation。
本 writer 不提供或重建 live #229／#232 的 resume/run argv。

## Descriptor 與原始輸入

外部 descriptor 的完整欄位如下。每個值都由 supervisor 從原 owner readback 選定。

```json
{
  "schema": 1,
  "kind": "prepublication_interruption",
  "authorization": {"path": "ORIGINAL_AUTH_ABSOLUTE_PATH", "sha256": "ORIGINAL_AUTH_DIGEST"},
  "original_envelope": {"path": "ORIGINAL_ENVELOPE_ABSOLUTE_PATH", "sha256": "ORIGINAL_ENVELOPE_DIGEST"},
  "lifecycle_owner": {"path": "SELECTED_EXTERNAL_ISSUE_ATOM", "sha256": "ENTRY_DIGEST", "source_sha256": "CLOSURE_DIGEST"},
  "carrier": {"platform": "SELECTED_PLATFORM", "noodle": {"path": "NEW_BINARY_PATH", "sha256": "NEW_BINARY_DIGEST"}, "codex": "UNCHANGED_ORIGINAL_CODEX_OBJECT"},
  "custody": "EXACT_NATIVE_CUSTODY_OBJECT",
  "custody_sha256": "EXACT_NATIVE_CUSTODY_DIGEST",
  "evidence_path": "EXACT_NATIVE_EVIDENCE_DIRECTORY"
}
```

這是欄位說明，不是可执行的 live selection。Resume 使用既有
`resume AUTH DESCRIPTOR SHA256`，回傳同一原 auth 的 run continuation。
原 admission、start、stdout/stderr 和 auth bytes 都必須保留。
原 process readback 使用原 carrier。後續 process 與 cleanup 使用投影後 carrier。
原 judge 和 unknown provider write obligations 不變。

Runtime closure 沒有新增模組。既有 LIFECYCLE_FILES 和 BUNDLE_PATHS 包含
本次修改的 producer、reader 和 worker。CLI positional argv 未改，shell wrapper 未改。
原 repair source closure 從原 Git bytes 解析，不套用新 closure 清單。

Supervisor 本次已選定的 fixture binary 為
`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/noodle-recovery`。
SHA-256 為 `9fdbafc13715ee17a4142c7464350a21d74fdb4e62ef806de2905509748237ef`。
Source head 為 `b372773b0baa5c33fad87b40591dd67c45e124fc`。
這個選擇只授權 disposable fixture。工程交付後，supervisor 仍需選定 live activation bytes。

## 後續驗證與交付

補足 scope 後，完成 control ack reentry 和完整 adapter 整合。
原生 sentinel fixture 支持 native prepare/manual/edit/release/唯一 successor。
Python 延遲 receipt control 支持 worker 初始化判別。兩者不可合稱完整恢復驗證。
P-class feedback 已消費 consume_verified_behavior，但只涵蓋三個指引判斷題。

本工程的 publication、exact-head CI、landing 和 reconciliation 仍由既有 owners 執行。
只有本工程完成後，supervisor 才依原 #232 continuation 完成本機收尾，再接入原 #229。
原 #229 的 publication、acceptance、landing、cleanup 與正常使用 readback 均仍未完成。
工程 source 或 fixture 通過不能取代這些結果。
