# Base recovery observations — N-class

Issue: [ed3c/soodles#16](https://github.com/ed3c/soodles/issues/16).
This document records scope and reproduction; `landing.py` and its executable controls own transitions.

Baseline `defc1084de1a0d760cf145755efb39ea8850a410` rejected a coherent main/PR-base change with `invalid base.head` and left a prepared checkpoint without a readmission entry. The external process observer reproduces that failure through the actual CLI using provider fixtures.

The correction exposes one supported path: `advance` or first `dispatch` records invalidation and returns `action=readmit`, `invalid.field=base.head`, and `next_command=./soodles landing readmit --help`. The supervisor updates the candidate through its existing admitted worktree, obtains canonical acceptance and successful exact-head provider evidence, then submits a fresh claim with complete provider comparisons. The command does not choose a repository, credential, authority or Git conflict resolution.

After readmission, use the returned `advance` route with fresh owner readback. The replaced admission remains in the same checkpoint as `SUPERSEDED`; it cannot dispatch again. A lost readmission reply is handled by reading the persisted state through `advance`, not by repeating `readmit` unchanged. Offered/legacy unknown writes return the readback route and cannot reset their delivery history.

The standalone observer was selected before candidate acceptance with SHA-256 `dc6e1a0cfb6783edf78a3d979e1357af9ae62940d06430a35b37314d719d0545`. It imports candidate code only inside fault-injected child processes. Baseline fails; the treatment recovers after both save-boundary SIGKILLs and admits only one concurrent consumer. A planted change that clears an offered write on base drift is rejected. The publishing verifier remains `faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb` outside the candidate.

The comparison is about observable lifecycle behavior, not measured Agent reasoning cost. Provider data in the fault experiment is a local fixture. Runtime Actions and actual Issue delivery receipts are linked from the PR; this document alone proves neither provider completion nor Noodle reconciliation. No verification-skill feature-map expansion or production scheduling is included.

## Supervised amendment observations — #19

At `0256f2923e978b989e25df07c74db4370d343312`, replacing a prepared candidate while keeping base unchanged produced `invalid pr.head.sha` from advance and `invalid readmit.phase=merge_pending` from readmit. Neither command offered a recovery path. The observed defect is a missing pre-offer invalidation transition, not proof that tests or architecture should be frozen.

The new route is supervisor invalidation → same-Issue amendment and new execution boundary → correction of source/tests/gates → fresh candidate evidence → existing readmit. No modification or PR is required when no defect is observed. The control checks durable recovery and retains the distinction between accepted, offered, merged, closed and locally reconciled.

Before production edits, the supervisor froze the extended observer outside the candidate with SHA-256 `082dcda0fa2b941b4c266cb0c59a2b46ba76bb3a5aaaedecc8184e18e1df416d`. The old source fails the new invalidation control. The same observer drives the treatment and planted negatives without importing candidate verdict logic. The publishing verifier remains the previously selected external implementation; no default-branch tip is loaded as judge. Exact runtime and delivery receipts belong to the Issue and PR, not this prose.
