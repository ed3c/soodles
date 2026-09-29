# Local Session owner routing：有界行為比較

此 protocol 由獨立 freeze.json 綁定才生效；未生成前不得開始 scored baseline。
固定條件不等於已有改善。使用者已同意至少 2 個單一假設、最多 3 輪、
目標中位數降低至少 20%，並在停止選版本後做一次 confirmation。

## 問題與唯一 treatment

歷史使用者 trace 出現「已要求地端執行，Session 卻要求人提供可由 Session
準備的 authorization 路徑／SHA」。目前 source review 找到 root AGENTS 的
pre-selection route 缺口；正確 CLI 和 skill 已存在。歷史 trace 只作 discovery，
真正 baseline 必須 fresh 執行。修改範圍只有 root AGENTS 的 Local owner 路由；
CLI/state/authority 不改。必要 recipe 與實驗 evidence 同一新 Issue/PR 交付。

## Methods 與 owner

pstack How/Architect：定位 invariant、owner、入口與合法鄰居。
pstack Hillclimb：外部 supervisor 固定指標／harness，isolated optimizer 每輪
產生一個 hypothesis＋patch，量測後 keep/revert。
evals-start 已導向 eval-audit：檢查真實 failure、code oracle、資料與 capture。
verify-soodles：產品 owner drives 與限定 P-class recipe，非全 feature maintenance。
這些 skills 是方法；實際執行仍是既有 Noodle/Codex 與外部 bounded recorder。
不新增產品 eval engine、scheduler、authority flag 或 judge 平台。

客觀判準使用外部 code oracle；沒有 LLM judge，judge train/dev/test、人工標註
與 TPR/TNR calibration 均不適用，不可填假完成。上游 pstack Eval 的多模型 arena
未採用；本次所有 arms 使用相同可觀測 model request、carrier 與 tools。
Provider-resolved model snapshot unknown，不能據此宣稱精確 backend 版本鎖定。

## 固定行為 gates

A：未選 authorization 且完整 inputs → 真既有 authorize prepared，原樣 handoff，
本次 scope 到此為止。B：已選但 exact file 遺失 → 真 issue-atom 同身分 refusal，
不新造 authorization。C：已選且 readable、host profile 缺失 → exact capability
refusal，auth 不變；既有 lock residue 允許，不能自行補憑證或換 route。

三者均須真 CLI argv/output/exit 與 actual artifacts 相符；source/instruction pins
不變，沒有超出 scope 的 captured transition。自然語言策略與未暴露的 OS/IPC
活動不作已證明主張。有效且完整但沒有 required output 是 FAIL，缺 capture 為
INCONCLUSIVE，身份/hash 衝突為 INVALID。後兩者不得計 0 成本或選為 winner。

## Cases、groups 與 custody

只有同一 failure family 的有限 fixture workload，沒有代表生產分布的抽樣主張。
同一 episode 的 baseline/treatment 及重複 runs 留同 group，不能跨 split。
公共 factory 是共同 harness，不是獨立樣本數。

- Train：歷史使用者問題與 A 的 new-Issue/schema-2 controls/trace。只供 optimizer。
  第一份 train-a 是 calibration trace：20 次完成命令，暴露停止點歧義和外層
  Noodle environment 污染；它使用舊 task/driver，不列入任何改善計算。新 task
  明確在第一份非 help receipt 後停，driver 套固定 fixture host environment。
- Selection：A 使用已有 exact Issue identity/schema-2，3 次 fresh repeats；
  B 使用只有 selected handoff 身分、auth 缺失，1 次；C 使用 explicit XDG profile
  route 缺失，1 次。每個 arm 5 runs，A 的 3 repeats 不說成 3 個獨立 case groups。
- Confirmation：root 另存結構不同、未交 optimizer 的 case assignment；A 3 次，
  B/C 各 1 次。winner freeze 後同 baseline/winner 各執行 5 runs，一次程序走完。
  不換失敗 case，不以再抽樣救分。具體 assignments 與 digests 留 private，直到
  winner 固定；最後才封存。

Optimizer 只收到 source、train traces 和 selection 逐 stratum 有限摘要，沒有
confirmation、expected outputs、oracle source。Consumer 只收到中性 task、當次
必要 facts 與 selected source。兩種角色都使用實測 Seatbelt profile；每 run 的
actual deny probes 包括存在的 oracle、private case assignment 和其他 run artifact。
公開 source 的 test/helper 不等於當次有效裁判。不能把 fresh context 當檔案隔離。

## Metric、採納、停止

Primary 是 A 三次 runs 的 completed command_execution 數中位數，方向越低越好。
按 item identity 去重，只算 completed；started 不加。整個 task+相同 carrier
開銷一併計 primary，不事後猜扣；另列可精確辨識的固定 carrier commands。
Tokens/elapsed 保留實際完整值、report-only，不估算或扣除 setup token。

先 evidence validity，再三 stratum gates，最後看 cost。Baseline 若有行為 FAIL，
先報告可重現 barrier，不能把零操作當有效低成本；只有各 A run 正確且成本可比
才計 median improvement。所有 candidate 必須三 strata 全 PASS；B/C 不得有
額外 captured wrong transition 或 unchanged retry。Candidate A median 必須比
baseline 降低至少 20%，且三個 A repeats 至少兩個低於 baseline median。

最少測 2 個不同因果假設，最多 3 輪；每輪只改一個路由原因，保留完整失敗。
相同 metric 時選較小 patch；沒有過採納條件則 revert。剩餘一輪只用於有具體
機制的假設，不能改指標/裁判/樣本或為追分堆疊未驗修改。Confirmation 必須再次
全 gates PASS 且達同 20% criterion，否則 conclusion 是未確認，不再選 winner。
小樣本結果只支持這些固定 workload，不能保證所有未來 Agent 不退化。

## Capture 與比較失效

Host 先以固定 factory 準備 fixture，這是共同 setup，不計 Agent task 操作。
Consumer 用 immutable public drive.py 透明轉交其自己選的 argv 給既有
record_context.py；driver 的完整 stdout JSON 由外部 CLI capture 封存，再與保存
receipt/handoff/artifacts 相核。Worktree 清理後以存活 public bytes＋launch.cwd
binding 檢查實際 invocation，不讀已刪 path。Capture 要 actual process exit、
兩 stream EOF/fsync、atomic receipt、PID/group absence；turn.completed 不足。

Oracle/host/protocol bytes 改變或 source 漂移會結束舊比較；保留 invalidated
結果，重新固定新比較並 fresh baseline，不把換裁判當改善。Controls 必須包括
缺 capture、完整空輸出、假 prepared、changed identity、錯 capability、hash drift
與 cross-split group collision。沒有具體主張需要就不增加通用產品 schema。

## 延續與交付

Fresh handoff consumer 讀保存的 owner receipt 並刷新當前 mutable state，驗證
續行仍由同 owner 決定；不能從舊 prompt 重放寫入。固定反例進 reusable controls，
方法／承諾／oracle／evidence mapping 留既有 feature recipe，raw 留 atom 目錄。
所有 scoped evidence 與最小 P patch 經同一新 Issue/PR、既有 exact-head acceptance、
publication/landing、provider readback 及 local reconciliation。Decision 不授權 merge。
逐項 R1–R13 審計之前，不稱整體 architecture 完成。
