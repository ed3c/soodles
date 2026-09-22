# Local provider-readback shortest path result

Classification: **VERIFIED** for the bounded local provider-readback executable
continuation on candidate `358aad592049dc03d84e3ffdb8e63f3c56a27c66`.

## Exact candidate evidence

- tree: `ac48d91ecea3f7abd95b97b6e092bfc2c9323a71`
- runtime run: `35601247586` / job `106337616304` — success
- quality run: `35601247613` — success
- runtime artifact: `10639152166`
- artifact digest: `sha256:37ae55a105e6c4bbda6aa154b93d17eea7502608f61224c51557d957b9f3b350`
- canonical acceptance: 219 tests in 15.173s — OK
- acceptance: `zero_residue=true`, `authorizes_landing=false`

## Focused behavior

All six provider-readback controls passed:

- landing preserves owner request keys and returns exact selected-publisher re-entry;
- merged PR adds exactly one confirmed merge-commit GET;
- next-Issue readback follows provider pagination, filters pull requests and returns exact reconcile argv;
- P-class routes provider-readback through one executable entry without manual GET assembly;
- wrong method/host, missing credential and output overwrite refuse; and
- wrong publisher identity and redirects are hard refusals.

The bounded shortest path is:

```text
current next.kind=provider_readback
→ provider-readback consume
→ exact owner-emitted GitHub GETs
→ readback.json | complete frontier.json
→ exact transition-owner re-entry argv
```

The adapter performs zero provider writes. It may add only one dependent
merge-commit readback from a confirmed merged PR and provider Link pagination
on the same registered Issues frontier. Credentials remain inherited and are
absent from argv/files/evidence.

## P-class disposition

verify-noodle now routes local provider-readback to the dedicated executable
Skill instead of Agent-side GET/pagination/snapshot/re-entry assembly.

No fresh matched independent model baseline/treatment experiment was run, so the
P-class disposition is **SCOPED_ALIGNMENT**, not a quantified model-behavior
improvement.

Every candidate/fixture receipt remains `authorizes_landing=false`.
