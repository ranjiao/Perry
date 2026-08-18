# `perry-task list --json` — the front-end contract

> Contract: **`perry-task/list/1.8`**
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
  "contract":     "perry-task/list/1.6",   // check this before anything else
  "project_root": "/abs/path",
  "state_root":   "/abs/path",             // where BOARD.md and journal/ live
  "conformance":  { /* see below */ },     // what this board did NOT parse cleanly
  "intake":       { /* see below */ },     // queue mode's inbox, by position
  "risks":        { /* see below */ },     // `## Top risks`, open ones
  "asks":         { /* see below */ },     // `## User Input Queue` — needs-you
  "drift":        { /* see below */ },     // board vs. the record of how it got there
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
| `mode` | string | `project` \| `pipeline` \| `queue` \| `inquiry`. **Derived** from this row's `track` and `.perry/config.md § Tracks`, never stored — a project with no track register reports `project` for `main`, and a row on a track the register does not declare reports `""`. It was read out of the event log until a review found that `route`-created rows shipped `""` on exactly the mode where routing is normal, and that deleting the derived-and-disposable event log blanked it for every row. |
| `stage` | string | non-`project` modes only; `""` otherwise |
| `stage_since` | string | `YYYY-MM-DD`; pipeline/inquiry. Dwell time is `today − stage_since`. |
| `arrived` | string | `YYYY-MM-DD`; queue mode. **Every SLA number is `today − arrived`.** |
| `parent` | string | inquiry mode: the question this was split from |
| `commitment` | string | the commitment id this row discharges |
| `next_action` | string | |
| `evidence` | string | the cell verbatim. Free text: often a comma-separated list of backticked paths, sometimes a symbol or a prose note. |
| `evidence_paths` | array | strings, each **relative to `project_root`** and each one that **exists**. Perry resolves against `state_root` and `project_root` in that order, because both conventions are live in that column on real boards and nothing in the string distinguishes them. Spans that resolve nowhere are in `conformance.evidence_not_found` rather than here — a dead link is worse than a string. **Resolved for closed rows as well as open ones** — it was not until 1.5, and a closed row's evidence is the document that justifies the close, which is the one a reader most wants to open. |
| `verification` | string | `V1`…`V6`, or `""` if unrated |
| `role` | string — the declared role accountable for this row, or `""`. **Required once the project declares any `.perry/roles/*.md`, absent otherwise** (1.8). A project with no role cards is never asked for one and never refused for omitting one, which is DESIGN-006's Goal 7. |
| `group` | string | the board section this row came from, verbatim. `P0`/`P1`/`P2` for a standard board; a workstream name like `Open — 投资线` on a project that organizes its board its own way. |
| `open` | bool | **`true` unless the work is finished** — the row left the board with a `done`/`drop` event, or its status is `done`/`dropped`. Still the live/closed test; do not derive it from `status` yourself, because a row can be closed by either route. **One limit, stated because it cannot be fixed from here:** a row whose `Status` cell is empty is reported `open: true`, and Perry cannot know better. Perry's own board stages finished work under `## Done this period (leaves the board at next triage)` in a table with no `Status` column — 20 rows that are done and say nothing. `conformance.rows_with_no_status` names every one. |
| `depends_on` | array | the ids this row waits on, verbatim from its `Depends on` cell, in cell order. **Opaque handles, like `id`** — an entry may name a task that is closed (that is what a satisfied dependency looks like), or a `DESIGN-`/`ADR-` id no board carries at all. `[]` when the row declares nothing, which on a board that predates 1.6 is every row. |
| `blocked_by` | array | the subset of `depends_on` that is **not known-finished** — an id whose task is still open, or an id this payload does not carry. An id Perry cannot see counts as unsatisfied: *"I do not know"* is not *"it is done"*, and reporting the row ready is the one error that sends somebody to work on something still blocked. |
| `blocks` | array | the reverse edge — ids in this payload whose `depends_on` names this row. So *"what does closing this free up"* is a lookup, not a scan. |
| `startable` | bool | **the field a dashboard sorts on.** `true` when the row is `open`, its own `status` is not `blocked` or `review` (both mean somebody else has the ball), and `blocked_by` is empty. This is served so you never walk the graph yourself. |
| `created` | string \| null | ISO-8601 of the `add`/`route` event; `null` if the row predates the event log |
| `updated` | string \| null | ISO-8601 of the most recent event; `null` as above |
| `timeline` | array | every event for this id, oldest first |

