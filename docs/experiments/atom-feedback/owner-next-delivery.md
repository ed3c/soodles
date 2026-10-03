# Issue 235 原 Noodle writer 紀錄

本紀錄只描述這次 admitted writer。歷史 fixture 與過去的 consumer 不算本次 Noodle 執行或交付。

## 身分與來源

原 Noodle order 是 `soodles-235-080a81e6b92f`。session 是 `soodles-235-080a81e6b92f-0-execute-20261003-085851-68e69f`。
Issue 是 `ed3c/soodles#235`，由目前 admitted binding 取得。base 是 `ce29059e6d9581e7c83257c45e7c88cdd9b9c3fe`。
固定候選來源是 `66d2935a9fe98750d6e68e6a0c76feba9b3a6856`。writer 核對 patch SHA-256 `5d7bc6c45b9d6d3e6f3c5d1d12901f3e1cb02a2fc007559cf206651e7437c677` 後，以 `git apply` 匯入原 Noodle worktree。
writer 未新增 worktree、替换 authorization 或選定 verifier。原 Issue body digest 是 `da1c70c1c658ecf69aa28b4f84e998c2e33e48f2a10ee4b4af58a1e6257c3709`。`stage_outcome.worker_context` 已從真實 owner 核對 body、contract、session、spawn 與 Git worktree。

## 方法及取捨

整顆 atom 採用 Poteto Mode 的 Feature playbook。六區塊仍是同一工作輸入。依原 task，writer 沿用既有 `synthesis.md`、`initial-bundle-audit.md` 與 fixed candidate 的設計及實作，不重做設計競賽。
Model the Domain 原則使 writer 保留單一 `continuation_state` 判別欄位。它描述 ready、waiting、input_required、complete 與 unknown。原 owner 仍保存 next 與效果權限。
Prove It Works 原則要求直接驗證實際 controls 與原 stage feedback。單靠 patch 或 fixture 報告不能證明真實 Noodle session 已消費證據。
阻擋步驟先核對 base、patch 與 owner。source reviewer 只讀 repository。三份 consumer 分別使用獨立目錄。writer 是 repository 唯一寫入者。這次沒有第二個 scheduler 或 writer。

下表記錄實際讀取的本機方法。路徑與 digest 只證明保存的來源身分，不授予 runtime 或 landing 權限。

