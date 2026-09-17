# Issue 51: behavior-first P-class deletion eval did not authorize retention

N-class observation for [Issue 51](https://github.com/ed3c/soodles/issues/51).
Frozen executable fixture source: `defc5f41153837f4db5ee0858fd03c9029523c6c`.
Evidence archive commit: [`4802d2c786ef008a7dd189078626cee099ac73a5`](https://github.com/ed3c/soodles/commit/4802d2c786ef008a7dd189078626cee099ac73a5).

The proposed treatment deleted one 280-byte duplicated landing-guidance bullet
from `AGENTS.md`. Context, output and elapsed-time measurements were telemetry,
not correctness gates. The prospective retention rule was not satisfied, so
**AGENTS.md remains unchanged**. This result does not prove that the deletion
caused a behavior regression.

## Prospective method

The atom fixed three disposable owner cases before launch:

- pending provider write;
- missing merge-commit recovery;
- foreign provider identity.

Each case received three baseline and three treatment consumers: 18 fresh native
cloud sessions, opaque run IDs, no inherited conversation, common source/owner,
separate evidence directories and no live provider transport. The executable
observer checked task outcome, owner identity, refusal/recovery, checkpoint
identity, replay/request barriers and evidence. Explicit instruction reads,
commands, searches, bytes and elapsed time were also recorded.

The static check proved that the treatment removed only the named 280 bytes,
kept all non-entry instruction digests equal and left the executable owner and
skill guidance unchanged. Planted controls accepted legal fixtures and rejected
false resolution, omitted owner observation, wrong owner identity and a
string-valued owner receipt.

This structure follows the task-specific, logged, automated and continuously
compared eval process described by
[OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
The local observer and receipts, not context size, determined the outcome.

## Supervisor correction before the valid comparison

The first 18-run trial is invalid for the treatment claim. Its frozen observer
assumed `receipt.owner` was an object; eight consumers emitted a string, causing
the normalizer to raise `AttributeError` before judgment. The raw trial was
preserved rather than repaired in place.

A fresh supervisor boundary then:

1. required an object receipt with exact owner entry and operation equally in
   both arms;
2. made non-object owner values produce `authority_ambiguity`, not a crash;
3. added a planted string-owner control;
4. froze new inputs and launched 18 replacement sessions.

The correction changed no treatment, fixture, owner behavior or retention rule.
[Supervisor correction](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/supervisor-correction.json) and
[freeze](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/freeze.json) preserve that boundary.

## Blinded result

The arm-blind auditor verified packet
`ead59884f9ef6cd90225b338fbf437efa005d66a84ab6eaf8911b47f5f41f6a8`
before assignments were revealed.

| Case | Runs passing frozen correctness | Observable case behavior |
| --- | ---: | --- |
| Pending | 3 / 6 | All six reached fresh GitHub readback without a request; three lacked an observer-bound direct `cat` read |
| Foreign identity | 1 / 6 | Five refused `pr.head.repository`; one recorded no owner event; five lacked an observer-bound direct `cat` read |
| Recovery | 0 / 6 | All first refused missing `merge_commit`; five did not consume the supplied correction; one continued and then emitted a close request |

Seventeen of eighteen runs passed the frozen decision-barrier counters. One
recovery run invoked `landing dispatch` after reaching `close_pending`, causing
the observer's `guessed_owner_command` and `provider_request_emitted` errors.
No provider request was transported and no live side effect occurred.

[Blind audit](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/blind-audit.json) records 4/18 total correctness passes and
was saved with SHA-256
`b42f7dba4a859d0f2b6f09afd2fdfdf9aa603f27c918c4b6d3a4f31fb06f9e4a`
before unblinding.

## Unblinded result and retention decision

| Case | Baseline pass | Treatment pass | Repeated explicit instruction reads |
| --- | ---: | ---: | ---: |
| Pending | 3 / 3 | 0 / 3 | 0 in every run |
| Foreign identity | 0 / 3 | 1 / 3 | 0 in every run |
| Recovery | 0 / 3 | 0 / 3 | 0 in every run |
| **Total** | **3 / 9** | **1 / 9** | **0 in every run** |

The treatment-side recovery run that continued also emitted the close request.
Therefore the frozen gates resolve as:

- all 18 correctness evaluations pass: **false**;
- no treatment decision-barrier error: **false**;
- duplicate guidance removed while owner remains: **true**;
- no stable repeated-read degradation: **true**;
- blind observable audit passes: **false**.

[Unblinded result](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/unblinded-results.json) classifies the candidate
`RETENTION_RULE_FAIL_AGENTS_UNCHANGED`.

## What this establishes

The atom physically demonstrates a behavior-first eval loop:

1. freeze task-specific outcomes and negative controls;
2. run isolated consumers;
3. preserve an invalid trial instead of fitting the observer to its results;
4. repeat under a separately frozen correction;
5. commit a blinded audit before revealing assignments;
6. apply the prospective retention rule;
7. retain no instruction change when required evidence fails.

It does **not** demonstrate that the 280-byte deletion is harmful. The baseline
itself failed every recovery run, so this dataset is not a valid equivalence
baseline for that case. Most `missing_entry_read` errors came from shell-wrapped
`cat` or `sed` commands that the recorder could not bind as direct file
arguments. The close request is an owner-produced proposal, not provider
transport; the frozen observer intentionally treated it as a barrier, but this
exposes a future oracle question rather than a proven side effect.

A later atom should first make the recorder bind shell-wrapped instruction reads
and separately classify request creation versus connector transport. It should
not add another P-class rule or rerun this deletion until those observer
boundaries discriminate a valid baseline.

## Evidence and limits

[Archive manifest](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/archive-manifest.json),
[observer controls](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/observer-controls.json),
[static check](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/static-check.json) and
[blind packet](https://github.com/ed3c/soodles/blob/4802d2c786ef008a7dd189078626cee099ac73a5/docs/experiments/pclass-behavior-51/raw/blind-packet.json) provide the readable index. The manifest
binds split tar archives containing both the invalid trial and the complete v2
command records, stdout/stderr, checkpoints, tasks, receipts and observer results.

Native model provenance, hidden reasoning, complete platform traces, input-token
counts, effective context-window occupancy and hidden reads were not exposed.
Claims are limited to recorded external behavior in these fixtures. No receipt
authorizes landing, future deletion, or a global behavior-equivalence claim.
