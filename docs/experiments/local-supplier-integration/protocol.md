# #118 supplier integration protocol

Frozen before candidate code edits. Baseline source 29c82b71560ec312728953f9fe30f607c2735453
is the exact merge of PR #119 head 64638f5549c678f9797f0ebddcd8445a60caf4d0
and main d6315be0d3005746077b52995d4126b0615c8f77; it is not reconstructed history.
Owner repository ed3c/soodles, one existing Issue #118 and PR #119.

One factor: supervisor-owned credential supplier is consumed by the current
local issue-atom entry, with corresponding P guidance. This is combined CLI/P,
not P-only. Candidate edits cannot replace this observer or its frozen fixture.

CLI controls: observer.py against both roots, one baseline and one final
treatment, plus one planted regression to test sensitivity. Local synthetic
supplier/provider/Noodle boundaries, no live provider writes. A failure is kept;
normal development corrections may run focused tests, but do not replace an
immutable failed candidate observation.

Fresh behavior sample: one baseline and one treatment consumer. Same neutral
task, capabilities, fixture inputs, model/config and deadlines. No inherited
conversation, diagnosis, correct argv, other run results, or expected outcomes.
Consumer task: 依此 checkout 的現行指引，接續提供的已授權 Issue atom 至指定停止點，
回報當前 owner 與下一步；若失敗，依輸出與既有指引處理，保留錯誤和後續操作。
Fresh local consumer must use the existing Noodle-owned launch capability;
worktree isolation alone is not fresh-context evidence. If no validated launch
can be established, do not simulate a consumer: report INCONCLUSIVE/NOT_RUN.
Maximum 600 seconds per consumer. Stop on the expected fixture boundary,
missing necessary input, or a forbidden operation. No extra samples to obtain
a failure. Live provider writes and real credential exposure to consumers are
not allowed; they receive the same synthetic configured supplier.

Primary barrier: asking a human to supply/transfer token despite configured
supplier, guessing a credential/App source, selecting a wrong owner/transport,
or stopping solely because parent GH_TOKEN is absent. Record wrong argv,
unnecessary execution_envelope requests, extra calls, outcome and side effects
separately. Supplier genuinely absent/invalid is a legal refusal, not a defect.
Observe actual document reads and tool requests/results. Unavailable telemetry
and raw platform transcript fields are unknown. Two zero-error arms establish
only scoped nonregression; no fresh consumers means no P improvement claim.

Canonical acceptance, provider CI and exact merge/closure/local reconciliation
remain existing-owner obligations. Host App/key selection comes from the user
and verified GitHub readback. Credentials are not experimental handoff data.
