# 把可確定的回饋接續放進 CLI

本輪修正 P-class 對最短路徑的推論。使用者要求減少 Agent 必須自行選路的障礙。耗時、token、工具數及文件長度不能代替決策量測。一般修正也不需要先增加計數器。已能由事實與政策決定的操作及輸入，應由既有 CLI owner 產生。

## 原推論與修正

原推論把「owner 已回傳唯一 next.operation」當成「Agent 已有完整 continuation」。來源顯示這個前提不充分。`feedback.test_scope` 已選定 observe、reuse 與 verified 案例，但 consumer 仍須從不同 selection 找出 references，再組成下一份輸入。`next.operation` 也只是標籤，不是 shell 命令。

本輪保留原有 operation、owner、admission 和 event writer。Schema Manager 依已驗證的 selection 產生下一份輸入的固定部分。Test Manager 仍決定哪些案例需要新觀察。stage adapter 加入經驗證的舊 references。Agent 只提供仍缺少的真實 observations。設計、條件審查及程式修正仍需要工程判斷。

只新增一個狀態標籤無法填補輸入缺口。本輪沒有增加另一套 kind/operation 對照表。既有 operation 仍是唯一判別欄位。

## CLI 的局部契約

`soodles schema pclass-feedback` 保持唯讀。`stage-outcome feedback` 保持原 admission、session 及非終端事件的檢查。

- 需要 observations 時，`next.input.selection` 提供固定 protocol、適用的 criteria review 及目前 passed references。stage adapter 同時加入合法 reuse references。
- `next.input.requests` 提供其餘 case ID、input reference、report identity 及必要輸出欄位。它不提供 expected 值。
- consumer 補入真實 report 與 trace references，保存 selection 並計算 digest。validator 仍核對原身分及完整 evidence。
- 需要審查條件、修正指令或重新評估根因時，`input` 為 null。不能把上一份供證據草稿當成修正方案。
- 本介面的 `next.argv` 為 null。operation 不是可執行命令。完整輸入仍經既有 CLI 提交。
- `VALID + behavior=null + criteria_pending` 要先審查條件。它不是 PASS。
- PASS 交回 task-owner。它不產生 stage outcome，也不授權 publication 或 landing。

新 input 不是已完成的 selection。若新報告缺失，CLI 保留 INCONCLUSIVE。若漏掉目前 passed observation，CLI 仍拒絕完整通過。若新觀察已有 failed check，舊 PASS 不能覆蓋它。來源被改動時，原 digest 與 criteria 綁定仍會拒絕。

## 小迴圈紀錄

獨立審查先修正兩個文案問題。決策比較只在任務有要求時進行，不成為一般修正的新 gate。失敗行為要求先以有效條件為前提，避免把錯誤判準算成 Agent 錯誤。

第一輪三個局部模組共 23 個控制通過。之後來源審查發現 legacy readback 的漏測。真正舊格式沒有 `next.evidence`，但第一版控制只刪掉新 input 和 argv。這會拒絕原本合法、資料齊全的舊回合。後續修正與證據保留在同一輪紀錄，不把第一輪綠燈當成恢復已完整驗證。

修正後，受影響的 `test_atom_feedback` 與 `test_feedback_owner` 共 19 個控制通過。未受影響的 `test_pclass_feedback` 五個控制沿用第一輪結果。本輪共覆蓋 24 個局部控制，沒有執行全套或 provider 寫入。舊格式控制刪除 `argv`、`input` 與 `evidence`。它覆蓋空 reuse、有 pinned prior reuse、缺少原 selection，以及不相容的歷史 scope。

兩個 `fork_turns: none` consumer 讀取保存後的三份 P-class 指令及 owner 資料。cedar 沿用 CLI 草稿，加上四份指定的 fixture observation references。固定欄位及原 references 完全保留，唯讀 schema CLI 回 `VALID / PASS`。birch 讀到 `criteria_pending`，保留 `review_criteria` 與 review-writing owner，未提交行為結果。兩者都未把 feedback 當成 stage 或 delivery 授權。

這兩份 consumer 輸出另綁定至本輪 P-class protocol。公開 schema CLI 回 `VALID / PASS`。Test Manager 的 `feedback_scope` 沒有待補案例。Schema Manager 投影 `consume_verified_behavior`，本任務的 supervising Agent 已消費此回覆。`owner-consumption.json` 保存實際承接與未證明的範圍。這完成本輪局部 P-class 回饋，不等於 Issue 已交付。

六份業務 observations 是 deterministic fixtures。真實模型行為只在讀取、組裝與回報接續的兩個 consumer 中。cedar 首次將兩個章節名稱當成一個名稱，擷取失敗後改正。birch 擷取時額外顯示同一指定檔案的相鄰段落。這些偏差保留在 capture，沒有改寫成零錯誤紀錄。原始碼控制與這些 consumer 結果不能證明決策總數下降。

本輪外部證據目錄為 `/Users/neon/soodles-audits/decision-cli-h_ik37x1/`。後續結果以該目錄的最終 receipt 為準。

## 結論邊界

這一輪只處理 P-class feedback 的 CLI input/output 和相關說明。它沒有把完整 poteto-mode 推理流程改成固定 DAG。它沒有建立另一個 scheduler，也沒有執行真實 Issue 交付。

軟體控制證明指定合法及拒絕邊界。fresh consumer 觀察只支持所給輸入的行為。新增欄位、控制通過或一次 consumer 成功，都不能證明全域最短路徑或 Agent 永不猜錯。比較改善仍需要相同任務、起始狀態、權限、合法終點及事前固定的可觀察決策單位。
