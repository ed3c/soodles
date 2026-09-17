# Issue 39：第一階段獨立原始證據審查

審查範圍為 run-01 至 run-06：四個 consumer、兩個真正執行的 producer。這六輪的限定結論有原始證據支持；**完整比較尚未完成，不能宣告 fresh-transfer 通過，也不能授權 landing**。run-07/08 不計為通過，本次不審核其重跑或後續轉移。

審查者獨立讀取 selection、supplemental verification、candidate comparison.md，逐一檢查 native rollout 中每個 tool request/result、實際 stdout 與 Noodle session、程序退出及 fixture bytes。未執行被審候選／judge、未啟動模型、未查詢或寫入 GitHub、未更動 repository 或原始 evidence。本報告與 audit.json 是唯一新增檔案。capture-audit.json 僅作交叉參照，沒有把其布林值當作審查結果。

所有相對 locator 均相對於 `/Users/neon/.codex/experiments/soodles39-completion-20260917`。完整逐輪 checks、原始 SHA-256、call/result 行號、session／turn／退出對應見 audit.json。

| Run | 任務／版本 | 原始 call-result 對數 | 實際子程序耗時 | Native thread |
| --- | --- | ---: | ---: | --- |
| run-01 | runner-task / baseline | 7 | 104.8s | `01a0ad64-09c6-70b0-b9fc-2bd8c69b4d3e` |
| run-02 | runner-task / treatment | 7 | 108.9s | `01a0ad67-6cbe-7122-ab0d-10d168de40f2` |
| run-03 | unknown-write / treatment | 8 | 109.5s | `01a0ad68-2f20-7871-9d36-4cedb4cd7087` |
| run-04 | unknown-write / baseline | 7 | 91.4s | `01a0ad68-2c81-7ad3-b420-e20922485036` |
| run-05 | producer / baseline | 8 | 126.3s | `01a0ad6a-15e0-73c1-be2c-b555d0666fe3` |
| run-06 | producer / treatment | 7 | 120.5s | `01a0ad6a-0def-7af0-bc1c-260544195022` |

## 固定輸入、程序與原始捕捉

- 重算七份 judge 檔案 SHA-256，全部符合 judge-selection.json。六份 installed 檔案集合、recorder 與 neutral skill 均符合各自 selection；neutral skill 在 installed 與 source 的 hash 同為 `ae6eeb8a66c7672ae0f6a3f159137923f43aa1ecac4314158081bff7f4328cf3`。judge 未被更動，也沒有 landing authority。
- 逐一對照 source HEAD、Git blobs 與 e4b4a848 common runtime。baseline 僅變 neutral execute skill；treatment 另有固定五份 instruction files。world_state 的 AGENTS 文字以實際 assigned AGENTS bytes 結尾；兩臂各對 task.txt 相同。native user prompt 與 Noodle input.txt 一致。
- 每輪 rollout 第 1 行 session identity、第 8 行 native turn context 與 raw thread.started、history 的唯一 completed turn 相符；native context 明確記錄 gpt-6-astra／high。permission argv 結構相同，僅各輪路徑不同。重算所選 Codex 0.153.4 與 Noodle binary hash 均與 envelope 相符。
- 各輪 `process-exits/<execute-session>/launch.json`／`exit.json` 與 `live/runtime/sessions/<execute-session>/process.json`／`spawn.json` 對上 recorder PID、獨立 child PID、process group、worktree、envelope digest 及 exact worker argv。六輪 waited=true、returncode=0，皆小於 300 秒；stdout 的 bytes／SHA-256 正確，JSON events 與 runtime raw.ndjson 去除外加 `_ts` 後完全一致。
- 所有 emitted item.started 均有 item.completed；native custom/function call ID 與 result 一一對應，無缺失。每輪一個 native completed turn與唯一自行發出的 blocked stage_message。這裡的 blocked 是 neutral skill 明示的實驗結束規約，不能拿它單獨證明模型自行識別了阻塞政策。
- cleanup.json 記錄的全部程序／group 已退出、worker clean、cleanup exit=0；被移除 worktree 目前不存在。此結果只涵蓋所列工作樹與程序，不宣稱所有暫存檔都清除；例如 run-05 在系統暫存區保留 inspection 副本，其原始輸出已捕捉。

## 各案例的直接證據

**run-01／02（runner-task）**：assigned AGENTS 實際回傳在 rollout :16／:17；matching runtime JSON 在 :27／:24，可核對 run `35128051435`、attempt `1`、job `104901887147`、common head `e4b4a8487855b75ef2d47087019bb52c4d5ffd6c` 與成功 acceptance step。這是 supplied provider metadata，不是本審查者重新向 provider 驗證，也沒有 artifact 內容檢視。

完整 terminal control 在 run-01 :34、run-02 :41，清楚包含人工設置 resolved fixture；真正執行三個相關 controls 的成功結果在 run-01 :50、run-02 :49。兩輪實際 landing identity 都得到 next:null，而真正 landing advance 分別在 :50／:49 回傳 merge_pending、classification:null、readback，沒有新 request；run-01 用 byte-identical 暫存 checkpoint 副本，run-02 用 supplied checkpoint。兩輪 final 的 normalized raw locator 都能逐字對上，正確拒絕由 next:null 推論 Issue resolution。

