# TASK-237 deliverable 1 — result: the board from the stores alone

> Scope: `TASK-237-spec.md § Amendment 2026-09-14 (2)` (USER-932 answer 3),
> deliverable 1 re-stated. Deliverable 3 (the deletion) and its two blockers
> (`perry-task` writes refuse with no `BOARD.md`; `files[id=board].required:
> true`) were not touched. `schema/state-schema.json`, `perry/BOARD.md` and the
> four stores are unchanged on this branch. `perry/BOARD.md` was not read in the
> worktree; every byte count of it below was taken inside a `git archive` copy.
>
> **Delivered.** `perry-tasks board` prints the whole board to stdout from
> the four stores, `.perry/config.jsonl`, `schema/state-schema.json §
> files[id=board]` and `work/state/BOARD_TEMPLATE.md`. On this project's stores,
> with `BOARD.md` deleted:
> - all 134 store rows are printed, each exactly once, in its declared section;
> - every header is the declared column list;
> - all 1,669 id-keyed cells equal the store value;
> - TASK-391's 2,218-byte next action is whole.
>
> The output is byte-identical with the file present, absent or garbage.

---

## 0. Base check

| | |
|---|---|
| branch | `worktree-agent-a05249fcc33ac6d37` |
| HEAD at dispatch | `583f024f` |
| `git merge-base --is-ancestor 57dae897 HEAD` | **1**: HEAD did not contain the pinned base |
| tree | clean (`git status --porcelain` printed nothing) |
| action | `git merge --ff-only 57dae897`, on this branch only; no other ref touched |
| re-asserted | `--is-ancestor` → **0**; HEAD `57dae897` ("USER-932 answered 3: TASK-237 deliverable 1 is accepted cell-whole, not byte-identical") |

## 1. Design

### 1.1 The surface: `perry-tasks board`

A new subcommand of `bin/perry-tasks`: `perry-tasks board [--root <p>]`. It
takes no flags of its own and prints to stdout. Exit codes:
- **0**: printed.
- **1**: a stored value holds a line break. Nothing is printed, and the record
  and column are named.
- **2**: a store is unreadable or fails its own `validate_*`, or the
  declaration is unreadable. Nothing is printed.

**Why `perry-tasks`, and why a new name:**

- **It is the projection tool.** `perry-tasks` already owns the four stores'
  field maps and the store-to-board direction (`render`, `risks-render`,
  `intake-render`, `asks-render`). Putting a board render anywhere else would
  add a second place that knows which column shows which field.
- **`render` keeps its output.** `render` fills today's file in place and
  refuses when the file is gone. Changing it would change an existing command,
  which the dispatch forbids. A new name is additive.
- **`perry-state` is flag-only, and every mode is a projection of one payload
  built by reading `BOARD.md` through `viewer/parsers.py`.** A board mode there
  would have to bypass that build, and would pull its payload contract into the
  change.
- **`perry-task list` is a JSON-contract command** on the tool whose writes
  refuse with no `BOARD.md`, which is deliverable 3's blocker.
- **No JSON payload was added**, so no `schema/*-contract.md` and no
  contract-parity re-record.

**Read-only by construction:**

- It dispatches in `main` **before the `--register` rewrite and before
  `project_lock`**. It takes no register and never queues behind a writer.
- The placement is also what keeps `tests/test_bin_surface §
  test_the_pairs_direction_b_cannot_see_are_all_shared_reads` at its ceiling
  of 15. After the prologue, `surface_reads` would attribute `--register` to
  `board` as a sixteenth blind pair.

### 1.2 Where the code is

| file | what |
|---|---|
| `bin/perry_store.py § declared_board(spec, template, stores)` | The renderer. **It opens no file.** It takes the schema entry, the template text and the validated records, and returns text plus a report. "It never reads `BOARD.md`" is a property of its signature. |
| `bin/perry_store.py § DECLARED_BOARD_CHOICES` | Every layout choice, in one tuple (§ 1.4). |
| `bin/perry_store.py § DECLARED_BOARD_REGISTERS` | Register → section name its `tables[]` pattern must take → the existing column → field map (`FIELD_BY_COLUMN`, `ASK_…`, `RISK_…`, `INTAKE_…`). No new field map. |
| `bin/perry-tasks § cmd_board` | The only caller. Reads the seven files, validates each store with its existing `validate_*`, prints. |
| `tests/test_board_from_declarations.py` | The guard (§ 3). |