| 路徑 | SHA-256 | 本次用途 |
| --- | --- | --- |
| `/Users/neon/.agents/skills/poteto-mode/SKILL.md` | `7645c9ee27ef9798c48a84060b6df409f8593d1058c7c25cbec28dce976195f9` | whole atom engineering entry |
| `/Users/neon/.agents/skills/poteto-mode/playbooks/feature.md` | `3a62cc4a8cbcf144bb9dd05f05420a15be0d38b784d3b141bb730a5852f50a62` | 固定已設計 patch 的新行為匯入與驗證 |
| `/Users/neon/.agents/skills/unslop/SKILL.md` | `195411d320b5b328f9f642baf59757ed19aaf0931c0838740e0aca273d538dc1` | 全部回覆與 prose |
| `/Users/neon/.agents/skills/how/SKILL.md` | `d31805589c7f6a63a6db6c9fadebbd79fb9660682cf1654e9b2e5e1e7cd30bc0` | 沿用既有 source chain audit，不重做探索 |
| `/Users/neon/.agents/skills/architect/SKILL.md` | `691cd39f52c7b613866e6baf9ea0b05451ffa21a6a9b4102f166418b89178fde` | 沿用既有 producer/projection synthesis，不重做候選設計 |
| `/Users/neon/.agents/skills/no-comments/SKILL.md` | `5c5b0882297d704c3a9720c52b7a793c68b013eaf717989f0945624efdfe2b05` | 識別 review carrier 能力要求 |
| `/Users/neon/.agents/skills/show-me-your-work/SKILL.md` | `bcff5f7f9fd23f92c12b251f9cd6b947e9485e1055cfacb6fdd9cae0789d7550` | 保留決策紀錄與未知 capture |
| `/Users/neon/.agents/skills/principle-model-the-domain/SKILL.md` | `bbadbb9a723fac3f76e782ae45665eb94058ec10993e4bae36d4dc6b0e4eac07` | continuation_state 五態單一判別欄位 |
| `/Users/neon/.agents/skills/principle-prove-it-works/SKILL.md` | `ec79a15025bac8d33d62011c54f3b612733fd2a024e623b531b3637aa75070e2` | 實際 controls、stage feedback 與 saved bytes readback |
| `/Users/neon/.agents/skills/technical-writing/SKILL.md` | `10c74685e1639cc4f8ff096007e5405b25ca0e824b65aaa17105c238faf6a1e8` | 本次 N-class 交付紀錄與 commit 文字 |
| `/Users/neon/.codex/skills/eval-audit/SKILL.md` | `c11338900d88d114c353a8865d9b7a4780d972bf740b80d5eb4e38357b1bf133` | 檢查既有 evaluation 方法與範圍 |
| `/Users/neon/.cursor/skills-cursor/create-skill/SKILL.md` | `f3df382ea9cf2119ee8f121143b2ec0cacbd8bbc6dc3a15fd981ea547cef42f8` | 既有 skill frontmatter 與指令结构 review |
| `/Users/neon/.codex/worktrees/atom-delivery-control/soodles/.worktrees/soodles-235-080a81e6b92f-0-execute/.agents/skills/execute/SKILL.md` | `ffb91182f2ace6e63f1bbf7e7139ab79e5cc998f4e789a3d88fce7cb5dc9699f` | selected execute 與寫作/feedback/test scope owner |
| `/Users/neon/.codex/worktrees/atom-delivery-control/soodles/.worktrees/soodles-235-080a81e6b92f-0-execute/.agents/skills/test-manager/SKILL.md` | `4f52741d304d1deea012b41194a61bdd5ed64001182e3fd4838f362ba95e4372` | selected execute 與寫作/feedback/test scope owner |
| `/Users/neon/.codex/worktrees/atom-delivery-control/soodles/.worktrees/soodles-235-080a81e6b92f-0-execute/.agents/skills/review-writing/SKILL.md` | `49d9161bb04733e1cbc99d85b4b463661f206d5a98c0b9b47c09c255a5e9591f` | selected execute 與寫作/feedback/test scope owner |
| `/Users/neon/.codex/worktrees/atom-delivery-control/soodles/.worktrees/soodles-235-080a81e6b92f-0-execute/.agents/skills/review-writing/features/writing-review.md` | `12c2c486930e9185342bdb35806fc121de10d179577ec781576e673dbba45c0c` | selected execute 與寫作/feedback/test scope owner |
| `/Users/neon/.codex/worktrees/atom-delivery-control/soodles/.worktrees/soodles-235-080a81e6b92f-0-execute/.agents/skills/review-writing/features/pclass-feedback.md` | `068792db262a27a2e4af333afa5edfd1719854f621b7498fe0a41e5a9329568d` | selected execute 與寫作/feedback/test scope owner |
| `/Users/neon/.agents/skills/deslop/SKILL.md` | `2f7b7def74af7ed11f5b44b4d32f0f91fca8c5d1f92bf2171e8d12fd33a0f810` | 新 capability readback 後執行 pre-commit 或 CLI/comment review 方法 |
| `/Users/neon/.agents/skills/control-cli/SKILL.md` | `13ac93e595bbda2000849bdb815d5f2ca03f7c2ca63788c8335f9212b9b422a2` | 新 capability readback 後執行 pre-commit 或 CLI/comment review 方法 |
| `/Users/neon/.local/share/pstack/agents/comment-sicko.md` | `c0fd0383008da45fc78cfac17b9007d62c42f87ad1c8d5c2fb658b1fd01f7c82` | 新 capability readback 後執行 pre-commit 或 CLI/comment review 方法 |

原 stage prompt 的 selected instructions 固定在 base。`selected-instruction-pins.json` 保存原 pins。上表的 repository treatment hashes 另描述匯入後的審查對象，不替換本 session 的原 instruction_context。

## 能力變化與方法執行

