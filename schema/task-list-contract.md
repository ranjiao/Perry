# `perry-task list --json` — the front-end contract

> Contract: **`perry-task/list/1.0`**
> Locked by `tests/test_task_writer.py § TestListContract`.
> Consumers today: aimark.

This is the one interface a program outside Perry should read task state
through. It is versioned separately from Perry itself, because its entire
purpose is to **not move when Perry's storage does**.

## Call it

```bash
"$PERRY_HOME/bin/perry-task" list --all --json --root /path/to/project
```

| Flag | Effect |
|---|---|
| `--all` | include closed and dropped tasks. **Without it you get open work only** — `BOARD.md` holds open rows and closed ones leave it, so "everything" is always a reconstruction and always needs this flag. |
| `--json` | the payload below. Without it, a human-readable table. |
| `--track <name>` | restrict to one declared track. |
| `--root <path>` | the project. Defaults to `$PERRY_PROJECT`, else walks up from the cwd. |

`list` writes nothing. It takes the same lock every write takes, so a read
never observes a half-applied change; on a contended project it may wait up to
10s and then refuse rather than return a torn view.

## Why call the tool instead of parsing `BOARD.md`

Because the second parser is the bug.

`viewer/parsers.py` and `bin/perry-task` were two parsers of one file, written
by the same project, and they disagreed silently: the writer placed cells by
resolved header name, the reader read them by position. On a board carrying one
extra column, every task's owner was reported as its track, its status as its
owner, and the open count as zero — with `perry-lint` calling the board clean,
because column order is not something the schema constrains. A front-end
parsing the markdown itself would be a third chance at exactly that.

It is also what makes a front-end survive a storage change. Whether `BOARD.md`
should stay the canonical task store at all is an open architectural question —
a quarter of the writer is markdown-format handling, and most of this migration's
blocking defects came out of that quarter. This payload is deliberately not part
of that question: whatever the answer, `list --json` keeps this shape.

## The payload

```jsonc
{
  "contract":     "perry-task/list/1.0",   // check this before anything else
  "project_root": "/abs/path",
  "state_root":   "/abs/path",             // where BOARD.md and journal/ live
  "tasks":        [ /* see below */ ],
  "open":         3,                       // counts AFTER --track filtering
  "closed":       11,
  "events":       57,                      // lines in the event log, unfiltered
  "untitled":     ["TASK-004"]             // ids with no title in any record
}
```

### A task

| Key | Type | Meaning |
|---|---|---|
| `id` | string | `TASK-NNN`. Never reused, including after close. |
| `title` | string | |
| `owner` | string | free text; the project's own owner model |
| `priority` | string | `P0` \| `P1` \| `P2`. May be `""` for a closed task whose creating event predates the field. |
| `status` | string | one of `schema § enums.task_status`: `not_started`, `blocked`, `in_progress`, `review`, `done`, `dropped` |
| `track` | string | declared track name; `main` when the project declares none |
| `mode` | string | `project` \| `pipeline` \| `queue` \| `inquiry`, or `""` if no event recorded it |
| `stage` | string | non-`project` modes only; `""` otherwise |
| `stage_since` | string | `YYYY-MM-DD`; pipeline/inquiry. Dwell time is `today − stage_since`. |
| `arrived` | string | `YYYY-MM-DD`; queue mode. **Every SLA number is `today − arrived`.** |
| `parent` | string | inquiry mode: the question this was split from |
| `commitment` | string | the commitment id this row discharges |
| `next_action` | string | |
| `evidence` | string | path, relative to `state_root` |
| `verification` | string | `V1`…`V6`, or `""` if unrated |
| `open` | bool | **`true` iff the row is still on `BOARD.md`.** This, not `status`, is the live/closed test. |
| `created` | string \| null | ISO-8601 of the `add`/`route` event; `null` if the row predates the event log |
| `updated` | string \| null | ISO-8601 of the most recent event; `null` as above |
| `timeline` | array | every event for this id, oldest first |

### A timeline entry

| Key | Type |
|---|---|
| `ts` | string — ISO-8601, seconds precision, local time, no zone suffix |
| `event` | string — `add`, `start`, `stage`, `status`, `done`, `drop`, `route` |
| `from` | string \| null |
| `to` | string \| null |
| `actor` | string \| null |

## The three rules that make it safe to code against

1. **Every key above is always present.** An unknown value is `""`, `null` or
   `[]` — never a missing key. You need no `if "owner" in task`.
2. **A key is never removed or retyped without a major bump.** `1.x` → `1.y` may
   only *add* keys.
3. **`contract` is the handle.** Check its `major` and refuse loudly on a
   mismatch rather than guessing:

   ```python
   major = payload["contract"].rsplit("/", 1)[1].split(".")[0]
   if major != "1":
       raise SystemExit(f"perry-task list contract {payload['contract']} is not supported")
   ```

## Polling

`updated` is the cheapest change signal per task; for the project as a whole,
`stat` the event log at `<project_root>/.perry/events.jsonl` — it is appended to
on every write. Both are advisories, not guarantees: **a hand-edited board
changes state and produces no event**, which is legitimate and reported rather
than refused. `bin/perry-state --json`'s `board.drift` block is what names those
rows; a front-end that wants to be honest about staleness should surface
`drift.unrecorded` rather than assume the log is complete.

## What this contract does not cover

`## Cadence`, `## User Input Queue` and `## Top risks` are board sections that
are not tasks and are not in this payload. `## Intake` is queue mode's inbox and
is likewise absent — `perry-task intake` and `route` write it, and nothing reads
it back out yet. If a front-end needs any of these, that is a new key in a `1.x`
bump, not a reason to parse the markdown.
