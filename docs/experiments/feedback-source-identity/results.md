# #253 驗證結果

本記錄是 N-class 證據。它記錄本機 discriminator 行為，不授予 landing 權限。
基底為 `cc0d235d0248947dd117a31c37f0a1d62924b4de`。
基底 `stage_outcome.py` 的 SHA-256 為 `74db56a7da5a157a0ef02ebc17968439ca758176b10090d34bd72297e85c5e56`。

## 原始故障證據

原證據目錄為 `/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/writer-229-ci-base/feedback`。
本次先讀取 admission 指定的 `feedback-source-owner/context.json`。
本次也重讀下列檔案，並確認其摘要與 context 相符。
原始檔案沒有修改。

| 原檔案 | 已驗證 SHA-256 |
| --- | --- |
| `reuse-response.json` | `da857e16c0ca9e34c534e451c864e3018c1cf315d5c64e228b1ed025782d6214` |
| `reuse-invocation.json` | `8fa04b139dfa8c87073d4d38d2d7925c857598011655987a95bdd3dd3669b057` |
| `completion-coverage.json` | `026dcc5ca862988685fa31fd4ab5f604afa67f22e075406a140487c08aee182a` |
| `protocol-prior-paths.json` | `3f5c54d605ccd5e1e3349fb476c42ab7878fa2de4a604290b4607c01ec49c509` |
| `selection-prior-paths.json` | `2527a62c396d684a6e4b30485b1b58cc27d65e8e447af2009c6dec445b0e8c12` |

原 feedback 的 `external_entries`、`scope_and_acceptance`、`unknown_write_schedule`、`legacy_launcher` 均為 passed。
整體結果為 `SUPPORTED / VALID / PASS`。
原 coverage receipt 以 `worker.feedback.coverage` 拒絕目前 worktree 的 13 個指引。
context 記錄這 13 個相對路徑的 source 與 current bytes 相同。
這是原故障證據，不是 #229 在新 source 上的 completion 讀回。

## 公開入口重現

本次使用 `tests/test_feedback_owner.py` 既有的小型 Git 與 owner fixture。
fixture 建立兩個已註冊 worktree，在相同相對路徑寫入相同指引。
fixture 透過 `stage-outcome feedback` 記錄原 PASS，再透過 `stage-outcome completed` 嘗試完成。
fixture 使用事件 writer sentinel，不會操作 live Noodle order 或 GitHub。

修正前的實際結果如下。這些值摘自保存的 JSON。

```text
feedback_exit=0
criteria=SUPPORTED
validity=VALID
behavior=PASS
completion_exit=1
status=refused
invalid.field=worker.feedback.coverage
```

新增的正向 regression test 也先執行失敗。
失敗輸出保存在 `soodles-253-worktree-positive-test.log`。

```text
Ran 1 test in 1.067s

FAILED (failures=1)
```

同一重現程式在修正後取得以下結果。

```text
feedback_exit=0
criteria=SUPPORTED
validity=VALID
behavior=PASS
completion_exit=0
status=recorded
```

正向測試另檢查 selection、protocol、instruction、requirements、method、input、criteria review、report 與 trace 的 bytes 完全不變。

## Test Manager 範圍與結果

本次執行以下選定範圍。

```sh
./soodles test --module test_feedback_owner --module test_stage_outcome --module test_pclass_feedback --module test_candidate_verification --reason 'Issue 253 completion coverage, preserved validation, and required candidate manifest'
```

Test Manager 回傳 `ready`，模式為 `focused`。
共 44 個測試通過，exit 為 0，wall time 為 20.586 秒。
沒有執行 physical controls、full suite 或新模型 cases。
這段時間是本次正常本機測試成本。它不是效能比較。

最終自動 mapping 另選出 `test_admission_revision` 與 `test_atom_feedback`。
它們分別覆蓋原 revision bundle 與 feedback fixture consumers。
本次只補跑這兩個模組，沿用前四個模組的結果。
追加 30 個測試通過，exit 為 0，wall time 為 28.125 秒。
六個模組共 74 個測試通過。兩次測試執行沒有重複模組。
完整選擇保存在 `final-test-plan.json`。

```sh
./soodles test --module test_admission_revision --module test_atom_feedback --reason 'Final Test Manager mapping adds revision bundle and feedback fixture consumers; reuse four completed modules'
```

新增 controls 實際檢查以下邊界。

