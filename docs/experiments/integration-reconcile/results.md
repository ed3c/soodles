# Integration reconciliation 修正紀錄

本紀錄屬於 N-class。範圍是 `ed3c/soodles#260` 的 local reconciliation。
本次 base 是 `67e477864a69c233f2e3d98b37d25143362e3c3b`。
base 的 `landing.py` SHA-256 是 `76f73a22874320bde07ca68c1da3f5499499018e5ddd7aff4b2ebacc6acca5ce`。
本文與 candidate 自測均不授予 publication 或 landing 權限。

## 原主張、證據與根因

原主張是 cleanup 拒絕可能只因 frozen publisher 沒有啟用已接受的新功能。
這個主張假設 accepted source 已能同步 local integration branch。
來源核對否定了這個前提。

`external-owner/landing.py` 第 918 行只在 `claim.control_root` 執行 FF。
`04032d233f7f286e485ce9d20a9ad7254d12f167:landing.py` 第 933 行也做同一操作。
本次 base 的檔案與該 accepted source 有相同 SHA-256。
同檔的 `cleanup_integration` 讀取 `refs/heads/<base_ref>`。
當 control 是 detached worktree 時，control HEAD 前進不會更新該 branch。
因此，缺少的行為屬於 reconciliation source。它不是既有功能的 activation 問題。

原始 owner 證據保存在下列外部目錄。
共同根目錄是 `/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery`。

- `landing-base-product-owner/prepared/authorization.json.d/landing-reconcile-xoj85le0.json` 記錄 #256 cleanup 的 unmerged commits 拒絕。exit status 是 1。
- 同目錄的 `landing-reconcile-485xb0bl.json` 記錄後續 `phase=resolved`。merge SHA 是 `04032d233f7f286e485ce9d20a9ad7254d12f167`，exit status 是 0。
- `pending-stage-correction/prepared/authorization.json.d/landing-reconcile-cexul6i5.json` 記錄 #258 的同類拒絕。
- `pending-stage-correction/reconcile-main-intent.json` 固定 main 的 before、target 和已合併 PR259。
- `pending-stage-correction/reconcile-main-readback.json` 記錄實際 FF 成功。main 到達本次 base，branch 仍為 main，status 為空。
- 同次 owner 的 `landing-reconcile-pzc7hh7m.json` 記錄 `phase=resolved`。

#256 的兩份 receipt 證明先拒絕、後 resolved。它們本身不是人工 FF 的完整 shell transcript。
#258 另有 FF 的 process result 和 checkout readback。
本次只讀取原始資料，沒有重演 live atom。

## 設計選擇與執行邊界

以下執行路徑由本次 candidate source 追蹤。實測範圍另列於驗證結果。

要求是讓原 owner 完成合法同步，再由 Noodle 判斷 cleanup。
重送 cleanup 仍會讀到舊 integration ref，不能修正根因。
force cleanup 會移除原 ancestor guard，也不符合要求。
因此，同步操作放在原 `landing.reconcile`，沿用原 checkpoint。
沒有新增 Git manager、scheduler、retry engine 或 authority flag。

資料形狀沿用設計中的 `integration_sync`。
它固定 checkout、common directory、integration ref、before head、target head 和 confirmed merge。
狀態區分 intent 與 confirmed。confirmed 表示完整 readback 已觀察到目標狀態。
checkpoint 不將這個觀察標為本次 process 的因果證明。
這是 Model the Domain 原則在本次的具體選擇。

reconcile 讀取原 claim、execution envelope 和已確認 provider 結果。
它 fetch 原 base ref，固定當次 target SHA。
原 order 必須 completed，相關 sessions 必須 quiescent。
Noodle readback 尚未滿足條件時，owner 保留原 continuation，停止同步和 cleanup。

