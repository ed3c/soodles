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

## 尚未閉合的 consumer

原 writer 的 execute 指令要求 `./stage-outcome`。
原 source 的 shell entry 直接執行同目錄 stage_outcome.py。
該模組從舊 candidate 載入 issue_admission；舊 exact-object validator
不接受 recovery_context。外部 worker bundle 更新不能改變這個 import。
因此 worker admission 成功不足以證明 writer 能回報 outcome。

本 Issue 的 write_paths 未含 stage-outcome、stage_outcome.py 或其直接 controls。
目前必須由原 admission owner 補足 consumer／activation 範圍。
候選 writer 不自行修改原 instruction pins 或新增 authority。
完整 resume、run、bundle、native dispatch、worker adapter、stage-outcome
整合尚未驗證。這個 candidate 保留 blocked，不可當成 activation-ready。
