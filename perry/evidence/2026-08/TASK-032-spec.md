# TASK-032 — Mode-aware writes

> Source: `perry/design/DESIGN-004-deterministic-writes.md` § 6 phase D
> Dispatch mode: auto
> Executor: codex — mechanical once TASK-029 fixes the write path
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

### Deliverable

`perry-task stage <ID> <stage>`, `intake <request>`, `route <intake-row> --track <t>`,
plus the container creation the four review rounds kept finding missing:

- `stage` re-stamps `Stage since` in the same write. Unconditionally — the whole
  point is that it cannot be forgotten, which is what happened when it was a
  prose rule (DESIGN-003 round-3 finding N1).
- `route` carries `Arrived` from the intake row onto the new board row. Also
  structural: round-4 finding B2 was that the procedure doing the routing
  dropped the date its own SLA check measures.
- Both create any column or section the track's mode requires and the board
  lacks — `## Intake`, `Stage`, `Stage since`, `Arrived`, `Parent`.

### Verification — V3

A fixture per mode. For each: create a track, add a row, move it through its
stages, and assert every column the mode's triage reads is present and current
without a single hand edit. Specifically —

- pipeline: `Stage since` changes on every `stage` call
- queue: `Arrived` survives `route` and equals the intake row's date
- inquiry: `Parent` is set on a split, and the mode's WIP cap counts correctly
- project: nothing extra is written — the no-op guarantee DESIGN-003 goal 7 made

### Dependencies

TASK-029.

### Out of scope

- `OKR.md § Commitments` — decision 3 scopes the first release to the task
  lifecycle. That table has the same defect and is the obvious second.
- Lane procedures calling any of this — TASK-033.

## Notes

Every one of these was a review finding that survived because the rule lived in
prose. Rounds 1, 3, 4 and 5 each found the same class one level further out;
this task is where four of those stop being possible rather than being caught.
