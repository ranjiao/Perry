# TASK-039 — `## User Input Queue` gets a writer

> Rung: V3 (reproducible run)
> Decided 2026-08-17: all three writerless board sections get tools, under one
> rule — the tool owns the row and every computed cell, the agent owns the
> prose cell, exactly as `## Intake` already works.

## The defect

The section had readers (`perry-state`, the standup dashboard) and no writer.
Two consequences, both live on Perry's own board when the work started:

| | |
|---|---|
| `Idle` on both rows | `—` — the one field the queue exists for, unfilled |
| `user_input_queue.count` | `2`, with both rows carrying `**answered 2026-08-16: …**` |

The second is the worse one: that count is the single number in the whole
payload a user is meant to act on, and it was reporting work they had already
done.

## What shipped

`perry-task ask` / `answer`, plus `Board.ensure_section_columns` and
`Board.find_section_row`.

**`Idle` was the wrong column.** A stored age is stale the next morning. Perry
had already solved this twice — `Stage since` and `Arrived` both store a date
and compute the age — and `Idle` was the one place that stored the derived
value instead. `~/proj/gimegime-pmo` had independently dropped the column from
its board for the same reason, and the schema still required it, so a project
was carrying a lint error for being right.

`Idle` is now optional and still read where present; `Asked` is what the tool
writes; `idle_days` is computed at read time.

## Verification performed

```
ask with no --needed        → refused
ask ×2                      → two ids minted in order, section created AFTER P0
answer the first            → status carries the date and the decision
answer again                → refused ("already answered")
ask after an answer         → the next number, no id reuse
ask --arrived 2020-01-01    → oldest chosen by date, idle_days > 2000
board with a 4-col section  → gains `Asked`, existing row widened, next id
                              minted above the pre-existing one
perry-lint                  → clean on Perry; gimegime-pmo 61 → 60
```

Three behaviours verified by reverting them: the idle computation, the column
widening, and the name-resolved parse.

## Found while building it

- **The UIQ parser read columns positionally** — cell 3 of a five-column row
  was assumed to be `Idle`, so a board storing `Asked` there would report every
  request as zero days old. **Third location of this defect**, after
  `_parse_task_table` and the reader/writer split that one caused.
- **`ensure_columns` had no sibling for named sections.** A board that already
  had the section would have had the date dropped silently — the way
  `--commitment` was lost.
- **`ensure_section` always inserted before `## P0`.** Correct for `## Intake`,
  which reads above the work it becomes; wrong here.

## One thing done wrong and reverted

A `Status` enum was added to the schema — while writing the rule that reading
must be tolerant. `gimegime-pmo` went 61 → **67** errors, because that column
holds prose there (`✅ done 6/4`, `**用户线下已沟通处理（6/8）**`). Reverted; the
tool writes a structured status and the reader accepts whatever is on the board.
Net 61 → 60.

## Not done here

`user_input_queue` is still exposed only through `perry-state --json`, which is
not a frozen contract. Putting it in `perry-task/list` would be a `1.x`
addition and a separate decision — aiMark has not asked for it.
