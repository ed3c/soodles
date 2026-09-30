# system-v1: contract index

Read only the boundary needed for the current task, together with [common authority limits](system-v1/common.md). These files preserve the existing requirements and transition owners; this index grants no execution authority.

Use `./system-context EXACT_REPOSITORY_RELATIVE_FILE [FILE ...]` to read the selected committed files and their required context. The read-only result supplies `source_head`, the selected dependency graph, existing `instruction_pins` and `instruction_context`; it does not choose a task, execute a next action or grant admission. Missing or unknown paths refuse explicitly. Existing consumers may follow the links directly, retaining the declared prerequisites in [routes.json](system-v1/routes.json).

## RUNTIME.ADMISSION.001

Read [`contracts/system-v1/runtime.md`](system-v1/runtime.md).

## ACCEPTANCE.BOOTSTRAP.001

Read [`contracts/system-v1/runtime.md`](system-v1/runtime.md).

## Authority limits

Read [`contracts/system-v1/common.md`](system-v1/common.md).

## LANDING.SUPERVISED.001

Read [`contracts/system-v1/landing.md`](system-v1/landing.md).

### Terminal candidate owner activation — ed3c/soodles#122

Read [`contracts/system-v1/landing.md`](system-v1/landing.md).

### Interrupted cleanup — ed3c/soodles#6

Read [`contracts/system-v1/recovery.md`](system-v1/recovery.md).

### Observed Git lock recovery — ed3c/soodles#8

Read [`contracts/system-v1/recovery.md`](system-v1/recovery.md).

### Atomic candidate delivery — ed3c/soodles#97

Read [`contracts/system-v1/candidate.md`](system-v1/candidate.md).

### Interrupted delivery preparation — ed3c/soodles#10

Read [`contracts/system-v1/recovery.md`](system-v1/recovery.md).

### Base advancement before delivery — ed3c/soodles#16

Read [`contracts/system-v1/recovery.md`](system-v1/recovery.md).

### Supervised correction before an offer — ed3c/soodles#19

Read [`contracts/system-v1/recovery.md`](system-v1/recovery.md).

### Owner next-action output — ed3c/soodles#21

Read [`contracts/system-v1/readback.md`](system-v1/readback.md).

### Exact comparison readback guidance — ed3c/soodles#25

Read [`contracts/system-v1/readback.md`](system-v1/readback.md).

### Dependent merged-commit readback — ed3c/soodles#29

Read [`contracts/system-v1/readback.md`](system-v1/readback.md).

### Cross-repository dependency satisfaction — ed3c/soodles#113, #115

Read [`contracts/system-v1/readback.md`](system-v1/readback.md).

### Local accepted-candidate publication — ed3c/soodles#128

Read [`contracts/system-v1/candidate.md`](system-v1/candidate.md).

### Local Issue atom shortest path — ed3c/soodles#131

Read [`contracts/system-v1/issue-atom.md`](system-v1/issue-atom.md).

### Issue-read argument recovery — ed3c/soodles#137

Read [`contracts/system-v1/readback.md`](system-v1/readback.md).

### Complete admitted child contract — ed3c/soodles#135

Read [`contracts/system-v1/instruction-context.md`](system-v1/instruction-context.md).

## Local selected-instruction activation

Read [`contracts/system-v1/instruction-context.md`](system-v1/instruction-context.md).

