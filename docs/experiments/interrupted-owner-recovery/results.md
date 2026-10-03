# #234 接入觀察

本輪完成 recovery outcome consumer 與 control ack 修正。
本輪 admission 已包含原先缺少的 adapter、activation 和 controls。
工程 candidate 的 source、必要控制和 scoped P-class feedback 已齊備。
Publication、exact-head CI、landing 和本機 reconciliation 仍由原 owners 接續。
未操作 live #229／#232。以下結果不宣稱它們已恢復，也不宣稱總需求完成。

## 本輪控制

原始結果保存在 `/tmp/soodles-234-resume-evidence/`。
Test Manager 選取下列必要模組，沒有要求 full suite。
表格只列各範圍的最後一輪結果。先前輪次保留，不累加為獨立 coverage。

| Evidence | 結果 | 支持範圍 |
| --- | --- | --- |
| closure-controls.log | 14 passed | 新 outcome closure、舊 explicit／implicit 原 repair identity |
| outcome-controls.log | 32 passed | Launcher bytepin、outcome／feedback imports、唯一 successor 和普通入口 |
| ordinary-controls.log | 59 passed | 普通 worker、scope resume、authorization 和 feedback owner 相容性 |
| control-review.log | 13 passed | Ack 重入、未知控制、外來 ack、兩個 snapshot 競態 |

首次 ack fixture 缺少 contract，失敗已保存在 control-review-fixture-failure.log。
補上 fixture 後，control-review-before-fix.log 重現正確 ack 搭配舊 snapshot 的誤拒絕。
修正後，edit 與 release 都在 ack 成功後重讀 owner。重入不重送控制。

`native-adapter-2/result.json` 記錄 supervisor-selected binary 的實際接入。
Prepare 和 manual hold 的 dispatch count 均為 0。Release 後只有一個 successor。
Generated external provider adapter 通過 worker admission 後才執行 sentinel。
Sentinel 讀取 exact native receipt，合法修改 candidate，再經 external launcher
寫入同 session 的一個 completed event。原 candidate outcome 檔案 bytes 保留。
原 session events 和 untracked 內容保留。沒有啟動 Codex 模型。
Provider 使用明示的本機 reader，沒有 live GitHub effects。此配置不是網路封包測量。
`native-regression-1/result.json` 同時保留原 `--native` 入口相容性。

可重跑的接入 fixture 入口如下。三個參數由當次 supervisor 選定。

```text
PYTHONPATH=. python3 -B tests/test_interruption_recovery.py --native-adapter BINARY SHA NEW_EXTERNAL_OUTPUT
```

`native-adapter-2/cleanup.json` 記錄 daemon returncode=1。
SIGTERM 與 backlog.done 發生競爭，stderr 保留 signal:killed。
`process-readback.json` 確認 daemon 51678 與 sentinel 51824 均不存在。
這個 fixture 只證明 native／worker／outcome 接線。它不證明 daemon terminal success，
也不執行完整 issue-atom resume/run、schema-3 feedback、publication 或 provider closure。
Python controls 分別覆蓋採用 selection、intent、ack 和相容性。
原 carrier 到新 carrier 的 publication／cleanup 傳遞另有 source trace，沒有 live 執行主張。

## 本輪 P-class feedback

使用 review-writing、technical-writing、unslop 和 eval-audit。
修改後的兩份 Markdown 與 issue_execution.py projection 均綁定 exact bytes。
Fresh native consumer 沒有 inherited conversation，也未取得期待值。
四案覆蓋 dirty worker／supervisor lineage、implicit source、unknown prepare、outcome route。
Schema-2 條件直接引用當次 task／contract，沒有語意模型 judge 或比較改善主張。

