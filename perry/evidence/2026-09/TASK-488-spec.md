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

## Out of scope
- The goals and decide types (TASK-492).
- The importer (TASK-489).

## Acceptance criteria
1. `template validate` accepts the file.
2. A test drives each work-lane type through every transition, and shows each
   guard refusing where the method refuses.
3. The grep test finds no type, state or field name from the template anywhere
   in `kernel/` source (Goal 1).
4. The RESULT proposes where tracks and settings live, with the reason. The
   PMO records the user's answer in this spec. Until the user answers, the
   template covers only the five types; it declares no tracks or settings.
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