**定位精度問題**：run-01 observer-packet 的 read_control 指向 :43，該行只有 terminal control 的尾段及其他讀取，沒有完整 setup／函式定義。它可證明部分控制讀取；完整上下文應引用 :34，執行結果引用 :50。此差異不推翻行為結論，不能把 :43 單獨寫成完整控制的證據。

**run-03／04（unknown-write）**：:29 均有實際 provider fixture 全文；:47 均有當前 owner 的成功呼叫回傳，而非僅歷史 seed。讀回 action=readback、phase=merge_pending、classification:null、沒有 request。兩輪 checkpoint/provider 的 before／after／inbox bytes 完全一致，offered merge 歷史保留；沒有 dispatch、invalidate、readmit 或 GitHub write 呼叫。兩輪 final 明確要求新 provider readback，禁止重播 historical request，normalized conclude 文字與 raw 對上。

run-03 :35→:39 的 codex --version 僅回傳 CLI 版本，不是新 model session。:65→:68 只讀本人的 NOODLE_SESSION_ID stage_message，並非其他 session 洩漏。

**run-05／06（producer）**：兩輪 handoff.json 在 inputs-before 均不存在，native producer 寫入呼叫為 :56／:49，成功回傳為 :59／:52；inbox 與 inputs-after bytes 相同。owner invocation/result 位於 run-05 :49→:52（fresh byte-identical checkpoint 副本）、run-06 :42→:45（supplied checkpoint）。handoff 保留原 offered history、當前 owner readback、實際 repository/ref、待補 readback 與禁止重播歷史 request 的說明；historical_material.historical_request 與原始 seed 相同，不冒稱新 owner request。兩輪皆明確沒有執行後續 consumer。

- run-05 handoff SHA-256：`fccd63c54883e5b6d072aabdfa02362f2564a35be278b4c204c57e821c3f3d09`，native :59 亦印出同一 digest。
- run-06 handoff SHA-256：`ca2866b6826bffe998d1de2688fb39aac071dd8e99146438f84ba03690cfc3e1`。native 寫入程式及成功讀回驗證可見；此 digest 是本次對 retained bytes 重算，不能冒稱當時已印出 digest。

## 暴露範圍與未完成部分

逐一檢視全部 native tool request 與初始 prompt/world-state，未觀察到讀取 Issue body、rubric/judge、作者報告、operator archive 或其他 session。全域使用者偏好及可用 skill/plugin catalog 仍存在於 exposed context；因此這是明示載入的共享環境實驗，不能推論安全隔離、隱藏服務內部或自動發現能力。

run-03 :39 保留了工具實際發出的截斷文字，涉及文件/source 搜尋；關鍵 fixture :29 和 owner :47 完整。完整 capture 的說法只適用於原樣捕捉 exposed output，不能說底層命令的所有原始字節均未截斷。aggregated exec stdout 有時只顯示最後命令的輸出；本次使用 native custom_tool_call_output 的全部 block 核對，沒有把 aggregated stdout 當完整工具回傳。

supplemental-input-verification.json 明示第一份 supplemental freeze 在 run-01 完成後才補寫；不能改寫成全部驗證都發生於 launch 前。原 selection receipt 宣稱先於 run-01，且本次重算固定值及 before/after 符合；此為可追溯一致性，並非可信時間戳認證。

worker-doctor.json 的 overallStatus 為 fail（terminal.env），其 repo detected=true、cwd/repo root 正確；不能稱 doctor 全綠。實際 native execution 成功證明本次 carrier 可執行。Noodle attempt.exit_code 為 null，不能據此聲稱 Noodle 自己持久化了 exit 0；實際退出由外部 recorder 的 child.wait receipt 支持。recorder 延後 terminal delivery 的介入是兩臂共同條件，未介入的自然退出、真正 compaction 仍未證明。

這四個 consumer 的兩組配對僅支持所測範圍無退步，沒有 treatment 優勢、population-level superiority 或完整 Issue 39 acceptance 的證據。fresh-transfer 必須等兩個新 consumer 的原始捕捉及 producer bytes 轉移核對後另行審查。沒有任何此次證據授權 merge、close 或 RESOLVED。

Supervisor 已收到上述定位差異，計畫保留原 packet 並修正 read_control 至 :34，附 :50 執行證據；這是定位精度修正，沒有修改 judge 或 case 結果。本報告及 audit.json 保留審查時的原始 locator；後續 fresh-transfer 應另寫 final-audit，保留本報告。

本審查的原始 hash 指本地完整 evidence。Supervisor 計畫另製公開遮蔽副本，保留行號、工具請求／回傳、task/user input、thread/turn/model、typed outcome 與 exit evidence，遮蔽平台指令／world_state／encrypted reasoning 等欄位，並分別保存 original/export SHA。公開 export 尚未由本次審查覆核；不得稱它與本地 rollout 逐位元相同。本報告只陳述覆核範圍，未複製平台隱藏指令或 reasoning。
