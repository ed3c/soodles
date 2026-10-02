# Soodles owner／capture boundary review

檢查對象是 `control-r02`，HEAD 是 `28de69b12b49fa24777adac5121953be0416b7e0`。
本次只讀 production source 與公開 local fixtures。沒有讀取 host、smoke、private expected、auth 或 confidential runtime。
沒有啟動 Noodle、Codex 或 provider effect。claim-refusal #189 已合併，不列為未修缺陷。

## Overview

目前 source 沒有可重現的分支會單憑 `turn.completed`、`meta.status=exited` 或 terminal typed outcome，判定程序與 capture 都已完成。
在 archived completion 路徑，Soodles 仍探測 session PID 與 process group。
在 publication 路徑，Soodles 等待 Noodle 的 `publication claim` 子程序成功退出。
若子程序失敗，就不進入 native readiness 或 publication。
如果外部 smoke 在 `turn.completed` 就停止，而 adapter 尚未寫 exit receipt，現有證據只支持 external observer 停得太早。
這不構成 Soodles product bug 的證據。

本次找到的缺口在 P-class 入口。根 `AGENTS.md` 的 Local selector 只涵蓋已供應 control root、admitted launcher/envelope 與 Noodle owner 的後段觀察。
如果使用者已授權本機 Issue atom，但尚未選定 authorization，根入口沒有連到現有 `issue-atom` skill。
skill 已有正確的 pre-admission 路徑，caller 卻必須先猜到它。
這是小而可控的文件修正，不需要新增 command、schema 或 eval runner。
過往誤問使用者提供 path/SHA 的紀錄只能說明修正動機，不能證明目前 baseline 有改善。
修正後仍須 fresh external pstack/evals 比較。

## Key Concepts

- **Session metadata**：`meta.json` 描述 Noodle session 狀態。它不是 OS process absence，也不是 publication authority。
- **Typed outcome**：Noodle 的 `stage_message` 表達 stage 結果。archived projection recovery 需要它，但仍須程序消失與 canonical owner 未漂移。
- **Process completion**：Soodles 以 `process.json` 的 PID 同時探測 PID 與 process group。這是 bounded local discriminator，不是完整 OS birth-identity 或 capture 安全證明。
- **Capture/publication completion**：contract 把 terminal typed outcome、session evidence 與 publication claim 的產生交給 Noodle。Soodles 執行 pinned Noodle 的 claim command，保存真實 exit/stdout/stderr；只在 exit 0 後驗 claim 並進 readiness。
- **P-class routing**：指示文件應把已知使用者意圖交給既有 owner。它能降低 caller 猜測，不能自行證明模型行為改善或授權 provider effect。

## How It Works

### 1. Running owner 不會因 premature meta 被當成完成

`issue_atom.own_start_wait` 只接受 canonical stage/attempt 的 live pair。
它要求 `meta.status` 與 attempt 相同，且 `meta.alive is True`。
接著實際探測 session PID、Noodle PID 與持有中的 lock，最後重讀 owner 與 metadata（`issue_atom.py:1038-1175`）。
現有 fixture 把 execute `meta.alive` 改成 `false` 時，owner 會拒絕，且不呼叫 provider credential supplier（`tests/test_issue_atom.py:240-264`）。

### 2. Terminal label、meta 與 typed outcome 仍不足以隱藏 live process

當 canonical order 還存在，`completed_original_order` 要求 order `completed`，之後仍呼叫 `quiescent_order`（`issue_execution.py:540-548`）。
後者逐一要求 attempt 為 terminal，讀取 `process.json`，再探測 `pid` 與 `-pid`。
任何 live target 都會觸發 `takeover.process_alive` 拒絕。之後還要重讀 canonical owner（`issue_execution.py:467-509`）。

當 order 已被 projected away，路徑要求唯一 dispatch、配對的 projection/ack、唯一匹配 session、`meta exited/alive=false`，以及唯一 completed/nonblocking typed outcome（`issue_execution.py:552-618`）。
接著它呼叫 `_absent_process`，再重讀 owner revision/effect ledger（`issue_execution.py:619-629`）。
`_absent_process` 同樣探測 PID 與 process group（`issue_execution.py:521-537`）。
這個分支使用 meta 與 typed outcome，但沒有把兩者當作 process absence。

### 3. Publication 依賴 Noodle claim owner，而非 raw turn event

`_run_claim` 執行 pinned Noodle 的 `publication claim`，保存 argv、exit、stdout 與 stderr。
只有 exit 0 才保存 JSON claim（`issue_atom.py:909-925`）。
若 exit 非零，lifecycle 回傳 `noodle.claim.exit`／`fresh_noodle_claim`，不呼叫 `_accept` 或 publisher（`issue_atom.py:1398-1426`；辨識 fixture 在 `tests/test_issue_atom.py:779-805`）。
`candidate_publication.validate_claim` 重新綁定 canonical snapshot 與 session events digest（`candidate_publication.py:92-141`）。
contract 也明定 Noodle 擁有 local order、terminal typed outcome、session evidence 與 claim（`contracts/system-v1.md:191-203`）。

Soodles claim schema 沒有獨立的 adapter exit-receipt 欄位。source 不能證明這是缺陷，因為 capture 封口目前由 Noodle claim producer 負責。
如果 pinned Noodle 在缺少 receipt 時仍成功產生 claim，需要 Noodle 自己的 source 與 fixture 證據，才能判定 producer contract 有缺陷。
外部 harness 提前停止，不能推導出 Soodles 應另做一份 Noodle capture validator。

