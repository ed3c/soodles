# Bootstrap with an admitted backlog, #166

The actual #156 re-entry on base `b6d4aac3e8c40cdc0b809fd3ce832460f0b7ee4c`
returned `noodle.bootstrap.owner=nonempty`: the one-cycle Noodle start exited zero,
but its full Issue backlog configuration caused a `schedule` order and session.
The failed control root and its canonical state remain with Noodle; the summarized
raw readback and source digests are in `raw/baseline.json`.

The admission producer now emits a separate pinned bootstrap configuration with
no Issue backlog adapter. Its existing start wrapper checks that configuration
for `--once`, and checks the full admission configuration for normal start.
The Issue-atom owner still requires a zero exit, empty Noodle owner, and restored
host configuration before continuing. A full-config `--once` is refused before
Noodle runs.

The selected real Noodle binary wrote an empty canonical snapshot in a disposable
fixture using the producer's bootstrap configuration, with no child invocation
(`raw/positive.json`). The 44 focused controls and 374 repository tests passed
(`raw/tests.txt`). These local observations are non-authorizing; exact-head Linux
runtime acceptance and external landing are required for delivery.
