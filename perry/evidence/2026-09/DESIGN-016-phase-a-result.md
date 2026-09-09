# DESIGN-016 phase A — result

> Rows: TASK-359, TASK-360, TASK-361, TASK-367, and the two opened for A5 / A6.
> Branch: `bin-contract-phase-a`, commit `871b8699`. Base: `4ebc0693`.
> Date: 2026-09-09 · Rung claimed: V3 (measured, reproducible), V4 pending review.

## What landed

| Item | Claim | Where it is asserted |
|---|---|---|
| A1 | `--root` beats `$PERRY_PROJECT` in every project-scoped tool | `TestTheFlagBeatsTheEnvironment`, 3 cases |
| A2 | An undeclared token exits 2; `-h` prints from any position and runs nothing | `TestAnUndeclaredTokenIsRefused` (5), `TestHelpPrintsAndRunsNothing` (2) |
| A3 | `--dry-run` and `--json` on the writers, and they touch nothing | `TestTheWritersTakeDryRunAndJson` (3) |
| A4 | `perry-task add --design` writes the edge, and refuses an id with no document | `TestAddWritesTheDesignEdge` (3) |
| A5 | A render that cannot place every record refuses; the success line counts lines changed | `TestARenderThatCannotRestoreRefuses` (4) |
| A6 | A refusal is one line and exit 1, never a traceback | `TestARefusalIsOneLine` (2) |

All in `tests/test_bin_argument_contract.py`, 22 tests.

## One resolver, one scanner

`bin/lib/__init__.py` gained `resolve_project_root` and `scan_argv`.
`resolve_project_root` calls `viewer/parsers § _resolve_project_root`'s walk
rather than copying it — `tests/test_project_root.py` exists because that walk
had two bodies once. `perry-diagnose` passes `walk=False`: it judges the
directory it is pointed at, so falling through to an ancestor would have it
answer about a project the caller did not name.

`scan_argv` reads the whole vector before anything dispatches. That is what
makes `-h` safe in any position: `perry-tasks render --write --help` used to
run the render and then not print help at all.

## The measurements this phase was opened on, re-run after the fix

| Command | Before | After |
|---|---|---|
| `perry-tasks build --root <empty>` with `$PERRY_PROJECT` set elsewhere | reported the other project's records | reports the named project's |
| `perry-tasks render --root <copy> --write`, 151 task rows deleted | `rendered … from 399 stored record(s)`, exit 0, 0 restored | exit 1, names the 151 it cannot place, writes nothing |
| `perry-tasks render --write` with no `BOARD.md` | Python traceback | `perry-tasks: refused — no BOARD.md at …`, exit 1 |
| `perry-tasks build --root . --totally-bogus` | exit 0, full payload | exit 2, names the token |
| `perry-diagnose --root . --max-files twenty` | exit 0, silently kept 20,000 | exit 2 |
| `perry-task add --design DESIGN-016` | `design_refs: []` | `design_refs: ["DESIGN-016"]` |

## Two contracts moved, deliberately

**`perry-diagnose` can now exit 2.** `bin/README.md:86` says it "always exits
`0` — an absent signal is a finding, not an error". That stays true of
findings and is now false of a bad invocation. The sentence belongs to D1.

**`intake-render --write` refuses where it used to write.** `## Intake` is
keyed on position, so a hand-deleted row shifts every later row up. The render
then filled row *n* from record *n*: the deleted request's text came back into
the row that used to hold the next one, and the LAST record had no row left and
was dropped from the board. Measured: store 4 records, board 3 rows, exit 0.
The next honest `intake-write --from-board` would then have deleted that fourth
record from the store — the shrink `USER-906` was answered with an invariant
against. `tests/test_intake_store` asserted the old behaviour by checking that
the TEXT came back, not that the record survived; it now asserts the refusal.

The refusal asks its question of the render OUTPUT rather than of the board on
disk, because the two registers disagree: task rows are filled in place and
cannot be restored, `## Intake` is rebuilt from records and can be. Refusing on
the on-disk drift would have broken a register whose recovery works.

## Found while verifying, and fixed here

`tests/test_slow_selector § _select` drives `tests/parallel.main()` in-process,
and two of its cases pass `--record` — which writes the LIVE
`tests/durations.json`, with the stub's canned `sec: 0.01`. Measured on
`65780a73`: 123 of 123 real module times replaced by `0.01`, stamped
`tests/parallel --record -j 8` by a run that passed no such flag. Step 0's tree
guard reported it on every full run; it was misattributed once to a concurrent
session before anyone read the call. `DURATIONS` is now redirected to a temp
file for those cases, and `tests/parallel` no longer raises printing a path
outside the tree.

Two tests were passing for the wrong reason and were corrected rather than
relaxed: the intake one above, and `test_last_updated_header`'s byte-compare,
which called `render --byte-compare` — a flag that never existed, so the run
rendered to stdout and exited 0 whatever the stamp had done.

## Suite

`bash tests/run` on `871b8699`: 120 modules, 3375 tests, one module red —
`test_contract_key_parity`'s two, which reproduce on `main` alone and are the
baseline `83e6ce86` recorded. Tree guard clean. `tests/durations.json`
re-recorded so the new module is listed rather than sorting as `inf` by
accident.

## Not done here

`bin/README.md` is untouched. Its eight false statements, plus the
`perry-diagnose` sentence above, are D1's.
