# 原 owner 的 admission revision

本文件記錄 #238 的實作與驗證設計。它不授予 publication 或 landing 權限。
原需求是接續兩個 publication 前的 atom。#229 的 clean completed candidate
尚未包含前進後的 provider base。#237 的 required_paths 錯把 unchanged reference
列為必須修改的產物。兩者都必須保留原 authorization、task、judge 與歷史。

## 原推論與修正

原 #229 設計一度把 execution.source_head 當成每次 dispatch 的 current HEAD。
這個前提導出錯誤結論，認為保留原 instruction source 就無法通過舊 judge。
Supervisor 的 source-head-semantics-review.json 與本次 fixed-reader control
證明舊 reader 可接受歷史 admission source。拒絕發生在原 worker 的 entry check。
因此本次只擴充有界 worker entry。Envelope 不假報 retained candidate 的身分。

原 #237 criterion review 建議另選 corrected judge。Supervisor 選了較小修正。
舊 judge 要求 required_paths 有淨變更。原 task 卻要求 reference bytes 不變。
製造空白變更會違反 task。改 candidate validator 也不能改變固定 judge。
本次讓 supervisor 明列 required/frozen reference 修正。其餘 task 與 artifacts
保持原約束。有效 contract 仍由原 judge 正常消費。

## 資料與 owner

| 資料 | 意義 | owner |
| --- | --- | --- |
| 原 authorization | 不可替換的 task、judge、修復身分 | 原 admission owner |
| standard envelope | 有效 Issue body/base 與原 admission/instruction source | supervisor_admission.prepare |
| revision-entry.json | retained head/tree、target、terminal、prior attempts、native acceptance | 同一 producer 的 external bundle |
| scope_history | 原 body intent、selection、custody、controls、acknowledgements | 原 issue-atom checkpoint |
| request_changes_requeued | 原 native review 接續的 candidate/session/worktree binding | Noodle review owner |

Selection 有明確 type。base_advance 只前進固定 base 並重算既有 base hashes。
criteria_correction 只修改逐筆列出的 required_paths/frozen_paths。
它可同時前進 base，但必須另通過 ancestry 與 provider readback 檢查。
Owner 從 immutable Git objects 讀取 hash。它不接受任意 JSON patch 或 candidate
自填的 reference digest。它不改 write_paths、task、acceptance 或 judge。

## 執行流程

Supervisor 固定 selection 與 accepted native refs。原 owner 在原 lock 下驗證
terminal event、停止的 process group、canonical order/session 與 clean head/tree。
它要求原有效 base 是 retained candidate 和 target 的祖先。
第一次 Issue patch 前，它刷新 repository/default branch/target readback。
它先保存 exact before/after intent，再呼叫 provider。失聯時只讀回同一 Issue。

Producer 保留原 execution/source/instruction bytes。它把 sidecar digest 寫入
bundle manifest 與 provider entry。Prepare readback 重驗所有固定 bytes。
原 held loop 依序執行 request-changes、edit-item、requeue 與 supervised release。
每個 control 先保存唯一 ID，然後等待 acknowledgement。未知結果不重送。

Worker 從 sealed entry 取得 retained candidate。它要求 exact successor、prior
attempts 與 native custody 相符。只有這個分支可在尚未包含 target 時啟動。
Writer 在原 worktree 整合 target。Completed 要求 clean 且 target 已是祖先。
普通 worker、claim、publication 與 landing 沒有取得 ancestry 例外。

若 target 在 effect 前前進，owner 要求新的 bounded selection。
未執行 selection 可被明確取代，但原 selection 留在 checkpoint。
已發生 effect 時，owner 先完成原 readback。完成的 revision 依序封存。
下一次 projection 從原 authorization 重建，並核對 body hashes 與 control acks。
自動建立 Issue 的原 body marker 也保持不變。

## 為何沿用原 owner

獨立 wrapper 會另造 checkpoint、unknown-effect 判斷與 dispatch 身分。
現有 scope amendment 已有這些機制，因此本次直接擴充其 typed selection。
只有 envelope 無法如實承載的 entry custody 放進 sealed sidecar。
改 prompt 而不改 producer/worker 無法驗證這個例外。改舊 judge 也不是所選方案。

## 證據界線

[results.md](results.md) 區分 source controls、fixed reader、native dispatcher
與 P-class consumer report。Fixture 不代表 #229/#237 已接續。
[handoff.md](handoff.md) 保留 root 的 runtime activation、真實交付與 medium replay。

## 固定 base 的整合

本次 supervisor 選定 `a90adfde0e0208e76183f8420aa7b0075d9edaf3`。
Writer 將它合併到原 retained candidate。新的 base 要求 stage prompt 帶完整
`issue_body`。Typed revision 仍須攜帶 sealed context。這兩個輸入不能互相替代。
前者讓 worker 驗證 body digest 與 contract。後者讓 worker 驗證 retained
candidate、原 instructions 與 exact successor。Projection 同時保留兩者。

`scope_projection` 保留 base 的已 prepared `base_recovery` 路徑。
Typed revision 仍由 scope history 還原有效 authorization。Body marker 由既有
`authorized_issue_body` 產生。這沿用新 base 的 body 規則，並保留原 revision
歷史。Worker 完成時仍須 clean，且 target 必須是最終 candidate 的祖先。
