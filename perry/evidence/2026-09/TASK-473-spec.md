# TASK-473 — Token efficiency — verify end-to-end savings without losing correctness

Date: 2026-09-18. Owner: Review Agent. Priority: P0. Required verification: V4.
> Dispatch mode: manual
> Executor: manual
> Estimated cycle: medium
> Subjective verification: independent reviewer checks all written acceptance criteria and retained safety behavior
> Touches architecture: §3, §6; preserve existing boundaries and select touched module documents at dispatch
> Deployed: no

## Authorization and rationale

USER-967 authorizes the iteration plan and P0 task registration. USER-968 explicitly chooses unlinked attribution and independent iteration acceptance. Smaller files alone do not establish lower total token use or unchanged quality. Compare controlled before/after scenarios including child sessions and retries, then report whether the iteration meets its savings and safety criteria.

Priority is P0 because this is a required package in the user-requested token-efficiency iteration, not an assertion that phase 004 KR targets have changed. Planning is complete when this spec and task record exist; implementation is not started or authorized for automatic dispatch by this spec.

## Deliverable

Independent acceptance report with raw receipt index, nine matched runtime pairs, five static bills and pass/fail against the iteration plan.

## Files in scope

perry/evidence/2026-09/ task-specific acceptance artifacts; disposable external scratch fixtures. Read product diff and specs; no product implementation or task-store hand edits.

## Acceptance criteria

1. Use three matched before/after runs for each of status-query, small-change and full-delivery classes. Pin commits, requests, fixtures, host/model settings and cache conditions; identify confounders and report median/range.

2. Include all parent/child measured usage and unsuccessful attempts; document dedup and reasoning/cache semantics. Incomplete telemetry leaves runtime acceptance open rather than silently excluding missing usage.

3. Meet >=30% lower median total input per successful case for each class and no unexplained >10% regression in a class; report the >=20% aggregate model/tool-round reduction target separately. Do not claim dollar or quota savings from raw token sums.

4. All written quality and safety cases pass, including recovery, interruption, missing identity, concurrent sessions, changed source and review-base drift. Report completion rate, retries, review rounds and wall time alongside savings.

5. Verify router/lane targets, existing page caps and the five static bills. Check exact candidate regression receipts and required independent architecture review; do not confuse author-branch tests with integrated-candidate validation.

6. Publish passed/failed/unmeasured criteria and remaining host overhead. If a target fails, leave acceptance open with a bounded remedy; no self-awarded V5, new paid API purchase or general evaluation framework.

## Dependencies

TASK-468, TASK-469, TASK-470, TASK-471, TASK-472. Typed dependency truth lives in perry-task list --json. Wait for accepted delivery and evidence, not merely an implementation branch. Resolve overlapping active work before editing.

## Verification

Nine matched runtime pairs, five bills, independent criterion-by-criterion verdict and exact-candidate regression receipt index.

Before implementation freeze base/head and actual relevant commands; use targeted tests, meaningful revert/negative proof and fresh-context V4. Required integration gates and release handling remain in force. This planning session awards no verification rung.

## Bound

Nine matched before/after runtime pairs, five static bills and the eight safety cases enumerated in the iteration plan. Stop at this sample; additional exploration requires an explicit scope decision.

Read perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md for shared protocol and targets. Stdlib-only constraints remain binding. The phase 004 net Python/test lines <=0 rule binds Objective 4 work only (phase/004-guided.md § Operating Rules); this unlinked task is not bound by it (USER-970, 2026-09-18), but must not add needless code, delete meaningful checks or compress code to save lines. Missing telemetry is unknown. If a target requires changing locked architecture, expanding a claim, relaxing a phase constraint or weakening a gate, stop that implementation and record the exact decision needed. Never delete tests or hide failed runs to meet cost targets.

## Out of scope

No phase/KR edits, new dependencies, claim-surface changes, paid API purchases, external publication, automatic implementation dispatch, self-review or self-merge. No implementation of the other five work packages. No new progress register.

## KR linkage

unlinked — explicit user decision USER-968. Independent iteration targets are in the plan; no KR progress is asserted.
