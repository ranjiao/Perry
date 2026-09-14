# TASK-237 deliverable 3a — result: nothing needs `BOARD.md`

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (3) § Deliverable 3a`.
> `schema/state-schema.json`, `perry/BOARD.md`, the six stores,
> `.perry/events.jsonl`, `ARCHITECTURE.md`, `.perry/hook.md` and the lane docs
> are unchanged on this branch. No id was minted and no row opened. Every
> `BOARD.md` deletion below happened inside a scratch copy.
>
> **Delivered, with one stop.**
> - **Read surfaces:** with `BOARD.md` deleted, every listed read payload
>   equals the payload with it present, apart from four fields that describe
>   the file and one clock (§ 2). The floor is gone:
>   - `asks --all` returns 33 of 33;
>   - `list` risks are 2 open and 2 cleared, source `table`;
>   - `drift.drift` is 0;
>   - `perry-state` risks are 2, source `table`.
>
>   This item includes **TASK-268** (`top_risks` built from `BOARD.md`).
> - **Writes:** 24 of the 27 declared writes exit 0 without the file. Each
>   lands the same store record, event and journal line as with it (§ 3), and
>   the file is still re-rendered when it exists.
> - **STOP: `cadence-add` and `cadence-done` cannot succeed without the file.**
>   `## Cadence` has no store, so the row lives only in `BOARD.md`. With no
>   file they now refuse and write nothing, rather than lose the row at exit 0
>   (§ 3.2). Making them succeed needs a cadence store, which is a schema
>   `claims` decision, not 3a's.
> - **`risk-migrate`** refuses identically in both states on this project:
>   there are no bullets to migrate.
> - **One present-state value changed, by judgement, and the reviewer should
>   rule on it (§ 2.2).** `asks[].idle` for USER-001 and USER-002 was `"—"`
>   read from the board's `Idle` cell and is now `""`. The ask store holds no
>   `Idle` field on purpose, so `idle_days` is `null` in both.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a50288c323f9a0ae8` |
| HEAD at dispatch | `583f024f` |
| tree | clean (`git status --porcelain` printed nothing) |
| `git merge-base --is-ancestor b7c89276 HEAD` | **exit 1**: stale |
| action | `git merge --ff-only b7c89276`, on this branch only |
| re-asserted | exit 0; HEAD `b7c89276` |

The dispatch's floor was measured on `d358a2cf`. Re-measured at `b7c89276`,
`drift.drift` is **96**, not 97: one more row has closed since. Every other
floor value matched.

Commits on this branch:
- `62169826`: the code and the test module;
- `fbc8be5d`: two guards sharpened before the mutation battery;
- the commit carrying this file: the durations entry.

All measurements below are on `git archive` copies of `fbc8be5d`, the final
code.

## 1. The call-site enumeration

**Method.** First, the base archive's read payloads were diffed with the file
present and then deleted, key path by key path. That found every read site
whose output moves. Then a grep: `BOARD.md`, `load_snapshot`, `snap.board`,
`board_text`, `board_as_authored`, `user_input_queue`, `top_risks` and
`ctx["board"]` over `bin/` and `viewer/`. That gave 386 lines in 15 files,
each filtered to "does this site's output depend on the file". The write side
came from `perry-task --describe --json`: 27 subcommands with non-empty
`writes`, each run in both states on the base (§ 3).

### 1.1 Sites changed

| # | site | before | after |
|---|---|---|---|
| C1 | `viewer/parsers.py § load_snapshot`, the risk register | `has_risk_table(board_text)` → the board's table, else board + `PROJECT_STATE.md` bullets | `risks.jsonl` when it exists (**TASK-268**); the old two branches only for a project with no risks store |
| C2 | `viewer/parsers.py § parse_board`, `## User Input Queue` | always parsed from the text | not read when `asks=` is given; `_asks_from_store` fills `user_input_queue`, and the P0 priority heuristic runs over it as before |
| C3 | `parse_board`, `## Intake` | parsed from the text | not read when `intake=` is given; `_intake_from_store`, with `discharged` through `intake_is_discharged` |
| C4 | `parse_board`, `## Top risks` → `BoardState.risks` | parsed | from the store when `risks=` is given; the field has no consumer, but it now agrees with `top_risks` |
| C5 | `viewer/parsers.py § _parse_risk_table` | row → `TopRisk` inline | `_register_risk(statement, id, status, opened, cleared=None)`, **one rule** for a table row and a store record; the store passes its `cleared` field, which the contract names as `cleared_on`'s source |
| C6 | `PMOSnapshot.board_as_authored`, which drift reads | `parse_board(board_text)`; empty text gave 96 `orphaned` | with no file on disk (`board_on_disk`, set by `load_snapshot`) → `board`, the store's rows |
| C7 | `bin/perry-task § ask_register` | `ctx["board"]`'s queue; `{}` with no file | `asks.jsonl` first; the board only for a project with no ask store |
| C8 | `bin/perry-task § cmd_list`, intake rows | `ctx["board"].section_rows("Intake")` | `intake.jsonl` first, `n` = position in stored order |
| C9 | `bin/perry-task § main` | refused every write with no file ("needs the projection layout") | `declared_write_board`: an in-memory `Board.declared` built by `perry_store.declared_board` from the four validated stores, the schema and the template; `NO_STORE_COMMANDS` (`cadence-add`, `cadence-done`) refuse |
| C10 | `bin/perry-task § commit` | always `write_atomic(board.path, …)` | skipped for a declared board; `board_rendered` is `None` |
| C11 | `bin/perry-task`, the success line | `+ BOARD.md` or a "not re-rendered" warning | names no board when `board_rendered is None` |
| C12 | `bin/perry_store.py § load_board_stores`, `BOARD_STORES` | inline in `perry-tasks § cmd_board` | moved here, so the board a write mutates and the board a reader prints load the same records; `cmd_board` calls it |
| C13 | `bin/perry-lint § check_{risk,intake,ask}_store_drift` | the board-absent early return left `records: 0`, so the summary read "risks store: 0 valid record(s)" of a store holding 4 | `records` set from the store's validator before the return |