**The edge is one hop, deliberately — not the transitive closure.** If A waits
on B and B waits on C, then `A.blocked_by == ["B"]` and nothing more. That is
not a simplification: A becomes startable the moment B closes, and B's own
history is not A's business. So `blocked_by`, `blocks` and `startable` are
exact, and there is no closure a consumer is missing.

**Computed over the whole task set, before `--track` and `--all` filter it.** A
row you filtered out still blocks the rows that name it. A `blocks` list that
changed with your flags would be a different graph per query.

A dependency is written by `perry-task depends <ID> --on "TASK-050, TASK-051"`,
by `perry-task status <ID> --status blocked --on …`, or by `add --depends`. It
lives in a `Depends on` **board cell** — not in the event log, which is derived
and disposable, and not in the journal's definition block, which is append-only
and cannot record a dependency being satisfied. A cycle is refused at write
time; a cycle already on a hand-edited board is **reported, never refused** —
see `conformance.dependency_cycles`.


### A timeline entry

| Key | Type |
|---|---|
| `ts` | string — ISO-8601, seconds precision, local time, no zone suffix |
| `event` | string — `add`, `route`, `start`, `stage`, `status`, `prioritize`, `retitle`, `next`, `rung`, `evidence`, `depends`, `done`, `drop` |
| `from` | string \| null — **see `field` for what it refers to** |
| `to` | string \| null — same |
| `field` | string — **what `from`/`to` refer to on this event** (1.7) |
| `actor` | string \| null |

**`field` exists so you need no hardcoded set of special cases.** `from`/`to`
are a status transition on most events and something else on the rest, and the
consumer that discovered this had written
`SECTION_MOVE_EVENTS = new Set(["prioritize"])` — a set that goes wrong the day
Perry adds a second such event, silently, with nothing in the payload to say so.

Its value, per event:

- **`status`** — on `add`, `route`, `start`, `status`, `done`, `drop`. A status value.
- **`section`** — on `prioritize`. A **board section**: `P2` → `P1`, or a project's own heading such as `Open — 工程线`.
- **`stage`** — on `stage`. A stage from the track's declared vocabulary.
- **`title`** — on `retitle`. The row's title.
- **`next_action`** — on `next`. The next-action cell, often several hundred characters of prose.
- **`verification`** — on `rung`. A rung, `V0`–`V6`.
- **`evidence`** — on `evidence`. The evidence cell.
- **`depends_on`** — on `depends`. The dependency cell.

The map's keys are asserted equal to the writer's own event set, so an event
cannot ship without declaring what its pair means. The ask that produced this
proposed `status` for everything except `prioritize`; that would have been
false for `retitle`, `next` and `rung`, and a wrong word in the field whose job
is to stop you guessing is worse than no field.

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
| `evidence_not_found` | array | `{id, paths}` — spans in the `Evidence` cell that resolve under neither root. Usually symbols or prose, not broken links. Covers open and closed rows alike, ordered by `id`. Together with `evidence_paths` this is the pair that lets you tell **"the file is gone"** from **"Perry did not look"**: a row whose cell names something reaches exactly one of the two, never neither. |
| `next_action_cites_closed` | array | `{id, cites, status}` — an open row whose `Next action` points at a task that has since closed. **Only ids in this payload are resolved**: `DESIGN-`, `ADR-` and `USER-` ids appear in these cells constantly and are not checked, because reporting "cites nothing closed" while skipping three id families would claim more than the data supports. |
| `rows_with_no_computable_age` | array | open ids with **no event and no date cell**, so `today − anything` is undefined for them. Every staleness rule is "idle ≥ N days", so these read as fresh forever. On Perry's own board this was **6 of 9 open rows** — the ones written before the tool existed. |
| `depends_on_unknown` | array | `{id, unknown}` — dependency ids this payload does not carry, ordered by `id`. Not an error and not refused at write time: a dependency **must** be able to name a closed task, or every satisfied dependency would have to be deleted from the record to be written in the first place, and `DESIGN-`/`ADR-` ids are legitimate here too. This is where a typo shows up. |
| `dependency_cycles` | array | arrays of ids, each a loop found in the declared edges, e.g. `[["A","B","A"]]`. Every row in one waits forever and none is `startable`. The write path refuses to create one; a board is hand-editable by design, so the reader reports what it finds rather than refusing to answer. |
| `blocked_without_dependency` | array | open ids whose `status` is `blocked` and whose `depends_on` is empty — the row says it is stopped and does not say on what. **The migration worklist**: their dependency is still in prose somewhere no program can read. On Perry's own board this is every blocked row today. |
| `has_event_log` | bool | `false` on any project that predates the writer. Then `created`, `updated` and `timeline` are empty for every task, and **that is not an error** — the markdown is canonical, the log is derived. |

