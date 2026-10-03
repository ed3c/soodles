# CI admitted base 修正

PR event base 與 Issue contract 的 `base_head` 代表不同輸入。
本次已知失敗中，event base 是 `5b0a73eae31fb414deeed4ffdf8082a71aee4e3d`。
Issue #229 的 admitted base 是 `4b60629a44a503637c93207a03cc81717148a076`。
PR #244 的 head 是 `d8b285fe5006819b8866a68c9f1cc0069855e485`。
CI run `37131032820` 的 job `111226010853` 回報 `candidate.base` 拒絕。
這些值來自本次 admission 提供的 raw log 與 `ci-base-review.json`。
本 writer 沒有重跑該 head，也沒有讀寫那些 Issue 的 owner。

舊 caller 假定 event base 等於 admitted base。
`issue_admission.verify_candidate` 對 schema 3 與 4 要求這個等式。
同時，Test Manager 也從 workflow 取得 event base。
因此，放寬 verifier 不能修正 scope 的起點。
修正必須讓 caller 先驗證 contract，再讓兩個 consumer 使用同一個成功結果。

## 選定的邊界

本次保留 strict candidate API。
caller 重用 `parse_contract`，不從 body 直接擷取未驗證字串。
schema 3 與 4 的 admitted base 來自 contract 的 `base_head`。
event base 必須等於 admitted base，或是 admitted base 的祖先。
admitted base 必須等於 head，或是 head 的祖先。
caller 不能從目前 main、共同祖先或其他 fallback 選 base。
schema 2 保留原先的 event base 行為。

成功 receipt 的 `base_head` 才能傳入 Test Manager。
PR 缺少成功 output 時，scope 必須拒絕。
`workflow_dispatch` 繼續使用明確的 base 與 reason。
它不執行 PR candidate step，也不成為 PR acceptance。

## 證據範圍

小型 Git fixture 建立舊 event base、新 admitted base 與 candidate head。
兩個 base 之間含一個不在本 Issue write scope 的 upstream 路徑。
成功控制需證明該路徑不進入 candidate diff 或 Test Manager scope。
負向控制需證明 lineage 合法仍不能繞過 Issue、checkout、manifest 與 frozen bytes 檢查。
所有控制使用當前程式與 disposable repository。
它們不代表 live provider acceptance，也不授予 landing 權限。

本 writer 的停止點是 clean committed candidate 與 stage outcome。
原 publication、Linux exact-head CI、landing 與 reconciliation owners 接續交付。
Root 另沿原 #229 的 base advancement 路徑驗證後續 PR。
medium source、fresh clone/replay、Production 與跨 repository 正常並行仍在原總 handoff。
本修正不能證明整體 full autopilot 完成。

## 實作選擇

本次選用 `runtime_candidate.verify_pull_request`。
它接收 repository 路徑、event base、head、新 Issue readback 與 caller 指定的 Issue 身分。
它回傳既有 strict verifier 的完整成功 receipt，並保留 `event_base`。
它不讀 credentials，不呼叫 provider，也不決定測試範圍。

另一方案把選值與 Git 檢查放在 workflow inline Python。
該方案可保留 CLI，但會讓 YAML 同時擁有 domain 判斷與輸出處理。
本次選擇一個可直接呼叫的 Python 函式，將這些相關判斷放在同一處。
這不需要 class、policy object 或新 CLI verb。

對 schema 3 與 4，adapter 檢查三個輸入都是精確 commit。
它檢查兩段有向祖先關係，再呼叫原 `verify_candidate`。
原 verifier 繼續檢查 Issue open 狀態、exact checkout head、tree、write scope、manifest 與 frozen pins。
任一步拒絕時，workflow 保留結構化拒絕資料，並以非零狀態結束。
workflow 只有在取得成功 receipt 後才寫入 base output。
未知錯誤不產生成功 output。

schema 2 直接沿用原 verifier 的 event base 行為。
不能只因選出的字串相同，就把新增 ancestry 拒絕稱為相容。
本次控制包含原 verifier 可接受的非祖先 schema 2 base，以檢查此界線。

兩個獨立設計 reader 與一個判讀 reader 使用目前 native carrier。
所有角色均遵循主機的 `inherit-parent` 設定。
這是同模型的獨立審查，不是跨模型證據。
