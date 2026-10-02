# Authorization 最短路徑：有界 P＋CLI 行為改善

最後固定產品與 P-class 原型通過產品 controls；v5 獨立行為判定為 **VERIFIED_BOUNDED_OBSERVED_IMPROVEMENT**。只採納本輪條件下的 bounded behavior claim。這份報告封存在交付前，不是 Issue／PR 已完成的宣告；後續 publication、exact-head acceptance 與 terminal receipt 由既有 owner 提供。

## 固化的局部路徑

```text
已授權的 Session 選定身份／能力／外部裁判
    → python3 -B ./supervisor-admission authorize SELECTION SHA256 OUTPUT
    → prepared.json：authorization digest + next.argv + next.environment
    → 既有 issue-atom run
```

本輪允許 Session 擔任 candidate 外的 supervisor。新入口取得 Git root/head、設定與 instruction digest，再驗證既有契約。入口保留已選定的 carrier／publisher，並回傳唯一 continuation。它不選擇自己的裁判、不啟動 Noodle／模型或 provider 寫入。首次準備不再要求使用者手工組 authorization。選定身份後，恢復仍須保持同一身份，不能因原檔遺失就另造一份。

P-class 只固定入口、適用條件與如何消費結果，不嵌入各階段可漂移的歷史命令。必要的 identity／owner／readback gate 保留。先前 claim 非零退出誤判成等待是另一個 transition 缺陷，未併入這個 atom。

比較屬於 **P＋CLI combined**，不把改善單獨歸因於提示詞。Baseline 是 `7e602dbe3fd4db670b15ef0267025e6c1dfffd4d`；最後固定 treatment 是 `8efb5347b6506e25a2d09f84ed823c64ccbc7d90`。原型在 disposable fixture；正式候選須由 Noodle writer 在同一 Issue 的 worktree 交付相同 bytes。

## 產品驗證

| 驗證 | 結果 | 限制 |
| --- | --- | --- |
| 原先獨立固定的 discriminator | 28 / 28 GREEN | 固定 fixture 產品判準，非行為改善證明 |
| 另行預先固定的 root／entry 反例 | 3 / 3 GREEN | r02 錯誤通過，r03 正確拒絕 |
| 最終相關 unit suite | 65 tests PASS | 52 Issue-atom、7 supervisor、6 新 producer controls |
| 封存 oracle 的可攜 replay adapter | 1 test PASS | 原 oracle bytes 不變；macOS temp 路徑先 resolve |
| canonical Linux acceptance | 交由既有 owner 在正式 head 執行 | 本報告不替代 Actions receipt |

原始產品/P 錯誤都保留：r01 直接執行不可執行的 wrapper；r02 未拒絕 Git 子目錄與不存在／不可執行的 continuation。修正後固定 r03，後續量測不再修改產品或 P。

## 行為實證與保留的失敗

| 量測 | 固定判定 | 原因 |
| --- | --- | --- |
| v1 | INCONCLUSIVE | 原 protocol 的全體 gate 包含 baseline 拒絕後留下 draft 的失敗；未事後豁免 |
| v2 | INCONCLUSIVE | baseline 搜尋讀到歷史實驗文字，違反曝光 gate |
| v3 | NOT_VERIFIED | 證據有效，但 task 写入 scope 排除了產品合法的暫存位置 |
| v4 | INCONCLUSIVE | 封存程式改錯 projection 執行 mode；只啟動兩個，未補抽其餘四個 |
| v5 | VERIFIED_BOUNDED_OBSERVED_IMPROVEMENT | 證據完整性與 treatment safety gates 全通過 |

v3 之後曾按三次上限停止；使用者明確要求「反覆直到修正成功」後，才繼續修正量測。原判定與停止報告保留於各輪目錄，沒有回寫舊裁判。v4 的設定錯誤也保留。v5 將 output 放進共同可寫的 work 範圍。完成全部 freeze 後，supervisor 才執行可重跑的 bytes／mode／fixture／metadata 核對，以及實際 staging／cleanup audit。supervisor 再核對一次，然後啟動 consumers。這些量測修正本身不計為產品改善。

v5 採相同 20-file 唯讀 source projection、6 個 fresh native consumers、51 次 recorded operations／204 個 raw files。4 份有效 authorization 通過原 frozen validator；兩個 publisher mismatch 均正確拒絕，沒有 output 或殘留 staging。唯一非零退出是預期 refusal exit1，沒有意外 recorded operation errors。

| 案例 | Baseline 操作數 | Treatment 操作數 |
| --- | ---: | ---: |
| schema 2 | 11 | 7 |
| schema 3＋number/config | 10 | 6 |
| publisher mismatch | 9 | 8 |

只比較同一輪、相同條件的 paired observations。數字由 `analysis.py` 讀取固定 receipt 聚合；不能比較 v1–v5 的分數再稱為連續產品進步。完整 protocol、observer、launch/completion、preflight、原始 requests/results 與 digests 見 `behavior-v5/`。

## 局部與全局閉環

局部目標是簡化一個 bounded transition 的合法完成與正確拒絕，同時保持身份、效果與恢復 invariant。全局目標是從需求與反例開始，先固定裁判，再取得 fresh 行為證據並作出採納判定。之後，同一候選仍須取得 acceptance／owner terminal receipt。反例與可執行檢查須保留給下一個 Session。

前幾輪未獲採納時，交付準備停止，沒有產生 production authorization。`verification/delivery-stop.json` 保留這次實測。新的正向判定通過後，外部 supervisor 才可用既有 Issue-atom owner 交付同一組 source、controls、失敗與成功證據。這是本次 task 的外部採納 gate，不是新增 production scheduler 或聲稱已有通用自動 hill-climb engine。最終交付狀態必須讀 owner receipt，不能從這份實驗的 PASS 推論。

## 主張限制與成本

- 每個 case／arm 一次觀察；只證明本輪 captured operations 的下降，不提供統計顯著、所有未來任務不退化或 Agent 永不猜錯的保證。
- Native fresh agents 共用檔案系統，唯讀 projection 不等於 OS sandbox；錄製不是完整 platform transcript。
- 同一 parent Session 兼具 supervisor 與實作角色；分離 consumer／observer context 不是獨立安全主體。
- 精確 native 模型身份、hidden reasoning tokens、總 context／工程與評測成本未取得；操作數下降不代表總成本下降，也沒有量到最初選擇 carrier／publisher 的全部成本。
- Native consumer 結果不能借給 Noodle／Codex CLI carrier；地端 doctor 只驗證能力與路徑。正式 Noodle writer 的交付另有實際 owner 證據。
- 控制與 recipe 可重用；只跑受影響驗證，有行為主張變更才做新比較。沒有執行完整 feature-map maintenance，也不宣稱完整無人值守生命週期已無缺陷。
- `decision.json`、驗證 receipt 與本報告皆不授權 merge。
