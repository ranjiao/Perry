# TASK-140 — result

> Date: 2026-08-21 · Executor: claude-subagent · PR: https://github.com/ranjiao/Perry/pull/23
> Branch: `coding/task-140-mode-slot-axes` · Cycle time: ~18 min
> 2 files: `perry/design/DESIGN-008-track-axes.md` (§ 5.2 replaced, one `## Changes`
> entry appended — **verified by diff: exactly two hunks, nothing else in the
> locked document moved**), `tests/test_track_axes.py` (new, 22 tests)

## The count was wrong, and so were three of the sketch's assignments

**21 distinct slots, not ~28.** 10/14/12/14 = 50 total. §§ 1.1 and 2 carry the
estimate made before anyone counted; the agent recorded 21 inside § 5.2 and left
the other sections alone, correctly, because the document is locked and only
§ 5.2 was its row. Final split: **8 spine · 8 flow · 4 derived · 1 field.**

### `Calendar` is derived, not flow — and this contradicts § 1.1's own column

Checked independently rather than accepted. The argument: binding-ness has **two
independent sources** that coincide only on the four diagonals — the *spine* may
name a date promised to a party, and the *flow* may run a breach clock.

The evidence is inside the presets:

```
modes/inquiry.md   Question clock → BOARD.md → Stage since   Calendar: ADVISORY
modes/pipeline.md  Stage clock    → BOARD.md → Stage since   Calendar: BINDING
```

**Same datum, same column, opposite calendar.** A clock is not what makes a date
binding; a promise is.

And each single-leg assignment breaks a live case in the opposite direction:

| assignment | case | what breaks |
|---|---|---|
| on `flow` | `Mode: pipeline · Flow: project` | a dated client promise reports as advisory — an enforcement someone was actually given, dropped |
| on `spine` | `Mode: project · Flow: queue` | **this repository, § 1.3's case** — a real SLA reports as a nudge |

Derived, binding when *either* leg says so.

### Two more, both against the sketch — which the PMO wrote

- **`Question clock` was in no group at all.** It is `Stage clock` under a second
  name, same column. Assigned `flow`.
- **`pipeline` and `queue` do not share a spine.** Both mode files point at
  `OKR.md § Commitments`, which invites one `commitments` value — and decision #2
  forbids it, because one spine implies one unit and queue's unit is not
  `deliverable`. Two values backed by one file.

### The arithmetic error it also caught

§ 5.2's sketch asserted **"four derived slots"** in two places while its table
listed the derived group as one row plus `Unit`. Confirmed: the count never
added up. With `Calendar` moved it is exactly four.

## Queue's unit was not a free choice

`modes/queue.md` writes *"the request — or the incident"* — two nouns where
decision #2 allows one. Three things pick the same one, and the third is the
strongest: `schema/state-schema.json § work_modes.modes.queue.unit` **already
reads `"request"`** — verified: `{project: task, pipeline: deliverable, queue:
request, inquiry: question}`. The test asserts the map against the schema, so
the two cannot drift.

## The round-trip was keyed by leg value, not by mode name

That choice is what produced finding 3: two presets sharing a leg must agree on
every slot of that axis. Assigning pipeline and queue the same `commitments`
spine **reddens 8 tests** and names the conflict on `Ends when`, `Horizon`,
`Spine` and `Unit` at once. Proved by making the edit and reverting.

## Five falsifications, all done and reverted

| mutation | red |
|---|---|
| delete queue's `Arrival` (one file only) | 4 |
| delete `Spine` from all four files | 3 |
| add `Escalation path` to `modes/queue.md` | 3 |
| merge pipeline + queue onto one spine | 8 |
| drop queue's row from the unit map | 5 |

The `In` column exists for case 1 specifically: **without it, deleting a slot
three other files still carry is invisible.** The first pass of case 3 crashed
`setUpClass` with a `KeyError` and took six unrelated tests down; the agent made
an unassigned slot a clean red instead and re-proved it.

## One boundary it could not cross, and marked rather than relaxed

`Triage asks`, `Signature failure` and `Calendar` are derived over **both** legs
and are recorded for the four diagonal pairs only. Rendering them for an
off-diagonal pair is § 6 step 4's job — which is why step 4 depends on this
table. `test_the_other_derived_slots_stop_at_the_diagonals` asserts the boundary
so it is visible rather than assumed.

`Unit` is the exception: it reads the spine alone, so it is total over all
sixteen pairs — which is what lets § 4's worked example be checked mechanically
(`Mode: project · Flow: queue` has a **task**, not a request).

## Process note, self-reported

Mid-run the agent reverted its own uncommitted § 5.2 edit with a `git checkout --`
used to undo a falsification demo. Caught immediately and restored from the
staged source before committing. Worth keeping: a falsification that mutates the
file the row is *writing* needs a different undo than one that mutates a file the
row only reads.
