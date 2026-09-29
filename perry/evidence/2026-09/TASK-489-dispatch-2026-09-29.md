# TASK-489 — dispatch record, 2026-09-29

Spec: `TASK-489-spec.md`, including § Decided 2026-09-29. Design: DESIGN-023
§ 6 row D and decision 13. Required verification: V4.

- **Executor.** A claude-subagent, run in the background with `isolation:
  worktree`.
- **Base.** `main` at the commit that records this file. The agent asserts it.

## Pre-flight

- **Budget:** UNKNOWN. The user started the task in session.
- **High-stakes screen: allow, with one guarded item.** The in-scope files
  are:
  - the new `bin/perry-kernel-migrate`;
  - the carried import items in `kernel/`;
  - the tests;
  - two reconciliation reports.

  None of these matches a line of `.perry/hook.md § High-stakes operations`.
  The guarded item is "Writing into a project Perry does not own". SkyTonight
  is read only. Every store and export goes under the agent's scratch
  directory, never under either project's `.git/perry` or state root. The
  brief says so, and the review checks it.
- **Architecture.** The trigger "new bin executable" is expected to be true,
  so the integration architecture review runs before merge.
