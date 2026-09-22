# Independent final guidance replay

Origin: #99. Fresh reviewer `/root/atom99_guidance_replay`, fork_turns none,
read-only. The following is the coordinator-preserved final return; full native
transcript provenance is unavailable. No source edits, provider contact or
landing authorization were performed by this reviewer.

Independent read-only review supports the bounded guidance result, with the limits below.

| Runs | Frozen observer result | Independent reason adjudication |
|---|---|---|
| X1, X2 | CHOICE_MISMATCH: next_action | Both explicitly request the unsupported execution envelope before correction: 2/2 detour handoffs. This follows incorrect producer guidance, not model misconduct. |
| Y1, Y2 | MATCHING_CHOICE | Both request correction on a new immutable head of the same PR, preserve subject identity, and introduce no envelope dependency: 0/2 detour handoffs. |
| Z1 | CHOICE_MISMATCH: next_owner | Legally preserves a distinct corrective Issue/PR after merge. Soodles Issue admission describes the new admission boundary without inventing an old-owner operation. Keep the strict mismatch unchanged. |

Verification completed:

- All five archived request/result objects exactly match original recorder files
  under fresh-atom-RIUzPp/runs/*/initial-read. Archived stdout matches original
  stdout byte-for-byte and equals the complete task/context/case concatenation;
  stderr is empty. Named file hashes and sizes match before/after and current bytes.
- X/Y differ only in candidate_output.next.owner and next.required[0]. The B head
  is 149adac52f71c78d4507b4425ff9d04ed0a7ab43, tree
  7d4b2de954ea013f84b5049e350df16585357c34. A/B/C baseline/treatment fixtures
  have equal base, head, tree, input and manifest; A/C outputs are unchanged.
- The source diff changes only the instruction-digest refusal's recovery owner
  and requirement, for both baseline and treatment digest checks. Refusal
  predicates remain intact.
- Original discovery scores recompute exactly: A1/A2/C1/C2 match; B1/B2 retain
  next_action mismatches; D1/D2 retain next_owner mismatches. No failures became green.
- Original reasons agree with their cases: A requests same-PR evidence completion;
  B requests the erroneous envelope prerequisite; C follows current readback
  requirements without claiming landing authority; D requests the new rollback boundary.
- Five read-only replay/control tests passed.

Prelaunch controls are separately evidenced by preflight/existing-controls:
three named tests passed before the first guidance read. Their source covers
historical baseline-byte mismatch refusal, missing/wider admission-envelope
rejection, and actual matched A/B/C verifier drives. The stdout/stderr hashes bind.

Limits and remaining gates:

- That preflight recorder has empty file snapshots; it does not itself bind
  imported test/source bytes. Preserve separate external source pins.
- Launch records request fresh contexts and no model override. Complete platform
  transcript, hidden reads, actual model provenance, tokens and compaction remain
  unknown. Recorder completeness does not prove complete model-visible delivery.
- D's post-merge missing artifact is a stipulated scenario premise, not a defect
  demonstrated by the resolved owner output.
- This establishes four first-handoff observations plus one legal-case control,
  not actual correction, transport, efficiency, model-specific performance, or
  P-class prompt improvement.
- Provider acceptance, external publication authority, merge and closure were
  not verified by this reviewer. Those remain separate delivery gates.
