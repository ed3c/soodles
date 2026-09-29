# Claim refusal：一顆 atom 的有界閉環

產品修正與固定外部 oracle 已通過；3組fresh native比較支持有界的決策非退化。改善成立在CLI內部：拒絕不再被當成等待。沒有證明Agent推理成本、token或全流程總成本下降。此報告在正式admission前封存；實際Issue由manifest綁定，交付完成以外部owner terminal receipt為準。

## 真實缺陷與最小修正

Baseline a6254973b15f4f97295a99b29de17fbe7009a171 的 issue_atom.py 在 _run_claim 非零退出後回傳 pending，drive 因而重複呼叫。既有 admission 的 running/proposal_pending 已負責合法等待；非零claim沒有可信的retryable分類。

只把這個分支導向既有 AtomRefusal(noodle.claim.exit)，保留原始process receipt，回傳 Noodle／fresh_noodle_claim 與 exact control_root/order_id/subject。原execution checkpoint與同一authorization/command保留。沒有新狀態、scheduler、retry engine、CLI flag或授權層。P只補上收到此receipt時的停止與fresh-readback要求；feature recipe和system contract更新到相同範圍。

## 固定產品判準

| 情境 | Baseline | Treatment |
| --- | --- | --- |
| claim exit2 | 4次claim、3次fake sleep、錯誤pending | 1次claim、0次sleep、具名input refusal |
| claim exit75 | 同上；不能挪用provider reader的75語義 | 1次claim、0次sleep、具名input refusal |
| 真正running | pending、零claim | 相同合法等待 |
| 成功claim | readiness/publication各一次、停在CI等待 | 相同 |
| 同auth跨3個fresh process | 身分保持，但最初拒絕錯當等待 | 拒絕→owner改變→running→成功接續 |

拒絕案例無claim/acceptance artifact，沒有readiness/publication；所有provider操作都是fixture。固定外部oracle拒絕了植入的重複publication與running時claim反例。Drive telemetry有實際subprocess argv/stdout/stderr/exit，fake clock只縮短測試，不是wall-clock latency證明。

77項focused tests通過，含既有issue_atom/issue_execution與一個固定oracle replay test。外部judge在candidate修改前固定；原始harness兩次allowlist遺漏及修復前baseline失敗保留。第一個產品修正即通過，沒有藉換裁判或反覆挑樣本取得勝利。

## Fresh consumer與上下文接續

使用6個無繼承對話的native consumers；一組train、兩組confirmation，之後未修改source/P/judge。每個只取得中性任務、固定instructions、identity與owner投影；獨立reader記錄實際送入的檔案bytes/digests。

- c1：baseline依pending選wait_for_change；treatment依refused選stop_for_input，交回Noodle的fresh_noodle_claim。兩者都遵守收到的介面，因此這不是模型能力提升。
- c2：兩臂對真正running都等待Noodle狀態改變，不提出claim或其他phase命令。
- c3：新consumer讀舊handoff，再讀當前owner receipt，改為等待GitHub Actions，沒有沿用舊Noodle阻擋，authorization與續接身份保持。

這是read-only report決策比較，不是模型實際執行reentry。真正跨程序重入由上述獨立worker證據支持。initial action gate偏寬（允許兩種停止/等待標籤），凍結後未改；原始treatment report確實選擇stop_for_input。完整平台transcript、精確模型provenance、hidden reads、token與實際compaction均未知。共同任務限制effects，不能推論無限制自主執行也不退化。Treatment instruction/read bytes略增；不能由內部重試下降推論Agent總成本降低。

## 閉環與資料流

已觀察失敗 → verify-soodles受影響recipe → objective code evaluator及正反controls → 外部固定baseline → 一個CLI/P假設 → 產品controls → fresh decisions與confirmation → 固定evidence manifest → 同一Issue/PR的既有acceptance/landing。

閉環目標是指定因果鏈內正確完成或正確阻塞、保留身分並能在真實狀態改變後恢復，同時移除可證明的無效重試。它跨session依靠持久化owner證據與當前readback，不依靠作者記憶。失敗控制透過tests重播，P規則回到既有feature/skill；不建立泛用eval平台或每輪全圖maintenance。

原始report與裁判見behavior/；產品raw見verification/；analysis.py可從原始stdout重算固定產品判定。Behavior輸入保留實際絕對路徑；異機重播須顯式映射封存路徑，不能假裝原runtime仍存在。來源、判準、carrier或owner語義改變時應重驗受影響範圍。全系統與任意未來任務永不退化不在本次證明內。

## 交付邊界

本候選必須通過既有native publication readiness、exact-head Linux acceptance，再由外部固定landing owner處理provider merge/closure與local Git/Noodle reconciliation。decision.json與fixture receipt皆不授權landing。delivery/references.json指向本次外部交付證據位置；此處不預造terminal verdict。
