# TASK-262 — result

> Spec: `perry/evidence/2026-09/TASK-262-spec.md`, Amendment (1) included
> Executor: claude-subagent, in an isolated worktree
> Branch: `worktree-agent-a6f859b7fd308b70c`
> Code commit: `16eba07d`. This file and the board sample are in the commit after it.
> Rung reached: V3 (items 1–4, 6). **Item 5, the reading, has not been done. It is the PMO's, after merge.**

## 0. Base check

- The worktree arrived at `583f024f`. `git merge-base --is-ancestor 7f97d337 HEAD` exited 1.
- The tree was clean, so the branch was fast-forwarded: `git merge --ff-only 7f97d337`.
- Re-asserted: exit 0, HEAD `7f97d337`. No other branch was checked out, reset or pushed.

## 1. What changed

Only `perry-tasks board` prints any of this. `perry_store.declared_board` takes a
new optional `sources` argument, and `cmd_board` is its only caller that passes
it. The in-memory board a `perry-task` write mutates (`declared_write_board`)
passes nothing and carries no marker. No file-writing path was touched, and no
`BOARD.md` is written.

### 1.1 The mark and the legend (deliverables 2 and 3)

- The mark is `†`, and it has one meaning: not stored. No record holds it; the
  render supplies it.
- The legend is one line, directly under the title:

  ```
  > † = not stored: no record holds it; the render supplies it. An unmarked cell is one field of one record, printed as written, and an empty one is an empty field.
  ```

- The title wears the mark, because the project name is the directory's name:
  `# Board — Perry †`. The mark is added only when the template's
  `{{project name}}` slot was filled.
- A column header wears the mark (`Idle †`) exactly when its register's
  `*FIELD_BY_COLUMN` map gives the folded header no field. Today that is one
  column, `User Input Queue § Idle`. The legend names no column, so there is no
  hand list anywhere.

### 1.2 The section line (deliverable 1)

One `> ` line, directly under every `## ` heading, including an undeclared
group (`## Someday`) and the `## Intake` tail. On this repository:

```
## P0 (must finish this period)
> Stored in `tasks.jsonl` under the state root; written by `perry-task` add, start, stage, track, ask, answer, next, cadence-add, cadence-done, risk-add, risk-clear, risk-migrate, done, drop, purge, intake, route, resolve-intake, retitle, summary, rung, evidence, prioritize, intake-sweep, status, depends, design-link
## Cadence (recurring; doesn't consume P0 slots)
> Stored in `cadence.jsonl` under the state root; no `perry-task` subcommand declares a write to it
## User Input Queue
> Stored in `asks.jsonl` under the state root; no `perry-task` subcommand declares a write to it
## Top risks (one-line; full list in `PROJECT_STATE.md`)
> Stored in `risks.jsonl` under the state root; no `perry-task` subcommand declares a write to it
```

`## P1` and `## P2` print the same line as `## P0`. The fixture's `## Intake`
prints `` > Stored in `intake.jsonl` under the state root; no `perry-task` subcommand declares a write to it ``.

**The last three lines are true of the declaration and false of the tool.**
That is finding F1 (§ 5), and it is the first thing a reader of this result
needs to know.

Two more wordings exist and are tested, though neither project prints them:

- a table under a heading no register owns:
  `` > † No store: this section's table is the template's, not a register's ``,
  with every header cell marked;
- a register whose store `§ claims` does not declare: `> † No store: ...`.

## 2. The derivation

| printed thing | derived from | how |
|---|---|---|
| the store path | `schema/state-schema.json § claims` | The file name comes from `perry_store.BOARD_STORES`, the function the render reads the register's records through (`where(Path("")).name`). The claim is looked up by that `path` with `kind: file`. Its `anchor` reads as "under the state root" or "at the project root". |
| the writers | `bin/perry-task § SURFACE` | Every subcommand whose `writes` list contains the claim's `path`, in declaration order. `perry-tasks § writer_surface` reads the assignment with `ast.literal_eval` and never executes it. Loading the module would cost ~0.37 s and open files at import; the literal costs ~0.03 s. `perry-tasks` imports (`--from-board`, `*-write`) are never consulted, so they are never named. |
| "no subcommand declares a write" | the same list | Printed when the list is empty. The nearest writer is never named (must-not 4). |
| the column mark | `FIELD_BY_COLUMN`, `ASK_`, `RISK_`, `INTAKE_`, `CADENCE_FIELD_BY_COLUMN` | `emit_table` already computed `fields = [fmap.get(k) for k in header_index(cols)]` to fill the cells. The mark is `f is None` on that same list, so the column that prints empty and the column that is marked cannot disagree. |

