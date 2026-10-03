# Current-base source 整合結果

本文件記錄 ed3c/soodles#256 的 writer 結果。它是 N-class 證據，不授予 delivery 權限。

## Source 與保留的歷史

本次 writer 在 Noodle worktree `soodles-256-e16fb006ac06-0-execute` 工作。
起點是 accepted generic factory `2fdc87afdb21d1512dab67da93bfea41939dc530`。
合併來源是 `d5cf7f7585f7eb76b4538827e4f389b5cad26dc1`。
Git 自動合併成功，沒有 conflict。
Merge 保留 generic factory 與外部修正的兩邊歷史。

外部 source 的首個 commit 是 `351224b24054e11887edd5ba2de19f199845cb7c`。
它曾把 local base 推論擴大到 cloud。
後續 `d5cf7f7` 保留 cloud 原 admission 條件。
本次合併包含兩個 commit，沒有只挑首個修正。

既有 criterion review 保存 #229 的拒絕與原始 provider 身分。
既有 source review 保存首次 157-test pass 的限制，以及 cloud 範圍修正後的 12-test pass。
原 handoff 的 146 個 unchanged controls 加 12 個 supervisor controls 是當時 source 的覆蓋。
本次 generic source 不同，不能把這些歷史結果直接算成本次 pass。
Writer 重用根因、設計與失敗歷史，另驗 generic 整合。

以下原始失敗文字來自既有 source review。本次沒有重跑 #229。

```text
REFUSED: landing.start: invalid base.head='cccccccccccccccccccccccccccccccccccccccc'
```

## 方法與本次驗證

本次使用 selected execute 與 Poteto Bug fix 小迴圈。
使用者已固定修正與 source，因此略過重新 reproduction、binary search 與 architecture exploration。
一個 implementation delegate 執行合併與 fixture 補強。
另一個無繼承對話的 native reviewer 檢查 saved diff。
主 writer 自審並保留所有效果給原 owners。
方法路徑、SHA-256、選擇理由與停止點記錄在外部 `work-record.json`。

Test Manager 以明確的 observed-behavior reason 選擇以下模組。
選擇結果為 `focused`，`unresolved` 與 `physical` 都是空陣列。
沒有執行 full suite、model eval 或 provider mutation。

| 模組 | 有效通過數 | 本次證據 |
| --- | ---: | --- |
| `test_landing` | 51 | 首次 run，source 未再變更。 |
| `test_landing_continuation` | 1 | 首次 run，source 未再變更。 |
| `test_issue_atom` | 94 | 首次 run，保留 adoption 與 offered-write 拒絕控制。 |
| `test_generic_repository_binding` | 19 | 首次 run，保留 generic target 與 runtime owner 控制。 |
| `test_candidate_verification` | 3 | 首次 run，驗既有 manifest discriminator。 |
| `test_landing_supervisor` | 13 | Fixture 修正後的 affected run。 |

有效覆蓋合計 181 個 controls。
首次 run 執行 181 個 cases，exit 為 1，runner wall time 為 82.368 秒。
其中五個模組的 168 個 cases 通過，supervisor 模組有一個 error。
修正後只重跑 supervisor 的 13 個 cases，exit 為 0，runner wall time 為 4.794 秒。
這些是正常執行的觀察值，不是 benchmark 或效能改善比較。
平行模組秒數不能相加後當成 wall time。
Token、價格與跨 repo 並行節省時間未量測。

Generic 新控制使用自訂 `trunk`、workflow 與 job。
它讓 PR 內嵌 base 保持歷史值，再經 producer 與複製的 publisher 執行 `prepare`、`landing.start`。
控制確認 claim 保留 target binding、execution envelope reference 與目前 base。
它也確認 snapshot、保存的 readback 與 envelope 未被改寫。
這個控制不執行 runtime argv。
既有 generic 模組另覆蓋 external test/outcome entry 與第二個 target 的 delivery owners。

既有 continuation control 在歷史 PR base 下通過 start、advance 與 dispatch。
它確認未知 write 結果不會產生重複效果。
錯 repo/ref、native base、head/tree/CI、真正 branch drift 與 cloud drift 的拒絕控制均保留。
這些都是 disposable fixture 的結果，沒有發送 live provider write。

## 一次 fixture 修正與 review 限制

