# Reporting, coordination and phase handoffs

All work-state reads and writes use `$PERRY_HOME/reference/kernel.md`. Query complete task/ask/risk
results as needed, inspect events for the relevant time range, and attach only
supporting documents that a reader can actually open. Legacy journals remain
historical documents; the work lane no longer appends to them.

## `status` / `friday-review`

A narrow status request is read-only. For an explicitly requested weekly report or
friday-review, use `reporting-format.md` and save `weekly/<ISO-week>.md` only
within the approved reporting scope. Distinguish implementation,
tests, independent review, human acceptance and integration. Query totals and
states; do not claim every returned row represents every stored row when truncated.

## `monday-plan` / `plan-week`

Use `planning.md`. Approved task changes go through kernel mutations; narrative
weekly documents do not become another board or task register.

## `midweek-check`

Read this week's task events and current dependencies. Report movement, evidence
gaps and user inputs in the weekly document. No cadence item or journal line is
created; a recurring meeting/report is a skill procedure, not a register workflow.

## `mid-phase-review` / `end-phase-retro`

Read the current phase and goals data through the goals lane's current contract.
Use task query/events and evidence to mark achieved, partial, missed or unknown
outcomes. Apply the phase's actual scope-reduction rule. Save a bounded evidence
report for goals; do not edit its OKR/phase files. Identify the native phase ID, slug and observed store seq in the report.
Its display header is narrative context; goals follows the native phase's
attachment and exact identity, not a retired header parser. Read `health-check.md`, `digests.md` and `promotion.md` when those
selected capabilities contribute relevant evidence. Promotion requires a recurring
lesson supported by two tasks and at most one question for the whole retro.

## `coordinate`

Inspect available authorized session/task reports. Do not infer other agents'
activity from absent markers. Reconcile each report with actual kernel state and
its evidence before updating an item. Do not message another chat or person
without the user's authorization. Stable goal attribution belongs to goals.

## `handoff`

Save `handoff/<date>.md` with current task IDs, observed state, exact base/branch
and checkout, criteria, changes, tests, open questions and next actions. Include
real architecture start/delivery paths and pending transaction/recovery errors.
Read the latest item seqs immediately before writing a snapshot; make its time
explicit so future sessions can query current state instead of trusting old counts.
No journal or handwritten task-register changes accompany a handoff.

## `rollover`

Read the phase retro and goals lane's phase-scoring result. Open tasks remain
items; they are not copied into a new phase. Ask before dropping scope. Create
calendar evidence folders only as needed, never create a journal folder for this
procedure. Hand phase creation to goals. There are no cadence or stage migrations.

After writes re-query changed items and report the next useful action.
<!-- next-close: work status --> <!-- next-close: work friday-review -->
<!-- next-close: work monday-plan --> <!-- next-close: work midweek-check -->
<!-- next-close: work mid-phase-review --> <!-- next-close: work end-phase-retro -->
<!-- next-close: work coordinate --> <!-- next-close: work handoff -->
<!-- next-close: work rollover -->

## `add-task`

Use `add-task.md` for proposal, criteria, kernel creation and attachments.

## `triage`

Use `planning.md` for complete kernel queries, evidence checks and approved updates.

### `end-phase-retro`

Save the bounded retrospective as evidence. Its header is
`> Phase: <PH-ID> · <slug> · Store seq: <observed-seq>`. This display context
does not create another phase identifier or state register. Describe actual results, unresolved criteria and evidence limits;
hand goal scoring to the goals lane. This document is evidence, not task state.
Offer reusable findings through the explicit skill procedure in `promotion.md`;
promote only after the user chooses a finding and its source evidence.

<!-- next-close: work plan-week -->

<!-- next-close: work triage -->

<!-- next-close: work risk -->

<!-- next-close: work add-task -->
