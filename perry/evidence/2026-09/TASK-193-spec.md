# TASK-193 — Response-sensitive discussion, premise challenge and escape

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Verification: V3 plus independent conversational review.

> Dispatch mode: manual
> Executor: codex
> Subjective verification: independent scenario review
> Touches architecture: existing goals lane and skill prose; no decided changes
> Deployed: no

## Readiness

Prepared; implementation awaits TASK-191 or an explicit change to the locked implementation sequence. Do not call preparation completion of TASK-191.

## Acceptance criteria

1. After each real user answer, briefly reflect the accepted meaning and select the most consequential remaining gap. Ask one question and stop; do not output both sides of a live interview.
2. Give a grounded proposal with consequences and allow an alternative in the user own words. Do not manufacture options, arbitrary metrics or approval merely because the proposal is recommended.
3. For a vague or activity-based goal, explain the concrete gap and offer one outcome-oriented rewrite. At most one push per answer within the route question budget; preserve disagreement and remaining unknowns.
4. Implement the locked escape: one offer of two consequential remaining questions, then immediately yield on a second refusal. Drafting from incomplete context is allowed; finalizing without approval is not.
5. Before approval, show the meaningful premises and let disagreement revise the relevant draft section. Run the unchanged advisory rubric once on the resulting draft; do not loop until the user agrees.
6. Demonstrate a rejected recommendation, a corrected beneficiary, an unknown baseline, activity-to-outcome refinement, refusal to continue and a fully formed pasted OKR. Record actual agent responses in isolated scenarios; independent review must assess preserved user intent, not just question count.

## Scope

goals/reference/elicitation.md; goals/reference/setup.md; goals/SKILL.md only for required pointers; existing relevant tests.

## Shared boundaries

User approved prioritizing constructive interactive OKR design on 2026-09-17. This is a bounded written implementation specification, not evidence of delivery. Locked DESIGN-020 section 5.5 and retained DESIGN-011 govern the behavior. Keep reference/input-quality.md byte-identical. Interpret prose with the agent; Python must not infer meaning or judge conversation quality. Do not fabricate real-user transcript evidence, change live SkyTonight files, auto-finalize goals, change architecture decisions or publish. Preserve all dependency gates until an explicit sequencing decision is recorded.

Use isolated Coding worktree and exact scoped commits. Run relevant pointer, ownership, budget and routing tests; committed affected selection and independent scenario review. Scenarios are hypothetical regression cases, never the TASK-191 real interview. Net Python/test lines must remain <=0 under the current phase constraint. No wording-mirror tests as a substitute for conversational evidence.
