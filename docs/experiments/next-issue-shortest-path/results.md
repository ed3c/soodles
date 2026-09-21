# Next-Issue shortest path result

Classification: **VERIFIED** for the bounded RESOLVED → exact next-Issue provider
identity path on candidate `29cc1209c8fe90b50221e85ae44a085ddafc74df`.

## Attempts

- `327fba31d4fa1bc4d3c8ce3e8e421f9bea5517b8`: immutable RED. Exact candidate
  verification correctly rejected the Issue because the P-class treatment path
  was in `required_paths` but omitted from the Issue `write_paths`. The Issue
  contract was corrected; this head was not rerun.
- `29cc1209c8fe90b50221e85ae44a085ddafc74df`: implementation GREEN.

## Exact candidate evidence

- tree: `413045281788871cff101a26d8e4d4d4c708b1ff`
- runtime run: `35587224079` / job `106293244705` — success
- quality run: `35587223863` — success
- runtime artifact: `10632987144`
- artifact digest: `sha256:7e85e998770d05c725c2d92a16aaf3dcbb0472eb54fea446ad4d081ec0697c26`
- canonical acceptance: 220 tests in 13.164s — OK
- acceptance: `zero_residue=true`, `authorizes_landing=false`

## Focused behavior

All seven next-Issue controls passed:

- dependency and write-boundary qualification are mechanical gates;
- local create consumes only the persisted intent and stops at provider Issue identity;
- P-class contains one executable entry and no manual create decisions;
- one eligible candidate materializes one exact Cloud create intent;
- unknown create outcome performs zero automatic retry and adopts one exact readback;
- unresolved predecessor/incomplete frontier refuse before intent; and
- zero/multiple eligible candidates never invent product priority.

The bounded shortest path is:

```text
RESOLVED
→ finite supervisor semantic candidates
→ complete provider frontier
→ eligibility / dependency / duplicate / write-boundary gates
→ exactly one eligible candidate
→ persisted causal fingerprint + create intent
→ Cloud exact connector request | Local exact executable
→ exact provider Issue readback
→ STOP
```

Zero eligible candidates stop. More than one eligible candidate returns
`selected_candidate` to the supervisor. No lexical/oldest/first-item priority
rule exists.

## P-class disposition

The new next-Issue Skill and verify-soodles route remove backlog discovery,
candidate ranking, Issue-body assembly and transport selection from the
instruction surface. Executable tests bind that route to the CLI.

No fresh matched independent model baseline/treatment experiment was run in this
atom, so the P-class disposition is **SCOPED_ALIGNMENT**, not a quantified model
behavior improvement.

Terminal success of this owner is one exact open GitHub Issue identity. Noodle
scheduling/admission remains a downstream owner. Every candidate/fixture receipt
is non-authorizing.
