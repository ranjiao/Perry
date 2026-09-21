# The budget boundary — the checkpoint between tasks

Moved out of `subcommands.md § handoff` on 2026-09-21 (TASK-470), unchanged: `close-task`, `dispatch`, `review` and `autopilot` run this checkpoint, and `handoff` writes what it asks for.

## Budget boundary

Two checkpoints, each between tasks, never inside one: **before** a task or review dispatch (`dispatch.md`, `review.md`, each `autopilot` iteration) and **after** a task's completion is recorded (`close-task`, `dispatch.md § On completion`). Both run one gate, which binds its own session and resolves the ceiling; never restate either:

```
"$PERRY_HOME/bin/perry-context-budget"
```

| Gate | Do |
|---|---|
| `OK`, exit 0 | continue |
| `OVER`, exit 1 | finish the atomic step in hand, dispatch nothing new, write the handoff, tell the user a fresh session resumes from it |
| `unknown`, exit 0 | print `context: unknown — not measured` and the reason; never call it within budget. `autopilot` is bounded by `--max-dispatches`; interactively, ask: hand off now, or one more task and ask again at the next boundary |

A `--session` reading (`explicit`, `historical`) is never a checkpoint verdict.

**Safe boundary.** Let a `perry-task` write return; it is atomic. Never stop between a status write and its evidence file, or with a mutation unrestored. In-flight dispatches keep running: list each (task, branch, checkout path, log) as pending in the handoff for the next session to process. A pending transaction or interrupted pipeline is recorded, never resumed here: the next session's recovery gate owns it.

**The handoff** fills the template's `§ 0 Resume point`: ≤ 8 KiB, evidence by path, no pasted logs.

**Resuming**, before any write: (1) the router's recovery and interrupted-run gates; (2) `git rev-parse HEAD` in each named checkout against its recorded head, and the main branch's tip against the recorded base; (3) `perry-task list --json` for each named task. A moved head or base, a changed status, or receipts older than the head → re-run the cited checks before relying on them. Then the recorded next command. Perry never resets the host session or schedules one: the user opens it.
