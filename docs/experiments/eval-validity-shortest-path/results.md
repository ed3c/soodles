# Issue #146: report evidence validity and the shortest supported consumer route

Claim: **combined deterministic correction plus scoped nonregression**. This is not an isolated P-only result, a model-behavior improvement, full-map verification, or a delivery gate.

The archived #143 evaluator incorrectly accepts missing/null operation observation as no operation, and groups source/read-binding errors with behavior barriers. It remains unchanged. The intentionally selected successor supports one feature-map report family through the externally supplied `./soodles eval report SELECTION.json EXPECTED_SHA256` invocation. The adapter verifies selector/evaluator bytes before loading; P-class guidance consumes validity, then behavior and current supervisor-owned missing input. Empty operation arrays retain consumer-report scope.

## Fixed deterministic qualification

The protocol and oracle were fixed outside the candidate before implementation. Actual legacy subprocess outputs are preserved alongside candidate subprocess outputs. No live provider transport occurs in these disposable controls.

| Control | Legacy output | Corrected output |
| --- | --- | --- |
| Complete normal | NO_OBSERVED_BARRIER | VALID / PASS |
| Valid wrong route | OBSERVED_BARRIER | VALID / FAIL |
| Missing operations | NO_OBSERVED_BARRIER | INCONCLUSIVE / null behavior |
| Null operations | NO_OBSERVED_BARRIER | INCONCLUSIVE / null behavior |
| Wrong source | OBSERVED_BARRIER | INVALID / null behavior |
| Wrong instruction digest | OBSERVED_BARRIER | INVALID / null behavior |

The fixed oracle goes from RED (four failed predicates) to GREEN (6/6). Original valid non-cases remain intact. Unit controls additionally cover pre-import selector/evaluator sentinels, malformed evidence, path escape, byte-count types, zero-byte reads, and exit codes. Source/evidence digests bind raw results; candidate report strings do not decide these external controls.

## One fresh pair

Exactly one baseline and one treatment consumer were started with `fork_turns:none`, requested native Astra/high, the same neutral task and four identical opaque reports. The treatment was frozen at source head `85f34beed1b507fabf01520dd3e883633b5303a5` before launch. P-class and executable digests in the manifest/selection must remain identical through final delivery; the later evidence-only commit changes the candidate head.

Both consumers reached correct bounded conclusions for all four cases: **0/4 observed decision barriers before and 0/4 after**. The baseline consumer read the old evaluator and independently rejected its misleading conclusions on incomplete/invalid evidence. The treatment consumed the explicit validity/behavior split and current typed next. There is no demonstrated decrease in Agent errors, and no additional sampling was performed. Command/time data remain telemetry, not a substitute behavior score.

Recorded subprocess argv, raw stdout/stderr, exit codes, file snapshots, consumer reports, selectors and input bytes are retained in `raw/consumer-runs.json`. Consumer self-reports are distinguished from recorder observations. Actual native model/config internals, full platform transcripts, hidden reads and independently verified absence of all effects remain unknown. The report family itself proves only consumer-report scope. Shared storage is not security isolation.

## Candidate and delivery boundary

One Issue and one PR contain the correction, minimal P-class/ownership alignment, fixed protocol/oracle, raw evidence and manifest. #143 history is byte-identical. No fresh-consumer launcher, map maintenance, scheduler, generic evaluation platform or merge/closure comparison gate was added.

The initial full local test process was terminated with exit 143 and its incomplete log was retained externally. A process-session-isolated run completed 336 tests with one pending evidence-dependent integration test. That intermediate run is not final acceptance. After this evidence patch, the writer must execute the oracle integration and complete the full suite with no skips; native publication readiness and exact-head Linux Actions remain required. The external `issue-atom` owner retains provider and local terminal receipts. This pre-publication experiment record does not claim merge, closure or RESOLVED; comparison results never grant landing authority.
