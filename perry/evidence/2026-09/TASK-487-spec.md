# TASK-487 — DESIGN-023 B: kernel core — store, items, guards, events

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V4
(DESIGN-023 decision 10: a defect here destroys state that cannot be recreated).
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.1–5.3`, `§ 6` row B.
Depends on: TASK-486 (the spec this implements).
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: the V4 fresh-context review against the criteria below
> Touches architecture: §2 (`kernel/`, `bin/`), §3 (the third Forbidden line), §6 NN-5
> Deployed: no

## Files in scope
- `kernel/` — new package, Python standard library only (`sqlite3` included).
- `kernel/tests/` — new suite.
- `bin/perry-kernel` — new executable. It is a thin wrapper that imports the
  `kernel/` package, and the user named it on 2026-09-24. At phase H it is
  renamed to `bin/perry`.
- `bin/perry` is **not** in scope. It stays DESIGN-016's index until phase H
  (DESIGN-023 § 8).
- `kernel/ARCHITECTURE.md` — the corrections and additions listed under
  Deliverable.
- `ARCHITECTURE.md` (root). The only edits allowed are the § 2 derived-field
  list and the § 3 Forbidden-line sunset, both listed under Deliverable, plus
  one § 8 line.
- One root test module, for example `tests/test_kernel_suite.py`, that runs
  `kernel/tests` in a subprocess so that `bash tests/run` and
  `tests/merge-check` cover the kernel. The executor may choose another
  integration if it is equally covered, and says which in its RESULT.

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

Carried from the TASK-486 merge review
(`evidence/2026-09/TASK-486-merge-2026-09-24.md`) and from decisions the user
made on 2026-09-24:
- **Two descriptive corrections.**
  - Add `rollup` to the derived-field lists in root `ARCHITECTURE.md § 2` (the
    `kernel/` entry) and in `kernel/ARCHITECTURE.md` lines 43–44.
  - Update `kernel/ARCHITECTURE.md` line 6, which still says the § 2 entry is
    unconfirmed.
- **Root § 3, the third Forbidden line** (`bin/lib § resolve_project_root` is the
  one implementation). The user confirmed adding a sunset like NN-1's, marked
  proposed:
  - it becomes false at DESIGN-023 phase H;
  - until then, the kernel's resolver (`kernel/ARCHITECTURE.md` § 5.7, NN-K5)
    is the only second implementation, and it must resolve in the same order;
  - a test proves the two agree on a shared set of fixture roots.
- **The CLI name** is `bin/perry-kernel`. Record it in `kernel/ARCHITECTURE.md`
  and close its open question there.
- **The live-store check** fails only on events whose actor session is the test
  run's own. A legitimate write from another worktree is reported, not failed.
  This resolves the executor's fourth open question from TASK-486.

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
9. A fresh-context reviewer, who did not write the code, scores items 1–8 and
   10–12 PASS against this file (`work/reference/review.md`).
10. `bin/perry-kernel --help` exits 0 and executes nothing. The wrapper holds no
    logic beyond importing the `kernel/` package.
11. `bash tests/run` runs the kernel suite. A red kernel test turns the root
    suite red.
12. The two descriptive corrections, the § 3 sunset and the CLI name are in
    place. A test shows the kernel's resolver and
    `bin/lib § resolve_project_root` resolve a shared set of fixture roots
    identically.

## Bound

The nine acceptance criteria plus the carried items. Only `kernel/`, `bin/perry-kernel`, one root test module and the bounded root `ARCHITECTURE.md` edits change. The kernel stays within 8 concepts and 12 command groups. If the spec seems to need a ninth concept, stop and report.

## Changes

- 2026-09-24 — `Dispatch mode: manual` → `auto`, and the carried items above
  are added: the user confirmed the dispatch, the CLI name and the § 3 sunset in
  session. Scope widens to `bin/perry-kernel`, `kernel/ARCHITECTURE.md`, three
  bounded edits to root `ARCHITECTURE.md`, and one root test module.
