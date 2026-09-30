# Issue #195：可接續的本機 Issue 入口

狀態：依使用者最新重述的正確性與證據閉環範圍，準備同一 Issue #195 的正式 writer／PR／交付。原先操作數降低至少 20% 的實驗仍判定失敗；本次交付只主張下列限定正確性修正，沒有重評或宣稱效率改善。

## 已實作

- 失敗 CI 的 current next 保留已知 repository／Issue／head／run 身分，指向既有 product＋fresh behavior 評估。
- 共享 local delivery gate 重用 frozen_paths 檢查，拒絕與外部固定 bytes 不同的證據。required_paths 仍由外部契約選定，不是通用語意裁判。
- next-issue 使用現有 host 註冊取得 issues:write token，不在 P 指引嵌入私鑰路徑、不要求 Session 搬運 token。
- 新準備的 local intent 帶有獨立、綁定其 bytes 的 create state；同一 intent 的進入由 lock 串行，POST 前 durable offered，之後只讀回。缺少 state 的舊 intent 不能重新 POST。
- 成功 create 後 exact GET 驗證同一 Issue；未知結果回傳 frontier 保存位置與既有 reconcile argv。HTTP 錯誤保存狀態碼與 request ID，不保存可能回顯憑證的 body。User-Agent 明確化不等於已證明歷史 500 的根因。

## 實證與限制

原 failed-head 比較：五個產品情境從 4/5 到 5/5；fresh selection 與 confirmation 都是 baseline 2/3、候選 3/3，shell 呼叫中位數均 5。既有 P skill 保留，額外文字被撤回。共享 evidence gate 的替換證據反例從錯誤通過改為拒絕。

create 延伸：14 項控制通過，含真实子程序在外部 effect 前／後退出、重入、並行、HTTP 500、錯誤身分、錯誤 GET 號碼、缺憑證、損壞／舊 state。既有 provider credential／continuation 39 項控制也通過。新增 credential 入口在沒有人工 GH_TOKEN 的情況下成功對真實 #195 執行 GET；没有測試用 live mutation。

三輪假設分別是 CLI 修正、P 指引更新、CLI 補足 reconcile continuation；12 次 selection 加上固定候選後 6 次 confirmation。所有 handoff 結構檢查通過。Baseline 始終帶出舊的 token 注入義務；候選正確區分正常 terminal、unknown readback、真正的 host prerequisite。這是 workflow 義務的修正，不能歸咎於 baseline Agent 不遵守原輸出。

Selection 的 shell 呼叫中位數：baseline 6、r01 7、r02 6、r03 6；confirmation：baseline 6、r03 8（增加 33.3%）。效率門檻未過，不能宣稱 token／時間／操作數最短或效率不退化。計數包括 carrier；原始命令與錯誤保留，不刪除不利數據。

Raw process capture 在 consumer 外執行；語意 trace review 由 supervising Session 執行，並非經人工校準的獨立語意裁判。Fresh 任務限定中性、只讀的 continuation handoff；它不證明任意 bug 自動修復或 model-driven live provider write。所有 fixture 使用相同 pinned local carrier，讀取隔離經探測；程序與暫時 credential runtime 已清理。原 17 次 failed-head consumer（含 2 次排除校準）與本次 18 次 create consumer 均保留。

## 閉環與未完成部分

證據鏈：真實失敗 → 固定評測／產品反例 → owner/P/CLI 修改 → 外部 capture → fresh handoff → once-only confirmation → 外部契約綁定 → 同一 PR exact-head acceptance → landing/reconciliation。前三組 source 修正與實驗已備妥，後面的交付尚未執行。

確認 Issue #195 建立不等於本候選已交付。历史 unknown POST 已保留；後續使用者明確指示的一次 create 得到 201，exact GET 驗證 #195。新的 CLI 不會倒寫該 historical intent 的狀態。所有觀察與 local receipts 均不授權 landing。

查看 archives 的 index 可將原始臨時路徑對應到封存 member；這些已清理的絕對路徑不是 production durable handoff。所有實際成功／失敗判準與原始資料都保留，不能把 docs 敘述當成 correctness authority。

## 完整驗證發現的相容性修正

第一個正式 writer 完整跑完 526 項測試：525 通過、1 失敗。新增 keyword `issue=` 與既有固定 oracle 的 positional adapter 不相容；owner 正確拒絕 publication，沒有 commit 或 PR。保留失敗原始 log、逐項 timing 與 typed blocked outcome。

只將 optional Issue 參數改為可用 positional 傳遞，並在 lifecycle 呼叫端使用 positional；固定 oracle 與所有 tests 未改。26 項受影響控制通過。外部觀察重播 5 個產品情境與 3 個 confirmation 輸入，僅正規化明確的 source-root 位移後，輸出與 read calls 全部等價。原 fresh consumer 證據的 source pin 保持原值，藉此等價證據連到修正後 source；未把舊模型執行冒稱新版本 fresh run。這是限定輸入的相容性證據，不是全面語意等價。

產品層此次需修正；P 指引、consumer-visible confirmation inputs 與 next-issue source 保留。沒有新增模型搜尋輪、改善主張或另一套測試引擎。舊 writer/authorization 不覆寫；同一 #195 以新選定的乾淨 control root 重新准入，交付仍限一個 PR。

## 原始 patch 的無損封裝

修正後正式 writer 的 526 項測試全部通過，沒有 skip；最後 staged whitespace check 發現原始 unified diff 的合法空白 context 行與 repo 檢查衝突。將該原始 patch 改存 deterministic gzip，解壓 bytes 與原 SHA-256 完全相同，原判準、失敗與模型記錄未改。產品 source 七檔、P 指引與 consumer 輸入全部未變，故重用這次完整產品測試與既有 fresh 證據，不新增模型搜尋或重跑不受影響產品套件。保留 staged 失敗紀錄，封裝檢查必須對全部選定檔案通過，不放寬 gate。

## Publication 前的本機 readback 修正

Native readiness 通過，但 Noodle claim 讀到 App 共用 Git repository 過期的 origin/main；既有 publication gate 拒絕不符准入 base 的 claim，沒有 push 或建立 PR。Fresh provider GET 確認 main 仍是准入的 0977f25，正常 git fetch 更新 remote tracking ref，主 working tree 的 main 與檔案未改。原 claim／authorization 保留。現有 lifecycle 缺少原地 pre-publication claim refresh 入口，因此同一 Issue 用 fresh admission 重新取得 owner claim。七個 source/P/test 檔案不變，重用既有產品與 fresh 證據；不宣稱本次有新的 Agent 自動修復 readback 比較。
