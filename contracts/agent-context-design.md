# Agent context design: evidence before reusable instruction

Owner: [Soodles #39](https://github.com/ed3c/soodles/issues/39).
Class: P (design metaprompt). Status: experimental; matched Astra behavior has not been established.
Read only when designing or auditing agent instructions, context transfer or their evidence. This is not an additional prerequisite for ordinary implementation or verification.

## Apply this metaprompt

Given current user intent, the exact Issue, candidate identity, relevant instructions and execution evidence, produce the smallest instruction change that improves a demonstrated task boundary. Keep proposals separate from observations. Use existing owners and controls; this document grants no runtime, provider or verifier authority.

Return: (1) the requested outcome and legitimate stop condition; (2) the instruction conflict or missing context with source locations; (3) the minimal patch and affected consumers; (4) baseline/treatment observations and a legal non-case, or the exact missing prerequisite; (5) a reusable rule scoped to that evidence. Never invent a failure, model measurement or successful handoff to fill this format.

Write conditions and actions: **when this task/state applies, use this owner/source, continue to this observable result, stop for this named missing input**. Prefer outcomes and constraints for ordinary work. Preserve exact sequences for side effects whose ordering is part of correctness.

## Different documents, shared evidence discipline

| Location | Responsibility | Read when | Does not establish |
| --- | --- | --- | --- |
| `AGENTS.md` | Short working agreement, task routing, autonomy and completion | Harness discovers applicable instructions | Successful execution or authority beyond the user/platform boundary |
| `contracts/system-v1.md` | Named behavior, transition ownership, refusals, evidence scope and nearest controls | Task changes or disputes that boundary; select its section | Implementation correctness because a requirement is written |
| `SKILL.md` | Precise trigger, shared constraints and conditional recipe routing | Capability applies | That the skill was actually loaded or followed |
| Feature recipe | Inputs, existing CLI, observations and cleanup for one capability | Feature is being exercised | A second implementation of the owner state machine |
| `docs/` | Observations, plans, history, receipt summaries and proposals | Relevant evidence/history is needed | Correctness authority through prose |
| This file | Metaprompt for designing context surfaces | Instruction-design/context-transfer task | A universal prerequisite or model-specific safety exemption |

`system-v1` and `AGENTS.md` share clarity, scope and provenance rules but serve different consumers. Keep behavioral requirements stable and route to them rather than copying every recovery branch into each entrypoint. Current user instructions define task scope within higher-priority platform and executable permission boundaries. A skill cannot silently expand scope or add an approval gate. Name the exact instruction when it actually blocks work.

## Select the active carrier before capability checks

Infer the execution path from the current user task, session context, invoked connector/launcher and provider readback. Record the actor, executor and observed basis once for that operation; re-evaluate when ownership/path changes. Binary presence, OS and a previous Session do not select the carrier. If evidence is insufficient, inspect the intended operation's existing owner rather than trying a speculative model launch.

| Actual path | Agent and execution owner | Applicable prerequisites |
| --- | --- | --- |
| Cloud ChatGPT Session → GitHub connector → Actions → Soodles/Noodle | Current Session reasons and calls the connector; Actions runs repository controls/runtime | Available connector action, correct repo/head/workflow, runner prerequisites and provider run/artifact readback; no Codex CLI requirement |
| Local Soodles → Noodle → Codex child | Local Noodle owns child execution | Admitted local Noodle plus usable local Codex CLI/authentication/launcher and child outcome evidence |

For the cloud path, load required repository documents through the connector and record exact file refs/blobs and returned content. Do not assume that an arbitrary fetched AGENTS file was automatically injected by a local CLI. Record session/model information exposed by the platform, connector actions, workflow version, run/attempt/head, job/step outcomes and available artifact receipts. Platform internals not exposed by the cloud carrier remain unknown, not a reason to invent CLI measurements.

A scratch-container failure, absent local Noodle or failed Codex CLI probe cannot block the cloud connector/Actions path. A missing cloud action, required fixture, trace or fresh-session observation can block its dependent operation. Preserve other authorized progress. Use existing pull-request workflows for canonical acceptance and bind each result to its tested head. Do not create a second model runtime or require API credentials merely to test the Agent already operating this Session.

This carrier-selection instruction is P-class. Provider run readbacks prove the exact workflow execution; they do not prove a matched Agent comparison. The current Session's correction after receiving the intended answer is not a blinded baseline/treatment run. An independent cloud Session can supply a fresh consumer without any Codex CLI. Unknown internal prompt/token data limits those measurements, not every observable behavior claim.

## N/P/L/R classify claims

These are Soodles conventions, not OpenAI terminology. Directories and extensions do not confer authority.

| Class | Meaning | Required discipline |
| --- | --- | --- |
| N | Descriptions, summaries, inventory, plans, metrics | Name subject/source/time and unknowns; separate proposed from observed |
| P | Model guidance, routing and this metaprompt | State applicability, scope, existing owner and completion/blocking boundary |
| L | Tested executable local discriminator | Bind subject, inputs, observer identity, actual execution/readback and residue; reject a defect and accept a valid case |
| R | Provider-enforced truth for a provider claim | Preserve exact provider subject, required checks and actual provider readback; local fixtures cannot supply it |

A prose contract can name an L/R requirement without proving it. Receipt summaries are N; underlying process/provider evidence supports only its measured claim. Syntax checks prove syntax, not agent comprehension. Local feature verification does not authorize landing. Existing external-verifier selection and supervised reconciliation remain unchanged. Executable consumers of prose require change-impact review even when the prose is N/P.

## Session intent becomes durable guidance through evidence

For each retained rule, preserve a compact provenance tuple: intent/Issue, applicable task/state, observed failure or successful control, source/model/harness/config identity, evidence link, limitation and revalidation trigger. Preserve observable decisions, actions and readbacks; do not copy entire sessions or hidden reasoning.

Session intent can establish a proposal immediately. Execution establishes only the behavior actually observed. One case does not establish a universally optimal prompt. Both baseline and treatment passing is scoped non-regression, not a repaired defect. A planted negative checks the observer; it is not a historical baseline failure.

A handoff carries goal, Issue/candidate, allowed scope, evidence/checkpoint references, unresolved inputs and next expected observation. The consumer rereads current owning state before action. Historical `next`/`request` is evidence, never a replay capability. A new-session handoff is different from actual model compaction.

## Context budgets and the short route

The earlier rule says **three document nodes**, which is **two link edges**. “3 hop” is ambiguous. This is a local navigation convention, not an OpenAI requirement or context-window guarantee. Keep routes short while reading necessary producers, consumers, controls and evidence. Record additional causal dependencies instead of dropping an invariant to meet a count.

Measure independently within the selected carrier. The CLI discovery details below apply only when that CLI actually loads the instructions; they are not assumed ChatGPT Session limits:

- Instruction discovery: global/project/nested paths and digests, injected bytes and truncation when visible. Codex documentation currently gives `project_doc_max_bytes` a 32 KiB default; record the effective setting of the tested version.
- Skill discovery: metadata catalog versus selected SKILL/recipe bodies. The documented catalog budget is at most 2% of model context, or 8,000 characters when unknown; that is not a budget for all skill bodies or total context.
- Inference context: rendered input tokens per request, effective window, next output/reasoning allowance and observed compaction boundary. Aggregate billed tokens and file bytes are not current window occupancy.
- Behavior: required context reached, task outcome, legitimate blocks, unnecessary questions, redundant checks and duplicate/unauthorized effects. Separate top-level commands from child commands.

For planning, headroom is effective window minus current rendered context and the reserve needed for the next reasoning/output/tool cycle. Mark unknown terms unknown; estimates are not gates. This proposal supplies no universal utilization percentage or formula mapping context size to hops.

If a real task lacks a dependency, compare the shortest complete route with a direct reference to that dependency. If measured pressure/truncation occurs, reduce irrelevant entry text, read bounded sections or use supported harness compaction. A larger window does not justify additional hops; a smaller window does not justify missing evidence. Vary one factor at a time. Do not change model, permissions, harness or compaction policy inside a document-only comparison.

## Physical comparison

Freeze task inputs and observable checks outside the candidate before judging it. Use isolated baseline/treatment sessions within the same selected carrier, with identical Astra model, exposed reasoning/harness configuration, tools, permissions and fixtures. In cloud runs, use the platform Session and connector/Actions observations; do not add Codex CLI to obtain them. Record unavailable internals explicitly and limit claims that depend on them. Bind actual instruction/skill digests and traces. Distinguish available, loaded and acted-upon: a skill listing establishes availability only.

Exercise an authorized task on the selected runner, legal blocking/unknown-write behavior, and a fresh-session handoff with stale guidance. Observe actual tool calls and state. Reject a planted bad result and accept a legal non-case before trusting the detector. Experimental provider-shaped data stays local. Never publish credentials.

One pair is a scoped smoke comparison, not an efficiency estimate. Repeat only a concrete unresolved variation within the Issue's declared bound. Real compaction stays NOT_RUN until an actual harness compaction event and a valid subsequent continuation are captured. Only missing model/observation capability required by the selected carrier can block that claim; unrelated local CLI failures do not block cloud work. Missing behavioral observations remain NOT_RUN, not simulated success. See [the #39 protocol](../docs/experiments/agent-context/protocol.md).

## Official basis (reviewed 2026-09-16)

- [Astra instructions and skills](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): conditional context, concise routing and explicit completion.
- [Astra model guidance](https://developers.openai.com/api/docs/guides/latest-model): autonomy, instruction conflicts and proportional verification.
- [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md): layered instruction loading and byte limit.
- [Skill loading](https://learn.chatgpt.com/docs/build-skills): metadata discovery and progressive disclosure.
- [Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/): harness-built inputs, appended tool results and compaction. Its implementation details describe publication time, not every later CLI.
- [Harness engineering](https://openai.com/index/harness-engineering/): repository knowledge as a discoverable map; the roughly 100-line example is not a universal cap.
- [Open Codex harness](https://developers.openai.com/blog/codex-as-a-platform): application-owned context/boundaries versus reusable execution loop.
- [Responses compaction](https://developers.openai.com/api/docs/guides/compaction): context carry-forward. API documentation is not evidence that this CLI run compacted.