No prose is parsed anywhere. Every decision is a dict lookup, a list membership
test or a regex over the schema's own `under` and `match` patterns. The choice
is recorded as `DECLARED_BOARD_CHOICES` "sources".

## 3. Verification

### 3.1 Enumeration (the Bound, recounted)

| project | sections printed | columns printed | marked columns |
|---|---|---|---|
| this repository, at `16eba07d` | 6: `P0`, `P1`, `P2`, `Cadence …`, `User Input Queue`, `Top risks …` | 62 = 15 × 3 + 7 + 6 + 4 | `User Input Queue § Idle` |
| the `test_board_from_declarations` fixture | 8: the six, plus `Someday` (undeclared group) and `Intake` | 80 = 15 × 4 + 3 + 7 + 6 + 4 | `User Input Queue § Idle` |

- This repository prints no Intake section. The fixture does, as Amendment (1)
  said it might.
- Last element: `Top risks § Status`, which is stored and unmarked.

### 3.2 Items 1 and 2: the section lines and the column marks

- The expectations are in `tests/board_sources.py`:
  - the store and anchor come from `§ claims`;
  - the writers come from a separate `ast` reader of `bin/perry-task § SURFACE`;
  - the section's register comes from `files[id=board].tables[].under`;
  - whether a column is stored comes from the five maps;
  - the line's wording is written there independently, so a renderer that
    rewords, drops or mis-names a line fails.
- The guard is `tests/test_board_names_its_sources.py`, 13 tests, run over the
  fixture and over this repository in place (`board` is read-only).
- Result: 6/6 and 62/62 on this repository, 8/8 and 80/80 on the fixture.

### 3.3 Item 3: nothing else moved

**The strip rule**, which is also the docstring of `tests/board_sources.py`.
Applied line by line:

1. Delete every line that starts with `> `. The board at `7f97d337` prints
   none; choice "prose" drops the template's `>` block. Measured: 0 such lines
   on both projects.
2. On a `# ` line, delete one trailing ` †`.
3. On a table header line (a `|` line whose next line is a separator), replace
   every ` † |` with ` |`.

Nothing else is touched.

**The run.**

- `7f97d337` was exported with `git archive` into scratch, and its
  `bin/perry-tasks board` was run against the same stores as the branch's.
- The two projects:
  - this repository's stores, in the worktree;
  - the d1 fixture, copied to a fixed path so both runs print the same project
    name.
- For each project, the branch's output was stripped and compared with `cmp`.

| project | lines added by the branch | `cmp base stripped` |
|---|---|---|
| this repository | 7 (legend + 6 section lines) | equal (exit 0) |
| fixture | 9 (legend + 8 section lines) | equal (exit 0) |

`test_nothing_else_moved` keeps this true in the suite, with one limit:

- **What it asserts:** strip(output) equals `declared_board` with no `sources`,
  byte for byte, and exactly `sections + 1` lines were removed.
- **What it cannot see:** its reference is the same renderer, so a cell changed
  in both paths passes it. That change is caught by
  `test_board_from_declarations § test_every_cell_equals_the_store_value`,
  whose expectation comes from the stores (M5a below).

### 3.4 Item 4: mutations

**Method.**

- Each mutation starts from a fresh extraction of `git archive 16eba07d`.
- The edit is anchored so it occurs exactly once (asserted), and `__pycache__`
  is cleared.
- The named modules are run alone with `python3 -m unittest discover`.
- The edit is then restored and the file compared byte for byte with
  `git show 16eba07d:<path>`. The cache is cleared again and the modules re-run.
- The harness is a scratch script and is not committed.

In the "restored" column, "== git show" means the restored file matched
`git show 16eba07d:<path>`, and "green" means every module re-ran without a
failure.

