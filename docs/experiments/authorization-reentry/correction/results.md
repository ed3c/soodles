# 同一 Issue #193 的 correction 實證

結論：外部 lifecycle owner 選定／準備／handoff 的局部正確性改善，獨立 confirmation 成立；提示詞短入口未達效率門檻，已撤回。完整交付仍由同 PR #194 的新 head 與既有 owner terminal receipt 證明，本文件不授權 merge。

| 比較 | A/B/C 結果 | 正常 A 操作數 | 判定 |
|---|---|---|---|
| Baseline | 0/5 通過 | 9、9、7，未完成不作效率分母 | 重現缺陷 |
| R01：CLI 修正、原 P | 5/5 | 10、9、9 | 保留正確性 |
| R02：CLI 相同、短 P 入口 | 5/5 | 9、9、9 | 中位數減少 0%，撤回 |
| R03：撤回短入口、必要契約文件整合 | 5/5 | 9、9、9 | 固定最終版本；不宣稱效率 |
| Confirmation baseline | 0/5 | 未完成，不作效率分母 | 缺陷仍在 |
| Confirmation winner | 5/5 | 9、8、10 | 正確性確認 |

R03 的事前 integration addendum 明確記錄文件整合與原 R02 優化門檻的差別，未改舊分數。跨 Session 補充由 fresh consumer 使用 R03-a1 實際保存的 handoff，產品對後續 head 變動回 git.head 拒絕，保留同一 authorization／next，無 lifecycle checkpoint。原始 archive 同時包含 producer consumer 與 downstream consumer，不能把重新生成的 fixture 當成 handoff。

產品證據分開讀：509 項 suite 通過；外部 Noodle process controls 驗證 review→failed→同 order promotion、mode hold 和 ack 無轉移反例；publisher fixtures 驗證同 PR 分支與新 head；新 lifecycle controls 驗證固定 bytes 與錯誤 source 拒絕。命令／輸出／退出碼／canonical state 由外部 observer 擷取。單元測試自述 PASS 不當作 independent telemetry。

資料流：真實失敗及 owner readback → eval-audit findings → protocol／固定 code oracle＋controls → baseline → 兩個單因果假設與一輪必要整合 → 固定 winner → 一次 confirmation → 跨 fresh Session handoff → 既有 Issue admission／Noodle／publication／exact-head acceptance／landing。主 protocol 是原始 pin；封存的絕對路徑是實際執行身分，離線重播只重定位觀察，不改寫身分。

重構判定：外部 observation 要求修正 canonical state 觀察和 process hold。只保留 correction_proposal 的共用生成，防止 producer／consumer 比較漂移；未發現需要再做大範圍輸入輸出等價重構的證據。每層都有保留或修正的理由；不強迫提示詞也必須改。

限制：小型固定案例不代表所有缺陷／所有 carrier／所有未來 Session 都不退化。不宣稱 >=20% 節省、零猜測、零打擾或完整 maintenance。各 run 保留 token、cache、reasoning 與 elapsed 原始量測；模型 alias 的實際後端版本未知，並行執行的 elapsed 不用作因果速度指標。Confirmation baseline-a2 另有 stdout provenance gate 失敗，保留原分數，未更换 run。

原來 authorization-reentry 三輪與 confirmation 完整保留；本 correction 是發現交付缺陷後、同一未 merge Issue 內另行固定的比較，不能合併成同一次獨立 confirmation。交付 provider readback／terminal receipt 由原 owner 保管，完成前不得宣稱整體閉環。

交付前另發現 producer 把 correction worker 綁到 control base 的缺陷，已由實際 Git worktree fixture 重現並修正。v1 confirmation 保持原 pins，不能冒充 v2 實證；v2 另需真實 fresh writer 與 exact-head acceptance。詳見 verification/worker-head-finding.md。

v2 真實入口拒絕揭露 schema 2 的 instruction context 也必須綁同一 worker head；v3 已修正並以原 Issue／order 的實際資料完成未啟動 bundle 驗證。103 受影響 controls 通過，真實 fresh writer 與 terminal delivery 仍待完成。詳見 verification/worker-context-finding.md。

v3 對已由原 owner 完成的 host restoration 再要求新 checkpoint 的相同標記，造成重入拒絕。v4 移除兩個重複前提，保留原 owner／process／config／身分的實際 gate；103 controls 通過。詳見 verification/restored-readback-finding.md。