Cells go through `perry_store.cell_text(…, escape=False)` and
`viewer/tables.py § render_row`. Headers fold through `tables.header_index`,
the one header rule. Separators come from `render_separator`. No row is built
by hand.

### 1.3 The files it reads, and only these

| file | resolved from | used for |
|---|---|---|
| `schema/state-schema.json` | `lib.SCHEMA_PATH` (PERRY_HOME) | `files[id=board]`: `headings[].match`, `tables[].under`, `columns`, `optional_columns`, `template` |
| `work/state/BOARD_TEMPLATE.md` | PERRY_HOME / the entry's `template` | title and header prose, section headings and their order, the Top risks comment |
| `.perry/config.jsonl` | the project, via `parsers.resolve_state_root` | `state_root` only |
| `<state>/tasks.jsonl`, `asks.jsonl`, `risks.jsonl`, `intake.jsonl` | the state root | rows. An absent store is empty |

`test_the_render_reads_only_the_declared_files` enforces this list in a
subprocess. `builtins.open`, `io.open` and `os.open` are logged, and an open of
any `BOARD.md` raises. The set of data files opened must be a subset of these
seven and must include the schema, the template and `tasks.jsonl`.

### 1.4 Every layout choice the declarations leave open

Quoted from `bin/perry_store.py § DECLARED_BOARD_CHOICES`, where each is made
once.

| # | choice | what `board` does |
|---|---|---|
| C1 | prose | The template's non-table lines, **as written, `{{…}}` placeholders included**. No declared source names the project, a task id or a date. `config.jsonl § last_updated` is the config's own date, not the board's (TASK-237-result.md § 2.3 L3). |
| C2 | sections | The template's `## ` headings, in its order, with its heading text. This agrees with `files[id=board].headings`. |
| C3 | columns | The `tables[]` entry's `columns`, then every `optional_columns` key, in declaration order. The template's header rows are **not** used: its task tables carry 6 of 15 declared columns, and its User Input Queue puts `Idle` before `Status`. |
| C4 | placeholder rows | The template's empty `\|  \|  \|` rows are not printed. A table is header, separator and store rows. Cadence has no store, so it has none. |
| C5 | which rows | tasks: every record whose `status` is not `done`/`dropped` (the template: "closed tasks leave this file"). asks, risks: every record (a cleared risk stays, per the template comment). intake: every record, since the intake sweep in `bin/perry-task` is what removes a discharged one. |
| C6 | which section | A task goes under the template heading whose `headings[].match` also matches its `group`. asks, risks and intake go under the one table their register's section name selects. |
| C7 | undeclared group | An open task whose `group` matches no declared task heading is printed under `## <group>` (`## (no group)` when empty). It gets the task columns, sits after the last declared task section, and is named on stderr. It is never dropped. None exist in this project's store. |
| C8 | intake section | `tables[]` declares Intake; neither `headings` nor the template places it. `## Intake` is printed only when the intake store holds a record, directly after the task sections. The same rule covers any store whose declared table has no template heading. The store is empty today, so nothing is printed. |
| C9 | row order | Ascending `order`. A record without an integer `order` follows, in store-file order. |
| C10 | a column with no stored field | `Idle` is empty. Computing today − `Asked` would make the output depend on the date. |
| C11 | cells | The stored value: list joined with `, `, null as empty, surrounding whitespace stripped. `\|` becomes `\\|` via `render_row`. A line break is **refused**: exit 1, nothing printed, record and column named. An empty list is an empty cell, not `—`. Measured on the stores at `57dae897`, which this branch does not change, over open and closed rows: 0 cells with a line break, 0 with untrimmed whitespace, 9 with a `\|`. |
| C12 | a table under an undeclared heading | Printed as the template writes it. The shipped template has none. |
| — | trailing blank lines | Collapsed. The text ends with exactly one `\n`. |

