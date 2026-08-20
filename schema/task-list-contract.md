# `perry-task list --json` — the front-end contract

> Contract: **`perry-task/list/1.13`**
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
| `--all` | include closed and dropped tasks from `tasks.jsonl`. **Without it you get open work only.** |
| `--json` | the payload below. Without it, a human-readable table. |
| `--track <name>` | restrict to one declared track. |
| `--root <path>` | the project. Defaults to `$PERRY_PROJECT`, else walks up from the cwd. |

`list` writes nothing. It takes the same lock every write takes, so a read

## Two things about *writes* that the payload cannot tell you

They are here because a consumer had to discover both by running the tools.

**`stderr` is not the failure channel.** Every successful write may print an
advisory conformance line there — `⚠ conformance (advisory) — …` — while
returning `0` and doing exactly what was asked. A front-end that treats any
`stderr` output as failure reports **every** successful write as an error. Check
the exit code; with `--json` the same verdict is in the payload and `stderr`
stays quiet.

**`event_written` is on every write result**, and it is the difference between
*"the row moved"* and *"the row moved and its timeline will have a hole"*. The
store+journal transaction lands first; the Board projection and event are
written afterwards. When it is `false` the canonical write succeeded but this payload's `timeline`
will not show it. **§ Polling rests on the log being complete**, so a front-end
that polls should surface this rather than assume.

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

It is also what makes a front-end survive the completed storage change:
`tasks.jsonl` is canonical task truth and `BOARD.md` is its human projection.
The payload shape remains stable even though its current values no longer come
from task rows in Markdown.

## The payload

