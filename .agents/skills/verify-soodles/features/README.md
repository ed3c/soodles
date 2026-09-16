# Soodles verification map

Initial scope: one user-facing feature, [runtime admission](runtime-admission.md). No claim of whole-app coverage.

Use a clean Soodles checkout and its already-admitted Linux amd64 Noodle binary. The executable driver in the parent skill provides isolation, command tracing, a receipt outside temporary state, and teardown. The first successful runtime check is both doctor and positive drive; reuse that observation within the run.

Every mapped feature must be driven during a full maintenance pass. A feature outside this index is not verified by this skill. A failed or unreachable path remains explicit in its receipt; a different successful path cannot replace it.