本 carrier 提供 `collaboration.spawn_agent` 和 `fork_turns: none`。writer 使用這個原生工具執行獨立 review 與 consumer。Comment Sicko reviewer 讀取本機實際 persona 檔案。這次未宣稱具備 Cursor Task、特殊 subagent_type 或指定外部模型。
Poteto Mode 明定提交前使用 `deslop`。最初搜尋本機安裝目錄時未找到 deslop 或 control-cli。後續 record reviewer 發現這兩份檔案已存在。writer 讀取新檔案並保存 `capability-readback.json`。原 `capability-gaps.json` 保留為歷史觀察，不能再作為目前阻擋結論。
writer 已執行 deslop diff review，未找到需新增程式修正的缺陷。control-cli 優先使用既有 repository harness，因此沿用已驗證來源的正常 CLI 與 disposable fixture receipts。原生 Comment Sicko review 建議刪除三行敘述性 docstrings。writer 已接受刪除，保留一行跨模組 API 契約。沒有 MUST KILL 重構項目或未處理 suppression。這些方法不要求替换原 runtime carrier。
本次按原 task 使用原生 fresh reviewer，未宣稱跨模型家族 review。完整平台 transcript 未取得。原生工具 requests/results 的選定欄位、consumer 自錄讀取及輸出均有保留。這些限制不能被寫成已執行的其他 carrier 驗證。

## 原始碼、審查與 controls

原缺陷把任何 next 都視為可立即接續。新 producer 宣告 readiness，Schema Manager 驗證宣告與 next 的一致性。缺值或矛盾維持 unknown。ready 僅允許呼叫原 continuation，並不授權其效果。
原 body projection 漏掉 Issue 正文。新 admission、projection 與 recovery bindings 保留 exact body。stage adapter 核對全文 digest 及 contract。缺少或不符時拒絕。首次 lifecycle bundle 使用已選定的 immutable external lifecycle bytes，instruction pins 與獨立 landing owner 維持原身分。
feedback 的輸入固定部分由 CLI 產生。Schema Manager 保存 current passed observations，stage adapter 加入驗證過的 prior reuse references。新的 failed check 不能被舊 PASS 蓋過。Agent 只補真正缺少的 observations。
獨立 reviewer `/root/candidate_review` 使用 fresh context 檢查 source、tests 與 changed P-class prose，回報沒有 supported blocking finding。這是 source/prose review，沒有代替 behavior feedback。
首次 Test Manager plan 對 Issue template 回 needs_scope。writer 追查改動後，把該填寫指引納入既有 prose review 分類。沒有為它新增 runtime gate。
正常命令 `./soodles test --base ce29059e6d9581e7c83257c45e7c88cdd9b9c3fe` 選出 34 個模組，共 507 個 controls，exit 0。命令 elapsed 約 90.31 秒，runner 回報約 89.62 秒。兩者不能相加。這不是 full-suite 要求，也沒有執行額外 benchmark。
Comment review 後，Test Manager 對兩個改動模組 `test_schema_manager` 與 `test_atom_feedback` 選定 30 個 controls，全部通過。正常命令約 13.43 秒。這是重驗受影響的 30 個案例，不是另外 30 個獨立驗收需求。其餘程式來源與輸入保持原身分。

選擇中的 physical controls `order_handoff` 與 `interruption_resume` 尚待原 canonical acceptance owner。local unit controls 不代表已執行這兩個 physical controls，更不代表 Linux exact-head acceptance。

## 原 session 的 feedback

第一輪實際 `./stage-outcome feedback` 回 recorded、round 1、review_criteria。行為未評分。第二輪先消費獨立 criteria reviewer 的 18 個 supported fields，再回 recorded、round 2、supply_behavior_evidence。
CLI 產生 `next.input.selection` 草稿與三份 requests。writer 未自行重組 observation union。consumer 使用 fork_turns none，分別處理 engineering、owner_states 與 feedback 的唯讀解讀。protocol 綁定全部七份 changed P-class 指令，包含 Issue template。
第三輪真實 stage feedback 已記錄 round 3。Schema Manager 回 `SUPPORTED / VALID / PASS`，next 是 `consume_verified_behavior`。Test Manager 回 observe 與 reuse 均為空，三個 cases 全部 verified。writer 已讀取實際 reports 與 captures，再於 `owner-consumption.json` 保存此承接與限制。沒有把 expected 寫入 consumer report。

