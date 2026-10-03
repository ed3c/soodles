# 驗證結果與限制

本紀錄屬於 ed3c/soodles#237 的 N-class 工程證據。
它不授予 publication、landing 或原 #232 的執行權限。

## 原 #232 的只讀來源檢查

原拒絕是 `lifecycle.resume.host_source=missing`。
原 authorization 的 `lifecycle_owner` 缺省。
檢查使用原檔案的外部副本，以及原 control root 中已存在的固定 Git objects。
沒有執行歷史 Python、live resume 或 live run。

- 原 base 為 `192f772923213f4d9be7e7886b589b502f6f5af6`。
- Authorization SHA-256 為 `f60cd4aa3ecd59b0f5ee5df9578b13880334a891321d5602aeeaa856f2f97baf`。
- Subject identity 為 `a038d1180e816d8178690459b01b034f48ff47d44a4e191f0d63aaae3ac0526e`。
- Plan identity 為 `68bdd7fdd085aa98d8db89ff1b35c6af6fc3af9190d5d5f2bafb9cd8da902a3b`。

Compiler 的 17 個不同讀取路徑全部來自同一固定 base。
其中九個 source hashes 組成原 plan identity。
重建 identity 與原 record 完全相等。
`Manager` 以重建 plan 驗證了原 facts、producer、authorization、subject 與 sequence。
Sequence 保持為 4。
`stop_offered=true` 與 `loop_live=true` 仍產生 `status=stop`。
Projection 要求 `original_owner_readback`，且 ready 清單不包含 stop。
這個結果表示效果仍未知，不表示 loop 已停止。

檢查前後比對了原 authorization、state 與 refusal 檔案。
三份原檔案的 SHA-256 均未改變。
原 state 的其他內容沒有經過本檢查修改。

外部證據保存於 `/tmp/soodles-237-ohkgmap9`。
這些檔案是本 session 的診斷產物，不是授權輸入。

| 檔案 | SHA-256 |
| --- | --- |
| `check_original.py` | `b46e631d05b14a39ddfdd9dd9b86e951a048d735bcdabbd8518313bd230beaef` |
| `original-source-result.json` | `74a1dec472390fe93b60e538e5a5e6945faa159a91f99c87a3958cd265cfa15f` |
| `original-refusal.json` | `409ee9faaeaf2f6c7272f5be878343f01f31197cffaab72592ec342c1e51e419` |
| `methods.json` | `49cda9d2256fd78da0b2f838a673759f36dde343a0ece35eb813d292efe2a4a1` |

原來源 hashes 如下。

| 固定 base 路徑 | SHA-256 |
| --- | --- |
| `schema_manager.py` | `c30b4633792101ffa90a6bdac81df81b47a4736d9ba628a8280826788c1a200d` |
| `policy/host-finalization.json` | `8b1d4749d0c3a4e0e9724cfaddfe75780277ceb5199406da18fe91ea06b79edc` |
| `issue_atom.py` | `96fd83b9d617578c848784aae6d866375b7cd9a1baa5a4573bbae4d0847e6307` |
| `system_context.py` | `ad89a275d75f01a66eb725c6b01dc9a6e35e5aa25bdec8bdb81fb4c4b7606e92` |
| `atom_repair.py` | `7abb92c98e5cb1a22b4931fca0584d8a7fe1bc34c205cf13ebd34f1e049c4e17` |
| `policy/repair-policy.json` | `1e9de3ea83b8af0b5498c068f13921be25955ed09cf86a0fd22139a2c1676820` |
| `contracts/system-v1/routes.json` | `22e84baf0ea582d394e5c6d0516c60e7e09a309e182d5257c75cb823035158b3` |
| `contracts/system-v1/common.md` | `f77ba6c4cc733a07a6f15e9697403041f197786fe785e4205e79f8899c65ea15` |
| `contracts/system-v1/issue-atom.md` | `049557bfbccd335bbf3c3bcef9fc9014f9ec8ae26234dcc5c40d2d6f98fb2512` |

## 原候選的必要 controls

Test Manager 選定 `test_lifecycle_activation` 與 `test_schema_manager`。
執行入口如下。

```sh
./soodles test --module test_lifecycle_activation --module test_schema_manager --reason 'Issue 237 implicit original host plan source and projection transfer'
```

修正前的小 fixture 保留了這個拒絕。

