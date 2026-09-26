# Selected instruction activation — ed3c/soodles#156

The fixed external oracle reports 16/16 PASS for code head
`fa3667645e38326a68f551a33a3b98c53d794840`. The baseline at
`00a5909941a632537dc6992b5354cd37614ea4a8` rejects valid selected-instruction
inputs because the API/schema is absent: capability RED → GREEN. Its six
reported PASS cases include broad schema refusals; they do not establish the
matching new negative guards. Treatment supports valid input, preserves the
legacy sentinel, and discriminates every frozen negative.

Authorization schema 3 selects nonempty instruction pins at its exact base.
Existing admission resolves committed regular UTF-8 files, seals the context
in envelope schema 2, and carries it unchanged through the canonical prompt.
Invalid selection precedes provider/checkpoint effects; invalid envelope or
prompt precedes worker launch. Explicit bounds are 32 files, 262144 UTF-8 bytes
per file and 1048576 total bytes. They are input bounds, not a context-capacity
claim. Schema-2 authorization and schema-1 envelopes preserve legacy behavior.

The supervisor ran exactly one fresh native consumer per arm (`fork_turns:
none`), with the same inherited configuration and no model/reasoning overrides.
Both consumer-produced results preserve the supplied owner's INCONCLUSIVE
state as `behavior: null`, `required: ["raw_results"]`, owner
`external-supervisor`, and `authorizes_landing: false`. The observer's PASS
means this bounded result matches the criterion; it does not turn the missing
underlying evaluation evidence into a behavior PASS.

| Independent reader measurement | Baseline sample-a | Treatment sample-b |
| --- | ---: | ---: |
| Input reads | 1 | 1 |
| Recipe reads | 1 | 0 |
| Input bytes returned | 4184 | 18045 |
| Separate recipe bytes returned | 12866 | 0 |

One required recipe acquisition read was removed because treatment received
those bytes in its stage prompt. Both legal results support scoped
nonregression and reduced recipe acquisition, not generalized model improvement
or fewer wrong behavior barriers. There is no token, latency, cost, capacity or
compaction claim. Telemetry records actual reader selections, digests, byte
counts, argv, PID and timestamps. Other platform operations, a complete
transcript, independently observed model ID and hidden internals are unavailable.
The inherited configuration is not independent proof of an Astra model ID.
The frozen observer replay also rejects a planted non-null behavior result.

Provider and Noodle state in the oracle/input producers is synthetic disposable
fixture data. Launcher CLI and worker sentinel subprocesses actually execute;
their success proves byte supply and local refusal, not model adherence or live
provider truth. The native consumers are actual independent contexts. Snapshot
fixtures are helper data; the active oracle, observer, protocol, reader and both
instruction arms were fixed externally before implementation. `frozen-selection.json`
and the delivery manifest bind their bytes and all saved empirical artifacts.
Replay tests run the fixed oracle against current production source and the
fixed observer over saved inputs in disposable directories; they do not launch
fresh consumers or replace the external judge.

Qualification failures remain in `raw/qualification-controls.json` and
`frozen/qualification.json`. A supervisor precommit CLI check also found that an
instruction AdmissionRefusal produced empty stdout instead of the atom's JSON
continuation. Its original receipt remains at
`/Users/neon/.codex/experiments/instruction-activation-az86ajr2/raw/precommit-cli-refusal.json`.
Commit `fa3667645e38326a68f551a33a3b98c53d794840` adapts that refusal to
AtomRefusal; an actual CLI control verifies the exact field, external owner,
same next.argv and absence of supplier/checkpoint effects. The initial 80
focused controls and the subsequent 41 correction controls passed without skips.

This live deployment intentionally uses legacy schema-2 authorization with a
schema-3 Issue contract and the previously pinned external publisher. New
schema-3 authorization is exercised in fixtures only; no first live R use is
claimed. Future live use needs a supervisor-selected compatible published
owner. Candidate source cannot promote itself into its own judge. The next-use
claim covers only explicitly selected bytes at the admitted source; existing
sessions are not retroactively refreshed, and semantic compliance remains
empirically bounded.

The complete evidence belongs to this one Issue/PR. Full repository controls,
native publication readiness, final exact-head Linux canonical acceptance and
supervised landing/reconciliation remain distinct delivery gates. This evidence
has `authorizes_landing: false`; neither a local suite nor this document grants
merge, closure or reconciliation authority.

## Readmission after #168

This candidate starts at `3d8f6490994cefa7d092d427c5f73be12824b3fe`.
The supervisor-selected patches `fb796ada5e5c51dceb9a281a8423b505525e67de`
and `fa3667645e38326a68f551a33a3b98c53d794840` were applied in that order.
The import conflict retains both scoped order identity and instruction resolution;
the contract conflict uses the external exact overlay. The four active instruction
files match `readmission-selection.json` (SHA-256
`f6b8fc2bc1327a71b754c8ac71e11af5de0242df7d1ac22ac64ba4558ee5448b`).
Its baseline is this admitted base. The overlay retains #161 pristine-root
bootstrap, #166 backlog-isolated bootstrap and #168 root-scoped order guidance.
Their production code and existing discriminating controls remain present;
#164 landing continuation code is unchanged by this atom.