```jsonc
{
  "contract":     "perry-task/list/1.13",  // check this before anything else
  "semantics":    [ /* see below */ ],     // meaning changes, oldest minor first
  "project_root": "/abs/path",
  "state_root":   "/abs/path",             // where tasks.jsonl, BOARD.md and journal/ live
  "conformance":  { /* see below */ },     // store findings and projection availability
  "intake":       { /* see below */ },     // queue mode's inbox, by position
  "risks":        { /* see below */ },     // `## Top risks`, open ones
  "asks":         { /* see below */ },     // `## User Input Queue` — needs-you
  "drift":        { /* see below */ },     // board vs. the record of how it got there
  "tasks":        [ /* see below */ ],
  "open":         3,                       // counts AFTER --track filtering
  "closed":       0,                       // 0 unless you passed --all — see below
  "events":       57,                      // lines in the event log, unfiltered
  "untitled":     ["TASK-004"]             // ids with no title in any record
}
```

**`open` and `closed` count the rows in THIS payload, not in the project.**
`--all` is what puts closed rows in it, so **a default call reports `closed: 0`
however much finished work the project holds** — on Perry's own board, `0`
against 57. That is not a bug and it is not a project with no history; it is
the flag.

Said here because the example above used to show `open: 3` beside
`closed: 11`, **a pair no single call can return**, and the field had no
definition row anywhere — so a front-end rendering "3 open · 11 closed" from
one request was reading a number the tool never produces. `--all` gives both
counts; without it, `closed` is a constant.

### A task

| Key | Type | Meaning |
|---|---|---|
| `id` | string | **An opaque stable string.** Conventionally `TASK-NNN`, but a real board carries ids under several project-declared prefixes, some with no number at all — a board's own `## ID prefixes` section is where a project states them. Never reused, including after close, which is the part you may depend on. **Do not parse a number out of it** or sort by a numeric suffix. |
| `title` | string | |
| `summary` | string | Optional stable explanation of why the task exists and the intended outcome. `""` means unset. It is stored explicitly and is never inferred from `title`, `next_action`, specifications, evidence or journal prose. Added in 1.11. |
| `owner` | string | free text; the project's own owner model |
| `priority` | string | `P0` \| `P1` \| `P2`. May be `""` for a closed task whose creating event predates the field. |
| `status` | string | the typed current status from `tasks.jsonl`: one of `schema § enums.task_status` — `not_started`, `blocked`, `in_progress`, `review`, `done`, `dropped` — or `""` for a legacy record that predates a known value. `BOARD.md` is a projection and cannot change this value. |
| `status_text` | string | **Legacy display alias of `status`.** Kept so existing consumers do not lose a key or change type; from 1.10 onward it is always byte-equal to `status` and never exposes raw, emphasized, or off-enum text from `BOARD.md`. |
| `track` | string | declared track name; `main` when the project declares none |
| `mode` | string | `project` \| `pipeline` \| `queue` \| `inquiry`. **Derived** from this row's `track` and `.perry/config.md § Tracks`, never stored — a project with no track register reports `project` for `main`, and a row on a track the register does not declare reports `""`. It was read out of the event log until a review found that `route`-created rows shipped `""` on exactly the mode where routing is normal, and that deleting the derived-and-disposable event log blanked it for every row. |
| `stage` | string | non-`project` modes only; `""` otherwise |
| `stage_since` | string | `YYYY-MM-DD`; pipeline/inquiry. Dwell time is `today − stage_since`. |
| `arrived` | string | `YYYY-MM-DD`; queue mode. **Every SLA number is `today − arrived`.** |
| `parent` | string | inquiry mode: the question this was split from |
| `commitment` | string | the commitment id this row discharges |
| `next_action` | string | |
| `evidence` | string | stored relation text. Often a comma-separated list of backticked paths, sometimes a symbol or a prose note. |
| `evidence_paths` | array | strings, each **relative to `project_root`** and each one that **exists**. Perry resolves against `state_root` and `project_root` in that order, because both conventions are live in that column on real boards and nothing in the string distinguishes them. Spans that resolve nowhere are in `conformance.evidence_not_found` rather than here — a dead link is worse than a string. **Resolved for closed rows as well as open ones** — it was not until 1.5, and a closed row's evidence is the document that justifies the close, which is the one a reader most wants to open. |
| `verification` | string | `V1`…`V6`, or `""` if unrated |
| `role` | string — the declared role accountable for this row, or `""`. **Required once the project declares any `.perry/roles/*.md`, absent otherwise** (1.8). A project with no role cards is never asked for one and never refused for omitting one, which is DESIGN-006's Goal 7. |
| `group` | string | the stored projection group. `P0`/`P1`/`P2` for a standard board; a workstream name like `Open — 投资线` when the project organizes its Board that way. |
| `open` | bool | `false` exactly when typed `status` is `done` or `dropped`; `true` otherwise. Use this served field as the live/closed test. |
| `depends_on` | array | the stored opaque ids this task waits on, in declared order. An entry may name a closed task, a task not present in this filtered payload, or a `DESIGN-`/`ADR-` handle. `[]` means no dependency is declared. |
| `blocked_by` | array | the subset of `depends_on` that is **not known-finished** — an id whose task is still open, or an id this payload does not carry. An id Perry cannot see counts as unsatisfied: *"I do not know"* is not *"it is done"*, and reporting the row ready is the one error that sends somebody to work on something still blocked. |
| `blocks` | array | the reverse edge — ids in this payload whose `depends_on` names this row. So *"what does closing this free up"* is a lookup, not a scan. |
| `startable` | bool | **the field a dashboard sorts on.** `true` when the row is `open`, `blocked_by` is empty, and its own `status` is not `blocked` or `review` (both mean somebody else has the ball) — **unless `blocked_stale` is `true`, in which case the stored `blocked` is a contradiction of the graph and does not win.** Changed in 1.12; see `semantics`. This is served so you never walk the graph yourself. |
| `blocked_stale` | bool | `true` when the row is `open`, its stored `status` is `blocked`, it **declares** at least one dependency, and **every one of them has closed** — the board says stopped and the graph says nothing is stopping it. Perry does not rewrite the cell, so `status` still reads `blocked` until somebody acts; this key is how you find out that it is out of date without walking the graph. It is `false` for a row with any open dependency, `false` for a `blocked` row that declares no dependency at all (that one is `conformance.blocked_without_dependency` — the edge is in prose Perry cannot read, and *"I cannot see it"* is not *"it closed"*), and `false` for `review`, which waits on a human and so can never be contradicted by a dependency edge. Added in 1.12. |
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
lives in `tasks.jsonl.depends_on`; the event log records its transition and the
Board renderer projects it into a `Depends on` cell. A cycle is refused at
write time; a cycle introduced by an external store edit is reported by
`conformance.dependency_cycles`.


### A timeline entry

