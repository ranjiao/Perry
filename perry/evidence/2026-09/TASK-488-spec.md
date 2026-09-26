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

## Changes

- 2026-09-24 — Two requirements carried from TASK-137 and TASK-291 (TASK-485 triage).
