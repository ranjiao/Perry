# Role · {{role-name}}

- Accepted by: {{actual output verifier}}
- Default rung: {{V1–V6; an actual task may require stricter verification}}
- Executors: {{allowed executor or any; subject to actual host and authority}}

## Context

{{Optional role purpose and limits. This is context, not a workflow.}}

## Loads

- knowledge: {{optional topics}}
- pack: {{optional selected pack}}

## May touch

- write: {{explicit owned paths or isolated output location}}
- run: {{allowed commands or authoritative instruction reference}}

## Must escalate

- any `{{literal operation or path fragment}}` requires {{actual escalation condition}}

<!--
Exactly one nonempty May touch and Must escalate section is required by the
roles helper. Missing, misspelled or duplicate safety sections block dispatch.
Context/Loads are optional context; extra prose cannot grant scope or remove a
project restriction. The retired perry-lint closed-heading grammar does not run.

The Agent reads actual scope and acceptance requirements. No automatic knowledge
injection, permission expansion or verification award follows from this card.
Role escalation adds to .perry/safety.json; the union cannot shrink project rules.
A default rung is guidance, never V4 independence or actual named human V5.
Instantiate only with real scope and explicit ownership. See tools/helper-contracts.md.
-->
