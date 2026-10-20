# Work modes

A mode tells the Agent how work progresses. It is procedural guidance, not a
native type, an automatically scheduled workflow or a separate state store.

| Mode | Main question | Typical evidence |
|---|---|---|
| [project](project.md) | What bounded outcome must we deliver? | Working artifact against written acceptance criteria |
| [queue](queue.md) | Which incoming request needs action next? | Triage, response expectations, resolved request and evidence |
| [pipeline](pipeline.md) | What must this piece satisfy before advancing? | Explicit entry/exit criteria and review of the artifact |
| [inquiry](inquiry.md) | What answer does the evidence support? | Sources, competing explanations and remaining uncertainty |

Use a primary mode per workstream. A software product can have project delivery,
a maintenance queue and an inquiry task without creating three stores. Inspect
the applied template: a mode name or pipeline stage is not automatically a task
field. Keep unsupported conventions in agreed narrative, linked to native items.
Do not invent commands, SLA timers or schedulers.

Packs add applicable domain requirements; scaffolds supply artifact starting
points. Neither changes a mode's safety/verification obligations. See the
[new-project guide](../reference/new-projects.md).
