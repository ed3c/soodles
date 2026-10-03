# Failed-order restart 的範圍與證據

本次修正屬於 `ed3c/soodles#243`。Writer 基準為
`a2e6f36bdffa893c6d9d31ad31b4880551634d80`。
目標是在已接納的 typed prepublication revision 中，讓原 owner 接續
request-changes、edit 或 requeue 後停止的原 order。

## 設計與來源

Supervisor 的 source 調查與設計保存在
`/Users/neon/soodles-audits/failed-order-restart/`。
本次沿用 `ground.md`、`synthesis.md`、`design-a.md` 與 `design-review.md`。
這些檔案提供 how 與 architect 的調查，不是 acceptance authority。

原推論認為 failed order 一律不能跨重啟。此前提來自舊 carrier。
已接受的 Noodle #106 保存 completed-origin request-changes custody。
支持的結論只涵蓋 supervisor 固定接受的 binary 與完整 custody。
因此本次擴充原 typed revision owner，不替換舊 carrier，也不遷移一般 failed-CI。
只放寬 failed 判斷仍不足以防止未知 start 或 control 的重複效果。

資料仍由既有 `scope_amendment` 保存。
Owner 以完整 native custody 區分 failed、edited 與 pending。
它比對 process、session bytes、candidate、config 與 control readback。
通過後，既有 start owner 保存一次 continuation restart intent，啟動 manual process。
原 ACK prefix、control identity、attempts、authorization 與 judge 保持不變。
Release 前重新驗證 requeued custody，Noodle 才能派發唯一 successor。

## 固定 native 輸入

Supervisor 選定的 acceptance descriptor 是
`/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/prepublication-base-owner/native-accepted.json`。
其 SHA-256 是 `175584927cd3ff119c640645072411951ccd05c787fbecd03b82535e9ea4906a`。
Binary SHA-256 是 `347dc64b9d98bc7f290ab6e6e4a54866a11f8a5bcb653b91122becb59c31acc5`。
Observer 重新驗證這些 bytes。Latest main 不替換此選擇。

## 方法與工作分配

Writer 使用 execute 選定的 Poteto Mode Feature 方法。
方法 paths 與 SHA-256 記錄在 `/tmp/soodles-243-work/methods.json`。
工作清單與決策記錄在同目錄的 `plan.md`、`decisions.tsv`。
Source 與 deterministic controls 由同一 code owner 修改。
另一個原生 agent 建立 native observer。Writer 負責文件、feedback 與整合。
兩者使用不同寫入路徑。沒有 Grok 或 Claude wrapper，也不宣稱多模型 review。

Model the Domain 原則讓 custody 判別集中在既有 owner 邊界。
Make Operations Idempotent 原則要求讀回原 intent，不重新發送未知效果。
Writing review 使用 review-writing、technical-writing 與 unslop。
Eval-audit 選擇 structured boolean comparisons，不使用未校準的模型 judge。

## 目前驗證紀錄

修改前的 exact base `advance_scope_amendment` 在真實停止後拒絕
`scope.process='stopped'`。原始輸出在 `/tmp/soodles-243-native/base-request-4/`。
這是原 production owner 的拒絕，不是 mock liveness。

Fixture 設定先暴露三個不同缺口。Local provider 缺 title。
Host config 沒有設定 ignored。啟動後的首次讀回仍位於 Python launcher。
Observer 保留各次 failure、cleanup 與 reassessment。
修正後，它等待 exact native argv，再呼叫原 production process reader。
第一個 current-source run 又暴露 raw envelope 缺 contract 的 `KeyError`。
這個錯誤屬於 implementation，須修正後才可建立成功證據。

最終 production bytes 的三個 native case 全部通過。
證據入口是 `/tmp/soodles-243-native/summary-final.json`。
每個 case 由 production `advance_scope_amendment` 驅動原 `ensure_noodle`。
以下是正常 fixture CLI。每次使用新的外部 output 目錄。

```text
python3 -B docs/experiments/failed-order-restart/observer.py /tmp/soodles-243-native/final-request --stop-after request
python3 -B docs/experiments/failed-order-restart/observer.py /tmp/soodles-243-native/final-edit --stop-after edit
python3 -B docs/experiments/failed-order-restart/observer.py /tmp/soodles-243-native/final-requeue --stop-after requeue
```

| 停止點 | 重啟前位置 | 原 held PID | replacement PID | 原 attempts | 最後 attempts | exit |
| --- | --- | --- | --- | --- | --- | --- |
| request-changes ACK 後 | failed | 47013 | 47914 | 2 | 3 | 0 |
| edit ACK 後 | edited | 46981 | 48264 | 2 | 3 | 0 |
| requeue ACK 後 | pending | 46880 | 48488 | 2 | 3 | 0 |

