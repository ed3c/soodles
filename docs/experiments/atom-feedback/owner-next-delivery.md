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
