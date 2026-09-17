# TASK-465 — Guided project initialization through the first approved plan

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Verification: V3 plus independent scenario review.
> Dispatch mode: manual
> Executor: codex
> Estimated cycle: medium
> Subjective verification: independent conversational scenario review
> Touches architecture: root sections 2, 3 and 5; existing config and lane ownership
> Deployed: no

User approved the deduplication and task adjustments in chat. This spec records
work to do, not implementation or permission to change locked architecture.
KR attribution: explicitly unlinked pending a fitting approved KR; neither
O2-KR3 nor P004-O2-KR3 is expanded by this task.

## Deliverable

Connect setup, project context, capability selection and existing planning
procedures into a guided path to the first approved plan and concrete next step.
Reuse existing writers, adoption flow and DESIGN-020 planning components.

## Acceptance criteria

1. For a new project, establish purpose and starting point, recommend relevant
   capabilities with consequences, allow optional choices to be skipped, then
   guide the user to a reviewed and explicitly approved plan and next action.
2. For an existing project, inspect and reuse approved conventions and route
   through the existing adoption/goal flow; do not restart answered interviews
   or overwrite existing project artifacts.
3. Capability recommendation happens once when useful; explain software-ops in
   user terms. Selecting it does not automatically configure version allocation.
4. Interrupted initialization can continue from recorded progress without losing
   answers or repeating completed setup. Reuse TASK-444 for planning-draft resume;
   verify the earlier setup-to-planning handoff separately using existing records.
5. Drafting is distinguishable from approval and finalization. A missing writer
   stops finalization without changing the target stores, per TASK-444.
6. Reuse TASK-190/191 interview evidence, TASK-192 routing/smart-skip,
   TASK-193 escape hatch, TASK-194 phase reuse and TASK-443 next-step behavior.
   No second question bank, draft state machine or capability manager.

## Files in scope

reference/first-run.md and existing setup/adoption/router handoff references;
conditional links to planning and TASK-464 capability procedures; isolated
scenario fixtures and this task's evidence. Identify precise paths at dispatch.
Existing lane writers retain their ownership. Additional state/schema or locked
architecture changes require their own reviewed proposal before implementation.

## Dependencies

TASK-464, TASK-192, TASK-193, TASK-194, TASK-443, TASK-444. TASK-190/191 and
TASK-264 are upstream through these rows; retain their existing gates.

## Verification

Independent end-to-end scenarios: empty software project, existing software
project, non-software project, skipped optional capabilities, interruption during
setup and during planning, missing writer. Record user prompts, reused facts,
resulting artifacts and next action; check no unintended project writes.

## Out of scope

Rewriting question banks or planning-draft machinery, changing KR definitions,
locked design decisions, automatic versions/publication or live external project
changes merely for tests. This task closes the orchestration and experience gap.

## Bound

First setup through the first approved plan and one concrete next action.
Existing later phase/week workflows remain owned by their implementation tasks.
