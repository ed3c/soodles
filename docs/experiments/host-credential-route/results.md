# Host credential route: bounded combined correction

Issue ed3c/soodles#148. Baseline `861f314d9cfd5aeb993038437f3dcea0aa14f0ba`; treatment source `8ab969f3c4cc79d3a351ea7ad7f68233ed740126`. Claim: deterministic correction plus scoped combined nonregression. No landing authority is conferred by these results.

The observed gap was a missing executable route from an externally registered host capability to the existing Issue-atom entry. The old entry safely refused without NOODLES_TOKEN_COMMAND. This is not evidence of an unsafe historical delivery or a naturally occurring Agent failure. A private-key path alone does not identify the supplier, its selected bytes, App client or installation.

The same `issue-atom run AUTHORIZATION` now consumes a supervisor-owned external profile when no explicit supplier is set. It checks fixed supplier bytes and required App locators before invocation, returns exact redacted missing-field diagnostics, and retains the legacy supplier contract. The P-class recipe names that entry, the host owner, and exact-result consumption. No new scheduler, authority flag or automatic identity selection is introduced.

## Fixed deterministic controls

The original frozen oracle reports treatment GREEN, 13/13 predicates. Baseline met only the explicit legacy positive predicate; the other 12 expected new-capability predicates were RED. Registered configuration now reaches the existing admission handoff; missing profile/fields, changed supplier bytes, absent key, child context and in-candidate profile are refused. Supplier failure remains opaque and redacted. All synthetic cases recorded zero provider writes; refusals preceded provider construction and lifecycle checkpoints. These counters cover the supplied fixture, not arbitrary hidden native effects.

The original internal-profile baseline stopped earlier at the legitimate dirty-control-root check. An isolated Git-template exclusion run was retained only to investigate that precedence. Final treatment used the original unmodified fixture environment, without that exclusion. Implementation separates immutable authorization validation from clean-root checking so static host diagnostics can precede the latter; dirty-root rejection still occurs before supplier invocation, checkpoint or provider effect. A focused regression test protects that ordering. No existing safety refusal was recast as an exploit.

## Fixed fresh comparison

Exactly one independent fresh native consumer per arm, four supplied exposures each, same neutral task/driver and requested Astra/high. Actual exposed agent identities, requests, source and instruction digests, raw stdout/stderr and consumer reports are retained. Every recorded invocation matched its supplied packet. Both consumers preserved legal refusals, avoided retries and alternate commands in their reported decisions, and did not declare delivery complete: 0/4 observed decision barriers before and 0/4 after. Registered and legacy treatment fixtures reached admission; missing installation named the exact field; failed supplier returned its current owner prerequisite. No additional samples were taken.

This supports scoped combined nonregression, not lower Agent error rates, population estimates, or attribution to P-class alone. Native model internals and complete platform transcripts were unavailable. Recorder observations cover subprocesses; consumer rationale and statements about other activity remain self-report. Treatment guidance was first read through native calls and then recorded before fixture execution; that snapshot is not the first read itself. Token/time are not behavioral success criteria.

## Validation and delivery boundary

Source-stage full suite passed 348 tests with zero skips; focused credential and atom controls also passed. Initial interrupted subprocess attempts (SIGTERM, cause not established) remain external receipts; they were not reported as test passes. The writer must rerun the full suite on the evidence-complete candidate and preserve the final receipt. Manifest binds code, instruction and raw experiment evidence on this same PR.

At preparation of this immutable evidence, delivery remains pending. Native publication readiness, exact-head Linux acceptance, independently pinned external landing owner, provider merge/closure and local reconciliation remain required. The supervisor will register actual host capability only after merge, then invoke this exact already-resolved atom from a fresh process with supplier/App environment cleared. Its external terminal receipt will establish actual host use without creating another Issue or PR. This atom does not implement comparison-to-delivery enforcement, fresh-consumer scheduling or cross-atom accumulation.
