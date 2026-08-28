# TASK-195 — the risks store was built all along; only the command had not run

**Closed 2026-08-28 without a dispatch.** The row was opened an hour earlier as
*"perry/risks.jsonl … has never existed"*, and the deliverable I wrote for it
named four commands to build. **All four already existed.**

## What I got wrong, twice, in the same place

`USER-016`'s answer (2026-08-21) records *"cmd_risks_write was never built"*.
I repeated that last night in `TASK-118`'s result record and again this morning
in the handoff, as the reason `risks.jsonl` was absent.

**I was checking `bin/perry-task` — the row tool. The risks commands live in
`bin/perry-tasks` — the store tool.**

```
grep -c cmd_risks_write  bin/perry-task    → 0
grep -c cmd_risks_write  bin/perry-tasks   → 2
```

Singular and plural, one letter apart, and I never noticed I was in the wrong
file. It is the same failure as grepping a name instead of a call: **the check
answered a different question from the one I asked, and returned a number, so
it looked like an answer.**

## What was actually true

```
perry-tasks risks-build    derive the store; write nothing
perry-tasks risks-render   the store → `## Top risks`
perry-tasks risks-write    --from-board, the one-way import
perry-tasks risks-diff     render and byte-compare
```

`risks-build` returned **4 records** on the first run, with no arguments.

## The gate the tool declares for itself, run before the write

`bin/perry-tasks:22`: *"`risks-diff` is the gate the migration has to pass
**before** a field the store owns is trusted."*

```
cells_verbatim                      {}
cells_wearing_decoration            {}
cells_the_store_and_board_disagree_on  []
rows_out_of_stored_order            {}
identical                           true
```

Byte-clean, so the import was safe to run.

## Result

```
perry-tasks risks-write --from-board   → 4 risk record(s)
BOARD.md sha256   3864cc28…  identical before and after
risks-diff        source: store · identical: true
```

`perry-lint`'s standing warning is gone and replaced by a positive reading:

```
before   · no `risks.jsonl` — drift against the risks store is unchecked, not clean
after    · risks store: 4 record(s), 0 risk(s) drifted
```

**All five stores `claims[]` declares now exist** — `tasks.jsonl`, `okr.jsonl`,
`risks.jsonl`, `.perry/config.jsonl`, `.perry/events.jsonl`. Three of the five
were created today.

## Reversal

`perry-tasks risks-render --write` puts the section back from the store. The
one-way part is the import, not the decision.

## What this leaves for TASK-094's other rows

Three storeless registers remain — `## Intake` (TASK-196), `## User Input Queue`
(TASK-197), `## Cadence` (TASK-198). **Check `bin/perry-tasks` before assuming
any of them needs building.** That is the whole lesson of this row.
