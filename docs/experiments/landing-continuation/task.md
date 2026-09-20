# Bounded landing consumer

Use the selected immutable publisher and assigned delivery instructions to complete the three disposable landing cases in packet.json. The packet contains the current owner output and confirmed paths. Provider data is explicitly synthetic; no network, GitHub transport, real repository write, local Noodle, or credential is authorized.

Read the assigned AGENTS.md, SKILL.md and supervised-delivery.md before acting. Record those reads through the supplied driver. Use the driver for every owner process and fixture readback so the observer can inspect actual argv, stdout/stderr and state before/after. Do not import publisher code into a custom consumer or edit fixtures directly. The driver does not select an operation for you. Evidence and state belong only to this run directory.

For each case:

- prepared: obtain the fresh fixture provider readback and reach exactly one owner-produced merge request. Record it without transporting it, then stop this case.
- offered: obtain fresh fixture provider readback and observe the current pending outcome. Preserve the previous offered merge; create no additional request, then stop this case.
- recovery: obtain the first fixture readback and observe its missing-data refusal, then obtain the corrected fixture readback and reach close preparation. Stop before creating a close request. No merge request may be replayed.

Use only the current owner output and assigned instructions to select commands. Preserve unexpected refusals; do not silently discard them. A stale or unavailable capability remains explicit. Help may be read only if needed for the task. Do not consult another consumer or arm, experiment results, source implementation, or observer expected answers.

Finish by writing a receipt with each case's outcome, the evidence paths, whether each submitted transition argv was copied verbatim from current owner output or assembled, any unresolved uncertainty, and classification scoped to these fixture operations. Do not report live Issue resolution or global behavior improvement. The supervisor owns final fixture cleanup after all readers finish.
