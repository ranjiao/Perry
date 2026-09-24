# TASK-491 — DESIGN-023 E2: aiMark reads the kernel instead of perry-task

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V3.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 4` decision 11, `§ 5.6`.
Depends on: TASK-489. Ships in the same release as TASK-490.
> Dispatch mode: manual
> Executor: claude-subagent (manual: the change lands in another repository, `~/proj/aimark`)
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Files in scope
- The six source sites in `~/proj/aimark` that call `perry-task` (measured
  2026-09-24).

## Deliverable
An aiMark commit that replaces each `perry-task` call with a call to the
kernel's `query`. The kernel keeps no compatibility command in the old
`perry-task/list` shape.

## Out of scope
- Any compatibility output in the kernel.
- Other aiMark features.
- Pushing aiMark to a remote. That is the user's call.

## Acceptance criteria
1. `grep` finds no `perry-task` call in aiMark's source.
2. aiMark's task views show the same rows for this repository from the kernel
   as they did from the old store. This is checked on a copy of the imported
   store before TASK-490 switches.

## Bound

The six call sites and the two acceptance criteria. Only aiMark's source changes.
