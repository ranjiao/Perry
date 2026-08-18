# PMO subcommands — full reference

The standup ritual + dispatch + delegate live in SKILL.md / `dispatch.md` / `delegate.md`. Everything else is here.

## Planning

### `plan-week`
Generate this ISO week's plan. Reads `phase/<current-NNN>-<slug>.md` (resolve via `phase/CURRENT`; if OKR present) and `BOARD.md` to see what's already on the board. Picks 3–5 highest-leverage open tasks for the week, marks them P0 (or proposes new P0 rows), confirms with user. **New rows go through `perry-task add --priority P0`**; a priority change on an existing row is still a hand edit and shows up as a post-tool edit at the next standup — the tool has no `priority` subcommand yet, and saying so beats pretending the path exists. Writes the day's plan entry to `journal/<YYYY-MM>/<today>.md` under `## Notes`. Drafts the week's row in `weekly/<YYYY-WW>.md`.

### `triage`

**Read the intake block first — do not count rows by hand.**

```
"$PERRY_HOME/bin/perry-task" list --all --json     # → .intake
```

`route <n>` and `resolve-intake <n>` act on a row **position**, and until the
payload carried one the only way to get it was to open `BOARD.md` and count —
twenty lines below the rule forbidding exactly that. `.intake` gives you `n`
per row, `undischarged`, and `oldest_undischarged` to start from.

**At the end of a review period, sweep:**

```
"$PERRY_HOME/bin/perry-task" intake-sweep
```

Discharged rows move to today's journal with their `Outcome` intact. This rule
lived in `modes/queue.md` and nothing implemented it, which matters because the
same file rests its overflow argument on it: intake pressure is supposed to mean
*taking on more than you discharge*, not *having discharged a lot*.

**Step 0 — drain `BOARD.md § Intake`, before anything else.** Applies to every queue-mode track. If the track exists and the section does not, it is created by the first `perry-task add` on a queue track or by `perry-task intake`; do not hand-write it, and do not skip the step — a self-skipping step is indistinguishable from a step that has nothing to do. Walk it top to bottom; every row gets exactly one outcome, and none may be left as-is:

- **Routed** to a track → `"$PERRY_HOME/bin/perry-task" route <n> --track <track> [--priority P1 | --group "<heading>"]`, where `<n>` is the intake row's position. `--group` names the project's own heading on a board that does not use `P0`/`P1`/`P2` — the same flag, and the same meaning, as on `add`. The tool carries `Arrived` onto the new row, sets `Stage` to the track's first post-intake stage, and writes the destination back into the intake row's `Outcome` so the request's record is complete. Carrying `Arrived` is not bookkeeping: `today − Arrived` is the number every SLA check measures, so a routing that drops it makes the mode's own breach check uncomputable and silently exempts the row from the only clock governing it (`modes/queue.md`). It was dropped, by this procedure, until the tool did it structurally.
- **Dropped** → `"$PERRY_HOME/bin/perry-task" resolve-intake <n> --outcome dropped --reason "…"`. "We are not doing this" is a real answer, and an undropped request is one that gets re-asked. The tool writes the `Outcome` cell, the journal line and the event, so a declined request is as visible as a routed one.
- **Deferred** → same command with `--outcome deferred --reason "<the named condition>"` — never a bare "later".

**Recording an arrival is a separate act from draining one.** A request that
reaches you between triages — in chat, from a colleague, out of a meeting — is
written down when it arrives, not remembered until the next walk:

```
"$PERRY_HOME/bin/perry-task" intake --title "<the request, in the asker's words>" \
    [--arrived YYYY-MM-DD]
```

`--arrived` defaults to today and is there for a request that reached you
earlier than you are recording it; backdating it honestly is what keeps the SLA
clock true. Do this whenever a request arrives on a queue-mode track, not only
during triage — an intake section that is only ever *drained* and never *filled*
is the failure `modes/queue.md` describes as "a track whose intake is always
empty while work is clearly happening."

A row still sitting in intake for **more than 14 days** is reported by age. Not "after two triages": `Arrived` is recorded and nothing counts triages, so elapsed time is computable and a triage count is not. And if intake is pushing `BOARD.md` toward the 200-line cap, **say so as a finding** — a project taking on more than it discharges is exactly what that pressure means. Do not raise the cap and do not move the section somewhere it can grow unnoticed; if it recurs, that is a reason to revisit DESIGN-003 § 4 decision 3, not to relax it quietly.

**Read the payload, then walk what it returns — do not open `BOARD.md` and
look.** Eyeballing a file for numbers is the one thing Perry's oldest rule
forbids, and this procedure was written before there was an alternative:

