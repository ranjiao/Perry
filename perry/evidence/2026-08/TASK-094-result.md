# TASK-094 — closed 2026-08-28, on a rescoped verification the user approved

**Eight days at `review`** (since 2026-08-20T19:50), gating TASK-050, TASK-067,
TASK-095 and — through TASK-095 — TASK-099. Four of the eight open rows below
TASK-100 traced to this one.

## What it asked for, and why that number was never reachable

> *verification item 1 asked for **0 call sites** and `BOARD.md` keeps 13 splits*

`viewer/parsers.py` still has **13** `split_row` calls today, unchanged. But the
number was measuring the wrong thing, and the code says so in two places.

### The three stores: already at zero, and guarded

`parse_board`'s own docstring:

> `tasks` is the task store's records. **When it is given, no task row is read
> out of `text`** … When it is `None` the project has no store and every
> register is parsed, **which is adoption and is the one caller that still needs
> a header rule here.**

Verified per call site rather than taken from the docstring — **every**
`_parse_task_table` call is behind `tasks is None`:

```
1019 · 1022 · 1025   if tasks is None
1044                 inside  if tasks is None
1049                 elif tasks is None
1610                 in _parse_backbone, reached only via backbone_chunk,
                     which is set only inside  if tasks is None
```

**So for the three stores the substantive goal is met**: `tasks.jsonl`,
`okr.jsonl` and — since this morning — `.perry/config.jsonl` all exist, and with
a store present zero task rows are read out of markdown.

### The remaining 13 serve two things TASK-094 was never meant to delete

**The adoption reader.** A project with no store has to be read *somehow*, and
deleting that path deletes adoption. TASK-050's own note said this in different
words: *"re-scope to the adoption reader"*.

**Four registers for which `BOARD.md` is not a projection — it is the record.**
`bin/perry-task:4111` states it plainly:

> **The queue has no store: the board section IS the record**, and `USER-` ids
> in `tasks.jsonl` are references a task makes, not rows.

```
2  _parse_cadence      ## Cadence
2  _parse_user_input   ## User Input Queue
1  _parse_intake       ## Intake            (46 rows live only here)
1  _has_risk_header    ## Top risks         (risks.jsonl declared, never built)
```

## The finding this closes on, and it is bigger than the row

**`perry/BOARD.md` carries two truth models in one file.** Its task table is a
rendered projection of `tasks.jsonl` — a hand edit there is drift. Its
`## Intake`, `## Cadence`, `## User Input Queue` and `## Top risks` sections
**are the canonical record** — a hand edit there is the only way to write them.

`perry-lint` reports *"188 record(s), 0 row(s) drifted"* about the first and
says nothing about the second, because there is nothing to compare against. So
ADR-007's guarantee — *a hand edit to a rendered file is reported rather than
honoured* — is **true of part of a file and false of the rest of it**, with no
marker at the boundary.

## Decision

**The user rescoped this row on 2026-08-28**: verification item 1 is met for
the three stores it names, and building stores for the four storeless registers
is separate work rather than this row's unstated precondition.

Closed at **V3** on the measurement above. Opened in its place: one row per
storeless register.

**This unblocks TASK-050, TASK-067 and TASK-095**, and TASK-099 behind
TASK-095 — the four rows that had been waiting eight days on a number that
could not be reached.
