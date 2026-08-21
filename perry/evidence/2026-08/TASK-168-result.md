# TASK-168 — `perry-task events` returned the log's head while four texts promised its tail

**Merged locally 2026-08-21** from `coding/task-168-events-tail` @ `634b035`.
Rung **V3**. `merge-check`: nothing new is red.
Option **A** — the first page is the tail. `perry-events/list` **1.0 → 1.1**
with a `semantics` entry.

## Verified independently

```
$ perry-task events --json --limit 6
contract : perry-events/list/1.1
seq      : [727, 728, 729, 730, 731, 732]
ts       : 2026-08-21T15:35:16 … 15:35:32     total: 733
```

Before: `seq [0..5]`, `2026-08-16T18:33:04`, five days stale.

**The check that catches a bad fix, re-run here from scratch** — page the whole
log in windows of 100 through the cursor, reverse, concatenate:

```
8 pages: 633-732 / 533-632 / 433-532 / 333-432 /
         233-332 / 133-232 / 33-132 / 0-32
reassembled == range(733): True    duplicates: 0    gaps: 0
```

An off-by-one at any page boundary fails that.

`perry/`, `schema/state-schema.json` and `tests/fixtures/contract-shapes.json`
all untouched. TASK-171's key table in the same contract file untouched.

## What the direction change forced

Paging necessarily runs **backwards**: if the first page is the newest window
there is nothing *after* it to page to. So the window became a half-open
`[start, end)` **anchored at its end**, `cursor` became the **oldest** event in
the window — the exclusive boundary the next page ends at — and `more` became
*"older events precede it"*.

`seq` is unchanged and still absolute, so a consumer reassembling pages sorts on
`seq` regardless of direction.

**Rotation restarts at the newest window**, not the head. Restarting at the head
would answer a rotation with the oldest events in the project — the exact defect
being removed.

## Why the old suite never caught it

**Every log in it was shorter than the default limit**, where head and tail are
the same rows, and the one paging test asserted `[0,1,2,3]` because that is what
it saw. Every new case uses a log longer than the window.

## The fixture the spec worried about was the wrong one

`contract-shapes.json` is structurally incapable of noticing this contract: its
`CONTRACTS` dict is `perry-task/list`, `perry-goals/list`, `perry-decide/list`.
Correctly not regenerated.

The one that needed a line is `contract-key-parity.json`, keyed by full contract
id. **Hand-patched to the events entry alone** rather than re-recorded, because
`--record` also absorbed unrelated live-state churn in `perry-task/list`
(115→113 documented, and an `intake`/`asks` table-assignment flip) that has
nothing to do with this row. Events parity 27/27, both diff lists empty.

## Reported, not absorbed

- **The log is 733 events, not the 726 the spec quoted** — it grew during the
  day. The measurement otherwise reproduced exactly.
- **"Three texts" is four.** The contract's own example comment is the fourth.
- **A stale busy-wait shell was spinning at 100% CPU on this machine**, from an
  earlier task in this same session. Its loop was
  `until ! pgrep -f "tests/parallel"; do sleep 5; done` — **its own command line
  contains the pattern it waits on**, so it can never exit, and while it lived it
  made `pgrep`/`ps` for `tests/parallel` report a false positive **for every
  agent on the machine**. That is precisely the check every dispatch prompt tells
  an agent to run before trusting a suite reading. Gone by the time the PMO
  looked; filed, because the pattern will recur.
