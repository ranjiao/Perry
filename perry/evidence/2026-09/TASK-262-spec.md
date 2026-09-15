# TASK-262 — spec

> Design: `ADR-010` (the board is a render), `USER-907` answer (a) (restated
> `P003-O2-KR3`), `DESIGN-013 § 5.4`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: whether a reader who has never seen Perry can tell,
> from `perry-tasks board` alone, what is a stored record and what the render
> made up. That is a person's judgement, taken on a sample (§ Verification 5).
> Touches architecture: no
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P2 · **Track / mode**: main / project
- **Dependencies**: `TASK-236` (done), **`TASK-237` (in progress)**. Do not
  dispatch this until `TASK-237`'s deliverable 3c is merged. Before 3c,
  `BOARD.md` is still re-rendered on every write, and a marker added to one
  renderer and not the other would give the board two faces.
- **KR linkage**: `P003-O2-KR3`. This is the row's only edge.
- **Verification rung**: V3, a reproducible run, plus one person's reading
  (§ Verification 5).

## Why

`USER-907` (a), 2026-08-29, in the user's words: the KR was never buying "a
marker in the file". It was buying the reader-visible property that a reader
can tell truth from projection, and that need survives onto the surface ADR-010
creates. `TASK-199` carried this scope on `BOARD.md` and was dropped in error on
2026-09-01; this row replaces it.

**After `TASK-237` the whole board is a projection.** The canonical records are
the JSONL stores. What `perry-tasks board` prints is three different kinds of
thing, and today nothing on the page tells them apart:

| kind | example | where it comes from |
|---|---|---|
| **stored** | a task's `Next action`, an ask's `Status`, a cadence row's `Next due` | one field of one record, printed as written |
| **rendered** | which `## P1` section a row sits under; a list joined with `, `; an empty cell for null | a rule in `bin/perry_store.py § DECLARED_BOARD_CHOICES`, applied to a stored field |
| **not stored anywhere** | the title's project name (the directory's name); `Idle`, printed empty | the render itself |

A reader who edits what they see needs to know which row of this table they are
looking at. Editing a stored value goes through one writer. A rendered value
changes only when the stored field under it does. The third kind cannot be
edited at all.

## Deliverable

1. **Every section names its canonical store and its writer.** Directly under
   each `## ` heading, the render prints one line naming:
   - the store path, as declared in `schema/state-schema.json § claims`;
   - the `perry-task` subcommands that write that register, taken from the
     tool's `SURFACE` rather than typed.
   The wording is the executor's; it must be one line and must not be a table
   row.
2. **Every column is classified, and the non-stored ones are marked.**
   - A column that maps to a stored field (`perry_store.*FIELD_BY_COLUMN`) is
     stored.
   - A column with no stored field is marked in its header, with a legend line
     in the board's header prose naming the mark.
   - The classification is **derived** from the column maps, never kept as a
     hand list.
3. **Text the render supplies is marked as such.** Today that is the title's
   project name. The mark is in the same vocabulary as item 2.
4. **The KR gets a measured value.** `P003-O2-KR3` has no `current` and no
   `target` today (`perry-goals list --json`). Propose a measurement in the
   result:
   - suggested: sections that name their store and writer, over sections
     printed; plus columns classified, over columns printed; both targeting
     100%;
   - a command that prints both numbers;
   - leave writing the KR record to the goals lane. **Do not write
     `okr.jsonl` or `linkage.jsonl`.**

## Files in scope

- `bin/perry_store.py`: the board renderer and `DECLARED_BOARD_CHOICES`.
- `bin/perry-tasks`: `board`, if the surface lookup belongs there.
- `tests/`: the guards.
- `perry/evidence/2026-09/TASK-262-result.md`: written.

## Bound

```
Enumeration:  every section perry-tasks board prints, and every column of
              every table it prints, on this repository and on the fixture
              test_board_from_declarations builds
Size:         derive it from the render's output. Measured 2026-09-14 on
              161c927c: 5 declared tables (tasks under P0/P1/P2, Intake,
              User Input Queue, Cadence, Top risks). Recount; do not take
              that number
Remainder:    JSON payloads (perry-state, perry-task list, …). They are
              queries of the canonical records, not a render, and they are out
              of scope
Last element: the last column of the last table in print order
```

## What it must not do

1. **Must not change any cell value, any row or row order, or any column
   order.** The markers are added lines and header marks only. aiMark renders
   this output as Markdown for a person; a changed cell is a regression there.
2. **Must not add a JSON field or change a published contract.**
3. **Must not hand-list which columns are stored.** A list kept beside the
   column maps is exactly the second enforcement point this project keeps
   paying for (`TASK-253 § 5`).
4. **Must not print a writer for a register that has none.** If a section's
   store has no `perry-task` writer, say so on that line rather than naming the
   nearest one.

## Verification

1. **Section markers.** For every section in the output, the named store
   exists in `§ claims`, and every named writer is a `perry-task` subcommand
   whose `SURFACE` entry writes that store. The expectation is built from the
   schema and the surface, not from the output.
