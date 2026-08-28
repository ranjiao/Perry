# TASK-030 — Event log and the full task set

> Source: `perry/design/DESIGN-004-deterministic-writes.md` § 6 phase B, § 5.3, § 5.5
> Dispatch mode: auto
> Executor: codex — self-contained, no MCP dependency, and the shape is fully specified by § 5.3
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

1. `.perry/events.jsonl` — append-only, one JSON object per line, opened
   `O_APPEND` so concurrent single-line writes stay atomic:
   ```json
   {"ts":"…","event":"start","id":"TASK-029","track":"core","actor":"agent","from":"not_started","to":"in_progress"}
   ```
2. `perry-task list [--all] [--track <t>] --json` — every task Perry has known:
   open rows from `BOARD.md`, closed ones reconstructed from events, each with
   its status timeline.
3. `bin/perry-state` reads the log for history, so the standup can answer
   questions the board alone cannot.

### Verification — V3

Two checks, and the second is the one that matters:

1. A fixture project with a known event stream produces a known
   `list --all --json` payload, including tasks whose rows have left the board.
2. **Delete `.perry/events.jsonl` and Perry is still fully functional.** Lint
   clean, standup renders, every existing test passes. What is lost is history
   resolution and drift detection — not truth.

Check 2 is the constraint that keeps this from becoming a database with a
markdown export, which is the failure DESIGN-002 argued against in a different
costume. If the log ever becomes load-bearing for current state, this task was
implemented wrong.

### Dependencies

TASK-029 — it is what emits the events.

### Out of scope

- Drift reconciliation (TASK-031). This task makes the history available;
  nothing compares it to the board yet.
- aimark calling it (TASK-034).

## Notes

**This is what a front-end actually needs.** `BOARD.md` holds open work only —
closed rows leave — so the full set exists today solely as a reconstruction
from date-sharded journal prose. A reader would have to parse every file in
every month and rebuild each task's timeline. One call replaces that, and it
means aimark never learns Perry's file formats: Perry can change them without
breaking a program it does not control.

`--all` is the flag that includes closed tasks. Without it, `list` answers
"what is open", which is what the board already says.
