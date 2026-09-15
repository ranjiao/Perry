# TASK-262 — round 2 result: the writer declaration

> Spec: `perry/evidence/2026-09/TASK-262-spec.md § Amendment (2)` (user decision)
> Round 1: `perry/evidence/2026-09/TASK-262-result.md` (finding F1)
> Executor: claude-subagent, in an isolated worktree
> Branch: `worktree-agent-ad79f277983e523ca`
> Code commit: `83fed4f3`. `f3b8e5c1` corrects one docstring line in the new
> test. This file, the board sample, the round-1 pointer and
> `tests/durations.json` are in `4a27b2c3`. The commit after it relabels this
> file's findings F6–F9 (they were `F-R2-n`, which `perry-diagnose` read as ids,
> § 9); § 9's totals are in the commit after that.
> Rung reached: V3 (items 1–6). **§ Verification 5, the reading, is not done. It
> is the PMO's, after merge.**

## 0. Base check

- The worktree arrived at `583f024f`. `git merge-base --is-ancestor ddf60594 HEAD`
  exited 1.
- The tree was clean, so this branch alone was fast-forwarded:
  `git merge --ff-only ddf60594`.
- Re-asserted: exit 0, HEAD `ddf60594`. No other branch was checked out, reset
  or pushed; main was not touched.

## 1. What changed

| file | change |
|---|---|
| `bin/perry-task` | The 27 `SURFACE` `writes` lists, each set to its measured files (§ 2). A comment above `SURFACE` says where the lists come from. No code path changed. |
| `tests/test_perry_task_writes_are_what_it_writes.py` | New. 6 tests: the one-declaration guard (§ 3) and the kept measurement (§ 2.3). |
| `tests/durations.json` | The new module, 2.57 s; source `2026-09-15-task262-round2`. |
| `perry/evidence/2026-09/TASK-262-board-sample.md` | Re-made from the code commit's archive (§ 5). |
| `perry/evidence/2026-09/TASK-262-result.md` | One line under F1 pointing here. |

Not touched: `schema/` (no contract page pins these lists; § 4), `bin/perry_store.py`,
`bin/perry-tasks` (its `render` verbs still declare `BOARD.md`), any store,
`.perry/events.jsonl`, the journal, other projects. No `perry-task`,
`perry-tasks`, `perry-okr` or `perry-goals` write ran against this checkout.

The diff to `bin/perry-task`, counted:

| new `writes` | subcommands |
|---|---|
| `["tasks.jsonl", "intake.jsonl", "linkage.jsonl", "journal/", ".perry/events.jsonl"]` | add |
| `["tasks.jsonl", "intake.jsonl", "journal/", ".perry/events.jsonl"]` | route |
| `["tasks.jsonl", "journal/", ".perry/events.jsonl"]` | start, stage, track, next, done, drop, purge, retitle, summary, rung, evidence, prioritize, status, depends, design-link (15) |
| `["asks.jsonl", "journal/", ".perry/events.jsonl"]` | ask, answer |
| `["cadence.jsonl", "journal/", ".perry/events.jsonl"]` | cadence-add, cadence-done |
| `["risks.jsonl", "journal/", ".perry/events.jsonl"]` | risk-add, risk-clear, risk-migrate |
| `["intake.jsonl", "journal/", ".perry/events.jsonl"]` | intake, resolve-intake, intake-sweep |

The old list, `["tasks.jsonl", "BOARD.md", "journal/", ".perry/events.jsonl"]`,
appears 0 times. The four reads still declare `[]`.

## 2. Item 1: the measurement

### 2.1 Method

- **The tool:** `git archive ddf60594`, extracted into scratch. Every write ran
  from that copy's `bin/perry-task` as a subprocess, with `PERRY_HOME` set to it
  and `PERRY_*` otherwise unset.
- **The projects:** fresh temp directories. The argv and prerequisites are
  `tests/test_board_less_reads_and_writes.py § WRITES`, used as-is, plus the
  extra cases below.
- **The measure:** a sha256 of every file under the project root, taken after
  the prerequisites and again after the write. A file counts as changed when
  it was added, removed, or its bytes changed.
- **The shapes:**
  - **A**: that module's fixture: `.perry/config.jsonl`, the tasks, asks,
    risks and intake stores, and an event log. No `BOARD.md`.
  - **B**: A plus a held `perry/BOARD.md`, printed by the archive's own
    `perry-tasks board`.
  - **C**: A plus this repository's `okr.jsonl` and `linkage.jsonl`, so a KR
    register exists.
  - **D**: A with the asks, risks and intake stores removed.
  - **E**: D plus a held `BOARD.md`.