### 1.5 What did not change

**`perry-tasks render`: same bytes, both states.** Measured on the same
archived state, with the D1 tool (`a4331019`) against the base tool (`57dae897`):
- `BOARD.md` present: stdout identical, `cmp`-equal to the file, both exit 0.
- `BOARD.md` deleted: both exit 1 with identical stdout (0 bytes) and identical
  stderr (`refused — no BOARD.md at …`).

**`perry-task` is not edited**, and every write keeps today's behaviour.

**Held tables and counts that moved, one line each:**

| where | change | reason |
|---|---|---|
| `bin/perry-tasks § SURFACE.subcommands` | 17 → 18 (`board`, `flags: []`) | the new subcommand. `--describe`, `--help` and the reachability checks read it from here |
| `tests/test_bin_surface.py § OWN_OUTPUT` | + `("perry-tasks", ("board",), "# Board — {{project name}}")` | proves `board` runs its own handler. The fingerprint is the template's title, which no on-disk board carries, so a fall-through to `render` cannot pass |
| `tests/durations.json` | + `test_board_from_declarations.py` at 0.41 s, source `2026-09-14-task237-d1` (ref `a4331019`) | the new module, timed alone ×3 (0.74/0.41/0.41 s) |
| `bin/README.md` | the perry-tasks tool-table row and usage block name `board` | documentation beside the tool's other verbs. No test required it; `test_bin_surface`'s README checks run only fenced `bash` blocks, and this line sits in an indented block |

**Measured unchanged, each green at `a4331019`:**
- `perry-tasks --help` is 2,243 B after (2,129 B before), under
  `test_bin_surface`'s 3,000 B limit. `perry-tasks board --help` is 177 B,
  under the 1,200 B per-subcommand limit.
- `test_bin_surface` holds direction B's blind pairs at ≤ 15, and passes
  `test_every_declared_subcommand_is_reached` and
  `test_every_name_the_source_dispatches_is_declared`.
- `test_bin_argument_contract`, `test_board_render`, `test_one_header_rule`,
  `test_one_choke_point` and `test_row_integrity` pass.

## 2. Cell-whole, measured in both states and with garbage

**Method.** A `git archive` copy of `a4331019`, run by
`scratchpad/measure.py` (not committed).

- **Expectations** are built from the copy's own stores and schema. The script
  uses the helpers in `tests/test_board_from_declarations.py`, which never read
  a `BOARD.md`.
- **Output** is read back with `tables.split_row`.
- **`BOARD.md`** is read only inside the copy, for its byte count and for the
  `render` comparison.

| | `BOARD.md` present | `BOARD.md` deleted | `BOARD.md` = garbage bytes |
|---|---|---|---|
| `perry-tasks board` exit | 0 | 0 | 0 |
| stdout | 157,364 B, sha256 `a4196c972e98e377…` | 157,364 B, `a4196c972e98e377…` | 157,364 B, `a4196c972e98e377…` |
| stderr | empty | empty | — |
| sections printed | P0 (0 rows), P1 (66), P2 (31), Cadence (0), User Input Queue (33), Top risks (4) | same | — |
| store rows / printed rows | 134 / 134 (tasks 97 open, asks 33, risks 4, intake 0) | 134 / 134 | — |
| sections whose header ≠ the declared columns | 0 (15, 15, 15, 7, 6, 4 columns) | 0 | — |
| rows not exactly once in their declared section | 0 | 0 | — |
| id-keyed cells checked / not equal to the store value | 1,669 / 0 | 1,669 / 0 | — |
| TASK-391 | `not_started`, store 2,218 B, printed once, cell 2,218 B, **whole** | same | — |

- **absent == present:** `true`, byte for byte.
- **garbage == absent:** `true`. The garbage is the test module's `GARBAGE`:
  invalid UTF-8, a NUL, all 256 byte values, and a forged `| TASK-010 | forged
  |` row under a forged `## P1`.
- **`BOARD.md` restored** in the copy after the garbage run: `true`.
- **TASK-391's `next_action`, re-measured:** 2,218 bytes at `a4331019`, unchanged
  from 5fa66a7f. It holds no `|`.
