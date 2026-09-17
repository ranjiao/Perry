# TASK-445 — concise recorded user decisions

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V5 after fresh V4.
> Touches architecture: shared user-load and existing task/spec procedure.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: fresh reviewer of four bounded decision examples; user approves concrete card format
> Deployed: no

Authorization: USER-957 permits implementation toward current phase 004. Phase 004 Operating Rule 1 requires every user decision to have a USER record before action, including spec amendments and commits. Objective 3 assigns the card format to reference/user-load.md and explicitly names the user as format approver. Prepare the concrete format and independent review first; do not claim the user approved it or close the task.

## Deliverable

Add the decision-card format and the rule that a spec amendment cites the USER ID it rests on. Use existing perry-task ask/answer paths, with at most 600 Unicode characters for the visible card and details one level down. The agent judges which utterance is a user decision; tools transport typed records only.

## Acceptance criteria

1. The shared user-load procedure defines a card of <=600 Unicode characters including ID/title, concrete user consequence, recommended answer/options, and a detail/evidence pointer when needed. A long technical explanation lives in evidence rather than being lost or silently truncated. At most three open decisions are presented at a time.
2. Before acting on a new user decision, the PMO records it with existing ask/answer writers, including an immediately answered decision. An existing recorded authorization is cited and reused rather than re-asked. A spec amendment and an implementing commit cite their actual USER ID. No fabricated user answer or approval from elapsed time, ambiguous assent, agent choice or unread report.
3. Agent-decided reversible choices remain visibly agent-decided; they must not be stamped as a user's choice. Preserve the current reversible-autonomy guidance, named-human/high-stakes requirements and the user's original scope.
4. Four bounded reviewer scenarios demonstrate a new pending choice, an immediately answered choice, reuse of prior recorded authority for a spec amendment, and an agent-decided reversible action. Agent-authored cards are measured; 601-character and missing-USER-before-action mutations are rejected at the appropriate deterministic/semantic layer. Existing pointer/route checks, smoke and committed affected tier pass. No Python natural-language classification.

## Files in scope

reference/user-load.md; the relevant ask/answer/spec-amendment instructions in work/reference/subcommands.md and work/reference/review.md only as necessary to point to the single shared format. Preserve unrelated content and TASK-455's independent architecture gate. Existing lexical/pointer tests only if an intentionally changed contract needs adjustment. No store/schema/code writer changes, no new command.

## Bound

One card format, four scenarios. Net Python/test lines <=0. No historical decision backfill or audit claim in this coding task: PMO will separately reconcile real phase evidence. No alteration to decided architecture or high-stakes gate. Product procedure change only; no live or copied PMO writes.

## Verification

Exact base/head and affected selection. Four measured examples and bounded negative evidence. Independent V4 reviews fidelity and authority distinctions. Human V5 accepts or declines the concrete format, with honest disposition. Canonical PERRY_HOME, unset PERRY_PROJECT, isolated TMPDIR; at most four test workers. Main integrator owns merged full/slow.

## Out of scope

Guessing which historical commits represent distinct user decisions, silently backdating records, treating agent choices as human answers, foreign writes, goal declarations, publication and main integration. User sign-off is queued behind existing pending decisions rather than adding a fourth live question.
