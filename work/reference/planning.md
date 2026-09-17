# PMO planning

## Planning

### `plan-week`
Generate this ISO week's plan. Reads `phase/<current-NNN>-<slug>.md` (resolve via `phase/CURRENT`; if OKR present) and `perry-task list --json` to see what's already on the board. Picks 3–5 highest-leverage open tasks for the week, marks them P0 (or proposes new P0 rows), confirms with user. **Both halves of that go through the tool** — `"$PERRY_HOME/bin/perry-task" add --actor <actor> --priority P0` for a new row, `"$PERRY_HOME/bin/perry-task" prioritize <ID> --actor <actor> --priority P0 [--reason "…"]` to move an existing one, which keeps its id and every cell. This line used to say the second was "still a hand edit" because "the tool has no `priority` subcommand yet"; `prioritize` closed that, and a procedure that keeps teaching the hand path after the tool path exists is how a row acquires a post-tool edit for no reason. Writes the day's plan entry to `journal/<YYYY-MM>/<today>.md` under `## Notes` — prose, and the one part of this that is genuinely yours. Drafts the week's row in `weekly/<YYYY-WW>.md`.

### `triage`

**Read the intake block first — do not count rows by hand.**

```
"$PERRY_HOME/bin/perry-task" list --json           # → .intake
```

`route <n>` and `resolve-intake <n>` act on a row **position**, and until the
payload carried one the only way to get it was to open `BOARD.md` and count —
twenty lines below the rule forbidding exactly that. `.intake` gives you `n`
per row, `undischarged`, and `oldest_undischarged` to start from.

**At the end of a review period, sweep:**

```
"$PERRY_HOME/bin/perry-task" intake-sweep --actor <actor>
```

Discharged rows move to today's journal with their `Outcome` intact. This rule
lived in `modes/queue.md` and nothing implemented it, which matters because the
same file rests its overflow argument on it: intake pressure is supposed to mean
*taking on more than you discharge*, not *having discharged a lot*.

**Step 0 — drain the intake register (`## Intake` in `perry-tasks board`), before anything else.** Applies to every queue-mode track. If the track exists and the section does not, it is created by the first `perry-task add` on a queue track or by `perry-task intake`; do not hand-write it, and do not skip the step — a self-skipping step is indistinguishable from a step that has nothing to do. Walk it top to bottom; every row gets exactly one outcome, and none may be left as-is:

- **Routed** to a track → `"$PERRY_HOME/bin/perry-task" route <n> --actor <actor> --track <track> [--priority P1 | --group "<heading>"]`, where `<n>` is the intake row's position. `--group` names the project's own heading on a board that does not use `P0`/`P1`/`P2` — the same flag, and the same meaning, as on `add`. The tool carries `Arrived` onto the new row, sets `Stage` to the track's first post-intake stage, and writes the destination back into the intake row's `Outcome` so the request's record is complete. Carrying `Arrived` is not bookkeeping: `today − Arrived` is the number every SLA check measures, so a routing that drops it makes the mode's own breach check uncomputable and silently exempts the row from the only clock governing it (`modes/queue.md`). It was dropped, by this procedure, until the tool did it structurally.
- **Dropped** → `"$PERRY_HOME/bin/perry-task" resolve-intake <n> --actor <actor> --outcome dropped --reason "…"`. "We are not doing this" is a real answer, and an undropped request is one that gets re-asked. The tool writes the `Outcome` cell, the journal line and the event, so a declined request is as visible as a routed one.
- **Deferred** → same command with `--outcome deferred --reason "<the named condition>"` — never a bare "later".

**Recording an arrival is a separate act from draining one.** A request that
reaches you between triages — in chat, from a colleague, out of a meeting — is
written down when it arrives, not remembered until the next walk:

```
"$PERRY_HOME/bin/perry-task" intake --actor <actor> --title "<the request, in the asker's words>" \
    [--arrived YYYY-MM-DD]
```

`--arrived` defaults to today and is there for a request that reached you
earlier than you are recording it; backdating it honestly is what keeps the SLA
clock true. Do this whenever a request arrives on a queue-mode track, not only
during triage — an intake section that is only ever *drained* and never *filled*
is the failure `modes/queue.md` describes as "a track whose intake is always
empty while work is clearly happening."

**The section is a projection of a record store** (TASK-196, ADR-007 applied to
a third register). `bin/perry_store.py` holds the record shape — `order`,
`arrived`, `request`, `outcome`, `discharged` — and renders it back through the
same functions the task and risks stores use.

