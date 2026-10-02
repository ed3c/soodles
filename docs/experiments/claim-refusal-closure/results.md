# Claim refusal：一顆 atom 的有界閉環

產品修正已通過固定外部 oracle。3 組 fresh native 比較支持有界的決策非退化。CLI 的修正使拒絕不再被當成等待，但沒有證明 Agent 推理成本、token 或全流程總成本下降。本報告在正式 admission 前封存。manifest 綁定實際 Issue，外部 owner terminal receipt 才能證明交付完成。

## 真實缺陷與最小修正

Baseline a6254973b15f4f97295a99b29de17fbe7009a171 的 issue_atom.py 在 _run_claim 非零退出後回傳 pending。drive 因而重複呼叫。既有 admission 的 running/proposal_pending 已表示合法等待。非零 claim 沒有可信的 retryable 分類。

修正將這個分支導向既有 AtomRefusal(noodle.claim.exit)，並保留原始 process receipt。回傳值包含 Noodle／fresh_noodle_claim，以及 exact control_root/order_id/subject。原 execution checkpoint、authorization 和 command 均保留。修正沒有新增狀態、scheduler、retry engine、CLI flag 或授權層。P 只補上收到此 receipt 時的停止要求與 fresh-readback 要求。feature recipe 和 system contract 更新到相同範圍。

## 固定產品判準

| 情境 | Baseline | Treatment |
| --- | --- | --- |
| claim exit2 | 4次claim、3次fake sleep、錯誤pending | 1次claim、0次sleep、具名input refusal |
| claim exit75 | 同上；不能挪用provider reader的75語義 | 1次claim、0次sleep、具名input refusal |
| 真正running | pending、零claim | 相同合法等待 |
| 成功claim | readiness/publication各一次、停在CI等待 | 相同 |
| 同auth跨3個fresh process | 身分保持，但最初拒絕錯當等待 | 拒絕→owner改變→running→成功接續 |

拒絕案例沒有 claim/acceptance artifact，也沒有 readiness/publication。所有 provider 操作都使用 fixture。固定外部 oracle 拒絕了植入的重複 publication，以及 running 時執行 claim 的反例。Drive telemetry 記錄實際 subprocess argv/stdout/stderr/exit。fake clock 只縮短測試時間，不能證明 wall-clock latency。

77 項 focused tests 通過，涵蓋既有 issue_atom/issue_execution 與一個固定 oracle replay test。外部 judge 在 candidate 修改前固定。原始 harness 的兩次 allowlist 遺漏，以及修復前的 baseline 失敗均保留。第一個產品修正即通過，沒有更換裁判或反覆挑選樣本。

## Fresh consumer與上下文接續

本輪使用 6 個不繼承對話的 native consumers，分為一組 train 和兩組 confirmation。之後未修改 source/P/judge。每個 consumer 只取得中性任務、固定 instructions、identity 與 owner 投影。獨立 reader 記錄實際送入的檔案 bytes/digests。

- c1：baseline 依 pending 選擇 wait_for_change。treatment 依 refused 選擇 stop_for_input，交回 Noodle 的 fresh_noodle_claim。兩者都遵守收到的介面，因此結果不表示模型能力提升。
- c2：兩臂收到真正的 running 狀態後，都等待 Noodle 狀態改變。兩臂均未提出 claim 或其他 phase 命令。
- c3：新 consumer 先讀舊 handoff，再讀當前 owner receipt，然後改為等待 GitHub Actions。它沒有沿用舊 Noodle 阻擋，並保持 authorization 與續接身份。

這次比較觀察 read-only report 的決策，沒有讓模型實際執行 reentry。上述獨立 worker 證據支持真正的跨程序重入。initial action gate 允許兩種停止/等待標籤，判準偏寬。固定後未再修改，原始 treatment report 選擇了 stop_for_input。完整平台 transcript、精確模型 provenance、hidden reads、token 與實際 compaction 均未知。共同任務限制了 effects，因此結果不能推論至無限制的自主執行。Treatment instruction/read bytes 略增。內部重試減少，不能證明 Agent 總成本降低。

## 閉環與資料流

本輪先將已觀察失敗對應到 verify-soodles 的受影響 recipe，再建立 objective code evaluator 與正反 controls。外部固定 baseline 後，以一個 CLI/P 假設進行修正。產品 controls、fresh decisions 與 confirmation 提供判定依據。固定的 evidence manifest 將這些證據交給同一 Issue/PR 的既有 acceptance/landing。

本輪目標是在指定因果鏈內正確完成或阻塞，同時保留身分。真實狀態改變後，原流程須能恢復。修正也須移除可證明無效的重試。跨 session 的接續依靠持久化 owner 證據與當前 readback，不依靠作者記憶。tests 重播失敗控制，既有 feature/skill 保存 P 規則。本輪沒有建立泛用 eval 平台，也沒有要求每輪執行全圖 maintenance。

behavior/ 保存原始 report 與裁判，verification/ 保存產品 raw。analysis.py 可從原始 stdout 重算固定產品判定。Behavior 輸入保留實際絕對路徑。異機重播須明確映射封存路徑，不能假定原 runtime 仍存在。來源、判準、carrier 或 owner 語義改變時，須重驗受影響範圍。本次結果不保證全系統與任意未來任務永不退化。

## 交付邊界

本候選仍須通過既有 native publication readiness 與 exact-head Linux acceptance。之後由外部固定 landing owner 處理 provider merge/closure 與 local Git/Noodle reconciliation。decision.json 與 fixture receipt 皆不授權 landing。delivery/references.json 指向本次外部交付證據的位置。本報告不預先宣告 terminal verdict。