- **Extra cases:**
  - `add` on the queue-mode `intake` track (A, B, D, E);
  - `add --kr P003-O2-KR3` and `add --unlinked` (C);
  - `risk-migrate` over a held board whose `## Top risks` is bullets, with no
    risks store (B).
- The harness is a scratch script, not committed. It hashes files and compares
  path names. It reads no file's meaning.

### 2.2 The table

On every successful run, `journal/` and `.perry/events.jsonl` changed or were
created. They are left out of the columns below.

| subcommand | stores changed, shape A | other shapes | `BOARD.md` rewritten, shape B | declared now |
|---|---|---|---|---|
| add | tasks | C `--kr`: + linkage. D/E queue track: + intake (created). A/B queue track with the store present: intake unchanged. C `--unlinked`: refused (no KR for the current phase) | yes | tasks, intake, linkage |
| start | tasks | same in C, D, E | yes | tasks |
| stage | tasks | same | yes | tasks |
| track | tasks | same | yes | tasks |
| ask | asks | D/E: asks created | yes | asks |
| answer | asks | D/E: refused, no such ask | yes | asks |
| next | tasks | same | yes | tasks |
| cadence-add | cadence (created) | same | yes | cadence |
| cadence-done | cadence | same | yes | cadence |
| risk-add | risks | D/E: risks created | yes | risks |
| risk-clear | risks | D/E: refused, no such risk | yes | risks |
| risk-migrate | refused: the register is already a table | B bullets case: risks created | yes (bullets case) | risks |
| done | tasks | same | yes | tasks |
| drop | tasks | same | yes | tasks |
| purge | tasks | same | **no** | tasks |
| intake | intake | D/E: intake created | yes | intake |
| route | tasks, intake | D/E: refused, no `## Intake` | yes | tasks, intake |
| resolve-intake | intake | D/E: refused | yes | intake |
| retitle | tasks | same | yes | tasks |
| summary | tasks | same | **no** | tasks |
| rung | tasks | same | yes | tasks |
| evidence | tasks | same | yes | tasks |
| prioritize | tasks | same | yes | tasks |
| intake-sweep | intake | D/E: refused | yes | intake |
| status | tasks | same | yes | tasks |
| depends | tasks | same | yes | tasks |
| design-link | tasks | same | **no** | tasks |

- **The rule for `writes`:** the union, over every shape and case, of the files
  whose bytes changed, spelled as the declaration spells them. A store under the
  state root is named by its file name, and anything under the journal is
  `journal/`. `BOARD.md` is left out by the user's decision (F6).
- **No write created or changed a register store it does not own**, in any shape.
  D and E, with three register stores absent, were run to catch exactly that.
- **Not exercised**, and so not measured:
  - `done`'s V5 flags (`--signer`, `--measured`, `--restated`, `--also`,
    `--checked`, `--not-looked-at`);
  - `add --unlinked` landing. It was refused in C. In `commit()` it takes the
    same `linkage` path that `--kr` does (`plan["linkage_record"]`), but that
    is read from the code, not measured.

  Every `commit()` write site was read: the transaction marker (transient), the
  canonical set (stores and journal), the held board, and the event log. The
  measurement touches each of them.

### 2.3 Kept as a test

`TestEachWriteChangesWhatItDeclares` repeats the measurement in the suite, in-process, on
shape A. It also runs three extra cases:

- `add` on a queue track with no intake store;
- `add --kr` on a KR register built from `test_add_writes_the_edge`'s fixture;
- `risk-migrate` from bullets.

It asserts that, per subcommand, the union of files its cases changed equals
`writes`, and that every declaring subcommand has a case. The bullets case is
the only one with a held board, and it discards `BOARD.md` by name.

## 3. Item 2: one declaration

**The choice is a guard test, not a derivation.**

- **`writes` must stay a literal.** `bin/perry-tasks § writer_surface` and
  `tests/board_sources.py § writer_surface` both read `SURFACE` with
  `ast.literal_eval`, and a `SURFACE` that is not a literal refuses the board.
  Deriving `writes` from `REGISTER_EVENTS` in code would break the render the
  amendment says should follow by derivation, or require changing
  `perry-tasks`, which is out of scope.