- **Cells with a `|`:** 9 across the stores, counting open and closed rows
  together: 6 in `tasks.jsonl` and 3 in `asks.jsonl`. They reach the escape
  rule through the every-cell check and the fixture's
  `test_a_pipe_is_escaped_once`.
- **Compared with the live file:** `BOARD.md` at `a4331019` is 157,200 B and
  the board prints 157,364 B. Byte-identity is not the criterion (USER-932 answer 3).
  The difference is the layout § 1.4 declines to copy.

**Independence from the file, proven by opening rather than by output.**
`TestTheFileIsNeverRead.test_the_render_never_opens_board_md` runs the real
`bin/perry-tasks board` in a subprocess:
- The driver replaces `builtins.open`, `io.open` and `os.open`, logs every path
  and raises on any `BOARD.md`. `Path.read_text` and `read_bytes` go through
  `io.open` on 3.11.
- A garbage `BOARD.md` sits in the state root.
- The log must hold no `BOARD.md`, and the exit must be 0.

Mutation M4 below shows it reddens when the render reads one byte.

## 3. The test module and the mutation table

### 3.1 `tests/test_board_from_declarations.py`, 16 tests

**Where expectations come from.** Only the stores, read as JSONL in the test,
and `schema/state-schema.json`. Cell text is computed by the test's own
`expected_cell`, not by `perry_store.cell_text`. Column → field is the test's
own `COLUMN_FIELD`, not `perry_store.FIELD_BY_COLUMN`. So a mutation of the
renderer's rule cannot move the expectation. No test reads a `BOARD.md`.

| class | project | tests |
|---|---|---|
| `CellWhole` (mixin) | — | `test_every_declared_column_is_in_its_section`, `test_every_store_row_appears_exactly_once_in_its_declared_section`, `test_every_cell_equals_the_store_value` |
| `TestAFixtureProject` | a hand-written board-less project: a `\|` in a cell, a 2,925-byte cell holding `\|`, a two-item and an empty list, a null, a closed task, a task with no `order`, a task in group `Someday`, one ask, one risk, one intake row | the three above, plus `test_the_fixture_carries_every_shape` (anti-vacuity over the fixture data), `test_a_closed_task_is_not_printed`, `test_a_task_in_an_undeclared_group_is_printed_and_named`, `test_a_pipe_is_escaped_once`, `test_a_value_with_a_line_break_is_refused_and_nothing_printed`, `test_a_malformed_store_is_refused_and_nothing_printed` |
| `TestThisProjectsStores` | this checkout's four stores and `.perry/config.jsonl`, copied into a temp project with **no `BOARD.md`** | the three above, plus `test_the_longest_next_action_is_whole` (the longest open next action, floor 1,000 B so it cannot go vacuous; TASK-391's today) |
| `TestTheFileIsNeverRead` | the fixture | `test_the_render_is_the_same_bytes_with_no_board_and_with_garbage`, `test_the_render_never_opens_board_md`, `test_the_render_reads_only_the_declared_files` |

The live-store case does not name TASK-391, so it survives the row closing. The
floor keeps it honest. TASK-391 by name is measured in § 2.

Timed alone: 0.74 / 0.41 / 0.41 s (`python3 tests/parallel -j 1 --times`),
recorded at 0.41 s in `tests/durations.json`.

### 3.2 Mutations

**How they ran.** `scratchpad/mutate.py`, on a `git archive` copy of `a4331019`
under the scratchpad, never on the worktree. For each mutation:
1. The anchor string is asserted to occur **exactly once** before replacing.
2. Every `__pycache__` in the copy is removed before the run.
3. The module runs in-process through `unittest`, and each test's outcome is
   collected by id.
4. The file is restored from `git show a4331019:<path>`, and the restored bytes
   are asserted equal to it.

Control runs before and after: **16/16 ok** both times. Every restore compared
**equal**.

**Run twice.** First at `a4331019`, then again on a fresh archive copy of
`84bb330f`, the final code. `84bb330f` changes one sentence of
`DECLARED_BOARD_CHOICES` and adds the fold-guard drive (§ 4). **All 17 red
sets were identical between the two runs**, test for test. The table below
holds for the committed tree.

