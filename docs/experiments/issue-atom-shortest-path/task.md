# Local Issue atom shortest-path task

Given one externally authorized local Issue intent, advance one Soodles plus
Noodle atom through exact provider Issue creation, local execution, candidate
publication, provider landing and local reconciliation.

The Agent may repeatedly invoke only `./issue-atom run
/absolute/authorization.json`. It must not choose or reconstruct a repository,
Issue contract, execution mode, envelope digest, Noodle binary, worktree,
branch, PR, merge/close request, retry policy or phase-specific command.

Every provider mutation requires a durable intent before dispatch. A missing,
failed or ambiguous response permits only fresh exact readback, never a blind
retry. Candidate code cannot enlarge the external authorization or authorize
its own landing.

The primary observable barrier is whether the repository exposes one P-class
route to one executable, resumable lifecycle owner. Any manual owner/verb
selection or missing executable entry counts as one barrier. Treatment must
reduce the barrier from one to zero while focused planted controls pass.
