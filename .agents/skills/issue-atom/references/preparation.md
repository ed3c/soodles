# Supervisor preparation

Use the existing [authorization producer recipe](../../verify-soodles/features/local-supervisor-admission.md).
The supervising Session selects actual host inputs and an independent immutable
publisher, then consumes the producer's authorization and continuation unchanged.
Do not hand-build derived authorization fields or ask the user for generated files.
