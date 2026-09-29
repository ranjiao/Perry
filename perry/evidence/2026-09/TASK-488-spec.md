# TASK-488 — DESIGN-023 C: work-lane process template

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V3.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5.4`, `§ 6` row C, `§ 8`.
Depends on: TASK-487.
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: §3 (the third Forbidden line's copy list), §6 NN-1, NN-2 (sunset wording), the kernel module document (split)
> Deployed: no

## Files in scope
- `templates/process/perry.json` — new.
- `kernel/tests/` — a test that loads this template, and the grep test.
- `kernel/ARCHITECTURE.md` and a new `kernel/architecture/` section file — the
  split, and the document updates carried below.
- Root `ARCHITECTURE.md` — three edits and nothing else: the NN-1 and NN-2
  sunset wording, the § 3 copy list, and one § 8 line. It stays at 500 lines
  or fewer.
- `bin/ARCHITECTURE.md` — the NN-B3 copy list and one § 8 line.

## Deliverable
*Round 2 replaces this list with DESIGN-023 decision 13; see § Round 2 below.*

The work lane's method, written as data:
- the item types `task`, `ask`, `risk`, `intake` and `cadence`, with their
  fields, states and transitions as the work lane runs them today (DESIGN-023
  § 3: the method is reproduced, not changed);
- rungs V0–V6 as an ordered enum. V0 is always refused;
- high-stakes work needs V5, and each track's default rung applies, both as
  `when` guards;
- WIP as a grouped `limit` in `warn` mode.

Two requirements carried from rows the TASK-485 triage dropped (confirmed by the user 2026-09-24):
- a queue row is born in its track's first declared stage, not the second (was TASK-137);
- a V4 verdict is a typed record on the reviewed item, never a block parsed from review prose (was TASK-291).

The phase also decides where tracks and project settings live
(DESIGN-023 § 8). The decision is recorded here before the template is written.

## Carried from TASK-487, decided by the user 2026-09-25

The first commit of this round, made before any template work, does two things:

- **Root § 6, the NN-1 and NN-2 sunsets.** Change the wording "only `import`
  reads the export" to "only `export`, to decide `unchanged`, and `import` read
  the export". The user confirmed this correction.
- **Split `kernel/ARCHITECTURE.md` by section.** It sits at its 600-line cap
  and cannot describe the error classes TASK-487 round 3 added. Move § 5
  Contracts into its own file under `kernel/architecture/`, following the root
  document's overflow convention. Then add the missing `usage` and
  `input_invalid` classes to kernel § 5.1.
- **After the split, bring the kernel document up to date with TASK-487's
  rounds 3 and 4.** Found by the round-3 architecture review on 2026-09-26.
  - Describe `id_exhausted` in § 5.1 and in `item create`'s error list
    (§ 5.6, near :343).
  - Describe the empty-variable rules: an empty `PERRY_STORE` is refused, an
    empty `PERRY_PROJECT` counts as unset, and an empty `PERRY_KERNEL_TESTING`
    counts as set. They go in § 5.1, § 5.7 and OQ-K5.
  - Add `export_token` to the `meta` key list (§ 5.7, :413).
  - § 5.9 should state the token exception.
  - The kernel § 8 line (:589) must describe § 5.9 accurately.

## Carried, decided by the user 2026-09-26

- **The copy list gains `perry-churn`.** Add `bin/perry-churn § detect_perry`
  (`:305–341`) to the "existing copies" in the root § 3 third Forbidden line and
  in `bin/ARCHITECTURE.md` NN-B3. It walks up to the first `.perry/`, stops at
  the git top level, and takes no `--root` and no environment variable. Keep
  the root edit line-neutral.
- **Record TASK-487's accepted choices in the kernel document** (the user
  accepted all three):
  - `id_exhausted` is part of the unreleased `surface` 1.0;
  - export temp files are named with the store's recorded token, and only a
    temp file carrying that token is removed;
  - an empty `PERRY_KERNEL_TESTING` counts as set.

## Round 2, decided 2026-09-29

Round 1 (`TASK-488-dispatch-2026-09-26.md`) stopped on eleven rules the
kernel cannot express. DESIGN-023 decisions 13 and 14 answer it: the method is
pruned to fit the kernel, and the kernel does not change. This round rewrites
`templates/process/perry.json` and its tests on the same branch. Commit
`4dc3a4dc`, the carried document work, stays as it is.

- **The template is exactly DESIGN-023 decision 13.** It has the types, fields,
  states, relations and guards listed there, and nothing else. The task states
  and the moves between them stay as round 1 wrote them, without the
  `restage_*` transitions. Field names are plain: `summary`, `reason`, and the
  risk state `open`.
- **`track`** is an enum of `main` and `intake` (decision 14). There are no
  per-track guards.
- **The two carried requirements.**
  - TASK-137, a queue row born in its track's first stage, no longer applies,
    because there are no stages.
  - TASK-291, the V4 verdict as a typed record, is met by `done` requiring
    `verified_by` at V4. The review document is attached to the task, and no
    field holds review prose.
- **Goal 1's grep** in `kernel/tests/test_vocabulary.py` matches a name only
  as a string literal (`"name"` or `'name'`) in kernel source. It keeps its
  test that the names come from the shipped template. It also shows red on a
  kernel file that spells one of those names as a literal.
- **`tests/test_kernel_suite.py` `COVERS`** gains `templates/process/`, so a
  template change selects the kernel suite.
- **Criterion 5, for the section file.** `perry-lint --architecture-module`
  accepts only `<component>/ARCHITECTURE.md`, and the old `bin/` is deleted at
  phase H. The section file passes criterion 5 when the lint's module checks,
  run on it from a scratch script, report 0 errors. Round 1 showed this.

## Out of scope
- The goals and decide types (TASK-492).
- The importer (TASK-489).
- Any change to `kernel/perry_kernel/`.
- Round 1's findings outside scope. The `SKILL.md:42` carve-out,
  `templates/README.md` and `work/reference/task-close.md:34` go to TASK-490's
  rewrite. The path quoting at `tests/selection.py:353` stays with the old
  `bin/`.

## Acceptance criteria
1. `template validate` accepts the file.
2. A test drives each work-lane type through every transition, and shows each
   guard refusing where the method refuses.
3. The grep test finds no type, state or field name from the template anywhere
   in `kernel/` source (Goal 1).
4. The RESULT proposes where tracks and settings live, with the reason. The
   PMO records the user's answer in this spec. Until the user answers, the
   template covers only the five types; it declares no tracks or settings.
   *Round 1 met this. The answer is DESIGN-023 decision 14.*
7. *(Round 2.)* The template's types, fields, states, relations and guards
   are exactly DESIGN-023 decision 13's list. The RESULT enumerates them
   against that list, one line each.
8. *(Round 2.)* Each guard in decision 13 has a test that shows it refusing,
   and a mutant of that guard turns its test red.
5. The first commit holds the carried document changes and nothing else.
   `perry-lint --architecture-module` reports 0 errors for
   `kernel/ARCHITECTURE.md` and for the new section file, and root
   `ARCHITECTURE.md` is 500 lines or fewer.
6. Every carried document item above is done, and the RESULT gives each one's
   file:line.

## Bound

The five work-lane types and the six acceptance criteria: one template file and its tests, plus the carried document changes. No change to kernel code. If the template cannot express a rule, stop and report; do not change the kernel (DESIGN-023 § 7, row 2).

## Changes

- 2026-09-24 — Two requirements carried from TASK-137 and TASK-291 (TASK-485 triage).
- 2026-09-26 — `Dispatch mode: manual` → `auto`. Added the carried items from
  TASK-487 (user decisions of 2026-09-25 and 2026-09-26), the new document
  files in scope, and acceptance criteria 5 and 6. Criterion 4 now routes the
  tracks and settings decision to the user.
- 2026-09-29 — Round 2 added, with criteria 7 and 8, following DESIGN-023
  decisions 13 and 14. Criterion 5 is now met for the section file by a
  scratch run of the lint's module checks. Out of scope now names the kernel
  code and round 1's other findings. The five types become three: § 3 now
  prunes the method, where it used to reproduce it.