```bash
"$PERRY_HOME/bin/perry-tasks" intake-build   # derive the records; write nothing
"$PERRY_HOME/bin/perry-tasks" intake-diff    # render them back and byte-compare
"$PERRY_HOME/bin/perry-tasks" intake-write --from-board   # the ONE-WAY import
```

**`order` is the key, and that is the one way this register is unlike the other
two.** An intake row has no id: `resolve-intake <n>` and `route <n>` take a
position, and `perry-task/list § intake.rows[].n` publishes one, so `n` is the
row's ordinal and `n = order + 1`. It is a **cursor, not a name** — `intake-sweep`
removes discharged rows and every row below them renumbers, exactly as it did
before the store existed. What the store adds is that this can no longer happen
unnoticed: a shift the store does not know about is `intake-store-drift` from
the first moved row on, and a shift it does know about is a sweep, which appends
an event. Minting a stable `IN-NNN` was considered and rejected — it would put a
stored identity on rows the board has no column for, and it would change what an
integer somebody types today addresses.

`discharged` is the field the three columns cannot hold, the way `cleared` is
for risks: whether a request has left the queue rides inside the `Outcome`
cell's prose. It is carried across `--from-board` only when the store says
`True`, because `check_intake_undischarged` makes discharge one-way — a row
takes exactly one outcome — so `True` is a fact the board cannot un-say while
`False` is "still waiting", which the cell answers for itself.

**The byte gate is run and, for this register, it cannot fail.** Nothing here
collapses two lines into one record the way a repeated `RX-001` does one
register over, so rendering the derived records back is an identity. It is kept
because it is the declared contract and because it will bite the day a stored
field stops being a copied cell — but the proof is carried by the report's
counters, `cells_verbatim` above all. The gate that is *not* a tautology is the
one beside it: the store's row count and `Board.section_rows`' row count are
compared row by row before a byte is written, because those are two functions in
two files and one integer with two meanings is what a register with no id cannot
survive.

`perry-lint` reports a hand edit as `intake-store-drift`, at `warn`, and is
silent-with-a-payload when there is no `intake.jsonl`: *no store* and *clean* are
different answers.

A row still sitting in intake for **more than 14 days** is reported by age. Not "after two triages": `Arrived` is recorded and nothing counts triages, so elapsed time is computable and a triage count is not. And if intake is pushing a `BOARD.md` the project still holds toward its 200-line cap, **say so as a finding** — a project taking on more than it discharges is exactly what that pressure means. Do not raise the cap and do not move the section somewhere it can grow unnoticed; if it recurs, that is a reason to revisit DESIGN-003 § 4 decision 3, not to relax it quietly. The board `perry-tasks board` prints is not a file and has no line cap, so a board-less project has no cap for intake to push against.

**Read the payload, then walk what it returns — do not open `BOARD.md` and
look.** Eyeballing a file for numbers is the one thing Perry's oldest rule
forbids, and this procedure was written before there was an alternative:

```
"$PERRY_HOME/bin/perry-task" list --all --limit 0 --json
"$PERRY_HOME/bin/perry-state" --json
```

The first carries `updated`, `stage_since` and `arrived` per row — every age
below is computed from those, not read off the board. The second carries the
drift block and the User Input Queue.

**Step 0.5 — read `conformance` before judging any row.** It says what the
board holds that the payload could not classify, and each entry is a
triage-shaped question the old walk had no way to ask:

