# Issue atom 回饋閉環模擬

本次工作把六個需求範例放入既有 Schema Manager 格式。Test Manager 選擇缺少的觀察。Schema Manager 把選擇結果放入原 owner 的 `next.evidence`。`stage-outcome feedback` 保留事件及失敗歷史。這次沒有建立第二個 scheduler 或執行器。

## 資料集與範本

[案例資料](../../../tests/fixtures/atom-feedback/cases.json)包含六筆參考答案。每筆資料都有輸入、明確需求、預期欄位、符合需求的樣本、植入錯誤的樣本及來源說明。

| 案例 | 檢查的決策 | 植入的錯誤 |
| --- | --- | --- |
| `whole_atom` | 整顆 Issue 使用 poteto-mode | 只選 how |
| `finite_explanation` | 明確子工作選 how，並在解釋後停止 | 改用完整 mode 並繼續寫入 |
| `missing_skill` | 必要 skill 的固定內容缺失時停止相依工作 | 繼續工作 |
| `unknown_route` | 完整路由資料缺失時保留未知 | 從單一例子猜出完整路由集合 |
| `candidate_changed` | candidate 改變後不沿用舊 verdict | 把舊 verdict 當成有效 |
| `unknown_write` | 寫入結果未知時先由原 owner 讀回 | 改用其他 owner，或先執行下一個效果 |

這是需求導出的 golden 範本。它不是人工標註的產品樣本，也不是保留測試集。`null` 是 `unknown_route` 範本明訂的表示方式。AGENTS 的一般原則只支持保留未知，不能單獨證明這個 JSON 表示方式。案例不聲稱官方 pstack 或實際產品已執行這些行為。

[測試](../../../tests/test_atom_feedback.py)把範本轉為既有 schema 2 protocol。它分開保存 requirements、instructions、input、criteria review、report 和 trace。測試對 report 使用 literal 樣本，沒有把 expected 直接當作執行結果。每個 trace 都標示 `deterministic_fixture`。

這些範本是開發資料。後續 Agent 比較需要另選未給 consumer 看過的輸入。supervisor 持有 expected。fresh consumer 只取得任務、固定指令及必要資料。consumer 的真實輸出不得被符合需求的樣本取代。

## 為何修改既有回饋鏈

原本的 Test Manager 在目前案例失敗時，仍可能重用同一 fingerprint 的舊成功。這個推論把「以前成功」誤當成「現在不必修正」。新失敗是反證，所以本次修改讓它優先要求新觀察。即使同一輸出還缺其他欄位，已觀察到的失敗也不能被舊成功蓋過。

原 CLI 另列 `feedback.test_scope`，讓 consumer 自行找舊證據。新投影把必要案例及可重用 report、trace 引用放入 `next.evidence`。adapter 先檢查引用的內容雜湊。檔案缺失或改變時，adapter 向 review-writing 回傳拒絕，並要求完整舊證據或新觀察。它不追加事件，也不把問題誤交給 Noodle dispatch。

只傳案例名稱更短，但無法指出要沿用哪一份觀察。重新執行全部案例可以取得資料，卻會重做已有證據的工作。因此這次保留原 owner，補上精確引用。Schema Manager 仍須驗證完整下一輪 selection。reuse 本身不會產生 PASS。

## 已觀察的模擬閉環

既有 disposable fixture 代替 Noodle event writer。測試呼叫實際 `stage-outcome` CLI。它核對 admission、派發內容、selection 及事件回讀。它不啟動模型、真實 Noodle worker 或 GitHub 寫入。

觀察順序如下。

1. 條件不成立時，owner 回 `review_criteria`。它不接受完成。
2. 缺少觀察時，owner 回 `supply_behavior_evidence`。失敗次數不增加。
3. 新觀察違反需求時，owner 回 `correct_pclass`。Test Manager 只要求受影響案例。
4. 完整修正通過時，owner 回 `consume_verified_behavior`。它保留先前失敗次數。
5. 同一 selection 再送一次時，owner 只讀回結果。它不追加事件。
6. fixture 的 stage 完成回報成功。回報仍為 `authorizes_landing: false`。

