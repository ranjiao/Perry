# TASK-192 — Routing and reuse for constructive goal discussions

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Verification: V3 plus independent conversational review.

> Dispatch mode: manual
> Executor: codex
> Subjective verification: independent scenario review
> Touches architecture: existing goals lane and skill prose; no decided changes
> Deployed: no

## Readiness

USER-959 records the user authorization on 2026-09-17 to implement downstream flows in isolated branches before the real interview. TASK-466 is the implemented question-bank prerequisite. TASK-191 remains a release acceptance gate through TASK-465. Do not claim the real interview completed, integrate this batch into main or publish it under this implementation-only authorization.

## Acceptance criteria

1. Route first OKR, revision and commitments by existing declared state and track spine. Missing context stays unknown; a project name or apparent maturity is not a routing fact.
2. Reuse explicitly supplied or approved answers and show their provenance in the draft. Distinguish an earlier decision from a proposed new threshold; smart-skip never supplies new consent.
3. For revision, discuss what changed and which goals are affected. Preserve unaffected accepted wording. Current revise steps must not directly append a finalized version without reviewed approval and an available writer.
4. Each route identifies its next unanswered consequential question and its draft destination. First and revision question caps remain 8 and 5; commitments <=3. Route selection does not silently start another horizon.
5. Demonstrate rich-context first project, existing-OKR revision, conflicting old/new context and queue commitments; no duplicate questions for explicit unchanged answers and no unsupported finalization claims.

## Scope

goals/SKILL.md; goals/reference/setup.md; goals/reference/elicitation.md; a narrowly scoped goals reference if needed; existing relevant tests only. Phase-specific procedure edits belong to TASK-194.

## Shared boundaries

User approved prioritizing constructive interactive OKR design on 2026-09-17. This is a bounded written implementation specification, not evidence of delivery. Locked DESIGN-020 section 5.5 and retained DESIGN-011 govern the behavior. Keep reference/input-quality.md byte-identical. Interpret prose with the agent; Python must not infer meaning or judge conversation quality. Do not fabricate real-user transcript evidence, change live SkyTonight files, auto-finalize goals, change architecture decisions or publish. USER-959 changes only implementation sequencing; preserve all other acceptance and human-signoff boundaries.

Use isolated Coding worktree and exact scoped commits. Run relevant pointer, ownership, budget and routing tests; committed affected selection and independent scenario review. Scenarios are hypothetical regression cases, never the TASK-191 real interview. Net Python/test lines must remain <=0 under the current phase constraint. No wording-mirror tests as a substitute for conversational evidence.
