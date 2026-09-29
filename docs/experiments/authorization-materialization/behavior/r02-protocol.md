# Round 2, frozen before new consumers

The round-1 candidate is rejected with its raw failure retained. No confirmation has started. Round 2 changes only the causal P-class command to the existing `python3 -B` entry; CLI implementation and external deterministic judge are unchanged. The original primary metric, hard gates and case definitions remain fixed. Reuse the two completed fresh baseline runs; run one new fresh treatment consumer per train case against this changed candidate, not a retry of unchanged failed instructions. Keep the incomplete round-1 schema3 pair explicit. After these runs, fix the winner and run the untouched confirmation pair. No further tuning after confirmation. Native carrier limitations remain as in protocol.md.

Candidate: f6ac0fc22d1e66c676089a538ba49f6fd8a3807c