owner 從 control 的 common directory 和 Git worktree registry 找唯一 base checkout。
它檢查 repository origin、common directory、checkout root、branch、HEAD 和 ref。
它也檢查 tracked、untracked、registration、lock 和 ancestry。
它不接受 Agent 另給 path 或 ref。
before 必須是 target 的 ancestor，target 必須包含 confirmed merge。

owner 先保存 exact intent，才在該 checkout 執行 exact SHA 的 `git merge --ff-only`。
它不切 primary branch，不 reset、force、刪 lock 或以 update-ref 修改 checked-out branch。
完整 readback 確認 target 後，owner 保存 confirmed，再交原 Noodle cleanup。
原 cleanup intent、unchanged observation、ref-lock 和 unmerged guards 仍負責各自的拒絕。

有 intent 而沒有確定 process result 時，before head 未變仍屬未知。
舊設計檔的一句話允許此時重送。該推論缺少命令從未執行的證據。
本次以 Issue 的明確要求修正它，未知結果不重送。
若 readback 已是乾淨 exact target，owner 可記錄已觀察的完成。
這個觀察不證明狀態一定由先前命令造成。
若 binding、target、checkout 或 bytes 改變，owner 保留原 intent 並具名拒絕。

## 方法與限制

本次採用 execute 選定的 Poteto Bug Fix。
已完成的 how、根因與設計來自 `full-autopilot-boundary-design.json`。
使用者要求沿該設計實作，因此沒有重做 bakeoff 或模型 eval。
實作與 fixture 分別委派。root 負責來源自審、測試結果和 manifest。
獨立 reviewer 使用原生 subagent，沒有繼承聊天。
目前 carrier 沒有 Comment Sicko 的專用 subagent type，不能宣稱執行過該 specialist。
一般獨立 review 仍包含新增註解與可讀性檢查。

完整工作紀錄保存在 `integration-reconcile-correction/writer-260`。
它記錄實際 skill 路徑、SHA-256、playbook 步驟、適用例外與原始 evidence digests。
執行次序是實作與 fixture、必要 controls、獨立 review、manifest 驗證、commit、stage outcome。
沒有提交失敗測試的中間版本。

## 驗證結果

執行命令是 `./soodles test --base 67e477864a69c233f2e3d98b37d25143362e3c3b`。
Test Manager 選出 12 個 unit modules，共 255 個 cases。
最終 exit 是 0。所有 modules 都回報 `complete=true`。
正常執行記錄為 4 workers、81.253 秒，discovery 另記 0.241 秒。
`test_landing` 的 67 cases 用時 63.066 秒。
`test_cleanup_continuation` 的 11 cases 用時 25.111 秒。
這些 module 時間互有重疊，不能相加作為總延遲。
raw case logs 包含 setup、body、teardown 和 cleanup。
本次没有 benchmark、成本改善比例或 Agent 決策數比較。
新 FF 的獨立耗時、model 成本和未來 provider 耗時未量測。

最終完整 raw logs 是外部工作目錄的 `tests-final.stdout` 和 `tests-final.stderr`。
`test-run-final.json` 固定最終 source hashes 與 raw log digests。
首輪 `test-run.json` 與 `tests.stderr` 保留 6 個失敗。
根因是新增 fixture 未統一路徑，macOS `/var` 和 `/private/var` 比較不同。
這也使兩個中斷攔截沒有命中預定 checkout。
修正只在新 fixture 的 primary 和 foreign root 呼叫 `.resolve()`。
既有 shared helper 與驗收條件不變。
第二輪收到終止訊號，tool 回報 exit 143。原因未知。
`test-run-interrupted.json` 保留此限制及沒有殘留測試程序的 readback。
第三輪使用同一必要 scope，取得上述完整 PASS。
這些紀錄不把 fixture 修正前的失敗當成本次產品 defect 的 RED 證據。
產品根因仍由原 owner receipts 與 pinned source 支持。

最近 controls 觀察到以下行為。

