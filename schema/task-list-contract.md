# `perry-task list --json` — the front-end contract

> Contract: **`perry-task/list/1.2`**
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
  "contract":     "perry-task/list/1.2",   // check this before anything else
  "project_root": "/abs/path",
  "state_root":   "/abs/path",             // where BOARD.md and journal/ live
  "conformance":  { /* see below */ },     // what this board did NOT parse cleanly
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
| `id` | string | **An opaque stable string.** Conventionally `TASK-NNN`, but a real board carries ids under several project-declared prefixes, some with no number at all — a board's own `## ID prefixes` section is where a project states them. Never reused, including after close, which is the part you may depend on. **Do not parse a number out of it** or sort by a numeric suffix. |
| `title` | string | |
| `owner` | string | free text; the project's own owner model |
| `priority` | string | `P0` \| `P1` \| `P2`. May be `""` for a closed task whose creating event predates the field. |
| `status` | string | one of `schema § enums.task_status` — `not_started`, `blocked`, `in_progress`, `review`, `done`, `dropped` — **or `""`**. Markdown emphasis is stripped before matching, so a board cell of `**done**` arrives as `done`. `""` means the board did not say, or said something that is not one state; `status_text` has the cell verbatim and `conformance` says which case it was. |
| `status_text` | string | the `Status` cell exactly as written, emphasis and all. Some cells are genuinely not one state — `迁移 done，占比目标 not_started` is two, and rounding it to either is a lie about the work. |
| `track` | string | declared track name; `main` when the project declares none |
| `mode` | string | `project` \| `pipeline` \| `queue` \| `inquiry`, or `""` if no event recorded it |
| `stage` | string | non-`project` modes only; `""` otherwise |
| `stage_since` | string | `YYYY-MM-DD`; pipeline/inquiry. Dwell time is `today − stage_since`. |
| `arrived` | string | `YYYY-MM-DD`; queue mode. **Every SLA number is `today − arrived`.** |
| `parent` | string | inquiry mode: the question this was split from |
| `commitment` | string | the commitment id this row discharges |
| `next_action` | string | |
| `evidence` | string | the cell verbatim. Free text: often a comma-separated list of backticked paths, sometimes a symbol or a prose note. |
| `evidence_paths` | array | strings, each **relative to `project_root`** and each one that **exists**. Perry resolves against `state_root` and `project_root` in that order, because both conventions are live in that column on real boards and nothing in the string distinguishes them. Spans that resolve nowhere are in `conformance.evidence_not_found` rather than here — a dead link is worse than a string. |
| `verification` | string | `V1`…`V6`, or `""` if unrated |
| `group` | string | the board section this row came from, verbatim. `P0`/`P1`/`P2` for a standard board; a workstream name like `Open — 投资线` on a project that organizes its board its own way. |
| `open` | bool | **`true` unless the work is finished** — the row left the board with a `done`/`drop` event, or its status is `done`/`dropped`. Still the live/closed test; do not derive it from `status` yourself, because a row can be closed by either route. **One limit, stated because it cannot be fixed from here:** a row whose `Status` cell is empty is reported `open: true`, and Perry cannot know better. Perry's own board stages finished work under `## Done this period (leaves the board at next triage)` in a table with no `Status` column — 20 rows that are done and say nothing. `conformance.rows_with_no_status` names every one. |
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

### `conformance` — what the board did not parse cleanly

**Read this before you trust `tasks`.** Perry's own template is not what real
projects look like. A live Perry project checked while writing this organizes
its board by workstream (`## Open — 投资线`, `## Open — 工程线 · phase #004`,
`## Backbone`) with exactly one section named `P2`, tables of four and five
columns rather than six, ids in strikethrough, statuses written in the project's
own language, and a `## ID prefixes` reference table that is not work at all.

Every one of those is legitimate. This block says which of them this board has,
so a front-end can show "12 tasks, 1 row unreadable" instead of quietly
rendering 12 and dropping one.

| Key | Type | Meaning |
|---|---|---|
| `sections_read` | array | `{heading, priority, rows}` per section that yielded tasks. `priority` is `null` unless the heading is `P0`/`P1`/`P2`. |
| `sections_skipped` | array | `{heading, why, columns}` — a `## ` section with a table that has no `ID`+`Title`. Usually a reference or legend table. |
| `rows_with_unrecognized_id` | array | `{section, cell}` — a row whose first cell is prose rather than a handle. **These are not in `tasks`.** |
| `off_enum_status` | array | `{id, status}` — the cell said something, and after stripping emphasis it is still not one of the six. `status` is `""` for these and `status_text` has the original. |
| `rows_with_no_status` | array | `{id, section}` — the row's `Status` cell was empty, usually because its section's table has no `Status` column. **`open` is an assumption for these**, see below. |
| `evidence_not_found` | array | `{id, paths}` — spans in the `Evidence` cell that resolve under neither root. Usually symbols or prose, not broken links. |
| `has_event_log` | bool | `false` on any project that predates the writer. Then `created`, `updated` and `timeline` are empty for every task, and **that is not an error** — the markdown is canonical, the log is derived. |

Two consequences worth designing for rather than discovering:

- **`status` is not guaranteed to be one of the six.** The enum is what Perry
  *writes*; a board that predates the tool holds whatever a human typed. Render
  an unknown status as itself, never as a default bucket.
- **`priority` is `""` for any row outside `P0`/`P1`/`P2`**, which on a
  workstream-organized board is most of them. Group by `group` and fall back to
  `priority`, not the other way round.

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

## Changelog

One line per version. `1.x` may only add keys; a removal or a retype is a major
bump. Semantic corrections — a field that was computed wrongly — are called out
here explicitly, because "only adds keys" does not cover them and a consumer
deserves to know when a value's *meaning* changed under it.

### 1.2 — 2026-08-17

Everything here came from aiMark's first production report, measured against
three real projects rather than against this document.

- **added** `status_text` — the `Status` cell verbatim. `status` now has
  markdown emphasis stripped before matching the enum, so `**done**` arrives as
  `done`. 17 of 41 rows on one real board were emphasized, and a consumer
  trusting the enum rendered every finished task as an unrecognized state.
- **added** `evidence_paths` — the cell split into paths, resolved by Perry
  against `state_root` then `project_root`, and filtered to ones that exist.
  Both conventions were live in that column on the same board, and the
  document declared only one of them. `evidence` still carries the cell.
- **added** `conformance.rows_with_no_status` and
  `conformance.evidence_not_found`.
- **corrected** `open`. It meant "still on the board", which was true when the
  board held only `P0`/`P1`/`P2` and closing removed the row. Since 1.1 read
  every section, a project staging finished work under its own heading reported
  those rows as open — 20 of them on Perry's own board. `open` now also respects
  a terminal status. **This changes a value, not a shape**; a consumer using
  `open` as the live/closed test gets a more correct answer without a code
  change.
- **relaxed** the documented shape of `id` to an opaque stable string. Real
  boards carry several project-declared prefixes, and some ids have no numeric
  part. Stability was always the guaranteed part; the shape never was.

### 1.1 — 2026-08-17

- **added** `conformance` — what the board did not parse cleanly.
- **added** `group` — the board section a row came from, verbatim.
- **corrected** the reader to see every `## ` section holding an `ID`+`Title`
  table, not only `P0`/`P1`/`P2`. It had reported **3 tasks for a project with
  41**, two of the three lifted out of a reference table.

### 1.0 — 2026-08-17

First frozen payload.
