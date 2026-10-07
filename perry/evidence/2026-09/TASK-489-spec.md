# TASK-489 — DESIGN-023 D: importer — this repository and SkyTonight reconciled

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V4
(DESIGN-023 decision 10: an import defect loses state).
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.3`, `§ 5.6`, `§ 6` row D.
Depends on: TASK-488.
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: the V4 fresh-context review; the user's call on long prose `Next action` cells
> Touches architecture: `bin/` gains one executable, the one-shot importer (`bin/ARCHITECTURE.md`; root § 2's tool count)
> Deployed: no

## Files in scope
- `bin/perry-kernel-migrate` (new): the one-shot importer. See § Decided 2026-09-29.
- `kernel/`: only the carried import-correctness items below. The kernel stays
  free of every template and old-store name (Goal 1).
- `tests/`: the importer's tests.
- `perry/evidence/2026-09/TASK-489-reconcile-perry.md` and
  `TASK-489-reconcile-skytonight.md`, one reconciliation report per project.
- Read-only: this repository's `perry/*.jsonl` and `.perry/events.jsonl`, and
  the same files under `~/proj/SkyTonight`.

## Deliverable
The importer moves today's stores into a kernel store:
- `tasks.jsonl`, the register stores, and `.perry/events.jsonl`.

It is run on both projects, **each into a temporary store**. Neither project's
live store is created before TASK-490.

Rules:
- Ids keep their numbers.
- Each prefix's id ceiling is seeded from every id ever issued. That includes
  purged task ids, which survive only in the event log.
- Evidence is imported as one text field. It is never split into attachments by
  pattern (ADR-007).
- Long prose `Next action` cells (DESIGN-013 § 7) are shown to the user and
  decided before the import runs.

## Carried from TASK-487, decided by the user 2026-09-25

The kernel's own `import` replays events, but it does not check the replayed
field values, or a declared relation's end types, against the template that
was in force when each event was written. Close that gap here, since this row
is where import correctness is verified at V4. Add a test for each check, and
show that each test goes red under a mutant of its check.

Also carried from TASK-487's round-3 V4 review (`TASK-487-review-round3.md`):
- **F1.** Decide whether a no-op `parent` change (`before: true`, `after: true`)
  replays. a408a4db accepted it; 0b14b8dd returns `export_invalid`. Pin the
  answer with a test, and correct the comment at
  `kernel/perry_kernel/store.py:623–625`.
- **F2.** Restore a test of the import id cap at `commands.py:1018`, using an id
  of 17 or 18 digits above 2^53. D2's 18-digit bound now shadows the only
  existing test of it.
- **F3.** Test that export records a token for a store that has none
  (`commands.py:907`).
- **F4.** Test the `Store.open` retries (`store.py:239`, `:253`), and test the
  deadline's upper bound (`:105`).
- **F6.** A damaged `export_token` must give `store_corrupt`, not `io_error`
  (`commands.py:901`).

## Carried from DESIGN-023 decision 13, 2026-09-29

The template has three types. Old records map onto them as follows:

- **Tasks.**
  - `title`, `summary`, `priority`, `owner`, `track`, `verification`,
    `next_action` and `evidence` keep their names.
  - `status` becomes the state.
  - `depends_on` becomes `blocks` relations, and `design_refs` becomes
    attachments.
- **Asks.**
  - `needed` becomes `question`.
  - `status` and `answered` become the state.
  - `blocks` becomes relations.
- **Risks.**
  - `risk` becomes `concern`.
  - A `status` of `open` stays `open`, and one that begins `cleared` becomes
    `cleared`.
- **Dates.** An item's create event is timed at its creation date: `created`,
  `asked` or `opened`. If the item is not in its type's initial state, one
  move event takes it to its current state. That event is timed at the last
  old status event for the id in `.perry/events.jsonl`, or at `cleared` for a
  risk. If neither exists, it uses the creation date. `arrived` and
  `stage_since` are not imported.
- **Fields not imported.** `group`, `order`, `commitment`, `role`, `stage`,
  `arrived` and `stage_since` are not carried over. Neither is `next_action`
  on a `done` or `dropped` task (§ Decided 2026-09-29). The report counts the rows that held a value in each
  one. They stay readable in git history and in the old files.

Import runs no guards. A row with no `verification` or no `summary` is imported
as it is. The item types `intake` and `cadence` do not exist. Both stores hold
no rows today. If a row appears in either before the importer runs, stop and
report it.

## Decided 2026-09-29

- **Long `Next action` cells (the user's call, option A).** Measured on
  2026-09-29:
  - in this repository, 160 of 488 cells are over 300 bytes, and the longest
    is 3,956;
  - 153 of those 160 are on `done` or `dropped` rows. The other 7 are open
    rows of 318–351 bytes: TASK-238, 334, 220, 371, 393, 309 and 286. (This
    list replaces an earlier sentence here, which said all 160 were closed.
    The executor found the error. The user's option A already covers these 7,
    because an open row is imported as it is.)
  - SkyTonight's longest is 158.

  A closed task's `next_action` is not imported. An open task's is imported
  as it is. The report counts the skipped cells. The text stays in git history
  and in the old `tasks.jsonl`.
- **Where the importer lives (decided by the PMO).** It is a one-shot tool in
  the old `bin/`, not kernel code, because it must name the old stores' fields
  and the template's. It works in four steps:
  1. It reads the old stores through the existing readers. Root § 3 forbids a
     second parse.
  2. It writes a synthetic export into a temporary anchor it creates.
  3. It runs the kernel's own `bin/perry-kernel import` into a temporary store.
     The kernel checks the replay (criterion 5).
  4. It is deleted at phase H with the rest of the old `bin/`. Both projects
     are migrated at phase E, before then.
- **A snapshot, not a replay of history (decided by the PMO).** Each item gets
  the events under "Dates" above, and no others. Old status and field history
  is not converted into kernel events. `.perry/events.jsonl` and `journal/`
  stay as read-only documents. The old event log still seeds each prefix's
  id ceiling, purged ids included.
- **Dispatch mode.** Changed from `manual` to `auto` once the long-cell
  decision was made.
- **Two import rules, decided after round 1.**
  - The old store's blank marker `—`, and an empty string, mean the field is
    unset, so neither is imported.
  - A move event is never timed before its item's create event.

  Both keep stored data to what it means (DESIGN-023 decision 13).

## Round 3, decided by the PMO 2026-10-07

Round 1's V4 review failed on the blank rule (`TASK-489-review-round1.md`).
The architecture review passed. Round 3 continues on `coding/task-489-importer`
from `8649b63b`. Each rule below names the existing reader it uses, because
root § 3 forbids a second parse.

1. **Blank cells.** A cell is unset when `lib.is_blank_cell` says so. That is
   the project's one blank rule, which `tests/test_blank_cell_is_one_rule.py`
   pins. It replaces "only `—` and an empty string" in § Decided 2026-09-29.
   Today's data holds only those two spellings. The report keeps its counts
   per spelling.
2. **Ask answers.**
   - For an answered ask, `answer` is the text `parsers.ask_answer` returns.
   - For a closed ask where that text is empty, such as `withdrawn …`,
     `answer` is the status cell verbatim.
3. **Risk state and reason.**
   - A risk is `cleared` when `parsers.status_is_cleared` says so. This
     replaces "begins with `cleared`".
   - A cleared risk's `reason` is its status cell verbatim. No new parse is
     written to cut the reason out.
4. **References.**
   - `blocks` and `depends_on` cells are split by the existing reader where
     one exists. Otherwise they split on commas, semicolons and whitespace.
   - A reference that does not resolve to an imported id makes the run "not
     reconciled", with a non-zero exit.
   - The one exception is a key-result id. It is listed under "for TASK-492",
     which must restore those edges once key results are kernel items. Today
     there are three: the asks that block `P003-O2-KR3`.
5. **Kernel errors.** A kernel refusal during reconciliation is reported, the
   run is "not reconciled", and no traceback is printed.
6. **Id ceilings.** These read every id-bearing key of the old events: `id`,
   `task` and `record.id`.
7. **The importer's own checks.** Its checks for criteria 3 and 5 get tests
   that show each one failing when it should. The round-1 mutants M8 and M9
   survived.
8. **Replay.** Replay checks an `attach:` ref the way a live write does, or a
   test shows that it already does.
9. **Documents.** These are the candidate's own module documents:
   - the reports' sentence "nothing is lost";
   - `bin/README.md:838` and the blank-rule wording, together with the
     importer's docstring;
   - `bin/ARCHITECTURE.md:83–86`, the template read;
   - `kernel/ARCHITECTURE.md:74–82`, the importer as a caller of the CLI;
   - `§5-contracts.md:314–319`, the importer's use of
     `PERRY_KERNEL_TESTING`.

   Root `ARCHITECTURE.md` and `bin/ARCHITECTURE.md` § 7 are the user's and are
   not edited here (see TASK-490).

## Out of scope
- OKR, design and ADR records (TASK-492).
- Historic prose.
- Switching any lane to the kernel.
- Writing to either project's tracked files.

## Acceptance criteria
1. For each project, the report shows equal counts per type and per status
   between the old stores and the kernel store.
2. Every old id resolves in the kernel store.
3. The next id the kernel mints for each prefix is above every id ever issued,
   purged ones included.
4. `import` refuses a store that is not empty.
5. Replaying the imported events reproduces the imported items.
6. A fresh-context reviewer, who did not write the importer, scores items 1–5
   PASS against this file (`work/reference/review.md`).

## Bound

The stores listed under Deliverable, for two projects, and the six acceptance criteria. Temporary stores only. Neither project's tracked files are written. No store and no export is created under either project's `.git/perry` or its state root.

## Changes

- 2026-09-29 — Carried DESIGN-023 decision 13's field mapping. Added § Decided 2026-09-29. The Dates rule is now one create event and at most one move per item. `Dispatch mode: manual` → `auto`. Files in scope name the one-shot `bin/` importer, and the Bound names the live-store paths it must not touch.
- 2026-09-29 — After round 1: the long-cell measurement is corrected, since 7 open rows are over 300 bytes, and option A still covers them. Two import rules added: the blank marker `—` means unset, and no move is timed before its create.
- 2026-10-07 — Round 3 added after round 1's V4 FAIL (`TASK-489-review-round1.md`): the one blank rule, ask answers, the risk state and reason, references, kernel errors, ceilings, the importer's self-checks, replay of `attach:` refs, and the candidate's own documents.