- 真實 Git fixture 建立 merge commit。primary main 落後，detached control 已到 target。reconcile 同步 main 一次，再經 fixture 的實際 Git ancestor guard 完成 cleanup。primary branch 與 detached 身份不變。
- primary 已到 target 時不重送 FF。control 本身是 integration checkout 時只執行一次 FF。
- generic `trunk` 使用 binding 選定的 base ref。legacy fetch callback 保持一參數。既有 cloud controls 仍通過。
- 原 order 未完成或 sessions 未 quiescent 時，integration 和 control 均沒有 FF 或 cleanup。
- tracked 或 untracked bytes、foreign origin 或 common directory、缺失、多義、locked 或錯 branch 的 registry、divergence、缺失 confirmed merge 皆拒絕。相關 bytes 和 refs 保持原值。
- intent-only 且 HEAD 仍是 before 時拒絕重送。FF 完成但 acknowledgement 遺失時，readback 記錄 observed confirmed，不重送。
- target、checkout 或 immutable binding bytes 漂移時拒絕，原 intent 與 history 保留。
- cleanup unknown observation 不重派。原 ref-lock 解除後可接續。candidate 不在 integration ancestry 中時，原 guard 仍拒絕。

fixture 使用真實 Git checkout、refs、檔案和 FF。
provider、carrier 與新 fixture 的 original-order readback 使用測試替身。
planted registry 輸出覆蓋無法由正常 Git 命令建立的錯誤 registration。
cleanup adapter 執行真實 ancestor、worktree remove 與 branch delete。
它不是本次實際 Noodle binary 的 physical acceptance。
原有 BoundLandingTests 和 issue-atom controls 另涵蓋既有 owner 消費行為。

Test Manager 既有 mapping 已涵蓋此次差異，因此 `test_manager.py` 沒有變更。
選出的 `cleanup_recovery`、`cleanup_lock_recovery`、`delivery_recovery` 和 `base_recovery` 留待 canonical acceptance。
本次 local unit PASS 不代表這四個 physical controls 已執行。

root 已完成 source 自審與 deslop 檢查。
獨立 reviewer 初次指出文件誤稱保存 process result，已改為 observed completion。
後續 review 確認 ancestry refusal 的欄位缺口。
修正加入 `integration_sync.ancestry` 與 `reconcile.merge_ancestry` 等具名診斷。
錯誤仍保留 ancestor、target 和原始 Git error，沒有把所有 Git 錯誤稱為 divergence。
現有 negative controls 已驗確切 field 與 bytes、refs 不變。
`review.json` 保存 finding、修正歷史、最終 source hashes 和 clean 結論。
N-class 文字另按 review-writing 檢查 actor、條件、因果、觀察與未知邊界。
沒有 P-class guidance 修改，也沒有新增 eval。

manifest 使用既有六鍵 schema。
`instructions` 綁定 `landing.py` 的 base 和 treatment hashes。
`artifacts` 綁定兩個實際改動的 test 檔與本文件。
manifest 不列未修改的 `test_manager.py`。
提交前，`issue_admission.validate_delivery_paths` 對 provisional Git tree 驗证完整路徑與 hashes。
該 receipt 保存在外部工作目錄的 `manifest-validation.json`。
它的 `authorizes_landing` 是 false。

## 後續 owner 與 activation

writer 只交 clean committed candidate 與 stage outcome。
原 supervisor 和固定外部 owner 仍負責 publication、Linux exact-head CI、merge、closure 及 Git/Noodle reconciliation。
本次不修改外部 publisher、oracle、authorization 或 credentials。
若本次固定 publisher 仍缺少同步能力，原 owner 依既有授權處理，並保留限制。
候選來源通過測試不代表本次已由新 owner 自動完成 delivery。
接受後，supervisor 才能為後續合法 activation 固定新版 owner bytes。
本修正不建立 parent 的 medium replay、持久使用或 Production 成果。
