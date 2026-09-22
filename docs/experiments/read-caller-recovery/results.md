# Issue #137: Issue-read caller recovery and recipe

The actual old recipe omitted the required repository argument. The real parser
then returned admission-specific execution_envelope recovery for this read error.
The correction changes only that CLI recovery, its direct guidance and scoped
system-v1 invariant, with executable nearest regression tests. No repository
profile, transport, credential route, scheduler or acceptance authority changes.

Baseline: `1497c07b795edbec3841cb5760371efd4769391d`.
Measured source candidate: `23762788d9bd143ee5fa7a894a282b0c20227a1b`.
The following evidence-only commit does not change measured instructions/code.

## Independent evidence axes

| Axis | Before | After | Supported claim |
| --- | --- | --- | --- |
| Frozen real CLI controls | 3/5 | 5/5 | Recipe executes; malformed read recovery no longer requests an envelope |
| Fresh normal read consumer | 1 sample, 0 barriers | Not run | NO_OBSERVED_BARRIER; no hill-climb claim |
| macOS default temporary path suite | 288 tests, 7 failures + 1 error | 291 tests, identical 7 failures + 1 error | Same named path-sensitive failures, not waived |
| Physical TMPDIR environment control | 288 tests pass | 291 tests pass | Scoped environment control, not Linux acceptance |

The fresh consumer actually read execute, issue-execution and the old github-read
recipe, then selected the correct repository + Issue argv. It read fixture Issue
44 open on its first call; wrong argv, wrong owner, envelope requests and recovery
calls were all zero. Eight completed shell calls include normal lifecycle help,
verification and outcome readback, not eight Issue reads. It wrote only result.json.
The source system-v1 was not explicitly read; no behavior is attributed to it.
Do not confuse the synthetic execution Issue118 with experiment owner Issue137.

The predeclared stop rule therefore ended behavior sampling. No treatment model
was launched and no baseline was repeated until failure. The deterministic RED
inputs prove specified recovery/correspondence improvement, not natural error.
This is a combined CLI/P correction, never isolated P-only efficacy. An observed
successful baseline cannot negate a separately reproduced defective command.

The initial P-only assumption was disproved by the pre-consumer CLI control.
protocol.md remains unchanged; amendment.md records the explicit scope change
before any consumer/candidate. Task, sample limit, scoring and fixed observer
did not change after results. Fixture transport substitutes only HTTP under the
real parser/reader; it proves neither App token scope nor live network reliability.

Noodle dispatched a new Codex exec with no inherited conversation. The raw archive
preserves actual prompts, command requests/results, source digests, owner and
session identity, preflight and cleanup. Worker completed outcome was read back.
Loop exit 1 is retained: backlog.done correctly refuses closure of the still-open
synthetic Issue. Recorded processes were absent before fixture removal. Native
worker exit is null/unknown; do not substitute the model's success message.

## Gates and feature-map boundary

Default macOS TMPDIR exposes the same eight path-sensitive test failures in both
subjects. The changed paths do not include their implementations. The separate
physical-path control passes both subjects. Existing native_readiness itself
already selects a physical temporary directory; no gate/test was disabled and no
carrier portability fix was added. Publication still requires that native gate;
landing requires existing Linux exact-head canonical acceptance.

All nine verify-soodles features received read-only source review. That is not a
full live maintenance pass. Other map/recorder/admission/recovery findings remain
out of scope and are retained in map-audit.md inside the raw archive. This atom
qualifies only github-read correspondence/recovery and one bounded P-class
baseline; its eventual delivery uses the existing delivery owners.

protocol.md, amendment.md and observer.py are externally fixed inputs copied
unchanged. raw.json binds a lossless archive and all member hashes; manifest.json
binds both instruction digests and required artifacts. Unknown hidden reads,
backend model identity and full nested telemetry remain unknown. No evidence here
grants landing authority or claims that publication/merge already occurred.
