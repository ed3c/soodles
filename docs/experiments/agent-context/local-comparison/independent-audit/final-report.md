# Issue 39：完成三組限定比較的獨立原始證據審查

**所要求的三組限定本機比較已完成**：runner-task（run-01／02）、unknown-write（run-04／03）、fresh-transfer（run-10／09），加上原 run-05／06 兩個真正 producer。兩臂在各自限定案例均達到支持的結論；這是所測條件下無退步的證據，**沒有 treatment superiority、真正 compaction、未介入的自然退出或 landing authority 的證據**。

追加 selection 的「successful fresh doctor」措辭與實際 overall fail 有明示差異，不能宣稱所有 selection 文字均無條件滿足。實際固定 repository/cwd 契約及預先存在的執行檢查均滿足，僅 terminal.env 因 TERM=dumb、非 TTY 而 fail；它不是本次行為比較的獨立阻斷。本審查保留原文字、原失敗與此限制，不回填 selection、不製造 doctor 全綠。

本次只新寫 final-audit.json 及本報告，保留原 audit.json／report.md。未啟動模型、未執行 judge、未查詢 GitHub，未修改 repository 或原始 evidence。所有 locator 相對 `/Users/neon/.codex/experiments/soodles39-completion-20260917`。本次審的是完整本地原件；尚未核对公開遮蔽 export。

| Consumer | 真正 producer | 新 native thread | Call/result 對數 | 實際 waited child 耗時 |
| --- | --- | --- | ---: | ---: |
| run-09 | run-06 | `01a0adc5-c74d-7993-8bfd-d171be527c08` | 6 | 82.0s |
| run-10 | run-05 | `01a0adc5-c713-71c0-b6b7-efa94d95bbef` | 7 | 84.3s |

## 真正 handoff 到新 consumer 的證據鏈

**Treatment run-06 → run-09**：producer 的 inbox/handoff.json、inputs-after/handoff.json、transfer-input-receipt.json 所記 SHA 與 consumer 的 inputs-before／inbox／inputs-after 五份 retained bytes 相符，SHA-256 為 `ca2866b6826bffe998d1de2688fb39aac071dd8e99146438f84ba03690cfc3e1`。Producer native thread 為 `01a0ad6a-0def-7af0-bc1c-260544195022`，實際 waited exit 先於 transfer receipt 的 copied_at，再先於新 consumer launch；沒有重跑 producer。

run-09/native/rollout.jsonl:19 的實際讀取迴圈順序為 handoff、checkpoint、provider、identity、runtime；:24 的 exposed result 包含相同完整 handoff bytes，接著是本轮 checkpoint/provider 全文。這是同一 call 中順序讀取，不應誇大為不同 tool call。真正 owner 呼叫在後續 :34，:38 回傳 landing.advance、action=readback、phase=merge_pending、classification=null，無新 request、exit_code=0。Checkpoint/provider bytes 不變。

**Baseline run-05 → run-10**：同一轉移鏈逐份比對，SHA-256 為 `fccd63c54883e5b6d072aabdfa02362f2564a35be278b4c204c57e821c3f3d09`，producer thread 為 `01a0ad6a-15e0-73c1-be2c-b555d0666fe3`。Producer 完成先於複製、先於新 consumer launch，原 producer artifacts 未改。

run-10/native/rollout.jsonl:25→:29 先讀原 handoff，再讀本輪 checkpoint/provider；:43→:47 實際呼叫目前 owner。它建立 byte-identical 暫存 checkpoint 副本，直接讀本輪 provider；before/after digest 相同，owner 回傳 merge_pending/readback、沒有 request、exit_code=0。TemporaryDirectory 在原工具程式中退出後清除，supplied inputs 逐位元未變。

兩個 handoff 的歷史 request 仍位於歷史欄位；consumer 沒有把 producer next 中的舊路徑或 request 當成當前授權。兩輪工具請求都沒有 replay、dispatch 寫入、invalidate/readmit、GitHub transport 或額外 model launch。run-10 查閱 dispatch --help 是唯讀命令，不是 dispatch execution。兩輪 final 皆明確停於新的 simulated provider readback，沒有宣稱 production Issue 39 resolved。

## 捕捉與身份的獨立檢查

逐一讀取兩輪 native 原始 call/result，確認全部配對且已完成；不是引用 capture-audit 的自報作結論。Every item.started 有 completed、每輪只有一個 completed turn，無 turn.failed。Native rollout 第 8 行的 turn context 明確是 gpt-6-astra/high，與 native session_meta、raw thread.started、history turn 對上；兩個 consumer thread 均不同於原六輪。

