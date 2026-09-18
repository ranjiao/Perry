# TASK-470 — Token efficiency — shrink runtime instructions and actual per-command load sets

Date: 2026-09-18. Owner: Coding Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. The router and execution documents carry historical explanations into routine work. Reuse the existing page-budget and context-bill deliveries, then reduce material actually loaded without losing normative gates or introducing broken references.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

Slimmed router and lane instructions, on-demand rationale pages, relocation map and before/after bills for the five declared commands.

## Files in scope

SKILL.md; goals/SKILL.md; work/SKILL.md; decide/SKILL.md; referenced pages under reference/ and lane reference/ directories; existing budget/pointer tests. No locked design or schema edits.

## Acceptance criteria

1. Integrate or reuse accepted TASK-456 and TASK-457 artifacts; do not reimplement their L2/L3 caps or static-bill backend. Freeze the exact combined base before changing shared files.

2. Router <=12 KiB and each lane <=24 KiB as stricter iteration targets; existing tier caps remain in force. Move incident histories, installation-only material and rationale out of routine load paths.

3. For add-task, close-task and dispatch, reduce unique declared loaded bytes >=30% versus the pinned baseline. Report all five static bills, count shared paths once per load set and list conditional/dynamic reads separately.

4. Moving prose behind a pointer counts as savings only if the routine path no longer requires it. Preserve required sections, authority, host behavior, safety gates and exact references; provide old/new heading and rule mapping.

5. No procedure body duplicated across router and lanes; one authoritative procedure plus precise references. Agent semantic review verifies retained meaning; deterministic guards verify bytes and references.

6. A cap+1 mutation and broken-pointer mutation fail their checks. Do not inflate budgets, remove meaningful guards or edit locked decisions to pass.

## Dependencies

TASK-469, TASK-456, TASK-457. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Five reproducible byte bills, path/hash load manifests, relocation map, budget/pointer negative proofs and fresh V4.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Four entry skill files and the transitive references needed for the five declared bills. The finite before/after load manifest and relocation map define the review universe; unrelated prose is excluded.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Stdlib-only constraints remain binding. The phase 004 net Python/test lines <=0 rule binds Objective 4 work only (phase/004-guided.md § Operating Rules); this unlinked task is not bound by it (USER-970, 2026-09-18), but must not add needless code, delete meaningful checks or compress code to save lines. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
