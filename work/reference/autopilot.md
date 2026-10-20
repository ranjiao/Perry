# Bounded execution

## `autopilot`

The first invocation is a dry run. Read `kernel.md` and `dispatch.md`; ask for the
allowed dispatch count, duration and failure budget when not already provided.
Never begin automation on ambiguous scope or an unarmed structured `.perry/safety.json` policy. An
unanswered boundary is not permission to continue because time elapsed.

Query nonterminal tasks and read their derived `startable` and `blocked_by`. Propose a bounded sequence
that is consistent with the user's priority and selected scope. Automation follows
only authorized tasks with criteria, valid host/executor and independent checkouts.
Incoming requests are tasks on `intake`; do not reconstruct stage/WIP/SLA or cadence
procedures. Host dispatch slots are process bookkeeping, not a kernel scheduler.

Run each selected task using `dispatch.md`, inspect its actual result, and re-query
dependencies after a write. Stop at the agreed budget, repeated failures, a required
human decision or missing evidence. Never auto-award `done`, V4 or V5; submit ready
work for acceptance. Report changes, tests, failures and next action from evidence.
<!-- next-close: work autopilot -->

Executors: claude-subagent | opencode-subagent | codex | manual, subject to the host matrix.