- **Deriving the other way was rejected too.** `REGISTER_EVENTS` built from
  `writes` would move a map `commit()` consults at runtime
  (`register_change`), 6,451 lines above `SURFACE`, into a computed value. It
  would also need `REGISTER_SPEC`'s path functions to name each store. That is
  a change to the write path, where this row only needed a declaration fixed.
- **The guard is strict equality:**
  `TestOneDeclaration.test_register_events_and_writes_name_the_same_writers`.
  For each key of `REGISTER_SPEC`, it takes the store name from the register's
  own path function (`spec[1](Path("state")).name`) and asserts that
  {subcommands `REGISTER_EVENTS` maps to it} == {subcommands whose `writes`
  names it}.
  - Anti-vacuity: every register has at least one writer, and every
    `REGISTER_EVENTS` key is a `SURFACE` subcommand.
  - Measured today: intake = add, intake, route, resolve-intake,
    intake-sweep; asks = ask, answer; risks = risk-add, risk-clear,
    risk-migrate; cadence = cadence-add, cadence-done. Equal on both sides.
- **What it cannot see:** `tasks.jsonl` has no `REGISTER_EVENTS` key. Its
  writers are held by the measurement test (§ 2.3), not by this guard.
- **Two neighbours in the same class:**
  - every mutating subcommand declares `journal/` and `.perry/events.jsonl`,
    and the four reads declare `[]`;
  - `BOARD.md` is in no entry.

## 4. Items 3 and 4: the gate and what pinned the old list

### 4.1 The gate is unchanged in effect

- **Why, from the code:** `lib.write_needs_installed` returns true when a list
  names a canonical store, `journal/` or `.perry/events.jsonl`. It never
  returned true because of `BOARD.md`. Every one of the 27 new lists names a
  canonical store and both of the other two paths. The test in § 3 holds the
  last two for every mutating subcommand. So the gate decides true for all 27,
  as it did before.
- **Measured, on the code commit:**

  | module | where | result |
  |---|---|---|
  | `tests/test_a_write_refuses_where_nothing_is_installed.py` | this worktree | 11 tests OK |
  | the same | a `git archive 83fed4f3` copy | 11 tests OK |

  The module covers the refusal: each of the 27 exits 1 on the empty,
  `BOARD.md`-only and pre-ADR-019 shapes, `--dry-run` included, and writes
  nothing.

- **Landing on an installed project:**
  - `TestTheStartStillInstalls` green;
  - `test_board_less_reads_and_writes § test_each_write_lands_its_record_event_and_journal_line`
    green;
  - every write in § 2.2 shape A exited 0.
- **The coverage guard notices a bad entry** (§ 6, G1, G2):
  - `next` declaring only `BOARD.md` reddens
    `test_each_write_refuses_and_writes_nothing` and
    `test_dry_run_gets_the_same_refusal`;
  - `status` declaring `[]` reddens
    `test_the_table_covers_every_declared_write` (in this module and in
    `test_board_less_reads_and_writes`).

### 4.2 What pinned the old list

- **Three searches found nothing to change.**
  - The old literal, `"tasks.jsonl", "BOARD.md", "journal/"`, over the whole
    tree except `evidence/`: before the change, the 27 `SURFACE` lines only.
    After it, one hit: this row's new test docstring, which quotes it as
    history.
  - `writes` and `BOARD.md` on one line, in `tests/**/*.py`: one assertion
    about a `writes` list, `tests/test_bin_surface.py:1182`. The other hits are
    prose or fixture text about procedures.
  - `"writes"` in `schema/`, `reference/`, `work/` and `bin/README.md`: no
    hits. `tests/fixtures/` has no `"writes"` key either.
- **No published contract page pins it,** so nothing was stopped.
- **The closest pin is on a different tool:** `tests/test_bin_surface.py:1182`
  pins `BOARD.md` for `perry describe tasks render`, which is `perry-tasks`, as
  the PMO said. It was not changed and is green.
- **Tests that read `writes` and still pass unchanged:**
  - `test_handed_back_root`: `bool(writes)` only;
  - `test_board_less_reads_and_writes`: the set of subcommands with non-empty
    `writes`;
  - `test_board_names_its_sources`: builds its expectation from `SURFACE`, and
    uses synthetic surfaces for the no-writer cases.
- **Result: no existing test needed an edit. One module was added.**
- **Green on the worktree after the change:** `test_bin_surface` (59),
  `test_board_names_its_sources` (13), `test_board_less_reads_and_writes` (27),
  `test_handed_back_root` (26).

## 5. Item 5: the board follows by derivation

