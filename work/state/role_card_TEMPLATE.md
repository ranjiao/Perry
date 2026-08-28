# Role · {{role-name}}

- Accepted by: {{who verifies this role's output}}
- Default rung: {{V0–V6}}
- Executors: any

## Context

{{Three to six lines. Who this is and what they are for — not an essay, and not
a list of steps.}}

## Loads

- knowledge: {{topic, topic}}
- pack: {{pack-name, optional}}

## May touch

- write: {{paths}}
- run: {{commands, or a pointer to a subscribed source-of-truth card}}

## Must escalate

- any outbound `{{term}}`, `{{term}}`
- any {{thing}} that will be `{{term}}`

<!--
A ROLE CARD IS A HIRING CONTRACT THE HARNESS INSTANTIATES, NEVER A WORKFLOW.
What the role *does* belongs in the task and the lane docs. This file says who
it is, what it may touch, and what it must escalate.

The four `##` sections are a CLOSED SET, and `perry-lint --knowledge` reports
anything else — including `## Steps`, `## Procedure`, `## How to`, which are
`## Workflow` wearing other names. Each of the four has a mechanical consumer:

  Context, May touch  → rendered into the delegation prompt, verbatim
  Loads               → knowledge injection, by topic
  Must escalate       → backticked spans extracted and UNIONED with the
                        project's high-stakes list in the dispatch pre-flight.
                        The union only ever grows: a role can add to what the
                        project refuses to do unsupervised, never subtract.
  Accepted by,
  Default rung        → the close-task gate. The STRICTER of the mode's rung
                        and the role's wins.

A fifth section is prose nothing reads.

THE EXISTENCE TEST. A role is warranted only when it has a permission boundary
or an acceptance standard *distinct from the default*. Finance and legal that
are both "read files, run nothing, user reviews output" are one role with two
knowledge topics, not two roles. Add roles after real collisions, not up front.
-->
