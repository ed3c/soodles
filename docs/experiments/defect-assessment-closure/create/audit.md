# eval-audit: registered local create continuation

## Error analysis
Problem exists: actual next-issue POST returned 500 without request identity, subsequent Session needed explicit user instruction and manual supplier wiring. Exact code reproduction additionally showed a second execute could send a second POST. Source-backed fixtures distinguish initial ready, offered unknown and genuinely absent registration. The successful direct create does not establish User-Agent as the cause of the historical 500.
Fix: reuse registered supplier, persist offered state before transport, serialize same-intent entry, verify successful response by exact GET, and emit the existing reconcile continuation with its data destination.

## Evaluator design
Objective handoff schema/subject/current-next checks use the pre-existing binary evaluator and six planted controls. Product fixture observes actual owner code and provider method ledger. These do not determine whether arbitrary agent prose is semantically correct. Full traces receive explicit supervising Session review; no claim of an independently validated semantic judge.

## Judge validation and human review
Cannot determine general semantic evaluator accuracy: no human-labeled calibration set, TPR/TNR or independent human review. Semantic conclusions are bounded qualitative reviews of these supplied traces. Raw process capture and source/state comparisons are external to the consumer; this independence must not be conflated with semantic adjudication. The task forbids provider effects; it evaluates a fresh continuation handoff, not end-to-end autonomous creation by the model.

## Labeled data
Small fixed three-stratum sample. It discriminates this observed credential/continuation failure but cannot estimate a population failure rate or guarantee global nonregression. Baseline follows an inadequate owner output; its manual token obligation is a workflow failure, not evidence that the model disobeyed its instructions.

## Pipeline hygiene
Old failed-head comparison and confirmation remain historical and valid only for their unchanged source scope. New create extension has separate source/input freezes, three bounded hypotheses and once-only confirmation after selection. r03 binds the previously absent reconcile argv. Code review also strengthened exact GET number validation before final confirmation. Never relabel prior score as final-source evidence. Preserve every run including carrier-command corrections and counts.

Selection shell-call medians: baseline 6, CLI-only r01 7, CLI plus revised P r02 6, explicit continuation r03 6. Original 20% efficiency criterion is unmet. Do not infer efficiency from fewer unresolved input strings or from incomplete baseline work. Product correctness retention and unsuccessful efficiency search are separate reported outcomes.
