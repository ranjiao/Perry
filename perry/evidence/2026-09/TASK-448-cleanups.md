# TASK-448 — the two things round 3 left open

> Branch: `coding/task-448-cleanups` · base `dd129bca` · no new row (the user
> asked for both under TASK-448).

Round 3 built `tests/live_stores.py` so that a fixture copies named parts of
this repository's state root instead of `shutil.copytree(ROOT / "perry")`, and
it found two things in its own work that it did not fix:

1. the copy still carried all seven stores to four call sites that read none of
   them — round 3's own mutation table records `copy_state` copying no stores
   leaving `test_board_render` and `test_task_store` green;
2. `tests/test_store_is_canonical.py § test_the_right_types_are_read_off_the_writer`
   still said *"the live store proves it"* after round 3 took that module off
   the live state root.

Both are done here.

---

## 1. The dead store copies

### What each call site actually reads

Read by measurement, not by reading the code alone: each part was withheld and
the modules re-run (the mutation table in § 3 is the same instrument).

The load-bearing fact is `tests/printed_board.py`. Both modules put **the board
this repository's stores print** on disk and then run `perry-tasks
write --from-board`. The live rows therefore arrive through the BOARD, and the
`*.jsonl` files copied beside it are opened by nothing, or opened and
discarded.

| # | call site | what it runs | what it reads | was | is |
|---|---|---|---|---|---|
| A | `test_board_render.py § Project.perry` (~150) | `write --from-board`, then `render` / `diff` / `verify` | the board, the anchor, and the `tasks.jsonl` **it writes itself** | 7 stores + anchor | `stores=False, events=False` |
| B | `test_board_render.py` (~554) `test_rendering_without_a_store_is_not_a_pass` | `render` on a project with no store | the anchor only — the case is the absence | 6 stores + anchor (`skip=("tasks.jsonl",)`) | `stores=False, events=False` |
| C | `test_task_store.py § setUpClass` (~61) | `build` | `bin/perry-tasks § build` reads the BOARD and the EVENT LOG and opens no store | 7 stores + anchor + events | `stores=False` (events kept) |
| D | `test_task_store.py § TestTheStoreReproducesTheBoard.copy()` (~89) | `write --from-board`, `verify` | the board, the anchor, and `.perry/events.jsonl` | 6 stores + anchor + events (`skip=("tasks.jsonl",)`) | `stores=False` (events kept) |
| E | `test_task_store.py` (~145) `test_build_and_verify_touch_no_file` | `build`, `verify` | **`tasks.jsonl`** — `verify` loads the store from disk and exits 2 at the door without one | 7 stores + anchor + events | `stores=("tasks",)` |

Site E is the correction to a first reading of this task. Copying its store
looks dead by the same test that made A–D dead — the module is green without
it — but `verify` *does* open it, and with no store on disk the case would be
asserting that a command which bailed immediately wrote no file. "Not detected
by an assertion" and "not read" are different findings, and only the second one
licenses deleting the copy.

Site C is the correction to the dispatch, which said `setUpClass` needs
`.perry/events.jsonl` "because `write --from-board` recovers closed rows from
the event log". `setUpClass` runs `build`, not `write`. `build` reads the event
log too (`bin/perry-tasks § build`, first paragraph), so the conclusion holds
and the reason is different — and **neither case under `setUpClass` can feel
it**: withholding the event log there is green. It is copied because it is
read, and the comment now says exactly that.

Bytes no longer copied, per call: 190,977 across the six non-`tasks` stores at
every site, plus 586,661 for `tasks.jsonl` at A, C and E.

### What changed in the helper

`copy_state` grew `stores`, which is `True` (all), `False` (none) or a tuple of
store names, and `_wanted_stores` **refuses a name that is not a store** — a
typo would otherwise copy nothing and look identical to a caller that asked for
nothing, which is the silent half of the defect this module exists to remove.

`skip=` is gone. It named store files to leave out and its only two callers
were the no-store cases (B and D), which say `stores=False` now; a parameter no
caller passes is the same dead weight. `tests/store_fixture.py § full_project`
is a second helper with no callers left — it is NOT touched here, because it is
outside what was asked and removing it is its own decision.

### `test_decoration_changes_nothing` is a third caller and is left alone

It takes the default `stores=True`, and that is correct: its readers
(`perry-state --json`, `perry-task list --json`, `perry-lint --json`) open
those stores, and the `break-a-type` mutation in § 3 reddens it, which is the
proof. **It is also green under `no-stores`, and that is a residual finding
this task does not fix.** Bolding only rewrites `*.md`, so the stores
contribute identically to both sides of the comparison; with no store at all
the two payloads are equal and empty and the module passes on the silence. Its
existing anti-vacuity assert covers the *documents* half (`assert decorated`)
and has no counterpart for the stores. Reported, not repaired: the module is
outside this cleanup's two named subjects, and the repair is an assertion about
what its fixture must carry, not a change to `copy_state`.

---

## 2. A claim that is no longer true

### The correction in place

`tests/test_store_is_canonical.py § test_the_right_types_are_read_off_the_writer`
said *"`depends_on` is a LIST, and the live store proves it … the live store
must pass its own gate"*, and failed with *"Perry's own store must satisfy the
type table"*. USER-942 took the module off the live state root in TASK-448
round 3, so `self.project()` builds `tests/store_fixture.py § BOARD` — three
synthetic rows — and the gate runs over what the WRITER wrote.

That is still worth gating, and it is what the test's own name says
(*read off the writer*), so the case is corrected in place rather than moved:
the docstring now says the table is read off what `perry-tasks write
--from-board` writes, records that the wording outlived the fixture by a round,
and points at where the live half went. The failure message says *"a store this
repository's own writer produced"*.

### The live half, rehomed

Nothing else asserted it. `store-badly-typed` is asserted in six modules
(`test_store_is_canonical`, `test_duplicate_ids_are_refused`,
`test_ns_collision`, `test_risks_store`, `test_store_drift`,
`test_cadence_store`) and every one of them runs against a fixture.
`test_bin_surface` is the only module that lints this repository itself, and it
counts census lines, not types. So the guarantee was unchecked.

Added: `tests/test_live_state_expectations.py §
TestTheLiveStoreSatisfiesItsOwnTypeGate`, two cases.

- `test_every_live_record_survives_the_type_gate` — `perry-lint` over a copy of
  the live `perry/tasks.jsonl` prints no `store-badly-typed`, **and** its census
  line names all 453 records. The count is half the assertion: the gate's first
  run excluded all 98 records because the table said `depends_on` was a string,
  and a check that reported survivors without the total would have read clean.
- `test_the_gate_is_reached_at_all` — the anti-vacuity half. Both assertions
  above are satisfied by a lint that never opened a store, so this plants a
  string `order` in the COPY and requires the gate to name the row.

**Why there.** The claim is about the live state, which is that module's
subject. It is the read direction of that module's own guard: live state as the
SUBJECT under test, rather than live state standing in for a value a tempdir
should have produced. The sweep in `tests/live_state_expectations.py` does not
flag it, and the recorded floor is unchanged.

**Why a copy** (`NN-5`). `perry-lint` only reads, but the mutation that proves
the case can fail has to break a type in a store, and no test may write into
the tree it runs in. `live_stores.copy_state(stores=("tasks",))` puts the live
bytes under a tempdir — which also makes this the one call site that asks that
helper for a store it will genuinely read, so § 3's first mutation has somewhere
to land.

`COVERS` gains `bin/perry-lint`, `tests/live_stores.py`, `perry/tasks.jsonl`
and `.perry/config.jsonl`. That is the honest declaration and it has a price
under `DESIGN-021 § 5.2`: this module is now selected whenever the task store
changes, which is often. It is also the only time the new case can newly fail.

`test_store_is_canonical` is NOT re-coupled to the live state root.

---

## 3. Mutations

Each on a fresh scratch copy under `$TMPDIR/perry-scratch/<agent>/`, never in
the repository. Modules run: `test_board_render`, `test_task_store`,
`test_decoration_changes_nothing`, `test_live_state_expectations`,
`test_store_is_canonical`.

| mutation | where | result |
|---|---|---|
| **`copy_state` copies no stores** (`for store in ()`) — TASK-448's own mutation, re-run | `tests/live_stores.py` | **red**, named: `test_live_state_expectations.TestTheLiveStoreSatisfiesItsOwnTypeGate.test_every_live_record_survives_the_type_gate` and `.test_the_gate_is_reached_at_all` ("this fixture asked `live_stores.copy_state` for the task store and did not get one"). `test_board_render`, `test_task_store` and `test_store_is_canonical` are unchanged **by construction** — they ask for no store, so the mutation copies exactly what they already got. `test_decoration_changes_nothing` green — § 1's residual. |
| **`copy_state` never copies `events.jsonl`** | `tests/live_stores.py` | **red**, named: `test_task_store.TestTheStoreReproducesTheBoard.test_it_carries_closed_tasks_the_board_no_longer_holds` (109 records, 109 board rows). Site D is the one site that can feel the event log; C and E are green, which is why their comments say the log is copied because it is read. |
| **`copy_state` breaks a type in the store it copies** (`order` → `"3"` on the first record) | `tests/live_stores.py` | **red**, named: `test_live_state_expectations…test_every_live_record_survives_the_type_gate` — the § 2 case can fail — and `test_decoration_changes_nothing…test_every_reader_reports_the_same_thing_on_a_bolded_board` (`perry-task` exits 1), which is the proof that module's copied stores are read. |
| **`copy_state` ignores `stores=`** (copies all seven regardless) | `tests/live_stores.py` | **red**, named: `test_board_render.TestItRendersAndNothingElse.test_rendering_without_a_store_is_not_a_pass` — site B's `stores=False` is load-bearing, not decoration. |
| **the type gate is renamed out of the linter** (`store-badly-typed` → `store-typing-was-not-checked`) | `bin/perry-lint` | **red**, named: `test_live_state_expectations…test_the_gate_is_reached_at_all` and `test_store_is_canonical.ABadlyTypedStoreIsReportedNotFatal.test_a_wrong_typed_field_is_named_and_the_row_excluded`. Recorded because the first attempt at this mutation replaced the id with `store-badly-typed-DISABLED`, which still **contains** the original string, so every `assertIn` passed and the run came back green. A green mutation that is green because the mutation did nothing is not a finding. |

---

## 4. Verification

- Each changed module green alone, by name: `test_live_state_expectations`
  (23 tests), `test_board_render` (14), `test_task_store` (7),
  `test_store_is_canonical` (10).
- `bash tests/run`, `PERRY_PROJECT` and `PERRY_HOME` unset, on the final
  commit: all green, tree guard clean (*"nothing under … moved"*).
- `tests/durations.json` **not** updated. Interleaved A/B, three rounds each,
  base tree vs branch tree in the same shell (medians):

  | module | base | branch | delta |
  |---|---|---|---|
  | `test_board_render.py` | 1.39 | 1.09 | −0.30 |
  | `test_task_store.py` | 1.64 | 1.31 | −0.33 |
  | `test_store_is_canonical.py` | 0.71 | 0.71 | 0.00 |
  | `test_live_state_expectations.py` | 7.20 | 7.39 | +0.19 |
  | `test_task_store_read_cutover.py` (control, untouched) | 1.54 | 1.48 | −0.06 |

  Nothing moves by more than 0.5 s. A first, non-interleaved measurement read
  `test_store_is_canonical` at 3.47 s against a recorded 0.69 — five times its
  own figure, for a module whose only change is a docstring. It was the first
  round of a cold run, and the base tree showed the same inflation when it was
  measured the same way. Quoted because a 5× on an unchanged module is what a
  wrong baseline looks like.

## 5. Architecture

No section of `ARCHITECTURE.md` changes. `NN-5` is respected in the new code
and is the reason the § 2 case runs over a copy rather than over `ROOT`; `§ 2
tests/` — a test must assert what it claims — is the whole of § 2 above. No
new `§ 7` question is opened.
