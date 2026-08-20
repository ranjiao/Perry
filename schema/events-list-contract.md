# `perry-task events --json` — `perry-events/list/1.0`

The event log's **tail**, in **log order**, with a cursor you can page on.

## Why this exists rather than `--limit` on `list`

`list` was the obvious place and it is the wrong one. **Three of its fields are
defined relative to the payload**: `blocks` is *"ids in this payload whose
`depends_on` names this row"*, `depends_on_unknown` is the ids this payload does
not carry, and `next_action_cites_closed` says outright that only ids in this
payload are resolved. **Paging `list` silently shortens all three**, so the same
consumer reading the same field gets a different answer per page — the class of
change `semantics` exists to report, and it has already happened once, at 1.5.

Measured before building, which is what makes a second surface worth its cost:
the last 20 events on Perry's own board span 10 tasks sitting at positions 24
through 79 of 80 by id. **Any paging key except `updated` returns the wrong
events** — and `updated` is exactly what a task-shaped payload cannot promise
once it is filtered. Without `--all` the feed is wrong today, because a close is
what makes a row leave the board; with `--all` it reconstructs every closed task
from journal plus log to answer a question about the log's tail.

## Order

**Log order. Not sorted, and do not re-sort.** `ts` has seconds precision and
ties are real — two drops in this project's log share one second.
`perry-task/list` promises array order only *within one id*, so a flattened
cross-task stream has no authoritative order at all unless the log's own order
is the answer. It is.

## The payload

```jsonc
{
  "contract": "perry-events/list/1.0",
  "project_root": "/abs/path",
  "events":  [ /* below */ ],
  "count":   20,          // events in THIS response
  "total":   256,         // events in the log
  "cursor":  "19:2026-08-18T21:04:11",
  "more":    true,        // there are events after `cursor`
  "rotated": false        // see below — this one matters
}
```

## An event

| Key | Type | Meaning |
|---|---|---|
| `seq` | int | position in the log. Stable **until rotation**, which is what `rotated` is for |
| `ts` | string | ISO-8601, **seconds**. Ties are real and are not duplicates |
| `event` | string | `add`, `start`, `status`, `done`, `drop`, `stage`, `prioritize`, `retitle`, `next`, `rung`, `evidence`, `depends`, `route` |
| `task` | string | the id this event is about |
| `title_then` | string | **the title as written when the event was appended.** A retitled task's earlier events still carry the old name — correct for a history view, wrong the moment you render it as the row's *current* name. `perry-task/list § title` has that one |
| `field` | string | which cell `from`/`to` describe — `status` on six events, `section`, `stage`, `title`, `next_action`, `verification`, `evidence` or `depends_on` on the rest |
| `from`, `to` | string | the movement, in the `field`'s terms |
| `actor` | string | who wrote it |
| `reason` | string | populated on 16 events in this project's own log and **exposed by no contract surface until 1.0** |
| `rung`, `evidence` | string | on a close |
| `owner`, `role` | string | **on `done` and `drop` since 2026-08-18.** Events written before that carry `""`; the log is history and is not rewritten, so a role's track record starts there |
| `track` | string | the row's track |

## Paging, and the one thing that can go wrong

```
perry-task events --limit 50 --json          # newest window is the FIRST page
perry-task events --limit 50 --since 49:2026-08-18T21:04:11 --json
```

The cursor is `<seq>:<ts>`. The `ts` half is not decoration: **if the event now
at that position carries a different timestamp, the log was rotated beneath
you** — lines were removed, every `seq` shifted, and the window you asked for no
longer means what it meant. That case sets `rotated: true` and restarts from the
beginning **rather than silently handing you the wrong events**, which would
look like a burst of new activity.

Rotation is TASK-070's territory and is not implemented yet. The flag is here
first on purpose: a consumer written against a feed that cannot yet rotate
should not need changing on the day it can.

## The three rules

1. **Every key above is always present.** An unknown value is `""`.
2. **`1.x` → `1.y` only adds keys.**
3. **Check both halves of `contract`.** Same rule as
   `schema/task-list-contract.md § The three rules`, which is also where a
   `semantics` array would appear if a value here ever changed meaning.

## Changelog

### 1.0 — 2026-08-18

First version. `reason` becomes readable; `owner` and `role` appear on closes
from this date forward.
