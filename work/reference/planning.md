# Planning and triage

Read `kernel.md` first. Query nonterminal tasks, including `blocked_by`, then
pending asks and open risks. Page through the whole result when evaluating every
row. Read selected task attachments, not every design or old journal.

## plan-week / monday-plan

Propose 3–5 P0 tasks serving the declared phase, with concrete deliverables,
dependencies, owner and rung. The user chooses scope before new specifications
are written. Existing tasks are updated with `item update` (priority and
next_action); new tasks follow `add-task.md`. Keep unknown KR linkage explicit
and hand stable attribution to goals. Save the approved narrative under
`weekly/<ISO-week>.md`; reference task IDs rather than maintaining another board.

## triage

For each open task, compare its state, next_action, criteria, latest event and
actual evidence. Distinguish blocked work, missing evidence and stale wording.
Propose scope changes in chat. Apply approved field changes with `item update`,
state changes with `item move`, and dependency changes with `rel add/remove`.
Never close merely because a task is old; never mark done from a prose assertion.
A task about code scheduled for deletion is assessed against the locked design,
not fixed automatically. Incoming requests are tasks on `intake`; no stage,
SLA, WIP or cadence procedure is recreated.

Re-read changed items, report the actual result and the next useful action.
<!-- next-close: work plan-week --> <!-- next-close: work triage -->