| Key | What triage does with it |
|---|---|
| `rows_with_no_status` | The row's section has no `Status` column, so `open` is an assumption. Ask whether it is finished — Perry's own board had **20 done tasks reported as open** this way. |
| `off_enum_status` | The cell says something the enum does not cover. Often legitimate (a composite state); sometimes a typo. Surface, never rewrite. |
| `evidence_not_found` | A path in the `Evidence` cell resolves under neither root. Usually a symbol or a note, not a broken link — check before treating it as one. |
| `sections_skipped` | A `## ` section holding a table with no `ID`+`Title`. If it is actually work, its table needs those columns. |
| `next_action_cites_closed` | **Not a wording finding — read `means` on the entry.** The row is waiting on work that finished, and there are two readings: the prose is stale, or the row is unblocked and its status has not caught up. The payload states both and picks neither, because it cannot. **Rewriting the cell is not the default fix.** On 2026-08-20 this fired on exactly TASK-037 and TASK-045, was read as prose hygiene, and the cells were rewritten — those two were the only stranded rows on the board and the rewrite deleted the evidence. Decide which reading holds with the user, then act on the row. Only `TASK-` ids are resolved; a cell citing a `DESIGN-` or `USER-` id is not checked and you still have to read it. |
| `blocked_by_closed_rows` | The row says `blocked`, names its dependencies, and **every one of them is terminal — a task that closed, or a `USER-` ask that was answered** (TASK-162). Nothing is stopping it. This is not `blocked_without_dependency` — the two are disjoint, and this one is the row whose edges are all satisfied. Move it out of `blocked` or say what else is holding it; leaving the cell is how TASK-037 and TASK-045 sat stranded. |
| `in_progress_with_no_live_run` | The row says somebody is working on it, no executor holds a dispatch slot, and nothing has moved it past `thresholds.in_progress_idle_hours`. A run probably died without reporting. **Ask before re-dispatching** — a second agent on a row a first one still holds is what the dispatch limit exists to prevent. |
| `review_idle` | The row has waited on a human past `thresholds.review_idle_days`. `review` is the one status no dependency edge can contradict, so nothing else in the payload notices it. Either the verdict was given and the row was never closed, or nobody has been asked for one — both are questions for the user. |
| `rows_with_no_computable_age` | No age exists for these. Every staleness rule below is an age comparison, so they were being read as fresh forever. Ask about each rather than skipping it. |
| `has_event_log: false` | The project predates the writer. `created` / `updated` / `timeline` are empty for every row and **that is not an error** — fall back to the row's own date cells. |

The software-ops triage checks below (architecture review, runbook and incident
attention) follow `$PERRY_HOME/reference/config.md § Pack capabilities and
controls`: run only for an active pack or an independent project requirement.
Disabled pack defaults never add attention items or an enablement question.

Then walk the rows the payload returned. For each open row:
- Stale? (P0 idle ≥3d, P1 idle ≥7d, P2 idle ≥14d, measured from `updated`) → flag. **A row in `conformance.rows_with_no_computable_age` has no age**: no event, and the six standard board columns carry no date. Do not treat it as fresh — that is what the old rule did to two thirds of Perry's own board. Ask instead: *"this row has no recorded age; is it still live?"*
- Same dependency cited in ≥2 rows? → structural blocker
- `done` claim without evidence file in `evidence/<YYYY-MM>/` → `"$PERRY_HOME/bin/perry-task" status <ID> --actor <actor> --status review --next "needs an evidence file before it can close"`
- Owner is an agent and the row is still `not_started`? → flag. **Read the row, not the chat**: `delegate` now writes `in_progress` with `delegated to <agent>; awaiting paste-back` in `Next action`, so a delegated task is visible in state. This check used to look for "a recent delegation prompt in chat", which is not a surface any tool can read and not a record that survives the session.
- Row inflated (long inline notes leaking into the board) → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only Status + Next action + Evidence path on the board.
- Spec has `Deployed: yes`, status `review`, but no `Runbook:` field or runbook file missing → flag with "blocks close" annotation (see `$PERRY_HOME/packs/software-ops/runbooks.md`).
- Spec's `Touches architecture:` non-empty, status `review`, but latest dispatch evidence has no `## Architecture review` PASS → flag with "blocks close — re-dispatch or override" annotation (see `$PERRY_HOME/packs/software-ops/architecture.md`).
- Latest `architecture/audit-history/<date>.md` has open drift items older than 7 days → flag with "audit drift open" annotation; not blocking but visible.
- Open `incidents/*.md` with status `open` for ≥3 days → surface as P0 attention items even if not on BOARD (see `$PERRY_HOME/packs/software-ops/incidents.md`).
- Cadence row past its `Next due` → **read `cadence.overdue` from `perry-state --json`; it is already sorted oldest-first with `days_overdue` computed.** Do not scan the table by eye — this bullet said "surface by age" for a release before anything could compute an age, and the register it describes had three readers and no writer. Also read `cadence.undated` (a periodic ritual whose `Next due` cell yields no date — the row most likely to have quietly stopped) and `cadence.unreadable_frequency`. In a queue-mode track this is the highest-value question triage asks: **what recurs?** A request seen three times is not a request, it is a process nobody has written down — propose converting it to a Cadence row with a runbook, or record an explicit decline.

**Every stage move goes through the tool — this is a global invariant, not a triage rule.**

```
"$PERRY_HOME/bin/perry-task" stage <TASK-ID> --actor <actor> --stage <name>
```

