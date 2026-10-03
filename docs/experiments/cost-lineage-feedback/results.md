# #248 成本 lineage 修正紀錄

本紀錄屬 N-class。它記錄已觀察的行為，不授予 publication 或 landing 權限。
本單位修正已接受 base revision 後的成本讀取，並接回同一 CLI 的 Manager 回饋。
完整 CLI 契約、歷次 attempt 成本、其他 consumer 整合及決策量測仍屬 parent task。

## 原錯誤與設計理由

原程式要求 publication claim base 等於 immutable cost subject base。
這個條件假設原 owner 不會接受新的 base。
#243 已接受 typed `base_advance`，因此這個假設不成立。
原 subject base 是 `a2e6f36bdffa893c6d9d31ad31b4880551634d80`。
已接受 target base 是 `5b0a73eae31fb414deeed4ffdf8082a71aee4e3d`。
原正式 CLI 回傳 exit `1`，拒絕原因為 `cost.claim_base`。

成本 subject 用來歸屬舊觀測。它必須保留原 authorization digest、repository、Issue 與 base。
claim base 則必須符合原 owner 已接受的有效 lineage。
直接改 subject 或刪除 base check 會破壞這兩個要求。
`scope_projection` 會在 release 前投影 future target，不能當成 accepted lineage reader。

本次沿用 supervisor 的兩案比較，選擇由原 `issue_atom` owner 提供唯讀 reader。
owner 共用既有 released history 驗證，成本 consumer 只比對驗證後的 base。
候選 B 建議另存 publication binding，但現有 #243 沒有完整 binding。
採 B 仍需重建原 lineage，且會增加保存格式。因此本次不採 B。
#243 的 candidate worktree 已清理，reader 不得依賴它仍存在。

## 執行時的檢查與回應

`cost_telemetry.report` 先由原 authorization bytes 建立 subject，再讀取原成本 observations。
遇到 claim 時，`external` 呼叫 `issue_atom.accepted_claim_lineage`。
reader 驗證原 authorization，依序套用已 release 的歷史 entry，再處理目前已 release 的 entry。
尚未 release 的 target 不改變 accepted base。
共用 validator 檢查 selection digest、原 authorization、prepared ref、typed selection、Issue body 前後 hash 與 control ACK。
同一 command ID 必須只有一筆 ACK，且 action 與 `status=ok` 相符。
目前 ACK 取自原 control root，歷史 ACK 取自原 owner 已封存的 entry。
後來的無關 ACK 不影響這些 exact IDs。
成本 reader 最後將 claim base 與 accepted base 作嚴格比較，沒有改寫 subject。

source 缺失、digest 漂移、衝突 ACK、斷裂 body chain 或錯誤 base 會拒絕。
這些拒絕保留診斷，不會修改 state、取得寫鎖或執行 provider operation。
prepared `base_recovery` 屬不同 acceptance 邊界，本 reader 不把它當成 typed release 證明。
報告結束前再次檢查必要 snapshot，避免把讀取期間已改變的 state 當作一致證據。

`project` 沿用 Test Manager `review_cost` 與 Schema Manager `project_cost`。
同一 report 將經驗證的 owner result 傳給 `project_owner_feedback`，回傳原 `next` 與 DAG。
正常 atom 重用本次 feedback。telemetry 拒絕時仍走原 Schema fallback，不改 owner continuation。
manifest 缺 owner result 時，Schema Manager 保持 owner transition unknown。
報告不從成本狀態或 state phase 推導 resolved，也不執行 next。

## 方法與工作分工

工程入口為 selected `execute`，方法為 Poteto Mode Bug fix。
原正式 CLI failure 與 `cost.md` 已建立相同故障與輸入，本次重用證據。
`how` 與 `architect` 使用原 source grounding、兩案與 synthesis。
native source reviewer 再核對 owner、歷史與 consumer。
implementation delegate 修改 source 及必要控制，writer 負責正式 readback、文件、review 與提交。
本次使用 native 同模型 delegation。未提供 upstream Grok 或 Claude wrapper，也未宣稱多模型審查。
`technical-writing` 與 `unslop` 用於此紀錄。`deslop` 與 native comment review 用於候選 diff。
未修改 P-class 指引，未新增 Agent eval 或測量實驗。

`Model the Domain` 促使實作分開 immutable subject 與 accepted base。
`Prove It Works` 要求回到原正式 CLI 讀取相同保存輸入。
Bug fix 的 failing-commit 步驟不適用，repository 禁止提交失敗候選。
原失敗 receipt 仍保留。writer 只提交通過必要控制的修正。
Bug fix 的開 PR 步驟由既有 publication owner 接手，writer 不執行 provider 寫入。

方法檔案與 SHA-256、原始證據引用及完整步驟紀錄位於外部 evidence directory。
目錄為 `/Users/neon/soodles-audits/manager-coverage-loops/cost-lineage/writer-248`。
其中 `methods.json` 記錄實際載入的方法，`original-evidence.json` 綁定原始失敗與設計。
`work-plan.md` 保留 playbook 步驟與 owner 分工，`decisions.tsv` 保留決策。
兩案來源是 `/Users/neon/soodles-audits/manager-coverage-20261003/cost-design-a.md` 與 `cost-design-b.md`。
綜合選擇位於 `/Users/neon/soodles-audits/manager-coverage-loops/cost-lineage/synthesis.md`。
這些設計輸入不是 external judge。

