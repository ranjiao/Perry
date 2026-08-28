# Phase #001 — witness

> **Owner**: `okr` skill (only writer). PMO reads this every standup.
> **Started**: 2026-08-01
> **Status**: active
> **Source**: `OKR.md` v1

## Phase Focus

Hold open the four collections Perry's own board leaves empty, so the contract
pages that describe them can be checked against a payload instead of skipped.

## Operating Rules

- Agent autonomy: none. This project is read, never worked.
- User authorization required for: any edit at all.

## Cost Ceiling (phase #001)

- Spend cap: ≤ $0 (nothing runs here).
- Soft fallback at 80%: n/a.
- Wiring status: doc-only ⚠ (no code guard yet).

## User Commitments

- Keep the four conditions below true.

## User-Unavailable Degradation

None. Nothing here waits on a person.

## Phase Scope Reduction Rule

- **Phase-day trigger**: none — the phase has one deliverable and it is this file set.
- **KR-progress trigger**: none.

---

## Objective 1 — Hold the collections open

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P001-O1-KR1 | Collections a live board leaves empty | 4 of 4 non-empty | KR-O1.1 |

### Projects (seed for PMO TASK-IDs)

- **WIT-001 — The row nobody is holding**
  - Owner: Coding Agent
  - Deliverable: an `in_progress` row with no dispatch slot and no recent event
  - Verification: `conformance.in_progress_with_no_live_run` names it

- **WIT-002 — The edge no register carries**
  - Owner: Coding Agent
  - Deliverable: a `depends_on` id neither `tasks.jsonl` nor the ask queue knows
  - Verification: `conformance.depends_on_unknown` names it

- **WIT-003 — The row waiting on a verdict**
  - Owner: PMO Agent
  - Deliverable: a `review` row nobody has ruled on for longer than the threshold
  - Verification: `conformance.review_idle` names it

---

## Definition of Done

### Must-Have (failure = phase missed)

- [ ] All four collections non-empty when the real tools read this directory

### Nice-to-Have (failure allowed; explained in retro)

- [ ] Nothing

## Not Doing in this phase

- Not becoming a second Perry.

## Process Note

PMO cadence is owned by the `pmo` skill.

## Changes / Pivots

- 2026-08-27 — created for TASK-132 — reason: the parity check could not see 15 keys.

## Mid-phase check

- **Pace**: on-pace
- **Scope-reduction rule status**: armed