```
"$PERRY_HOME/bin/perry-task" list --all --json
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
| `next_action_cites_closed` | The row is waiting on work that finished. Re-read the `Next action` with the user — it is usually one edit from correct, and it is the cheapest stale row to fix. Only `TASK-` ids are resolved; a cell citing a `DESIGN-` or `USER-` id is not checked and you still have to read it. |
| `rows_with_no_computable_age` | No age exists for these. Every staleness rule below is an age comparison, so they were being read as fresh forever. Ask about each rather than skipping it. |
| `has_event_log: false` | The project predates the writer. `created` / `updated` / `timeline` are empty for every row and **that is not an error** — fall back to the row's own date cells. |

Then walk the rows the payload returned. For each open row:
- Stale? (P0 idle ≥3d, P1 idle ≥7d, P2 idle ≥14d, measured from `updated`) → flag. **A row in `conformance.rows_with_no_computable_age` has no age**: no event, and the six standard board columns carry no date. Do not treat it as fresh — that is what the old rule did to two thirds of Perry's own board. Ask instead: *"this row has no recorded age; is it still live?"*
- Same dependency cited in ≥2 rows? → structural blocker
- `done` claim without evidence file in `evidence/<YYYY-MM>/` → `"$PERRY_HOME/bin/perry-task" status <ID> --status review --next "needs an evidence file before it can close"`
- Owner is an agent and the row is still `not_started`? → flag. **Read the row, not the chat**: `delegate` now writes `in_progress` with `delegated to <agent>; awaiting paste-back` in `Next action`, so a delegated task is visible in state. This check used to look for "a recent delegation prompt in chat", which is not a surface any tool can read and not a record that survives the session.
- Row inflated (long inline notes leaking into the board) → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only Status + Next action + Evidence path on the board.
- Spec has `Deployed: yes`, status `review`, but no `Runbook:` field or runbook file missing → flag with "blocks close" annotation (see `$PERRY_HOME/packs/software-ops/runbooks.md`).
- Spec's `Touches architecture:` non-empty, status `review`, but latest dispatch evidence has no `## Architecture review` PASS → flag with "blocks close — re-dispatch or override" annotation (see `$PERRY_HOME/packs/software-ops/architecture.md`).
- Latest `architecture/audit-history/<date>.md` has open drift items older than 7 days → flag with "audit drift open" annotation; not blocking but visible.
- Open `incidents/*.md` with status `open` for ≥3 days → surface as P0 attention items even if not on BOARD (see `$PERRY_HOME/packs/software-ops/incidents.md`).
- Cadence row past its `Next due` → **read `cadence.overdue` from `perry-state --json`; it is already sorted oldest-first with `days_overdue` computed.** Do not scan the table by eye — this bullet said "surface by age" for a release before anything could compute an age, and the register it describes had three readers and no writer. Also read `cadence.undated` (a periodic ritual whose `Next due` cell yields no date — the row most likely to have quietly stopped) and `cadence.unreadable_frequency`. In a queue-mode track this is the highest-value question triage asks: **what recurs?** A request seen three times is not a request, it is a process nobody has written down — propose converting it to a Cadence row with a runbook, or record an explicit decline.

**Every stage move goes through the tool — this is a global invariant, not a triage rule.**

```
"$PERRY_HOME/bin/perry-task" stage <TASK-ID> --stage <name>
```

It re-stamps `Stage since` in the same write and refuses a stage outside the track's declared vocabulary. The rule applies wherever `Stage` changes. `close-task` is in this same file and does load it; `dispatch` and `autopilot` are not, so the invariant is restated in `reference/dispatch.md` and `reference/autopilot.md` rather than relying on this one. Hand-editing the cell leaves the clock reading from whenever the row was created, and pipeline triage's first question then measures nothing. Changing a row's `Stage` sets `Stage since` to today **in the same edit**, and writes the move into today's journal `## Status changes` line alongside any `Status` change. This is the rule that makes dwell time real: `Stage` and `Status` are orthogonal by design, so a `draft → review` move produces no `Status` change and would otherwise leave no trace anywhere. A stage moved without its timestamp is a clock that reads whatever it read last.

**Asking the user something, and recording their answer, go through the tool.**

```
"$PERRY_HOME/bin/perry-task" ask --needed "<the question>" [--blocks <TASK-ID>]
"$PERRY_HOME/bin/perry-task" answer <USER-ID> --answer "<what they decided>"
```

`ask` mints the `USER-NNN`, stamps **`Asked`** — a date — and creates
`## User Input Queue` after the priority tables if the board lacks it, adding
the `Asked` column to a section that predates it.

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
"$PERRY_HOME/bin/perry-task" cadence-add  --title "<what recurs>" \
    --frequency <weekly|monthly|quarterly|Nd|…> [--owner O] [--on YYYY-MM-DD]
"$PERRY_HOME/bin/perry-task" cadence-done <CAD-ID> --evidence <path> \
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
"$PERRY_HOME/bin/perry-task" next <TASK-ID> --next "<the real next step>"
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
"$PERRY_HOME/bin/perry-task" retitle <TASK-ID> --title "<what this row is now>"
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
"$PERRY_HOME/bin/perry-task" next     <ID> --next "…"
"$PERRY_HOME/bin/perry-task" retitle  <ID> --title "…"
"$PERRY_HOME/bin/perry-task" rung     <ID> --rung V1..V6
"$PERRY_HOME/bin/perry-task" evidence <ID> --evidence "…"
```

They are one implementation with four configurations — they were three copies
of one function before `evidence` made the pattern obvious. What is **not**
shared is the part that matters: each has its own event name, so a reader can
tell "the plan changed" from "what this is called changed" from "where this got
to". One event name would lose all three at once.

`next` is the only one that refuses a finished row: a completed row has no next
step, and writing one puts a live-looking instruction on finished work. Its
title, its rung and its evidence path stay correctable.

**A rung is set when the row is opened, and corrected the same way.**

```
"$PERRY_HOME/bin/perry-task" add   --title "…" --rung V4
"$PERRY_HOME/bin/perry-task" rung  <TASK-ID> --rung V4
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
"$PERRY_HOME/bin/perry-task" status <TASK-ID> --status blocked|review|not_started|in_progress \
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
> in `.perry/config.md § Tracks`, or accept that this track has no clock.

This is not a nicety. `modes/pipeline.md § The mode contract`, `modes/queue.md § The mode contract` and
`schema/state-schema.json` all say **triage** reports the missing value rather
than skipping the step — and for a release it did not: `perry-lint` reported it
at file level, this procedure had nothing to read, and the rule was stated in
three documents and implemented in a fourth place none of them named. The field
above is what makes those three sentences true. It is computed from
`work_modes.modes.<mode>.no_default`, the same source the linter reads, so the
two cannot name different tracks.

