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
| `event` | string | which kind of event this is. **The twenty-five kinds are § The event kinds**, below — ten of them do not describe a task at all |
| `task` | string | the id this event is about — **not always a `TASK-` id, and on four kinds `""`.** § The event kinds says which, and what a consumer indexing on this key has to do about it |
| `title_then` | string | **the title as written when the event was appended.** A retitled task's earlier events still carry the old name — correct for a history view, wrong the moment you render it as the row's *current* name. `perry-task/list § title` has that one |
| `field` | string | which cell `from`/`to` describe — `status` on six events, `section`, `stage`, `track`, `title`, `summary`, `next_action`, `verification`, `evidence` or `depends_on` on the rest of the task kinds, and **`""` on the ten kinds that are not about a task** |
| `from`, `to` | string | the movement, in the `field`'s terms |
| `actor` | string | who wrote it |
| `reason` | string | populated on 16 events in this project's own log and **exposed by no contract surface until 1.0** |
| `rung`, `evidence` | string | on a close |
| `owner`, `role` | string | **on `done` and `drop` since 2026-08-18.** Events written before that carry `""`; the log is history and is not rewritten, so a role's track record starts there |
| `track` | string | the row's track |

## The event kinds

**Every kind the writer can emit.** This list is no longer kept by hand: it is
derived from `bin/perry-task` — its `TASK_EVENTS` / `SECTION_EVENTS` registers
plus every literal `"event"` written at a commit site — and compared against
this page by `tests/test_events_feed.py § TestTheDocumentedKindsAreTheWriters`.
It was a hand-kept list until 2026-08-21, by which time it had drifted by
**eleven** names, three of which this project's own log already carried.

**Ten of them are not about a task.** `## Intake`, `## User Input Queue`,
`## Cadence` and `## Top risks` are written through the same three-way commit
into the same log, so their events arrive on this feed too. `perry-task list`
folds only the task half; this surface is the log, and the log is all of it.

**So `task` is not always a `TASK-` id, and is sometimes empty.** A consumer
that indexes this feed by `task` has to handle both: grouping by `task` and
dropping the empty key silently discards every `intake`, `resolve-intake`,
`intake-sweep` and `risk-migrate` row, and grouping without reading the prefix
files a `USER-` ask under a task id that does not exist. `field` is `""` on all
ten — `from`/`to` there describe the section row's own status, which is not one
of the task cells `field` names.

### The fifteen that describe a task row

| Kind · the subcommand that writes it | `task` | What it records |
|---|---|---|
| `add` · `perry-task add` | the new `TASK-` id | a row was created |
| `route` · `perry-task route` | the minted `TASK-` id | an `## Intake` request became a task row |
| `start` · `perry-task start` | `TASK-` id | the row was picked up — `not_started → in_progress` |
| `status` · `perry-task status` | `TASK-` id | the status cell moved |
| `stage` · `perry-task stage` | `TASK-` id | the stage cell moved |
| `track` · `perry-task track` | `TASK-` id | the row changed track. The stage the move re-stamped rides on the event's own `stage` keys, not on `from`/`to` |
| `prioritize` · `perry-task prioritize` | `TASK-` id | the row moved between `## P0` / `## P1` / `## P2` |
| `retitle` · `perry-task retitle` | `TASK-` id | the title was rewritten. `title_then` on **earlier** events keeps the old one |
| `summary` · `perry-task summary` | `TASK-` id | the summary cell was written or cleared |
| `next` · `perry-task next` | `TASK-` id | the next action was rewritten |
| `rung` · `perry-task rung` | `TASK-` id | the verification rung was set |
| `evidence` · `perry-task evidence` | `TASK-` id | the evidence cell was written |
| `depends` · `perry-task depends` | `TASK-` id | `depends_on` was rewritten |
| `done` · `perry-task done` | `TASK-` id | the row closed. `rung`, `evidence`, `owner` and `role` ride along |
| `drop` · `perry-task drop` | `TASK-` id | the row closed unfinished. Same extra keys as `done` |

### The ten that describe something else

| Kind · the subcommand that writes it | `task` | What it records |
|---|---|---|
| `intake` · `perry-task intake` | **`""`** — written against the queue, not a row | an unrouted external request arrived in `## Intake` |
| `resolve-intake` · `perry-task resolve-intake` | **`""`** | an intake request was discharged `dropped` or `deferred` without becoming a task. Routing one instead emits `route` |
| `intake-sweep` · `perry-task intake-sweep` | **`""`** | discharged intake rows left the board for the journal. `count` says how many |
| `ask` · `perry-task ask` | a **`USER-`** id | a question for the user was queued in `## User Input Queue` |
| `answer` · `perry-task answer` | a **`USER-`** id | the user answered it |
| `cadence-add` · `perry-task cadence-add` | a **`CAD-`** id | a recurring item was registered in `## Cadence` |
| `cadence-done` · `perry-task cadence-done` | a **`CAD-`** id | an occurrence of it ran |
| `risk-add` · `perry-task risk-add` | an **`RX-`** id | a risk was opened in `## Top risks` |
| `risk-clear` · `perry-task risk-clear` | an **`RX-`** id | it was cleared |
| `risk-migrate` · `perry-task risk-migrate` | **`""`** | the legacy `## Top risks` bullets became table rows. `migrated` carries the ids |

**A kind not in these two tables is a kind this feed cannot emit** — and the
test above is what makes that true tomorrow rather than only today.

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

**Not a version, 2026-08-21 (TASK-171).** § The event kinds documents the
**eleven** emittable values of `event` this page never listed — `summary`,
`intake`, `resolve-intake`, `intake-sweep`, `ask`, `answer`, `cadence-add`,
`cadence-done`, `risk-add`, `risk-clear`, `risk-migrate` — and states what
`task` carries on each. **No key was added, removed or retyped**, and every one
of those kinds has been emittable since long before 1.0; three of them (`ask`,
`answer`, `intake`) are in this project's own log today. Documenting what
already ships is not a bump, so the version does not move — the same reading
`schema/task-list-contract.md`'s two *"Not a version"* notes took. `stage`,
`track` and eight others are documented and not yet exercised here, which is
also not a defect: this page describes what the tool can emit, not what one
project happened to do.

**The list is no longer hand-kept, and that is the actual change.** It went
stale by eleven names because nothing compared it to the writer;
`tests/test_events_feed.py § TestTheDocumentedKindsAreTheWriters` now derives
the emittable set from `bin/perry-task` — the `TASK_EVENTS` / `SECTION_EVENTS`
registers **and** every literal `"event"` at a commit site — and fails if the
two sets differ in either direction. A twenty-sixth kind added to the writer
reddens it on the commit that adds it.

**`tests/contract_key_parity.py` cannot see this class of drift.** KR-O2.4 was
0 before this change and is 0 after: that check compares documented *paths*
against emitted *paths*, and the kinds above are a field's **values**. An enum
can therefore go stale where a key cannot, which is why the pin above had to be
written rather than delegated to the instrument that already existed. The two
tables are also deliberately shaped so that check does **not** read them —
their first cell is `` `kind` · `perry-task <subcommand>` ``, not a bare
backticked identifier, because a first cell of nothing but backticked
identifiers is how that parser recognises a key table, and twenty-five event
names declared as payload keys would be twenty-five paths the payload does not
carry.

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