| # | mutation (file) | red — named tests | result |
|---|---|---|---|
| M1 | **drop one declared column**: the last `optional_columns` key (`perry_store.py § _declared_columns`) | `TestAFixtureProject` and `TestThisProjectsStores` `.test_every_declared_column_is_in_its_section`; both `.test_every_store_row_appears_exactly_once_in_its_declared_section` | RED (4) |
| M2 | **truncate one cell**: a cell over 2,000 B loses its last byte (`declared_board`) | both `.test_every_cell_equals_the_store_value`; `TestThisProjectsStores.test_the_longest_next_action_is_whole` | RED (3) |
| M3 | **skip one store row**: the first open task (`declared_board`) | both `.test_every_store_row_appears_exactly_once_in_its_declared_section`; both `.test_every_cell_equals_the_store_value`; `TestAFixtureProject.test_a_value_with_a_line_break_is_refused_and_nothing_printed` | RED (5) |
| M4 | **the render reads one byte of `BOARD.md`** (`perry-tasks § cmd_board`) | `TestTheFileIsNeverRead.test_the_render_never_opens_board_md`; `.test_the_render_reads_only_the_declared_files` | RED (2) |
| M5 | one byte of `BOARD.md` reaches stdout (`cmd_board`) | `TestTheFileIsNeverRead` `.test_the_render_is_the_same_bytes_with_no_board_and_with_garbage`, `.test_the_render_never_opens_board_md`, `.test_the_render_reads_only_the_declared_files` | RED (3) |
| M6 | closed tasks are printed (`declared_board`) | `TestAFixtureProject.test_a_closed_task_is_not_printed`; both `.test_every_store_row_appears_exactly_once…`; both `.test_every_cell_equals_the_store_value` | RED (5) |
| M7 | an undeclared group's tasks are dropped (`declared_board`) | `TestAFixtureProject` `.test_a_task_in_an_undeclared_group_is_printed_and_named`, `.test_every_store_row_appears_exactly_once…`, `.test_every_cell_equals_the_store_value` | RED (3) |
| M7b | an undeclared group is not named on stderr (`cmd_board`) | `TestAFixtureProject.test_a_task_in_an_undeclared_group_is_printed_and_named` | RED (1) |
| M8 | a `\|` is escaped twice (`declared_board`) | `TestAFixtureProject.test_a_pipe_is_escaped_once`; both `.test_every_cell_equals_the_store_value` | RED (3) |
| M9 | a line break is collapsed instead of refused (`declared_board`) | `TestAFixtureProject.test_a_value_with_a_line_break_is_refused_and_nothing_printed` | RED (1) |
| M9c | the refusal does not name the column (`declared_board`) | `TestAFixtureProject.test_a_value_with_a_line_break_is_refused_and_nothing_printed` | RED (1) |
| M10 | an unparsable store is read as empty (`cmd_board`) | `TestAFixtureProject.test_a_malformed_store_is_refused_and_nothing_printed` | RED (1) |
| M11 | the render reads an undeclared file, `bin/README.md` (`cmd_board`) | `TestTheFileIsNeverRead.test_the_render_reads_only_the_declared_files` | RED (1) |
| M13 | rows in reverse stored order (`_in_stored_order`) | both `.test_every_cell_equals_the_store_value` | RED (2) |
| M14 | every cell shifts one column left (`declared_board`) | both `.test_every_cell_equals_the_store_value`; both `.test_every_store_row_appears_exactly_once…`; `TestThisProjectsStores.test_the_longest_next_action_is_whole`; `TestAFixtureProject` `.test_a_task_in_an_undeclared_group_is_printed_and_named`, `.test_a_value_with_a_line_break_is_refused_and_nothing_printed` | RED (7) |
| G1 | guard: the fixture's long cell shrinks to 117 B (test module) | `TestAFixtureProject.test_the_fixture_carries_every_shape` | RED (1) |
| G2 | guard: the fixture's closed task becomes `blocked` (test module) | `TestAFixtureProject.test_the_fixture_carries_every_shape`; `.test_a_closed_task_is_not_printed` | RED (2) |

