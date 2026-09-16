# Issue #39 bounded cloud continuation

Class N; no landing authority. Prior records remain at c6ac2e1a43eb21993b8903a292bf3f60a80414f0.

Four fresh consumers actually invoked the pinned existing landing.advance owner
against disposable mutable checkpoints and simulated provider readback. All calls
returned exit 0, action readback, merge_pending, classification null, and no new
request. Independent supervising reads found before/after bytes identical with
SHA-256 e3881548ceababec1070e2509ead654f58249ce69a9c6bd6d4388143a17a14ed.
Offered history remains [merge]. All four live checkpoint files were then removed;
before.json/after.json remain evidence. Source blobs remain unchanged.

The two resume tasks used the real previous producer handoffs. resume_x captured
its handoff read; resume_y disclosed its initial handoff read was unrecorded.
No missing event was reconstructed. pending_x recorded initial discovery late;
pending_y disclosed unrecorded initial pwd. Failed discovery calls remain visible.

The frozen observer now returns INCOMPLETE without violations for all four new
packets. All lack complete_capture and observed_model; resume_y additionally lacks
handoff_received. This resolves the mutable before/after observation gap, not native
transcript/model provenance. Earlier raw REJECT results are preserved unchanged.

Two fresh route consumers received a runtime-review task, assigned instructions,
and no prescribed connector, Actions, CLI or browser route. Both selected GitHub
connector/Actions and correctly read exact-head canonical acceptance evidence
without a runtime rerun. This supports scoped route selection after explicit
instruction loading; it does not prove platform automatic injection/discovery,
reliable behavior on all tasks, improvement over baseline, or automatic delegation.
route_y encountered artifact download HTTP 403; no unchanged retry was performed.
Signed credential-bearing URLs were redacted and the limitation retained.

Requested model gpt-6-astra and native task identities are recorded in protocol.json.
Observed provider model and complete native transcript remain unavailable. No CLI
model probe, browser, live fixture write, production merge or closure occurred.
All captured records are consumer/supervisor observations, not authenticated native
platform export. Independent findings are in review.json.

The original Issue evidence gate still requires missing native capture/model
evidence. PR #40 remains draft and Issue #39 open; these tests cannot authorize
landing. The remaining blocker is specific platform telemetry, not cloud inability
to run checkpoint or route experiments. Do not repeat these bounded trials without
a new concrete variation or reinterpret missing observations as PASS.
