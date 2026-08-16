# Mode · `queue` — nothing ends it; it is steady state

> Loaded by the router for any track whose `Mode` is `queue`.
> DESIGN-003 § 5.1. This is the shape behind the **largest single category of
> observed agentic work** — business process and operations, 33.4% — plus
> customer support (0.8%) and personal assistance (3.8%).

Carries rules rather than references.

## The mode contract

| Slot | Value |
|---|---|
| **Ends when** | It doesn't. Steady state, reviewed on a period |
| **Unit that gets an ID** | The request — or the incident |
| **Spine** | Standing commitments + an SLA. No objectives cascade |
| **Horizon** | A review period, which reports rather than closes |
| **Calendar** | **Binding** — arrival date + SLA |
| **Item states** | `new → triaged → in_progress → resolved` |
| **WIP control** | Queue depth and age |
| **Triage asks** | What breached SLA, what recurs, what should become a runbook? |
| **Default rung** | **V2** + a resolution note |
| **Signature failure** | The board shows intentions while the real work arrives and completes in chat |

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

| Arrived | Request |
|---|---|
| 2026-08-14 | Finance wants the Q3 vendor spend reconciled against the PO log |
| 2026-08-16 | Someone asked for the onboarding checklist to cover contractors |
```

It lives inside `BOARD.md` rather than a separate `INTAKE.md` because
DESIGN-003 decision 3 chose zero new claimed paths, and `BOARD.md` is already a
path Perry claims. The cost of that choice is real and named in the design's
risk table: untriaged requests compete with the 200-line board cap.

**That cost is the feature.** An intake that overflows the board is a project
taking on more than it is discharging, and the correct response is to surface it
as a finding, not to raise the cap or move the section somewhere it can grow
unnoticed. If it recurs, revisit decision 3 — do not quietly relax it.

### `triage` drains intake first

Before anything else — before stale rows, before priorities — `triage` walks the
intake section top to bottom. Each row gets exactly one outcome:

- **Routed** to a track, becoming a normal row with an owner and a rung.
- **Dropped**, with a reason recorded. "We are not doing this" is a real
  answer and it must be written down, because an undropped request is one that
  gets re-asked.
- **Deferred**, with a named condition — never a bare "later".

An intake row that survives triage untouched is the failure this whole organ
exists to prevent, so a row still sitting there after two triages is reported by
age.

## Standing commitments, not objectives

There is no goal whose achievement ends an operations queue. What exists instead
is a short list of **standing commitments** — what this track promises to keep
true — and an SLA against which arrivals are measured.

```markdown
## Commitments      (in OKR.md)

| Promise | To whom | By when | Status |
|---|---|---|---|
| Vendor invoices reconciled | Finance | 5 working days from arrival | active |
```

Forcing an objectives cascade onto this produces goals nobody set and a phase
that never legitimately closes. Perry's `phase/` machinery is not used by this
mode; the review period reports throughput and breaches, and then the next
period starts.

## Recurrence is a first-class object here

Most queue work is not novel. Month-end close, the weekly report, the quarterly
access review and the daily backup check are the same object: a thing that
repeats on a trigger, has an owner, has a procedure, has a last-run and a
next-due. `BOARD.md § Cadence` is that register.

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
was actually done. Two escalations override it:

- **The consequence rule.** Anything outward-facing, irreversible, or touching
  money, legal exposure or personal data needs **V5** regardless — and in an
  operations queue that is a *lot* of items, because operations is where the
  outward-facing actions live. `perry-lint --verification` matches each closure
  against `.perry/hook.md § High-stakes operations` and reports the gap.
- **Incidents.** An incident resolved without a written cause is not resolved;
  it is paused. Those close at V3 minimum with the evidence that the cause was
  found, not merely that the symptom stopped.

## Triage in this mode

Ordered:

1. **Drain intake** (above). Nothing else happens first.
2. **SLA breaches** — items past their promised turnaround, oldest first, with
   the age and the commitment they breach.
3. **Queue depth and trend.** Arriving faster than discharging is the finding;
   a single number without the trend hides it.
4. **What recurs** — anything seen three times becomes a Cadence row with a
   runbook, or is explicitly declined.
5. **Overdue recurrences** — Cadence rows past `Next due`, surfaced exactly the
   way a stale User Input Queue item is.

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
- `pmo/reference/incidents.md` — the incident record a queue-mode track uses.
