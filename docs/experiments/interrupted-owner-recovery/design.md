# 原 authority 的 interruption 接入

本 candidate 屬於 ed3c/soodles#234，base 為
`ce29059e6d9581e7c83257c45e7c88cdd9b9c3fe`。
它保留原 #229／#232 的 identity 和未完成需求。它不操作這兩個 live runtime。

原 normal log 顯示 #229 backlog GET 回傳 401，loop 隨後退出。
沒有 expires_at 證據，因此不能推論 token 已過期。
#232 run003 顯示 repair.invariants changed。原 implicit repair binding
使用會隨 landing 同步的 control source，因而失去原 source identity。
這些是來源與既有 log 的觀察，並非本次重演 live 故障。

## 設計與執行路徑

要求是保留原 dirty candidate，同時只允許原 order 的唯一 successor。
直接放寬 clean check 無法區分原 candidate 與 foreign worktree。
因此 worker 消費 Noodle 的 custody、candidate manifest 和 successor receipt。
Soodles 不另建 manifest。普通 worker 的 clean gate 保留。

Resume 消費外部 descriptor，保存原 auth 與 custody selection。
Run 先讀 fresh Issue，再保存 prepare intent，執行 native 回傳的 argv。
未知結果只讀回。Native prepare 保留 candidate，取消原 attempt 並保留 exit unknown。
它產生 pending stage，沒有 dispatch。

Supervisor producer 產生新 external bundle。它保存原 task、instruction context、
source head 和 Issue body，只投影已選定 carrier 及 recovery context。
Ensure_noodle 使用原有 start intent 與 config 保存流程，先 manual hold。
原 edit-item ack 和 prompt 相符後，mode owner release。Native owner 派出唯一 successor。
Soodles 等到 dispatched readback 才進入普通 lifecycle。

Worker 可能比原生 dispatch-result.json 先啟動。
它只在 existing spawn、live native lock 和 offered attempt 相符時等待。
Spawn 與 result 共用兩秒期限。等待不啟動模型，也不重送任何 effect。
Receipt 出現後，worker 重新讀取 current session/attempt 和原生 candidate_unchanged。
模型前要求 true。Supervisor 在 writer 合法修改後只驗證 lineage。

原 repair source reader 支援 explicit external owner 和 implicit auth.base_head。
Implicit reader 解析原 issue_atom.py 的 literal LIFECYCLE_FILES，再讀該 base 的 Git objects。
它不 import 歷史 Python。新 runtime 的文件清單不改變歷史 binding。
Policy、context、binding、lineage、history 和 counters 必須完全匹配。
新 owner 保留原 ledger，且不取得新的 repair effect allowance。

## 原 candidate 的 outcome consumer

原 writer 的 execute 指令要求 `./stage-outcome`。
原 source 的 shell entry 執行同目錄 stage_outcome.py，再載入舊 validator。
該 validator 不接受 recovery_context。只更新外部 worker bundle 不能改變這個 import。
首輪 writer 因此保留 consumer scope 缺口。本輪 contract 已納入所需 adapter 和 controls。

接入必須保留原 candidate bytes 和 instruction pins，同時讓 writer 完成 feedback 與 outcome。
本輪選擇由現有 external launcher 轉交 stage_outcome.main。
另一個方案是另建 outcome executable，再把其路徑和 bytepin 投影給 writer。
既有 launcher 已有 manifest 驗證和環境入口。沿用它可避免第二份入口 identity。

Recovery prompt 在 typed recovery_context 中提供兩個命令。
兩者使用 `"$SOODLES_ADMISSION_LAUNCHER" stage-outcome`，再附上原回報參數。
它明確替代當次機械入口，保留原 task、instruction pins 和回報規則。
Launcher 先檢查 bundle bytes，再從選定 runtime 載入 outcome reader 和 feedback 依賴。
Reader 驗證 current stage、session、spawn 和 native successor。
此時 writer 可已修改 candidate，因此 reader 驗 lineage，不重用模型前的 unchanged 條件。
錯誤 identity 或變動 bundle 會在 event write 前拒絕。未知 event write 仍只做 owner readback。

## Ack 到達次序

原實作先讀 stage，再讀 control ack，最後以先前 stage 判斷 ack 的效果。
控制可能在兩次讀取之間完成。此時新 ack 配上舊 prompt 或 mode，造成誤拒絕。
重現控制取得 `interruption.prompt=changed`，但 fixture owner 已保存正確 prompt。

修正後，supervisor 在 edit ack 成功後重讀 prompt，在 release ack 成功後重讀 mode。
既有 intent 仍阻止重复 append。沒有 ack 時只等待 readback。
測試覆蓋兩種 ack 競態、未知控制、外來 ack，以及 writer 修改後的 dispatched lineage。
原生 fixture 另驗證 external bundle、native dispatch、worker admission 和同 session outcome。
它不執行 live resume、publication 或 provider closure，也不證明完整 live lifecycle。