### 1.2 Sites left, each with its reason

| # | site | why it stays |
|---|---|---|
| L1 | `bin/perry-state § build`, `board.lines` | describes the file (§ 2.1) |
| L2 | `parse_board`, `last_updated_header` → `perry-state board.last_updated` | the file's own `> Last updated:` line (§ 2.1) |
| L3 | `parsers § _resolve_project_name` → `project.name` | the file's H1 is the only source; **no store holds a project name** (§ 2.1, § 6 R2) |
| L4 | `perry-task § cmd_list`, `conformance.missing_projection` | its documented meaning is the file's path |
| L5 | `parse_board`, `## Cadence` → `perry-state cadence` | no store exists; empty without the file. This project has 0 cadence rows, so the payloads are equal (§ 6 R1) |
| L6 | `perry-task § _cmd_list_from_board`, intake rows | the board-to-record derivation `store_records` runs mid-write; its intake output is discarded (`sections: False`) |
| L7 | every `ctx["board"]` mutation inside a write (`ensure_section`, `section_rows`, `append_section_row`, `mint_*_id`, …) | operates on whichever board `main` built, file or declared; no per-command change was needed |
| L8 | `perry-lint § check_store_drift` and the three register drift checks | they compare the file with the store; with no file they say `*-drift-uncheckable`, which is true. 3b decides what they become |
| L9 | `perry-lint:1571` (done-needs-evidence), `:1715` (closure judgement), `:2744` (`check_reviews`), `:2129` (id lookup) | read the file and **return quietly** when it is absent. Output is identical in both states on this project, but in general these checks go silent without the file (§ 6 R5) |
| L10 | detection disjuncts: `perry-lint:4906`, `:5882`; `perry-state:1822`, `:2595`; `perry-explain:663`; `bin/lib:540`; `parsers:579`; `perry-diagnose:1482`, `:2612` | D2 made `configured()` sufficient; the disjunct goes dead in 3b |
| L11 | `perry-diagnose § open_user_asks` (`:486`), intake count (`:2047`) | not a listed surface; reads the queue and intake out of the file (§ 6 R3) |
| L12 | `perry-goals list`, `perry-decide list` | measured equal in both states with no change (§ 2) |
| L13 | `perry-tasks render` / `diff` / `verify` / `*-render` | the projection machinery; 3b |
| L14 | `perry-okr`, `perry-knowledge`, `perry_md_store.py`, `bin/lib` (other mentions) | prose and lock documentation only |