All 39 original delivery evidence files were copied, and all 37 records in the
external `live/evidence-ready.json` matched before adapting this results file
and manifest. Frozen inputs and raw telemetry remain byte-for-byte unchanged.
The historical consumer pair measured only the unchanged execute guidance and
selected recipe. It did not measure the readmission edits to issue-atom guidance
or the system contract; this readmission does not claim another fresh pair.
`manifest.instructions` binds the active overlay while `frozen-selection.json`
continues to bind the historical baseline/treatment experiment.

The historical raw oracle still names `fa366764`; it is not an exact-head
receipt for this candidate. The source-byte record below records SHA-256
comparisons made from that Git commit's actual source and current source:

| Executable source | Same bytes as historical oracle subject | Preserved new-base differences |
| --- | --- | --- |
| `issue_admission.py` | No | Root-scoped order validation |
| `issue_atom.py` | No | Pristine-root bootstrap and scoped-order continuation |
| `issue_execution.py` | Yes | None |
| `supervisor_admission.py` | No | Isolated bootstrap config/launcher and scoped-order production |

```json
{
  "historical_head": "fa3667645e38326a68f551a33a3b98c53d794840",
  "base_head": "3d8f6490994cefa7d092d427c5f73be12824b3fe",
  "files": [
    {
      "path": "issue_admission.py",
      "historical_sha256": "1b7d6891d2d7a7958a09a77e072c6b523ee029c4ad4d44aa5ba3f991927fa728",
      "candidate_sha256": "6bb652a9c1b41f9ad68b83fbf589bcf2a668b80eca6944752497c152798889fa",
      "unchanged": false
    },
    {
      "path": "issue_atom.py",
      "historical_sha256": "362be3efb0fd16e80383c56046a8c63bdbccdeea0db968a862abce9e2ce36d37",
      "candidate_sha256": "fc709be6efbb3b252c91000bdfd4f4f495646ca2b05b969474cc7a798748b214",
      "unchanged": false
    },
    {
      "path": "issue_execution.py",
      "historical_sha256": "d4c66cd582c454e9b997b8ff95cf87278d5a841ba49c88899cf6b3b4ff77d12c",
      "candidate_sha256": "d4c66cd582c454e9b997b8ff95cf87278d5a841ba49c88899cf6b3b4ff77d12c",
      "unchanged": true
    },
    {
      "path": "supervisor_admission.py",
      "historical_sha256": "11aeda62d621074c22b2876b55be053ee52551f19f861a50dad841356e0d1937",
      "candidate_sha256": "4b28dae7e49af10eced199441c274dff2825a9bb1819dd9dd347d763b03b559a",
      "unchanged": false
    }
  ],
  "scope": "Historical oracle receipt is unchanged; replay uses current source with preserved bootstrap, backlog-isolation and root-scoped order changes.",
  "authorizes_landing": false
}
```

The replay test checks current source hashes and runs the unchanged frozen
16-case oracle against these current executable bytes. This is a fresh local
fixture replay, not a relabeling of the original receipt or Linux acceptance.
The replay also verifies the overlay hashes against the admitted base, the
historical selection, complete evidence manifest and planted observer sensitivity.

Readmission validation uses `TMPDIR=/private/tmp`. The first 11 instruction and
replay tests passed, including all 16 oracle cases. The first additional focused
run executed 82 tests with one failure: the host-bundle control inherited this
real child's `NOODLE_SESSION_ID`, producing `worker.spawn` where its intended
missing-session input requires `worker.session_id`. The test now explicitly
removes that inherited session before launching its disposable worker; the
production guard and assertion are unchanged. The failed run remains at
`/private/tmp/soodles-156-validation-_jmjknzn/focused-tests.log`, with the
instruction run and correction run alongside it. The final full repository
run is recorded in that directory as `full-tests.log` and `full-tests.json`.
These local controls are non-authorizing; the parent retains publication,
final exact-head Linux acceptance, provider landing and reconciliation.

The initial complete suite passed 387 tests without skips. During its run,
manifest self-review caught an extra source-comparison field incompatible with
the existing closed manifest schema. That record was moved into this document
and the replay control; production schema validation was not widened. The
existing delivery validator then accepted the staged tree with all 51 changed
paths. The first full-run receipts are preserved as
`full-tests-before-manifest-review.log` and `.json`; the final-content full run
uses the `full-tests` paths above. Diff review reports one pre-existing final
blank line in the externally frozen baseline contract; those pinned bytes are
preserved, and all other changed files pass the whitespace check.
