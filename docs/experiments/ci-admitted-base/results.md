# CI caller 驗證紀錄

## 原始失敗

原始來源是 PR #244 的 head `d8b285fe5006819b8866a68c9f1cc0069855e485`。
run `37131032820` 的 job `111226010853` 在 controls 前拒絕 candidate。
以下保留 raw log 的原文。

```text
2026-10-03T14:50:03.4055874Z REFUSED: candidate verify: invalid candidate.base='5b0a73eae31fb414deeed4ffdf8082a71aee4e3d'; supported help: ./soodles candidate verify --help
2026-10-03T14:50:03.4184666Z ##[error]Process completed with exit code 1.
```

本 writer 沒有重跑該 CI。
以下外部檔案保留完整來源。

```json
[
  {
    "path": "/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/fresh-base-229/ci-job-111226010853.log",
    "sha256": "accb529777e1b5412c67ae920aee24870f98ff41cf24f9e48d6b23b300f39d81",
    "bytes": 38109
  },
  {
    "path": "/Users/neon/.codex/experiments/cross-repo-factory-kvlba2k1/autopilot-recovery/fresh-base-229/ci-base-review.json",
    "sha256": "db4236edd60aba31776f89ef147510b6b9d0b6157814e5f50093d1be3b048075",
    "bytes": 7066
  }
]
```

## 修正前的近端控制

writer 重用現有 `CandidateVerificationTests` 的小型 Git 與 manifest fixture。
writer 在 event base 後新增一個 admitted commit。
該 commit 加入不在 candidate write scope 的 `upstream.txt`。
writer 再產生 candidate head。
原 caller 的 `verify_candidate(root, event_base, head, issue)` 拒絕。
同一 head 使用 admitted base 時，原 strict verifier 通過。
這個結果證明 caller input 有誤，不能據此放寬 verifier。

```json
{
  "event_base": "08a0c80b6ae3db961757dc820a7182d8e76bc336",
  "admitted_base": "93a4ef07607cfc8c8de49fde84a1e361e11d2fac",
  "head": "aa2eadd4bce94ed76ebc03db2cf501d1a12c8aa0",
  "old_caller": {
    "classification": "REFUSED",
    "invalid": {
      "field": "candidate.base",
      "value": "08a0c80b6ae3db961757dc820a7182d8e76bc336"
    }
  },
  "strict_correct_input": {
    "head": "aa2eadd4bce94ed76ebc03db2cf501d1a12c8aa0",
    "base_head": "93a4ef07607cfc8c8de49fde84a1e361e11d2fac",
    "changed_paths": [
      "manifest.json",
      "observer.py",
      "policy.md"
    ],
    "evidence_manifest_sha256": "95db21cfd8b526c25b730ce0b31b25a6f0048f66a51f4c0f8c29785be91199b8",
    "authorizes_landing": false,
    "issue": 18,
    "issue_body_sha256": "6c2ea686465a94c6b6801ade65b0f756c1a542c02a1c66415057d03f9d0e1667",
    "tree": "81bc4fab6c2d368f27b172a454d325fb56539cef",
    "frozen_paths": [
      {
        "path": "observer.py",
        "revision": "head",
        "sha256": "6793f242eefc943233ffeb80bdeaee239cdca62e3cf7b4db444435f92c1a62c0",
        "actual_sha256": "6793f242eefc943233ffeb80bdeaee239cdca62e3cf7b4db444435f92c1a62c0"
      }
    ],
    "owner": "candidate.verify",
    "classification": "VERIFIED"
  }
}
```

## 修正後控制

Test Manager 選出 5 個模組，共 43 項測試。
本次執行 exit 0，全部通過。總 elapsed 為 9.207 秒。
這是本次正常控制的量測，不是效能比較。
沒有執行 physical controls、full suite、model benchmark 或 live provider 測試。