三個 consumer 的結果符合已審核條件。owner_states 正確區分五態及 initial runtime/instruction 來源。engineering 保留 whole-atom 入口、body refusal、缺能力不可完成及 writer 無發布權限。feedback 使用 CLI 草稿，保留 criteria_pending、current failure 與 terminal outcome 的界線。這些是對給定情境的解讀，不是這些 owner 操作的實際執行。

Schema 本輪讀取與驗證約 5.435 ms，decision projection 約 0.0755 ms。Test Manager 已把這些值放入同一 feedback 的 cost。projection 是其中一部分，不能重複加總。模型專用時間、tokens 與完整決策總數維持 unknown。

captures 記錄第一次大批讀取曾被工具截斷，consumer 隨後補讀相關段落。完整 bytes hash 相符，不表示模型看見每一行。此限制與原始 reports 均有保留。這次 PASS 只支持三組被審核的解讀。當時 deslop 尚缺的觀察保存在原 owner-consumption.json。後續 capability-readback 與方法執行紀錄補齊該前置條件，沒有改寫舊 observation。

## 決策量測與交付邊界

主指標是可見的工作流程決策。照原 owner 的固定 next 執行不新增選擇。`decisions.tsv` 保留已觀察的 scope、evidence 與 capability 決定。首列時間未由工具觀測，後續列已撤銷該時間精度，保留核對結果。
完整 capture 不可得，完整 atom 決策總數是 unknown。工具數、507 個 controls、18 個 expected fields 與耗時都不是決策總數。沒有同條件比較，也未聲稱 speedup、全域最短路徑或普遍正確性。
writer 未執行 push、PR、merge、Issue closure 或 local reconciliation。writer 的最終 typed outcome 仍由原 stage-outcome entry 記錄。原 supervising issue-atom owner 保留後續 publication、native readiness、Linux exact-head acceptance、merge、closure 與 reconciliation。

外部證據保存在 `/Users/neon/soodles-audits/owner-next-k9dj8l1s/writer-235/`。其中 requirements、binding、selected-instruction-pins、method-loads-current、capability-readback、controls stdout/stderr、independent review、criteria review 與 feedback process receipts 均可讀回。`delivery-manifest.json` 只綁定候選 bytes，`authorizes_landing=false`。

## 尚未發布候選的 base 更新：準備紀錄

原 writer 提交 `1c0b22cb86c1353dfa415c1e7944103b74f9513d` 後，provider base 前進至 `5e2cd1b0f11de685dab26c5370c566b508062857`。原 owner 在 `noodle.claim.exit` 拒絕 publication。候選不是新 base 的後代。當時沒有 PR 或 publication claim。這份拒絕不能用新 authorization 或虛構的 prior publication 解除。

Supervisor 在隔離 checkout 準備整合輸入。整合 commit 保留原候選與新 base 作為兩個 parents。兩者只在 Test Manager boundary map 發生文字衝突。整合保留 interruption recovery 與 atom feedback 兩個既有 mapping。對應 `test_test_suite` 的 12 個控制通過。這份輸入沒有 publication 或 landing 權限。

最初設計先將 completed review 改為 failed，再停止 loop。源碼審查推翻了這個順序。選定 Noodle 的 `reconcileFailedOrders` 會在啟動時移除一般 failed order。`preserveRequestChanges` 僅保存具備 blocked outcome 的 recovery binding。原 attempt 是 completed，因此不適用。兩份獨立工程審查確認了這個反例。它們是 source review，不是新的 clean-context consumer 實驗。

修正後，原 lifecycle 先阻擋舊完成紀錄的 publication。Owner 在 manual 模式保留 review，再停止 loop。Owner 檢查身分、範圍、frozen pins 與 ancestry，然後執行固定 fast-forward。Owner 更新同一 Issue 的 base 與既有 base pins，讀回正文，再建立新 envelope。新 loop 在 manual 模式恢復原 review。它之後才執行 request-changes、替換任務與恢復派發。這個順序讓一般 failed order 留在同一個正在運行的 loop 內。

