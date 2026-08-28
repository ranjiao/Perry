# TASK-088 — the renderer, and the two cells it cannot reproduce

## The run, re-derivable

```
python3 bin/perry-tasks write            # derive the store
python3 bin/perry-tasks render > /tmp/r  # store -> BOARD.md
cmp perry/BOARD.md /tmp/r                # empty
python3 bin/perry-tasks diff --root <a gimegime-pmo copy>
#  -> {"identical": true, "rows_from_store": 41,
#      "rows_verbatim": [{"cell": "2 待核项"}], "cells_verbatim": {"Status": 4}}
```

Both run by the author of this file, not read from the implementer's report.

## Why V3 and not V4

V3 is *a reproducible run — command, inputs, output, attested by a script*, and
that is exactly what the acceptance is: `cmp` is empty or it is not. There is no
judgement for a fresh reviewer to exercise, which is what V4 buys.

The row was written V3 for this reason, and it is closed at V3 rather than
waiting for a round that would re-run the same command.

## What holds

- `cmp` empty on Perry's `BOARD.md` (85 lines, 29 rows).
- `identical: true` on a gimegime-pmo copy — 172 lines, CJK, non-`P0/P1/P2`
  headings, 41 rows.
- **The renderer can be made to print a wrong value.** Editing one stored title
  moves the rendered row and `diff` reports it. Verified independently, because
  the first implementation fell back to the file's bytes whenever the store
  disagreed — so mutating the store changed nothing and `cmp` stayed clean.
  A renderer that cannot print a wrong value cannot be shown to print a right
  one.

## What does NOT hold, and belongs to TASK-089

- **4 `Status` cells the store cannot reproduce.** The four `off_enum_status`
  cells such as `**迁移 done，占比目标 not_started**`: `status` is `""` because
  the cell carries two states in one sentence, and `status_text` is **derived,
  not stored**. The layout keeps those bytes verbatim and the report counts
  them. **Who owns them is TASK-089's decision**, and writers cannot stop
  writing the board until it is made.
- **1 verbatim row** — `| 2 待核项 |`, a first cell that is prose rather than a
  handle. `perry-task list` already reports it as `rows_with_unrecognized_id`.
- **Row order is layout, not the store.** `perry-task/list` sorts by id and
  Perry's own `## P1` runs `TASK-047` before `TASK-038`; ordering from the store
  would move two rows of the board it is meant to reproduce.

=== VERDICT ===
task: TASK-088
rung: V3
result: PASS
criteria: this file § The run, re-derivable
checked: cmp empty on Perry's board; identical:true over 41 rows on a
         gimegime-pmo copy; the store mutated and the render confirmed to carry
         the change, because the first implementation could not
not-checked: no third project; no CRLF board; the 4 Status cells and the 1
             prose row are carried verbatim rather than reproduced, and are
             handed to TASK-089 rather than resolved here
proof: (none — this is a PASS)
=== END VERDICT ===
