# Scoped delivery and acceptance

Use the task's written criteria and the [project contract](../../reference/project-contract.md).
This is a work-lane procedure using existing states, relations and attachments.
It adds no criterion entity, result enum, automatic invalidation or rollup.

## Define the scope before work

Specify the deliverable, intended consumer and what `done` will prove for this
task. Distinguish provider delivery, consumer integration, package acceptance,
independent review and actual human approval when they are separate obligations.
Use a finite criterion table with:

| Condition | Required or optional | Subject and environment | Evaluator | Actual outcome | Evidence and exclusions |
|---|---|---|---|---|---|
| {{written falsifiable condition}} | {{agreed requirement}} | {{exact source/config/criteria/environment}} | {{actual role/person}} | {{actual observation or untested}} | {{reopenable evidence; scope not covered}} |

This table is authored evidence for the named review, not a native schema or a
second current-state board. Use the optional [acceptance template](../templates/acceptance_TEMPLATE.md)
inside an existing spec/report where useful; do not create an empty report per task.

Use separate tasks only when work needs independent ownership, scheduling or
acceptance. Keep ordinary checks as criteria. Use numeric native checks only
for declared KR measurements through goals; do not turn a qualitative judgment
into an invented metric. `parent` means membership; `blocks` means an actual
dependency. Neither silently imposes an acceptance sequence.

## Review the actual candidate

1. Read fresh task/spec/relations and all required evidence. Identify the exact
   tested and proposed subjects under the project contract; inspect each criterion.
2. Classify the observed result explicitly: passed, failed, untested,
   not applicable with reason, or applicability unknown. These are prose judgments,
   not API values. Required/optional and exclusions are agreed, never retrofitted
   to turn a failure into a pass. Required not-applicable needs an actual agreed
   exclusion or criterion revision; a reviewer cannot waive it alone.
3. Retain evaluator identity, commands/inspections, scope, environment and result.
   Explain reliance on earlier evidence and its applicability. Keep failures and
   older candidate results unchanged. A hash match alone proves no behavior.
4. Missing, failed, unreadable or applicability-unknown required evidence prevents
   acceptance of that scope. Return the concrete criterion/deliverable or record
   the input needed; do not reject unrelated independently accepted work.
5. Apply the task's rung. V4 requires a fresh independent reviewer and actual
   criterion-level verdict. V5 requires the named human's acceptance of the exact
   artifact and limits. Neither a role card nor implementation authorization
   supplies either result. Use [review](review.md) and [close](task-close.md).

A provider-delivery task can finish when its own criteria pass. Its consumer
or package remains open until its distinct required conditions pass. Terminal
children do not automatically close a parent; query and inspect the package's
own criteria. No average, task ratio or newest report date grants package acceptance.

## Report without creating another state writer

For an on-demand summary, capture current native IDs/titles/states and seq with
complete paging for its declared population. Open the applicable cited criterion
records and evidence. Show each assessed scope, subject, result, evaluator,
missing required gates and next responsible owner. Separate native facts from
the Agent's evidence interpretation; unknown or uninspected evidence stays visible.
The summary is a dated observation, not a new source for later state transitions.

If evidence applies to different candidates, show separate rows and explain
the comparison. Do not mix an old pass with a new failure into a current overall
pass. Changed bytes require reassessment; they do not prove a regression or
silently rewrite the old verdict. A terminal task is not reopened through an
unsupported transition. Record necessary revalidation/integration work as a
linked follow-up with its own scope, preserving the original accepted result.

## Illustrative handoff

A source asset passes its provider's geometry checks. Its runtime-integration
task has no device evidence and its package requires a human visual review.
Report the provider delivery as accepted only within its geometry scope, the
integration gate as untested and the package as pending its own criteria. Do not
infer runtime or visual acceptance from the asset's hash, `done` state or parent link.
This is an example of the procedure, not an executed test or current project state.