It re-stamps `Stage since` in the same write and refuses a stage outside the track's declared vocabulary. The rule applies wherever `Stage` changes. `subcommands.md § close-task` loads this rule; `dispatch` and `autopilot` are not, so the invariant is restated in `reference/dispatch.md` and `reference/autopilot.md` rather than relying on this one. Hand-editing the cell leaves the clock reading from whenever the row was created, and pipeline triage's first question then measures nothing. Changing a row's `Stage` sets `Stage since` to today **in the same edit**, and writes the move into today's journal `## Status changes` line alongside any `Status` change. This is the rule that makes dwell time real: `Stage` and `Status` are orthogonal by design, so a `draft → review` move produces no `Status` change and would otherwise leave no trace anywhere. A stage moved without its timestamp is a clock that reads whatever it read last.

**Asking the user something, and recording their answer, go through the tool.**

```
"$PERRY_HOME/bin/perry-task" ask --actor <actor> --needed "<the question>" [--blocks <TASK-ID>]
"$PERRY_HOME/bin/perry-task" answer <USER-ID> --actor <actor> --answer "<what they decided>"
```

`ask` mints the `USER-NNN`, stamps **`Asked`** — a date — and creates
`## User Input Queue` after the priority tables if the board lacks it, adding
the `Asked` column to a section that predates it.

**An ask is a node in the dependency graph, so declare the edge both ways.**
`--blocks <TASK-ID>` writes the queue side; `perry-task depends <TASK-ID> --actor <actor> --on
<USER-ID>` writes the task side, and from contract 1.14 the reader resolves it:
a `pending` ask keeps the row in `blocked_by` exactly as an open task does, and
an **answered** one satisfies the edge exactly as a closed task does — at which
point the row turns up in `blocked_by_closed_rows` with `blocked_stale: true`,
because its question came back and the cell has not caught up. Blocking a row
on an ask with `--reason` prose instead puts it in
`blocked_without_dependency`, where nothing can resolve it. A `USER-` id this
project never minted is still `depends_on_unknown`.

**It stamps a date, not an age.** The column used to be `Idle`, a number a
human retyped, and the result was measurable: both rows on Perry's own board
read `—`, so the one field the queue exists for was empty, and a live project
had already dropped the column entirely. `Idle` is now optional in the schema
and still read where it exists; `today − Asked` is computed at read time and
comes back as `user_input_queue.oldest.idle_days`.

`answer` refuses without `--answer`: flipping the status without recording what
was decided leaves the row closed and the decision nowhere. It also refuses a
row that is already answered.

**`perry-state` counts only unanswered rows.** It used to count the whole
section — two answered rows on Perry's board were reported as two people
waiting, which is the single number in the payload a user is meant to act on.

The prose cell stays yours. The tool owns the id, the dates and the status;
what is being asked, and what was decided, are written by whoever knows.

**Registering a recurrence, and recording that it ran, go through the tool.**

```
"$PERRY_HOME/bin/perry-task" cadence-add --actor <actor>  --title "<what recurs>" \
    --frequency <weekly|monthly|quarterly|Nd|…> [--owner O] [--on YYYY-MM-DD]
"$PERRY_HOME/bin/perry-task" cadence-done <CAD-ID> --actor <actor> --evidence <path> \
    [--on YYYY-MM-DD] [--frequency F]
```

`cadence-add` mints the `CAD-NNN`, creates `## Cadence` after the priority
tables if the board lacks it, and **computes `Next due`** from the frequency.
`cadence-done` records the occurrence: it stamps `Last run`, writes
`Last evidence`, and **recomputes `Next due` from the row's own `Frequency`** in
the same write. That recomputation is the whole point of the pair.

**`Next due` is a derived cell, and a human was doing the arithmetic.** This is
the third time Perry has hit that: `Stage since` and `Arrived` store a date and
compute the age, and `Idle` was removed from the User Input Queue for it. Here
the stored value is a *date* rather than an age, so it does not rot overnight —
but it is wrong the moment the ritual runs, and only a person re-deriving
`frequency + last run` after every occurrence could keep it true. Nobody does,
and the result is visible on a real register: cells reading `2026-W32` and
`**2026-08-31**` with a parenthetical listing which occurrences were skipped.
`Last run` is now stored alongside, because it is the input `Next due` is
computed from and without it the due date is an assertion nothing on the board
can check.