另一組控制把舊成功、本輪成功及本輪缺件放在同一輪。consumer 合併原 reuse 引用、目前 verified 觀察及新觀察後，才取得 PASS。內容、方法、需求、輸入或 expected 改變時，舊 fingerprint 不能重用。既有 owner 測試另涵蓋三次失敗後重新評估，以及未知事件寫入的讀回。

測試也找到先前 Issue 全文改動的整合缺口。派發 producer 已加入 `issue_body`，但 outcome adapter 仍按舊欄位重建 binding。結果是合法回報被拒絕。本次 adapter 先核對全文雜湊與所選 contract，再重建 binding。缺少或竄改全文的回報仍被拒絕。

## 成本回饋及證據範圍

本次保留八次 fixture CLI 呼叫的 stdout、stderr、exit code 及實測時間。Test Manager 的 `review_cost` 消費這些資料。Schema Manager 的 `project_cost` 與 `project_owner_feedback` 將結果放回原回應。控制確認原 owner 的 `next` 沒有改變。未知模型成本維持未知。另一個植入缺失成本資料的控制確認 `needs_owner_readback` 也不會產生新效果。

這是 fixture 驅動的成本回饋模擬。沒有啟動真實 Issue owner。它證明資料可以走過這些現有函式，不能證明實際 Noodle 交付成本或自動修復成效。

本機紀錄位於 `/Users/neon/soodles-audits/atom-feedback-20261003/`。`source-pins.json` 固定來源內容。編號 receipt 保留每次 CLI 觀察。`schema-owner-feedback.json` 保留成本投影及原 continuation。這些歷史路徑不是重播授權。

六次新 feedback 觀察的 Schema 驗證時間約為 0.65 至 1.22 ms。完整 fixture CLI 呼叫約為 152 至 429 ms。讀回 receipt 中的 Schema 時間是原回合數值，不算新的測量。這些數字不包含模型、網路或實體驗證。它們不能用來排序完整工程架構。

## 可重跑的局部控制

```sh
./soodles test --module test_atom_feedback --module test_feedback_owner --reason 'Issue atom feedback fixtures and owner continuation'
```

Test Manager 對 fixture 目錄有既有 boundary map 中的對應。資料檔修改會選到此控制。這條命令只重跑 disposable 控制，不請求真實產品執行或交付。

目前支持的結論是模擬回饋鏈可以完成，並能拒絕指定反例。真實 Noodle 的實作、委派、驗證、交付與恢復最短路徑仍未測得。要比較那個結果，仍需同一任務與停止點、固定來源、fresh consumer、獨立驗證者、真實 owner 交接及正常執行成本。這次模擬不替代那些證據。

## 保存後的指令消費實驗

一個 `fork_turns: none` consumer 只取得任務、保存後的 feedback procedure、混合 owner 回應及目前 selection。supervisor 事先保存 protocol 與 expected，沒有把它們提供給 consumer。

consumer 選出四個需要新觀察的案例。它保留 `whole_atom` 的原 reuse 引用及 `finite_explanation` 的目前觀察。它回報 `can_complete=false` 和 `authorizes_landing=false`。Schema Manager 對這份實際輸出回傳 `VALID`、`PASS` 及 `consume_verified_behavior`。task owner 已消費此結果。receipt 是 `consumer-schema-receipt.json`，讀回記錄是 `consumer-owner-readback.json`。

這份證據與 deterministic fixture 分開。它只有一個 consumer 的規劃決策，沒有執行四個缺件案例。capture 是 consumer 保存的輸出與讀取記錄，不是完整平台 transcript。它不證明實作或交付成功，也不證明相對效率改善。


## 後續小迴圈：補齊缺件並修正錯誤判準

