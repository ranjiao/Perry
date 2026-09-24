# TASK-488 — DESIGN-023 C: work-lane process template

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V3.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.4`, `§ 6` row C, `§ 8`.
Depends on: TASK-487.
> Dispatch mode: manual
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Files in scope
- `templates/process/perry.json` — new.
- `kernel/tests/` — a test that loads this template, and the grep test.

## Deliverable
The work lane's method, written as data:
- the item types `task`, `ask`, `risk`, `intake` and `cadence`, with their
  fields, states and transitions as the work lane runs them today (DESIGN-023
  § 3: the method is reproduced, not changed);
- rungs V0–V6 as an ordered enum. V0 is always refused;
- high-stakes work needs V5, and each track's default rung applies, both as
  `when` guards;
- WIP as a grouped `limit` in `warn` mode.

The phase also decides where tracks and project settings live
(DESIGN-023 § 8). The decision is recorded here before the template is written.

## Out of scope
- The goals and decide types (TASK-492).
- The importer (TASK-489).

## Acceptance criteria
1. `template validate` accepts the file.
2. A test drives each work-lane type through every transition, and shows each
   guard refusing where the method refuses.
3. The grep test finds no type, state or field name from the template anywhere
   in `kernel/` source (Goal 1).
4. This spec records where tracks and settings live, with the reason.

## Bound

The five work-lane types and the four acceptance criteria. One template file and its tests, and no kernel change. If the template cannot express a rule, stop and report (DESIGN-023 § 7, row 2).
