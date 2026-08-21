# `perry-task events --json` — `perry-events/list/1.1`

The event log's **tail**, in **log order**, with a cursor you can page on.
`--limit N` is the **newest** N events; the cursor walks **backwards** from
there into older ones. Until 1.1 the first page was the log's head while this
line said tail — see `semantics` and the Changelog.

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
  "contract": "perry-events/list/1.1",
  "semantics": [ /* below */ ],  // meaning changes, oldest minor first
  "project_root": "/abs/path",
  "events":  [ /* below */ ],
  "count":   20,          // events in THIS response
  "total":   256,         // events in the log
  "cursor":  "236:2026-08-18T21:04:11",   // the OLDEST event in this window
  "more":    true,        // there are OLDER events before `cursor`
  "rotated": false        // see below — this one matters
}
```

The first page of a 256-event log is `seq` 236 through 255 — **the end of the
log, not its start.** `seq` is the absolute position in the log and is not
renumbered per page, so a consumer reassembling pages sorts on `seq` and never
has to know which way the cursor walked.

## An event

| Key | Type | Meaning |
|---|---|---|
| `seq` | int | position in the log. Stable **until rotation**, which is what `rotated` is for |
| `ts` | string | ISO-8601, **seconds**. Ties are real and are not duplicates |
| `event` | string | `add`, `start`, `status`, `done`, `drop`, `stage`, `track`, `prioritize`, `retitle`, `next`, `rung`, `evidence`, `depends`, `route` |
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
perry-task events --limit 50 --json           # newest window is the FIRST page
perry-task events --limit 50 --since 206:2026-08-18T21:04:11 --json   # older
```

**Paging runs backwards, and that is forced rather than chosen.** If the first
page is the newest window there is nothing after it to page to; the only
direction left is older. So `cursor` is the **oldest** event in the window — the
boundary the next page ends at, exclusive, which is what keeps the pages a
partition — and `more` says whether anything sits before it. Stop when `more`
is `false`; the pages you collected, **reversed and concatenated, are the log**,
in order, each event exactly once.

The cursor is `<seq>:<ts>`. The `ts` half is not decoration: **if the event now
at that position carries a different timestamp, the log was rotated beneath
you** — lines were removed, every `seq` shifted, and the window you asked for no
longer means what it meant. That case sets `rotated: true` and restarts at the
**newest window** — where a feed with no cursor starts — **rather than silently
handing you the wrong events**, which would look like a burst of new activity.

Rotation is TASK-070's territory and is not implemented yet. The flag is here
first on purpose: a consumer written against a feed that cannot yet rotate
should not need changing on the day it can.

## The three rules

1. **Every key above is always present.** An unknown value is `""`.
2. **`1.x` → `1.y` only adds keys.**
3. **Check both halves of `contract`.** Same rule as
   `schema/task-list-contract.md § The three rules`. The major says whether you
   can parse it; **the minor says whether a value still means what it meant
   when you wrote your code**, and that is a different question. Do not refuse
   on a minor — `1.x` only adds keys, so an old consumer keeps working. What
   that guarantee does not cover is a value whose meaning was corrected, and
   that has now happened once, at 1.1. Walk `semantics` for every entry newer
   than the minor you read against.

### `semantics[]` — the entry, key by key

**Ordered oldest minor first**, which makes "everything newer than the minor I
tested against" a slice rather than a search. It is not the Changelog: the
Changelog records every shipped minor including the ones that only added keys,
while this array carries **only the minors under which an existing value
changed meaning** — the strictly smaller set a working consumer must act on.
Same shape as `perry-task/list § semantics[]`, on purpose.

| Key | Type | Meaning |
|---|---|---|
| `version` | string | the minor the change shipped in, `"1.1"`. A string, not a number: `1.10` sorts below `1.9` numerically and above it correctly |
| `fields` | array | the payload paths whose meaning moved, as strings, in this payload's own notation |
| `note` | string | prose, always populated: what the value used to mean, what it means now, and what a consumer that hardcoded the old meaning does wrong. Meant to be shown, not branched on |

## Changelog

### 1.1 — 2026-08-21 (TASK-168)

**The first page is now the log's TAIL, and the cursor pages backwards.** No
key was removed or retyped, and the change needed none added: `events[]`
returns **different rows** under the same key with the same type, which is the
one case rule 2 does not cover and rule 3 and `semantics` exist for. It is
announced there rather than flipped silently.

Until 1.1 the first page was the log's **head** while this page's first line,
its § Why this exists, `perry-task events --help` and this page's own paging
example (`# newest window is the FIRST page`) all promised the tail. On a
733-event log `events --limit 6` returned the six **oldest** events in the
project, five days stale, with nothing in the payload saying so — a consumer
that trusted the documentation shipped a "recent activity" panel of the oldest
events it had. The one that caught it worked around it by requesting a window
larger than any real log, **437 KB per project**, and slicing the end itself.
**The implementation was what drifted from the design, not the other way
round**, so it is the implementation that moved.

`cursor` was the newest event in the window and is now the oldest one; `more`
asked whether events followed the cursor and now asks whether older ones
precede it. `seq` is unchanged and still absolute.

Also **adds `semantics`** — which is a plain `1.x` key addition, and is the
key the change above is reported in.

### 1.0 — 2026-08-18

First version. `reason` becomes readable; `owner` and `role` appear on closes
from this date forward.