### 1.3 The sites that surprised me

1. **`ask_register` (C7), a third ask read path, and the one the floor did not
   name.** With no file it returned `{}`. On this project eight answered asks
   became `kind: "unknown"` edges at exit 0, their rows lost `startable` and
   gained a `blocked_by`, and `depends_on_unknown` went from 0 to 8. That is
   the task graph telling a reader that finished work is still blocked.
2. **Writes needed no per-command change.** Every write already derives its
   records from the board it mutates in memory. Seeding that board from the
   declared render was sufficient for 24 of 27. The size warning in the
   spec's 250 mentions did not materialise as edits.
3. **Cadence has no store (L5).** That makes two declared writes impossible
   without the file, which is the stop.
4. **`project.name` comes from the board's H1 (L3).** Without the file it
   silently becomes the state-root directory name (`perry`).
5. **perry-lint's summary line was false (C13):** "0 valid record(s)" of
   stores holding 4 and 33.

## 2. The payload-diff table

**Method.** `git archive fbc8be5d` into two scratch copies. `perry/BOARD.md`
was removed from one. Each command ran as the copy's own `bin/` tool with
`PERRY_HOME` set to the copy and `HOME` set to an empty directory. JSON
payloads were compared key path by key path, with each copy's root path
normalised to `<ROOT>`. The same was done on `git archive b7c89276` (base).

### 2.1 Present against deleted, at `fbc8be5d`

| payload | exit (present/deleted) | key paths that differ | verdict |
|---|---|---|---|
| `perry-task list --json` | 0 / 0 | `conformance.missing_projection`: `""` → `"<ROOT>/perry/BOARD.md"` | **file exception**: the key's documented meaning is the file's path |
| `perry-task list --all --limit 0 --json` | 0 / 0 | the same one key | file exception |
| `perry-task asks --json` | 0 / 0 | none | equal |
| `perry-task asks --all --json` | 0 / 0 | none | equal |
| `perry-task events --json` | 0 / 0 | none | equal |
| `perry-state --json` | 0 / 0 | `board.lines` 188 → 0 | **file exception**: the file's line count |
| | | `board.last_updated` `"2026-09-14"` → `""` | **file exception**: the file's `> Last updated:` header |
| | | `project.name` `"Perry"` → `"perry"` | **file exception, and a gap.** The H1 of the file is the only declared source; with none, the fallback is the state root's directory name. No store holds a project name (§ 6 R2) |
| | | `generated_at` | clock |
| `perry-goals list --json` | 0 / 0 | none | equal |
| `perry-decide list --json` | 0 / 0 | none | equal |
| `perry-tasks board` | 0 / 0 | 155,964 B both, sha256 `d092f7ab105500f3…` | equal |

Values the fix restored, with the file deleted, base against final:

| value | base `b7c89276`, deleted | final `fbc8be5d`, deleted | final, present |
|---|---|---|---|
| `asks --all` `count` / `answered` | 0 / 0 | 33 / 33 | 33 / 33 |
| `list` `risks.open` / `cleared` / `source` | 0 / 0 / `none` | 2 / 2 / `table` | 2 / 2 / `table` |
| `list` `drift.drift` / `len(orphaned)` | 96 / 96 | 0 / 0 | 0 / 0 |
| `list` `conformance.depends_on_unknown` | 8 rows | 0 | 0 |
| `list` `tasks[]` with an answered-ask edge as `unknown` | 2 (default), 8 (`--all`) | 0 | 0 |
| `perry-state` `risks.count` / `source` / `cleared_items` | 0 / `none` / 0 | 2 / `table` / 2 | 2 / `table` / 2 |
| `perry-state` `board.drift.drift` | 96 | 0 | 0 |
| `perry-lint --json` `ask_store_drift.records` / `risk_store_drift.records` | 0 / 0 | 33 / 4 | 33 / 4 |

### 2.2 Present state, base against final: what changed because it now comes from a store