| # | mutation | file | red, named test (both project cases unless noted) | still green, and why that is right | restored |
|---|---|---|---|---|---|
| M1 | drop one section's line (P2) | `perry_store.py` | `test_every_section_names_its_store_and_its_writers`, `test_nothing_else_moved` (4 failures) | — | == git show, green |
| M2a | wrong writer: `tasks.jsonl`'s writers on every store | `perry_store.py` | `test_every_section_names_its_store_and_its_writers`; `TestTheDeclarationsTheLinesComeFrom.test_the_writers_are_the_surface_s_not_the_nearest` (9) | — | == git show, green |
| M2b | wrong writer: one writer too few | `perry_store.py` | same two (9) | — | == git show, green |
| M3 | mark a stored column (`Title`) | `perry_store.py` | `test_every_column_is_marked_exactly_when_it_has_no_stored_field` (7) | `test_board_from_declarations`: its `sections()` drops a header mark by design, and marks are this module's question | == git show, green |
| M4 | unmark the derived column (`Idle`) | `perry_store.py` | `test_every_column_is_marked_exactly_when_it_has_no_stored_field` (4) | — | == git show, green |
| M5a | change one cell (`Owner` gains `.`), in both paths | `perry_store.py` | `test_board_from_declarations § test_every_cell_equals_the_store_value` (97) | `test_board_names_its_sources`: its reference is the same renderer (§ 3.3) | == git show, green |
| M5b | change one cell only where sources are printed | `perry_store.py` | `test_nothing_else_moved`; `test_every_cell_equals_the_store_value` (2 + 97) | — | == git show, green |
| M6 | title's project name unmarked | `perry_store.py` | `test_the_title_is_marked_and_the_legend_names_the_mark`; `test_cadence_store § test_the_title_is_the_project_directory_name` | — | == git show, green |
| M7 | legend dropped | `perry_store.py` | `test_the_title_is_marked_and_the_legend_names_the_mark`, `test_nothing_else_moved` (4) | `test_cadence_store`: a missing line is not leaked prose | == git show, green |
| M8 | SURFACE reader returns no subcommands | `perry-tasks` | `test_every_section_names_its_store_and_its_writers` (7) | — | == git show, green |
| M9 | a table no register owns printed unmarked | `perry_store.py` | `TestATableNoRegisterOwns.test_its_section_says_no_store_and_every_column_is_marked` | — | == git show, green |
| M10 | claim looked up by the wrong file name | `perry_store.py` | `test_every_section_names_its_store_and_its_writers`, `test_a_store_no_subcommand_declares_says_so_and_names_nobody`, `test_the_writers_are_the_surface_s_not_the_nearest` (10) | — | == git show, green |

- Every mutation reddened at least one named test.
- The green modules in the fifth column were checked and are expected, for the
  reason given. None is a finding.
- M9 was added after I saw that neither project prints a table under an
  unowned heading. `TestATableNoRegisterOwns` was written first, so that branch
  is not held by nothing.

### 3.5 Item 5: the reading, NOT DONE

I cannot ask the user, so this belongs to the PMO, after merge.

- **Sample to show:** `perry/evidence/2026-09/TASK-262-board-sample.md`, 167
  lines.
- **How it was made:** `bin/perry-tasks board` from a `git archive 16eba07d`
  copy extracted into a scratch directory named `Perry`, over the stores that
  commit carries. The live stores were not used, so the sample will not change
  before the reading.
- Show the file and nothing else, then ask:
  1. "Where would you change this row's next action?" Point at one `## P1` row.
  2. "Why is this cell empty?" Point at one `Idle †` cell in `## User Input
     Queue`. Pointing at an empty stored cell as well, such as `Asked` on
     `USER-001`, tests the legend's second sentence.
  3. "Is the title stored anywhere?"

**Answers (verbatim):** _empty. Nobody has been asked. The row closes only
after the PMO records the reading here._

Before showing it, read F1: the Cadence, User Input Queue and Top risks lines
say no writer is declared. A reader asked about an ask or a risk will be misled
until F1 is fixed.

## 4. The KR measurement proposal (`P003-O2-KR3`)

I wrote no `okr.jsonl` or `linkage.jsonl`. This proposal is for the goals lane.

| metric | definition | current, this repository, `16eba07d` | target |
|---|---|---|---|
| sections that name their store and writer | `## ` sections whose next line equals the line built from `§ claims` and `perry-task § SURFACE`, over `## ` sections printed | 6/6 (100%) | 100% |
| columns classified | printed columns whose `†` agrees with the register's `*FIELD_BY_COLUMN` map, over printed columns | 62/62 (100%) | 100% |

The command, which prints both numbers:

```
python3 tests/board_sources.py --root <project>
sections naming their store and writer: 6/6 (100%)
columns classified: 62/62 (100%)
```

It exits 0 when both are 100%, 1 when either is short, and 2 when no board
printed.

