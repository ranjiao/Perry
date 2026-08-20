# Mode · `queue` — nothing ends it; it is steady state

> Loaded by the router for any track whose `Mode` is `queue`.
> DESIGN-003 § 5.1. This is the shape behind the **largest single category of
> observed agentic work** — business process and operations, 33.4% — plus
> customer support (0.8%) and personal assistance (3.8%).

Carries rules rather than references.

## The mode contract

| Slot | Value | Where it is written |
|---|---|---|
| **Ends when** | It doesn't. Steady state, reviewed on a period | — |
| **Unit that gets an ID** | The request — or the incident | `BOARD.md` row |
| **Spine** | `OKR.md § Commitments` — standing promises + an SLA. No objectives cascade | Written by the **goals** lane |
| **Horizon** | A review period, which reports rather than closes | `.perry/config.md § Tracks` → `Cycle` |
| **Calendar** | **Binding** — arrival date + SLA. Same meaning as `modes/pipeline.md § What "binding" does and does not mean`; read it there, it is one argument for both modes | — |
| **Item states** | `Status` (the global enum, unchanged) and `Stage` — default `new → triaged → in_progress → resolved` | `BOARD.md` → `Status`, `Stage` |
| **Arrival** | The date it came in, carried from intake and **never lost** | `BOARD.md` → `Arrived` |
| **SLA** | Response/turnaround time. **No default** — a track without it cannot run the breach step, and triage reports that rather than skipping it | `.perry/config.md § Tracks` → `SLA` |
| **WIP control** | Depth (from `Status` + `Track`) and age (from `Arrived`). **No cap** — see below | — |
| **Triage asks** | What breached SLA, what recurs, what should become a runbook? | — |
| **Default rung** | **V2** + a resolution note. Overridable per track (`Tracks` → `Default rung`) and per row | `BOARD.md` → `Verification` |
| **Signature failure** | The board shows intentions while the real work arrives and completes in chat | — |

`Status` and `Stage` are orthogonal here for the same reason as in pipeline
mode — `Status` stays the global lifecycle enum and `Stage` carries this
track's vocabulary. See `modes/pipeline.md § Status and Stage are orthogonal, and that is the point`.

## Declaring a queue track — ask for the SLA, never default it

**Whoever writes a `queue` row into `.perry/config.md § Tracks` asks for the
`SLA` in the same breath.** That is first-time setup, `/perry adopt`, and any
agent proposing a track register. One `AskUserQuestion`, before the row is
written; a row is not written with the cell left blank and filled in later.

The question is forced at creation because that is the only moment where both
of the alternatives are unavailable:

- **Perry may not default it.** The SLA is a promise the project makes to
  whoever is filing the requests. A number Perry invented is a promise nobody
  made, and it would not sit inert: the breach check, the age sort and the
  triage question all measure real work against it, so from then on Perry
  reports work as "overdue" against a deadline that exists only because a tool
  guessed. `schema/state-schema.json § work_modes.modes.queue.no_default` is
  where that is declared, and `Cycle` is on the same list for the same reason.
- **Perry may not leave it silently blank.** `SLA` is the clock this whole
  mode is measured against (§ Triage in this mode, § Commitments). A queue
  track without one has a breach check whose signal never clears — which
  `reference/diagnose.md` names as strictly worse than having no check.

If the user genuinely has no SLA, that answer is a fact worth writing down —
say `no SLA — best effort` in the cell. It is a declaration, so triage stops
asking, and it is honest, so nothing is measured against a number.

**After creation it is a warning, not a refusal.** `perry-lint` reports
`no-default` on a queue or pipeline row whose `SLA` or `Cycle` is undeclared,
and stops there: a project that already has such a track predates this rule,
and under ADR-004 an error would make the whole of `.perry/config.md`
undeclarable and therefore unwritable — one blank cell taking the entire track
register read-only. The hard stops live where the missing value is actually
used instead: `goals/reference/phases.md` refuses to write a queue commitment
while the track has no `SLA` cell, and triage below reports the gap rather than
skipping the breach step.

## Work arrives; it is not planned

This is the assumption that breaks when project mode is applied to operations.
Project work comes from `plan-week`: someone decides what matters and writes it
down. Queue work arrives from outside, at a rate nobody controls, and the only
decision available is what to do with it once it is here.

So this mode has an organ no other mode needs: **intake**.

### `BOARD.md § Intake`