Two consequences worth designing for rather than discovering:

- **`status` is not guaranteed to be one of the six.** The enum is what Perry
  *writes*; a board that predates the tool holds whatever a human typed. Render
  an unknown status as itself, never as a default bucket.
- **`priority` is `""` for any row outside `P0`/`P1`/`P2`**, which on a
  workstream-organized board is most of them. Group by `group` and fall back to
  `priority`, not the other way round.

### `intake` — queue mode's inbox

`route <n>` and `resolve-intake <n>` act on a row **position**, and until 1.4
the only way to get one was to open `BOARD.md` and count — twenty lines below
the rule forbidding exactly that.

| Key | Type | Meaning |
|---|---|---|
| `rows` | array | one entry per intake row, in board order; fields below |
| `undischarged` | int | rows still waiting for an outcome — what triage step 0 works through |
| `oldest_undischarged` | int \| null | the `n` of the longest-waiting undischarged row |

An intake row:

| Key | Type | Meaning |
|---|---|---|
| `n` | int | the row's position — **the number `route` and `resolve-intake` take** |
| `arrived` | string | `YYYY-MM-DD`, carried onto the task when routed |
| `request` | string | the asker's words |
| `outcome` | string | `routed → TASK-NNN`, `dropped … — reason`, `deferred … — condition`, or `—` |
| `discharged` | bool | an outcome has been recorded. A row takes exactly one. |
| `age_days` | int \| null | `today − arrived` |

Absent `## Intake`, `rows` is empty and the counts are zero. Not every project
is queue-shaped, and that is not an error.

**Discharged rows stay until they are swept.** `perry-task intake-sweep` moves
them into the journal with their `Outcome` intact. That rule lived in
`modes/queue.md` and nothing implemented it, which mattered because the same
file rests its overflow argument on it: intake pressure is supposed to mean
*taking on more than you discharge*, not *having discharged a lot*.

### `risks` — `## Top risks`, the open ones

Written by `perry-task risk-add` / `risk-clear`, and readable until 1.6 only
through `perry-state --json`, **the one payload that carries no version at
all**.

| Key | Type | Meaning |
|---|---|---|
| `items` | array | the open risks; fields below |
| `open` | int | `len(items)` |
| `cleared` | int | risks in the section that are over — struck through, or a `Status` cell that says so |
| `source` | string | `table` \| `bullets` \| `none`. The two forms carry different amounts of truth and you are entitled to know which you got. |

A risk:

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the `RX-NNN` `risk-add` minted — and **`""` on a bullet**, which has no id. It used to be the first word of somebody's sentence, or worse, the severity letter. |
| `title` | string | the risk statement, with any leading severity marker and list punctuation removed |
| `severity` | string | `top` \| `watch` \| `accept` \| `resolved` — the **stance**, what was decided about the risk, read from words like `TOP RISK` and `ACCEPT`. Not a magnitude. |
| `severity_text` | string | the **magnitude marker the project wrote**, verbatim: `H`, `M`, `L`, `高`/`中`/`低`, `🔴`. `""` when the line carries none, which is most of them. |
| `severity_rank` | string | that marker normalized — `high` \| `medium` \| `low` \| `""` — so you can sort without a marker table of your own. |
| `source` | string | `table` \| `bullets`, per row |
| `opened` | string | `YYYY-MM-DD` on a table row; `""` on a bullet |
| `age_days` | int \| null | `today − opened`. `null` on a bullet, which carries no date — the honest answer rather than a zero you would read as "raised today". |
| `status` | string | the `Status` cell verbatim; `""` on a bullet |
| `cleared_on` | string | `YYYY-MM-DD` parsed out of a cleared status |
| `meta` | string | the source line, whole |

### `asks` — `## User Input Queue`, the **needs-you** list