新的 publication 檢查要求一個後續 completed attempt。原 authorization、Issue、order、worktree、外部 judge 與歷史保持原身分。未知 Git、provider 或 process 效果需要讀回。Owner 不重送未知效果。若新 loop 在 request-changes 後、替換前中斷，本路徑仍不能自動恢復該 failed order。

Test Manager 選定 `test_issue_atom` 的 93 個控制，全部通過。Runner 回報 68.529 秒，physical list 為空。接合 fixture 使用真正的 `correction_owner`，以一次性 snapshot 模擬 Noodle 回報；它沒有啟動產品 writer。另一次唯讀檢查以原 session 的實際 events 和 pending review 通過 completed custody 檢查。這些結果不證明 live base recovery 已完成。

準備證據位於 `/Users/neon/soodles-audits/owner-next-k9dj8l1s/base-owner-loop/`。實作測試與失敗歷史位於同一根目錄的 `evidence/base-owner-loop/`。新的指引仍須在後續 admitted session 取得目前保存文字的 consumer evidence，並經 stage-outcome feedback 交由 Schema Manager 消費。此準備紀錄不取代該結果，也不證明 PR 已合併。


## Base recovery 後的 admitted writer

本次 session 是 `soodles-235-080a81e6b92f-0-execute-20261003-102013-056a97`。原 order 與 Noodle worktree 保持不變。`stage_outcome.worker_context` 已核對目前 running attempt、原 owner、正文與 envelope。新 base 是 `5e2cd1b0f11de685dab26c5370c566b508062857`。起始 integration head 是 `ee7fa3318491b59e2073ffcc5384c7b18eb03593`。本次 Issue body SHA-256 是 `4a0d6a36096042d12196c893ee1cc0c6ccb4622d9a8518e1eeb7f9807732641d`。

原 patch 已在 integration 的祖先中，因此 writer 沒有再次套用。Poteto Mode 先以 Session pickup 找回既有設計、source review 與失敗歷史，再接續 Feature 的驗證與修正步驟。依原 task，writer 沒有重做設計競賽。`method-loads.json` 保存本次實際讀取的路徑與 SHA-256。`playbook.md` 保存步驟、續行點與範圍取捨。

Prove It Works 原則使 writer 重新核對整合後的實際來源與 controls。Model the Domain 原則保留既有 binding 的 `contract` 與 `issue_body`，沒有為恢復建立另一份狀態。原生 `collaboration.spawn_agent` 支援 `fork_turns: none`。獨立 source reviewer、criteria reviewer、修正 writer 與各 consumer 使用自己的證據檔案。只有修正 writer 在指定四個 repository 檔案寫入，主 writer 隨後接手紀錄與 manifest。這次沒有宣稱具備 Cursor Task、特殊 subagent_type、跨模型家族 review 或完整平台 transcript。

### 整合失敗與修正

第一輪 Test Manager 依目前 admitted base 選出 35 個模組、538 個 controls。命令 exit 1，wall time 約 118.73 秒。三個模組失敗，其餘 32 個模組通過。原始 stdout、stderr 與 process receipt 均保留，後續成功不覆寫這次結果。

`adopt_interruption` 已核對 Issue body digest，卻沒有把正文加入交給 projection 的 binding。另一個 recovered stage fixture 也只傳 contract。新 projection 要求 exact body，因此兩個 consumer 出現 `KeyError: issue_body`。修正把已驗證正文傳入既有 binding，並讓 fixture 保留原 prompt 正文。沒有用空值或略過驗證來消除錯誤。

`system-context` 使用共同的有限讀取器來固定 source bytes。整合後的 `issue_atom.py` 是 284362 bytes，超過原 256 KiB 單檔上限。正式 entry 與其 control 都拒絕這個來源。拆分 owner 會擴大這次修正與固定 runtime 的檔案邊界。這次將既有單檔上限調為 512 KiB，總量仍限制為 1 MiB。新增控制涵蓋有效的大檔、上限值與超過上限一個 byte 的拒絕。這項改動讓現有來源可讀，沒有移除有限容量檢查。

