# TASK-021 — `BOARD.md § Cadence` gets a writer

> Source: `perry/design/DESIGN-003-work-modes.md`; `modes/queue.md` § "Recurrence is a first-class object here"; `schema/state-schema.json` → `BOARD.md` → `^Cadence\b|^例行节奏`
> Dispatch mode: manual
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: `work` lane's ownership of `BOARD.md`
> Deployed: no

**This file is the rubric a V4 reviewer scores against.** It states what the
work must satisfy, taken from the sources above. It is deliberately not the
same document as `TASK-021-recurrence-register.md`, which is the producer's
account of what was built — scoring an artifact against its author's own
description of it is not a review.

## Scope

The recurrence register only. `OKR.md § Commitments`, named in this row's
original title, belongs to the `goals` lane and is **TASK-042**; this row was
retitled on 2026-08-17 so it could close on the half it actually did. A
reviewer finding Commitments work here should treat that as a defect, not as
completeness.

## What must be true

### 1 · The section has a writer, and it is the only one

`## Cadence` had three readers and no writer. The failing shape is a rule
Perry states and nothing implements.

- [ ] A row can be created by a tool call, not a hand edit.
- [ ] A recurrence can be marked as having run, by a tool call.
- [ ] Both write `BOARD.md` and the journal together and append an event, like
      every other `perry-task` write. A board row without its journal line is
      the divergence the tool exists to remove.
- [ ] No procedure anywhere still instructs a hand edit of this section.

### 2 · `Next due` is computed, never stored by a human

This is the section's distinguishing property: it is the only board section
whose cell is **derived**. A human retyping it after every occurrence is the
defect, not the workflow.

- [ ] `Next due` is recomputed from `Frequency` and the run just recorded.
- [ ] The columns written match the schema exactly: `ID`, `Recurring task`,
      `Owner`, `Frequency`, `Next due`, with `Last run` / `Last evidence`
      optional. Resolved **by name**, never by position.

### 3 · `Frequency` is read tolerantly and written strictly

The schema says outright that `Frequency` is **not** enum-checked, and why:
`continuous` and `hourly` are live in a real project's register.

- [ ] A frequency the tool cannot parse does not crash, and does not get
      rewritten into something the tool prefers.
- [ ] Such a row is *reported* rather than skipped silently — a register whose
      unreadable rows disappear is worse than one that admits it cannot read
      them.

### 4 · The readers stop instructing an eyeball

Two files told the agent to "surface Cadence rows past their `Next due` by
age". That is an instruction to scan a table by eye, which is the thing
Perry's oldest rule forbids, and it was written a release before anything
could compute an age.

- [ ] `perry-state` exposes overdue rows already sorted, with the days
      computed — not a list the agent must sort.
- [ ] Rows whose `Next due` yields no date are surfaced as their own category.
      A periodic ritual with an unreadable due date is the row most likely to
      have quietly stopped happening, and it is invisible in an overdue count.
- [ ] Every procedure that used to say "by age" now reads the computed field.

### 5 · A cadence row is not a task

- [ ] `perry-task done` refuses a Cadence row, and says why. A recurrence has
      no end; it is retired by removing the row.
- [ ] The cadence events are in the section-event set, not the task-event set —
      a recurrence appearing in task counts would inflate them forever.

## Out of scope

- `OKR.md § Commitments` — TASK-042.
- Migrating any project's existing `## Cadence` section. A register written
  as prose or with different columns is not malformed.

## Verification the reviewer should expect to find

| Rung | Check |
|---|---|
| V1 | `perry-lint` clean |
| V2 | tests covering each refusal |
| V3 | a run against a register whose `Frequency` cells the tool cannot parse |
| V4 | this file, scored by someone who did not build it |

Each refusal should have been verified by reverting it and confirming the test
goes red. A refusal with no such record is an untested claim.
