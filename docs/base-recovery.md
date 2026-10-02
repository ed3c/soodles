# Base recovery observations — N-class

Issue: [ed3c/soodles#16](https://github.com/ed3c/soodles/issues/16).
This document records the scope and reproduction. `landing.py` and its executable controls own the transitions.

Baseline `defc1084de1a0d760cf145755efb39ea8850a410` rejected a consistent change to main and the PR base with `invalid base.head`.
It left a prepared checkpoint with no readmission entry.
The external process observer reproduces that failure through the actual CLI with provider fixtures.

The correction adds one supported path.
`advance` or the first `dispatch` records invalidation.
It returns `action=readmit`, `invalid.field=base.head`, and `next_command=./soodles landing readmit --help`.
The supervisor updates the candidate in its existing admitted worktree.
It obtains canonical acceptance and successful provider evidence for the exact head.
It then submits a fresh claim with complete provider comparisons.
The command does not select a repository, credential, authority or Git conflict resolution.

After readmission, use the returned `advance` route with fresh owner readback.
The replaced admission remains in the same checkpoint as `SUPERSEDED`. It cannot dispatch again.
If the readmission reply is lost, read the saved state through `advance`.
Do not repeat `readmit` with unchanged input.
Offered writes and legacy unknown writes return the readback route. They cannot reset their delivery history.

The standalone observer was selected before candidate acceptance.
Its SHA-256 is `dc6e1a0cfb6783edf78a3d979e1357af9ae62940d06430a35b37314d719d0545`.
It imports candidate code only inside child processes used for fault injection.
The baseline fails. The treatment recovers after SIGKILL at both save boundaries.
It admits only one concurrent consumer.
The observer rejects a planted change that clears an offered write when the base advances.
The publishing verifier remains `faaf6892ea1e14dfa31319aa5dcd92162cc471e3eaad8dfe1d215da5face6ccb`, outside the candidate.

The comparison measures observable lifecycle behavior. It does not measure Agent reasoning cost.
The fault experiment uses local fixtures for provider data.
The PR links to runtime Actions and actual Issue delivery receipts.
This document alone proves neither provider completion nor Noodle reconciliation.
The work does not expand the verification-skill feature map or include production scheduling.

## Supervised amendment observations — #19

At `0256f2923e978b989e25df07c74db4370d343312`, a prepared candidate was replaced while the base stayed unchanged.
Advance returned `invalid pr.head.sha`. Readmit returned `invalid readmit.phase=merge_pending`.
Neither command offered a recovery path.
The missing transition was invalidation before an offer.
This defect does not justify freezing tests or architecture.

The new route starts with supervisor invalidation.
The supervisor amends the same Issue and obtains a new execution boundary.
The writer corrects the source, tests and gates. Fresh candidate evidence then permits the existing readmit operation.
If no defect is observed, no modification or PR is required.
The control checks recovery from saved state.
It distinguishes accepted, offered, merged, closed and locally reconciled states.

Before production edits, the supervisor froze the extended observer outside the candidate.
Its SHA-256 is `082dcda0fa2b941b4c266cb0c59a2b46ba76bb3a5aaaedecc8184e18e1df416d`.
The old source fails the new invalidation control.
The same observer drives the treatment and planted negatives without importing candidate verdict logic.
The publishing verifier remains the previously selected external implementation.
No default-branch tip is loaded as judge.
The Issue and PR contain the exact runtime and delivery receipts. This prose does not replace them.
