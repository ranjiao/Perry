# TASK-089 — `perry-task` writes the store, not the board

> Source: `perry/decisions/ADR-006-task-store-is-not-the-log.md`, `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`, and `perry/evidence/2026-08/TASK-089-v4-review.md`
> Dispatch mode: auto
> Executor: opencode-subagent (the task requires repository edits, adversarial regression tests, and no external CLI session)
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P0
- **Attribution**: P-O1.1

### Deliverable

1. One shared definition decides which lines are task rows. `Board.find`, every
   section/table walker, and `perry_store.plan` use it. A second table after
   prose or a subheading cannot lose a typed value or mint a record whose id is
   the literal header `ID`.
2. Duplicate task ids are refused before any task mutation. The row checked by
   the typed-status gate and the row stored by `cmd_list` cannot differ.
3. The canonical store + journal transition cannot leave one side committed
   and the other absent without a deterministic recovery path. Pre-write and
   rename failures are concise refusals, staged files are cleaned, and the
   implementation no longer claims multi-file atomicity it does not provide.
4. Store field types are validated before sorting or comparison. In particular,
   a non-integer `order` produces a lint finding and cannot terminate
   `perry-lint` or `perry-tasks diff`.
5. Every writer of `perry/tasks.jsonl` takes the project lock and uses staged
   replacement. Recovery guidance names the authoritative direction:
   `perry-tasks render --write` regenerates `BOARD.md`; board-to-store import is
   explicit and destructive. `perry-migrate` cannot leave the store stale or
   restore only the rendered board.
6. Writes preserve the existing target file mode rather than resetting tracked
   files to `0600`.
7. The read-side cutover remains TASK-090. This task may read the current board
   to construct a write, but it must not silently discard an already-reported
   store edit; any temporary limitation is explicit and test-locked.

### Verification — V4

1. Add behavioral regressions for review findings A5-A7, B1-B2, C, D, and E in
   `perry/evidence/2026-08/TASK-089-v4-review.md`. Each test is demonstrated to
   fail when its fix is removed; happy-path assertions alone do not count.
2. A forced failure between the store and journal replacements either leaves
   both old values visible or is repaired deterministically on the next run.
   No orphaned temporary file remains and no raw traceback reaches the user.
3. A board containing a second table, a repeated header, or a duplicate id is
   refused or represented losslessly; `perry-tasks diff` and `perry-lint`
   cannot both report clean while a typed value differs.
4. Wrong-typed `order` values yield findings from both the linter and diff path,
   with normal JSON output and no process-level TypeError.
5. `perry-tasks write` obeys the project lock; `perry-migrate` apply + restore
   keeps `tasks.jsonl` and `BOARD.md` mutually consistent.
6. Run:
   - `python3 tests/parallel test_store_is_the_write_target test_store_drift test_task_writer test_migrate`
   - `python3 tests/parallel test_contract_invariance`
   - `python3 tests/parallel`
   - `python3 bin/perry-lint`
7. A fresh V4 reviewer repeats destructive cases only on disposable copies and
   records what was not checked.

### Dependencies

- TASK-088 — done. Its byte-identical renderer is the projection path this task
  writes after committing the store.

### Out of scope

- TASK-090's full read-side cutover from `BOARD.md` to `tasks.jsonl`.
- TASK-092's OKR/config stores.
- Changes to `state-schema.json`, `claims[]`, host skill installation, public
  publishing, `git push`, or files in another project.
- Closing TASK-089. A successful dispatch moves it to `review`; fresh V4 is the
  close gate.

## Notes

The previous V4 found green tests around false guarantees. Prefer one shared
mechanism plus mutation-sensitive tests over another list of patched call sites.
