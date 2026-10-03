---
name: schedule
description: Materialize the one externally admitted Soodles Issue through the shared validator.
schedule: When Noodle requests a Soodles schedule decision.
---

# Schedule the admitted Issue

若目前 admission 提供 `SOODLES_ADMISSION_LAUNCHER`，執行該絕對路徑並傳入 `inspect`。
入口會先驗證固定的 manifest、envelope 與 runtime bytes，再檢查目前 Noodle role。
不要掃描 PATH 或從歷史輸出重建 launcher。Target 不需要 `./soodles`。
若沒有這個 admission，既有 Soodles checkout 使用 `./soodles issue inspect`。
This read-only entry
reads the current Noodle role before checking the supervisor-selected launcher.
Use the returned result:

- `action: not_applicable`: return to the caller's original task.
  `next: null` does not imply a schedule prerequisite or task completion.
- `next.kind: input` / refusal: report the named owner and required input for
  this operation. Continue unrelated authorized work.
  Do not retry unchanged input. Do not use help as a capability probe.
- `next.kind: executable`: execute the current `next.argv` array exactly once,
  without shell reconstruction. Then read the launcher's structured result.

Inspection does not admit an Issue, execute the launcher, or grant authority.
The selected launcher revalidates its external envelope and current Noodle and
provider state before effects. Never search for, construct, export or reuse a historical launcher.
Do not dump the environment.

Noodle owns the canonical order, worktree and process. An owned or previously
admitted result is an observation, not permission to establish another writer.
Never reconstruct an order, overwrite `orders-next.json`, request an implicit
restart, or write canonical state. Do not edit target source or perform delivery
from the schedule task. This Skill provides guidance. The installed validator
and worker enforce the boundary.