**Caveat for whoever writes the KR record.** Both numbers measure agreement
with the declarations. With F1 open they read 100% while three section lines
mislead a reader. The KR's real property is still the reading in § 3.5, and the
record should not treat 100% here as the KR met.

## 5. Findings

**F1 — `bin/perry-task § SURFACE` `writes` does not say which store a
subcommand writes, and it disagrees with a second declaration in the same
file.**

- All 27 mutating subcommands declare the identical list
  `["tasks.jsonl", "BOARD.md", "journal/", ".perry/events.jsonl"]`. None
  declares `asks.jsonl`, `risks.jsonl`, `intake.jsonl` or `cadence.jsonl`.
- `bin/perry-task § REGISTER_EVENTS` declares which register store each
  subcommand makes current:
  - `risk-add`, `risk-clear`, `risk-migrate` → risks;
  - `intake`, `resolve-intake`, `intake-sweep`, `route`, `add` → intake;
  - `ask`, `answer` → asks;
  - `cadence-add`, `cadence-done` → cadence.
- The consequences, derived as the spec requires:
  - the Cadence, User Input Queue and Top risks lines say no writer is
    declared;
  - every task section names all 27 subcommands, including `ask`, `risk-add`
    and `cadence-add`.
- `writes` also still lists `BOARD.md`, which no command writes since TASK-237
  3c.
- Not fixed here:
  - `bin/perry-task` is outside this row's scope;
  - `lib.refuse_write_unless_installed` gates writes on this very list;
  - `tests/test_bin_surface.py:1182` asserts `BOARD.md` is in it.
- A fix is one declaration made to agree with the other. Once it lands, the
  board lines correct themselves, because they are derived.
- **No row opened.**

**F2 — the task-section line is long.** 27 names on one line, printed three
times. It is what the declaration says, and F1's fix would shorten it only if
`tasks.jsonl` were declared by fewer subcommands. Whether the line should
instead name the writer family is a wording question for after the reading.

**F3 — `bin/README.md`'s `perry-tasks` row lists the files `board` reads** and
does not include `bin/perry-task § SURFACE`. The comment above `cmd_board` in
`bin/perry-tasks` was updated (seven files → eight). The README is outside this
row's scope.

**F4 — the render is slower.**

- Each `board` now also parses `bin/perry-task` with `ast`, about 0.03 s.
- `test_board_from_declarations`, timed alone three times back to back at
  load1 11.08:
  - base `7f97d337`: 0.53 / 0.86 / 0.60 s, median 0.60;
  - this branch: 0.91 / 0.91 / 0.89 s, median 0.91.
- Re-recorded in `tests/durations.json` (§ 6).

**F5 — found in passing, not caused here:** `tests/parallel` reports
`test_a_write_refuses_where_nothing_is_installed.py` and
`test_contract_page_snippets.py` as absent from `tests/durations.json` at the
base.

## 6. Files

| file | change |
|---|---|
| `bin/perry_store.py` | `NOT_STORED_MARK`, `BOARD_LEGEND`, `board_store_claim`, `surface_writers`, `section_source_line`; `declared_board(..., sources=None)`; choice "sources" |
| `bin/perry-tasks` | `writer_surface()`; `cmd_board` passes `sources`; the read-list comment |
| `tests/board_sources.py` | new: the expectations, the strip rule, the KR command |
| `tests/test_board_names_its_sources.py` | new: 13 tests |
| `tests/test_board_from_declarations.py` | `sections()` drops a header's ` †`; `bin/perry-task` added to the declared reads |
| `tests/test_cadence_store.py` | the title test expects ` †`; the prose test admits a `> ` line only as the legend at line 2 or directly under a `## ` heading, so template prose still fails it |
| `tests/durations.json` | `test_board_names_its_sources.py` 0.64 s (0.79 / 0.64 / 0.57); `test_board_from_declarations.py` 0.41 → 0.91 s; source `2026-09-14-task262`, ref `7f97d337` |
| `perry/evidence/2026-09/TASK-262-board-sample.md` | the Verification 5 sample |

Not touched: `schema/`, `okr.jsonl`, `linkage.jsonl`, the task, ask and risk
stores, `.perry/events.jsonl`, the journal. No `perry-task`, `perry-tasks`,
`perry-okr` or `perry-goals` write was run against this checkout.

## 7. The suite

See § 7.1, added after the run on the commit that carries this file.
