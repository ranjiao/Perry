# TASK-471 — Token efficiency — enforce session budgets at safe task boundaries

Date: 2026-09-18. Owner: Coding Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. A long session repeatedly carries old context into new work even when a context ceiling exists. Use the correctly bound measurement at explicit boundaries and save a compact verifiable handoff before continuing in a fresh session.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

Shared budget-boundary and handoff procedure, bounded resumption checklist and documented unknown-telemetry behavior.

## Files in scope

work/reference/autopilot.md; work/reference/dispatch.md and split sections; work/reference/subcommands.md handoff section or its moved target; existing handoff template; existing context tests only if needed.

## Acceptance criteria

1. Inspect TASK-309 through the task contract before editing; leave executor checkpoint implementation there. This package owns orchestration boundaries, not a second checkpoint engine.

2. Check budget before a new task/review dispatch and after completing a task. Reuse measured source/freshness and configured ceiling; do not hard-code a second budget or assume the current tool is measuring this session.

3. At or over ceiling, complete/stop at an atomic safe boundary, record pending work and decline the next dispatch. Never interrupt an in-flight store transaction, abandon a mutation halfway or automatically resume an interrupted pipeline.

4. Handoff contains goal, task/spec paths, exact base/head/worktree, changes, test receipts, unresolved criteria, pending decisions and next command. Target <=8 KiB with evidence by reference, not copied logs.

5. A fresh-context reader verifies source revision and current recovery/task state before resuming; changed base or stale receipts require revalidation. No automatic host reset API or scheduler is introduced.

6. Demonstrate below/at/over ceiling, unknown telemetry, active operation, stale handoff and changed-source cases. Unknown is visible and follows an explicit bounded manual fallback; never label it within budget.

## Dependencies

TASK-468. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Boundary fixtures where applicable and authored safe-stop/resume cases; handoff byte measurement; fresh V4.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Two budget checkpoints, one handoff shape, and the seven boundary/resumption cases above. No executor checkpoint engine or host session-management implementation.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Current phase net Python/test lines <=0 and stdlib-only constraints remain binding. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