| Key | Type |
|---|---|
| `ts` | string — ISO-8601, **seconds** precision, local time, no zone suffix. **Ties are possible and are not duplicates** — two events one operation apart land in the same second routinely. Timeline order is array order and is authoritative; if you re-sort by `ts`, use a stable sort or you will reorder a `start` after the `status` that followed it. |
| `event` | string — `add`, `route`, `start`, `stage`, `track`, `status`, `prioritize`, `retitle`, `summary`, `next`, `rung`, `evidence`, `depends`, `done`, `drop` |
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
- **`track`** — on `track`. A track declared in `.perry/config.md § Tracks`. **Not `stage`**, though a move re-stamps one: a consumer told the pair was a stage would resolve `main` → `intake` against a stage vocabulary that does not contain them. The stage and the `Arrived` the move produced ride on the stored event's own `stage` / `stage_from` / `arrived` / `arrived_from` keys.
- **`title`** — on `retitle`. The row's title.
- **`summary`** — on `summary`. The stable purpose/outcome explanation; `""` is an explicit clear.
- **`next_action`** — on `next`. The next-action cell, often several hundred characters of prose.
- **`verification`** — on `rung`. A rung, `V0`–`V6`.
- **`evidence`** — on `evidence`. The evidence cell.
- **`depends_on`** — on `depends`. The dependency cell.

The map's keys are asserted equal to the writer's own event set, so an event
cannot ship without declaring what its pair means. The ask that produced this
proposed `status` for everything except `prioritize`; that would have been
false for **eight** of the fifteen — `stage`, `track`, `retitle`, `summary`,
`next`, `rung`, `evidence` and `depends` — and a wrong word in the field whose job is to stop
you guessing is worse than no field.

### `conformance` — what task truth or its projection could not classify

**Read this before you trust completeness.** Current task findings come from
validated `tasks.jsonl` plus disposable history. Projection-only findings are
explicit compatibility fields and `missing_projection` says when Board-backed
non-task registers could not be read.