`bin/perry_store.py` and `bin/perry-tasks` are unchanged. From
`bin/perry-tasks board` in a `git archive 83fed4f3` copy, extracted into a
directory named `Perry`, over the stores that commit carries:

```
## P0 (must finish this period)
> Stored in `tasks.jsonl` under the state root; written by `perry-task` add, start, stage, track, next, done, drop, purge, route, retitle, summary, rung, evidence, prioritize, status, depends, design-link
## Cadence (recurring; doesn't consume P0 slots)
> Stored in `cadence.jsonl` under the state root; written by `perry-task` cadence-add, cadence-done
## User Input Queue
> Stored in `asks.jsonl` under the state root; written by `perry-task` ask, answer
## Top risks (one-line; full list in `PROJECT_STATE.md`)
> Stored in `risks.jsonl` under the state root; written by `perry-task` risk-add, risk-clear, risk-migrate
```

- **This repository:** `## P1` and `## P2` print the `## P0` line. The task
  sections name 17 subcommands, down from 27.
- **The fixture:** it also prints
  `` > Stored in `intake.jsonl` under the state root; written by `perry-task` add, intake, route, resolve-intake, intake-sweep ``.
  Its `## Someday` line is the task line.
- **Nothing on either board says "no subcommand declares a write" any more.**

**The sample:** `perry/evidence/2026-09/TASK-262-board-sample.md`, 167 lines,
that render byte for byte. Against round 1's sample, 7 lines differ:

- the 6 section lines;
- one `## P1` row, `TASK-262`, whose `Status` reads `in_progress` instead of
  `not_started`. The task store at `ddf60594` says so. It moved between round
  1's commit and this base; it is not a change here.

## 6. Verification, on the code commit

`bin/` and `schema/` are identical between `83fed4f3` and this branch's last
commit. So is every `tests/*.py` except one docstring line in the new module,
which corrected a line count ("twelve hundred" to 6,451). The commits after it
change only that line, this file, the sample, round 1's pointer line and
`tests/durations.json`.

### 6.1 Verification 1 and 2: section lines and column marks

| project | sections naming their store and writer | columns classified | how |
|---|---|---|---|
| this repository's stores (`83fed4f3` archive) | 6/6 (100%) | 62/62 (100%) | `python3 tests/board_sources.py --root <archive>/Perry`, exit 0 |
| the `test_board_from_declarations` fixture | 8/8 (100%) | 80/80 (100%) | the same command, over a copy of `Fixture()` at a fixed path, exit 0 |

- `test_board_names_its_sources` (13) and `test_board_from_declarations` (16)
  pass inside the `83fed4f3` archive.
- The expectations are built from `§ claims`, a separate `ast` reader of
  `SURFACE`, and the `*FIELD_BY_COLUMN` maps (round 1 § 3.2).

### 6.2 Verification 3: nothing else moved

Round 1's strip rule (`tests/board_sources.py` docstring) was applied to the
`83fed4f3` board, and the result compared with `cmp` against `7f97d337`'s
`bin/perry-tasks board` (the pre-TASK-262 base, from a `git archive` into a
directory also named `Perry`). Both ran over the same stores.

| project | lines the strip removed | `cmp base stripped` |
|---|---|---|
| this repository's stores | 7 (the legend and 6 section lines) | equal (exit 0) |
| the fixture | 9 (the legend and 8 section lines) | equal (exit 0) |

### 6.3 Mutations (items 1–3 and Verification 4)

**The harness.** For each mutation:

- a fresh `git archive 83fed4f3` into its own scratch directory;
- the anchor asserted to occur exactly once, then replaced;
- every `__pycache__` cleared;
- each named module run alone with
  `python3 -m unittest discover -s tests -t . -p <module>`;
- the original bytes restored and compared with `git show 83fed4f3:<path>`;
- caches cleared again and the modules re-run.

One mutation ran per shell command. The harness is a scratch script and is not
committed.

- **Every mutation:** anchor count 1, restored file == `git show`, every module
  green after the restore.
- **Failure counts** include subTests. The named tests are the distinct ids
  that failed.

