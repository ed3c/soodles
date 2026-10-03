# #234 supervisor handoff

本輪 contract 已補足 stage-outcome consumer／activation 範圍。
外部 launcher 現在提供固定來源的 outcome 與 feedback reader。
原 candidate entry、task 和 instruction pins 保留。普通 writer 仍用原入口。
本工程未操作 live #229／#232，也未更新其 authorization、checkpoint 或 candidate。

保存原 authorization、session、task、contract 和 correction history。
本 writer 只回報本工程 stage。Publication、exact-head CI、landing 和本機 reconciliation
仍由現有 owner 接續。不要從這份說明重建 live effect argv。

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

新 LIFECYCLE_FILES 加入 stage_outcome.py。
新 BUNDLE_PATHS 加入 stage_outcome.py、schema_manager.py、system_context.py 和 test_manager.py。
Supervisor 必須固定整份新 closure。舊 owner 保留其原 literal closure。
Resume positional argv 和 issue-atom／stage-outcome shell wrapper 未改。
新 external launcher 接受 `stage-outcome` 並轉交既有 outcome／feedback 參數。
原 repair source closure 從原 Git bytes 解析，不套用新 closure 清單。

Supervisor 本次已選定的 fixture binary 為
`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/noodle-recovery`。
SHA-256 為 `9fdbafc13715ee17a4142c7464350a21d74fdb4e62ef806de2905509748237ef`。
Source head 為 `b372773b0baa5c33fad87b40591dd67c45e124fc`。
這個選擇只授權 disposable fixture。工程交付後，supervisor 仍需選定 live activation bytes。

## 接入證據與後續交付

Control ack reentry、普通 worker／scope resume、原 repair closure 和 outcome controls 已通過。
原生 `--native-adapter` fixture 經 generated provider adapter 啟動 sentinel。
Sentinel 保留 dirty/untracked candidate，合法修改 tracked 檔案，再寫入同 session completed event。
它保留原 candidate stage-outcome bytes。沒有啟動 Codex 模型或 live provider 操作。

此 fixture 的 daemon 在清理時回傳 1。SIGTERM 與 backlog.done 發生競爭。
Process readback 確認 daemon 與 sentinel 均不存在。這是接入控制，不是完整 daemon 終態。
Fixture 的 provider 是本機 readback。它沒有執行完整 issue-atom resume/run、schema-3
feedback、publication 或 landing。各 Python controls 和本 writer feedback 分別覆蓋其邊界。

Supervisor 後續先以選定的新 immutable lifecycle 消費原 #232 postwrite continuation，
核對原 implicit repair binding 和非零 ledger，完成原本機收尾。
然後從原 #229 的目前 owner readback 選定 descriptor、新 Noodle bytepin 和 lifecycle closure。
原 process 的 PID/argv/readback 使用原 carrier；新 process 和後續收尾使用有效投影。
Resume 只採用 selection，回傳同一原 authorization 的 run continuation。
Supervisor 必須原樣消費該 continuation。Prepare/start/control 結果未知時，只做原 owner readback。

原 #229 的 publication、acceptance、landing、cleanup 與正常使用 readback 均仍未完成。
工程 source、fixture 或本工程落地不能取代這些結果。
本工程目前 feedback 與 stage outcome 的精確結果見 results.md 和原 Noodle session event log。