**Reading is tolerant; writing is strict.** `cadence-add` refuses a frequency it
cannot schedule from, naming what it accepts. Nothing refuses a cell a project
already wrote: `continuous` and `hourly` are live in a real `Frequency` column
and are recorded as recurrences with no computable due date (`Next due: n/a`),
and prose in `Next due` is reported as unreadable rather than silently treated
as never due.

`cadence-done` refuses without `--evidence`, for the reason `done` does: a
recurring task that reports itself run and cites nothing is exactly the ritual
nobody notices has stopped happening. `--on` backdates a run that already
happened; `--frequency` changes the schedule in the same write, which is also
the escape hatch when a row's existing cell is prose the tool cannot read.

`perry-task` cannot close a Cadence row with `done` and never could — `## Cadence` is not a task section. A recurrence has no end; it is retired by removing the row.

**A wrong `Next action` is corrected with its own subcommand.**

```
"$PERRY_HOME/bin/perry-task" next <TASK-ID> --actor <actor> --next "<the real next step>"
```

The most common thing a triage does, and it had no tool path until TASK-041:
`status` is the only other writer of that cell and it refuses a no-op
transition, so correcting a plan meant changing a status the row did not
warrant, or hand-editing. `next` is its own event — a reader has to be able to
tell "the plan changed" from "the state changed", and folding them makes that
impossible forever.

**Write the next step, not the history.** A cell that explains what already
happened keeps `conformance.next_action_cites_closed` firing and re-reads as
stale at every triage; what happened is already in the journal and the event
log.

**A wrong `Title` is corrected the same way.**

```
"$PERRY_HOME/bin/perry-task" retitle <TASK-ID> --actor <actor> --title "<what this row is now>"
```

The same gap, one column over. A row filed as two pieces of work whose second
half later splits out to its own row carries a title describing work it will
never do, and until this existed it could not close honestly without a hand
edit. TASK-021 was the case that surfaced it.

Safe because the `Id` is the identity and never moves — a `Commitment` cell, a
linkage graph and every event point at the id, and none of them reads the
title. That is also why there is no subcommand for changing an id.

**Four cells are correctable in place, each with its own subcommand.**

```
"$PERRY_HOME/bin/perry-task" next     <ID> --actor <actor> --next "…"
"$PERRY_HOME/bin/perry-task" retitle  <ID> --actor <actor> --title "…"
"$PERRY_HOME/bin/perry-task" rung     <ID> --actor <actor> --rung V1..V6
"$PERRY_HOME/bin/perry-task" evidence <ID> --actor <actor> --evidence "…"
```

They are one implementation with four configurations — they were three copies
of one function before `evidence` made the pattern obvious. What is **not**
shared is the part that matters: each has its own event name, so a reader can
tell "the plan changed" from "what this is called changed" from "where this got
to". One event name would lose all three at once.

`next` is the only one that refuses a finished row: a completed row has no next
step, and writing one puts a live-looking instruction on finished work. Its
title, its rung and its evidence path stay correctable **while the row is still
on the board** — a project that stages finished work in place rather than
removing it.

**Once a row has left the board, `retitle` is the only one of the four that
still reaches it.** Closing removes the row, so all four normally refuse with
*is not a row on the board*; `retitle` alone falls back to the record in
`tasks.jsonl`. The reason is what the cell is. A rung and an evidence path are
claims about work that was checked, and a claim about finished work is finished
with it; a title is the row's NAME, `reference/user-load.md` forbids handing a
reader a bare id, and a name is needed for as long as anybody reads the record.
TASK-166 was the case that surfaced it — `TASK-029` sat `done` at `V3` with real
evidence and no title, reported by nothing and repairable by nothing.

A rung or an evidence path that is genuinely wrong on a closed row is a
different conversation and does not have a tool path: correcting either means
re-stating what was checked, which is a re-review, not a repair.

**A rung is set when the row is opened, and corrected the same way.**

```
"$PERRY_HOME/bin/perry-task" add --actor <actor>   --title "…" --rung V4
"$PERRY_HOME/bin/perry-task" rung  <TASK-ID> --actor <actor> --rung V4
```

`--rung` used to exist only on `done`, which is far too late to argue about
it. `add --rung` parsed and wrote nothing — a flag that is silently ignored is
worse than a missing one, because a missing flag refuses and this one reported
success.

`ADR-005` is what makes the cell load-bearing: the rung is a claim about **who
is hurt when the work is wrong**, not about who wrote it. V4 for what runs on a
project Perry did not create; V3 for what is internal to this repo; V5 wherever
`.perry/hook.md § High-stakes operations` matches, overriding both. A claim
like that has to be arguable in review, and one nobody can correct without a
hand edit is one nobody corrects.