The most decision-relevant section on a board, and until 1.6 the one behind the
unversioned tool. Written by `perry-task ask` / `answer`. **Answered rows are
not here** — one shared predicate decides that, because counting them is how a
dashboard came to say "2 items waiting on you" about two questions answered the
same day.

| Key | Type | Meaning |
|---|---|---|
| `items` | array | the unanswered asks; fields below |
| `open` | int | `len(items)` |

An ask:

| Key | Type | Meaning |
|---|---|---|
| `id` | string | `USER-NNN` |
| `needed` | string | what the user has to supply |
| `blocks` | string | the cell verbatim — free text, often a task id |
| `asked` | string | `YYYY-MM-DD`, or `""` on a board that carries `Idle` instead |
| `idle` | string | the `Idle` cell as written (`"9d"`, `"—"`). Displayable. |
| `idle_days` | int \| null | **the number to sort on.** Derived from `asked` at read time when the board has it, else the digits out of `idle`; `null` when nothing says. A stored age is stale the morning after it is written. |
| `status` | string | the cell verbatim |
| `priority` | string | `P0` when the ask blocks a P0 task, else `""` |

### `drift` — does the board agree with the record of how it got that way

The polling section below already told you to surface `drift.unrecorded` rather
than assume the event log is complete, and then left it in the payload with no
version. Same block, same meaning, now under this contract.

| Key | Type | Meaning |
|---|---|---|
| `checked` | bool | `false` when there is no event log — a pre-`perry-task` project, not a broken one. Everything else is then zero or empty. |
| `baseline` | string | the earliest event timestamp, so you can judge `unrecorded` yourself |
| `drift` | int | `len(orphaned) + len(stale_done)` — **only the unambiguous conditions** |
| `unrecorded` | int | board rows with no creating event. **Not counted as drift**: a row can be a hand-edit or can simply predate the tool, and nothing on a row distinguishes them. Perry's own board had 29 the day the writer shipped. |
| `unrecorded_sample` | array | up to 5 of those ids |
| `orphaned` | array | ids an event opened and the board has neither a row nor a close for — the mutation did not land in the markdown |
| `stale_done` | array | `done` rows whose latest event is not their close — edited after the tool wrote them |

A hand-edited board is legitimate; the right response is that Perry notices.


## The three rules that make it safe to code against

1. **Every key above is always present.** An unknown value is `""`, `null` or
   `[]` — never a missing key. You need no `if "owner" in task`.
2. **A key is never removed or retyped without a major bump.** `1.x` → `1.y` may
   only *add* keys.
3. **`contract` is the handle — and check BOTH halves.** The major says
   whether you can parse it. The **minor says whether a value still means what
   it meant when you wrote your code**, which is not the same question, and
   this section used to show only the first:

   ```python
   version = payload["contract"].rsplit("/", 1)[1]
   major, minor = (int(x) for x in version.split("."))
   if major != 1:
       raise SystemExit(f"perry-task list contract {version} is not supported")
   if minor > TESTED_MINOR:            # the minor you actually read against
       for change in payload["semantics"]:
           if change["version"] > TESTED_MINOR_STR:
               warn(change["fields"], change["note"])
   ```

   **Do not refuse on a minor.** `1.x` only adds keys, so an old consumer keeps
   working — that guarantee is real and rule 2 is unchanged. What it does not
   cover is a field whose *meaning* was corrected, which has happened once
   (1.5) and is what `semantics` reports.

   The snippet here previously extracted the major and discarded the rest,
   which taught a consumer that the minor is noise. A front-end that followed
   it exactly could not see 1.5 — the version whose whole reason for existing
   was that two fields changed meaning under it.

## Polling

`updated` is the cheapest change signal per task; for the project as a whole,
`stat` the event log at `<project_root>/.perry/events.jsonl` — it is appended to
on every write. Both are advisories, not guarantees: **a hand-edited board
changes state and produces no event**, which is legitimate and reported rather
than refused. `bin/perry-state --json`'s `board.drift` block is what names those
rows; a front-end that wants to be honest about staleness should surface
`drift.unrecorded` rather than assume the log is complete.

## What this contract does not cover

`## Cadence` is a recurrence register, not work, and is not in this payload.
`## User Input Queue` and `## Top risks` were in this paragraph until 1.6 and
are now `asks` and `risks`; `## Intake` became `intake` in 1.4. If a front-end
needs the one that is left, that is a new key in a `1.x` bump, not a reason to
parse the markdown.