| payload | key path | base | final | why, and whether it is allowed |
|---|---|---|---|---|
| `asks --all --json` | `asks[0].idle` (USER-001), `asks[1].idle` (USER-002) | `"—"` | `""` | **Judgement.** The store holds no `Idle` field on purpose (`perry_store.py § ASK_STORED`: "an age is derived at read time"), so a store-read ask has no cell to report. `idle_days` is `null` in both, because `"—"` carries no digits. The contract row says "the `Idle` cell as written (`"9d"`, `"—"`)". Reading the cell back would put a `BOARD.md` read into the ask path, which is mutation M1's shape. I judged `"—"` and `""` to be two spellings of "nothing written" and made the change. **If the reviewer reads the row as promising the cell, this is a stop, and the fix is a contract clarification, not a version bump.** |
| `list` / `list --all` | `conformance.in_progress_with_no_live_run[0].idle_hours` and `.means` | 68.7 | 69.1 | clock; `means` is equal with the numbers masked |
| `perry-state` | `generated_at` | — | — | clock |

**Nothing else moved.** `lint`, `lint --json`, `goals`, `decide`, `events`,
`asks` and `perry-tasks board` are byte- or key-equal to base with the file
present.

The dispatch expected some changes: "`risks` may count the store's 4 records
rather than the table's 2". **It does not.** `risks.open` counts OPEN risks.
The store holds 4 records, 2 open and 2 cleared, exactly as the table does, so
`open` is 2 in both.

### 2.3 `perry-lint --root <project>` on the board-less copy (item 3)

