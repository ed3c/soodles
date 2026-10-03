# 原 host-finalization source 的重建

本紀錄對應 ed3c/soodles#237。它記錄工程設計，不授予 publication 或 landing 權限。

## 問題與證據

原 #232 authorization 沒有 `lifecycle_owner`。它以 `base_head` 固定 Git 來源。
原 resume 回傳 `lifecycle.resume.host_source=missing`。
舊程式的前提是每個原 host plan 都有 explicit lifecycle owner。
這個前提不符合 implicit authorization。

只讀檢查以原 `base_head` 讀取 Git objects。
重建的 plan identity 等於已保存的 `host_finalization.identity.plan`。
因此本次來源是原 base，不是後來同步的 control root。
本結論只涵蓋這份原紀錄，不能推定所有歷史 record 都符合其 base。

## 選擇與執行路徑

Schema Manager 仍使用 `Plan` 與 `Manager`。
Plan 保存來源雜湊、規則、consumer、依賴文件與 fact catalog。
Record 保存 authorization、subject、plan identity、sequence 與 facts。
這些資料結構已有所需的身份與進度，不需要另一份狀態。

`compile_plan` 接受可選的 `read_bytes`。
一般呼叫仍讀 filesystem。
Implicit resume 的 reader 只讀原 authorization 的 `control_root` Git object database 與 `base_head`。
Compiler 以同一 reader 解析 JSON、檢查 Python AST、取得 context，並計算所有 source hashes。
AST 檢查只讀函式定義。它不 import 或執行歷史 Python。
原 `compile_repair` 已支援讀取注入，因此不需更改 `system_context.py`。

替代方案是把固定 Git bytes 寫進暫存目錄，再使用原 filesystem compiler。
這個方案仍需取得同一組依賴，並增加寫檔、partial output 與清理。
Byte reader 已能滿足相同身份驗證，因此採用較小的介面變更。
讀目前 root 更短，但不能證明原 record 的來源，故不符合要求。

Resume 先驗證原 lifecycle chain。
原 owner 明確指定來源時，resume 保留既有 external source 驗證。
原 owner 未指定來源時，resume 使用固定 base 的 Git bytes。
Schema Manager 比較規則、consumer、依賴與 fact 語義，再用原 plan 驗證 record。
歷史驗證沿既有 lifecycle chain 讀取每次轉移的固定來源。
每個 prior record 都必須符合其 plan、authorization 與 subject。
Sequence 不可倒退。相同 sequence 必須具有相同 facts。
不同 sequence 可保留後續 owner observation。
早期沒有 projection 的 lifecycle 不要求額外 host history。
合法轉移只更換目前 plan identity，並保存原 record 與既有轉移歷史。
Facts、sequence、subject、authorization 與 repair ledger 不因轉移而重設。

## 驗收邊界

固定來源可讀、語義相同、原 identity 相符且 record 合法時，轉移才可接受。
來源缺失、錯誤 base、語義改變、identity 或 record 不符時，轉移必須拒絕。
`stop_offered` 或 `restore_offered` 已保存而效果未確認時，projection 仍要求原 owner readback。
這些檢查驗證來源、資料格式與身份鏈。
它們不新增原 readback 的外部真實性證據，不能偵測每一種格式合法的事實篡改。
來源轉移不證明 stop、restore、publication、CI 或 landing 已成功。

產品 controls 使用小型 disposable fixtures。
原 #232 資料只提供只讀 identity 證據。
本工程不執行其 live resume 或 run，也不修改原 state。

## Criteria correction 的設計判斷

原任務要求保留 contract reference，但原 required paths 要求它有 net diff。
Validator 對原選項的拒絕符合實作。修改 validator 會改變未授權的驗收語義。
Supervisor 已提供修訂，將 required source 改為實際修改的 `issue_atom.py`。
因此本輪只整合指定 base，更新實際 hashes，並驗證相同功能。
既有 manifest 欄位名稱不授予 Agent 指令或外部效果權限。
未修改的 contract 在候選中保持與新 base 相同。
