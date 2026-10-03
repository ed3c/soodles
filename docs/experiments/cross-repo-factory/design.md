# 跨 repository factory 的 target 與 runtime 分離

本次 Issue 是 `ed3c/soodles#229`。基線為 `069e866949c268efee3d529f4d9ae7a4fdf8c106`。
需求是讓已授權 target 使用既有 owners，且 target 不必攜帶 Soodles 原始碼。
本文件記錄設計與 source trace。執行觀測見 [results.md](results.md)。

## 問題與選擇

基線的 authorization 與 publication 要求 repository 等於 Soodles。
其他 consumers 從 `PROFILES` 取 base 與 workflow。Admission 從 target Git 讀取 runtime。
因此只移除 repository equality 不足以完成需求。後續 worker、scope、CI 與 cleanup 仍會失敗。

| 方案 | 資料與 owner | 代價 |
| --- | --- | --- |
| A | Supervisor 在 initial selection 固定完整 target 設定，沿既有 owners 傳遞 | 若每層複製設定，acceptance 資料可能漂移 |
| B | 每個 consumer 解析一個固定外部 reference | 若仍從 target 載入 runtime，reference 不能解除執行耦合 |

採用 A 的選擇時機與既有 owner，使用 B 的單一 immutable reference。
Binding reference 是絕對 `path` 與 `sha256`。其 schema 1 保存 repository、base_ref、workflow_path、jobs 與 verification。
Runtime 另由 supervisor 固定完整檔案集合及 digest。這個選擇不新增 scheduler、source registry 或 authority flag。
較簡單的新增 profile 只能再支援一個寫死的 target，不能滿足兩個未註冊 targets 的要求。
把 factory 複製到 target 會保留耦合，因此不採用。

## Runtime 資料流

Supervisor 的 authorize 讀 selection、target Git、carrier 與兩個 external owners。
它核對 origin、base、binding bytes、workflow、target scope 與 runtime closure。
成功時，它原子寫入 authorization 與既有 continuation。失敗時，不建立 lifecycle 或 provider effect。
沒有 target_binding 的 legacy selection 保留原固定 profile、格式與 source closure。

Issue atom 讀同一 authorization，要求 generic lifecycle 從已固定的外部來源執行。
Admission 複製已選 runtime closure 到自己的外部 bundle。Target Git 只提供 target source 與選定 instructions。
Bundle 的 launcher、worker、outcome 與 test entries 在 import 前驗證全部 pinned bytes。
Noodle 仍建立 order、session 與 worktree。Scheduler 以 launcher inspect 取得原 automatic continuation。
Worker prompt 帶入 binding reference、contract 與外部 runtime argv。

Test Manager 從 binding.verification 讀 owner、覆蓋 paths 與命令 argv。
它不使用 Soodles BOUNDARIES 推導 target tests。缺少覆蓋時，它回傳具名 scope owner input。
外部 test entry 在原 worktree 執行命令，回傳退出碼、輸出與耗時。
Schema Manager projection 區分 scope 已選定與命令尚未觀測。它保留原 owner next，不授予 effect。
P-class feedback 經同一 stage-outcome entry 寫入原 Noodle session。

Publication 核對 Noodle claim、clean candidate、origin、base、fresh Issue 與 manifest。
它將 binding reference 保存於 readiness。它不修改 Noodle claim。
Atom 的 select_run 核對全部 selected jobs、必要 steps、repository、head 與 run attempt。
Failure context 保留同一 reference。Correction 從 binding 取得 base_ref，不猜 provider default branch。

Landing claim 保留同一 reference 與原 execution envelope。
Landing 在 effect 前驗證完整 provider evidence、dependency edges 與 candidate。
Legacy consumer 若依賴 generic producer，landing next 也必須攜帶 producer binding。
Provider readback 用該 reference 驗證 dependency GET，再回到原 checkpoint。
Unknown write 保留 checkpoint，只有原 owner readback 能決定後續行動。
Local reconciliation fetch 選定 base_ref，核對 merge、closure、Git 與原 Noodle order，再使用既有 cleanup owner。
Next-Issue 沿 candidate reference 驗證 frontier、intent 與 readback。
Local create 先持久化 offer，再呼叫 POST。再次進入已有 offer 時，只要求 readback。

## 接受與拒絕的邊界

可接受條件包括固定且完整的 runtime closure、正確 target Git 身分、完整 target scope，以及 exact-head 多 job evidence。
錯 repository、origin、base、digest、head、attempt 或缺少 job/step 都必須在相關 effect 前拒絕。
Missing scope 是具名 owner input。它不要求 full suite。
Native readiness 只允許後續 publication；它不是 Linux canonical acceptance。

目前 carrier 的 Noodle publication claim 與 cleanup 使用 origin/HEAD。
因此 generic initial admission 要求選定 base_ref 與該 integration branch 相符。
不同 targets 可用不同 defaults。任意非 default base 尚未支援。
Source trace 來自 selected binary 對應的 Noodle revision `3732a02f9994c23bbb2be30c31801b7a2da586af`。
沒有透過改寫 claim 或 origin/HEAD 迴避這項限制。

## 證據不能授予的結論

「文章已完整描述流程，所以 runtime 可用」的推論缺少實際 consumer 與 effect 證據。
本次用 source tracing 找到 consumers，再以小型 target fixtures 執行可觀測的邊界。
文章、hash 與 passing fixture 仍不能證明真實 target 已交付或 Agent 普遍遵守指引。
P-class 使用 saved-byte consumer reports 與原 session feedback，只支持該次 scoped decisions。

Writer 交付本因果修正與證據。後續 owner 仍須完成 factory exact-head canonical CI、publication、landing 與 reconciliation。
原 supervisor 然後以獨立 target admission 完成真實生產、正常使用讀回、replay 與並行證據。
這些 later-owner outcomes 未在本 writer stage 執行，整體需求仍未完成。