新 generic fixture 初版將 runtime argv 指向 candidate 目錄。
原 `load_external_envelope` 要求 entry 位於 envelope 的同一外部 bundle。
實際 publisher 拒絕如下。

```text
REFUSED: landing.start: invalid envelope.runtime.bundle='foreign_entry'
```

Writer 只把 fixture 的兩個路徑改成 `envelope_path.parent / "stage-outcome"` 與 `/ "test"`。
產品 source 與 validator 不變。
Affected run 的原始結尾如下。

```text
Ran 13 tests in 4.661s

OK
```

首次獨立 source review 沒有查出這個 fixture 約束錯誤。
Review 已保留首輪結論、實際失敗、漏查原因與修正後的來源檢查。
主 writer 不把靜態 review 當作執行證據。
五個先前通過模組的 source/input hashes 未變，也沒有 import 修改後的 supervisor fixture。
因此它們的 168 個結果仍可重用。
原失敗 log 不覆寫，修正結果另存。

主 writer 的 saved diff 自審確認 production delta 與指定的外部修正相同。
Generic target binding、selected profile、runtime entry 與 effect custody 沒有被替換。
No-comments 與 deslop review 沒有新增 findings。
變更沒有新增或修改 code comment、docstring 或 suppression。
獨立 review 的結果限於已保存的 source 範圍。

## Owner 與完成界線

本次 order 是 `soodles-256-e16fb006ac06`。
原 Noodle session 是 `soodles-256-e16fb006ac06-0-execute-20261003-171327-7d0464`。
Normal session/event log 仍由 Noodle 保存。
Writer 將使用原 admission launcher 的 `stage-outcome` entry 回報。
回報後，stage receipt 將另存於本次外部證據目錄。
實際結果以該 receipt 為準。

本文件與 manifest 不宣稱本 Issue 已通過 exact-head Linux CI 或已解決。
Publication、CI、merge、Issue closure 與 Git/Noodle reconciliation 由原 parent 及 owners 接續。
本次 writer 沒有修改 #229 的 frozen publisher、authorization 或 raw provider data。
它也沒有操作 medium target，或宣稱 medium replay、Production 與所有歷史 helper 已完成。

## 證據索引

歷史證據根目錄是 `/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery`。
本次證據根目錄是 `/Users/neon/.codex/experiments/current-base-landing-256-94dwjvm_`。
這些絕對路徑是本機觀察紀錄，不是可攜式 delivery authority。
Repository manifest 綁定本 candidate 的七個 source、test 與說明檔。
Manifest 不把外部歷史結果升級為本 candidate 的 provider acceptance。

| 證據檔案 | SHA-256 |
| --- | --- |
| `landing-pr-base-criterion-review.json` | `b7228057b8a838a75ba7bf0a85875b417b17ae5e3d3097701967f64e2147a1ba` |
| `landing-base-correction-writer/handoff.json` | `eb4f95e6e47f049e3f541d9647d99d315494ccf32156e5efcd0debf06a989574` |
| `landing-base-correction-writer/source-review.json` | `4ec57aced7f3747aa23b1393287a35187c81c5cf9c0fad06dd008b13d9e51d20` |
| `test-plan.json` | `0b312ed86a9b386af680f1495cf792c82a95710a41be8eaa038a0a9ac177d793` |
| `test-receipt.json` | `55aa6017d178624127da73f668a25a6573c74ee82e4aab47924a8f52aebbbc6e` |
| `tests.stdout` | `86d10b2846b51a7ec70f7b820696ed5a43c0ab291ee492f62e8543123020fca7` |
| `tests.stderr` | `237154038b11c4739ece17685b7efe0bd53be2b0eaa1ee5512aae2607839df68` |
| `correction-receipt.json` | `9fb15117c5c164037ada3ae4aa43041eb4015890d0a90756250a13f67ad4865e` |
| `correction.stdout` | `d3d06617d00085bd913fe889e4f7cb775790080ade3ce3809a8934907fba49be` |
| `correction.stderr` | `78c7c9686ca533290e85d0355cb4be5b0ecbfac5ef5ca9edf69cee9be59c1f13` |
| `current-evidence-reuse.json` | `bae158c4c6c659264a8e77353d4bb29e659aa1f9dfd2f36e9750964c27ebc7d0` |
