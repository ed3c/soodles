# #238 驗證結果

本記錄支持本 unit 的 writer candidate。它不宣稱原 #229/#237 已完成接續。
所有 software controls 都由 Test Manager 選取。沒有執行 full suite。

## Source 與 consumer controls

`final-controls-2.json` 記錄 182 個 tests 通過，耗時 52.432 秒，4 個 workers。
範圍是 admission revision、instruction context、interruption recovery、issue atom、
issue execution、scope amendment、stage outcome 與 supervisor admission。

其後收尾修正集中在 history projection、fresh branch identity 與 fixture 身分。
`final-owner-controls.json` 記錄該輪 130 個 tests 通過，耗時 48.5 秒，4 個 workers。
範圍是 admission revision、candidate publication、issue atom、scope amendment
與 supervisor admission。這兩個數字有重疊，不能相加當成 unique coverage。
最後自審修正了 scope_custody 的原 carrier 讀回。custody-controls.json 記錄
24 個 tests 通過，耗時 12.958 秒。該輪涵蓋 exact carrier、foreign custody、
successor、pending write 與相鄰 scope 路徑。先前 successor-controls.json 的
11 個 tests 也通過。未變動的 worker/native 路徑沿用其原結果。

新控制涵蓋 base-only、criteria-only 與 combined projection。它們比對未選欄位
保持原值，並拒絕 scope/acceptance/source 偷換、candidate 自選 hash、錯誤 base
pin、非後代 target、dirty retained tree 與 changed sealed bytes。
原 typed completed event 不改報 blocked。原普通 scope 路徑仍通過。

Owner control 在 Issue patch 回應遺失後只讀回。它為 request-changes、edit-item、
requeue、release 分別保存 intent 與 acknowledgement。相同 pending readback
不追加第二個 control。Producer 的已存在 bundle readback 不重建 bytes。
新增 history control 驗證兩次 revision、原 authorization bytes、body marker、
body hash 與 ack。重複採納同一 selection 不重新 capture custody。

普通 publication claim 在 target 未整合時拒絕 `git.base`。整合後同一個普通
validator 接受 claim。這個控制沒有呼叫 live provider。

## 固定 external reader

`external-reader-2/results.json` 記錄實際 read-only validator 執行。
Reader 是 supervisor 指定 external-owner 的 issue_admission.py。
SHA-256 是 `5697876cc0d97b97d33a4eafe4f69a49a4b8309fe37114941a9e7dda930e331e`。
它沒有從 candidate import，也沒有更改 judge bytes。

| Case | 觀察 |
| --- | --- |
| integrated_original_instructions | 接受 standard envelope、原 instruction source 與整合後 candidate |
| missing_manifest | 拒絕 candidate.missing_required_paths |
| wrong_digest | 拒絕 candidate.instruction.treatment_sha256 |
| replaced_instruction_source | 拒絕 instruction_context.source_head |
| unintegrated_target | 拒絕 candidate.outside_write_paths，因 fixture 的 target-only file 不在 retained candidate |

最後一列不是獨立的 ancestry discriminator。Ancestry 的直接正負例由上面的
普通 publication claim control 提供。這些結果支持相容性，不授予 acceptance。

## Accepted native dispatcher

`native-2/result.json` 使用 root 的 native-accepted.json 所固定 binary。
其 digest 是 `347dc64b9d98bc7f290ab6e6e4a54866a11f8a5bcb653b91122becb59c31acc5`。
Producer 與 consumer 都重新核對 acceptance/interface refs。

Disposable native loop 先產生 completed review，再沿原 controls 接續。
第二個 worker 讀到 retained committed candidate 與原 instruction context。
它整合固定 target。實際 stage-outcome event 記錄 completed nonblocking。
Consumed interruption marker 的 history count 是 1。Revision successor count 是 1。
Prepare/manual hold 的提前 dispatch 數是 0。Revision dirty exception 是 false。

外層 interruption fixture 的 dirty_preserved=true 只描述原 interruption 段。
它不表示本次 revision 允許 dirty entry。Revision 段另驗 clean committed head。
這次使用真實 native dispatcher 與 worker entry，沒有 model call 或 live provider。
因此它證明 custody/dispatch/entry，並不證明模型能解決任意 merge conflict。

## P-class feedback

review-writing 審查 system contract 與 execute skill 的保存內容。
eval-audit 檢查需求來源、條件與 evidence 分工。Fresh consumer 只取得這兩份
指引和三個 case inputs，沒有取得 expected values 或 reviewer condition table。

Cases 分別是 retained candidate 的 target integration、錯誤 required reference
與 unknown Issue patch。Consumer report/簡短 trace 的結果均符合原需求。
原 `stage-outcome feedback` 記錄 round 1。Schema Manager 回傳 VALID、SUPPORTED
與 PASS。Next 是 task-owner 的 consume_verified_behavior，required 為空。
Writer 已消費此結果。Test Manager 沒有要求另一輪 eval 或 software controls。

