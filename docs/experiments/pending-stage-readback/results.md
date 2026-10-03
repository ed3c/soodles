# 初始 pending execute 讀回修正

本紀錄是 Issue #258 的 N-class 證據。它不授權 publication 或 landing。
本次 base 是 `04032d233f7f286e485ce9d20a9ad7254d12f167`。

## 原主張與證據

原 `_admit` 要求每個 canonical stage 的 `attempts` 都是 list。
這個條件隱含了一個錯誤前提。它把 order 已排入視為 attempt 已建立。
Noodle 的 admission 與 dispatch 發生在不同時點。
初始 pending stage 可以明確帶有 `attempts=null`，而且沒有 session 或 worktree。

原診斷位於 `/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/cli-shortest-path-readback-review.json`。
本次重新讀取它引用的兩份 raw schedule 日誌。兩份日誌的雜湊都與原紀錄相同。
兩次 automatic 呼叫都以 exit 1 回傳 `status=refused`，欄位為 `noodle.stage`。
它們的 stage 都是 index 0、task_key 與 skill 為 execute、provider 為 codex、runtime 為 process。
兩者的 status 都是 pending，attempts、session_id 與 worktree_name 都是 null。

| 原始來源 | SHA-256 |
| --- | --- |
| `/Users/neon/medium-compiler/.noodle/sessions/schedule-20261003-170444-8b1f83/raw.ndjson` | `801d6b19a35848924f51764d92b11467ae423ea45e684d8361a742c7acb31627` |
| `/Users/neon/.codex/worktrees/landing-base-product/soodles/.noodle/sessions/schedule-20261003-171241-94591e/raw.ndjson` | `d0fd08c4cb0482409bf4b211427f5a826441216bad19101f6876d4c7f541e133` |

base 的 `issue_execution.py` SHA-256 是 `86759220d3667ebfcc30c0e4ba04c3387cfe0980e2e7b7dd227dab74fb162b82`。
這與原診斷的 source 相同，也符合 contract 的 frozen base path。
本次保留原始日誌。未重寫失敗紀錄，也未重演其他 live atoms。

原診斷另記錄後續相同 order 已進入 running。
這是原 owner 的後續觀測，不是本次對那些 live owners 的新查驗。
舊 schedule 拒絕不能代替目前 owner 狀態，也不能授權重啟 writer。

## 選擇與執行行為

要求是讓讀取者辨識已被 Noodle 持有的初始 pending order。
接收該讀回只代表觀察成功。它不建立第二個 proposal 或 writer。

`_admit` 仍先讀取原 envelope、Issue binding、carrier 與 canonical snapshot。
當 attempts 明確為 null 或空 list 時，新增的局部分支驗證以下條件。
order 必須具有原 order_id、active status，而且只有一個 stage。
stage 必須具有正確 index、execute task_key 與 skill、codex provider、已選 model，以及 process runtime。
它必須處於 pending，而且沒有非空 session_id 或 worktree_name。
prompt 必須等於原 binding、envelope digest 與原 prompt route 的完整 projection。
缺少已選 model 時，分支回傳具名 refusal，不產生 KeyError。

automatic 或 supervised 的 `observe_live=True` 接受符合條件的 pending 讀回。
它們沿用既有 `action=owned` 與 `published=false` 回應。
`next` 保留 Noodle owner、原 order_id 與 `current_order_and_session_readback`。
程式不改 snapshot 或 mailbox，也不執行 dispatch、restart 或 provider write。
普通 supervised takeover 不接受這個例外。它仍依原 stopped 與 quiescent 條件運作。
後續有正確 live attempt 時，既有 supervised observation 仍回 `running`。

全域把 None 轉成空 list 不符合要求。
該作法會掩蓋 running、dispatching 或 terminal 狀態缺少 attempts 的錯誤。
本次只在 `_admit` 辨識已驗證的初始 pending shape。
空 stages 也會拒絕。沒有 stage 時，owner 無法建立所需的 execute 身分。
原 automatic 路徑曾略過空迴圈並回 owned。這個既有缺口不符合本次 missing stage identity 拒絕要求。
本次在原 order guard 加入非空條件，並以負例檢查。
非空 attempts 沿用原檢查。空 attempts 只接受上述初始 pending shape。
新增負例也拒絕缺少身分、外來 prompt 或 carrier、非 list attempts、非 dict attempt，以及矛盾 session 或 worktree。

