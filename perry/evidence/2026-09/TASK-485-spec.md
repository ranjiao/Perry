# TASK-485 — Triage open rows against DESIGN-023

Date: 2026-09-24. Owner: User + Agent. Priority: P1. Required verification: V1.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.6`, `§ 6` row A.
Decision record: `perry/decisions/ADR-025-earlier-designs-reconciled-with-design-023.md`.
> Dispatch mode: manual
> Executor: claude-subagent (manual: every drop is the user's call)
> Estimated cycle: medium
> Subjective verification: the user's keep, drop or re-scope call on each row
> Touches architecture: (none)
> Deployed: no

## Files in scope
- `perry/evidence/2026-09/TASK-485-triage.md` — the triage table.
- The task store, through `perry-task drop` and `perry-task next` only. Each
  write is dry-run first and confirmed by the user.

## Deliverable
The triage table has one line per row that was open when the triage started
(86 on 2026-09-24, not counting TASK-485 to TASK-494). Each line records:
- the row's id and title;
- keep, drop, or re-scope after a named DESIGN-023 phase;
- a one-line reason.

Every drop is applied with `perry-task drop <ID> --reason "…"`, and the reason
cites DESIGN-023.

Default rule, from DESIGN-023 § 5.6:
- A row that changes code DESIGN-023 deletes is dropped.
- A row about the method stays, and is imported at phase D.

## Suggestions to start from
These come from the three reviews recorded in ADR-025. They are suggestions,
not decisions.

**Drop:**
- **TASK-218**, "thread the closing phase id through every close stage".
  `phase/CURRENT` becomes a phase item's state.
- **TASK-219**, "retro-cites-phase-scores". It is a `cross_file` lint over
  markdown.
- **TASK-221**, "a phase close that stopped halfway is visible at the next
  snapshot". The snapshot is rebuilt at phase G.
- **TASK-369**, "DESIGN-015 stores a field that is derived at read time".
  DESIGN-015 is superseded.
- **TASK-375**, "linkage.jsonl has no uniqueness or mutual-exclusion
  invariant". `linkage.jsonl` becomes kernel relations.
- **TASK-240**, "an ADR id can be reissued". This one is the PMO's suggestion,
  not a reviewer's: the importer seeds id ceilings (DESIGN-023 phases D and F).

**Re-scope after DESIGN-023 phase F or G:**
- **TASK-220**, "the close-phase router subcommand".
- **TASK-444**, "a planning draft survives interruption" (blocked).
- **TASK-461**, "a due KR check is recommended".

**Follow DESIGN-023 phase E:**
- **TASK-188**, "the scout, run by hand on ten real rows".
- **TASK-189**, "autopilot becomes the two-stage scout-then-build loop".

**Still valid as written:**
- **TASK-454**, "a decided architecture section changes only with a recorded
  confirmation".

## Out of scope
- Implementing anything.
- Rows that are not open.
- Phase 004's plan, which is the `goals` lane's decision (DESIGN-023 § 5.6).

## Acceptance criteria
1. `TASK-485-triage.md` exists. It has a line for every id that
   `perry-task list --json` showed open when the triage started, apart from
   TASK-485 to TASK-494.
2. Every line marked drop names the user's confirmation, and
   `perry-task list --json` no longer shows that row open.

## Bound

The rows open when the triage starts, excluding TASK-485 to TASK-494; the round ends at the last of them. No row is added, and no code or document is edited.
