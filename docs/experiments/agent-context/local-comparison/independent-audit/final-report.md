# #39 最終獨立 raw／export 審查

結論：本次固定輸入的三個狹義 local cases 有配對證據，支持 **scoped nonregression**，不支持 treatment 改善、降低決策成本或 baseline 缺陷。`authorizes_landing=false`；`unqualified_preregistration_compliance=false`。這不是 Issue RESOLVED 或 production landing 授權。

| 案例 | 採納配對 | 證據與範圍 |
| --- | --- | --- |
| runner-task | run-01／run-02 | 讀既有 control／common runtime，正確區分 identity 的 next:null 與 resolution；run-02 native:41／56 包含控制來源及實際九案結果 |
| unknown-write | run-09／run-10，唯一補充 pair | 原始 inbox checkpoint 上的 dispatch 得 owner exit1、dispatch.status=offered，沒有 request；實際前後 SHA256 相同。native:52／53 是直接結果 |
| fresh-transfer | run-05→08／run-06→07 | Producer 真實寫出 handoff，consumer thread/session 不同且晚於 producer exit；handoff bytes 原封不動。consumer native:19 的循序 loop 先讀 handoff 再讀當前 provider，後續 native:37／38 是自身 checkpoint 的新 owner 結果 |

原 unknown-write pair **run-04／run-03 仍保留 INCOMPLETE**。run-03 在暫存副本上操作，只觀測副本語義相同；未量測被操作副本的 after bytes。原 inbox digest 不能代填固定 judge/observe.py:79–83 的 read_owner 主體。初始 normalized green 已保存，修正為 null 後固定 judge 拒絕 checkpoint_preserved；這是證據缺口，不是觀測到資料損壞。補充 pair 在 launch 前凍結，兩臂只加相同的實際路徑／before-after 記錄說明，沒有再換 judge。

10 個實際 worker 均可串接 exact task/envelope、原生 gpt-6-astra/high turn、工具 request/result、自身 typed blocked、OS child wait0 與 recorder/session/PID。共 **70 native outer pairs、100 command results**。1 個 outer command exit2 是 run-01 的錯誤 source search；另外 run-09／10 的兩個 nested owner exit1 是合法拒絕，不能被 outer wrapper exit0 隱藏。Typed blocked 為 neutral execute 指定，因此不是自主選擇 stop policy 的獨立證據。Token 與 duration 欄逐筆從原生數值重算一致，只能作描述統計。

Fixed observer／recorder bytes 與歷史 88d38bfd 一致；共同 code 為 1ff2882891792b50d97529c9ee1a3e76eac1a6e7，五份 treatment 指引綁 388c86be5eef0f317b0ae38ffac70892f24c13de。Noodle／Codex binaries 與凍結 digest 相符。Issue 文字指定 PR48 run，但實際事前供應 exact-main run 35200528246，此 provenance 偏差保留。8+2 組 doctor 均不可稱 overall pass；僅 repo/cwd/root usability predicate 合格。

所有 10 個 fixture worker checkout 已由 Noodle 清除，exact source commits 保留在 control roots。初始 EPERM、普通 cleanup 拒絕未 merge commit、post-run adapter 修正及後續明示 --force 都保留；沒有把失敗改寫成首次成功。App receipt 皆記錄 scoped issues:read 與撤銷 204，這不是 reviewer 重新查詢 provider token inventory。

已核對目前公開 stage **1,381 個檔案**，root manifest 含 1,380 entries，SHA256：

`969d72ec1030a62df3e621ffa01eed1f712284aaf7c87496e576db9e307f4224`

全部 manifest bytes/digests、非遮蔽 source copy 與主要 evidence 子樹一致，未找到漏列的本次 native／live／process-exits／inputs／handoff 檔。10 份 rollout 逐行比對：只允許平台指令/context assembly 與內部 reasoning 的已宣告遮蔽；行數及 task/tool/result/model/final 行 bytes 都保留。CLI stdout、實際 wait、typed events 未改。既有 native output truncation 與 CLI aggregated_output 缺漏仍存在，不能宣稱完整 shell stdout；相關必要結論用 native tool results 支持。已知 GitHub/OpenAI key、JWT、private-key 格式掃描零命中，非任意秘密不存在的證明。

Production-authoring 附錄逐檔匹配來源；當次原 #39 authoring session 的 completed event 與 child wait0 留存。15 個被排除的既有歷史 session 皆列出理由與匹配的原始 hashes，原檔未動；此次 trial 失敗未被刪除。此附錄只做來源／隱私與 scoped authoring 記錄核對，不提供正式交付核驗。

保留限制：run-05 web cache miss、hook timeout diagnostic、來源輸出 truncation、run-08 錯誤 locator 的初始 packet（修正為 native:17）、未知服務內部模型路由、actual compaction、automatic discovery 與 uninstrumented natural exit。Local 證據不替代 cloud verdict；neutral task 明確要求讀文件，不是自動 discovery 實驗。

詳細逐行 join、sha256、normalized 修正與統計在 final-audit.json；export-audit.json 保存逐行遮蔽核對。此審查綁上列已凍結 stage；後續只能以獨立 manifest extension 附加 final reviewer／receipt／明示後處理失敗資料，不能改既有受審 bytes。current-report.md 的 EVIDENCE_COMMIT 仍為待發佈替換的草稿 placeholder。正式 candidate 的 exact-head acceptance、merge／closure readback 與 original-order reconciliation 另循既有 owner。