`feedback/response.json` 已寫入當次 Noodle session 的非終態 feedback event。
Criteria 為 SUPPORTED，evidence 為 VALID，behavior 為 PASS。
本 writer 已消費 next.operation=consume_verified_behavior，記錄在 feedback/consumed.json。
Test Manager 沒有要求額外 consumer、software module、physical control 或 full suite。
Schema 為 3.425 ms，projection 為 0.053 ms。模型時間、tokens 和價格未知。
四個 report／trace 是 consumer 自錄證據，不是完整平台 transcript。
原先三案與失敗紀錄均保留，沒有把舊指令的 PASS 冒充新 bytes 的結果。

第一次 fresh consumer spawn 因 thread limit 被拒絕。
待實際完成的 threads 可讀回後，新 fresh consumer 成功。沒有換 runner 或繼承舊consumer。
Poteto 指定的 Cursor roles、Comment Sicko、跨模型 arena 和 deslop 不在可用能力中。
本輪只使用 native 同模型 tasks，不宣稱完成那些方法。
Model the Domain 原則使回報沿用既有 envelope、launcher 和 outcome owner。
Prove It Works 原則要求讀取同 session 事件與實際 process cleanup 結果。
方法載入記錄在 methods.json；分工與理由在 plan.md 和 decisions.tsv。

## 本輪 source 與 evidence bytepins

以下 source hashes 是保存後的檔案。它們不授予 verifier 或 landing authority。

| Source path | SHA-256 |
| --- | --- |
| `issue_atom.py` | `929b86e32aad384f846f5be1e562ce0062b1e979ecead0389de3788c5bc2fa80` |
| `issue_execution.py` | `3a665e8914924222832550f850d8cd9d4ff1abf54144df34aed6872f43c3dc28` |
| `stage_outcome.py` | `7fab44e6c1ea67351b49a3aaf13194d57ca92b08ec09e5f1ead3facf940b756b` |
| `supervisor_admission.py` | `b7ded57890e05df25db8192838302a30061f513bb84019989e49a91d21b8e42b` |
| `tests/test_interruption_recovery.py` | `d77dd9cfc5630348fe15492b5eea59792ea6677f15052ba8efd64a1d04332241` |
| `tests/test_lifecycle_activation.py` | `fc131805a434fc32efbb112bab1e82f896d7fdc7b1f7fc9685d161dfb9763543` |
| `tests/test_stage_outcome.py` | `33869059151a7486fbfc47a42aa022197701e4101a346c6b097583526f4f5df2` |
| `tests/test_supervisor_admission.py` | `df8f24d5b9c63805327c6b1201b3e7dbb406c6ed0db41f7b065ee0619b882e4d` |

下列相對路徑以 `/tmp/soodles-234-resume-evidence/` 為根。