**Per-mode ordering.** The walk above is project-mode's. A track in another mode asks its own questions first, per its mode file: `pipeline` leads with oldest-item-per-stage and stages at their WIP limit (`modes/pipeline.md`); `queue` leads with SLA breaches and queue-depth trend after the intake drain (`modes/queue.md`); `inquiry` leads with open questions against the cap, then **`perry-lint --provenance`** — a dangling source id outranks everything else in that mode's list (`modes/inquiry.md`). Read the mode file for any track you are triaging.

Print the triage table. **For each row that needs a decision**, use `AskUserQuestion` (header = the TASK-ID, options = `Apply suggestion (Recommended) | Edit | Skip`). Batch up to 4 rows per call. Apply each accepted suggestion through the subcommand that owns it — `perry-task stage` / `status` / `drop` — which writes the board row and the journal line together. Do **not** then update `BOARD.md` or write a `## Status changes` block yourself: the tool already wrote both, and doing it again duplicates the journal line and leaves a post-tool board edit that `unrecorded` will report. Anything the triage decided that is *not* a transition — a rewritten Next action, a note on why a row survives — goes in today's `## Notes`.

If `BOARD.md` is over the 200-line cap, triage MUST propose specific cuts before exiting.

## Cadence (recurring; never consume P0 slots)

### `status` (a.k.a. `friday-review`)
This week's PMO status report using the format in `reporting-format.md`. Reads `BOARD.md` + this week's journal entries. Save to `weekly/<YYYY-WW>.md`.

### `monday-plan`
Run at start of week. Reads `BOARD.md` + last week's `weekly/<YYYY-WW>.md` if any. Output: priorities, P0 set, blockers needing user input, scope cuts. Append to current week's `weekly/` file AND write a `## Notes` entry in today's journal.

### `midweek-check`
Mid-week pulse. Reads `BOARD.md` + journal entries since Monday. Output: P0 movement check, blocker escalations, cost-ceiling progress, tests/verification reminders. Write to today's journal.

### `mid-phase-review`
Triggered manually (or surfaced by the standup when ≥40–60% of phase day budget elapsed). Reads `BOARD.md` + journal entries since the current phase started (resolve start date from the phase file header). Mark each Objective `on_track | at_risk | off_track` based on KR progress. Apply any **Phase Scope Reduction Rule** declared in `phase/<NNN>-<slug>.md`. Recommend scope cuts. Save to `evidence/<YYYY-MM>/midphase-review-<NNN>-<slug>.md`.

**Inline health-check** (added to mid-phase-review): run `/pmo health-check` (see `reference/health-check.md`) and fold its findings — audit violations, runbook gaps, incident patterns — into the mid-phase-review report. The detailed report lives at `evidence/<YYYY-MM>/health-check-<YYYY-MM-DD>.md`; the mid-phase-review summarises the top decision items inline.

**Digest archive review** (added to mid-phase-review): if `knowledge/` exists, scan for active digests with no reference in `BOARD.md` / `journal/` / `evidence/` / `DECISIONS.md` / `phase/` for ≥ `archive_inactive_days` days (default 90; override per-project hook). For each candidate, use `AskUserQuestion` (header = digest basename, options): `Archive (Recommended) | Keep active — still relevant | Mark eternal — never propose archive | Delete entirely`. On Archive: flip `Status: archived` in the digest header + record `Archived: <date> (reason: <user input>)`. On Eternal: flip `Status: eternal`. On Delete: `git rm` source + digest. Update `knowledge/INDEX.md`. See `reference/digests.md § Archive lifecycle` for full detail. (Note: `health-check` already includes the digest stale scan; running it here is the same scan, surfaced for the user to act on.)

### `end-phase-retro`
Triggered when OKR `score-phase` is about to run (or explicitly by the user). Reads `BOARD.md` + all journal entries since the current phase started + `evidence/<YYYY-MM>/` for the calendar months the phase spanned. For each KR: mark `achieved | partial | missed | dropped`, link evidence file. Capture lessons. Identify carry-over candidates. Save to `evidence/<YYYY-MM>/retro.md` (using the calendar month at scoring time). This is OKR's input for `plan-phase` of the next phase.

**Inline health-check** (added to end-phase-retro): run `/pmo health-check` (see `reference/health-check.md`). The retro additionally folds in:
- **Incident feedback-loop ratio**: of all incidents resolved during this phase, how many produced derived changes (architecture / runbook / digest)? A low ratio + recurring components = a structural problem worth a KR in next phase's OKR.
- **Audit drift trend**: how many `ARCHITECTURE.md`-vs-code drift items from the last audit are still open at phase-end? Carry them into next phase's OKR as either resolution KRs, deferral ADRs, doc edits, or `Not Doing` lines (see `goals/reference/phases.md § plan-phase <slug>`).
- **Runbook coverage**: count of deployed components without runbook, vs same count at phase start. Drift in this number is a red flag.

These three numbers go into `evidence/<YYYY-MM>/retro.md` § "Health metrics" section so OKR's `plan-phase` for next phase can read them directly.

**Knowledge promotion** (DESIGN-006 § 5.4; procedure in `reference/promotion.md`): **at most one question for the whole retro**, and only for a lesson the retro itself already identified as recurring across two or more tasks. Run `"$PERRY_HOME/bin/perry-knowledge" propose --source "evidence/<YYYY-MM>/retro.md" --root . --json` first — `fires: false` means ask nothing — and write it with `perry-knowledge promote`, never by hand. Batching is the named risk (DESIGN-006 § 7): a retro that offers six cards produces six rubber stamps. If the phase produced several durable claims, promote one and note the rest as candidates in the retro; the next `close-task` will offer them where they belong.

