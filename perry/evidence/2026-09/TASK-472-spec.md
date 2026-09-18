# TASK-472 — Token efficiency — bound tool output and repeated review work

Date: 2026-09-18. Owner: Coding Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. Repeated shell programs, broad reads, polling and expanding review scope inflate model turns. Tighten the existing execution and review procedures while preserving independent judgment and mandatory tests.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

Concise execution/review contracts, bounded result format and evidence showing reduced repeated reads and tool turns.

## Files in scope

work/reference/dispatch.md and split sections; work/reference/review.md; work/reference/review-constraints.md; work/reference/autopilot.md; existing result/handoff templates and pointer guards.

## Acceptance criteria

1. Batch independent reads; keep dependent actions, mutations and approvals sequential. Put long/repeated scripts in repository-derived unique scratch files; do not share scratch filenames across sessions.

2. Successful commands return concise status and evidence paths; failures retain exit code, diagnostic excerpt and full log path. Structured JSON is filtered structurally or stored intact; never feed truncated JSON back as a valid contract.

3. Use host completion events when available, otherwise bounded/backoff polling. Record call counts and waiting behavior; do not add a scheduler or claim tool-call count equals model-turn count.

4. Review briefs carry exact base/head, written acceptance, scope, diff and primary evidence by reference. Re-review covers changed findings and their affected invariants; base changes or wider changes trigger re-expansion. Fresh V4 remains independent.

5. After two failed review rounds, summarize unresolved criteria and needed decision; do not silently widen scope or automatically approve. Unrelated discoveries remain evidence for later triage.

6. Compare one small-change and one reviewed-delivery trace against the baseline. Preserve targeted checks during iteration and required final merged-candidate full checks. No repeated full suite without a new change, failure or unresolved concern.

## Dependencies

TASK-468. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Before/after bounded command and review traces, failed-output diagnostic check, changed-base review case and fresh V4.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Six numbered acceptance criteria, one small-change trace and one reviewed-delivery trace. No repository-wide cleanup or new review categories.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Current phase net Python/test lines <=0 and stdlib-only constraints remain binding. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
