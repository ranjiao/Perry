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

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Stdlib-only constraints remain binding. The phase 004 net Python/test lines <=0 rule binds Objective 4 work only (phase/004-guided.md § Operating Rules); this unlinked task is not bound by it (USER-970, 2026-09-18), but must not add needless code, delete meaningful checks or compress code to save lines. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.

## Carried from TASK-468 (added by the PMO, 2026-09-18)

TASK-468 landed as local 0.1.17: `perry-context-budget` is session-bound. See `TASK-468-integration/acceptance.md` and `TASK-468-review/review.md`. The findings below are now part of this row's scope. They widen files in scope to `bin/perry-context-budget` and `tests/test_context_budget.py` for these items only.

1. **R-M1 (Medium), settle before any checkpoint relies on the gate on Claude.**
   - **The risk.** On the plain Claude CLI a subagent may bind its main session's transcript as `current`. A simulation (child flag blanked) reproduced the original false attribution: the parent's context reported as this session's, `OVER`, exit 1.
   - **Why the environment can't tell.** On Desktop the PMO verified that `CLAUDE_CODE_CHILD_SESSION=1` and `AI_AGENT` are identical in the main session and in subagents. The environment cannot separate them, so Desktop already reports `unknown`.
   - **What to do.** Either verify a real plain-CLI subagent's environment and add a distinguishing fixture, or treat Claude without a verified distinguishing signal as `unknown`. Document the outcome in `reference/host-capabilities.md`.
2. **R-L1.** In a forked Codex child the last `session_meta` record wins (`bin/perry-context-budget` ~:210). Make the first record win, and add a fixture.
3. **R-L2.** Two parts of TASK-468's H1 fix are untested; the reviewer's mutants S2 and S3 survived.
   - S2: applying the fix only when `forked_from_id` is present.
   - S3: removing the inherited-snapshot skip.

   Add tests that kill both.
4. **R-L3.** Document that on Desktop an explicit `--session` path is the only way to get a verdict, and that it is labelled `explicit`.

A checkpoint that meets `unknown` must follow the plan's rule: unknown is never zero or a clean budget.