Untriaged external requests, one line each, with the date they arrived:

```markdown
## Intake

| Arrived | Request | Outcome |
|---|---|---|
| 2026-08-14 | Finance wants the Q3 vendor spend reconciled against the PO log | — |
| 2026-08-16 | Onboarding checklist should cover contractors | dropped 2026-08-16 — covered by the HR handbook |
| 2026-08-16 | Quarterly access review automation | deferred until the SSO migration lands |
```

`Outcome` is where a drop reason or a defer condition is written. Without it the
mode mandated recording something and shipped a table with nowhere to put it —
which is what an independent review of this file found.

It lives inside `BOARD.md` rather than a separate `INTAKE.md` because
DESIGN-003 decision 3 chose zero new claimed paths, and `BOARD.md` is already a
path Perry claims. (Perry does ship a standalone `templates/ops/INTAKE.md` with
different columns — that is the scaffold `/perry diagnose` hands to a project
which should *not* adopt Perry, where there is no board for the section to live
in. Adopting Perry moves that list into this section.) The cost of that choice is real and named in the design's
risk table: untriaged requests compete with the 200-line board cap.

**That cost is the feature.** An intake that overflows the board is a project
taking on more than it is discharging, and the correct response is to surface it
as a finding, not to raise the cap or move the section somewhere it can grow
unnoticed. If it recurs, revisit decision 3 — do not quietly relax it.

### `triage` drains intake first

Before anything else — before stale rows, before priorities — `triage` walks the
intake section top to bottom. Each row gets exactly one outcome:

- **Routed** to a track, becoming a normal board row. **The `Arrived` date moves
  with it** — that is not optional bookkeeping. Age-since-arrival is the number
  every SLA check measures, so a routing that drops it makes triage step 2
  uncomputable, and the row is silently exempt from the only clock that governs
  it. The row carries `Arrived`, enters at the first post-intake stage, and
  takes a `Commitment` if one applies — all three set structurally by
  `perry-task route`, which is how the `work` lane performs this
  (`work/reference/subcommands.md § triage`). Stated here as what the mode
  requires, not as steps to type: this file is declarative, and a queue triage
  reads it in the same session as the procedure that executes it.
- **Dropped**, with the reason in the `Outcome` cell. "We are not doing this" is
  a real answer and it must be written down, because an undropped request is one
  that gets re-asked. The row stays in intake with its outcome recorded.
- **Deferred**, with a named condition in `Outcome` — never a bare "later".

An intake row that survives triage untouched is the failure this whole organ
exists to prevent. **Report it by elapsed time, not by triage count**: `Arrived`
is recorded and there is no triage counter, so "still here after 14 days" is
computable and "still here after two triages" is not.

**Rows with an `Outcome` leave at the end of the review period.** (Not
"resolved" — that word is already the terminal *stage* of this mode's item
vocabulary two screens up, and one word cannot mean both.) Routed, dropped and
deferred rows all stay visible until the period closes, then move to that day's
journal entry with their `Outcome` intact — the same live/history split
`BOARD.md` and `journal/` use everywhere else. Without this rule intake only
grows, and a board could overflow on a year of recorded drops, which would
destroy the argument above: overflow is supposed to mean *taking on more than
you discharge*, not *having discharged a lot*.

## Standing commitments, not objectives

There is no goal whose achievement ends an operations queue. What exists instead
is a short list of **standing commitments** — what this track promises to keep
true — and an SLA against which arrivals are measured.

```markdown
## Commitments      (in OKR.md — written by the goals lane)

| Id | Track | Promise | To whom | Due | Status | By when note | Discharged by |
|---|---|---|---|---|---|---|---|
| ops/1 | ops | Vendor invoices reconciled | Finance | 3d | active | within the track SLA | routed intake, worked oldest-first |
```

The link is written from the **board** side — each row's `Commitment` cell
carries the `Id` above, and never a row position or the promise text. `Id` is
stable; row position is not, and the goals lane rewrites this file. A position
reference does not dangle when a row is inserted, it silently re-points every
board row to the wrong promise, which is worse than a broken link because
nothing looks broken.

Triage reads it in the direction it actually needs: given a commitment due this
week, which board rows carry its id, and how far along are they.