| # | item | mutation (`bin/perry-task` unless noted) | red, named test (failures) | green, and why that is right |
|---|---|---|---|---|
| W1 | 1 | `ask` loses `asks.jsonl` | `test_register_events_and_writes_name_the_same_writers`, `test_writes_is_the_union_of_what_its_cases_changed` (2) | `test_board_names_its_sources`: its expectation reads the same `SURFACE`, so a wrong declaration is not its question. The gate module: `journal/` still gates `ask`. |
| W2 | 1 | `next` also declares `linkage.jsonl` | `test_writes_is_the_union_of_what_its_cases_changed` (1) | — |
| W3 | 1 | `retitle` declares `BOARD.md` again | `test_board_md_is_in_no_entry`, `test_writes_is_the_union_of_what_its_cases_changed` (2) | — |
| W4 | 1 | `drop` loses `journal/` | `test_every_mutating_subcommand_declares_and_no_read_does`, `test_writes_is_the_union_of_what_its_cases_changed` (2) | The gate module: `tasks.jsonl` still gates `drop`. |
| W5 | 1 | `add` loses `linkage.jsonl`, a write only `--kr` makes | `test_writes_is_the_union_of_what_its_cases_changed` (1) | — |
| W6 | 1+2 | `add` loses `intake.jsonl` | `test_register_events_and_writes_name_the_same_writers`, `test_writes_is_the_union_of_what_its_cases_changed` (2) | `test_board_names_its_sources`, as W1 |
| R1 | 2 | `REGISTER_EVENTS` loses `"answer": "asks"` | `test_register_events_and_writes_name_the_same_writers`, `test_writes_is_the_union_of_what_its_cases_changed` (2) | — |
| R2 | 2 | `REGISTER_EVENTS` maps `cadence-done` to risks | the same two (3) | — |
| R3 | 2 | `writes` alone: `risk-clear` names `cadence.jsonl` | the same two (3) | `test_board_names_its_sources`, as W1 |
| G1 | 3 | `next` declares only `BOARD.md`, which nothing gates | `test_a_write_refuses_where_nothing_is_installed`: `test_each_write_refuses_and_writes_nothing`, `test_dry_run_gets_the_same_refusal` (6). Also this row's three `TestOneDeclaration`/measurement tests (3). | — |
| G2 | 3 | `status` declares `[]` | `test_the_table_covers_every_declared_write` (1). `test_board_less_reads_and_writes § test_the_write_table_covers_every_declared_write` (1). `test_every_declared_write_is_measured`, `test_every_mutating_subcommand_declares_and_no_read_does` (2). | — |
| V4-M1 | V4 | `perry_store.py`: no section line under `## P2` | `test_every_section_names_its_store_and_its_writers` and `test_nothing_else_moved`, repository and fixture (4) | `test_board_from_declarations`: lines are not its question (round 1) |
| V4-M2a | V4 | `perry_store.py`: every store gets `tasks.jsonl`'s writers | `test_every_section_names_its_store_and_its_writers` ×2, `test_the_writers_are_the_surface_s_not_the_nearest` (9) | as M1 |
| V4-M2b | V4 | `perry_store.py`: one writer too few | the same three (16) | as M1 |
| V4-M3 | V4 | `perry_store.py`: mark the stored `Title` column | `test_every_column_is_marked_exactly_when_it_has_no_stored_field` ×2 (7) | `test_board_from_declarations`: its `sections()` drops a header mark by design (round 1) |
| V4-M4 | V4 | `perry_store.py`: unmark the derived `Idle` column | the same (4) | as M3 |
| V4-M5 | V4 | `perry_store.py`: one cell (`Owner` gains `.`) | `test_board_from_declarations § test_every_cell_equals_the_store_value`, fixture and repository (97) | `test_board_names_its_sources`: its reference is the same renderer (round 1 § 3.3) |

- Every mutation reddened at least one named test.
- Every green in the last column was checked against the reason given. None is
  a finding.

## 7. Verification 5: the reading, NOT DONE

I cannot ask the user, so this belongs to the PMO, after merge.

- **Sample to show:** `perry/evidence/2026-09/TASK-262-board-sample.md`, 167
  lines, made as § 5 says from `83fed4f3`'s committed stores. The live stores
  were not used, so the sample will not change before the reading.
- **F1 is fixed in this sample:** the Cadence, User Input Queue and Top risks
  lines name their writers.
- Show the file and nothing else, then ask:
  1. "Where would you change this row's next action?" Point at one `## P1`
     row.
  2. "Why is this cell empty?" Point at one `Idle †` cell in
     `## User Input Queue`. Pointing at an empty stored cell as well, such as
     `Asked` on `USER-001`, tests the legend's second sentence.
  3. "Is the title stored anywhere?"

**Answers (verbatim):** _empty. Nobody has been asked. The row closes only
after the PMO records the reading here._

## 8. Findings

