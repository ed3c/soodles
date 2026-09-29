# Authorization 最短路徑：本輪不採納

產品原型與 P-class 修正已完成，行為採納判定是 **NOT_VERIFIED / DO_NOT_ADOPT**。本輪第三次量測後停止，不啟動 production Issue、PR 或 landing；尚未完成使用者要求的單一 Issue atom 終端交付。缺項是有效的行為採納證據，不是使用者需要補交 authorization。

## 已固化的局部路徑

```text
已授權的 Session 選定身份／能力／外部裁判
    → python3 -B ./supervisor-admission authorize SELECTION SHA256 OUTPUT
    → prepared.json：authorization digest + next.argv + next.environment
    → 既有 issue-atom run（本輪未啟動）
```

Session 可以擔任 candidate 外的 supervisor。新入口代為取得 Git root/head、設定與 instruction digest，驗證既有契約，保留明確選定的 carrier／publisher，回傳唯一 continuation。它不選擇自己的裁判、不啟動 Noodle／模型或 provider 寫入。首次準備不再要求使用者手工組 authorization；已選定後的恢復仍須保持同一身份，不能找不到就另造一份。

P-class 只固定入口、適用條件與如何消費結果，不嵌入各階段可漂移的歷史命令。必要的 identity／owner／readback gate 保留。先前 claim 非零退出誤判成等待是另一個 transition 缺陷，未併入這個 atom。

原型 source：baseline `7e602dbe3fd4db670b15ef0267025e6c1dfffd4d`；最後固定 treatment `8efb5347b6506e25a2d09f84ed823c64ccbc7d90`。原型在 disposable fixture；主 working tree 未修改。

## 產品驗證

| 驗證 | 結果 | 限制 |
| --- | --- | --- |
| 原先獨立固定的 discriminator | 28 / 28 GREEN | 固定 fixture 產品判準，非行為改善證明 |
| 另行預先固定的 root／entry 反例 | 3 / 3 GREEN | 原先 r02 錯誤通過，r03 正確拒絕 |
| 最終相關 unit suite | 65 tests PASS | 52 Issue-atom、7 supervisor、6 新 producer controls |
| 封存 oracle 的可攜 replay adapter | 1 test PASS | 保持原 oracle bytes；macOS temp 路徑先 resolve |
| canonical Linux acceptance | NOT_RUN | 沒有 production candidate head |

原始錯誤沒有刪除：r01 的 P-class 直接執行不可執行 wrapper；r02 未拒絕 Git 子目錄與不存在／不可執行的 continuation。修正後固定 r03，後續量測不再修改產品或 P。

## 行為 hill climb 與第三次停止

| 量測 | 固定判定 | 原因 |
| --- | --- | --- |
| v1 | INCONCLUSIVE | 原 protocol 的全體 gate 包含 baseline 拒絕後留下 draft 的失敗；不能事後豁免 |
| v2 | INCONCLUSIVE | baseline 搜尋讀到歷史實驗文字，違反曝光 gate |
| v3 | NOT_VERIFIED | 證據有效，但所有 treatment 違反本輪寫入 scope |

v3 使用相同 20-file 唯讀 source projection、6 個 fresh native consumers、43 次 recorded operations／172 個 raw files。完整性檢查通過；4 份有效 authorization 通過原 frozen validator；兩個 publisher mismatch 都正確拒絕且無最終 output。

| 案例 | Baseline 操作數 | Treatment 操作數 |
| --- | ---: | ---: |
| schema 2 | 10 | 5 |
| schema 3 | 9 | 5 |
| publisher mismatch | 7 | 7 |

這些只是可觀察操作數，不構成已採納的改善。固定 observer 得到 `evidence_valid=true`、`treatment_safety_pass=false`：authorize 會在 output 父目錄建立驗證暫存，驗證後清理；本輪 task 只允許寫 output／scratch／evidence。原產品 oracle 明確允許這種 staging，量測 task 卻排除了它。不能因最終沒有殘留而改判安全，也不能據此宣稱產品相對退化。

精確判定、launch/completion、原始 requests/results 與 byte digests 見 `behavior-v3/`。原有 v1/v2 保持原判定。沒有第四次抽樣、替換失敗 consumer、事後更改裁判或把修量測帶來的分數變化算成產品改善。

## 全局閉環停在哪裡

局部目標是：一個 bounded transition 的合法完成與正確拒絕更容易，相關身份、效果與恢復 invariant 不退化。全局目標是：需求／反例 → 固定裁判 → fresh 行為證據 → 採納判定 → 同一候選的 acceptance／owner terminal receipt，並把反例留給下一個 Session。

本輪完成了原型、產品檢查、獨立量測、失敗封存；沒有通過行為採納 gate，所以沒有開始 Issue／PR／交付。外部 packet 的交付準備也檢查 `decision.adoption == ADOPT`，未滿足就拒絕產生 authorization。這是本輪的外部停止決定，並非新增 production 全局 gate 或已證成的自動部署能力。

下一步需要先修量測設計：把 CLI 的實際 read/write footprint（包括合法 temporary staging 與 cleanup）映射到 feature recipe、host 可用隔離能力及 observer 判準；在任何新 consumer 前固定，並先用 deterministic controls 確認三者一致。不能默默放宽本輪 scope，也不能為了得分修改已固定產品。依三次上限，本輪不執行新的比較。

## 主張限制

- Native fresh agents 共用檔案系統，唯讀 projection 不等於 OS sandbox；錄製不是完整 platform transcript。
- 精確 native 模型身份、hidden reasoning tokens、總 context／工程與評測成本未取得；操作數下降不代表總成本下降。
- 每個 case／arm 一次觀察，不提供統計顯著或所有未來任務不退化的保證。
- 本輪 native consumer 的結果不能借給 Noodle／Codex CLI carrier；地端 doctor 只驗證能力與路徑。
- 同一 parent Session 兼具 supervisor 與實作角色；獨立 consumer／observer context 不是獨立安全主體。
- `decision.json`、驗證 receipt 與本報告皆不授權 merge。