```text
issue_atom.AtomRefusal: issue atom: invalid lifecycle.resume.host_source='missing'
```

最後一輪結果為 32 tests、exit 0，正常執行時間為 61.966 秒。
Lifecycle 的 22 個 tests 與 schema 的 10 個 tests 全部通過。
沒有執行 full suite 或 physical controls。
最終 runner 輸出含 `"exit": 0, "count": 32`。

Controls 覆蓋固定 Git bytes、目前 root 漂移、錯誤 base、缺失 object 與未執行歷史 Python。
它們也覆蓋 rules、consumer、依賴與 producer 不符，以及錯誤 JSON、UTF-8、AST 和非有限數值。
合法轉移保留完整 facts、非零 sequence、repair 與原 history。
錯誤 authorization、subject、plan、sequence、producer 或 history 均拒絕，state 保持不變。
Legacy facts 保留缺少 producer 的原貌。
先有 lifecycle、後有 host projection 的短 history 仍可接受。
相同 owner resume 重入後，state bytes 不變。
未確認 stop 或 restore 不會再被提供。

第一輪修正後有兩個新 fixture 失敗。
Byte-reader fixture 缺少 compile_repair 其他決策所需的兩份 contract。
History 植錯 fixture 的 deepcopy 保留共享 facts alias，沒有模擬持久化後的獨立 JSON objects。
修正只補齊 fixture 來源，並加入實際 owner 保存與讀回的 JSON roundtrip。
最終 controls 通過。原失敗輸出仍保留，未更改期待行為或停用測試。

| 外部 runner 紀錄 | SHA-256 |
| --- | --- |
| `source-tests-red.txt` | `d3c5cb83dc90f6725c1643d391889344337469546d6f4dbf9bd0afceec829ec2` |
| `source-tests-green-1.txt` | `f74b4bac5d9992c909f4ad06822620782eec4aeceb7c233d50b4198bacddf89a` |
| `source-tests-green-2.txt` | `65becf9cd4a77fbc9bd42bf36368b434df31b3aef87f3492c315ed7a3db4613b` |

通過 controls 的 source 如下。

| 檔案 | SHA-256 |
| --- | --- |
| `issue_atom.py` | `af096164b8116682f106575ed016b64268b263496c91ee289e6d37bf5c1036d6` |
| `schema_manager.py` | `d8952b2450016b274d60d60bb60c9e530263bd594e7226d79a4a7cbf9b0c9863` |
| `tests/test_lifecycle_activation.py` | `c3b1abe07a3aac9b4f6a051edaf152af5a286a1c828182cbbf15b06bd4d12e2b` |
| `tests/test_schema_manager.py` | `0a5eea3c29625013353516b415cc31675b7d588100ab316b7bbd249000e0bc66` |

## 原候選的方法與能力界限

本 session 讀取 `execute` 的已選 instruction context，並採用 Poteto Bug Fix。
`how` 與 `architect` 追查 compiler、source reader、projection 與 owner 邊界。
兩個原生子代理分別負責 source 設計及獨立審查。
設計比較了 byte reader 與實體暫存 snapshot。
`Model the Domain` 保留既有 Plan 與 record，沒有增加狀態層。
`Fix Root Causes` 修正 implicit 來源讀取，不刪除舊 state。
`Prove It Works` 以原 record identity 和 selected controls 驗證結果。
文字使用 `unslop` 與 `technical-writing`。

`methods.json` 保存實際讀取的方法路徑、SHA-256 與選擇原因。
目前 carrier 沒有 Poteto 指定的 Cursor Task、模型別名或 Comment Sicko 類型。
本紀錄不宣稱執行那些專用能力，或取得跨模型一致性證據。
原生子代理的審查沒有擴大來源寫入或 provider 權限。

未修改任何 P-class 文件。
Frozen contract 仍為 `229258a611bcde90973fe5cb1e5573cab626354f73f684ec5f4f4c4324bcd7aa`。
本次沒有 Agent 行為改善主張，也沒有以 code controls 冒充 Agent 行為證據。

## 未完成的外部結果

原 #232 activation、stop readback 與本機收尾尚未執行。
#229 與跨 repository 需求仍為 pending。
本工程沒有執行 publication、exact-head CI、landing 或 reconciliation。
前一輪的 admission 選項錯誤已由 supervisor 修訂，詳見 [handoff](handoff.md)。
原拒絕與錯誤歸因仍保存在原 commit 與外部紀錄。