| 輸入 | 結果 |
| --- | --- |
| 同一絕對路徑 | completed |
| 同 repository 的已註冊 worktree、相同相對路徑與 bytes | completed，原證據不變 |
| 相同 basename 與 bytes，但相對路徑不同 | `worker.feedback.coverage` |
| 無關 repository 中的相同相對路徑與 bytes | `worker.feedback.coverage` |
| 複製 `.git` 指標的未註冊目錄 | `worker.feedback.coverage` |
| 已註冊 root 內的巢狀 foreign repository | `worker.feedback.coverage` |
| 目前 target bytes 改變 | `worker.feedback.coverage` |
| 合法搬移之外，另有未覆蓋的 changed P 檔案 | refusal 只列未覆蓋檔案 |
| 原 instruction 遺失，或 report、trace、input 被改寫 | `worker.feedback.incomplete` |
| report instruction map 或 input digest 與 protocol 不符 | `worker.feedback.input`，原因為 `report.identity` |
| protocol 的 task 或 contract 不同於 admission | `worker.feedback.requirements` |

既有 controls 繼續檢查 criteria 修正、behavior failure、原 instruction bytes 變更、event 身分與 outcome 唯一性。
測試結果沒有建立新的 Agent 行為主張。

## 方法與證據保存

本次使用選定 execute、Poteto Bug Fix、how、architect、arena、TDD 與 control-cli 方法。
兩個獨立設計與交叉評審使用 host `inherit-parent` 設定。
它們具有獨立 context，但不是跨模型比較。
本次以公開 CLI 的小型 fixture 落實 Test Behavior, Not Implementation 與 Prove It Works 原則。
technical-writing 與 unslop 用於說明。
source review 也涵蓋 deslop 與新增註解檢查。
獨立 source review 結果為 clean，沒有待修 correctness 或測試品質問題。
新增註解由 native reviewer 檢查。carrier 未提供 typed Comment Sicko Task，未宣稱使用該工具。
本次沒有新增 workaround、suppression 或約束式註解。

原始 source 與 receipts 已充分定位原因，因此不另啟動歷史調查或模型觀測。
失敗測試保存在外部證據中，不提交不能通過的中間版本。
這符合 repository 的每次提交可驗證要求。
publication 與 landing 沒有轉交 writer。

工作記錄、skill 路徑及其 SHA-256、完整重現輸出與測試 logs 保存在 `/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/soodles-253-evidence-f7yi74lb`。
以下摘要綁定本次原始輸出。

| 保存檔案 | SHA-256 |
| --- | --- |
| `original-context.json` | `775a062f9ff1df44aacb7d50f818e739deb06d7603931858da2905051bc2ad10` |
| `before.json` | `d951d78c077c430a78bf1b0b4e889d68a4f91655729f389e8981b9d25c6a1ed2` |
| `after-source.json` | `25b5b54963f7cf711e5bb5c1060787fec7e47aa88353f7daf0cabdaf352ea349` |
| `tests-stdout.json` | `7c4549707f8a55991093dfaa55a1af5ee922afb46398b1f170a1a52172213caf` |
| `tests-stderr.txt` | `191461d18993cde92afea94f091356dae1414f63350e65659ad04378bd1b0b50` |
| `soodles-253-worktree-positive-test.log` | `9e114cba45f35972fb1a09d19c6d1aebe3898272a76cefdd24ef6edeb948ee27` |
| `consumer-tests-stdout.json` | `5f012907a81808e21ab846b560afdfc3a9a69ca085a1a30333ddaefb01fd81ff` |
| `consumer-tests-stderr.txt` | `75932aa7b0174fc261da366080eebae20e09030cd2f8b26e45298abda81310bd` |
| `final-test-plan.json` | `f01124b456028636c142d76f33d488bd239d7f6a6b6c5fc696026f6b04ffcaaa` |
| `soodles-253-review.md` | `6d6b667afa850aa73e96e5a7bd8de3c57abb596ba66d730c6eaa0a52c70029f5` |

## 尚未建立的結果

本次沒有修改 P-class 指引，因此沒有新 P-class writing 或模型行為 claim。
本機測試不能代表精確 PR 的 Linux CI、landing 或 local reconciliation。
本次沒有對 live #229、#239、#245、#247 的 authorization、order、worktree 或 publication 寫入。
原 parent owner 仍需完成 #253 交付，再沿 #229 原 continuation 讀回實際 completion 與完整使用者成果。