| Key | Type | Meaning |
|---|---|---|
| `sections_read` | array | `{heading, priority, rows}` per stored task group. `priority` is `null` unless the group is `P0`/`P1`/`P2`. |
| `sections_skipped` | array | Legacy compatibility field; task reads do not scan Board tables, so this is empty. |
| `rows_with_unrecognized_id` | array | Legacy compatibility field; projection-only rows never enter task truth, so this is empty. |
| `off_enum_status` | array | `{id, status}` — a legacy or externally edited store record carries a status string outside the six typed values. The board projection is never consulted to populate this finding. |
| `rows_with_no_status` | array | `{id, section}` — a legacy store record has no typed status. `open` is `true` because no terminal value is present. |
| `evidence_not_found` | array | `{id, paths}` — spans in the `Evidence` cell that resolve under neither root. Usually symbols or prose, not broken links. Covers open and closed rows alike, ordered by `id`. Together with `evidence_paths` this is the pair that lets you tell **"the file is gone"** from **"Perry did not look"**: a row whose cell names something reaches exactly one of the two, never neither. |
| `next_action_cites_closed` | array | `{id, cites, status, row_status, blocked_stale, readings, means}` — an open row whose `Next action` points at a task that has since closed. **This is not a prose-style finding, and the entry says so in `means`.** The hit has two readings and this check decides between them in no case: the *prose* is stale, or the *row* is unblocked and its status has not caught up. `readings` states both, `row_status` and `blocked_stale` carry what the graph already knows about the row, and `means` is the sentence to show a reader. On 2026-08-20 this fired on exactly the two rows on Perry's own board that were stranded, was read as wording, and was silenced by rewriting the cells — which settled the disagreement by deleting the evidence of it. **Only ids in this payload are resolved**: `DESIGN-`, `ADR-` and `USER-` ids appear in these cells constantly and are not checked, because reporting "cites nothing closed" while skipping three id families would claim more than the data supports. |
| `blocked_by_closed_rows` | array | open ids whose stored `status` is `blocked`, which **declare** at least one dependency, and every one of which has closed — the aggregate of `tasks[].blocked_stale`, read from that field rather than recomputed, so the rule behind it stays stated exactly once in `bin/lib § resolve_startability`. **Disjoint from `blocked_without_dependency` by construction**: that one is the empty list, this one is the non-empty list nothing is left in. TASK-037 and TASK-045 were both of these on 2026-08-20 and neither was named, because the only check in the family tested `not depends_on`. A row in neither array is one whose blocker is real. |
| `in_progress_with_no_live_run` | array | `{id, status, last_event, idle_hours, threshold_hours, means}` — an open row that says `in_progress`, holds **no dispatch slot** (`~/.cache/perry/in-flight/`, read without cleaning), and whose last event is older than `thresholds.in_progress_idle_hours`. Neither half alone is a finding: a long dispatch holds a slot and writes nothing, and a row worked by hand never had a slot. Together they mean nobody is holding it and nobody has said so — two agents starved at the 600s watchdog on 2026-08-20 and their rows sat exactly here. **Empty when `has_event_log` is false**, for the reason 1.9 gives. |
| `review_idle` | array | `{id, status, last_event, idle_hours, threshold_hours, means}` — an open row in `review` whose last event is older than `thresholds.review_idle_days`. `review` waits on a human, so no dependency edge can ever contradict it and nothing else in this payload notices such a row; TASK-100, TASK-111, TASK-127 and TASK-133 all sat there after their PRs had merged. **Empty when `has_event_log` is false**, for the reason 1.9 gives. |
| `rows_with_no_computable_age` | array | open ids with **no event and no date cell**, so `today − anything` is undefined for them. Every staleness rule is "idle ≥ N days", so these read as fresh forever. On Perry's own board this was **6 of 9 open rows** — the ones written before the tool existed. |
| `depends_on_unknown` | array | `{id, unknown}` — dependency ids this payload does not carry, ordered by `id`. Not an error and not refused at write time: a dependency **must** be able to name a closed task, or every satisfied dependency would have to be deleted from the record to be written in the first place, and `DESIGN-`/`ADR-` ids are legitimate here too. This is where a typo shows up. |
| `dependency_cycles` | array | arrays of ids, each a loop found in the stored edges, e.g. `[["A","B","A"]]`. Every task in one waits forever and none is `startable`. The write path refuses to create one; an externally edited store is reported rather than hidden. |
| `blocked_without_dependency` | array | open ids whose `status` is `blocked` and whose `depends_on` is empty — the row says it is stopped and does not say on what. **The migration worklist**: their dependency is still in prose somewhere no program can read. On Perry's own board this is every blocked row today. |
| `has_event_log` | bool | `false` on any project that predates the writer. Then `created`, `updated` and `timeline` may be empty, and that is not an error: current fields remain canonical in the store while history is unavailable. |
| `missing_projection` | string | `""` when `BOARD.md` exists; otherwise its expected path. Task records and event history remain readable, while Board-backed risks, asks and intake keep their empty contract shapes. |

#### `sections_read[]` — the entry, key by key

One entry per stored task group, in the order the store yields them. This is
how a consumer checks that the group it renders was actually seen, rather than
inferring it from the rows that came back.

| Key | Type | Meaning |
|---|---|---|
| `heading` | string | the group's heading exactly as stored, including any parenthetical — `"P0 (must finish this period)"` is one heading and not the `P0` beside it. Two groups may normalize to the same priority and they stay two entries. |
| `priority` | string \| null | `P0`, `P1` or `P2` when the heading **is** one of those three, and `null` otherwise. `null` is the common case on a workstream-organized project and is not a finding; it is the same fact `tasks[].priority` states as `""`, and the two spellings differ because this key distinguishes *no priority* from *a priority that is the empty string*. |
| `rows` | int | how many rows the group holds. Counted from the store, so it may exceed what a filtered call returns — compare it against `open + closed` only on an unfiltered `--all`. |

#### `evidence_not_found[]` — the entry, key by key

Ordered by `id`, and **covering closed rows as well as open ones since 1.5**.
Together with `tasks[].evidence_paths` this is the pair that separates *the file
is gone* from *Perry did not look*: a row whose `Evidence` cell names anything
reaches exactly one of the two arrays, never neither.

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the row whose `Evidence` cell carried the span. |
| `paths` | array | the spans that resolved under neither root, as written, in cell order. **Usually not broken links** — the cell is prose and a project writes test ids, symbols and command lines into it, so `["tests/…::TestRungDistribution"]` and `["git diff"]` are both ordinary entries here. Nothing is guessed at: a span is reported unresolved, never repaired. |

#### `depends_on_unknown[]` — the entry, key by key