每輪 recorder launch/exit、Noodle process/spawn、envelope hash／worker argv、PID/process group/worktree 相符；實際 child.wait=true、returncode=0，均小於 300 秒。Stdout hash／bytes 正確，去掉 Noodle 外加 `_ts` 後的 raw events 與原 recorder stdout 相同。兩輪均保留相同 terminal-delivery 延後機制，並各自真正發出唯一 blocked typed stage_message。Noodle attempt.exit_code 仍為 null；exit 0 的依據是實際 recorder wait receipt，不能改寫成 Noodle attempt 自帶 exit 0。

所有 supplied inputs 的 before／after／inbox bytes 完全相同。Installed/runtime/neutral skill hashes、source HEAD、五份 assigned instruction blobs 全部匹配 selection；common runtime 之外只有預定 instruction＋neutral skill 差異。兩個 doctor 都滿足 repo detected=true 且 cwd/repo root 指向相應工作樹。cleanup receipts 的已列程序與 process groups 已退出、worker clean、cleanup exit=0，實際工作樹路徑現在不存在。此處「無殘留」限於列管程序／工作樹，不是整個系統的檔案清除宣告。

初始 task/input 與全部實際工具請求未觀察到取得 Issue body、rubric/judge、作者報告、其他 session。Handoff 內含 producer 的歷史 identity/path 是授權輸入，不是新 consumer 讀取 producer session 檔案。這仍是 exposed-context 審查，不是安全隔離或隱藏服務模型證明。兩臂的 blocked outcome 是 neutral skill 明示規約，不能單憑它宣稱模型自行發現阻塞政策。

兩個 observer-packet 所有 normalized locator 均能直接對上原始輸出：AGENTS、handoff SHA／producer thread、provider blob、owner output／checkpoint before/after 及 final 文字全部吻合。完整行號與 checks 見 final-audit.json。

## 原失敗、追加 pair 與既有結果連續性

run-07 在 backlog provider readback 得到 HTTP 403；run-08 的 worker admission 也得到 403，native raw 為空，沒有 native thread。run-08 同時保留 recorder BrokenPipeError；不能隱藏這個尾隨失敗或由 launcher failure 推論 Codex 已退出 0。兩輪仍為 INCOMPLETE，其原錯誤／failure-and-cleanup.json、清理結果與 absent worktree 都保留。

additional-pair-selection.json 在 03:36:42 UTC 準備；rate-limit-recovery.json 的 05:08:39 UTC 原始 provider readback 回傳 HTTP 200、remaining 59，Issue body 與原 retained Issue 相同，早於 run-09／10 launch。新 pair 使用新根目錄、owner/order/native sessions；原 failed orders 沒有重啟。只追加這一組；producer 原件保持相同，沒有重新產生手寫替代或新的 producer session。

doctor 措辭差異已述於上方。其客觀依據為 prepare_trials.py:88–89 原有 predicate：精確 repository/cwd 身分，以及只容許 terminal.env 失敗。追加 preflight 同樣保存 doctor_exit=1 和該失敗；沒有藉事後變更 judge/控制讓結果通過。不過 selection 的「successful fresh doctor」確實過寬，報告必須保留，不得稱全綠。

重算原 run-01..06 的 native rollout、實際 child stdout 與兩 producer handoff，均與上一份 audit 的 hash 相同；七份 judge bytes 仍符合外部固定 selection。run-01 原 packet 已另存，修正檔僅把 read_control 從 :43 改成 [:34,:50]，並新增透明 locator_correction metadata；完整控制及實際執行結果對得上原始資料，沒有改 case 結論。

**審查者自身的時間記錄補正**：上一份 audit 最後追加 observer_packet_sha256_at_audit 時，supervisor 的 run-01 locator 修正已生效，因此該 hash 是修正後 packet `3c93009706a2582c94c73f7de6797d1960ec7016b539d79b1196ace1377094e8`。舊 audit 的逐行 checks 描述原 :43，而非已改 packet；這是取 hash 與內容審查間的時間差。保存的原 packet hash 為 `c542d9a42c1115168f7c2a8d4ad1389f5d78362b7f64b002f199fd910a8f8b2d`，其內容符合當時讀到的 locator。本次不修改舊 audit，也不把缺乏更早的 hash 說成原檔遭改。

## 結論邊界

六個已完成 consumer、兩個 producer 的三組限定行為比較有完整 exposed raw 證據與獨立核對；原兩次 pre-model failure 不計入 pass，仍保留。這支持本機共同 instrumentation 下的 scoped non-regression，不支持 treatment 優勢或一般化可靠度。原報告指出的 exposed truncation、後補 supplemental freeze、共享環境與自然退出／compaction 限制繼續有效。

本結論不是 final candidate acceptance、merge/closure readback 或 Noodle production reconciliation，也不授權 landing。公開 export 必須另外核對遮蔽範圍、原件／export hash 與 exposed 可觀測內容；在此之前不宣稱公開檔與本地原件逐位元相同。
