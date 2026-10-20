# ADR-025 — Every earlier design and ADR is reconciled with DESIGN-023, and DESIGN-023 is revised

> Status: active
> Type: Design
> Date: 2026-09-24
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`perry/design/DESIGN-023-a-kernel-and-a-skill.md` was locked on 2026-09-24. The
same day, the user asked for every earlier design and ADR to be reviewed
against it. Three fresh-context, read-only reviews covered DESIGN-001 to
DESIGN-022 and ADR-001 to ADR-023. They returned two things:

- a disposition for each document;
- about twenty-five places where DESIGN-023 contradicted an earlier decision
  without saying so, or dropped a constraint it had to carry.

Five of those places needed the user. The rest were refinements within the
decisions already made.

## Options

- **Revise or supersede DESIGN-023.** Revise it: the direction did not change.
  The gaps are decisions inside it and details of its architecture.
- **Decision 8, KR progress:** a `metric` field type the kernel computes, or the
  agent judging "met". The second reverses DESIGN-022.
- **Decision 9, conditional guards:** one `when` condition per guard, plus
  grouped and warn-only limits; or four unconditional guards, with conditional
  rules moving to the agent's discretion.
- **Decision 10, verification:** V4 for the store (phase B) and the importer
  (phase D), as ADR-018 asks where a defect destroys state that cannot be
  recreated; or V3 throughout, as an exception to ADR-018.
- **Decision 11, aiMark:** aiMark moves to the kernel's `query` in the same
  release as phase E; or the kernel keeps a compatibility command in the old
  `perry-task/list` shape.
- **Decision 12, the parts of DESIGN-007 that were signed off but never
  built:** drop them; or carry them into the first template. They are: every
  task has a spec, the Run holds runtime state, and the Agent store.

## Chosen

The recommended option in every case, chosen by the user on 2026-09-24:

- revise DESIGN-023;
- metric field;
- one `when` condition;
- V4 for phases B and D;
- aiMark moves at phase E;
- DESIGN-007's unbuilt decisions are dropped.

The dispositions:

| Disposition | Documents |
|---|---|
| Superseded by DESIGN-023, now | DESIGN-004, DESIGN-005, DESIGN-007, DESIGN-014, DESIGN-015, DESIGN-016 |
| Dropped, now | DESIGN-019 — a draft whose mechanism lives entirely in code DESIGN-023 deletes |
| A `## Changes` entry pointing to DESIGN-023, now | DESIGN-001, 002, 003, 006, 008, 009, 010, 012, 013, 017, 020, 021, 022 |
| Unchanged | DESIGN-011 (already superseded by DESIGN-020) |
| Superseded, now | ADR-023 by ADR-024. ADR-003 by ADR-021 — unrelated housekeeping: ADR-021 withdrew Objective 5 on 2026-09-15 |
| At phase E, the work-lane cutover | ADR-006 and ADR-020 superseded by new store and rung ADRs; ADR-010 archived |
| At phase F or H, the final cutover | ADR-012 and ADR-014 folded into the store ADR; ADR-017 and ADR-022 superseded by an ADR for OKR items; ADR-011 archived; ADR-015 and ADR-019 amended |
| Kept | ADR-001, 002, 007, 008, 009, 016, 018, 021 |

The ADR changes wait for their phase because `perry-decide new` writes an
`active` record. A successor written today would govern code that keeps running
until its cutover (DESIGN-023 decision 6).

## Consequences

- DESIGN-023 carries decisions 8–12 and the refinements. Its `## Changes` entry
  for 2026-09-24 lists them.
- None of the nine designs `perry-state` reports as pending handoff gets
  implementation tasks, and six of them were built long ago:
  - DESIGN-001 to DESIGN-005 under TASK-001 to TASK-038;
  - DESIGN-013 under TASK-235 to TASK-237.

  Those rows do not cite the design id, and the handoff count matches literal
  mentions only.
- The reviews made task-level suggestions. They go to the triage row in
  DESIGN-023 phase A, and are not filed here.

## What would reopen this

A disposition proves wrong during phases A–H, for example an amended design
that turns out to be superseded. The fix is a `## Changes` entry on that design
that cites this ADR, not a new ADR.