**Digest archive review** (same procedure as `mid-phase-review`; second pass per phase): re-scan archive candidates and process via `AskUserQuestion`. Phase-end is the safer gate — anything still un-referenced after a full phase is more likely truly inactive. Also at phase-end, **rebuild `knowledge/INDEX.md` fully** (not just incrementally): re-grep all references for `Last referenced` dates, recompute counts, alphabetize within topics. Cheap operation (~2-3 sec for 30 digests).

## Decisions & risk

### ~~`decide <topic>`~~ — moved to the `decide` lane

ADR recording left this lane on 2026-08-16, when the signed hand-off contract
(`$PERRY_HOME/SKILL.md § The hand-off contract`) gave `DECISIONS.md` and
`decisions/` to `decide`. It is now **`/perry decide adr <topic>`**, with the
same `--supersede` / `--expire` / `--archive` lifecycle, and the full procedure
lives at `$PERRY_HOME/decide/reference/decisions.md`.

**`work` no longer writes `DECISIONS.md` or `decisions/` at all.** If a request
lands here that would, route it — do not write and mention it afterwards. That
is the refusal case the contract names.

The old-monolithic-`DECISIONS.md` migration moved with it.

### `risk`

**Raising a risk and clearing one both go through the tool.**

```bash
"$PERRY_HOME/bin/perry-task" risk-add   --title "<the risk, in your words>" [--opened YYYY-MM-DD]
"$PERRY_HOME/bin/perry-task" risk-clear <RX-ID> --reason "<why it is over>"
"$PERRY_HOME/bin/perry-task" risk-migrate            # bullets → the table, once
```

`BOARD.md § Top risks` is a table — `| ID | Risk | Opened | Status |` — and the
rule is the one `## Intake` and `## User Input Queue` already follow: **the tool
owns the row and every computed cell; the agent owns the prose cell.** `risk-add`
mints the `RX-NNN`, stamps `Opened`, and writes the board row, the journal line
and the event together. `Risk` is your sentence and nothing rewrites it.

Do not hand-write a row and do not retire a risk by striking it through. That
was the old shape and it had two defects nothing could fix from the outside: a
`~~struck-through~~` risk is decoration, not a field, so it stayed in every
count forever — one on Perry's own board survived a day past being cleared —
and with no id column the reader split the first sentence on whitespace and
published `id: "Perry"`, `title: "is half-adopted: …"`.

**A cleared risk stays on the board.** `risk-clear` writes
`cleared <date> — <reason>` into `Status` and the row remains: it is the record
that the mitigation worked. It simply stops counting.

**`perry-state` reports open risks only**, with `age_days` computed from
`Opened` at read time — the same rule as `Asked`/`Idle` on the User Input
Queue, and for the same reason. `risks.source` is one of four values —
`table`, `bullets`, `mixed`, `none` — saying which form the payload was read
from; on a bullet the `id` is invented and `age_days` is `null`, and a reader
is entitled to know which it got. `mixed` means the rows came from more than
one form, which now only happens on a board that has not migrated: **once
`BOARD.md § Top risks` is a table, that table is the register and
`PROJECT_STATE.md` is no longer merged into it.** Before the table existed both
files held bullets and both ids were invented out of the prose, so a risk
written into both collapsed by accident — the invented ids were the first word
of each sentence. Minted ids can never collide with invented ones, so the merge
would double-report every shared risk, once open and once cleared. Migrating is
the project saying where its risks live, and it is read as exactly that — so a
project that kept a second list in `PROJECT_STATE.md` should `risk-add` the
still-live ones onto the board, because after migrating they stop being
counted. Measured on one real project: the merged count went 13 → 9. Four
`PROJECT_STATE.md` entries left it, three of them already marked closed there
and one still live — that one is the `risk-add` the migration asks for. The
alternative, on the same board, was 15: every shared risk counted twice, one
of them reported open and cleared at once.

**An older board keeps working, and is never converted behind your back.** A
bullet list is still read, and `risk-add` on one **refuses**: it says how many
bullets it would have to rewrite and prints `perry-task risk-migrate`, which is
the command that does it (`--dry-run --json` first shows every row it would
write). "No automatic rewrite of a project's existing structure. Adoption
proposes; the user declares" is an Anti-Goal, and a section of hand-written
risks is exactly the kind of structure it protects.

The conversion carries every bullet across **verbatim** into its own row with
`Opened` left empty — the date a pre-existing risk was raised is not recorded
anywhere and stamping today would assert it is new. A bullet the reader already
treated as resolved (`~~strike~~` or `**RESOLVED`) migrates as `cleared`, with
whatever date the human wrote in it. A placeholder (`- (no active risks)`) is
not a risk and is not migrated; a section holding only one is not asked about,
because there is nothing of yours to protect. A table under this heading with
no `Risk` column — a legend, a severity key — is refused by both commands
rather than written into: the reader reads that section's bullets, and adding
the risk columns to a legend would make it stop.

There is deliberately **no `Severity` column**: both real projects surveyed
write severity inside the sentence (`H · …`, `🔴 …`), so it stays derived from
the statement rather than becoming a column nothing on a real board fills.

**Triage has no risk step.** This section used to claim it did — "triage still
asks, for each open risk: still valid? severity changed? mitigation in place?"
— and the `triage` procedure above has never contained the word *risk*. What
exists instead is the payload: `perry-state` reports the open rows with
`age_days`, so a risk open ninety days and untouched is visible without a
procedure asking about it. Retiring one is `risk-clear`; changing what it says
is a rewrite of the `Risk` cell, which is yours. If a triage step is ever
written, note that the schema has nowhere to record "mitigation in place" —
`Status` is a binary plus a closing reason — so it would need a column first.

### `nudge`
For every User Input Queue item idle ≥5 days, surface a one-line reminder in chat with: USER-id, what's needed, what it blocks, days idle, original ask context.