本輪沿用先前混合回應中的四個缺件。每個案例由新的 native consumer 處理，且 `fork_turns` 為 `none`。consumer 只讀原先固定的簡短工作契約及該案例輸入。它們沒有收到 protocol 或 expected。這不是完整 poteto-mode 的執行實驗。

前三個 consumer 分別回報停止相依工作、保留未知路由，以及不沿用其他版本的 verdict。第四個回報 `next_effect="original-owner readback"`。原判準只接受 `"readback"`，所以 Schema Manager 先記錄 FAIL。

這個 FAIL 揭露判準缺陷。原需求只規定 owner 和操作順序。它沒有規定字串 enum。獨立 clean-context 審查確認第四個回答符合決策需求。只比較字串也可能放過錯誤 owner 或錯誤順序，因此直接改成接受另一個同義字仍不夠。

修正保留原輸出與原 FAIL。owner 接著記錄 `review_criteria`。新判準使用 `readback_owner` 和 `readback_before_next_effect`。前者比對輸入指定的 owner。後者表示讀回是否須先於下一個效果。新的 request 明確定義這兩個欄位，再交給另一個 fresh consumer。它回報 `publication` 和 `true`。

Test Manager 在這次修正後只要求 `unknown_write`。其餘五份觀察維持原引用。Schema Manager 收到完整 selection 後回傳 PASS。重送相同 selection 取得 readback。最後，原 disposable fixture 的 `stage-outcome completed` 回傳 `recorded`，並保留兩次失敗歷史。這是 fixture 的 stage outcome，沒有把真實 Noodle order 改為完成。

最終六筆觀察具有不同來源。`whole_atom` 與 `finite_explanation` 仍是既有 deterministic fixture。其餘四筆是模型對模擬狀態的決策。不能把它們合稱為六次真實工程執行。另有一個舊版格式的模型回答及一份獨立判準審查，均保留在歷史中。

局部控制改為逐一植入錯誤欄位。它分別驗證錯誤 owner 和錯誤順序都會被拒絕。Test Manager 選定的 `test_atom_feedback` 模組共 10 個控制通過。本次沒有重跑全套，也沒有修改產品執行器。

本輪紀錄位於 `/Users/neon/soodles-audits/atom-followthrough-ax3_13_o/`。`01-initial-feedback.json` 保存原 FAIL。`02-criteria-feedback.json` 保存判準拒絕。`03-partial-feedback.json` 保存只需補一個案例的決定。`04-complete-feedback.json` 及 `05-feedback-readback.json` 保存通過與讀回。`06-stage-completed.json` 保存 fixture 完成回報。`closure.json` 綁定來源分類、成本投影與未解問題。

Test Manager 將正常呼叫的時間與歷史失敗送回 Schema Manager。成本審查回傳 `needs_owner_readback`。本輪以原 owner 的最新 PASS 與精確 readback 承接此要求，再記錄 stage outcome。歷史失敗沒有被清除。模型專用時間、tokens、費用及實際交付效益仍為未知。

本輪只支持這個有限結論：四個缺件已補齊，錯誤判準已修正，既有模擬 feedback owner 已接受並讀回完成回報。真實 Noodle 派發、獨立驗證、provider 交付與恢復仍需要所選 atom 的實際 owner 證據。既有 native consumer 不會因此變成 Noodle worker，這輪也不建立全域最短路徑的結論。


真實歷史資料的後續核對見[真實交付資料的可證範圍](real-evidence.md)。它區分已記錄的交付成功、成本覆蓋缺口與尚未成立的最短路徑結論。


使用者已將最短路徑指定為決策數量。後續比較採用[Agent 決策量測定義](decision-metric.md)，不以耗時或 token 數代替決策數。


後續已將可確定的 selection 組裝放入既有 CLI。見 [CLI 輸入與接續的小迴圈](cli-input-loop.md)，其中保留錯誤推論、legacy 反例、局部控制及 P-class consumer 回饋。
