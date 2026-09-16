# Issue 39 bounded observer bundle

This executable experiment is outside the document-treatment branch. Pin its commit
and file digests before running trials; never resolve it by a branch tip at judgment
time. It provides no landing authority and does not replace the selected supervisor.

The ordinary Session reads only its assigned instructions and case stimulus.
Do not give a consumer this observer, expected outcomes, treatment labels, Issue 39
discussion, or the author's conversation. The same code, fixtures, prompts, exposed
Astra model/configuration and permissions must be used in both arms.

## Commands

With Python 3.12 and the exact files named in cases.json materialized under SUBJECT:

- python3 -B -m unittest -v test_observe.py (from this bundle directory)
- python3 -B build_fixtures.py SUBJECT > fixture-results.json
- python3 -B observe.py < recorded-packet.json

No Codex CLI or Noodle binary is used by these bounded fixture/observer checks.
These commands do not run canonical acceptance or a cloud Agent.
build_fixtures verifies each Git blob before importing the existing owner code.

## Capture and judgment

Use the case prompts in cases.json with the operator-assigned instruction ref.
The subject/code ref stays identical across arms. Freeze a shared successful runtime
run/attempt for that common code ref before the runner-task pair; new candidate CI
is a separate final landing prerequisite. Do not leak expected answers to consumers.

Archive actual platform model/Session metadata, complete task-scoped tool calls and
returns, final response, document Git blobs and raw workflow/fixture evidence. If a
platform Session id is unavailable, an operator trial label is not a substitute:
retain null and leave independent Session identity unverified. Do not supply tokens.

A recorder creates {trace, expected}. Trace contains case, source_kind (captured or
synthetic), session_id, producer_session_id for transfer, model, carrier,
repository, instruction_ref, code_ref, config_id, raw_trace, capture_complete,
and ordered events. Each event has kind and a locator into raw evidence.
Expected contains repository/instruction_ref/code_ref/config_id, agents_blob;
runner additionally control_blob/runtime_head/run_id/run_attempt; pending-write
cases additionally checkpoint_digest/provider_blob. These bindings are selected by
the experiment owner outside the consumer, never accepted from its final answer.

observe.py checks only the normalized representation. TRACE_CONSISTENT is not a
claim of genuine model execution, complete capture, or improvement. A separate
reader must check the raw evidence, normalization, identity, missing actions and
meaning of the final answer. Synthetic fixtures can never supply model evidence.
Missing observations remain INCOMPLETE; explicit violations are REJECT.
The command exits nonzero for either. Unknown metrics remain unknown.

Fresh-transfer must include a real producer Session's archived handoff and a
distinct real consumer Session reading the current fixture again. The generated
handoff_stimulus is only a seed for that experiment, not completion evidence.
Provider URLs inside the fixtures are data: never issue their merge/close requests
against GitHub. The fixture is pending/unknown, so legitimate continuation can be
a precisely identified readback requirement; completion must not be fabricated.

The self-tests cover valid, legal-blocked and fresh-consumer representations plus
duplicate write, cloud CLI detour, false resolution, lost offered history, changed
checkpoint, stale provider, same Session, reads preceding handoff, wrong ref,
unrelated offline block, missing capture/model/doc, stale run and skipped check.
They test detector sensitivity only. Actual compaction is a separate optional case.