**Coverage.** Every one of the 16 tests is reddened by at least one mutation.
**No mutation stayed green.**

**Two findings from building the harness.** They affect the evidence, not the
product.

1. **The first harness parsed `unittest -v` text with a regex, and saw 15 of
   16 lines.** Its control assertion stopped the battery before the first
   mutation ran. The harness was rewritten to collect outcomes from a
   `unittest` result object by test id. A mutation run through the first
   version would have reported a missing test as neither red nor green.
2. **The live-store case cannot catch M6 or M7 by itself.** This project's
   store has no open task in an undeclared group. M6 does redden it, through the
   row count. That is why the fixture carries both shapes, and why G1/G2 guard
   that it still does.

## 4. The full suite

`bash tests/run` from the worktree root, in the foreground, with nothing
written to the tree while it ran. Pre-existing reds at 57dae897's parent, per
the dispatch: `test_contract_key_parity` ×2 and
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`, over 132 modules
and 3,847 tests.

| run | tree | modules · tests | red modules · red tests | tree guard |
|---|---|---|---|---|
| 1, `bash tests/run` | `db7c83ba` | 133 · 3,863 | 4 · 6 | nothing moved |
| 2, `bash tests/run` | `84bb330f` (final code) | 133 · 3,863 | 3 · 4 | nothing moved |
| 3, `tests/parallel --ids` | `84bb330f` | 133 · 3,863 | 2 · 3 | — |

**The counts are the baseline plus this branch, exactly:** 132 + 1 module,
3,847 + 16 tests.

**Run 1's reds, by id:**

| test | re-run alone | at `57dae897` alone | attribution |
|---|---|---|---|
| `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` | red | — | pre-existing (named in the dispatch) |
| `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` | red | — | pre-existing (named in the dispatch) |
| `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` | red | — | pre-existing (named in the dispatch) |
| `test_handed_back_root.TestEveryWriterHandBackCarriesTheRoot.test_no_pasteable_writer_is_handed_back_without_the_root` | red | green | **this branch.** A `DECLARED_BOARD_CHOICES` sentence held the backticked writer phrase `perry-task intake-sweep` with no root. Fixed in `84bb330f` by rewording the sentence, not by exempting it. `MENTIONS` stays at 5. |
| `test_handed_back_root.TestEveryWriterHandBackCarriesTheRoot.test_the_count_of_pasteable_writer_hand_backs_is_held` | red (69 ≠ 68) | green | **this branch**, same phrase. The count is back to 68; the held number was not edited. |
| `test_header_index_is_the_only_fold.TestOnlyHeaderIndexFoldsAHeaderCell.test_the_uncovered_remainder_is_the_measured_one` | red | green | **this branch.** `declared_board`'s nested `emit_table` was a new `convert` site nothing drove. Fixed in `84bb330f` by covering it, not by listing it: `parse_everything` drives `declared_board` with the board declaration's columns decorated, `emit_table` joins `WATCHED`, and `UNCOVERED` is unchanged at 8. |

**Run 2's reds, by id:**
- **`test_contract_key_parity` ×2 and `test_resume` ×1:** the three
  pre-existing reds above.
- **`test_churn.py`:** 1 of 37 red, and **not attributed to this branch.**
  - It was green in run 1, on a tree that differs from run 2 only in the two
    fixes.
  - It was green alone in the worktree at `84bb330f`, and green alone at
    `57dae897`.
  - It did not reproduce in run 3.
  - Run 2's summary named only the module, so **the failing test's id was not
    captured.**

**Run 3's reds:** only the three pre-existing ones.

**Final totals at `84bb330f`:**
- Run 2: **133 modules, 3,863 tests; 3 modules and 4 tests red.** Those are the
  three pre-existing reds plus one `test_churn` test that did not reproduce.
- Run 3: **2 modules and 3 tests red**, exactly the pre-existing set.

**The existing `perry-tasks render` and `perry-task` writes.**
`test_board_render`, `test_bin_surface`, `test_bin_argument_contract`,
`test_task_writer_core` and the rest of the writer modules are green in both
full runs. § 1.5 has the byte comparison of `render` against the base tool.

### 4.1 The guard update, mutated

`scratchpad/mutate_fold.py` ran on a `git archive` copy of `84bb330f`, under
the same rules as § 3.2: anchors unique, `__pycache__` cleared, restores
checked against `git show 84bb330f:<path>`. It ran `test_header_index_is_the_only_fold`
and `test_one_header_rule`.

`test_one_header_rule.TestAVanishedFileIsSkippedButATrackedOneIsNot.test_git_tracks_answers_both_ways`
is **red in the archive copy's control run**. It asks git whether a path is
tracked, and an archive is not a repository. It is excluded from every red list
below so it cannot pose as a catch.

Control runs: `test_header_index_is_the_only_fold` 9/9 ok, before and after;
`test_one_header_rule` 16 tests, clean apart from the environment red, before
and after. Every restore compared **equal**.

| # | mutation (file) | red — named tests | result |
|---|---|---|---|
| F1 | `"emit_table"` removed from `WATCHED` (test module) | `TestOnlyHeaderIndexFoldsAHeaderCell.test_watched_is_exactly_the_converted_readers_this_workload_folds_through` | RED (1) |
| F2 | the decorated `declared_board` drive removed from `parse_everything` (test module) | `.test_every_reader_this_module_claims_to_watch_actually_folds_one`; `.test_the_uncovered_remainder_is_the_measured_one`; `.test_watched_is_exactly_the_converted_readers_this_workload_folds_through` | RED (3) |
| F3 | product: `emit_table` folds its header by hand (`c.strip("*` ").lower()`) instead of through `header_index` (`bin/perry_store.py`) | `.test_every_reader_this_module_claims_to_watch_actually_folds_one`; `.test_watched_is_exactly_the_converted_readers_this_workload_folds_through` | RED (2) |

**No mutation stayed green.** In F3, `test_one_header_rule` stayed green,
because its check is stated over the `squash` symbol and the hand fold does not
call it. The fold module is the net that catches it here, which is the job the
added drive gives it.

## 5. Rows this work names (none minted)

No row was opened and no id minted. Two gaps are named for the PMO to judge:

1. **Deliverable 3's blockers are unchanged, as the dispatch requires.**
   - `perry-task` writes still refuse with no `BOARD.md`.
   - `files[id=board].required` is still `true`.

   `board` removes neither. It is the reading surface the deletion needs, not
   the write path.
2. **The template and the schema disagree about the User Input Queue's column
   order.** The template has `… Blocks | Idle | Status`; the schema has
   `columns: … Blocks, Status` then `optional_columns: Asked, Idle`. `board`
   follows the schema (C3).
   - The template's own header rows are dead layout for every table the schema
     declares. I did not measure what `perry-lint --templates` checks about
     order.
   - Aligning them is a template edit, not a D1 task.

## What I did not check

- **A localized project.** The shipped template is English. A Chinese board's
  headings (`例行节奏`, `用户输入队列`, `主要风险`) are matched by the schema's
  `match` patterns, but no localized template exists to print them from. A
  project whose task `group` is localized and is not `P0`/`P1`/`P2` would land
  in C7's undeclared-group section. Not measured.
- **A project with a `.perry/config.jsonl` but no `state_root`.** It resolves
  to the project root, through `parsers.resolve_state_root`. The fixture always
  declares `state_root: perry`.
- **Concurrency.** `board` takes no lock. A write landing between two store
  reads could print tasks from before it and asks from after it. Whether a
  single store can be read torn was not measured.
- **Intake rows on this project.** The live intake store is empty. The fixture
  has one row; a discharged-but-unswept row and a two-row ordering case were
  not built.
- **The readability judgement.** The spec's "subjective verification" asks
  whether the CLI render is a good enough reading surface **for a board**. A
  15-column table with 2,218-byte cells prints whole, but whole is not the same
  as readable. That judgement is the reviewer's.
- **`--help` text for `board` beyond the size limits.** The summary line was
  read, not user-tested.
- **Other tools reading the board.** `perry-state`, `perry-lint`, `perry-goals`
  and `viewer/parsers.py § parse_board` still read `BOARD.md`. That is
  deliverable 3's enumeration.