每案 release 前沒有 successor，release 後恰有一個 successor。
原 order、worktree、prior attempts 和四個 session hashes 保留。
每個 request、edit、requeue、release command 只有一個 ACK。
Fixture local provider 在完成一次 Issue patch 後回報 MutationUnknown。
下一次 owner 讀回既有結果，沒有第二次 patch。
Fixture 也保存尚未被 Soodles 消費的 ACK，重啟後接續同一 control identity。
這些結果不主張能恢復任意未知 start。
所有 fixture process 都已退出。Snapshot、request、ACK、stdout、stderr 與 cleanup
都保存在各 case 目錄。六個歷次故障及修正留在 `failure-history.json`。

Final native runs 後，review 移除 unit fixture 的未使用參數。
這項變更沒有改 production source、observer 或實際執行的 `native_successor`。
`/tmp/soodles-243-native/final-source-readback.json` 保存 bytes 與 AST 比對。
該小修再執行 16 個 admission revision controls，全數通過。

## Test Manager 與 software controls

`/tmp/soodles-243-work/test-plan-final.json` 記錄 Test Manager 的 focused selection。
新增 observer 原先回傳 needs_scope，現已映射到既有 admission revision controls。
CLI 執行 `./soodles test --base a2e6f36bdffa893c6d9d31ad31b4880551634d80`。
21 個受影響模組共 399 個 tests 通過。Process exit 為 0，wall time 為 108.357 秒。
這不是 full suite。原始輸出與 timing 在 `affected-tests.stdout`、
`affected-tests.stderr` 和 `affected-tests-process.json`。
測試選取中的 Linux physical controls 仍由後續 canonical acceptance 執行。
本次 native fixture 不替代該結果。

新增 controls 區分 failed、edited、pending，並拒絕 custody 值、review、session
四檔、candidate 和原歷史的漂移。它們拒絕 foreign 或 rejected ACK。
Unknown Popen 測試觀察先保存 offered intent，再拒絕第二次 spawn。
既有受影響 controls 另驗 live process group、foreign process、config drift、
unknown provider/control outcomes 和 carrier 身分。Software fixture 與 native
process fixture 的證據範圍保持分開。

## 獨立 review 與 P-class feedback

`/tmp/soodles-243-work/independent-review.md` 記錄原生 fresh-context review。
Review 未找到 blocking correctness defect。
兩項低優先事項已處理。Unit helper 的未使用參數已刪除。
Decision log 已串接後續 scope、native、feedback 與驗證證據。
工具沒有 Comment Sicko subtype，使用原生 comment/deslop review。
本紀錄不宣稱完成該 wrapper workflow 或多模型 review。

三份 P-class 文件的原 bytes 保存於 `/tmp/soodles-243-work/original/`。
Writer 重讀保存文字與 diff，確認 legacy 與 accepted native 的範圍分開。
Schema-2 protocol 固定全部三份保存文字、eval-audit method、原 requirements
與 stopped、unknown、legacy 三個 case。Consumer 均使用 `fork_turns: none`。
Consumer 僅接收 task、instructions 與 output paths，未收到 expected values。
Raw response、report、consumer trace 與 dispatch 記錄在 `pclass/`。
獨立 criteria reviewer 以原 requirements 的 exact quotes 支持 12 個欄位。
Writer 檢查 raw rationale，未發現與 structured outputs 矛盾。

第一次 stage feedback 因 requirements identity 不符而拒絕。
原 Issue 正文的兩個 path 陣列順序不同於 validated admitted prompt。
Writer 從原 running session 的 `worker_context` 取得正確 binding。
新 protocol 只修 requirements 引用。所有 instructions、inputs、expected
與 observations 保持原 bytes。獨立 reviewer 核對後綁定新 protocol。
舊 protocol、拒絕和修正原因都保留，沒有把 missing evidence 計為 behavior FAIL。

原 `./stage-outcome feedback` 已記錄 round 1。
Schema Manager 回傳 evidence VALID、criteria SUPPORTED、behavior PASS。
Test Manager verified cases 為 stopped、unknown、legacy，無追加 observation。
Writer 已消費 `next.operation=consume_verified_behavior`。
`pclass/feedback-v2.stdout` 保存 owner response，`pclass/consumed.json` 保存 readback。
Schema validation/projection 共 6.663 ms，其中 decision projection 為 0.0645 ms。
這兩個數值為巢狀測量，不相加。Model 時間和 tokens 未提供，保持 unknown。
PASS 僅支持這三個 consumer reports，不授權 stage completion 或 landing。

## 證據限制與後續 owners

工程 fixture 不呼叫模型或 live provider write。
其 provider-shaped 回覆只屬於 disposable fixture。
保存的 observations 不證明 live Issue 恢復或 Linux acceptance。
Fresh consumer reports 只支持指定 inputs 與保存文字。
Capture 不是完整 platform transcript。不主張全域最短路徑、speedup 或一般成功率。