## 驗證與 review

第一次歷史 readback 已通過。保存檔為外部 evidence directory 的 `243-after-1.stdout`、`243-after-1.stderr` 與 `243-after-1-process.json`。
process receipt 綁定當次 source SHA-256。這是修改後、尚未提交 source 的觀察。
下列正式 CLI 使用原 authorization 與原 manifest，沒有修改輸入。

```text
./soodles atom cost-report /Users/neon/soodles-audits/failed-order-restart/admitted-atom/authorization.json /Users/neon/soodles-audits/manager-coverage-20261003/243-cost-manifest.json
```

原 stdout 的拒絕內容如下。

```json
{
  "status": "refused",
  "invalid": {
    "field": "cost.evidence",
    "value": "cost.claim_base"
  },
  "authorizes_landing": false,
  "reason": "cost projection unavailable; original owner continuation unchanged"
}
```

第一次修正後的 CLI exit 為 `0`，`status` 為 `reported`。
immutable authorization digest 仍為 `e7509c50fd69f065dec8741cc52481e1910d49d5e6a756847f0aa401f2d5ca5f`。
subject 保留原 base 與建立 Issue 前的 `issue=null`，另由既有 created-Issue binding 驗證 #243。
結果保留 364 筆 observations，包含 5 筆 refused、225 筆 pending 與 3 筆 unknown。
Test Manager review 為 `needs_owner_readback`。這些歷史紀錄不等於目前 defect。
Schema feedback 的 state 為 `resolved`，owner transition 為 `complete`，`next=null`。
`review_disposition=history_retained`，cost review DAG 為 `observed`。
effectiveness 仍為 `unknown`，尚需下一個正常單位的 activation 證據。
feedback 的 `effects=[]`、`test_demand=null`、`authorizes_landing=false`。

`readback.py` 比較讀取前後 286 個原始檔案的內容雜湊，沒有差異。
範圍包含原 authorization、state、成本資料、manifest refs 及原 control root 的 Noodle 檔案。
本次 process elapsed 為 1.193 秒。這是單次正常讀取量測，不能推論效能改善。
報告的 tokens 與 price 仍為 unknown，不代表來源中所有 usage 都已接入。

source reviewer 的 `source-review.md` 確認 acceptance 與 cleanup 邊界。
comment reviewer 的 `comment-review.md` 提出三行重述文字及整批來源重讀疑點。
writer 接受刪除重述文字。實作已縮小重讀範圍至 state、authorization 與 lineage refs。
Test Manager 首輪選擇 `test_admission_revision` 與 `test_cost_telemetry`，共 43 個控制通過。
`implement-plan-1` 與 `implement-test-1` 保存 selection、stdout、stderr、exit 及 source hashes。
必要控制涵蓋原 base、released revision、歷史接續、未 release target、錯誤 base、foreign 或 tampered ref、缺失或衝突 ACK，以及讀取期間 state 漂移。
唯讀控制禁止 state writer、control effect、lock 與 provider 網路操作，並比較 fixture 全部檔案內容。
舊成本控制保存原 subject 的 7 秒觀測，確認 revision 前後仍為一筆、7 秒，原紀錄 bytes 不變。

補強既有斷言與 malformed-input 拒絕後，只重跑 `test_cost_telemetry`，27 個控制通過。
`implement-plan-2` 與 `implement-test-2` 保存該次必要變更的驗證。
兩輪的 `physical=[]`，均未選 full suite。43 與 27 是執行次數，不能相加宣稱 70 個不同控制。
第二輪涵蓋最後的邊界 guard。原 admission 控制所覆蓋的正常 lineage 行為未變，沿用首輪結果。
其後僅刪除 module docstring 的錯誤「No subprocesses」敘述，因 owner validator 確實使用唯讀 Git。
沒有為這個 docstring 變更重跑軟體測試。

最終 source 的正式 CLI 再度通過，保存為 `243-final.stdout`、`243-final.stderr` 與 `243-final-process.json`。
exit 為 `0`，process elapsed 為 0.691 秒。286 個原始檔案前後雜湊一致。
此 readback 與最後 source hashes 綁定。先前兩次 readback 仍保留，沒有覆寫失敗或中間證據。
第二次用於邊界 guard 後的確認。最後一次綁定 docstring 修正後的確切 source。
這些讀取不是 benchmark，耗時差不能建立改善結論。

`independent-review.md` 記錄 fresh native reviewer 對最後四個 source/test 檔案的 hash 與結論。
reviewer 未發現 P1/P2 或其他待修 finding，writer 已讀回並核對。
comment review 的三行文字已刪除，沒有還原、encoding 或未處理約束。
writer 自審 diff，`git diff --check` 通過。
此處沒有以 review 代替 Linux exact-head CI 或 external acceptance。

## 後續 owner 與限制

writer 的停止點是完成 scoped implementation、必要驗證、獨立 review、commit 與 stage-outcome。
supervisor 接續 publication、exact-head Linux CI、merge 與 Git/Noodle reconciliation。
合併後，supervisor 用 installed main 讀取同一歷史 CLI，並在下一個正常單位檢查 activation。
歷史 #243 保持 resolved。歷史 readback 不代表新 normal activation。
本次不宣稱全生命週期成本完整、成本降低、決策減少或 metadata 零值等於零帳單。
