# 同一原 order 的 correction 與本機 reconciliation

本次 Issue 是 ed3c/soodles#264。整合基準為 `00febf390f621c26f454c2146346e283d1ac0b8e`。
本文件記錄 admitted writer 的來源修正。Publication、Linux exact-head CI、landing 與終端本機 reconciliation 仍由原 owners 執行。

## 原 claim 與推論修正

原 claim 是外部 `2089b384a17c9786bb79fccf3c13e7d4a6e478b4` 已使 #254 原 child resolved。
若據此推論可以整檔覆蓋 main，隱含 premise 就是兩份來源和 judge 的條件相同。
這是本次要排除的推論，不是使用者要求的做法。
已讀 `source-scope.md`、兩份 context-fix result、independent-review，以及 `control-reconcile-child-run.stdout`。
原 terminal 記錄 #254、PR262、head `4831729cd53eeb91f1790eee23fbc7d62c3e5d63`、merge `00febf390f621c26f454c2146346e283d1ac0b8e`、`status=resolved`、`next=null`。

推論失敗在來源和 judge 配對不同。External2089 基於舊 `cc0d235d0248947dd117a31c37f0a1d62924b4de`。
Main 已加入 generic repository binding、retained publication、cost feedback 和 integration sync。
整檔覆蓋會移除這些能力。Main 另有 native-before-control 循環依賴，舊配對的成功沒有覆蓋它。
支持的結論是按 causal hunk 整合缺少的 correction，另驗本次 main lander。
必要 action 是保留原 owner、固定 judge、原失敗紀錄，並在當前 source 跑必要 controls。

## 身分與執行順序

原 authorization source、先前 target、失敗 candidate 與新 descendant target 各有用途。
Correction producer 只更新 schema-3 base 和既有 base pins。
它保存原 task、prompt、failed-CI context、carrier、attempts 與 parent-selected native capability。
Worker 驗證 sealed typed entry，先整合固定 target，再完成原工作。

Provider 確認 merge 與 closure 後，原 lifecycle 先驗 exact parked custody，再停止自己的 loop。
它保存 intent，將乾淨且已註冊的 detached control 從原 source 推進到 selected base。
Lander 驗原 claim、provider confirmation、session custody 與 Git 狀態，才讓 control 包含 merge。
原 native publication reconcile 因此取得所需 ancestry。
Native canonical completion 成立後，既有 `sync_integration` 更新唯一 registered integration checkout。
原 cleanup 與 host restore 接著完成。

單純前移 merge 會跨越 session 檢查，也缺少 durable intent。
新增 coordinator 則會重複既有 owner。
本次沿既有 owner 保存各自的 intent，公開 continuation 不變。
Active、foreign 或 missing custody 不能移動 control。
未知 Git 結果只讀回 exact intent；未知 native 回覆若已有 canonical completion，就採納該證據，不能重送。

## 已保留的證據限制

`0c285e0` 與 `b839cb6` 的主要修正已在基準，不重複匯入。
`f1ce199` 的新用途限於有 typed custody 的 correction ACK 與 created-Issue marker。
舊 CI/base result 的 234 distinct cases 與 control result 的 173 distinct cases 是歷史範圍，不是本次測試數。
舊 exit 143 的原因仍未知。Control result 原先的一次 failure 和一次 error 由其後修正處置，歷史不刪除。
舊 Git 與 file-lock fixtures 有真實操作，但 PID、native completion 或 cleanup 部分使用 stub。
原 #254 live terminal 只支持其原 fixed lifecycle/judge 配對。

當前 schema1 scope 接在 schema2 後，control alignment 仍需追到原 source。
原外部 correction source 沒有為這種 schema1 selection 提供新的 typed native acceptance 追溯能力。
缺少 selected native capability 時仍拒絕，不猜另一份 capability。

## 本次驗證與後續責任

Writer 已完成來源整合、必要 controls、獨立 review 與 P-class feedback。
下表各次命令均由 `./soodles test --module ... --reason ...` 執行，exit 都是 0。
檔名相對於外部證據目錄 `/tmp/soodles-264-evidence`。

| 保存的 stdout | 範圍 | 測試數 | 正常執行秒數 |
| --- | --- | ---: | ---: |
| `producer-final.stdout` | scope amendment、base readmission、supervisor authorization | 42 | 23.064 |
| `activation-retest.stdout` | atom repair、cleanup continuation | 27 | 29.609 |
| `lifecycle-retest.stdout` | lifecycle activation | 22 | 86.316 |
| `landing-final.stdout` | landing、landing continuation | 75 | 97.980 |
| `final-core.stdout` | issue atom、correction preparation | 155 | 111.079 |

