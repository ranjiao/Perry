# ADR-006 — The task store is not the event log

> Status: active
> Type: Design
> Date: 2026-08-18
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`DESIGN-005 § 4` decision #1 chose **(c) split**: markdown stays canonical for
goals and decisions, and tasks get a structured store. Decision #2 chose
**JSONL append-only** for that store, over JSON, YAML and SQLite. Both hold.

`DESIGN-005 § 5.2` then fused two things that decision #2 did not fuse. Its
title is *"The task store **is the log that already exists**"*, and its argument
is that making `.perry/events.jsonl` canonical is *"a reclassification, not a
new file — which is what keeps ADR-002 satisfied"*.

Three observations, all measured on Perry's own state at `fed289c`:

1. **The fusion makes every full-set read O(events).** `perry-task list --all`
   replays the whole log to reconstruct closed rows. The log is 173 events for
   75 tasks — 2.3 per task, and the ratio only rises, because a task accrues
   events forever while it only ever has one current state.

2. **57% of the log's bytes are superseded cell text.** By event type:
   `next` 46 events / 44,957 bytes / **57.0%** (977 avg) · `done` 15.3% ·
   `add` 13.9% · `status` 8.1%. A `next` event is a cell overwrite whose
   historical value is near zero — nobody replays what a next action said three
   revisions ago — yet it dominates the file that must be traversed to answer
   *"what is the full set of tasks?"*.

3. **`ADR-002` does not support the argument § 5.2 makes from it.** ADR-002 is
   *no cross-project registry*; it objects to *"state that outlives and
   outranks the thing it describes"*. It contains no clause against adding a
   file **inside** a project, and it explicitly exempts `.perry/events.jsonl`
   as *"inside the project it describes, under an already-claimed path"*. The
   citation was wrong, and it was the only stated reason not to have two files.

There is a fourth fact that makes this urgent rather than tidy, recorded
separately in `perry/handoff/2026-08-18-event-log-is-not-disposable.md`:
`DESIGN-004 § 5.3` declares the log *"derived and disposable … what is lost is
history resolution and drift detection, not truth"*. Deleting it takes the
payload from 39 open + **35 closed** = 74 tasks to 39 open + **0** closed. The
claim is false today, and it is false **because** of the fusion.

## Options

**A · Leave the fusion, correct `DESIGN-004 § 5.3` to say the log is canonical.**
Honest, free, and keeps one file. Rejected: it concedes the O(events) full-set
read permanently and makes a file that is 57% superseded prose the thing every
query must traverse. It also makes the log un-prunable forever, which is the
question `TASK-070` is open on.

**B · Leave the fusion, make disposability true** by reconstructing closed rows
from `journal/` when no log is present. Rejected: `DESIGN-004 § 1.3` names
exactly that reconstruction — *"date-sharded prose"* — as the problem these
contracts were built to eliminate. It would re-create a second parser for facts
a store already holds, which is the defect class this project has spent five
review rounds removing.

**C · Split the fusion.** A task store holds the full set as current state, no
history. The event log stays a log. Chosen.

**D · SQLite.** Already rejected as decision #2's option (d), and nothing here
revisits that: it is binary, not git-mergeable, and unreadable without a tool.
Option C needs none of it — which is the point worth recording, because C can
be mistaken for a step toward a database and is the opposite.

## Chosen

**C.** Three layers, one job each:

| | file | grows with | disposable |
|---|---|---|---|
| **truth** | `perry/tasks.jsonl` — one JSON object per task, current state, **rewritten in place** | project scope | no |
| **view** | `BOARD.md` — the open subset, rendered | open work | yes (regenerable) |
| **history** | `.perry/events.jsonl` — append-only | activity | **yes** |

- The store lives under the **state root**, not `.perry/`. Location is the claim:
  `.perry/` holds config and derived artifacts, and putting canonical state
  there is what let the fusion look reasonable.
- **One object per task, rewritten**, not appended. This is the one place
  decision #2's wording moves: JSONL is kept, `append-only` is not. Append-only
  is the log's property and it stays there.
- `BOARD.md` becomes a projection — `DESIGN-005 § 6` step 4, unchanged in
  substance and corrected in wording: it is the **store** that becomes
  canonical, not the log.

## Consequences

- **`DESIGN-004 § 5.3` becomes true again** rather than being corrected. Delete
  the log and Perry loses history replay and drift detection, and no tasks.
  That is what the sentence always claimed.
- **Full-set reads become O(tasks).** 75 rows instead of 173 events, and the
  gap widens with every `next` write.
- **`TASK-070` shrinks.** The log becomes a rotation candidate, which it could
  not be while it was the only record of 35 tasks. Its scope is now `journal/`,
  `evidence/` and log rotation.
- **Three files where there were two, and this is the real cost.** It is
  partly offset: `BOARD.md` stops being an independently-written second record
  and becomes a render, so the pair that can disagree today is replaced by a
  pair that cannot disagree by construction. What remains is whether the render
  is correct, which is testable in a way "two humans edited two files" is not.
- **Hand-editing `BOARD.md` stops being authoritative** — unchanged from
  decision #1(c), and still the expensive-to-reverse part.
- `perry-task/list` is a frozen contract and **does not change shape**. Where a
  value is read from is not a contract fact.

## What would reopen this

A project where the task store itself grows past what a full read can carry —
i.e. task count, not activity, becomes the scaling problem. That is the failure
this decision does not address, and the point at which the answer is an index
or a real database rather than another file split.

Also: if `BOARD.md` rendering proves unable to preserve what users write in it —
hand alignment, section names, group headings — then the projection model is
wrong for the file, and decision #1 reverts to (a) rather than this ADR being
patched.