| | present | deleted |
|---|---|---|
| exit | 0 | 1 |
| errors | 0 | **1**: `✗ BOARD.md [missing-file] required state file not found` (3b's) |
| warnings | 37 | 41 |

The four added warnings, each true:
- `perry/BOARD.md [store-drift-uncheckable]`: the store could not be derived
  from the current files (`Refused: no BOARD.md at …`), so drift is unknown
  here rather than absent.
- `perry/risks.jsonl`, `perry/intake.jsonl` and `perry/asks.jsonl`, each
  `[*-store-drift-uncheckable]`: the store exists and there is no `BOARD.md`
  to project it onto, so drift is unknown here rather than absent.

The summary lines read "tasks store: 434 valid record(s)", "risks store: 4",
"intake store: 0" and "ask store: 33", each followed by "comparison incomplete —
drift is unchecked, not clean". At base the risks and ask lines read **0**
(C13). No present-state warning disappeared: the text diff is additions only.

## 3. The write matrix

**Method.** `scratchpad/matrix.py`, with the tools from the `fbc8be5d` archive.
The project is a copy of this repository's state: `.perry/`, and `perry/` minus
`evidence/`, which is symlinked from the base archive. For each subcommand:
- two fresh copies are made, and `BOARD.md` is removed from one;
- the case's prerequisites run in the same state;
- then the command runs.

Compared across the two states:
- every store file after the write (`tasks`, `asks`, `risks`, `intake`,
  `linkage`, `okr`);
- the events it appended;
- the journal text it appended.

Timestamps and the copy's root path are normalised. The subject is TASK-190
(open, `not_started`, P1, main, no dependencies) unless noted.

### 3.1 Results at `fbc8be5d`

"equal" means stores, events and journal are all equal across the two states.

| subcommand | prerequisite (both states) | exit present / deleted | stores written | equal? | file re-rendered when present |
|---|---|---|---|---|---|
| `add` | — | 0 / 0 | tasks, linkage | equal | yes |
| `start` | — | 0 / 0 | tasks | equal | yes |
| `track` | — | 0 / 0 | tasks | equal | yes |
| `stage` | `track --track intake --stage new` | 0 / 0 | tasks | equal | yes |
| `ask` | — | 0 / 0 | asks | equal | yes |
| `answer` | `ask` | 0 / 0 | asks | equal | yes |
| `next` | — | 0 / 0 | tasks | equal | yes |
| `cadence-add` | — | 0 / **1** | none | events and journal differ: present wrote them, deleted refused | yes |
| `cadence-done` | `cadence-add` (refused when deleted) | 0 / **1** | none | events and journal differ | yes |
| `risk-add` | — | 0 / 0 | risks | equal | yes |
| `risk-clear` | — (RX-003) | 0 / 0 | risks | equal | yes |
| `risk-migrate` | — | 1 / 1 | none | equal: the same refusal, "already a table (4 row(s))" | — |
| `done` | `start` | 0 / 0 | tasks | equal | yes |
| `drop` | — | 0 / 0 | tasks | equal | yes |
| `purge` | `add --prefix ZZPROBE`, `drop ZZPROBE-001` | 0 / 0 | tasks | equal | no: a terminal record has no line |
| `intake` | — | 0 / 0 | intake | equal | yes |
| `route` | `intake` | 0 / 0 | tasks, intake | equal | yes |
| `resolve-intake` | `intake` | 0 / 0 | intake | equal | yes |
| `retitle` | — | 0 / 0 | tasks | equal | yes |
| `summary` | — | 0 / 0 | tasks | equal | no: no board column |
| `rung` | — | 0 / 0 | tasks | equal | yes |
| `evidence` | — | 0 / 0 | tasks | equal | yes |
| `prioritize` | — | 0 / 0 | tasks | equal | yes |
| `intake-sweep` | `intake`, `resolve-intake` | 0 / 0 | intake | equal | yes |
| `status` | — | 0 / 0 | tasks | equal | yes |
| `depends` | — | 0 / 0 | tasks | equal | yes |
| `design-link` | — | 0 / 0 | tasks | equal | no: no board column |

- **No run in the deleted state created a `BOARD.md`.**
- **At base `b7c89276`, the same matrix:** every one of the 27 exits 1 in the
  deleted state ("no BOARD.md at … this command needs the projection layout to
  render its write"). Its present-state exits are the ones in the table above.

### 3.2 The stop: `cadence-add` and `cadence-done`

`BOARD.md § Cadence` is the only record of a cadence row. No `cadence.jsonl`
exists and `perry_store` has no cadence register. Against a declared board,
`cadence-add` would append the row to memory, write the journal line and the
event, and exit 0 with the row gone.

So with no file both refuse, before anything is staged:

> no BOARD.md at …, and `## Cadence` has no store: `cadence-add` writes its row
> into the board file and nowhere else, so with no file the row would be lost
> at exit 0. Nothing was written.

With the file present, both run exactly as at base. Making them succeed
without the file needs a cadence store: a new `claims` entry in
`schema/state-schema.json` and a register in `perry_store`. That is outside 3a
and outside the consent the amendment records.

## 4. Tests and the mutation table

### 4.1 `tests/test_board_less_reads_and_writes.py`: 23 tests, 4.76 s

**Where expectations come from.** Two sources only:
- the store records the module writes (`TASKS`, `ASKS`, `RISKS`, `INTAKE`), or
  this checkout's stores read as JSONL;
- the values a command was given.

No test reads a `BOARD.md` for an expectation. The file appears in two roles
only:
- absent;
- `FORGED_BOARD`, whose three registers carry rows no store holds (`USER-777`,
  `RX-777`, `forged request`) and none of the stored ones.

| class | tests |
|---|---|
| `RegistersFromTheStores` (mixin: 5 tests × 2 cases) | `test_asks_all_is_every_stored_ask`, `test_asks_default_is_the_open_stored_asks`, `test_list_carries_the_stored_risks_asks_and_intake`, `test_an_answered_stored_ask_satisfies_its_edge`, `test_perry_state_carries_the_stored_registers` |
| `TestTheRegistersWithNoBoard` | the 5 above, plus `test_the_fixture_carries_every_shape` (anti-vacuity) and `test_drift_names_no_stored_open_row`. Drift is asserted only here: with a file on disk it is documented to be about that file |
| `TestTheRegistersWithAForgedBoard` | the 5 above, plus `test_no_forged_row_reaches_a_payload`, which first asserts the forged rows are in the file |
| `TestThisProjectsStoresWithNoBoard` | `test_every_stored_ask_is_listed`, `test_every_open_stored_risk_is_listed`, `test_no_stored_open_row_is_drift`, `test_every_edge_to_a_stored_ask_resolves_as_an_ask`, each with a floor of ≥ 1 |
| `TestEveryWriteLandsWithNoBoard` | `test_the_write_table_covers_every_declared_write` (against `--describe`), `test_each_write_lands_its_record_event_and_journal_line` (24 subTests), `test_a_write_is_the_same_with_and_without_the_file` (24 subTests; the present file is `perry-tasks board`'s render and must be re-rendered), `test_a_cadence_write_refuses_and_writes_nothing` |
| `TestLintOnABoardlessProject` | `test_the_errors_are_the_present_errors_plus_the_missing_file`, `test_the_store_counts_are_the_stores_with_no_file` |

`tests/durations.json` gains an entry: 4.76 s, source `2026-09-14-task237-d3a`.
It was timed alone three times with `python3 -m unittest` at `fbc8be5d`
(4.82 / 4.03 / 4.76 s), with load1 8.35.

### 4.2 Mutations

**How they ran.** `scratchpad/mutate.py`, on a `git archive` copy of
`fbc8be5d`, never on the worktree. For each mutation:
- the anchor was asserted to occur exactly once, and all 19 did;
- every `__pycache__` in the copy was removed;
- the module ran in a subprocess, with outcomes collected by test id from a
  `unittest.TestResult` (subTest failures counted against their test);
- the file was restored from `git show fbc8be5d:<path>` and compared equal.

Control runs before and after: 23/23 ok. Every restore compared **equal**.

| # | mutation (file) | red: named tests | result |
|---|---|---|---|
| M1 | **ask read path**: `load_snapshot` passes `asks=None`, so the board's queue is parsed (`viewer/parsers.py`) | NoBoard and Forged `.test_asks_all_is_every_stored_ask`, `.test_asks_default_is_the_open_stored_asks`, `.test_list_carries_the_stored_risks_asks_and_intake`; NoBoard `.test_perry_state_carries_the_stored_registers`; Forged `.test_no_forged_row_reaches_a_payload`; Live `.test_every_stored_ask_is_listed` | RED (9) |
| M2 | **risk read path**: the `risks.jsonl` branch disabled, so the board's table is parsed (`viewer/parsers.py`) | NoBoard and Forged `.test_list_carries_…`, `.test_perry_state_carries_…`; Forged `.test_no_forged_row_reaches_a_payload`; Live `.test_every_open_stored_risk_is_listed` | RED (6) |
| M3a | **intake read path (state)**: `load_snapshot` passes `intake=None` (`viewer/parsers.py`) | NoBoard and Forged `.test_perry_state_carries_the_stored_registers` | RED (2) |
| M3b | **intake read path (list)**: `intake_records = None`, so `list` reads the board's section (`bin/perry-task`) | NoBoard and Forged `.test_list_carries_…`; Forged `.test_no_forged_row_reaches_a_payload` | RED (3) |
| M4 | **ask read path (graph)**: `ask_register` ignores the ask store (`bin/perry-task`) | NoBoard and Forged `.test_an_answered_stored_ask_satisfies_its_edge`; Live `.test_every_edge_to_a_stored_ask_resolves_as_an_ask` | RED (3) |
| M5 | **every write refuses again without the file** (`bin/perry-task § main`) | `.test_each_write_lands_…`, `.test_a_write_is_the_same_with_and_without_the_file` | RED (2) |
| M5b | **one write path refuses**: `risk-add` raises when the board is not on disk (`bin/perry-task`) | `.test_each_write_lands_…`, `.test_a_write_is_the_same_…` | RED (2) |
| M5c | a write with no file renders one anyway (`commit`) | `.test_each_write_lands_its_record_event_and_journal_line` | RED (1) |
| M6 | drift with no file parses the empty text (`PMOSnapshot.board_as_authored`) | NoBoard `.test_drift_names_no_stored_open_row`; Live `.test_no_stored_open_row_is_drift` | RED (2) |
| M7 | cadence writes are not refused without the file (`main`) | `.test_a_cadence_write_refuses_and_writes_nothing` | RED (1) |
| M8 | lint's ask summary counts nothing with no file (`bin/perry-lint`) | `.test_the_store_counts_are_the_stores_with_no_file` | RED (1) |
| M9 | a store risk's `cleared_on` ignores the record's `cleared` (`_register_risk`) | NoBoard and Forged `.test_perry_state_carries_the_stored_registers` | RED (2) |
| M10 | with the file present, a write no longer re-renders it (`commit`) | `.test_a_write_is_the_same_with_and_without_the_file` | RED (1) |
| M11 | lint raises an extra error on a board-less project (`bin/perry-lint`) | `.test_the_errors_are_the_present_errors_plus_the_missing_file` | RED (1) |
| G1 | guard: the fixture's answered ask becomes open (test module) | NoBoard `.test_the_fixture_carries_every_shape`; NoBoard and Forged `.test_an_answered_stored_ask_satisfies_its_edge` | RED (3) |
| G2 | guard: the forged board loses its forged ask row (test module) | Forged `.test_no_forged_row_reaches_a_payload` | RED (1) |
| G3 | guard: the write table loses `next` (test module) | `.test_the_write_table_covers_every_declared_write` | RED (1) |

**Coverage:** every one of the 23 tests is reddened by at least one mutation.
**No mutation stayed green.**

**Two guards were sharpened before the battery (`fbc8be5d`), because each
would otherwise have let a mutation through.**
- The cleared fixture risk's `Status` named a date. That made M9 an equivalent
  mutation: the date parsed from the status equalled the stored `cleared`. It
  now reads `cleared — read the store`.
- The forged-board test did not assert its forged rows exist. With them
  deleted it would pass while checking nothing, which is G2. It now asserts
  them first.

## 5. The suite

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| `bash tests/run`, foreground, nothing written during it | `fbc8be5d` | 134 · 3,890 | 2 · 3 | "nothing … moved" |
| `python3 tests/parallel --ids <scratch file>` | `fbc8be5d` + the durations entry | 134 · 3,890 | 2 · 3 | — |

**The counts are the base plus this branch, exactly:** 133 + 1 modules and
3,867 + 23 tests.

**Reds, by id, identical in both runs and all pre-existing (named in the
dispatch):**
- `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`
- `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness`
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

No other red, so no module needed re-running alone.

**The harness reports two missing durations entries:**
- `test_board_less_reads_and_writes.py`, this branch's, added in this commit;
- `test_contract_page_snippets.py`, already missing at base (§ 6 R6).

## 6. Rows this work names (none minted)

- **R1: Cadence has no store.** `cadence-add` and `cadence-done` refuse without
  `BOARD.md` (§ 3.2), and `perry-state cadence` is empty without it. **3b
  cannot delete the file while a project may hold cadence rows** unless this
  is decided first: a cadence store, which is a schema `claims` edit, or an
  explicit decision to drop the register.
- **R2: `project.name` has no store.** Without the file, `perry-state` reports
  the state root's directory name (`perry`) instead of the project's (`Perry`).
  It needs a config setting, or a fallback to the project root's name, before
  3b.
- **R3: `perry-diagnose § open_user_asks` and its intake count read
  `BOARD.md`,** bypassing `asks.jsonl` and `intake.jsonl`
  (`TASK-237-result.md § 3.4` named the first). They go to 0 when the file is
  deleted.
- **R4: the `asks[].idle` contract row is board-shaped** ("the `Idle` cell as
  written"). With the store read, it is always `""` (§ 2.2). It needs a
  wording clarification, not a version change, or the reviewer's ruling that
  this is a stop.
- **R5: perry-lint checks that go quiet without the file** (§ 1.2 L9):
  done-needs-evidence, the closure judgement, `check_reviews` and the id
  lookup. Identical output on this project in both states; not audited.
- **R6: `test_contract_page_snippets.py` has no `tests/durations.json` entry**,
  already at base.

## What I did not check

- **A project with no ask, risk or intake store.** The unmigrated fallback, the
  board parse, is unchanged code and `test_parsers` is green. No board-less
  unmigrated project was built.
- **A malformed register store.** `load_register_store` returns `None` for
  unparsable JSONL, so an unmigrated-style board parse runs. With no file that
  reads empty. I did not build the case, and `cmd_asks` does not refuse for it.
  For a write, `declared_write_board` refuses on validator findings; that path
  was not exercised.
- **A stored value holding a line break with no file.** `declared_board` raises
  `UnrenderableCell`, and `declared_write_board` turns it into a refusal. Not
  exercised: the live stores hold none (D1 § 1.4 C11).
- **`--dry-run` writes with no file.** Not in the matrix.
- **The viewer (`viewer/templates/`) without the file.** It reads the same
  snapshot, but no page was rendered.
- **Localized boards and a localized template**, as in D1.
- **Concurrency.** A declared board is built inside `project_lock`, from store
  reads under the same lock. Not stress-tested.
- **perry-lint's board-reading checks in § 1.2 L9**, beyond "same output on
  this project".
- **The live project's intake register.** The store is empty, so its read path
  is exercised only by the fixture.