**`perry-state --json` is still not a contract.** It carries no version and may
change under you. Everything a Work surface needs is here.

## Changelog



### 1.8

**Added `role`.** Empty on every project that has not declared a role card,
which today is all of them — so nothing a consumer renders changes until a
project opts in.

**What a consumer sees.** A new string on every task. When it is non-empty, the
project has `.perry/roles/<name>.md` declaring who is accountable for the row,
what they may touch, what they must escalate, and — the part that reaches this
payload's neighbours — an `Accepted by` and a `Default rung` that the close gate
reads. **The stricter of the row's mode rung and its role rung wins**, so a
`role` can raise `verification`'s effective floor without appearing to.

`perry-task add` refuses a roleless row **only** on a project that has declared
roles, and the refusal lists the roles that exist. On a project with none, the
flag is accepted, nothing is demanded, and no refusal mentions a concept the
project has not adopted.

### 1.7

**Added `semantics` (top level) and `timeline[].field`.** Both asked for by
aimark, by name, after a second pass over the payload.

**What a consumer sees.** Two guesses it had to make are now answered by the
payload:

1. *"Has a value's meaning changed since I wrote this code?"* — `semantics`
   lists the minors where one did, with the fields and why. It is a list rather
   than a single entry so a front-end jumping 1.4 → 1.7 still learns about 1.5.
   `§ The three rules` rule 3 previously showed a snippet that extracted the
   major and discarded the rest, which taught the opposite; it now reads both
   halves and does not refuse on a minor.
2. *"Is this timeline entry's `from`/`to` a status?"* — `timeline[].field` says
   so per event. The consumer that reported this had written
   `SECTION_MOVE_EVENTS = new Set(["prioritize"])`, a set that goes wrong
   silently the day a second event overloads the pair.

Also documented, not changed: the event enum in § A timeline entry listed 7 of
13 events. `prioritize`, `retitle`, `next`, `rung`, `evidence` and `depends`
were all shipping and none was named, so a front-end building its event handling
from the spec met them first at runtime.

`field` is `status` on six events, and `section` / `stage` / `title` /
`next_action` / `verification` / `evidence` / `depends_on` on the rest. The ask
proposed `status` for everything except `prioritize`; that is false for
`retitle`, `next` and `rung`, and a wrong word in the field whose job is to stop
you guessing is worse than no field.
One line per version. `1.x` may only add keys; a removal or a retype is a major
bump. Semantic corrections — a field that was computed wrongly — are called out
here explicitly, because "only adds keys" does not cover them and a consumer
deserves to know when a value's *meaning* changed under it.

### 1.6 — 2026-08-18

Two additions, one bump, because both add keys to this payload and two minors
fighting over one response is worse than one that says everything.

**What a consumer sees.**

You can now tell, from this payload alone, **which open rows can actually be
worked on**. Every task carries `startable` — open, not itself waiting on a
reviewer or a blocker, and nothing unfinished under it. Sorting a dashboard on
it needs no graph walk, no second call and no guess. `blocked` used to say a row
was stopped and never say on what; a row now names its dependencies in
`depends_on`, the unfinished ones in `blocked_by`, and the rows it is holding up
in `blocks`. A dependency may name a task that has already closed — that is what
a satisfied dependency looks like, and it stays in the record instead of
vanishing when the work finishes.

The edges have to be written before they can be read. On a board that predates
this version every `depends_on` is `[]`, and
`conformance.blocked_without_dependency` names the rows whose blocker is still
prose — the worklist, and the honest measure of how far it has got. `startable` is already correct on those
rows, because a `blocked` or `review` status is itself a statement that somebody
else has the ball.

Three things a Work surface shows arrive here instead of from `perry-state
--json`, which carries **no version at all**: `risks`, `asks` (the *needs-you*
list, `## User Input Queue`) and `drift`. Two shapes are fixed rather than
carried across. A bullet-sourced risk used to arrive as `{"id": "H", "title":
"· Apple developer agreement expired", "severity": "watch"}` — the severity
letter had become the id, the list marker was glued to the title, and the H/M/L
a human wrote survived only inside `meta`, so a project's own H and M both
displayed as "watch". A bullet now carries `id: ""` (it has no id, and saying so
beats inventing one from the first word of a sentence), a clean `title`, and the
marker on two axes: `severity_text` verbatim and `severity_rank` normalized to
`high`/`medium`/`low`. `severity` keeps its old meaning — the *stance*, not the
magnitude. And `asks[].idle_days` is an integer beside the rendered `idle`
string, so the needs-you list can finally be sorted by age.