修正後，Test Manager 選出的七個受影響模組共 88 個 controls 全部通過，命令約 43.79 秒。它們涵蓋 admission、instruction context、system context、interruption recovery、stage outcome、feedback owner 與 atom feedback。正式 `./system-context entry issue-atom run` 也回傳 `ready`。這份 readback 的 source head 仍是起始 integration commit，不能宣稱已驗證未來的 commit。

獨立 comment review 建議移除兩個重述 helper 動作的 docstrings。主 writer 接受這兩項建議。它們沒有外部限制或 public API 契約。沒有 MUST KILL 項目或未處理的 suppression。其餘 source/prose review 與修正後 readback 保存在 `integration-review.md`。最終 owner controls 與 feedback 結果另記於下段。

本次外部證據目錄是 `/Users/neon/soodles-audits/owner-next-k9dj8l1s/writer-235-resume/`。所有新的紀錄與原 `writer-235/` 分開。完整 atom 決策總數、模型時間、tokens 與價格仍是 unknown。沒有 benchmark 或同條件勝出比較。


### 本次 owner controls 與 consumer 續行

移除兩行 docstrings 後，Test Manager 對最終 owner source 執行 `test_issue_atom`。94 個 controls 全部通過，命令約 70.64 秒。這項結果與前述 88 個 controls 各自保留輸入與 scope，不把重跑次數當成新的驗收需求。最初 32 個模組的成功仍是當時來源的歷史結果。這次依修正影響選定必要重驗，沒有宣稱所有 35 個模組都在最終來源上重新執行。

本次 protocol 使用 schema 2。requirements 從目前 `worker_context` 取得，與 admitted task 及 contract 相同。protocol 綁定全部七份 changed P-class instructions。獨立 `/root/criteria_review` 先核對四組案例的 25 個 expected fields，全部 supported。第一輪真實 stage feedback 回 `review_criteria`。第二輪回 `supply_behavior_evidence`，CLI 提供 selection 草稿及四個 requests。主 writer 沿用這份草稿，不另組固定輸入。

四組 fresh consumers 由原生 `collaboration.spawn_agent` 建立，均使用 `fork_turns: none`。每組只取得 task、pinned instructions、必要 method 與自己的輸出目錄。預期值與 protocol 留在 supervising writer。第三次 consumer 派發曾回 `agent thread limit reached`。兩個既有 consumers 結束後，原工具成功建立其餘 consumers。`capability-readback.json` 保留原拒絕及後續 readback。沒有改用另一個 runner。


第三輪真實 `./stage-outcome feedback` 已記錄 round 3。Schema Manager 回 `SUPPORTED / VALID / PASS`，next 是 `consume_verified_behavior`。Test Manager 的 observe 與 reuse 均為空，四組 cases 全部 verified。主 writer 已讀取四份 reports 及 captures，並於 `owner-consumption.json` 保存回覆 digest、承接動作與限制。這份結果綁定目前七份 P-class saved bytes，沒有改寫原 observations。

四份 reports 保留 whole-atom 入口、五態 continuation、CLI feedback input 及未發布 base recovery 的邊界。它們是對指定情境的實際解讀，不是真實 owner effects 的執行。部分合併工具輸出曾被截斷，consumer 已補讀並在 trace 記錄。完整平台 transcript 與 consumer 全程耗時仍未知。Schema 本輪讀取及驗證約 8.250 ms，decision projection 約 0.0964 ms。後者是前者的一部分，不能重複加總。

當前 writer 的 source、必要 controls、獨立 review 與 scoped feedback 已有證據。`delivery-manifest.json` 已綁定目前 admitted base、Issue 235 與保存檔案。原 typed outcome 仍由 `./stage-outcome completed` 記錄。這些 writer 證據不授予 publication 或 landing。後續 native readiness、Linux exact-head acceptance、push、PR、merge、Issue closure 及 Git/Noodle reconciliation 仍由原 supervising issue-atom、publication 與 independent landing owners 執行。