新增的 `test_runtime_base` 含 15 項測試。
它執行 caller 與 Git/manifest，涵蓋舊 event base、相同 base、schema 2 與 schema 4。
它拒絕較新、不相關、缺失、格式錯誤與非 commit 的 event base。
它也拒絕無效 contract base、head 缺少 admitted base、wrong checkout、錯誤 Issue 與 frozen/artifact/write-scope 違規。

workflow 控制擷取保存的 candidate 與 scope Python 程式，並在小型 repository 執行。
成功時，receipt、candidate output、scope request 與 scope output 都是同一 admitted base。
拒絕時，candidate 保留結構化 JSON，且不寫成功 base output。
scope 在 PR output 缺失時拒絕，不使用另一個 base 補值。
dispatch 的明確 base 與 reason 通過。
既有 `test_test_suite` 繼續拒絕沒有 reason 的 dispatch 與其他未請求事件。

schema 4 使用既有 `comparison_fixture.build`。
該 fixture 只複製指定的當前 analyzer 與其必要 modules。
它重新綁定既有 synthetic JSON 的 instruction 與 experiment identities。
它執行當前 comparison discriminator，沒有執行模型或歷史 implementation。
此控制不能證明新的 Agent 行為改善。

完整測試輸出與 source 雜湊如下。
同一候選 source 可用所列 command 重新執行。
fixture 自動建立並清除其 Git inputs。
每次 Git SHA 可能因 commit 時間不同而改變，驗收條件保持相同。

```json
{
  "command": [
    "./soodles",
    "test",
    "--base",
    "4b60629a44a503637c93207a03cc81717148a076"
  ],
  "exit": 0,
  "count": 43,
  "seconds": 9.207,
  "modules": [
    "test_admission",
    "test_candidate_verification",
    "test_delivery_refs",
    "test_runtime_base",
    "test_test_suite"
  ],
  "physical": [],
  "source_sha256": {
    "runtime_candidate.py": "791ca4987d8ac641319a2ddda24ab936378b6c4cc32cc5058a725dcbd93a2ad7",
    ".github/workflows/runtime.yml": "2fdd2451a63c985eeb41b85ebf461bdad914b282b3cc5b0eac1153909f42c113",
    "test_manager.py": "f137cc8af93fd41b76b8bb8adaa87b109881631b52fd6f801c34bb91a8541d64",
    "tests/test_runtime_base.py": "6941b4a86061a633e870022f6e58d31ff64f33dae98183b9f97e8d3f51eeb386",
    "issue_admission.py": "3a55f01892c2071e5ea7879fab17fb6d1b9986c3fa90c56a0d11321ac0aaf929",
    "tests/test_candidate_verification.py": "7a1613001c4df647f6b0370d8e38e89cf6be71ce3bf839b71d3f412e0bb00130",
    "tests/comparison_fixture.py": "9bb6f786fab14094959ad22b30122f69d5d7c60fa3f152cc154a00049c55508b"
  },
  "receipt": {
    "path": "/Users/neon/.codex/experiments/ci-admitted-base-250-writer/tests.json",
    "sha256": "5dcac7142df79274e2e17c940e5f076af9f503ce76214ef3c0b6283022e1b808"
  },
  "log": {
    "path": "/Users/neon/.codex/experiments/ci-admitted-base-250-writer/tests.log",
    "sha256": "15c619187d1c8a801b86e7f92835be14bf38818ab2c223d4bb449cdd22300a76"
  },
  "authorizes_landing": false
}
```

測試的成功摘要保留如下。

```text
Ran 15 tests in 9.096s

OK
```

原始逐項結果與時間保留在上列 `tests.log`。


## 交付界線

本文件記錄本機 fixture 與來源檢查。
它不表示 GitHub Linux exact-head acceptance、publication、landing 或 reconciliation 已完成。
原 owners 接續這些工作。
Root 仍須透過原 #229 continuation 驗證真實後續 PR。
本 unit 不完成 medium source、fresh clone/replay、Production 或跨 repository 並行的總目標。

獨立 source 與 control review 未發現 correctness must-fix。
review 未自行執行測試。
本次沒有 P-class Markdown 變更，因此沒有新 P-class behavior claim 或 feedback round。
