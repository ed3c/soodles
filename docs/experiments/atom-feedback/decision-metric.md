# 以 Agent 決策數量定義最短路徑

使用者已明確指定主目標：減少 Agent 完成合法工作時必須自行做的決策，尤其是容易猜錯的流程決策。前一輪把「最短」主要解讀成耗時，偏離這個目標。原有成本紀錄仍是有效的輔助資料，但不能代替決策量測。

這份文件是本次工作的 N-class 量測定義。它沒有增加產品 gate、scheduler 或新的 owner。現有 Test Manager 與 Schema Manager 尚未因此自動具備決策計數器。

後續需求另指出實作位置：計數用來觀察效果，不能取代修正。已能由事實與政策決定的轉移，應由既有 CLI owner 決定。CLI 應輸出固定輸入、合法下一步或缺件。P-class 說明這份契約，不能被當成程式已強制執行的狀態機。本輪先修正 `pclass-feedback` 的 selection 組裝與完成邊界，沒有宣稱已移植全部 poteto-mode 路由。

## 計數單位

一個可觀察的決策事件，是 Agent 在一個已識別的狀態與固定輸入下，自行選擇一次會影響後續工作的動作。事件必須引用實際 request、response、工具操作或 owner receipt。觀察者不推測模型內部思考。

- owner 已選定唯一 `next.argv`，Agent 原樣執行：不新增決策。
- Agent 自行選擇 owner、操作、證據、工作範圍或停止點：記錄一次決策事件，再判定其類別。
- 從已明示的 ID 找出唯一對應檔案：是資料查找，不因讀了一個檔案就新增決策。
- 同一狀態與相同輸入下重新選擇相同問題：另記重複決策事件。不要只按獨特問題去重。
- 缺少輸入且 owner 已明確返回缺件與負責者：記錄阻塞。不能因此算 Agent 猜測。
- 狀態或輸入有實質改變後重新判斷：保留新的決策事件，不一概當成浪費。

一個事件可以同時判斷數個相互依賴的欄位。不能按 JSON 欄位數、工具次數、文件數或分支數直接估算決策數。工具操作多也不必然表示 Agent 做了更多選擇。

單一相符輸出不能揭露 Agent 內部判斷過幾次。比較前要固定外顯選擇邊界，例如提交一份 observation selection。兩組都只做同一份提交時，不能把其中一組按欄位拆成更多決策。當 baseline 已含 owner 的確定選擇時，把選擇複製到另一個欄位不算新的改善。

## 分開記錄的量

| 量 | 含義 |
| --- | --- |
| `decision_events` | 已觀察的 Agent 決策事件總數 |
| `necessary_judgment_events` | 原需求與現有事實仍不能唯一決定的必要工程判斷 |
| `avoidable_workflow_events` | 已有政策與事實可以決定，卻仍交給 Agent 選擇的流程判斷 |
| `repeated_decision_events` | 沒有新狀態或輸入，卻再次處理相同選擇 |
| `unsupported_choice_events` | Agent 在缺少必要依據時仍選擇操作或補造資料 |
| `wrong_choice_events` | 違反有效原需求或 owner 契約的選擇 |
| `blocked_inputs` | 已明確識別且尚未補齊的必要輸入 |

這些量不是全部互斥。重複、錯誤與無依據是事件的屬性，不能把所有欄位相加成總數。capture 不完整時，只能報已觀察數與覆蓋範圍；完整總數保持 unknown。沒有看到錯誤不等於錯誤數為零。

## 比較成立的條件

比較兩條路徑時，先固定原始任務、起始狀態、輸入、授權、必要驗證與停止點。兩條路徑都要達成同一合法結果，才能比較總決策數。提早 blocked、遺漏驗證或把工作留給另一個未計數的 actor，不能算較短。

目標是減少 `decision_events`，並優先移除 `avoidable_workflow_events` 與無必要的重複判斷。`unsupported_choice_events` 和 `wrong_choice_events` 是不可用較少決策數抵銷的缺陷。必要的設計、調查和語意驗證仍保留給 Agent。

「讓 Agent 不會猜錯」在可測範圍內表示：既有 owner 已明確決定的事情不再讓 Agent 猜；缺少前提時能停在具體缺件；已知錯路能被拒絕。它不表示任何模型在所有任務都不會出錯。

## Test Manager 與 Schema Manager 的分工

觀察記錄需要包含狀態身分、問題、Agent 當時可見的資料、owner 是否已給唯一下一步、實際選擇、結果及來源引用。這是本次量測資料，不是新的 runtime 授權契約。

Test Manager 根據實際事件與原需求審查計數。它區分必要判斷、可消除的流程判斷及缺失 capture。對新增或修正的 decision boundary，它只選擇足以區分正確與錯誤行為的控制。

Schema Manager 消費已綁定的事實與 review。對程式可決定的轉移，沿用現有 owner 的唯一 continuation。對缺件，暴露缺少的前提及其負責者。對仍需工程判斷的問題，保留該工作。欄位存在或 schema 驗證成功，都不能證明 Agent 沒有猜測。

本輪尚未加入自動計數實作，也沒有將歷史成本投影當成決策量測。新的比較須先固定這個單位，再由實際事件取數，避免看完結果才改計數方式。

## 既有證據能說什麼

先前 `unknown_write` 的條件只接受字串 `readback`，而 consumer 回答 `original-owner readback`。原需求沒有定義該 enum。獨立審查確認這是評分條件缺陷，不能把這次 FAIL 算成 Agent 猜錯。

修正後，輸出明確表示 owner 與先後順序。這移除了一個已知的表示法障礙。它尚未量測整段工作少了幾次 Agent 決策。

`next.evidence` 已明示哪些案例需要新觀察、哪些引用可重用。其 consumer 曾正確使用該資料。但缺少同條件的逐事件前後對照，不能直接把「少重跑五個案例」換算成「少五次決策」。

Issue #215 的真實交付 receipts 支持該次交付與 reconciliation。它們沒有完整記錄本指標所需的決策事件。因此先前的秒數與 token 數不能證明這次定義的最短路徑。
