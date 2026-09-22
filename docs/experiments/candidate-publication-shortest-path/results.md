# Candidate publication shortest-path result

The frozen task was observed against Soodles main
`cf204ed40050198b5dfe3b1848baaab9e729ada9` and this treatment worktree.

| Arm | Primary barrier | Focused tests | Classification |
| --- | ---: | ---: | --- |
| Baseline | 1 | exit 1 (entry/tests absent) | FAIL |
| Treatment | 0 | exit 0 | PASS |

The treatment provides one P-class command backed by one executable owner.
Focused controls cover exact create/reuse, dirty and stale refusal, drifted PR
refusal, failed-push readback, lost-create adoption and unknown-create stop.

These fixtures are L-class local discrimination only. They perform no live
provider mutation and authorize neither landing nor Issue closure.
