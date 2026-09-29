# 完整目標與完成判準（實作前）

使用者來源：/Users/neon/.codex/attachments/76953e31-9b59-46e6-8663-e373d9250685/貼上的文字.txt。新目標要求逐項完成，不可把 #189 的有界修正等同整體。

| ID | 必要結果 | 必要驗證 |
| --- | --- | --- |
| R1 | 真實 failure → owner/state/side effect → recipe/oracle 映射 | 已觀察來源引用、baseline 重現、合法不同 case |
| R2 | 按需 eval 方法入口與實際版本/適配 | 全路由有明確条件/產物；code優先；人標/審閱不能假造；pins有digest |
| R3 | 可重用的精簡實驗目錄與資料流 | recipe可到入口，protocol/manifest/raw/analysis/decision/delivery各有實物；選用分支不製造空假證據 |
| R4 | 有效裁判在candidate外固定，controls有鑑別能力 | 確定正反/合法不同case，換bytes或缺controls拒絕，不以candidate測自己授權 |
| R5 | Judge train/dev/test 與 optimizer train/selection/confirmation 分開 | group/trace/衍生關係防洩漏，碰撞拒絕；無LLM judge時記明不適用，不能說已校準 |
| R6 | 實際角色資料隔離 | consumer/optimizer無法讀本次private expected/confirmation；實際host denied-read探測；只fresh context不算 |
| R7 | Fresh baseline 與固定條件下實際Agent執行 | common carrier/model/tools，actual actions/results，獨立telemetry；禁止只靠report |
| R8 | 有界多輪 hypothesis/patch→測量→保留/回退 | 對客觀決策barrier固定指標與停止規則，失敗保留，不靠換裁判；正確性逐stratum gate |
| R9 | 停止選版本後未見同分布 confirmation | winner pin，隔離group，失敗不可換樣本／重算；一次程序走完 |
| R10 | 證據有效性→行為正確→成本順序 | missing invalid不能計分；Agent可觀測操作/usage成本與CLI內部成本分開；結果不佳就修正或如實停 |
| R11 | context/handoff與全受影響因果鏈閉環 | 新consumer刷新owner；state保持；必要產品drive、下一owner、terminal evidence |
| R12 | 新失敗/裁判bug/語義漂移再驗證 | 已結束舊比較、固定新bytes重啟量測的可重現拒絕/正例；反例回流controls |
| R13 | 既有owner交付與副作用控制 | 同一新Issue/PR final complete head、existing acceptance/landing/readbacks/reconciliation，無新scheduler |

完整架構不等於所有未來任務永不退化，也不等於強迫每顆atom啟用所有conditional skills。未適用路由仍須被正確定義和驗證不能偽造前提；任何必需證據unknown不得完成相應項目。

TODO：Ground（進行中）→Sketch兩個不同形狀→Cross-review/synthesis→固定外部oracle及隔離carrier→Implementation→真實比較與confirmation→既有writer/交付→逐項審計。沒有可證明結果前不標complete。