原 atom 的已啟動 owner 使用既有 `own_start_wait` 分支。
整合控制在同一個 snapshot 先取得 admission 的 owned 讀回，再執行原 atom run。
原 atom 維持 pending 與 waiting，回傳同一個 issue-atom run argv。
Schema 的 owner_transition 必須同為 waiting，且 gaps 為空。
兩次呼叫各自讀取同一 snapshot。atom 由 require_available_owner 提前回傳 own_start_wait。
它不直接消費前一次 supervised 呼叫的 owned receipt。
這個控制證明相同資料的等待判定一致，不證明新 receipt 的端到端消費。
這個控制不把一般 owned 狀態解釋成新效果授權。

## 方法與驗證範圍

工程入口是所選 `execute` 與 Poteto Mode Bug fix。
本次沿用使用者提供的 how 與 diagnosis 證據。沒有新增架構 bakeoff 或 model eval。
實作只改 `_admit`，沒有新增 production function boundary。
獨立原生 subagent 負責有限實作。root 負責 evidence、Test Manager 與原 atom 整合控制。
另一個原生 subagent 進行獨立 source review 與新增 comments review。
目前 carrier 未提供 Cursor Task 型別或其預設模型，使用目前可用的原生工具。
方法路徑與 SHA-256 保存在 `/Users/neon/.codex/experiments/pending-stage-258-writer/methods.json`。
工作步驟與例外保存在同目錄的 `work.md`。
依使用者要求，沒有提交失敗 tests，也沒有執行 Opening a PR 的外部效果。

Test Manager 選擇 `test_issue_execution`、`test_issue_atom` 與 `test_candidate_verification`。
前者驗證兩個公開 admission 入口。第二個驗證原 continuation 與 Schema 消費者。
第三個保留既有 delivery evidence validator 控制。
本次不修改測試選擇器。明確 scope 沒有請求 physical control 或 full suite。
所有 fixture 都使用 disposable directories。測試不啟動 live Noodle 或 model。

初輪執行 126 tests，exit 0。總 wall time 為 77.552 秒。
`test_candidate_verification` 通過 3 tests，module wall time 為 2.388 秒。
`test_issue_atom` 通過 95 tests，module wall time 為 77.544 秒。
初輪 `test_issue_execution` 通過 28 tests，module wall time 為 12.130 秒。
自審後新增 missing model 與空 stages 控制。因此再執行受影響的 `test_issue_execution`。
最終該 module 通過 29 tests，exit 0，wall time 為 10.310 秒。
重跑有 source 與控制變更原因。沒有追加 full suite 或 benchmark。
並行 module 的耗時不能相加視為總 wall time。
這些 fixture 成本不構成 live lifecycle 成本改善的比較。

可重用的驗證命令如下。

```sh
./soodles test --module test_issue_execution --module test_issue_atom --module test_candidate_verification --reason 'Issue 258 exact initial pending discriminator, original atom wait and Schema projection, and required delivery manifest'
```

原執行輸出保存在 `/Users/neon/.codex/experiments/pending-stage-258-writer/tests.stdout` 與 `tests.stderr`。
最終受影響 module 的輸出保存在同目錄 `tests-final.stdout` 與 `tests-final.stderr`。
獨立審查沒有發現程式缺陷。審查指出上述 consumer 證據限制，本文已明列。
第二輪審查確認空 stages guard。它要求修正空 attempts 的描述，本文已修正並讀回。
新增 diff 沒有 comments 或 docstrings，no-comments review 沒有要求刪除。
root 自審 production diff、effect 邊界與測試斷言。`git diff --check` 通過。
`deslop` review 沒有發現需新增抽象或刪除的程式碼。

## 交付界線

writer 完成 clean candidate、必要控制、獨立 review、commit 與原 stage outcome。
原 publication 與 landing owners 仍須完成 exact-head CI、merge、Issue closure，以及 Git 與 Noodle reconciliation。
parent 的 medium replay、持續使用與 Production 工作仍未由本 unit 證明完成。
本次 fixture 只證明列出的 runtime 判定與效果邊界。
它不證明所有 Agent 都不會猜錯，也不構成決策數量改善的量測。