Feedback selection digest 是
`25b825b433742861c545320b3ccc815b9277432c7c3c1ba44eee0869a8812860`。
Schema feedback 耗時 9.715333 ms，projection 耗時 0.066166 ms。
這只是該次正常 feedback projection。模型耗時、tokens 與價格未知。
Evidence 是 consumer report，不是完整平台 transcript。沒有比較改善 claim。

## 保留的失敗與限制

最初 fixture 缺 carrier，之後 path ordering 不符合 canonical contract。
兩次都修正 fixture，保留原 logs。相鄰舊 scope fixture 又暴露無條件 carrier
讀取；實作改為只在 typed revision 分支讀取。後續相鄰 controls 通過。
不存在的 test_test_manager module 曾被 Test Manager 在執行前拒絕。
Writer 改選實際存在的相關 modules，沒有以 full suite 補過。

收尾 history fixture 的 provider target 和 Issue number 缺漏已修正。
一次 shell 找不到 python；之後使用主機已安裝的 python3。
部分 external-reader/control process 曾以 143 結束，原因未知。
這些 partial results 不算通過。後續有 source 修正或完整對應 readback 的結果
分別保存。failure-history.json 與 final-failure-readback.json 保留失敗鏈。

Poteto Bug Fix 方法記錄於 methods.json 和 plan.md。
目前 carrier 沒有原方法的 Grok/Claude 或 Comment Sicko subtype。
本次使用可用 native agent 作只讀設計審查與限定 consumer observation。
這不是上述 subtype 或多模型驗證的等價證明。

原始 evidence 位於 `/tmp/soodles-238-revision-work`。
持久副本位於外部 evidence 根目錄的
`prepublication-base-owner/soodles-238-writer-evidence`。
該目錄的 archive-index.json 綁原始路徑、相對副本與 SHA-256。
原始 receipts、logs、instruction snapshots 和失敗結果保留原 bytes。
候選 head/tree 與乾淨狀態由完成後的 candidate-receipt.json 記錄。
本 unit 的 publication、Linux acceptance 與原 atom 正常使用讀回仍屬 root。

## Exact base integration 的目前結果

本輪把原 candidate 合併到 supervisor 指定的
`a90adfde0e0208e76183f8420aa7b0075d9edaf3`。本節的 evidence 位於外部
`prepublication-base-owner/soodles-238-integration-evidence`。前面各節保留原輪次。

Test Manager 的 `controls-1.json` 選取 232 個 controls。220 個通過。
Revision 模組的 12 個 controls 中有一個 fixture 失敗。它缺少新 base 要求的
`issue_body`。補齊後，第二輪發現同一 fixture 還缺 `authorization_sha256`。
兩個欄位都屬 canonical binding/state。修正沒有放寬 production 檢查。
`controls-3.json` 的 12 個 controls 全部通過，耗時 13.672 秒。
它們也驗證 projection 同時保留完整 body、有效 contract 與 sealed revision。
未變動的其餘 220 個 controls 沿用首輪結果。沒有執行 full suite。

`external-reader/results.json` 以原固定 external reader 執行同一組正負例。
整合後 candidate 被接受。缺 manifest、錯 digest、換 instruction source 與
未整合 target 都被拒絕。各例的範圍與前述限制不變。

第一次 native run 在進入 revision 前收到終止訊號。`native/failure.json`
保留 process 與 readback。現有證據無法識別 signal 發送者。它不算通過。
下一次 run 增加 fixture 發送 signal 的實際 call-stack 記錄，並單獨執行。
`native-2/result.json` 記錄通過。Revision successor 與 marker history 各一次，
提前 dispatch 為零，dirty exception 為 false。原 instruction context 保留。
`native-2-signals.jsonl` 記錄該輪正常停止 daemon 的 fixture 呼叫。
新結果支持本輪 native 路徑，不解釋第一次未知的 signal 來源。

合併後 execute 指令 bytes 已變。Writer 沒有把舊 P-class pass 當成本輪結果。
原 session 的固定 launcher 記錄新的 feedback。Round 1 要求三個 observations。
Fresh native consumer 讀取保存後的指令和原案例，沒有取得 expected values。
Round 2 回傳 VALID、SUPPORTED、PASS。Writer 已消費
`consume_verified_behavior`。`pclass/review-readback.json` 保存回應和限制。
這仍是 consumer_report，沒有完整平台 transcript 或比較改善 claim。

本輪 outcome 與 feedback 使用 supervisor 指定的
`"$SOODLES_ADMISSION_LAUNCHER" stage-outcome`。此機械入口保留本輪原 prompt
格式與固定 owner。Candidate 的新 body-aware adapter 用於後續按新格式
建立的 sessions。本次不更換原 admission 的 instruction source 或 judge。