## Task lifecycle

### `add-task` (interactive)
After OKR `plan-week` (or any other source) proposes a task and the user approves, PMO does THREE things — the third is conditional on priority.

**First, an input-quality pass** (`$PERRY_HOME/reference/input-quality.md § 4 Task`): check the task's Verification is falsifiable (not "looks good"), Deliverable is an artifact (not an activity), Owner is a single value from the Owner model, Priority is justified (P0 only if it blocks a Must-Have), and a `kr:` linkage is present when the task came from `plan-week`. Surface ≤3 issues, advisory + override — fix with the user or write as-is with a one-line journal reason. Never silently rewrite. (Tasks arriving already-clean from `plan-week`, which ran the same §4 pass, usually pass with `✓ Input quality: clean`.)

**Then, the KR-attribution gate** (`$PERRY_HOME/reference/okr-linkage.md`) — hard, not advisory: resolve the task's KR by stable ID through `phase/<NNN>-linkage.md` (explicit `kr:` → Project ID → registered alias). If it resolves to exactly one KR, set `kr:` and continue. If it resolves to zero or many — a drifted/ambiguous name, or a Project no registry row claims — **do NOT fuzzy-match**: ask the user (`AskUserQuestion`, header `"KR attribution"`, options = the candidate KR IDs + text, plus "Other → new/none"). Record the chosen KR in the spec, then **hand the result to `okr`**, which is the only writer of `phase/` (`goals/reference/linkage.md`):

