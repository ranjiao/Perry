# {{TASK-ID}} — {{Title}}

> Evidence file for {{TASK-ID}}. Lives at `evidence/{{YYYY-MM}}/{{TASK-ID}}-<short-slug>.md`.
> The TASKS.md `Evidence` field points here. Long-form analysis lives in this file, not in the board.

## Linkage

- **Objective/KR**: {{KR ref}}
- **Owner**: {{owner type}}
- **Priority**: {{P0 | P1 | P2}}
- **Status**: {{at time of evidence write}}
- **Author**: {{PMO Agent | Coding Agent | Research Agent | User}}
- **Date**: {{YYYY-MM-DD}}

## Deliverable

{{What this evidence file proves was done.}}

## Method

{{How the deliverable was produced. Commands run, files changed, sources consulted, hypotheses tested.}}

## Findings / output

{{The substance. Tables, numbers, file diffs, decision recommendations. Be specific. Cite sources.}}

## Verification

{{The test / check / sign-off that justifies marking the task `done` or `review`.}}

- {{verification step 1, e.g., "command output snapshot"}}
- {{verification step 2, e.g., "test passed"}}
- {{verification step 3, e.g., "user signed off in chat: <quote, date>"}}

## Constraints checked

> If this is a recommendation, list the user-specific constraints (R-rules, risk tolerance, cash needs, etc.) that were verified before producing the recommendation.

- {{constraint check 1}}
- {{constraint check 2}}

## Open questions / follow-ups

- {{question that surfaced; will become a USER-id or new TASK-ID}}
- {{follow-up needed from another agent}}

## References

- Source files: {{paths}}
- Linked decisions: {{ADR ids in DECISIONS.md}}
- Linked tasks: {{TASK-IDs}}
