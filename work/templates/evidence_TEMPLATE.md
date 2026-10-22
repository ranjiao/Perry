# {{TASK-ID}} — {{Title}}

> Evidence file for {{TASK-ID}}. Lives at `evidence/{{YYYY-MM}}/{{TASK-ID}}-<short-slug>.md`.
> The native task's `evidence` field and/or attachment points here; update through `bin/perry item` / `attach`, with fresh seqs. Long-form analysis lives in this file, not in the record.

## Linkage

- **Objective/KR**: {{KR ref}}
- **Owner**: {{owner type}}
- **Priority**: {{P0 | P1 | P2}}
- **Status**: {{at time of evidence write}}
- **Author**: {{PMO Agent | Coding Agent | Research Agent | User}}
- **Date**: {{YYYY-MM-DD}}

## Deliverable

{{What this evidence file proves was done.}}

## Subject and acceptance scope

{{Name provider delivery, integration or package scope; immutable tested and
proposed subjects, source anchor, configurations/environment, criteria version
and exclusions. Explain applicability of older evidence. Follow the project
contract; a hash or HEAD alone is not a complete retained working tree.}}

## Method

{{How the deliverable was produced. Commands run, files changed, sources consulted, hypotheses tested.}}

## Findings / output

{{The substance. Tables, numbers, file diffs, decision recommendations. Be specific. Cite sources.}}

## Verification

{{Use scoped acceptance: per-criterion required/optional condition, exact subject,
actual result, evaluator, evidence and exclusions. Keep untested or applicability-
unknown gates visible. Distinguish delivery, integration, independent review and
named human approval. Use acceptance_TEMPLATE.md only when useful; do not create
a second live board or infer a parent pass from completed children.}}

- {{verification step 1, e.g., "command output snapshot"}}
- {{verification step 2, e.g., "test passed"}}
- {{verification step 3, e.g., "user signed off in chat: <quote, date>"}}

## Constraints checked

> If this is a recommendation, list the user-specific constraints (operating rules, tolerances, resource limits, etc.) that were verified before producing the recommendation.

- {{constraint check 1}}
- {{constraint check 2}}

## Open questions / follow-ups

- {{question that surfaced; will become a USER-id or new TASK-ID}}
- {{follow-up needed from another agent}}

## References

- Source files: {{paths}}
- Linked decisions: {{ADR ids under decisions/}}
- Linked tasks: {{TASK-IDs}}
