# Task creation rationale

Current task creation follows [add-task](add-task.md), native item operations
and the [dispatch preflight](dispatch-preflight.md). Old `perry-task`, board
rendering, register routing and journal mutation procedures are retired. Their
historical implementation and measurements remain in Git before DESIGN-023 H.

## Why the spec shape is load-bearing

A scope must be extractable before dispatch. Use explicit `## Files in scope`,
`## Deliverable` and `## Out of scope` sections. An empty or unreadable scope
must refuse; it cannot be interpreted as a clean safety scan. This lesson came
from the old parser accepting empty sections when specs used bullet headings.

Current helpers report structural facts. The agent reads actual operations,
checks the additive project/role policy and verifies real authorization. A
well-shaped packet or a matching string does not authenticate consent. See
[operating rules](../../reference/operating-rules.md).

IDs, fields, state and history are kernel-owned. Never reconstruct a task from
an old board or append a journal definition/status line after item creation.
