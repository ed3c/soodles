# Poteto 工程方法交接

本次範圍是 ed3c/soodles#230。原 Noodle execute writer 修改兩份 skill。
所需結果是 writer 實際讀取 Poteto Mode 及適用方法，並保留既有生命週期 owner。
本次不修改 runtime、provider policy、global Poteto package 或外部 judge。

## 為何同時修改兩份 skill

原問題是 supervisor 選了工程方法，但 writer 入口沒有要求消費該方法。
`supervisor_admission.py` 的 `prepare` 封存 execute skill。
`issue_execution.py` 的 `_admit` 建立 `do=execute` 的 stage。
原 prompt 帶有 task、contract 及 selected instruction context。
這些 source 支持在 execute 入口交接方法。它們不證明模型已使用方法。

只在 issue-atom 增加 supervisor 指示不能滿足 writer 消費需求。
另開 writer 會更換原 session，並超出本次要求。
因此 issue-atom 指向 execute 的方法入口，execute 要求原 writer 讀取可用方法。
兩份 skill 保留原 admission、worktree、stage、修正歷史及 provider owners。

Supervisor 先讀可用 Poteto Mode 與適用 playbook。
它把需求、失敗及證據交給既有 task 和 contract。
Noodle 繼續派發 execute。Writer 讀取實際方法檔，保存 path、SHA-256 及理由。
如果必要能力缺少，writer 記錄缺口，繼續不依賴該能力的已授權工作。
若缺口阻止 writer 要求完成，writer 使用既有 blocked outcome。
工程方法沒有額外 publication 或 restart 權限。

## 修正拒絕推論

原錯誤主張是「停止本身不授權重啟，所以所有修復都必須停止」。
其前提把 restart effect 與診斷、推論修正、owner repair 混為一談。
原 task 已授權 skill 修正與 scoped feedback。既有 source 已將 recovery 分屬不同 owner。
因此 restart 限制不能推出所有授權工作都停止。

Snapshot 的 `running` 是狀態紀錄，不是程序存活證明。
程序消失也不能證明先前 provider write 沒有效果。
Agent 必須保留 refusal、失敗歷史及原 continuation。
未知 write 需要原 owner readback。沒有材料變更時，Agent 不重試原拒絕。
Predispatch resume 只處理該段已定義的未派發 correction。
Active writer 中斷需要原 owner recovery。兩者不能互換。
本次只修正這個推論及路由，不執行任何 stopped writer recovery。

## 本次採用的方法

主方法是 Poteto `authoring-a-skill`。
Writer 已讀 `bug-fix`，用 source 和既有 receipt 定位錯誤前提。
本次不需要重演 provider effect。缺少的證據是保存後指示的 consumer 決策。
Writer 使用 review-writing 審查條件及文字，使用 eval-audit 檢查既有 feedback 管線。
Test Manager 選 scope。Schema Manager 比對綁定證據的結構欄位。
`unslop` 與 `technical-writing` 用於短句、actor、條件及一致術語。
`principle-prove-it-works` 使驗證綁定實際保存檔，不沿用舊三案的 PASS。

Cursor Task、指定 role model、`poteto-agent`、Comment Sicko 及 worktree isolation 參數在本 carrier 不可用。
Cursor create-skill、control-cli 及 deslop 未由本 session 提供。
Writer 使用已安裝的 Codex skill-creator 做局部 authoring 審視。
這不是 Cursor 方法或跨模型驗證的等效完成聲明。
本 task 已明確要求原 writer 完成修正，因此沒有委派 implementation writer。
原生 fresh consumers 只作指定觀察，各自寫獨立外部 evidence 目錄。
它們共享 filesystem。`fork_turns=none` 不代表 filesystem isolation。

## 可觀察的接受邊界

四個案例分別覆蓋正常交接、stale running、錯誤 acceptance condition 及不支援的 carrier 參數。
Protocol 在 consumer 啟動前保存。Expected values 留在觀察者一側。
每個 consumer 只取得 task、兩份 saved instructions、所需方法及自身 output 目錄。
問題使用 bool，避免以未定義的字面標籤評分。
原 writer 逐欄對照原需求，再讀 trace 檢查 report 是否矛盾。
條件審查屬原 writer 的自審，不是獨立 judge。

若指示、輸入或方法 digest 不符，證據無效。
若缺少 consumer report，行為仍未知。
若有效 report 違反受原需求支持的條件，該案例失敗。
只有受支持條件及有效 passing observations 齊備，才完成此 scoped P-class feedback。
Schema Manager 的 PASS 僅涵蓋 consumer report。它不證明未觀察 effects 或普遍行為改善。

原 writer 透過 `stage-outcome feedback` 消費 Test Manager 與 Schema Manager。
完成後以原 `stage-outcome completed` 交接。
Supervisor 後續負責 publication、exact-head CI、landing 及 Git/Noodle reconciliation。
本次不取代 #229 authority 或其未提交候選，也不宣稱 factory 總要求已完成。
