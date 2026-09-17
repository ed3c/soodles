# #39 獨立 setup 審查

審查時間：2026-09-17T08:59:53.591655+00:00。本報告只確認 setup bytes 與證據邊界，不是行為通過或 landing 授權。

## 已直接核對

- 8 個 committed fixture trees 都以 `1ff2882891792b50d97529c9ee1a3e76eac1a6e7` 為共同 code。Baseline 只替換 neutral execute；treatment 只額外替換已選定的五份指引。每份指引 digest 均匹配 instruction-selection.json；基準缺少 design 文件也被核對。
- neutral execute 8 組相同，SHA256 `ae6eeb8a66c7672ae0f6a3f159137923f43aa1ecac4314158081bff7f4328cf3`；installed manifest 與 envelope digest 逐一一致。各對 task bytes 相同，初始 task-input 只差 assigned_instruction_ref；五種共同原始 fixture bytes 相同。
- 7 份 active judge/recorder/test 檔直接與 `88d38bfd7984a52298a7d8bb6501e1be12e2652b:docs/experiments/agent-context/local/` 比對，全部相同；各 SHA256 見 setup-review.json 的 judge。已有 observer log 記錄 14 tests OK；本 reviewer 未重新執行。
- 8 組 envelope 綁同一實測 Noodle SHA256 `5657c8c3dcaa2491d290a35995c35e4c3d46993955b151f3c75e3bac94476aff` 與 Codex SHA256 `b973d440acac501fd2594a43e7ca9ce41e0a65b9dfb28d0d7a7837c99e1261e3`，本次直接重算亦一致。requested model 都是 gpt-6-astra/high；實際 model 仍待 raw turn 證據。
- pending fixture 保留 merge_pending、delivery.status=offered、writes_offered=[merge]；identity 與 checkpoint verifier 相同。historical-seed 的舊 merge request 非 null，清楚標註歷史。

## 具體偏差與限制

- **S1 / provenance_deviation**：現行 Issue active §7 指定 PR48 runtime 35200315530；實際 supplied runtime 為 main run 35200528246，head 1ff288... 正好匹配共同 code。這不是指定 run 的原樣沿用。 證據：live-issue.json JSON body lines 7；fixtures/runtime-readback.json:3；fixtures/runtime-readback.json:7。
- **S2 / stale_template_metadata**：fixtures/cases.json 仍記錄歷史 code e4b4a848 / treatment f98a3384；實際 task-input 與選擇表使用本次 refs。案例模板不能被當成本次身份 SSOT。 證據：fixtures/cases.json:5；fixtures/cases.json:6；prepare_trials.py:63；instruction-selection.json。
- **S3 / scope_limit**：prospective freeze 的時間順序目前由 freeze at 與檔案 mtime 支持；檔案 mtime 不是不可變第三方時間戳。尚待完整 raw launch/turn timestamps 交叉核對。 證據：freeze-verification.json:2；run-01/live/launch.json。
- **S4 / scope_limit**：doctor 8 組皆退出 1（terminal.env）；exact repo/cwd/root predicate 8 組皆成立。不可稱 overall doctor pass。 證據：preflight.json；prepare_trials.py:89；prepare_trials.py:90。

## 後續審查邊界

完整 raw/native exports 到齊後才審核 tool completeness、實際 child exit、native thread/model、typed event、case semantics、producer/consumer freshness、cleanup 與統計。Normalized TRACE_CONSISTENT 不能單獨證明任何一項。

以上判斷的逐組資料與讀取檔案 SHA256 都存於 `setup-review.json`。工作只寫入本 independent-audit 目錄。
