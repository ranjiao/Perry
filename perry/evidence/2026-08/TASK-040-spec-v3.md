# TASK-040 spec v3 — the risks write path

**Row**: `TASK-040` — *risks are still read from a markdown table and are not
records in the store*. Rung **V3**.

**What already landed** (merged 2026-08-21, `68ca393`): the record shape
(`perry_store.RISK_STORED`), the renderer, the byte-identity gate
(`perry-tasks risks-diff`), the drift report (`perry-lint`), and the reader
unification — three implementations of three questions in `viewer/parsers.py`,
with `bin/perry-task`'s four names as **bindings**, asserted by `is` identity.
Read `perry/evidence/2026-08/TASK-040-result.md` first; it is the account of
that half and of why this half was deliberately left out.

**What USER-016 changed**: `schema/state-schema.json § claims` now declares
`risks.jsonl` (`owner: work`, `anchor: state`). The stop that halted the last
round is released.

## The scope

Build `perry-tasks risks-write --from-board`.

There is no `cmd_risks_write`. The dispatch at `bin/perry-tasks` prints a
refusal and returns 1. That refusal now reads the schema and picks between two
messages — `RISK_STORE_UNDECLARED` and `RISK_STORE_NO_WRITE_PATH` — and the
second one is the live branch today. Your change makes the second branch
unnecessary; **delete it and the selector with it**, do not leave a dead
message behind.

The model is `perry-tasks write --from-board` for tasks, and
`perry-okr write --from-file` for the OKR store. Read both before writing
anything. This is **the one-way import**: `BOARD.md § Top risks` → `risks.jsonl`,
run once per project, never in reverse.

## Five rules this has to satisfy

1. **`risks-diff` must still report `identical: true` on Perry's own board
   after the store exists.** Today it reports `source: "board"` because there
   is no store; once there is one it reads `source: "store"`, and that is the
   comparison that actually means something. `cells_verbatim` must stay `{}` —
   a cell that survives as a literal is a cell the renderer did not rebuild
   from a typed field.

2. **A risk with no date stores `""`, not today's date and not a zero.** An
   `opened` migrated from a bullet is genuinely unrecorded; a `cleared` on an
   open risk is genuinely absent. This project has already paid a day for a
   `current: 0` default that read as "met before the work started". There is an
   existing test for this — keep it green, do not weaken it.

3. **Refuse rather than guess on a section shape you cannot reproduce.** If
   `risks-build` cannot derive a record set whose render is byte-identical to
   what is on the board, the import must stop and name the row and the cell.
   *A migration that cannot reproduce what it replaces has not understood it.*

4. **`ADR-004`: a refusal means nothing was written.** Assert it — compare the
   board and the store byte-for-byte across a refused import.

5. **The event log.** `perry-task risk-add` / `risk-clear` append events. Decide
   whether the import does, state the decision in the code, and test whichever
   you chose. Do not leave it unstated.

## Out of scope, explicitly

- **Do not run the import on `perry/`.** Shipping the command and migrating
  this project are two acts; `git diff -- perry/` must be empty. The row's own
  merge note says so.
- **Do not touch `schema/state-schema.json`.** The declaration is done. If you
  believe the declared `## Top risks` markdown shape must change, **stop and
  report** rather than editing it.
- **Do not generalise into a `Register` abstraction.** `## Cadence`,
  `## Intake` and `## User Input Queue` are still document-shaped and the last
  round deliberately declined to invent a pattern from two instances. Three is
  a later decision, not yours.
- **Do not rewrite the risk *encoders*.** `bin/perry-state § encode_risk` and
  `bin/perry-task § cmd_list`'s risk dict are two answers to "what does a risk
  look like in a payload" and they already differ. Real, filed, not this.

## Verification

1. `risks-diff` on a fixture project **with** a store: `identical: true`,
   `source: "store"`, `cells_verbatim: {}`.
2. The import is idempotent — running it twice produces a byte-identical store.
3. A corrupted stored value makes the render diverge **at the right column**,
   and a hand-edited board cell raises exactly one `risk-store-drift` warning.
   Both already exist; they must still pass with a real store present.
4. A refused import wrote nothing — board and store byte-compared.
5. The dead refusal branch is gone: `grep -c RISK_STORE_NO_WRITE_PATH` is 0.

## Ground rules

- Branch `coding/task-040-risks-write`, commit there, **do not open a PR** and
  **do not push**. The PMO merges locally.
- Measure your own baseline before touching anything. Do not take a red count
  on trust — **the red set on this repository differs by interpreter**. Use
  `/usr/bin/python3` and say which you used.
- `python3 tests/parallel -j 4`. Never `bash tests/run` while another suite is
  running on this machine; two concurrent runs pollute each other and
  `test_host_support`'s dispatch-cap test reads machine-wide state.
- Known pre-existing reds on `/usr/bin/python3`: `test_diagnose` (two
  failures — TASK-153, and `['TASK-007','TASK-9999']`) and
  `test_contract_invariance` (`intake.oldest_undischarged was NoneType, now
  int` — a union-typed key, diagnosed in
  `evidence/2026-08/contract-invariance-union-types.md`, **not yours to fix**).
- `TASK-045` is running in parallel and touches `perry-state`, `perry-task`,
  `perry-goals`, `perry-decide` and `perry-lint`. You should need none of
  those. If you find yourself editing one, say so in your report.
