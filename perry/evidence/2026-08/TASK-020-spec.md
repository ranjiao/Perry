# TASK-020 — `modes/queue.md` + `BOARD.md § Intake`

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase D (locked 2026-08-16)
> Dispatch mode: auto
> Executor: codex (self-contained; the board section is a schema-declared shape)
> Estimated cycle: medium
> Subjective verification: default SLA value — a judgment, flag it rather than pick silently
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1 — queue is the shape behind the largest observed category of
  agentic work (33.4%, DESIGN-003 §1.1)
- **Attribution**: unlinked

### Deliverable

1. `modes/queue.md` implementing the `queue` column of DESIGN-003 §5.1:
   - **Spine**: standing commitments + SLA. No objectives cascade — the work is
     reactive and has no goal that ends it.
   - **Horizon never closes**; it is reviewed on a period.
   - **Calendar binding** — arrival date + SLA.
   - **Item states**: `new → triaged → in_progress → resolved`.
   - **Throttle**: queue depth + age, not priority.
   - **Default rung**: V2 + a resolution note.
2. A `## Intake` section in `BOARD.md` — untriaged external requests, one line
   each, with arrival date (decision 3).
3. `triage` gains a **first step**: drain intake, routing each row to a track or
   dropping it with a reason.

### Verification — V4

A fixture whose intake holds more rows than the board cap can absorb. `triage`
must surface it as a **named finding** — not silently truncate, not quietly
absorb, not raise the cap. DESIGN-003 §7 records this as the cost decision 3
buys, and the mitigation is that an overflowing intake is the signal, so the
test is that the signal actually fires.

### Dependencies

TASK-018.

### Out of scope

- **Firing recurrences.** DESIGN-003 §3 is explicit: Perry is not a scheduler.
  The register (TASK-021) records what repeats and when it last ran; the host's
  cron or scheduled agents do the firing.
- The recurrence register itself — TASK-021.

## Notes

The signature failure from §5.1: *the board shows intentions while the real work
arrives and completes in chat*. Intake exists to make arrival visible. A queue
mode without a working intake drain is the failure wearing the fix's name.

`reference/project-archetypes.md § 3.C` already named intake as archetype C's
distinguishing organ and shipped `templates/ops/INTAKE.md` — which no subcommand
ever read (§1.4 B3). This task is what closes that gap; check whether the
template should now point at the board section instead.
