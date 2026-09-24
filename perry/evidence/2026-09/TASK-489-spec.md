# TASK-489 — DESIGN-023 D: importer — this repository and SkyTonight reconciled

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V4
(DESIGN-023 decision 10: an import defect loses state).
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.3`, `§ 5.6`, `§ 6` row D.
Depends on: TASK-488.
> Dispatch mode: manual
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: the V4 fresh-context review; the user's call on long prose `Next action` cells
> Touches architecture: (none)
> Deployed: no

## Files in scope
- `kernel/`: the import path for today's stores.
- `perry/evidence/2026-09/TASK-489-reconcile-perry.md` and
  `TASK-489-reconcile-skytonight.md`, one reconciliation report per project.
- Read-only: this repository's `perry/*.jsonl` and `.perry/events.jsonl`, and
  the same files under `~/proj/SkyTonight`.

## Deliverable
The importer moves today's stores into a kernel store:
- `tasks.jsonl`, the register stores, and `.perry/events.jsonl`.

It is run on both projects, **each into a temporary store**. Neither project's
live store is created before TASK-490.

Rules:
- Ids keep their numbers.
- Each prefix's id ceiling is seeded from every id ever issued. That includes
  purged task ids, which survive only in the event log.
- Evidence is imported as one text field. It is never split into attachments by
  pattern (ADR-007).
- Long prose `Next action` cells (DESIGN-013 § 7) are shown to the user and
  decided before the import runs.

## Out of scope
- OKR, design and ADR records (TASK-492).
- Historic prose.
- Switching any lane to the kernel.
- Writing to either project's tracked files.

## Acceptance criteria
1. For each project, the report shows equal counts per type and per status
   between the old stores and the kernel store.
2. Every old id resolves in the kernel store.
3. The next id the kernel mints for each prefix is above every id ever issued,
   purged ones included.
4. `import` refuses a store that is not empty.
5. Replaying the imported events reproduces the imported items.
6. A fresh-context reviewer, who did not write the importer, scores items 1–5
   PASS against this file (`work/reference/review.md`).

## Bound

The stores listed under Deliverable, for two projects, and the six acceptance criteria. Temporary stores only. Neither project's tracked files are written.
