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

## Amendment (3) — 2026-09-15, round 3: a held `BOARD.md` is retired (user decision)

**Correction.** Amendment (2) said nothing writes `BOARD.md` since `TASK-237`
3c. That was the PMO's error. Round 2's F6, reproduced by the PMO on a copy of
`21d271e5` that holds `perry/BOARD.md`: `perry-task next` and `perry-task ask`
both rewrite it (24 of 27 writes do). A held board is also READ: the write
builds its layout from it, and a stale one refuses the write
(`reference/version-compatibility.md`, the G2-with-a-stale-board row). Several
`perry-lint` checks read `state_root / "BOARD.md"` too.

**User decision, 2026-09-15:** 停用老的 `BOARD.md`，并且提示用户可以删除 — retire
the old `BOARD.md`, and tell the user they can delete it. Kept in this row
because F6 arose here and no new row is opened.

Deliverable:

1. **No `perry-task` write reads or rewrites a held `BOARD.md`.** The board a
   write mutates is built from the declarations exactly as on a board-less
   project. On an installed project holding a `BOARD.md` that disagrees with
   the stores, the write succeeds and the file's bytes are unchanged.
   `writes` stays without `BOARD.md`, which is now true.
2. **The hint.** Where a `BOARD.md` exists at the state root (or the project
   root), print one line to **stderr** on a successful write, on
   `perry-tasks board`, and as a `perry-lint --root` **warning** (not an
   error): it names the path, says no tool reads or updates it any more, that
   the board is `perry-tasks board`, and that it can be deleted
   (`git rm <path>`). Exit codes and stdout (including `--json` payloads) are
   unchanged. One wording, defined once.
3. **Every other reader in `bin/` and `viewer/`, enumerated and classified**
   (write the table into the result):
   - (a) **import verbs** that read a board to create stores
     (`perry-tasks write --from-board`, the `*-write --from-board` family,
     `perry-task risk-migrate`): the upgrade path, keep reading
     (`reference/version-compatibility.md`);
   - (b) **render / diff / verify verbs** that write or compare `BOARD.md`
     (e.g. `perry-tasks render`, `*-render`): retiring them is `R5`, not this
     round. Leave them, list them;
   - (c) **everything else** stops reading it. If the check still means
     something, read the store it projects; if it only existed to police the
     file, remove it and say so. If a removal would drop a check with no store
     equivalent, **stop and report** instead of removing it.
4. **Guards.** The writes guard gains a held-board case (no `BOARD.md` byte
   changes, the hint is printed). A test proves a stale held board no longer
   refuses a write.
5. **Docs.** Update `reference/version-compatibility.md` (the stale-board row
   and rule 4) and any `bin/README.md` / `bin/ARCHITECTURE.md` sentence saying
   a write re-renders a held board. **Do not edit `ARCHITECTURE.md` § NN-2**:
   it is the user's (NN-6). Propose the new wording in the result.
6. **Mutations**, each red on a named test: the rewrite re-enabled; the hint
   suppressed; the write reading a held board again (the stale-board refusal
   returns); one (c) reader restored.
7. Verification 1–4 and 6 again, and re-make the board sample only if the
   output changed (it should not).

## Amendment (4) — 2026-09-15, round 4: full retirement, with the pins lifted (user decisions)

Round 3 stopped correctly on contract pins (`TASK-262-round3-result.md § 1`,
P1–P6, verified by the PMO) and measured the blast radius (Stage A: 40 red
modules; Stage B: 20). The user decided, 2026-09-15:

- **Scope: full retirement as Amendment (3) wrote it.** The contract pins are
  lifted: amend `schema/task-list-contract.md` (P1, P2, P3, P6),
  `schema/asks-list-contract.md` (P4) and `schema/goals-list-contract.md` (P5),
  each with a **minor version bump and a `semantics[]` entry** in the tool that
  emits it, following how `installed` was added in TASK-237 3b′.
- **F14: re-point, do not drop.** `done-needs-evidence`, `check_verification`'s
  board pass and `check_reviews`' V4 board pass judge **terminal
  `tasks.jsonl` records that carry no `done` event** (the imported ones) instead
  of hand-kept board rows. PMO measured this repository at `81a0e808`: 267
  `done` records, 0 without a `done` event, so it adds no warning here.
- **`schema/state-schema.json`, consent for exactly two text edits:**
  `files[id=board].note` (a held file is retired and read only by the import
  verbs; the headings and tables stay declared because `perry-tasks board` lays
  the board out from them) and `cross_file[id=done-needs-evidence].description`
  (a `tasks.jsonl` record, not a BOARD row). **Any other edit to that file:
  stop and report.**
- **NN-2:** the user accepted round 3 § 5's wording. The PMO edits
  `ARCHITECTURE.md` at merge; executors do not.

Delivered in **two rounds, in order**, because both reshape the same tests:

**Round 4a — the write path.**
1. Amendment (3) item 1: every `perry-task` write builds from the declared
   board; `commit()` never writes a board file; `risk-migrate` keeps reading
   `## Top risks` as its import input and never rewrites the file.
2. The hint (round 3 § 4's wording, defined once in `bin/lib`) on stderr after a
   successful write where a `BOARD.md` exists.
3. P1 rewritten, with the `perry-task/list` version/semantics entry if the
   payload's meaning changes (if it does not, say why no bump).
4. F12: the ~40 modules that assert held-board write behaviour are rewritten to
   the board-less behaviour or deleted with it — each deletion named with the
   behaviour it tested. No test is weakened to pass.
5. F13: delete `refuse_store_drift`.
6. Mutations: the rewrite re-enabled; the hint suppressed; the stale-board
   refusal restored.

**Round 4b — every other reader** (after 4a merges).
1. F15 first: upgrade `tests/fixtures/sample-project` and any other fixture
   holding a board and no stores, by the documented upgrade procedure, with
   expectations re-derived rather than copied.
2. Retire every class-(c) reader in round 3 § 3: `viewer/parsers.py §
   load_snapshot`, the `perry-task list`/`asks` fallbacks, `drift`,
   `perry-state`, `lib.task_status_index`, `perry-diagnose`, `perry-lint`
   (F14 re-pointed as above), with P2–P6 and the two `state-schema.json` notes.
3. The hint from `perry-tasks board` and as a `perry-lint --root` warning.
4. Docs: `reference/version-compatibility.md`, `bin/README.md`,
   `bin/ARCHITECTURE.md`, and any contract prose round 3 § 6 lists.
5. Mutations: one retired reader restored; an F14 pass dropped; the lint hint
   suppressed.

Both rounds: import verbs (class a) keep reading; render/diff/verify verbs
(class b) stay for `R5`; stdout of non-contract output and exit codes change
only where a contract amendment says so; the suite on the final commit.
