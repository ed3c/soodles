# Landing continuation relocation, #164

The frozen observer failed on the exact base: `landing-supervisor` emitted a valid
final checkpoint, but `next.known.readback` and the last two `next.argv` entries
still pointed into the deleted temporary directory. The baseline receipt is in
`raw/baseline.json`.

The correction checks the selected owner's temporary paths before rebasing its
top-level checkpoint, both known inputs and both argv inputs to the final
directory. A malformed owner argv
now refuses instead of returning a misleading continuation. The same observer
passed after the correction (`raw/candidate.json`). All 6 focused tests and the
368-test repository suite passed (`raw/tests.txt`). These are local, non-authorizing
results; exact-head Linux runtime acceptance and the external landing owner remain
required for provider merge and Issue closure.