Writer 完成後只 commit 並回報原 typed stage outcome。
Publication、exact-head Linux CI、landing 與 local Git/Noodle reconciliation
仍由 supervisor 沿原 owners 完成。
既有 resolved #235 保留為歷史證據，不重新開啟。
所有本地證據的 `authorizes_landing` 都是 false。

## 指定 base advance 的接續

Publication owner 因 provider main 前進而拒絕原 candidate `e8cdabc`。
Supervisor 隨後接納 exact target
`5b0a73eae31fb414deeed4ffdf8082a71aee4e3d`。
Writer 在原 worktree 合併此 target，保留原 candidate commit 與失敗 attempt。
Revision context 位於
`/Users/neon/soodles-audits/failed-order-restart/base-revision/admission/revision-entry.json`。
Writer 驗證其 SHA-256 為
`881bdeb7b114ba84279aa90970ceea24b5d9bed55079172fc51ef18cd75f786d`。
本段的工作紀錄與 receipts 位於 `/tmp/soodles-243-base-integration/`。

Git 自動合併沒有衝突。新基底只在 `issue_atom.py` 加入或修改
`original_host_plan` 與 `resume_host_finalization`。
它也修改 `schema_manager.compile_plan`，使原 host plan 可從固定 Git bytes 編譯。
`source-comparison.json` 記錄 AST 與 hash 比對。
本次 stopped continuation 的函式、module statements、`issue_execution.py`
與 native observer 均保留原內容。
因此本次沒有重新設計 restart，也沒有新增 native process 實驗。
前面的三個 native case 仍是原 source 的觀察，不能改稱本次合併 head 的執行。
合併後的 software controls 另外驗證目前 source 與 host plan consumer。

原 Feature 計畫保留。Writer 單獨處理 Git 與 N-class 證據。
獨立原生 reviewer 只讀取 source，並寫入外部 review 紀錄。
此 carrier 沒有 Grok、Claude 或 Comment Sicko wrapper。
本次使用原生 review，不宣稱多模型或指定 wrapper 驗證。
`methods.json` 與 `plan.md` 保存方法身分、工作分配及 writer 停止點。

目前 admission 的 task 與原 task 相同。
Contract 只有 `base_head` 改變。
三份 P-class 指令、三個 case inputs、expected values 與 eval method 均未改變。
獨立 reviewer 重新以目前 requirements 核對全部 12 個條件。
`criteria-review.json` 綁定新 protocol，原 consumer reports 與 raw responses 保留。
Writer 沒有把重用觀察稱為新 consumer 執行。
本 session 的 `./stage-outcome feedback` 回傳 VALID、SUPPORTED 與 PASS。
Test Manager verified stopped、unknown、legacy，沒有要求新 observations。
Writer 已消費 `consume_verified_behavior`。
`feedback.stdout` 與 `consumed.json` 保存 response、digest、next 與採取的行動。
此 PASS 只支持原案例的指令行為，不授權 publication 或 landing。

Test Manager 對指定 target 選取 21 個受影響模組，共 407 個 tests。
Writer 另選 `test_schema_manager` 的 17 個 controls，驗證合併後的 host plan reader。
此 CLI 的 `--module` 會使用明列範圍，不會附加 base 自動選取的模組。
因此兩組範圍分開執行，未使用 full suite。

首次受影響模組執行中，9 個模組留下完整 PASS 紀錄。
`test_interruption_recovery` 留下 exit 1，但詳細輸出仍在 manager buffer。
工具隨後回報整個執行程序 exit 143，manager 未寫出最後 receipt。
Writer 沒有取得 SIGTERM 原因或該模組的首次失敗診斷。
`interrupted-run.json` 與原 stdout、stderr 保留這個缺口。

Writer 先隔離執行該失敗模組，13 個 tests 全數通過。
接著只執行尚無完整觀察的 11 個模組，全部通過。
兩次執行均保留 stdout、stderr、exit code 與 process receipt。
`verification-summary.json` 將原 9 個 PASS、單模組診斷與後續 11 個 PASS
連回 Test Manager 的完整選取，合計 407 個 tests。
另有 17 個 schema controls 通過，總計覆蓋 22 個模組、424 個 tests。
這是多次執行的觀察聯集，不是首次中斷執行的 PASS。
後續成功不解釋原失敗原因，也不刪除失敗歷史。

獨立 review 未發現合併引入的 correctness、comment 或 deslop 缺陷。
`independent-review.md` 保存 source 判斷與當時尚待補足的驗證範圍。
本次不修改 publication、judge、carrier 或原 owner 的交付權限。
Supervisor 仍須執行 exact-head Linux acceptance，並沿原 owner 完成後續交付。