Tabulated at 1.13. It was prose until 2026-08-21, when a row on Perry's own
board was blocked on a `USER-` ask and the collection became non-empty for the
first time — at which point `tests/contract_key_parity.py` could compare it and
found both keys undocumented. **That is the collection-empty limitation this
contract names under `review_idle[]`, seen from the other side**: a page cannot
be checked against a collection nothing populates, so the check is silent until
the day it is not.

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the row carrying the edge. |
| `unknown` | array | the dependency ids this payload does not carry, sorted. A `USER-` ask lands here today: `perry-task depends --on USER-nnn` is accepted at the write and reported here at the read, which is the disagreement TASK-162 is open for. |

#### `next_action_cites_closed[]` — the entry, key by key

Its first three keys have been here since 1.3 and are unchanged. The other four
arrived at 1.13 because the triple alone was read as a wording complaint and
silenced as one.

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the open row whose `Next action` cites finished work. |
| `cites` | string | the closed task it names. |
| `status` | string | that task's status — `done` or `dropped`. |
| `row_status` | string | the citing row's own stored `status`. A `blocked` row here is a different situation from a `not_started` one and the reader needs both. |
| `blocked_stale` | bool | the citing row's `tasks[].blocked_stale`. When it is `true` the dependency graph has already reached the second reading on its own, and `blocked_by_closed_rows` names the row too. |
| `readings` | array | the two things this hit can mean, as strings, in no particular order of likelihood: the prose is stale, or the row is unblocked. This array is the check declining to guess. |
| `means` | string | one sentence naming both rows, both readings, and what the graph does or does not already say. Show this, not the triple. |

#### The idle entry — `in_progress_with_no_live_run[]` and `review_idle[]`

**One shape for both**, so a consumer needs one code path. They differ in which
status they watch and which threshold they read, not in what an entry looks
like.

| Key | Type | Meaning |
|---|---|---|
| `id` | string | the row nothing has moved. |
| `status` | string | `in_progress` or `review` — which of the two checks produced the entry, without keying on the array it came out of. |
| `last_event` | string | its most recent event timestamp. This is the clock both checks measure; a row with none is skipped and is already in `rows_with_no_computable_age`. |
| `idle_hours` | number | hours since `last_event`. **Hours for both**, including `review_idle`, whose threshold is declared in days: the unit a person reads belongs in `means`, and a shared shape is worth more to a program than a friendlier number. |
| `threshold_hours` | number | what it was judged by — `thresholds.in_progress_idle_hours`, or `thresholds.review_idle_days × 24`. Carried rather than left to be inferred, because a reader who cannot see the threshold cannot tell a finding from a setting. |
| `means` | string | the sentence to show a reader. For `in_progress_with_no_live_run` it names the one thing that is unsafe to do on reading it — re-dispatch without asking. For `review_idle` it names both readings: the verdict was given and the row was never closed, or nobody has been asked for one. |

Two consequences worth designing for rather than discovering:

- **`status` is not guaranteed to be one of the six.** The enum is what Perry
  *writes*; a legacy or externally edited store may hold another string. Render
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

### `drift` — legacy Board/event history reconciliation

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

A hand edit to the Board projection is not task truth. `perry-lint` reports
store/projection drift; this compatibility block only describes whether the
event history explains the rows visible in that projection.


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

### `semantics[]` — the entry, key by key

The array rule 3 above walks. **Ordered oldest minor first**, which is what
makes "everything newer than the minor I tested against" a slice rather than a
search; `tests/test_task_writer § test_the_semantics_list_is_ordered_oldest_first`
holds that order, because the list shipped once as 1.5, 1.9, 1.7.

It is not the Changelog. The Changelog records every shipped minor including
the ones that only added keys; this array carries **only the minors under which
an existing value changed meaning**, which is the strictly smaller set a
working consumer has to act on.

| Key | Type | Meaning |
|---|---|---|
| `version` | string | the minor the change shipped in, `"1.12"`. A string, not a number: `1.10` sorts below `1.9` numerically and above it correctly. Compare it as the pair of ints rule 3's snippet builds, or as the string against the same-shaped string — never as a float. |
| `fields` | array | the payload paths whose meaning moved, as strings, in this payload's own dotted notation — `"conformance.sections_read"`, `"timeline[].from"`. These are paths to read against, not keys to look up at the top level. |
| `note` | string | prose, always populated: what the value used to mean, what it means now, and what a consumer that hardcoded the old meaning does wrong. Written for a reader, and long — this is the one field here meant to be shown rather than branched on. |

