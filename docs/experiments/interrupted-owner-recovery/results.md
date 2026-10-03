# #234 接入觀察

本結果是未完成工程 candidate 的證據。整條 Soodles 恢復路徑尚未驗證。
Stage-outcome consumer 的 scope 缺口阻止 writer completion。
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