2. **Column classification.** For every printed column, the mark is present
   exactly when the column maps to no stored field. The expectation is built
   from the `FIELD_BY_COLUMN` maps.
3. **Nothing else moved.** With the marker lines and header marks stripped by
   a documented rule, the output is `cmp`-equal to `perry-tasks board` at the
   base commit, on the same stores.
4. **Mutations.** Each of these reddens a named test:
   - drop one section's marker line;
   - name the wrong writer;
   - mark a stored column;
   - unmark a derived one;
   - change one cell.
5. **A reading.**
   - Give `perry-tasks board` output, with no other context, to one person:
     the user, or someone they name.
   - Ask three questions:
     - "Where would you change this row's next action?"
     - "Why is this cell empty?"
     - "Is the title stored anywhere?"
   - Record the answers verbatim in the result. This is the KR's actual
     property; items 1–4 only make it checkable.
6. **The suite**, with any pre-existing reds named.

## Out of scope

- Deleting `BOARD.md` or anything else in `TASK-237`.
- Writing the KR record (the goals lane).
- `TASK-434` (answered asks never leave the board).

## Amendment (1) — 2026-09-14, at dispatch

- **The dependency is met.** `TASK-237` closed at V4 on 2026-09-14 (`90d2f853`):
  `BOARD.md` is deleted, nothing re-renders it, and `perry-tasks board` is the
  only board. There is one renderer, so the "two faces" risk above is gone. Do
  not recreate `BOARD.md` or add a marker to any file-writing path.
- **Base.** Pinned to the commit that carries this amendment. Assert it is an
  ancestor of your HEAD before any work; if it is not, fast-forward your own
  branch to it (never another branch, never main).
- **Recount the sections.** On this repository at `90d2f853` the board prints
  `## P0`, `## P1`, `## P2`, `## Cadence …`, `## User Input Queue` and
  `## Top risks …`, and **no Intake section** (no intake rows here). The
  fixture `test_board_from_declarations` builds may print Intake. Verification
  1–3 cover both.
- **Writers.** Name the `perry-task` subcommands whose `SURFACE` entry writes
  the section's store. The `perry-tasks … --from-board` and `*-write` imports
  are upgrade paths (`reference/version-compatibility.md`), not the writer a
  reader should use; do not name them. A store with no such `perry-task`
  writer says so (What it must not do 4).
- **Verification 5 is the PMO's, after merge.** You cannot ask the user. Put
  in the result: the exact board sample to show (a file under
  `perry/evidence/2026-09/`, rendered from a copy, not this repository's live
  stores if they would change before the reading), and the three questions.
  Leave the answers section empty and say so. The row closes only after the
  PMO records the reading.
- **The suite** on your final commit, foreground, with the tree still. There
  are no standing reds at `5f6bee61` (`TASK-335` closed them).

## Amendment (2) — 2026-09-15, round 2: the writer declaration (user decision)

Round 1's result F1, reproduced by the PMO on main at `8c8b3602`: all 27
mutating subcommands in `bin/perry-task § SURFACE` declare the identical
`writes` list `["tasks.jsonl", "BOARD.md", "journal/", ".perry/events.jsonl"]`
(the other 4 declare `[]`), while `bin/perry-task § REGISTER_EVENTS` says
`risk-*` write risks, `intake`/`resolve-intake`/`intake-sweep`/`route`/`add`
write intake, `ask`/`answer` write asks and `cadence-add`/`cadence-done` write
cadence. Since the board's section lines are derived from `writes`, three
sections say no writer is declared and the task sections name all 27. The user
chose to fix the declaration **inside this row**, before the reading.

**Scope added:** `bin/perry-task` (the `SURFACE` `writes` entries only, and
whatever single source the fix derives them from), plus the tests that pin
them.

1. **Each subcommand's `writes` names what it actually writes.** Measure it —
   run each subcommand on a copy and diff which files change — rather than
   reading prose. `BOARD.md` leaves every entry: nothing writes it since
   `TASK-237` 3c.
2. **One declaration, not two.** `writes` and `REGISTER_EVENTS` must not be
   able to disagree again: derive one from the other, or add a guard that goes
   red when they differ. Say which, and why.
3. **The install gate is unchanged in effect.** `lib.refuse_write_unless_installed`
   decides on `writes`. Every one of the 27 must still be refused on a
   non-installed shape and land on an installed one; re-run
   `tests/test_a_write_refuses_where_nothing_is_installed.py` and mutate a
   `writes` entry to prove its coverage guard notices.
4. **Published surfaces.** `perry describe` prints `writes`. Find every test or
   page that pins the old list (for example `tests/test_bin_surface.py`) and
   update it; if a published contract page pins it, stop and report instead of
   editing the page.
5. **The board follows by derivation.** No change to `bin/perry_store.py`'s
   derivation should be needed; the section lines for Cadence, User Input Queue
   and Top risks should now name writers, and the task sections fewer. Re-make
   the Verification 5 sample from the final commit.
6. Verification 1–4 and 6 again on the final commit, with mutations for items
   1–3 above.