## Polling

`updated` is the cheapest change signal per task; for the project as a whole,
`stat` the event log at `<project_root>/.perry/events.jsonl` — it is appended to
on every tool write. Both are advisories, not guarantees: an external store
edit changes truth without adding history, and a failed event append leaves a
hole. A front-end that wants to be honest about staleness must not treat the
event log as the canonical current record.

## What this contract does not cover

`## Cadence` is a recurrence register, not work, and is not in this payload.
`## User Input Queue` and `## Top risks` were in this paragraph until 1.6 and
are now `asks` and `risks`; `## Intake` became `intake` in 1.4. If a front-end
needs the one that is left, that is a new key in a `1.x` bump, not a reason to
parse the markdown.

**`perry-state --json` is still not a contract.** It carries no version and may
change under you. Everything a Work surface needs is here.

## Changelog

**Not a version, 2026-08-21 (TASK-131).** `semantics[]`,
`conformance.sections_read[]` and `conformance.evidence_not_found[]` gained key
tables. **No key was added, removed or retyped** — all three shapes have shipped
since 1.10 or earlier and were described in prose, which
`tests/contract_key_parity.py` does not read; nine emitted paths were therefore
documented nowhere it could see. Documenting what already ships is not a bump,
so the version does not move.

### 1.13 — 2026-08-21

**Three checks for a row that a process bug stranded, and one existing check
told what it is for.**

`conformance` already carried this family — `blocked_without_dependency`,
`depends_on_unknown`, `dependency_cycles`, `next_action_cites_closed` — and
triage already reads it before judging any row. These are predicates added to
that block, each traced to an incident on Perry's own board rather than
invented.

**`blocked_by_closed_rows` is one predicate away from a check that already
existed, and that is why it was missed.** `blocked_without_dependency` tests
`not depends_on` — the list being **empty**. TASK-037 and TASK-045 had a
non-empty list whose every entry had closed, so the board said stopped, the
graph said nothing was stopping them, and no array named either row. The new
key is the **aggregate of `tasks[].blocked_stale`**, read from that field: the
rule is stated once, in `bin/lib § resolve_startability`, under an AST guard
that fails on a second statement of it.

**`in_progress_with_no_live_run` needs both halves.** A dispatch slot under
`~/.cache/perry/in-flight/` and a fresh event each rule the row out on their
own; the check names a row only when neither says anything. The marker
directory is read, never cleaned — a `list` that could delete another session's
slot would be a read command with a side effect on shared state.

**`review_idle` covers the status nothing else can.** `review` waits on a human
and no dependency edge can contradict it, so it is invisible to every other
check here.

**`next_action_cites_closed` now reports what a hit might MEAN.** Its keys are
unchanged and four are added. The array's job was always to catch a row waiting
on finished work, but a bare `{id, cites, status}` triple reads as a wording
complaint — and on 2026-08-20 it fired on exactly the two stranded rows, was
read as prose hygiene, and was silenced by rewriting the cells. The hits were
two rows raising their hands. A check that reports a pattern without its
meaning is suppressed by whoever reads it, so each entry now states both
readings and picks neither.

Both new idle checks are **empty when `has_event_log` is false**, for the
reason 1.9 gives about `rows_with_no_computable_age`: on a project that
predates the writer every open row qualifies by construction, and an array that
restates the flag once per row has named no finding.

- **added** `conformance.blocked_by_closed_rows`,
  `conformance.in_progress_with_no_live_run`, `conformance.review_idle`.
- **added** `row_status`, `blocked_stale`, `readings` and `means` to each
  `conformance.next_action_cites_closed` entry; announced in `semantics`,
  because what changed is what a consumer should do with the array.
- **added** `thresholds.in_progress_idle_hours` and
  `thresholds.review_idle_days` to `schema/state-schema.json`. The first is
  calibrated against `PERRY_DISPATCH_STALE_TTL` rather than chosen freely: at
  or below the marker TTL the two signals would contradict each other.

### 1.12 — 2026-08-20

**A stored `blocked` no longer masks an empty `blocked_by`.** Until now
`startable` read the row's own `status` before the dependency graph it had
already computed, so a row whose every declared dependency had closed reported