| Evidence path | SHA-256 |
| --- | --- |
| `closure-controls.log` | `cb14ef280cb69685d05342b1bd1c852b5b7b068e55504c5706025db22404d5c9` |
| `outcome-controls.log` | `ffaaafacc317a44f4e7587c814c1a810793b505547e90493f8f16e91addb8520` |
| `ordinary-controls.log` | `296145b4995aed7eedc5a733385e6aff4f481cd286ee6660fbe9f0454c085d8b` |
| `control-review.log` | `f7213c9a011c47d9918675f45d05a5edfa5312baef70bedd47e17fe04da5e26c` |
| `control-review-before-fix.log` | `7e1839b2c2b2b212cb9dc561dfac03a2648b6f47e40be65a26b3175f13f49ad8` |
| `control-review-fixture-failure.log` | `ea89487fe8eea42b8eadcf529eb0c4d73bea03419c7f738b206a2221ebd22598` |
| `native-adapter-2/result.json` | `3a440396c7d6f9b61a37a665a311c62b35085b847533dcc35e85d71509842e15` |
| `native-adapter-2/11-outcome-readback.json` | `8f0a667a8306b746e88fc86f14f75ef28db979c11d3873cd0797699c63851b32` |
| `native-adapter-2/cleanup.json` | `d340ad82cbe6140fc9fe0e423cb9cb6ae4b52fa70fe14c3e302aa3264a058e82` |
| `native-adapter-2/process-readback.json` | `e96558c800f433d313011d5966488f132b9931f2205322e03025756d35cbc2a6` |
| `native-adapter-2/scope.json` | `c5a9bde759d2e95ed2c8d551654737bf0437276f8ddbb8ac98f61d43669f63b3` |
| `native-regression-1/result.json` | `14bdeaba33d12207f67b3399a7c503acb28a890fc7f25b83395ba66d05bf6acf` |
| `feedback/protocol.json` | `3d4f61b8090a01d25fbcf9f62458ea3da75a3aa16401a71695f78f87fd4c13a5` |
| `feedback/selection.json` | `af252593238138c8ce5d747cf76cd8e68073eee564af347367db0645af48dedb` |
| `feedback/response.json` | `98383a9dbe78a83a758628094b7e7d21cc8c6f540096c1665de6286293a94e42` |
| `feedback/consumed.json` | `49e1a3ad5b545a119c005136f471860e1c11021a09cb28ade8feec09cf79c78d` |
| `methods.json` | `3f1a2045f36f25e39d1eee494752e80acb3fff284ab6a6edab5cae84030a9d8b` |
| `decisions.tsv` | `53da923f04615bd7af42f28c8cdb048cdc1261d4ab2d2e25133f97ee427c7739` |

# 首輪 writer 的觀察

以下保留首輪 commit 36c80cc 的結果。當時 candidate 未完成。
當時 Stage-outcome consumer 的 scope 缺口阻止 writer completion。
未操作 live #229／#232，未建立或修改 provider Issue、PR、judge 或 authorization。

## 已觀察的控制

Test Manager 選擇 scoped modules，沒有執行 full suite。
原始 stdout/stderr 保存在 `/tmp/soodles-234-evidence/`。
下列各 run 有重疊控制，不可將 count 相加當成獨立 coverage。

| Run | 結果 | 支持範圍 |
| --- | --- | --- |
| compatibility.log | 50 passed | 普通 worker、supervisor bundle、external lifecycle 相容性 |
| recovery-source.log | 33 passed | 固定原 Git source、非零 ledger、system context、prepare unknown |
| final-focused.log | 46 passed、1 failed | Scope resume、atom repair、Test Manager；bundle assertion 錯誤，後續修正 |
| bundle-final.log | 8 passed | Bundle 保存原 task/instructions、實際 local backlog sync |
| closure-compatible.log | 14 passed | Explicit／implicit 原 closure 與既有拒絕相容性 |
| final-recovery.log | 23 passed | Descriptor adoption、foreign prompt refusal、unknown held start、dirty successor 和 repair ledger |

Python worker 控制以 mock native readback 驗證其邊界。
Delayed-result 控制由真實短命 process 延後寫入 receipt。
它驗證 worker 等待後才執行 sentinel，以及 timeout、foreign receipt、
owner 消失、candidate drift/readerror 和 fresh Issue 拒絕。
它沒有重送 prepare、start 或 dispatch。它不等於實際 worker adapter 接入。

原生 CLI/process 控制使用 supervisor 指定的 Noodle bytes。
`native-agent/run-3/result.json` 通過原生 prepare、manual hold、edit、release、
唯一 successor、dirty/untracked 保存及原 session events 保存。
保存到 tests/test_interruption_recovery.py 的同一 fixture 由
`native-saved-2/result.json` 再次通過。此 run 的 successor 為
`order-1-0-attempt-1`／`order-1-0-execute-20261003-083348-38ef89`。
Prepare 和 manual start 的 dispatch count 都為 0。Release 後 count 為 1。
Sentinel 不呼叫 Codex 模型。Fixture 使用本機空 backlog adapter。
沒有封包擷取，不能把這個配置描述成獨立的網路流量測量。
`native-saved-2/process-readback.json` 確認 fixture daemon 25006 與 sentinel 25036 均不存在。

