# TASK-466 — First-OKR response propagation

Date: 2026-09-17. Priority P1. Owner Coding Agent. Verification V3 plus fresh independent scenario review.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: independent conversation scenarios
> Touches architecture: existing goals skill prose only
> Deployed: no

## Authorization and bound

User requested implementation of constructive OKR discussion on 2026-09-17. Independent TASK-191-readiness-audit identifies a first-route weakness: corrections are not explicitly propagated through dependent proposals. Repair only the existing phase-C question bank before the real interview. This does not implement gated downstream TASK-192/193/194/444 or substitute for TASK-191.

## Scope

goals/reference/elicitation.md and goals/reference/setup.md only, with at most a necessary goals/SKILL.md description correction. No runtime code, schema, new framework, rubric, routing or architecture changes. Existing tests only; do not add wording-mirror tests.

## Acceptance criteria

1. At each response, use the latest accepted intent; briefly state substantive changes without re-confirming unchanged explicit facts. If beneficiary, capacity, objective or evidence changes, invalidate and visibly revise dependent proposed KRs, thresholds and commitments. Do not silently relabel stale proposals.
2. Choose the next consequential unresolved gap from the existing bank; Q1-Q4 remain a coverage guide, not a rigid script that ignores answers. One question then stop and wait. All followups count toward the existing cap of eight. Do not hide a second independent question in reflection text.
3. Explain the practical consequence/evidence basis for a recommended focus or scorecard. Proposed targets remain proposals until accepted. No fabricated baseline, option, user capacity or preferred answer. A correction must not merely be acknowledged while original metrics survive.
4. Preserve explicit rejected suggestions and the user's wording where accepted. If an answer conflicts with earlier context, show the conflict and ask only where needed; do not infer consent from silence or confidence. Existing single-push/advisory rubric rules remain intact.
5. Preserve first-OKR-only route and chat-draft boundary, default one objective and <=3 KRs, exact rubric bytes, missing-writer refusal and no auto-phase. Do not implement escape/premise or existing-project routes under this row.
6. Provide hypothetical scenario walkthroughs for changed beneficiary, reduced capacity, rejected metric, fully supplied context and unknown baseline. Each includes input, actual proposed agent response and resulting draft changes. Clearly label hypothetical evidence, not human interview acceptance. Independent review evaluates behavioral consequences and scope, not keyword presence.

## Verification

Relevant existing pointer, budget, ownership and vocabulary checks; smoke and committed affected selection against exact base. Record exact scope and rubric hash. Negative semantic check: reverting response-propagation instructions must fail the independent scenario criterion even when structural tests stay green. No artificial failing keyword test. No V4/V5 or architecture self-award. Coding commits only product paths; PMO archives evidence. No push, release or main merge.
