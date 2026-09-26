# Issue #145: externally pinned sibling helper

The current baseline is main `820a579e3a9e6f6724f6defbcda2d0dc3422a87f`.
Its `resume_oracle.py`, `handoff_oracle.py` and selected order-handoff recipe
have the same SHA-256 bytes as the original Issue baseline. The candidate
source correction was tested at `a2da2e4eba431fb2547049f883e96378db99dbe4`.

The externally fixed comparator SHA-256 is
`4443f411750871806b17edfcfe764d7cd24eb96e7c8f8a7570e5f7ce96e13eba`;
its protocol SHA-256 is
`bed7c4e511019cc825a6e32a210cee7ea1127f33071b85d4d22cc46005086a71`.
Running those same bytes once per arm returned `OBSERVED_BARRIER` on baseline
and `NO_OBSERVED_BARRIER` on treatment. The matching case reached the deliberately
absent next dependency in both arms. In the planted mismatch, baseline executed
the candidate helper and wrote its marker; treatment loaded the external sibling
and left the marker absent. Both source trees stayed clean and at their exact
refs. The direct `test_issue_resume` suite passed 11 tests on the candidate.

`baseline.json`, `treatment.json` and `decision.json` contain the typed results.
`captures.tar.gz` preserves both raw process outputs, copied source/helper bytes
and marker. These observations distinguish the transitive verifier identity
boundary only. They do not grant landing authority or prove provider delivery.
Final exact-head Linux canonical acceptance and supervised landing remain.
