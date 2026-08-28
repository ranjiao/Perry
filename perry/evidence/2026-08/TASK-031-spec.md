# TASK-031 — Drift reconciliation, and the standup line

> Source: `perry/design/DESIGN-004-deterministic-writes.md` § 6 phase C, § 5.4
> Dispatch mode: auto
> Executor: codex — the comparison is fully specified and mechanically checkable
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: **P0** — this is the task that makes DESIGN-004 worth building
- **Attribution**: unlinked

### Deliverable

`bin/perry-state` reconciles `BOARD.md` against `.perry/events.jsonl` on every
standup and reports three conditions:

| Condition | Means |
|---|---|
| A board row with **no creating event** | Written by hand, or by a Perry older than the tool |
| An event with **no board row and no close event** | A mutation that did not land in the markdown |
| A `done` row whose **latest event is not a close** | The row was hand-edited after the tool wrote it |

Surfaced as a `drift` count in the payload and one standup line.

**Reported, never refused** (decision 5, and § 5.4). A user editing their own
markdown in a text editor is legitimate; the correct response is that Perry
notices, not that Perry objects. Refusing would make using a text editor on your
own files an error.

### Verification — V3

1. Hand-edit one row on a fixture board after the tool wrote it → drift reports
   exactly that row.
2. Append an event with no corresponding row → reported.
3. A board and log written entirely by the tool → drift is 0.
4. A pre-DESIGN-004 project with no event log at all → **drift is not reported
   as an error.** Every row predates the tool; treating that as a finding would
   make the first standup after upgrade a wall of noise.

### Dependencies

TASK-030 — the log has to exist and be readable before anything reconciles it.

### Out of scope

- Refusing or blocking on drift. Not in this release, and § 5.4 argues not ever.
- Changing lane procedures to call the tool — TASK-033, which is **hard-blocked
  on this task** (§ 5.7).

## Notes

**Without this, the tool is a convenience and the discipline problem is
untouched.** DESIGN-004 § 3 says so outright: `perry-task start` is still called
by an agent that must remember to call it, and this design does not fix that.
What it buys is that forgetting becomes *detectable* — and this task is where
that claim is made good or is exposed as another unbacked assertion.

**The honest limit, which belongs in the standup line's wording.** Drift catches
an agent that edited markdown without the tool. It cannot catch an agent that
did the work and called nothing at all — no row, no event, no trace. Nothing
short of host hooks can, and § 8 records why those are out of scope. The line
should not imply a coverage it does not have.

**This is the same move DESIGN-003 made** when it replaced "evidence exists"
with a declared rung: turning an unverifiable expectation into a number that
can be watched. If the drift count does not fall over the releases after this
lands, that is the measurement telling us the tool is being routed around, and
§ 7 commits to saying so rather than defending the design.