```
status=blocked   blocked_by=[]   startable=false
```

— all three in the same object, with no key a consumer could read to see that
the first contradicted the second. On Perry's own board two of the four blocked
rows were in exactly that state, one of them still carrying a `Next action`
naming a chain that had fully closed. The other half of the same problem is
that `perry-task done` does not look at its dependents, so the ordinary close
path *creates* this state and the old `startable` then hid it.

Such a row is now `startable: true` and carries the new `blocked_stale: true`.

**The stored status is deliberately left alone.** This payload reports; it does
not rewrite a cell nobody asked it to rewrite. So a stale row still *reads*
`blocked` on the Board and in `status` until a human or a subsequent write
clears it — `blocked_stale` is what makes that visible in the meantime, rather
than silently recomputing it behind the consumer's back.

Three cases deliberately unchanged, because this is not "drop the check":

- a row with **at least one open dependency** keeps a non-empty `blocked_by`
  and stays unstartable;
- a `blocked` row that **declares no dependency at all** is untouched. Its
  blocker is prose Perry cannot read — that is
  `conformance.blocked_without_dependency` — and *"I cannot see it"* is not
  *"it closed"*, the same rule that makes an unknown id unsatisfied;
- **`review` is untouched.** A row in review waits on a human, not on a row, so
  no dependency edge can contradict it.

- **added** `tasks[].blocked_stale`.
- **changed the meaning of** `tasks[].startable`; announced in `semantics`.

### 1.11 — 2026-08-20

**Added `tasks[].summary` as a string on every Task.** It is optional task
truth, so legacy records and tasks created without it return `""`; consumers
never need a missing-key branch. `perry-task add --summary` creates it and
`perry-task summary` updates or explicitly clears it. The Board remains a
compact projection with no required Summary column.

This minor is additive: no existing key changed type or meaning. Perry does
not synthesize the value from a title, next action, specification, evidence or
journal text. A consumer that wants an explanation may display `summary` when
non-empty and otherwise show only the canonical title.

### 1.10 — 2026-08-19

**`status_text` is now a legacy display alias of typed `status`.** The key and
its string type are unchanged, but its meaning moved: raw Markdown decoration
and off-enum prose in `BOARD.md` are projection bytes, not task truth. A hand
edit to that cell cannot change either payload field. Consumers that displayed
`status_text` may keep doing so; consumers that used it to recover raw board
text must stop, because `tasks.jsonl.status` is now the only current status.

This semantic change is listed in the payload's `semantics` array. It is the
explicit typed-status authority for TASK-090's store-only read cutover, rather
than an undocumented reinterpretation under contract 1.9.

The same entry announces the conformance cutover: `sections_read` now
summarizes stored groups, while `sections_skipped` and
`rows_with_unrecognized_id` remain shape-compatible legacy keys and are empty
because current task reads do not scan Board tables.

### 1.9 — 2026-08-18

**`conformance.rows_with_no_computable_age` is empty when
`conformance.has_event_log` is false.**

**What a consumer sees.** On a project with no event log, every open row used to
appear in that array — 17 of 17 on the front-end that reported it — because they
all qualify by construction. The array restated the flag once per row instead of
naming a finding, and `conformance` is meant to be the payload's account of what
it could not *classify*. "This project predates the writer" is one fact, and
`has_event_log` already carries it.

It now reports only rows whose age is uncomputable for a reason the flag does not
already give. **If you rendered that list, read `has_event_log` instead.** Listed
in `semantics` because the meaning moved under a live consumer.

Also documented in this release, unchanged in behaviour: **`stderr` is not the
failure channel**, **`event_written`**, and that **`ts` ties are possible and are
not duplicates** — three things a consumer had to discover by running the tools.

### 1.8 — 2026-08-18

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

### 1.7 — 2026-08-18

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

`field` is `status` on six events, and `section` / `stage` / `track` / `title` /
`summary` / `next_action` / `verification` / `evidence` / `depends_on` on the rest. The ask
proposed `status` for everything except `prioritize`; that is false for
**eight** of the fifteen — `stage`, `track`, `retitle`, `summary`, `next`, `rung`,
`evidence` and `depends` — and a wrong word in the field whose job is to stop you guessing is
worse than no field.
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
