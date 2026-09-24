# TASK-487 — DESIGN-023 B: kernel core — store, items, guards, events

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V4
(DESIGN-023 decision 10: a defect here destroys state that cannot be recreated).
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.1–5.3`, `§ 6` row B.
Depends on: TASK-486 (the spec this implements).
> Dispatch mode: manual
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: the V4 fresh-context review against the criteria below
> Touches architecture: §2 (`kernel/`)
> Deployed: no

## Files in scope
- `kernel/` — new package, Python standard library only (`sqlite3` included).
- `kernel/tests/` — new suite.
- `bin/perry` is **not** in scope. It stays DESIGN-016's index until phase H
  (DESIGN-023 § 8).

## Deliverable
The kernel as `kernel/ARCHITECTURE.md` specifies it:
- `sqlite3` in WAL mode, one transaction per command, ids minted inside the
  transaction;
- items, the four guards with `when` running on create and on transitions,
  relations, and attachments;
- events that record each changed field's value before and after;
- `item create` with its relations in the same transaction;
- `query` returning the derived fields;
- `describe` reporting shape only, and `template show` returning the template;
- `export` and `import`;
- `--store` / `PERRY_STORE`.

## Out of scope
- Any process template (TASK-488).
- The importer for today's stores (TASK-489).
- Any change to the old `bin/`.

## Acceptance criteria
1. Every test uses a temporary store. The suite fails if the live store's file
   changes while it runs.
2. The suite passes in a checkout with every `*.md` file removed (Goal 2).
3. A scripted test drives the whole lifecycle through the CLI alone (Goal 3):
   - init, apply a test template, create items of each type;
   - move each item through every transition, relate, attach, query;
   - export, import into an empty store, export again. The two exports are
     byte-identical.
4. `import` refuses a store that is not empty.
5. Two processes writing through two worktrees of one repository mint distinct
   ids, and each reads the other's writes at once (Goal 5).
6. Each guard kind, with and without `when`, has a test that shows it refusing.
   `limit` has a test in `warn` mode and one in `refuse` mode.
7. The budget test fails when a ninth concept or a thirteenth command group is
   added (Goal 6).
8. No kernel source file names a type, state or field from
   `templates/process/perry.json`. Once TASK-488 lands, this is TASK-488's grep
   test.
9. A fresh-context reviewer, who did not write the code, scores items 1–8 PASS
   against this file (`work/reference/review.md`).

## Bound

The nine acceptance criteria. Only `kernel/` is created, and no file outside it changes. The kernel stays within 8 concepts and 12 command groups. If the spec seems to need a ninth concept, stop and report.
