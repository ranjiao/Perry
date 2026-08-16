# Intake

> **This is the standalone scaffold, not the Perry form.** `/perry diagnose`
> hands this file to a project that should *not* adopt Perry — the
> three-files-and-no-tooling floor. A project that later adopts Perry moves
> this list into `BOARD.md § Intake`, whose columns are `Arrived | Request |
> Outcome`, because DESIGN-003 decision 3 chose zero new claimed paths and
> `BOARD.md` is already claimed. The two shapes are deliberately different —
> this one has no board to live in — and neither is a misspelling of the other.

> Everything that arrived and has not yet been routed. Triage before starting
> new work.
>
> This queue is the organ the other archetypes do not need. A software project
> generates its own work from a plan; this one is handed work by other people,
> and the requests that never get routed are the ones that resurface later as
> emergencies.
>
> **Every item leaves this list as scheduled, delegated, or declined.** Nothing
> leaves by going quiet — a request that silently ages out teaches the person
> who sent it to escalate next time instead of asking.

| # | Arrived | From | Ask | Routed to | Status |
|---|---------|------|-----|-----------|--------|
| 1 | {{YYYY-MM-DD}} | {{who}} | {{what they want, one line}} | {{deliverable / runbook / —}} | {{new \| scheduled \| delegated \| declined}} |

## Declined

Kept, not deleted. A visible "no" with a reason stops the same request arriving
three more times, and it is the record you need when someone asks why it never
happened.

| Arrived | From | Ask | Why not | Told them |
|---------|------|-----|---------|-----------|
| {{YYYY-MM-DD}} | {{who}} | {{what}} | {{reason}} | {{YYYY-MM-DD}} |