這些是分次必要驗證。表中時間不是端到端延遲，也不建立成本改善主張。
初次整合命令的外層程序 exit 143，原因未知。`integrated-process.json` 保存該結果。
不能將整次命令標為 PASS。
`integrated-tests.stderr` 另保存各模組的完整結果。
其中 candidate verification、candidate publication、cross-repository delivery、cost telemetry、issue execution、admission revision、local continuation、publisher receipts、stage outcome、supervisor admission 共 174 個 tests 已通過。
本次重用這些已完成模組的對應證據。後續修正沒有改動它們所驗的 producer 或 consumer 分支。
改動的 correction、atom、legacy producer 與 activation 分支則使用上表的新結果。

Lander fixture 的初始 native order 尚未 completed，detached control 只到 base。
合法 parked review 先通過 custody，control 才 fast-forward 到 merge。
接著 fixture 的 native completion stub 回報完成，原 integration owner 和 cleanup 繼續。
Git 操作使用 disposable repositories；provider、native completion 和部分 cleanup 是 stub。
這些 controls 不證明本次 live delivery 已完成。當前來源仍需原 owner 的 Linux exact-head acceptance。

本次失敗與修正均保留。`landing-first-run` 的一個舊預期由 integration intent 改成更早拒絕的 control outcome。
`producer-tests` 的新測試改為比較 parser 正規化後的 write paths。
`scope-diagnostic` 暴露 legacy schema-1 沒有 base_head 的相容性缺陷，已保留 same-base bytes 並新增拒絕 descendant 的控制。
`correction-diagnostic` 的 typed ACK fixture 改用原 scope projection 選出的 bundle。
`atom-retest` 的自然接續 fixture 明確令 owner availability 回傳 None，讓測試進入預定分支。
產品 validator 沒有為這兩個 fixture 放寬。

獨立 source/comment review 找到兩個接線缺陷，並確認修正。
第一個是新 parked 路徑攔截既有 activation 或 restored checkpoint，現已交回原 owner。
第二個是遺失 native 回覆後，lander 可能直接到 resolved，atom 卻未採納原 completion intent。
現由原 lifecycle 在 lander 前採納 canonical completion。
Pending、observed、resolved 各有控制，未知結果不重送 reconcile。
最終 review 核對 14 份來源 bytes，沒有剩餘阻擋 finding。
完整 finding、修正史與 hashes 在 `independent-source-review.md`。

兩份 P guidance 的保存文字已完成 review-writing。
原 stage-outcome feedback 保存兩輪。首輪要求三案觀察，沒有 behavior failure。
Fresh native consumer 使用固定 instructions 和 inputs，沒有繼承對話或取得預期答案。
Schema Manager 對 descendant route、custody、unknown completion 回傳 `VALID`、`PASS`。
原 writer 已消費 `consume_verified_behavior`，結果保存在本目錄 `pclass-feedback.json`。
該結果限於 consumer report；carrier 沒有提供完整平台 transcript。
它不證明 runtime effects、普遍服從或較少決策，也不授權 landing。

方法與 SHA-256 記在 `methods.json`，選擇與取捨記在 `plan.md`、`decisions.tsv` 和 `synthesis.md`。
本次依 Poteto Bug fix 執行。已知 live 故障採用原 evidence-reuse 規則，沒有重播未知效果。
兩個設計 Agent、獨立 reviewer 和 consumer 使用 native carrier，模型依主機規則繼承 parent。
這不是跨模型比較。Carrier 沒有 Comment Sicko 專用 subagent_type，故保存獨立 comment review 的實際範圍。
沒有提交故意失敗的中間版本。失敗輸出保留在外部證據，遵守本次提交必須通過的約束。

外部證據另逐檔原樣保存於 `/Users/neon/soodles-audits/manager-coverage-loops/landed-correction-import/writer-264-evidence`。
`archive-index.json` 保存相對路徑和 SHA-256。原 feedback 的絕對路徑與 bytes 不改寫。
複本提供耐久讀回，不建立新的 authority。
沒有執行 full suite、benchmark、live fault 或歷史 provider write。

本 Issue 只交付 demonstrated correction。
Publication 前的 proactive base detection、再次 retarget、#251、#248，以及外部 `../handoff.json` 的 parent outcomes 仍由 supervisor 保留。
此結果不建立 full-autopilot、fewer-decisions 或所有 CLI coverage 已完成的主張。
