# TASK-469 — Token efficiency — route explanations, state queries and mutations through bounded startup

Date: 2026-09-18. Owner: Coding Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. Perry can run a full project ritual for an explanation or a narrow query. Give agents explicit intent-specific read paths while retaining recovery and ownership checks for every operation that accesses or changes project state.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

One authoritative startup-routing procedure, aligned router/lane references and a bounded acceptance transcript matrix.

## Files in scope

SKILL.md; goals/SKILL.md; work/SKILL.md; decide/SKILL.md; reference/snapshot.md; reference/host-capabilities.md; relevant existing routing/pointer tests.

## Acceptance criteria

1. Define explanation/help, bounded state query and state mutation paths. Explanation-only requests load needed instructional material without project dashboard, update check, mode loading or project-state reads.

2. A state query checks recovery before project-state access and reads only the requested projection. Blocking recovery and interrupted pipeline cases retain their existing stop/choice semantics; never resume a pipeline implicitly.

3. Mutation paths retain applicable recovery, interruption, ownership, hook, evidence and high-stakes gates. Explicit /perry overview continues to produce the required snapshot.

4. Router and lanes share one startup contract; do not repeat the full ritual when routing within the same unchanged operation. State-dependent results are refreshed after writes and when invalidated, not reused indefinitely.

5. An agent reviews eight cases: explanation, help, explicit overview, narrow status, task mutation, blocking recovery, interrupted pipeline and unknown/ambiguous intent. Each records expected reads, actual reads and the decision. No Python keyword classifier judges intent.

6. All eight cases meet written outcomes; pointers and relevant guards remain valid. Log fixed and conditional load sets to compare with the baseline.

## Dependencies

TASK-468. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Eight written routing cases with read traces, negative recovery/interruption cases, relevant structural tests and fresh V4.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Exactly three intent routes and eight acceptance cases listed above. No unrelated command redesign or new intent-classification engine.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Stdlib-only constraints remain binding. The phase 004 net Python/test lines <=0 rule binds Objective 4 work only (phase/004-guided.md § Operating Rules); this unlinked task is not bound by it (USER-970, 2026-09-18), but must not add needless code, delete meaningful checks or compress code to save lines. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