**F6: the amendment's premise holds only for a board-less project.
`BOARD.md` is still written where a project holds one.**

- **What the premise says:** "nothing writes it since TASK-237 3c". That is
  true of this repository and of any project with no `BOARD.md`.
- **What the measurement found (shape B):**
  - 24 of the 27 re-render a held `BOARD.md`. `purge`, `summary` and
    `design-link` do not.
  - `risk-migrate` writes only on a held board, because its input is the
    board's bullets.
- **The source:**
  - `commit()` calls `lib.write_atomic(board.path, board_text)` whenever the
    board was loaded from disk (`Board.on_disk`);
  - `bin/README.md` documents it: "`BOARD.md`, RE-RENDERED from (1), only
    where the project still holds one";
  - `test_board_less_reads_and_writes` holds it ("While the file exists it is
    still re-rendered").
- **What I did:** dropped `BOARD.md` from every entry, as the amendment and
  the dispatch direct.
- **The cost:** on a project that still holds a `BOARD.md`, `perry describe`
  does not list a file most writes rewrite.
- **It changes neither the gate nor the board.** `write_needs_installed` never
  counted `BOARD.md`, and no board section's store is `BOARD.md`.
- **The decision is the user's:**
  - either `writes` names the held board after all;
  - or the held-board re-render is retired, with its README line and test.

  I made neither change. **No row opened.**

**F7: every register write replaces `tasks.jsonl` with identical bytes.**

- **What happens:** `commit()` always stages the task store in the canonical
  set, `canonical = [(spath, perry_store.store_text(records))]`.
- **Measured:** `ask`, `risk-add`, `intake` and `cadence-add` each moved
  `tasks.jsonl`'s inode and mtime, and left its sha256 unchanged.
- **The declaration follows bytes.** Naming a replacement with the same
  content would have made `ask` a writer of the task sections. The rule is in
  the test's docstring.
- **The risk is inside the transaction's guarantees, not outside them.** Any
  reader that watches mtimes sees the task store "change" on every register
  write. **No row opened.**

**F8: `REGISTER_EVENTS` maps `add` to intake, and `add` changes
`intake.jsonl` only when it creates it.**

- **When:** on a queue-mode track with no intake store (D, E).
- **Otherwise:** with the store present, the store is left unchanged (A, B).
- **Result:** the declaration names it, and both declarations agree. Recorded
  so that "`add` writes intake" is not read as "every `add` changes the intake
  store".

**F9: round 1's F2 remains, shorter.** Each task section names 17
subcommands. Whether the line should name a writer family is still a wording
question for after the reading.

## 9. The suite

### 9.1 A red on `4a27b2c3`, and whose it was

The first two runs, both on `4a27b2c3` (the evidence commit), each reported
**1 of 141 modules red**:
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
`user_load.dangling == ['R2-1', 'R2-2', 'R2-3', 'R2-4']`.

- **Re-run alone on this branch:** red, the same four ids.
- **Run alone in the base `ddf60594` archive:** green (158 tests).
- **Cause:** this file. Its findings were labelled `F-R2-1` … `F-R2-4`.
  `perry-diagnose` finds ids with `\b(?:<prefix>)-\d+\b`, so it read `R2-1`
  and the rest as references to ids that exist nowhere.
- **Fix:** `1696571c` relabels them F6–F9, continuing round 1's F1–F5, which
  have no dash-digit.
- **After the fix:** the module alone is green (158 tests).

Not a standing red, not order- or clock-dependent, and not a code regression.

### 9.2 On `1696571c`

`bash tests/run`, in the foreground, with nothing else running in the tree.
The output was saved to scratch.

| step | result |
|---|---|
| 0. tree guard | recorded at the start; at the end, nothing under the worktree moved |
| 1. schema drift guard | clean |
| 2. contract tests | **141 modules, 3998 tests, 0 red**, 95.3 s, 8 workers: all green |
| 3. `bin/` scripts | all OK |
| 4. sample projects lint | English: 0 errors, 9 warnings, the fixture's own standing ones. Chinese: clean |

- **Against round 1:** 140 modules and 3992 tests, plus this row's module
  with its 6 tests.
- **The durations line** reads 142 recorded, 144 on disk, 4 unmeasured. It
  still names the two modules round 1's F5 named,
  `test_a_write_refuses_where_nothing_is_installed.py` and
  `test_contract_page_snippets.py`. Neither is this row's.
  `test_perry_task_writes_are_what_it_writes.py` is recorded.

This section is the only change in the commit that adds it.