### 4. 真實 P-class route gap

根 selector 的 Local row 直接要求已供應的 control root、admitted launcher/envelope 與 Noodle owner，再導向 bounded execution recipe（`AGENTS.md:9-12`）。
另一條 current-boundary 規則只說，externally authorized local Issue atom 應執行既有 authorization file（`AGENTS.md:39-45`）。
對以下最小狀態，兩者都沒有提供下一個 owner：

```text
carrier = authorized local Session
intent = execute one local Issue atom
authorization_selected = false
user_scope_supplies = exact task / allowed local execution
```

合法鄰居已完整存在。`issue-atom/SKILL.md:8-35` 明定，若 authorization 尚未選出，已授權的 Local Session 可擔任 supervisor。
Session 依 `local-supervisor-admission` 建立 explicit selection，執行 `supervisor-admission authorize`，再原樣消費 receipt 的 `authorization`、`next.argv` 與 `next.environment`。
skill 也明確禁止要求使用者計算 hash 或手做 authorization。
recipe 說明 preparation 沒有 Issue、Noodle session 或 provider effect。Session 不可要求使用者準備自己能推導的檔案（`local-supervisor-admission.md:3-8,23-45`）。

兩個相似 root route 顯示既有慣例。completed typed outcome 直接連到 `candidate-publication` skill（`AGENTS.md:14-18`）。
terminal candidate 則以明確條件直接命名 `landing-supervisor` entry（`AGENTS.md:29-31`）。
pre-admission Issue atom 缺少同等 root 入口。因此問題是 discoverability 與 owner routing，不是 CLI 能力缺失。

最小候選 diff 僅需調整 `AGENTS.md`：

1. 把現有 Local row 明確命名為「already-admitted local child observation」。
2. 新增其前一列：「authorized Local Session、Issue atom authorization 尚未選出 → 讀 `issue-atom` skill，走其 local supervisor admission，再原樣消費 returned next」。
3. 將 `AGENTS.md:45` 的 `issue-atom` 名稱連到該 skill，保留它作 post-selection 規則。

不應把 selection schema 複製到根文件，也不應新增 assessment CLI。判斷條件仍由既有 skill/recipe 與 `supervisor-admission` owner 保有。

## Reproductions

共三次，均在 temporary fixture 中執行，無 model/provider/production write。

1. 現有 process controls：
   `test_completed_label_cannot_hide_a_live_process_group` 與 `test_projected_away_original_order_requires_exact_completed_session` 均通過。前者證明 terminal label 不能遮蔽 live process group；後者是合法 archived neighbor。
2. 直接由 `archived_completion()` 建立同一組 `meta exited + completed typed outcome`。合法鄰居的已退出 process 得到 `source=archived_projection`、`process_and_group_absent=true`；只把 `process.json.pid` 換成實際 live `sleep` PID，結果為 `completion.process_alive`，owner=`Noodle`，required=`quiescent_writer_and_session_readback`。
3. `test_own_running_metadata_and_pins_remain_required`、`test_live_owner_wait_does_not_ask_for_claim_or_take_over`、`test_failed_claim_stops_drive_before_wait_or_publication` 均通過。它們分別辨識 premature `meta.alive=false`、live owner wait 不發 claim，以及 nonzero claim exit 阻止 readiness/publication。

P-class route gap 只是一個靜態 source counterexample：目前 root selector 對 pre-selection 狀態沒有 edge，但 skill 內有合法 neighbor。
這不是模型 behavior 實證。後續 fresh baseline 應由外部 pstack/evals 固定相同 caller task 與 pins，再觀察是否直接選到 supervisor-admission。
至少需要一個負控制：若 authorization 已選但檔案遺失，必須要求 exact owner recovery，不能重新 authorize。

## Where Things Live

| 邊界 | Owner/source |
| --- | --- |
| Local entry selector | `AGENTS.md:5-18,39-45` |
| Pre-admission owner | `.agents/skills/issue-atom/SKILL.md:8-35` |
| Selection materialization | `.agents/skills/verify-soodles/features/local-supervisor-admission.md:3-45` |
| Canonical/process quiescence | `issue_execution.py:467-537` |
| Archived completion | `issue_execution.py:540-629` |
| Live owner observation | `issue_atom.py:1038-1175` |
| Claim process gate | `issue_atom.py:909-925,1398-1426` |
| Claim/readiness binding | `candidate_publication.py:92-185` |

## Gotchas

- `turn.completed` 不是上述 production modules 的 transition key；它出現在一個 consumer-gate synthetic test，不應據此把 harness event 提升為 Soodles owner truth。
- `meta exited + typed outcome + process absent` 只證明這個 bounded recovery discriminator；JSON 本身不證明 OS 隔離或 adapter capture 安全。
- 若 external observer 要求獨立 exit receipt，它必須等待該 receipt 或 Noodle claim owner 的 terminal response。看到 `turn.completed` 就退出是 observer policy 問題。
- P-class 文件修正只能減少 caller 猜測。舊對話 trace、靜態可達性與 unit test 都不能代替修正後的 fresh behavior comparison。
- 目前沒有理由修改 `issue_atom.py`、`issue_execution.py`、claim schema 或 publication semantics。