可重跑的 fixture 入口如下。BINARY、SHA 和 OUTPUT 都由當次 supervisor 選定。

```text
PYTHONPATH=. python3 -B tests/test_interruption_recovery.py --native BINARY SHA NEW_EXTERNAL_OUTPUT
```

本次 selected binary SHA-256 為
`9fdbafc13715ee17a4142c7464350a21d74fdb4e62ef806de2905509748237ef`。
Source head 為 `b372773b0baa5c33fad87b40591dd67c45e124fc`。
Native CLI fixture 和 Python worker controls 分別支持各自邊界。
完整 resume/run/bundle/native/worker/stage-outcome 整合仍需 scoped admission 和驗證。
Control ack reentry 與原 carrier 到 cleanup 的完整執行也尚未觀察。

## 失敗與修正紀錄

Native run-1 把 agents.codex.path 填為檔案。Native config 要求目錄並附加 codex。
Run-2 錯誤要求 canonical mode 變 manual。`--mode manual` 是 effective override。
這兩項 fixture 前提已修正。原始 failure.json 保留，沒有替換 binary。
保存 fixture 時曾把內嵌 script 的 pathlib.Path 改成未匯入的 Path。
`native-saved/failure.json` 保留該失敗。修正 import 後，native-saved-2 通過。

Bundle control 初次使用不符合 producer prefix 的 argv，因而被拒絕。
第二次以未存在的字串 admission-backlog 當預期而失敗。
修正後直接執行保存的 backlog sync 並比對回傳 identity、task 和 admission_snapshot。
各失敗 log 保留。沒有停用測試或繞過 gate。

新增 literal closure reader 後，舊 malformed-source control 先遇到未包裝的 SyntaxError。
改為 owner refusal 後，第二輪指出既有 source_sha256 diagnostic 不相容。
修正 validator 邊界，保留舊 refusal field，並附上原 literal parser diagnostic。
closure-final.log 與 closure-corrected.log 保留這兩輪失敗。

## P-class feedback 與方法限制

使用 review-writing、technical-writing、unslop 和 eval-audit。
Scoped eval pipeline 以原 requirements、exact saved instructions 和 Boolean
consumer outputs 比對。它不使用未校準的語意 judge，也不主張統計效能提升。
三個 case 分別判斷 dirty worker／supervisor lineage、implicit source、unknown prepare。
新 native consumer 無 inherited conversation。它沒有取得 expected protocol。
Capture 是 consumer 自錄 report/trace，不是完整平台 transcript。

`feedback/response.json` 記錄 round 1，criteria SUPPORTED、evidence VALID、behavior PASS。
本 writer 已消費 next.operation=consume_verified_behavior。
Test Manager 未要求更多 case、software module 或 physical control。
Schema 約 3.960 ms，projection 約 0.038 ms。這不包含模型或 process 時間。
Token、價格和完整模型 elapsed time 未知。
這個 PASS 不證明原 #229 能完成 runtime，也不解除 consumer scope 缺口。

Poteto 所指定的 Cursor Task roles、Comment Sicko、跨模型 arena 和 deslop
不在本 Session 的已提供能力。已完成 native 同模型只讀 source review。
它不是那些方法的等價執行。Review 找到的 pending successor 與 fixture import
問題已修正。完整 adapter 接入缺口仍保留。

Model the Domain 原則使 descriptor、原 checkpoint 和 native custody 保持單一 ownership。
Prove It Works 原則要求讀取 actual native receipts，並重跑修改後保存的 fixture。
方法 path/digest 記錄於 methods.json，決策記錄於 decisions.tsv。
沒有可讀的完整平台 transcript；review 依本 Session 訊息及保存的工具結果，保留此限制。

## 保存的 source 與 controls

以下 SHA-256 綁定本 candidate 的實際檔案。