## Criteria correction 後的整合驗證

本輪 session 是 `soodles-237-92e049f919db-0-execute-20261003-125649-451dd9`。
指定 base 是 `a2e6f36bdffa893c6d9d31ad31b4880551634d80`。
Git 無衝突整合該 base，並保留原候選 `8f3b3a6d53b951cc4d4cb1eb22cd044eec256f25`。
相對指定 base，source 與 controls 的修改內容和原候選相同。
目前 contract bytes 與指定 base 相同，並非沿用舊 base 的 hash。
原 instruction pins 與外部 judge 未更換。

Test Manager 以指定 base 選定三個模組。
`test_lifecycle_activation` 的 22 tests、`test_schema_manager` 的 17 tests、
`test_candidate_verification` 的 3 tests 全部通過。
Runner 回傳 `exit=0`、`count=42`，正常執行耗時 76.732 秒。
沒有執行 full suite 或 physical controls。
本輪沒有改變原 source 演算法或 test assertions。

```sh
./soodles test --base a2e6f36bdffa893c6d9d31ad31b4880551634d80 --module test_lifecycle_activation --module test_schema_manager --module test_candidate_verification --reason 'Issue 237 integrates selected base and corrects source manifest criteria'
```

整合後重新執行原只讀診斷。
Plan identity 仍為 `68bdd7fdd085aa98d8db89ff1b35c6af6fc3af9190d5d5f2bafb9cd8da902a3b`。
Sequence 仍為 4，結果仍要求 `original_owner_readback`。
Authorization、state 與原 refusal 的檢查前後 hashes 相同。
本輪沒有執行 live #232 resume 或 run。
這是 Prove It Works 原則的實際應用，直接驗證保存的 identity 與候選 bytes。

外部證據目錄為 `/var/folders/l6/44bf7nvs64j60f1mpyy88hdm0000gn/T/soodles-237-revision-xp4xf7jh`。

| 檔案 | SHA-256 |
| --- | --- |
| `controls.txt` | `8472d6ca89fc097cbb42704ec8fa218b13b0a570e289a87443b33b9a4bf48852` |
| `original-source-result.json` | `a4c41e5da1b584de41d61023eba501d581084aa992cbe61ed6ee58b2052e4aa7` |
| `check_original.py` | `b46e631d05b14a39ddfdd9dd9b86e951a048d735bcdabbd8518313bd230beaef` |
| `binding.json` | `3227df5e3337f64ca9bd654c48432757813ebacf4d44468fea5509f5c464d696` |
| `methods.json` | `0f62cfef68a68e28b65e01e2821f3d70fa2ee45ea8f1e973ac4db2ea406dd5b4` |

本輪通過 controls 的 source 如下。

| 檔案 | SHA-256 |
| --- | --- |
| `issue_atom.py` | `13fff27a9d48acd097467369cf661fced3eb955ae4a9436e461ec917cbf2c146` |
| `schema_manager.py` | `012f755a296b1ef9e5a336e7636cebe9f77d2c6f4361baf16adda3337ae2ab3f` |
| `tests/test_lifecycle_activation.py` | `c3b1abe07a3aac9b4f6a051edaf152af5a286a1c828182cbbf15b06bd4d12e2b` |
| `tests/test_schema_manager.py` | `29817781c33016e07962d381ca2996cdcf356251a46f87036b3fe14faf535174` |

原生只讀子代理審查了來源與整合邊界。
它沒有找到影響原 #232 implicit source 恢復的具體缺陷。
它指出另一條路徑的靜態風險。
若先完成 base revision，再產生 host record，最後更換 lifecycle owner，subject 可能使用不同 base。
這條路徑沒有 runtime 重現證據。
原 #232 沒有 scope revision 或 base recovery，因此不符合該前提。
本工程保留這個限制，不改變原來源或 subject 權限。

review-writing 修正了 handoff 對 validator 的錯誤歸因。
原文存於本輪外部證據的 `original-docs/`，原失敗 receipt 保持不變。
更新只涵蓋 N-class 設計、結果、handoff 與 manifest。
相對指定 base 沒有 P-class diff，沒有新增 Agent 行為主張。
Poteto 的專用 Cursor Task、Comment Sicko 與模型別名在本 carrier 不可用。
原生審查不宣稱等同那些專用能力。