- resolved → `/perry goals link <TASK-ID> <KR-ID>` (appends the edge to that KR's `tasks[]`)
- a name confirmed as an existing Project → `/perry goals link --alias <PROJECT-ID> "<name>"`
- unresolved, or the user is unavailable → `/perry goals link --unlinked <TASK-ID>`, and write the BOARD row with `attribution: unlinked` so it stays out of every KR roll-up until the standup surfaces it

Print the exact command — **in its `/perry <lane> …` form**, since this string is quoted to the user and `/okr` is a withdrawn host command that `setup` deletes and that collides with `lark-okr`. Don't edit `phase/` yourself.

**Mode columns — the write path, not just the column.** A column nobody writes is not a control. For a row on a track whose mode is not `project`, `add-task` sets these in the same edit that creates the row:

| Track mode | Set at creation |
|---|---|
| `pipeline` | `Track`, `Stage` = the first stage of the track's `Stages`, `Stage since` = today, `Commitment` if the row discharges one |
| `queue` | `Track`, `Stage` = first post-intake stage, `Arrived` = the date it arrived (carried from `## Intake`, or today for a row raised directly), `Commitment` if applicable |
| `inquiry` | `Track`, `Stage` = `open`, `Stage since` = today, `Parent` = the question this was split from, or blank for a root |
| `project` | nothing extra — this is today's behavior, unchanged |

**Add the column if the board has none.** You cannot set a cell in a column with no header, and `BOARD_TEMPLATE.md` ships six columns — so the first non-`project` row on a board also adds the headers it needs, in the same edit. `perry-task add` and `route` do this via `ensure_columns`; nothing is expected of you.

(An earlier draft justified this as "the same clause `close-task` already has for `Verification`." There is no such clause. `Verification` is a declared *optional* column in `schema/state-schema.json`, but `close-task` removes the row rather than stamping it — the rung is written to the journal line and the event, which is where `perry-task list` reads it from. The back-reference pointed at a precedent that never existed; the rule stands on its own.)

A pipeline- or inquiry-mode board must carry `Stage` and `Stage since`; a queue-mode board must carry `Stage` and `Arrived`. They are optional in the schema so that no pre-DESIGN-003 board is invalidated, **not** so a mode track can skip them — a track that does is missing the clock its own triage reads.

**Creating a queue-mode row also creates `BOARD.md § Intake` if it is absent**, with its three columns (`Arrived`, `Request`, `Outcome`). Intake is the organ queue mode is built on and the first thing `triage` walks; a section nothing creates means step 0 no-ops forever, and `modes/queue.md`'s warning about a track "whose intake is always empty while work is clearly happening" would describe the guaranteed default rather than a risk.

1. **Create the row with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" add --title "<title>" --owner "<owner>" \
       --priority <P0|P1|P2> [--track <track>] [--next "<next action>"] \
       [--parent <ID>] [--commitment <Id>]
   ```

   It mints the ID from board ∪ journal ∪ events (never reused, never
   accidentally gapped), stamps the timestamp at call time, sets `Stage` /
   `Stage since` / `Arrived` for the track's mode, **creates any column or
   section the mode needs and the board lacks**, and writes the board row, the
   journal line and the event — the row and the journal line atomically with
   each other, the event appended after and reported if it fails.

   **Which id family it mints into.** `TASK-NNN` unless the board says
   otherwise, and the board says otherwise in exactly one way: if every
   numbered id in its task tables shares one prefix, a new id joins it. A board
   of `AIM-001`…`AIM-017` gets `AIM-018`, where it used to get `TASK-001` — a
   second id family appearing on a board that had one, with no way to ask for
   the first (TASK-060, reported by aiMark).

   Perry stops at *exactly one* and does not take the most common. A real board
   here carries 36 families in its task tables, declared in its own
   `## ID prefixes` section, and they are not stylistic — `IPS-*` / `ALLOC-*` /
   `DUE-*` mean one workstream and `TECH-*` / `DATA-*` another, filed in
   separate sections. Picking the plurality winner would mint an id that
   asserts a workstream nobody chose, and an id is permanent. A `TASK-001` on
   such a board is visibly Perry's and claims nothing.

   ```
   "$PERRY_HOME/bin/perry-task" add --title "…" --deliverable "…" \
       --verification "…" --prefix AIM
   ```

   `--prefix` names the family outright and wins over adoption. It is how a
   front-end that cannot supply an id asks for one in the right family, and it
   is the only answer on a board carrying several. Pass the prefix, not an id
   (`AIM`, not `AIM-018`); segments join with `-` and each starts with a letter,
   so `ARCH-V2` is a prefix and `AIM-018` is refused. `USER`, `RX`, `CAD` and
   `CADENCE` are refused too — `perry-task` mints those for the queue, risk and
   cadence registers on the same board, and a task numbered in one of them
   would collide with rows the tool writes itself. `route` takes `--prefix` and
   adopts by the same rule; both verbs mint, so both had to.

   Do not hand-write the row. Every field above was one an agent supplied and
   got wrong at least once: malformed pipes, a reused ID, a timestamp that was
   an assertion, a clock nobody wound. `perry-state` reports a hand-written row
   as `unrecorded` at the next standup — reported, not refused, because editing
   your own markdown is legitimate; but it is visible, and that visibility is
   the point.

   **On a board that does not use `P0`/`P1`/`P2`**, name the project's own
   heading instead:

   ```
   "$PERRY_HOME/bin/perry-task" add --title "…" --deliverable "…" \
       --verification "…" --group "Open — 工程线"
   ```

   A real year-old project files work under headings like that, and `add`
   refused it outright until TASK-019/020's review found it. Perry will **not**
   create a priority section on such a board — rewriting a project's structure
   is an Anti-Goal — but it will add the columns it needs to write a row,
   widening existing rows with empty cells rather than dropping the data that
   does not fit. Run `add` without `--group` to see the sections a board
   actually offers; the refusal lists them.

   **`route` takes `--group` too, and means the same thing by it.** It did not
   until TASK-053: the flag parsed and `route` never read it, so the intake
   drain could not run at all on a board with no `## P0`/`## P1`/`## P2` — and
   the refusal that told the user to pass the heading to `--group` was telling
   them to pass it to a flag that verb threw away. Both verbs resolve the
   landing section through one function now, so a board Perry can `add` into
   is a board Perry can `route` into.

   **Refusals are outcomes, not errors.** The tool exits 1 and writes nothing on
   a missing title, an undeclared track, a priority outside `P0`/`P1`/`P2`, a
   stage outside a track's vocabulary, or a `--stage` on a `project`-mode track
   (which has none). Read the message and fix the call; do not fall back to
   editing the file.

2. **Append the full definition** to `journal/<YYYY-MM>/<today>.md` under `## New tasks added`, including full schema (Owner, Priority, Deliverable, Verification, Dependencies, Out of scope, KR linkage). The tool writes the one-line status change; this block is the rich record and is still written by hand.
3. **For P0 and P1 tasks**, ALSO write `evidence/<YYYY-MM>/<TASK-ID>-spec.md` containing the same schema PLUS the dispatch-routing fields below. BOARD's Evidence column points at this spec file. P2 / backlog / watch may rely on the journal entry alone — promote a P2 to P1 → write the spec at promotion time.

   **Required header fields in every spec file** (used by `dispatch` and `close-task`):
   ```
   > Dispatch mode: auto | manual               # default 'manual'; 'auto' is explicit opt-in
   > Executor: claude-subagent | codex | manual # only consulted when Dispatch mode = auto
   > Estimated cycle: small | medium | large    # informs sync vs async + cycle-time tracking
   > Subjective verification: <list, or '(none)'>
   > Touches architecture: <comma-separated §-section refs (§2, §3, §6.NN-3), or '(none)'>   # used by dispatch pre-flight + review agent; see $PERRY_HOME/packs/software-ops/architecture.md
   > Deployed: yes | no                          # default 'no'; 'yes' triggers runbook + observability gate at close
   > Runbook: runbook/<slug>.md                  # required ONLY when Deployed: yes; path must exist before close-task
   ```

   **When `Deployed: yes`, the spec ALSO requires an `## Observability` section** with three sub-fields (see `$PERRY_HOME/packs/software-ops/runbooks.md § Spec contract`):
   ```
   ## Observability
   - Success signal:   <log line / metric / endpoint / `command` output that proves it's working>
   - Failure diagnosis: `<single command>` — one line that answers "what's broken right now"
   - Runbook path:     runbook/<slug>.md
   ```

   **Choosing executor (spec writer responsibility)**:
   - `claude-subagent`: small task, needs MCP tools the parent session has, needs codebase familiarity.
   - `codex`: medium/large self-contained, no MCP dependency, save Claude Code quota.
   - `manual`: high-stakes per project hook (production deploys, prod credentials, .env, paid APIs, cost ceiling raise) OR subjective decision-making (research candidate selection, design choices).

   Commit to the choice with one inline reason: `> Executor: codex (high confidence — pure analytics task, no MCP needed)`.

The spec uses the same template as the journal `## New tasks added` block; not duplication, two surfaces with different access patterns:

| File | Purpose | Lifetime |
|---|---|---|
| `journal/<YYYY-MM>/<creation-day>.md` | Historical "this was created here" record | Frozen after the day ends |
| `evidence/<YYYY-MM>/<TASK-ID>-spec.md` | Live schema for dispatch / re-dispatch / audit | Mutable as scope refines (subsequent edits must add `## Changes` log inside the file) |
| `evidence/<YYYY-MM>/<TASK-ID>-*.md` (other names) | Deliverable artifacts: reports, drill records, checklists | Per-deliverable |

When the task closes, leave the spec file in place — it's the canonical scope record.

Slug IDs are never reused or recycled across months.

If the task needs a working artifact from day one (checklist, design ladder, subtasks), the working artifact lives at `evidence/<YYYY-MM>/<TASK-ID>-<slug>.md` (separate file from the spec).

### `close-task <id>`
Reject if no evidence path provided.

**Pre-close gate 1 — `Touches architecture:` requires review agent PASS** (see `$PERRY_HOME/packs/software-ops/architecture.md § close-task gate`):
1. Open `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. If header has `Touches architecture:` non-empty:
   - Find the latest dispatch evidence file for this task (`evidence/<YYYY-MM>/<TASK-ID>-dispatch-*.md`, latest mtime).
   - Verify it contains an `## Architecture review` section ending with `PASS`. `FAIL` or missing → refuse close.
2. **If review missing or FAIL**, use `AskUserQuestion` (header = TASK-ID, options): `Re-dispatch to fix (Recommended) | Override — close without arch review (NOT recommended) | Keep as review`. "Override" requires written reason; logged as `architecture-override: <reason>` in journal.
3. `Touches architecture: (none)` or field absent → skip this gate.

**Pre-close gate 2 — `Deployed: yes` requires a runbook** (see `$PERRY_HOME/packs/software-ops/runbooks.md § close-task gate`):
1. Open the spec. If header has `Deployed: yes`:
   - `Runbook:` field must be present AND point at an existing file.
   - The referenced runbook file must have all four mandatory sections (What / Healthy / Failures / Escalation), non-empty.
   - The spec must contain an `## Observability` section with non-empty Success signal / Failure diagnosis / Runbook path.
2. **If any check fails**, refuse close. Use `AskUserQuestion` (header = TASK-ID, options): `Add runbook now (Recommended) | Keep as review until runbook exists | Override — close without runbook (NOT recommended)`. "Override" requires a written reason; the override is logged under `## Status changes` as `runbook-override: <reason>`.
3. `Deployed: no` or field absent → skip this gate.

**Pre-close gate 3 — record the verification rung** (DESIGN-003 § 5.3; `schema/state-schema.json § verification`):

Before flipping status, capture **how** this was verified, not just that evidence exists. Pre-select the track's `Default rung` from `.perry/config.md § Tracks` (V3 for `project`, V5 for `pipeline`, V2 for `queue`, V4 for `inquiry`), so the ordinary case costs the user no decision at all — they confirm rather than choose.

Two rules override the default, and neither is optional:

- **Consequence beats mode.** If the task matches `.perry/hook.md § High-stakes operations` — outward-facing, irreversible, or carrying money, legal or safety exposure — the rung is **V5 minimum** whatever the mode default says. `perry-lint --verification` reports the mismatch as `consequence-needs-signoff`, so a close below V5 on a high-stakes row will surface at the next standup regardless.
- **V4 needs a rubric, V5 needs a signature.** A `V4` close must cite the acceptance-criteria file the reviewer scored against, and that reviewer must not have seen the reasoning that produced the artifact. A `V5` close must record **name, date, and what was checked** — "reviewed" is not what was checked.

**Choose** the rung here and hand it to `perry-task done --rung`. Do not write it into the row or the journal yourself — the tool writes both, and doing it here as well produces a duplicate journal line and an edit to a row the next command removes. **Advisory this release** by DESIGN-003 § 4 decision 4: a missing or unsatisfiable rung is reported, never refused, because a hard gate on day one would retroactively invalidate every `done` row written before rungs existed. The number to watch is `unrated` in `perry-state`'s `board.verification` — it is what should shrink before the gate hardens.

**Pre-close gate 4 — inquiry mode** (`modes/inquiry.md`). On an inquiry-mode track:
1. `evidence/<YYYY-MM>/<ID>-answer.md` must exist — the question restated, the answer, the claims with their `[SRC-n]` citations, and what would change the answer. The mode's signature failure is re-deriving the same synthesis every session, and its one cause is the answer living in chat.
2. `perry-lint --provenance --root .` must report no `citation-dangling` for that file. This is the half of the bar `modes/inquiry.md` calls the mode's test suite; the rung is the other half, and shipping only the rung leaves the script unrun.
3. **A parent may not close before its children.** Any row whose `Parent` is this ID must be `done` or `dropped` first. An answered parent over an open child means either the child was not load-bearing — drop it and say why — or the answer is premature.

If the task spec lists `Subjective verification` items, **use `AskUserQuestion`** (header = TASK-ID, options = `Verified — close (Recommended) | Partial — keep as review | Reject — needs rework`) before flipping status. On `Verified — close`:
1. **Close it with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" done <TASK-ID> --evidence "<path or citation>" --rung <V1..V6>
   ```

   It removes the board row, writes the journal status-change line with the rung
   in it, and records the close event — atomically. `--rung` defaults to the
   track's `Default rung`, then the mode default, so the ordinary case needs no
   flag. **`--evidence` is required and the tool refuses without it**: Perry's
   oldest rule, enforced at write time rather than reported afterwards.

   `V0` is refused by name — it is what is being rejected, never a rung a row
   may carry.

   On a pipeline track, check the row reached the terminal stage of its `Stages`
   first: `approved` is not `published`, and closing short of the last stage is
   that mode's signature failure wearing a green checkmark.

2. The tool wrote the status-change line. Anything more the close deserves — a
   paragraph of what was learned, a correction, a finding — goes in today's
   `## Notes` by hand.
3. If the task was a Must-Have item in `phase/<NNN>-<slug>.md`, **do not tick it there** — `phase/` is the `goals` lane's file and this lane is not its writer (`SKILL.md § The hand-off contract`). Print the hand-off instead: "`<ID>` closed; it is a Must-Have in `phase/<NNN>-<slug>.md` → run `/perry goals link` to tick it." Asking and stopping is the contract; writing and apologising is the thing it forbids.
4. The original task definition (creation-day journal entry) stays untouched — that's the historical record.
5. **If `Deployed: yes`**: bump the runbook's `Last verified: <today>` field (the close is evidence the user reviewed the runbook against reality at this moment).

**Post-close capture point — knowledge promotion** (DESIGN-006 § 5.4; full procedure in `reference/promotion.md`):

After the close is written, ask whether the run produced a **reusable claim about how to do something correctly** — the one kind of memory Perry has no other home for. Run `"$PERRY_HOME/bin/perry-knowledge" propose --source "<the citation you passed to --evidence>" --rung <the rung> --root . --json` first: it is read-only and it says whether the capture point fires at all. `fires: false` → ask nothing and say nothing (`no-source`, `source-unresolvable`, a `V0`/`V1` rung, or a card already citing this source).

`fires: true` is permission to consider asking, not an instruction to ask. **You must have a draft** — an actual one-line claim and an actual tripwire — and the claim must be true of the next task too, not a fact about this one. Most closes produce neither, and the question does not fire on them; that is what keeps it from becoming the prompt people dismiss by reflex. Then **one** `AskUserQuestion` showing the drafted claim and tripwire, with `Skip — nothing durable` as a one-keystroke option that writes nothing anywhere. On confirm, `"$PERRY_HOME/bin/perry-knowledge" promote …` writes `knowledge/<topic>/<slug>.md` and re-renders `## Cards by topic` in `knowledge/INDEX.md`. **A sourceless card is refused, not written blank** — the tool enforces it; do not hand-write a card to get around a refusal.

Does not fire on `drop-task`: a dropped row produced no verified finding.

To find a closed task later: `grep "TASK-007" journal/` returns its creation entry, all status changes, and its close entry.

### `drop-task <id> <reason>`
Symmetric to `close-task`, and like it, tool-written:

```
"$PERRY_HOME/bin/perry-task" drop <ID> --reason "<reason>"
```

`--reason` is required and the tool refuses without it — a dropped row that
does not say why is indistinguishable from one that was lost.

The tool removes the board row, writes the journal status-change line and
appends the closing event, atomically. **Do not remove the row by hand.** A
hand-deleted row leaves its `add` event with no row and no close, which is
exactly the `orphaned` condition `perry-state` reports — so hand-dropping
manufactures, on every drop, the false drift the detector exists to catch.

The original task definition in its creation-day journal entry stays untouched
— that is the historical record.

## Cross-session

### `coordinate`
Pull a snapshot of work from other Claude sessions/terminals tagged for this project (use a session-listing MCP tool if the project hook declares one; otherwise ask the user to paste summaries). Append a consolidated update to `PROJECT_STATE.md` under `## Recent cross-session work`. Distribute follow-ups by appending new tasks.

When an incoming update references a Project by **name** (progress reports usually do, and the name may have drifted), resolve it to a KR **by ID through `phase/<NNN>-linkage.md`** before rolling any progress up — explicit `kr:` → Project ID → registered alias (`$PERRY_HOME/reference/okr-linkage.md`). Ambiguous or unmatched → ask the user which Project/KR it is; never attribute by fuzzy name. Hand the answer to `okr` (`/perry goals link …`) rather than editing `phase/`. Unresolvable while the user is away → `/perry goals link --unlinked <id>` rather than pinning it to a guessed KR.

### `handoff`
Generate the **Day-N Status doc** — a single self-contained document a future PMO session can read instead of re-walking the conversation. Save to `handoff/<YYYY-MM-DD>.md` from `state/handoff_TEMPLATE.md`. Always include:
1. Must-Have progress count (e.g., "4/5 done")
2. Today's deliverables (code/decisions/finance)
3. User Input Queue with recommendations
4. Next ISO week's day-by-day milestones
5. Open risks with mitigations
6. BOARD snapshot — copy the current `BOARD.md` table contents (or summarize if too long)
7. "Read these N files first when you resume" pointer (typically: `handoff/<this-doc>.md`, `BOARD.md`, last 1–2 journal entries, `PROJECT_STATE.md`)

The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc is the bridge.

## Phase transition

### `rollover`
Runs when a phase has been scored via `okr score-phase` and the user is ready to start the next phase. With the BOARD/journal split, rollover is mostly informational — `BOARD.md` is already current; previous phase's journal entries are intact. Steps:

1. Confirm `evidence/<YYYY-MM>/retro.md` exists (the phase score from OKR). If not, prompt to run `okr score-phase` first.
2. **Calendar-month directories** — `journal/<YYYY-MM>/` and `evidence/<YYYY-MM>/` are calendar-bound; create new month dirs only if the calendar month rolled (most rollovers do NOT need this — phases can span multiple calendar months OR fit inside one).
3. **`BOARD.md` is left alone.** Open carry-forward tasks already live there; no "carry forward" step is needed because the board never had a phase boundary in the first place. If a row's task ID encodes a date or phase prefix, leave it untouched — it's the canonical handle.
4. For each unresolved task on BOARD: **use `AskUserQuestion`** (header = TASK-ID, options = `Carry forward (Recommended) | Drop with reason`). Batch up to 4 per call. For "Drop with reason", follow up with a free-text prompt for the reason, then run `perry-task drop <ID> --reason "<reason>"` — the reason the user just gave, verbatim, not a paraphrase.
5. Hand off to OKR: print "OKR `plan-phase <new-slug>` is needed — pick the next phase's slug." Do **not** create the new phase file yourself — that's OKR's lane.
6. Append a `## Notes` entry to today's journal: "rollover from phase #<old-NNN>-<old-slug>; <n> rows carried; see evidence/<YYYY-MM>/retro.md".

`git log -- journal/` shows the full history per day; `git log -- BOARD.md` shows the live board's evolution; `git log -- phase/` shows phase progression.