| Path | SHA-256 |
| --- | --- |
| `issue_atom.py` | `0a0193b0f3c739cf71507666c184a675115db4e862314efa51e95cffe7677b30` |
| `issue_admission.py` | `b193e8a0ba27ee80ddd6219f25617135997e00905baa0fcddad757ae50bbc183` |
| `issue_execution.py` | `ac459f528404add80edf99858f61ccadea0e97d37de9f2b988f405c14dc12eba` |
| `supervisor_admission.py` | `003107d956148d956ed9211a0757a733924c5485ef14801edd758454653d5363` |
| `system_context.py` | `8091fd0f19e04b1f2c0a59464c7fbda1174d3a46d35f9f1da1a4019fdf54eba6` |
| `soodles.py` | `74676f73e116661249dc08406409bcb94d4065eb6f0dca7216dc529e1f5af156` |
| `test_manager.py` | `97cd1fa4d2c02a26181c0852fadee369d7f9d113d43bec0b0e3115213d04050d` |
| `tests/test_interruption_recovery.py` | `feb0c7d4ef9f9fe3ea80cffbeb55ec827493dd83a4745c7eaf8b3423d436a2ee` |
| `tests/test_lifecycle_activation.py` | `90e24ec8d91de18a7f6c2d0057723035d475487a4f87d70f6d2fdf316ad75d0a` |

## 外部 evidence references

這些 raw receipts 原樣保留。絕對路徑根為 `/tmp/soodles-234-evidence/`。

| Path | SHA-256 |
| --- | --- |
| `compatibility.log` | `82d87bc3b571432e4b650a78296a279ae873b7c277d231d7ad85f12513608d45` |
| `recovery-source.log` | `e502163758e1aa546e6ae25f7d485c17b79418041ffcb9165e0a6eae9927af81` |
| `final-focused.log` | `ac2032a684be7f1bdf83a8ffa4450bf548d05b8b91060ca680be700f66797c16` |
| `bundle.log` | `4306ee195b2e82aa3e87e19318581d7a34834b3c4b4338c8a275fa04c5d802dd` |
| `bundle-final.log` | `eb5d240ab3dc60ec82fee84f7daecc4c60f5a793a1d7752908df13535a722ec1` |
| `final-recovery.log` | `6baedd1e9ff591058eba578889c7189cde625871279652b5cb531177be44badd` |
| `closure-final.log` | `2661b101f2448ca372ee679933b4f25b32c90be40a865c69edf2279de7cca47c` |
| `closure-corrected.log` | `97deb462868c1d7b1a26705ed0e04aa1894fc44f212b116329e5de27f9e4136c` |
| `closure-compatible.log` | `8756f1c815249fd05b7c99eb3ff25066e54936fd4626b74937fc63bb9eecda63` |
| `native-saved/failure.json` | `700b6c97fa1f318f6b79237348cb54936e73cb20d762d1c03f1c762018b75a11` |
| `native-saved-2/result.json` | `1b77813d510df3c2c16a198addbb83d8e9f03a8f92c49a406a694bb9e7d1b1e4` |
| `native-saved-2/process-readback.json` | `903b4a46038474515e2ee77962e94bc722fb5f0d442ec65de8ccb15e1c7dd314` |
| `feedback/response.json` | `b6f5591484d39ae5145c7b8c76e17fcb108e6ce0b1ce18fcb49a7a47d0a84bdd` |
| `feedback/protocol.json` | `e6af8e8a8ce9d8ab3c9ff0aaf46a5813be89d93930d748e0eb14cf819f5e7786` |
| `feedback/selection.json` | `03f17fd6d02406170a83d4fefcd863acec4436a058ccd17efb26c86bf4d2dcbd` |
| `methods.json` | `fe561663f8b82b6f6c37fe23c13ae744e68a63033b7be76164730ad0fb369859` |
| `decisions.tsv` | `0787cd540262404fced9534d223e572448d363020ceee26eeaa06107e873e0b8` |