**Every status change that is not a close goes through the tool too.**

```
"$PERRY_HOME/bin/perry-task" status <TASK-ID> --actor <actor> --status blocked|review|not_started|in_progress \
    [--reason "<why>"] [--next "<next action>"]
```

Three refusals, each protecting something a general status setter would walk past:

| Refuses | Because |
|---|---|
| `--status done` / `dropped` | Those close a row. `done` requires `--evidence` and validates the rung; `drop` requires `--reason`. Reaching either through `status` would route around both gates, so it points you at the right subcommand instead. |
| `blocked` with no `--reason` | A blocked row with no named dependency is one nobody can unblock. The reason also becomes the row's `Next action` (`blocked on <reason>`) when you don't supply one. |
| a status already set | A no-op transition writes a journal line asserting a change that did not happen. |

`review` is the one `dispatch` and `autopilot` use on every completion, which is
why the gap here was never cosmetic: for as long as `review` had no tool path,
every dispatch produced a post-tool board edit and buried the drift signal under
noise the lane generated itself.

**Before the per-mode walk, report every track that cannot run its own first
step.** `perry-state --json` → `project.config.tracks[].missing_defaults` names
them: the columns that track's mode has **no honest default** for and which it
left blank. Say it as a line per track and do not skip the step it blocks —

> `ops` (queue) has no `SLA`, so the breach step below cannot run. Declare one
> with `perry-config track ops --sla <value>`, or accept that this track has no clock.

This is not a nicety. `modes/pipeline.md § The mode contract`, `modes/queue.md § The mode contract` and
`schema/state-schema.json` all say **triage** reports the missing value rather
than skipping the step — and for a release it did not: `perry-lint` reported it
at file level, this procedure had nothing to read, and the rule was stated in
three documents and implemented in a fourth place none of them named. The field
above is what makes those three sentences true. It is computed from
`work_modes.modes.<mode>.no_default`, the same source the linter reads, so the
two cannot name different tracks.

**A queue track's breach step is now read, not eyeballed.** `perry-state --json`
→ `project.config.tracks[].sla_breaches` is `today − Arrived` per open row
against that track's `SLA`, oldest first, each with its `age_days`,
`over_by_days` and the `commitment` it breaches. Read the other two fields in
the same breath or the step has a blind spot, the same way step 5's three
cadence lists do:

- `…[].sla_no_clock` — open rows with no readable `Arrived`. **Not a pass.** A
  row with no clock is a different finding from a row inside its SLA, and it is
  the finding `perry-task route` was changed to preserve.
- `…[].sla_check.runnable` — whether the step ran at all. `false` carries a
  `reason` (`no-sla`, `sla-not-a-duration`, `not-a-queue-track`) and a `note`
  naming the track; report the note and do not report zero breaches, which is
  the answer a *declared* track with no rows gives (`runnable: true`,
  `rows: 0`). `no-sla` is the same gap `missing_defaults` names one paragraph
  up — say it once, at the step it blocks.

**Per-mode ordering.** The walk above is project-mode's. A track in another mode asks its own questions first, per its mode file: `pipeline` leads with oldest-item-per-stage and stages at their WIP limit (`modes/pipeline.md`); `queue` leads with SLA breaches and queue-depth trend after the intake drain (`modes/queue.md`); `inquiry` leads with open questions against the cap, then **`perry-lint --provenance`** — a dangling source id outranks everything else in that mode's list (`modes/inquiry.md`). Read the mode file for any track you are triaging.

Print the triage table. **For each row that needs a decision**, use `AskUserQuestion` (header = the TASK-ID, options = `Apply suggestion (Recommended) | Edit | Skip`). Batch up to 4 rows per call. Apply each accepted suggestion through the subcommand that owns it — `perry-task stage` / `status` / `drop` — which writes the board row and the journal line together. Do **not** then edit a store or write a `## Status changes` block yourself: the tool already wrote both, and doing it again duplicates the journal line and leaves a post-tool board edit that `unrecorded` will report. Anything the triage decided that is *not* a transition — a rewritten Next action, a note on why a row survives — goes in today's `## Notes`.

If a `BOARD.md` the project still holds is over its 200-line cap, triage MUST propose specific cuts before exiting.

After completed writes, follow `subcommands.md § Completion routing`.