**The clock is two columns; the authority is `SLA` in the track register.**
`Due` is typed — an ISO date or the same `<n><unit>` SLA shorthand — and is
what triage sorts and compares. `By when note` is prose and says what was
promised in the words it was promised in ("within the track SLA", "same
business day"); **nothing validates it, and no regex asks it anything**
(ADR-007, rule 2). The number triage actually measures against still lives
once, in `.perry/config.md § Tracks` → `SLA`. Writing "5 working days" into the
note as well is how the same value ends up in two places disagreeing about
whether days are calendar or working. **`5d` means five calendar days.**

**The goals lane owns this section**, like every other section of `OKR.md`. The
modes read it and never write it — the same one-writer-per-file rule that
governs everything else (`SKILL.md § The hand-off contract`). A commitment to a
named party *is* a goal; DESIGN-003 already frames a KR as the special case
where the party is the project itself. What these modes disclaim is the
objectives→KRs *cascade*, not the goals file.

`Track` is what keeps two tracks' promises apart in one table. `Id` is what
lets triage answer "are this commitment's items far enough along" — it is the
value board rows carry, so the question becomes a scan rather than a search.
`Discharged by` is prose for a human reader and is never dereferenced.

Forcing an objectives cascade onto this produces goals nobody set and a phase
that never legitimately closes. Perry's `phase/` machinery is not used by this
mode; the review period reports throughput and breaches, and then the next
period starts.

## Recurrence is a first-class object here

Most queue work is not novel. Month-end close, the weekly report, the quarterly
access review and the daily backup check are the same object: a thing that
repeats on a trigger, has an owner, has a procedure, has a last-run and a
next-due. `BOARD.md § Cadence` is that register, and it already exists:

```markdown
## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Last run | Next due | Last evidence |
|---|---|---|---|---|---|---|
| CAD-001 | Month-end vendor reconciliation | User + Agent | monthly | 2026-08-01 | 2026-09-01 | runbook/month-end-close.md |
```

**The register has a writer.** `perry-task cadence-add` mints the id and stamps
the first `Next due`; `perry-task cadence-done <id> --evidence <path>` records
an occurrence and recomputes `Next due` from the row's `Frequency`. `Next due`
is a derived cell, and until it had a writer a human redid that arithmetic after
every occurrence — which nobody does, so the register drifts into reporting
everything as permanently overdue or permanently fine. `Last run` stores the
input the due date is computed from, so it can be checked instead of trusted.
See `work/reference/subcommands.md`.

The **procedure** goes in `runbook/<slug>.md` — an existing claimed path
(`schema/state-schema.json § claims[]`), so converting a recurring request into
a runbook adds no new claim. `Last evidence` points at it. What that schema
entry (`§ files[] runbook`) makes normative is the **path, the template
(`work/state/runbook_TEMPLATE.md`) and the cap** — its `headings` list is empty,
so a runbook containing nothing but `# nonsense` draws no lint finding. The
shape below is what the template carries and what an agent should write, not
something a check enforces; the software-ops pack elaborates the staleness
and coverage rules at `$PERRY_HOME/packs/software-ops/runbooks.md`. A queue-mode
track that is not software uses the schema shape and needs no pack, since "what
it does, what healthy looks like, what failure looks like, who to escalate to"
is not a software question.

The triage question that matters most in this mode is **"what recurs?"** —
because a request that has arrived three times is not a request, it is a
process that has not been written down yet. Converting it into a Cadence row
with a runbook is the single highest-value move available in queue mode, and it
is the one nobody makes without being asked.

## Why the default rung is V2

Queue items are usually small, internal, and numerous. Demanding a human
sign-off on each would either stop the queue or turn the gate into a rubber
stamp — and a rubber stamp is worse than no gate, because it produces a record
that claims something nobody did.

So the floor is **V2**: a structural check plus a resolution note saying what
was actually done. **The note goes in the row's `Evidence` cell** for a
one-liner, or at `evidence/<YYYY-MM>/<ID>-resolution.md` when it needs more —
naming the location because a mode that mandates recording something and ships
no place to put it is the defect this file already fixed once, in its own Intake
table. Two escalations override the floor:

- **The consequence rule.** Anything outward-facing, irreversible, or touching
  money, legal exposure or personal data needs **V5** regardless — and in an
  operations queue that is a *lot* of items, because operations is where the
  outward-facing actions live. This is the one rung rule with a **check** —
  `perry-lint --verification` matches each closure against
  `.perry/hook.md § High-stakes operations`, the single canonical name for that
  list, and reports `consequence-needs-signoff`. It **reports**; it does not
  refuse. The ladder is advisory for one release (DESIGN-003 decision 4), so
  neither this rule nor the V2 default stops a close. Reported and enforced are
  different words and only one of them is currently true.
- **Incidents.** An incident resolved without a written cause is not resolved;
  it is paused. Those close at V3 minimum with the evidence that the cause was
  found, not merely that the symptom stopped.

## Triage in this mode

Ordered:

1. **Drain intake** (above). Nothing else happens first.
2. **SLA breaches** — rows whose `today − Arrived` exceeds the track's `SLA`,
   oldest first, each named with its age and the `Commitment` it breaches.
   Both inputs are columns: this is arithmetic, not judgment.
3. **Queue depth and trend.** Depth is the count of **active** rows in this
   track — `Status` neither `done` nor `dropped`, the same definition
   `modes/pipeline.md` counts WIP with. A row `perry-task drop` retired has
   already left the board and cannot be counted; the exclusion is what keeps a
   row a project archived **by hand** at `Status: dropped`, in a section of its
   own, from being counted as still waiting. Counting those would make depth
   rise monotonically for any queue that declines requests, reporting the exact
   opposite of reality for a queue doing the right thing. The trend is that
   count against the same count at the last
   triage, which the journal's status-change lines carry — arrivals and
   resolutions are both dated, so the series is recoverable without a new file.
   Arriving faster than discharging is the finding; a single number hides it.
   **Default cap: none.** A queue is not throttled by refusing arrivals, it is
   throttled by discharging faster or promising less — so depth is reported,
   never enforced.
4. **What recurs** — anything seen three times becomes a Cadence row with a
   runbook, or is explicitly declined.
5. **Overdue recurrences** — Cadence rows past `Next due`, surfaced exactly the
   way a stale User Input Queue item is. Read `cadence.overdue` out of
   `perry-state --json`, sorted and aged for you; a periodic ritual whose
   `Next due` cell yields no date at all is in `cadence.undated` and is the row
   most likely to have stopped happening without anyone noticing. Read
   `cadence.unreadable_frequency` too — a row whose `Frequency` cell this build
   has no period for is scheduled by nothing at all, and it is in that list
   only. Three lists, and `work/reference/subcommands.md § triage` reads the
   same three: a procedure that reads two of them is a procedure with a blind
   spot, not a shorter one.

**The review period** is the track's `Cycle` cell (`.perry/config.md § Tracks`)
— `monthly`, `2026-W34`, whatever fits. It reports throughput, breaches and
depth trend, and then the next period starts. Nothing closes.

## Where the rows physically sit

Board rows live under `## P0` / `## P1` / `## P2` **by default**, in every mode,
because those are the schema's required headings and the file has exactly one
row table shape. A queue- or pipeline-mode row filed there carries a priority —
**used for placement, not for meaning.** The throttle in this mode is depth and
age, and in pipeline mode it is the per-stage WIP limit; priority is where the
row is written down, not how it is chosen. Default to `P1` when nothing else
argues.

**A project that files work under its own headings keeps them.** `perry-task add
--group "<heading>"` writes into any `## ` section whose table resolves `ID` and
`Title`, with no priority at all — a real adopted project organizes its board as
`## Open — 工程线` and `## Open — 投资线`, and rewriting that structure to suit
this file is an Anti-Goal. The row table shape is still one shape: the section
is widened to the six required columns if it is narrower, and the mode columns
join it the same way they join `## P1`. This paragraph claimed "in every mode"
without the `--group` half for one release after `--group` shipped.

## What this mode does not assume

- **That the board reflects the work.** It is the mode's signature failure: the
  board shows intentions while the real work arrives and completes in chat.
  Intake exists to make arrival visible, so a queue-mode track whose intake is
  always empty while work is clearly happening is not healthy — it is
  unrecorded.
- **That Perry fires the recurrences.** It does not. DESIGN-003 § 3 is explicit
  that Perry is not a scheduler: the register records what repeats, when it last
  ran and what is due; the host's cron or scheduled agents do the firing.

## See also

- `perry/design/DESIGN-003-work-modes.md § 5.1`, `§ 5.5` — the mode table and
  the intake/recurrence/commitments decisions.
- `modes/pipeline.md` — for the committed, date-bound deliverables a queue often
  feeds.
- `$PERRY_HOME/packs/software-ops/incidents.md` — the incident record a queue-mode track uses.
