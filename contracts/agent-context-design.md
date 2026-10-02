# Agent context design: evidence before reusable instruction

Owner: [Soodles #39](https://github.com/ed3c/soodles/issues/39).
Class: P (design metaprompt). Status: experimental for the current integrated inputs.
Earlier comparisons support only their frozen inputs. They do not support this
integration or an improvement claim.
Read this file only when designing or auditing agent instructions, context
transfer, or their evidence. Ordinary implementation and verification do not
require it.

## Apply this metaprompt

Use current user intent, the exact Issue, candidate identity, relevant
instructions, and execution evidence. Produce the smallest instruction change
that improves a demonstrated task boundary. Keep proposals separate from
observations. Use existing owners and controls. This document grants no runtime,
provider, or verifier authority.

Report the requested outcome, instruction conflict with source locations, correction,
affected consumers and available evidence. Baseline/treatment observations and
non-cases belong only to a selected behavior comparison. Ordinary instruction
corrections need no experiment packet; report their static checks without claiming
measured behavior improvement. Never invent observations to fill a report format.

Write conditions and actions: **when this task/state applies, use this owner/source, continue to this observable result, stop for this named missing input**. Prefer outcomes and constraints for ordinary work. Preserve exact sequences for side effects whose ordering is part of correctness.

Use short sentences with one instruction each. Put the condition before its action.
Name the actor and use the same term for the same concept. Keep command and field names exact.
Separate historical observations from current instructions. These choices follow the practical
writing principles in [ASD-STE100](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
This is a writing aid, not a compliance claim, numerical score or new verification gate.

## Different documents, shared evidence discipline

| Location | Responsibility | Read when | Does not establish |
| --- | --- | --- | --- |
| `AGENTS.md` | Short working agreement, task routing, autonomy and completion | Harness discovers applicable instructions | Successful execution or authority beyond the user/platform boundary |
| `contracts/system-v1.md` | Named behavior, transition ownership, refusals, evidence scope and nearest controls | Task changes or disputes that boundary; select its section | Implementation correctness because a requirement is written |
| `SKILL.md` | Precise trigger, shared constraints and conditional recipe routing | Capability applies | That the skill was actually loaded or followed |
| Feature recipe | Inputs, existing CLI, observations and cleanup for one capability | Feature is being exercised | A second implementation of the owner state machine |
| `docs/` | Observations, plans, history, receipt summaries and proposals | Relevant evidence/history is needed | Correctness authority through prose |
| This file | Metaprompt for designing context surfaces | Instruction-design/context-transfer task | A universal prerequisite or model-specific safety exemption |

`system-v1` and `AGENTS.md` share clarity, scope, and provenance rules.
They serve different consumers. Keep behavioral requirements stable and route
to them. Do not copy every recovery branch into each entrypoint.
Current user instructions define task scope within higher-priority platform
and executable permission boundaries. Skills and model-generated contracts
cannot silently expand or narrow that scope. They cannot replace the requested
outcome with an intermediate artifact or add an approval gate.
Preserve the original outcome across admission and handoff. A limitation
describes a gap. It does not permit removal of the requirement. If an instruction
blocks work, name that exact instruction.

## Keep one operational route owner

[Root AGENTS — Session entry](../AGENTS.md#session-entry--select-once-then-act)
owns the cloud/local decision and shortest actions. README exposes that entry.
Skills consume the selected path. Do not copy a second decision table into this
metaprompt or require ordinary work to read it.

Select the path from the current task, available session tools, and actual
execution owner. Cloud Sessions use GitHub reads and existing Actions for
Soodles/Noodle controls. Only a local Noodle launch of a Codex child needs the
Codex CLI. Local runtime checks without a Codex child do not need it.
Keep the selection and evidence in the existing handoff. On resume, refresh
mutable state. Do not add a flag, selector process, or state store.

Check each route against its required outcome. A cloud request must reach
exact-head Actions evidence without scratch or CLI preflight. A local child
request must reach its admitted launcher and typed outcome. An unavailable
capability must block only its dependent operation.

For independent cloud work, use native subagent threads without inherited
conversation when the platform exposes that capability and delegation is
authorized. Context separation does not isolate the shared filesystem.
Pin read-only input refs and give each consumer its own evidence directory.
Keep the observer and expected outcomes outside consumer inputs.
This measured carrier does not require a new browser conversation, branch,
or worktree. Record actual connector document reads. Do not assume automatic
CLI injection. Fetch a draft route at its PR ref. Writing the route does not
install it into every future Session.

These are P-class instructions. Observe actual file loading and subsequent
behavior. Workflow success alone is not a matched Agent comparison.
The steered authoring Session is not a blinded fresh consumer. Keep unavailable
context internals unknown. Continue claims that have sufficient observable
evidence.

## N/P/L/R classify claims

These are Soodles conventions, not OpenAI terminology. Directories and extensions do not confer authority.

| Class | Meaning | Required discipline |
| --- | --- | --- |
| N | Descriptions, summaries, inventory, plans, metrics | Name subject/source/time and unknowns; separate proposed from observed |
| P | Model guidance, routing and this metaprompt | State applicability, scope, existing owner and completion/blocking boundary |
| L | Tested executable local discriminator | Bind subject, inputs, observer identity, actual execution/readback and residue; reject a defect and accept a valid case |
| R | Provider-enforced truth for a provider claim | Preserve exact provider subject, required checks and actual provider readback; local fixtures cannot supply it |

A prose contract can name an L/R requirement without proving it. Receipt
summaries are N. The underlying process or provider evidence supports only its
measured claim. Syntax checks prove syntax, not agent comprehension.
Local feature verification does not authorize landing. Existing external-verifier
selection and supervised reconciliation remain unchanged. If executable code
consumes prose, review the impact of prose changes even when the prose is N/P.

## Session intent becomes durable guidance through evidence

For an instruction correction, retain its source, reason, applicable task/state
and available evidence in the existing diff or task handoff. A selected behavior
comparison additionally binds model, harness, configuration, observations and
limits in its existing evidence. Ordinary corrections need no per-rule experiment
tuple, new record format or invented measurements. Preserve observable decisions,
actions and readbacks; do not copy entire sessions or hidden reasoning.

Session intent can establish a proposal immediately. Execution establishes
only the observed behavior. One case does not establish a universally optimal
prompt. If both baseline and treatment pass, the comparison shows scoped
non-regression. It does not show a repaired defect. A planted negative checks
the observer. It is not a historical baseline failure.

A handoff carries the goal, Issue/candidate, allowed scope, evidence/checkpoint
references, unresolved inputs, and next expected observation. Before acting,
the consumer rereads current owning state. Historical `next`/`request` is
evidence. It never permits replay. A new-session handoff differs from actual
model compaction.

## Context budgets and the short route

The earlier rule specifies **three document nodes**, or **two link edges**.
"3 hop" is ambiguous. This is a local navigation convention. It is not an
OpenAI requirement or context-window guarantee. Keep routes short while reading
necessary producers, consumers, controls, and evidence. Record additional causal
dependencies. Do not drop an invariant to meet a count.

Measure independently within the selected carrier. The CLI discovery details below apply only when that CLI actually loads the instructions; they are not assumed ChatGPT Session limits:

- Instruction discovery: global/project/nested paths and digests, injected bytes and truncation when visible. Codex documentation currently gives `project_doc_max_bytes` a 32 KiB default; record the effective setting of the tested version.
- Skill discovery: metadata catalog versus selected SKILL/recipe bodies. The documented catalog budget is at most 2% of model context, or 8,000 characters when unknown; that is not a budget for all skill bodies or total context.
- Inference context: rendered input tokens per request, effective window, next output/reasoning allowance and observed compaction boundary. Aggregate billed tokens and file bytes are not current window occupancy.
- Behavior: required context reached, task outcome, legitimate blocks, unnecessary questions, redundant checks and duplicate/unauthorized effects. Separate top-level commands from child commands.

For planning, subtract the current rendered context and the reserve for the
next reasoning/output/tool cycle from the effective window. The remainder is
headroom. Mark unknown terms unknown. Estimates are not gates. This proposal
supplies no universal utilization percentage or formula that maps context size
to hops.

If a real task lacks a dependency, repair the route to that dependency.
If measurements show pressure or truncation, reduce irrelevant entry text,
read bounded sections, or use supported harness compaction. A larger window
does not justify additional hops. A smaller window does not justify missing
evidence. In a selected document-only comparison, vary one factor. Keep the
model, permissions, harness, and compaction policy fixed.

## Physical comparison

Apply this section only when the admitted task selects a behavior comparison.
Unsupported improvement claims stay unsupported; they do not automatically authorize
an experiment or block an otherwise complete instruction correction.

Before judging a candidate, freeze task inputs and observable checks outside
it. Use isolated baseline and treatment sessions within the same selected
carrier. Keep the selected model, exposed reasoning and harness configuration,
tools, permissions, and fixtures the same.
For cloud runs, use the platform Session and observations from the connector
and Actions. Do not add Codex CLI to obtain them. Record unavailable internals
explicitly and limit claims that depend on them. Bind actual instruction and
skill digests and traces. Distinguish availability, loading, and use. A skill
listing establishes availability only.

Exercise an authorized task on the selected runner. Also exercise legal
blocking, unknown-write behavior, and a fresh-session handoff with stale
guidance. Observe actual tool calls and state. Before trusting the detector,
reject a planted bad result and accept a legal non-case. Experimental data
shaped like provider responses stays local. Never publish credentials.

One pair provides a scoped smoke comparison. It does not estimate efficiency.
Repeat only a concrete unresolved variation within the Issue's declared bound.
Real compaction stays NOT_RUN until evidence captures an actual harness
compaction event and a valid subsequent continuation. Only missing model or
observation capability required by the selected carrier can block that claim.
Unrelated local CLI failures do not block cloud work. Missing behavioral
observations remain NOT_RUN. They are not simulated success.
See [the historical #39 protocol](https://github.com/ed3c/soodles/blob/2e9d51261c80b2c5c120ca6549c759704c615c61/docs/experiments/agent-context/protocol.md).
The current admitted Issue selects any new comparison.

## Official basis (reviewed 2026-09-16)

- [Astra instructions and skills](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): conditional context, concise routing and explicit completion.
- [Astra model guidance](https://developers.openai.com/api/docs/guides/latest-model): autonomy, instruction conflicts and proportional verification.
- [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md): layered instruction loading and byte limit.
- [Skill loading](https://learn.chatgpt.com/docs/build-skills): metadata discovery and progressive disclosure.
- [Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/): harness-built inputs, appended tool results and compaction. Its implementation details describe publication time, not every later CLI.
- [Harness engineering](https://openai.com/index/harness-engineering/): repository knowledge as a discoverable map; the roughly 100-line example is not a universal cap.
- [Open Codex harness](https://developers.openai.com/blog/codex-as-a-platform): application-owned context/boundaries versus reusable execution loop.
- [Responses compaction](https://developers.openai.com/api/docs/guides/compaction): context carry-forward. API documentation is not evidence that this CLI run compacted.