Nothing was removed, renamed or retyped.

- **added** `tasks[].depends_on`, `blocked_by`, `blocks`, `startable`.
- **added** `conformance.depends_on_unknown`, `dependency_cycles`,
  `blocked_without_dependency`.
- **added** `risks`, `asks` and `drift` as top-level blocks.
- **added** `perry-task depends <ID> --on … | --clear`, and `--on` on
  `status --status blocked`, which satisfies the same gate `--reason` did and,
  unlike it, reaches this payload. `add --depends` now writes a board cell and
  takes ids rather than free text; it wrote prose into the journal's definition
  block before, once, at creation, never updatable.

### 1.5 — 2026-08-17

No new keys. The minor moves anyway, because two values changed meaning under
a consumer and the version handle is the only way that consumer finds out —
which is the whole reason this changelog exists.

- **corrected** `evidence_paths` on closed rows. It was resolved inside the
  board walk, and a closed row is not on the board — `done` removes it. So the
  field was empty for every closed row on every project: **32 closed rows on
  Perry's own board, every one carrying an evidence cell, every one
  `evidence_paths: []`, every file present on disk.** The identical path on the
  identical board resolved while the row was open and stopped the day it
  closed. It is resolved after the event merge now, for every row, from the
  same `evidence` string the payload publishes.
- **corrected** `conformance.evidence_not_found`, which was populated in the
  same walk and so was silent about closed rows too. `[]` and silence together
  meant a consumer could not tell *"Perry did not resolve this"* from *"the
  file is gone"* — aiMark rendered the document that justifies a close as a
  dead link. It now reports closed rows, and is ordered by id rather than by
  board position so two reads of an unchanged project are identical.

**What a consumer sees.** Rows that reported `evidence_paths: []` now report
paths; `evidence_not_found` gains entries for closed rows whose cell names
something that is not a file — usually a symbol or a prose note, as documented.
No key was added, removed or retyped.

### 1.4 — 2026-08-17

- **added** `intake`. `route` and `resolve-intake` take a row position and no
  payload carried one, so the drain could only be run by opening the board and
  counting — which `subcommands.md` forbids twenty lines above the step that
  needed it. Found by a V4 review.

### 1.3 — 2026-08-17

- **added** `conformance.next_action_cites_closed` — an open row still pointing
  at finished work. Orthogonal to the age check: a row can have been touched
  yesterday and still be waiting on something that closed. Measured before
  shipping, it fires **once** on Perry's own board, and it does **not** catch
  the three rows that motivated it — their `Next action` is prose about a
  review verdict and cites no id at all. Those are surfaced by
  `rows_with_no_computable_age` instead. Two signals, neither a substitute for
  the other.
- **added** `conformance.rows_with_no_computable_age`. The six standard board
  columns carry no date, so a row written before the event log has no age at
  all — and every staleness rule is an age comparison, which made those rows
  permanently fresh. Found while updating `triage` to read this payload: the
  procedure said "measured from `updated`, or from the row's date cells when
  there is no event log", and **the row's date cells do not exist** on a
  standard board. A fallback that names a source which is not there is the
  defect this project keeps finding; the honest answer is that the age is
  unknown and the payload now says so.
- **corrected** which events reach `tasks`. The board half of "these sections
  are not tasks" was always right — the reader skips `## Intake`,
  `## Cadence`, `## User Input Queue` and `## Top risks` by heading. The
  *event* half folded every event that carried an id, so a user-input row
  raised by `perry-task ask` arrived as a task with `status: "pending"`,
  `open: false`, no priority and no group, counted in `closed`, and listed in
  `untitled` when the question predated the `title` field. `perry-task
  cadence-add` would have put its rows in the same place. Only events from
  the subcommands that write a priority-table row are folded now. **This
  changes a value, not a shape**: a consumer sees fewer rows, and the ones
  that leave were never work. Section rows stay out of this payload — that is
  still a `1.x` addition if a front-end asks for them.

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
