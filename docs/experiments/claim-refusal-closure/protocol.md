# Claim refusal 的單一 atom 閉環

目標：在同一 authorization 的 execution→claim→readiness/publication 因果鏈內，停止把 claim 非零退出當成正常等待。正常 running 必須仍可等待；fresh owner state 改變後，同一入口必須能恢復。任何拒絕都不得觸發 readiness/publication 或 provider writes。

方法：既有 verify-soodles issue-execution/pclass-context；evals-start 已知失敗路由直接採程式判準，無須新建 LLM judge、人工 discovery 或通用 eval engine。Pstack 的單一假設/固定量測/保留或回退方法；本次只維護受影響 recipe，不聲稱 full-map maintenance。

固定 source baseline a6254973b15f4f97295a99b29de17fbe7009a171。外部 oracle manifest 在 candidate 修改前選定；其 protocol 定義7個process drives、獨立consumer比較、樣本與停止規則。查 evaluator/protocol.md 與 evaluator/manifest.json；不得在看到候選結果後替换有效裁判。

假設：將 claim 非零退出導向既有 AtomRefusal，將 exact owner/identity 與 fresh-readback 缺項交給 Agent，比 pending 更不易造成無效重試。修改只涵蓋該分類、相鄰控制、P指引及映射契約。

產品門檻優先於效率：所有有效拒絕、合法等待、成功接續、身分保持及敏感度控制通過。重試數由外部 subprocess capture 計算；fake clock 不代表真實 latency。Agent 結果獨立報告；相等只算非退化，不能算prompt效果改善。原始輸出與失敗保留。

一個實作假設最多三次修正後重估原因；已有固定判準下的成功即可停止，不為挑好看的樣本增加消費者。Confirmation失敗不得重算為成功。唯一正式provider mutation由同一Issue的既有issue-atom/landing owner處理，fixture與模型比較不取得寫入權限。

閉環終點：產品控制＋有界行為證據完成，固定完整candidate交給既有exact-head acceptance及landing，取得merge/closure和地端reconciliation receipt。Experiment decision不授權landing。沒有單次實驗能保證所有未來任務永不退化。
