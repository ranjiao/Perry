# DESIGN-008: `Mode` is three axes wearing one name

> Status: draft
> Date: 2026-08-20 · Locked: —
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: KR-O1.1, KR-O1.2, KR-O1.3 (`perry/OKR.md` v2, Objective 1)
> Supersedes: —   · Superseded by: —
> Revisits: `DESIGN-003-work-modes.md` § 5.1

## 1. Problem

DESIGN-003 gave a track a `Mode`, one of four values, and made that value carry
**everything** about the track's shape. The user raised, on 2026-08-20, that
this conflates two different questions:

> *`project` is how a project's goals are organised and decomposed. `queue` is
> how an individual task is advanced. One project could organise with `project`,
> work its decomposed tasks as a `queue`, and maintain a knowledge base from a
> `pipeline` of inbound documents — all at once.*

### 1.1 The four modes are four diagonal picks out of a grid

DESIGN-003 § 5.1's own semantics table is the evidence. Every row of it is an
independent question, and the four modes answer all of them together:

| Row of § 5.1's table | The question it answers | Axis |
|---|---|---|
| Spine | what the work is accountable to | **spine** |
| Horizon closes when | when the container ends | **spine** |
| Unit that gets an ID | what a row *is* | contested — § 5.2 |
| Item states / stage vocabulary | how a row advances | **flow** |
| Calendar binding vs advisory | whether a date is a commitment | **flow** |
| WIP control | what too much looks like | **flow** |
| Stage clock / Arrival / Dwell | what the clock measures | **flow** |
| Triage asks | derived from spine + flow | derived |
| Default min. rung | how much verification the *consequence* needs | **consequence** |
| Signature failure | derived | derived |

Counted across the four mode files, that is **10 / 14 / 12 / 14 = 50 contract
slots**, ~28 distinct, resolving to three axes and two derived rows.

### 1.2 The coupling is prose, not mechanism — measured, not assumed

This was tested on 2026-08-20 rather than argued (`evidence/2026-08/TASK-133-track-experiment.md`).
A `queue`-mode track was declared on this repository, a row created on it, and
that row attached to `P-O1.3`, a KR of a `project`-mode phase:

```
attribution.linked          4 → 5
attribution.linkage_error   ''
perry-lint                  0 errors
```

Nothing refused it, nothing warned. Searched for the gate and found none:

- no code in `bin/perry-state` or `bin/perry-task` conditions a KR edge on a
  track's mode;
- `perry/phase/002-linkage.md` contains neither `mode` nor `track`;
- **"No objectives cascade" appears exactly twice, both in `modes/queue.md`** —
  line 16 (the contract table's `Spine` cell) and line 188.

**So the combination the user asked for already runs.** What stops it is that
the mode file tells the agent it is not a thing, so triage never asks the KR
question on a queue track and no procedure offers the combination.

### 1.3 What that costs today

A project whose shape is not one of the four diagonals must pick the nearest
one and mis-handle the rest — **which is verbatim the defect DESIGN-003 § 5.1
rejected "mode as a property of the whole project" for.** Tracks fixed that at
the project level and reproduced it one level down.

Two concrete cases, both live:

- **This repository.** Goals decompose through `OKR.md` → `phase/002`; the work
  that actually arrives (an agent's mid-run finding, a sweep's sibling, a review
  result — 8 of the last 15 rows) has an arrival date, a backlog depth and a
  recurrence question, and none of that is expressible on a `project` track.
- **`~/proj/TeckWork`.** Ingesting an article into a knowledge node is a
  `pipeline`; querying that base for a research report is an `inquiry`. This
  case **is already served** by DESIGN-003 — two tracks, one table — and is
  recorded here only so § 3 can say so explicitly.

## 2. Goals

1. A track can name its spine and its flow independently.
2. **A project that writes only `Mode: project` changes by zero bytes** and
   behaves identically. The no-op property `modes/project.md` is built on is
   not negotiable.
3. Every one of the ~28 distinct contract slots is assigned to exactly one
   axis, in a table, with the ambiguous ones argued rather than assigned
   silently.
4. The four mode names survive as **presets**, because they are four observed
   clusters and a user should not have to assemble a common shape from parts.
5. No new claimed path, and no new state file. The register already exists.

## 3. Non-Goals

- **Not a new mode.** The axes are a factoring of what exists.
- **Not multi-track rows.** A row belongs to one track, as today.
- **Not the per-project case.** DESIGN-003 § 5.1 settled that with `1..N`
  tracks and its reasoning stands; § 1.3's `TeckWork` example is served by it
  unchanged. This document does not reopen it.
- **Not a config schema rewrite.** `## Tracks` gains optional columns; existing
  rows parse unchanged.
- **Not the triage rewrite.** What triage asks *follows* from the axes; the
  procedure change is a separate row once the axes are fixed.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | How many axes | Two — spine, flow / **Three — spine, flow, consequence** / Two plus rung as a plain per-track field | — | — |
| 2 | Which side owns "the unit that gets an ID" | Spine / Flow / Neither — it is derived from spine | — | — |
| 3 | Whether `Mode` survives | As a preset name expanding to a triple / As a deprecated alias / Removed, axes only | — | — |
| 4 | What an unspecified leg means | Inherit from the preset / Inherit from `project` / Refuse the row | — | — |
| 5 | Whether a mode file stays one file per mode | One per mode, annotated / One per spine + one per flow / A single matrix page | — | — |
| 6 | Whether existing declarations migrate | Never — presets are permanent / On next write / A one-time `perry-config` migration | — | — |

Notes on the non-obvious rows:

- **#2 is the one genuinely contested slot.** "The deliverable, not the task"
  (pipeline) reads like a statement about what the work is *for*, which is
  spine. But it decides what a board row **is**, which drives `Stage`,
  `Arrived` and the WIP denominator — all flow. Getting this wrong puts a
  column on the wrong axis and the error only shows up when someone combines
  two presets that disagree about it.
- **#1's third option is not a dodge.** `Default rung` was already overridden
  per-track on this repository's first real declaration — `intake` runs V3 where
  queue's default is V2 — for a reason ("an arriving row here is a code defect")
  that has nothing to do with either spine or flow. That is evidence for a third
  axis; it is also evidence that a plain overridable field would have sufficed.
- **#4 decides whether the presets are defaults or templates.** "Inherit from
  the preset" keeps `Mode: pipeline` meaningful after an override; "inherit from
  `project`" makes every unstated leg the same everywhere and makes a partial
  declaration surprising.

## 5. Architecture

*Drafted against decisions that are not resolved. Every claim below is
conditional on § 4 and must be re-read after it is walked.*

### 5.1 The declaration

```markdown
## Tracks

| Track  | Mode             | Spine      | Flow        | Stages | WIP | SLA | Cycle | Default rung |
|--------|------------------|------------|-------------|--------|-----|-----|-------|--------------|
| core   | project          | —          | —           | —      | —   | —   | —     | —            |
| ops    | project + queue  | objectives | arrival+sla | new→…  | 6   | 5d  | weekly| V3           |
| kb     | pipeline         | —          | —           | brief→…| 3   | —   | 2026-W34 | V5        |
```

Row 1 is what every project writes today and it parses identically. Rows 2–3
are only reachable by someone who needs them.

### 5.2 The slot table — where the work is

Each of the ~28 distinct slots gets one axis. Sketched below; **completing it is
the implementation, not a preliminary**, and #2's row is why.

| Slot | Axis | Note |
|---|---|---|
| Ends when · Horizon · Spine | spine | |
| Item states · Stage vocabulary · Stage clock · Arrival · Dwell · SLA · WIP · Calendar | flow | |
| Default rung | consequence (#1) | |
| Unit that gets an ID | **contested** (#2) | |
| Commitment link · Question tree · The answer · Sources · Claim → source | spine, provisionally | each names a file or a column that exists because of what the work is accountable to |
| Triage asks · Signature failure | derived | rendered from the other three, never declared |

### 5.3 What is not changing

`BOARD.md` gains no column — `Track`, `Stage`, `Stage since`, `Arrived`,
`Parent`, `Commitment` and `Role` already exist and are already created on
demand. The linkage graph is untouched: § 1.2 measured that it never consulted
the mode.

## 6. Implementation plan

| # | Step | Depends on | Note |
|---|---|---|---|
| 1 | Complete § 5.2 slot by slot | #1, #2 | The document's real payload |
| 2 | `Spine` / `Flow` columns parsed, defaulted from the preset | 1, #3, #4 | `bin/perry-state § parse_tracks` |
| 3 | Mode files annotated per slot with their axis | 1, #5 | No rule moves; each gains a label |
| 4 | Triage renders its question from (spine, flow) | 2, 3 | Where a mixed track stops being invisible |
| 5 | A mixed track exercised end to end on this repository | 4 | The pass condition, DESIGN-003 § 5.9's sense |

## 7. Risks & mitigations

- **The matrix becomes the interface.** If presets erode, every user meets a
  4×4 grid. *Mitigation:* goal 2 and decision #3 — the preset name stays the
  documented way in, and the axes are an override, not the front door.
- **A combination that cannot work.** `inquiry` spine with `pipeline` flow may
  be incoherent. *Mitigation:* step 1 must name illegal pairs, and the parser
  refuses them by name rather than producing a half-configured track.
- **Slot #2 assigned wrongly.** It only fails when two presets are combined,
  which is exactly the new case. *Mitigation:* it is a user decision, not an
  author's call, and step 5 exercises it.
- **This document becomes a second account of work modes.** *Mitigation:* it
  revisits DESIGN-003 rather than superseding it; on lock, DESIGN-003 § 9 gains
  a `## Changes` entry pointing here.

## 8. Open questions

1. **Does `phase/` survive on a mixed track?** DESIGN-003 § 8 already asks this
   for non-`project` modes and defers it to a fixture. A spine axis makes the
   question sharper — a track with an `objectives` spine has a phase whatever
   its flow is — but does not answer it.
2. **Is "consequence" one axis or a property of the row?** `Default rung` is a
   floor; the row can raise it. A floor that every row overrides is not an axis.
3. **What does a track with no flow mean?** `project` mode's flow is "Status
   only", which is a real answer. Whether that is a fourth flow value or the
   absence of one changes whether `Flow` can be blank.

## 9. Changes (append-only after lock)

- 2026-08-20 — created. Raised by the user against DESIGN-003 § 5.1; § 1.2's
  measurement run first, as `TASK-133`, so the document opens with what is true
  rather than with what is argued.

## 10. References

- `perry/design/DESIGN-003-work-modes.md` § 5.1, § 5.2, § 8 — the design this revisits
- `perry/evidence/2026-08/TASK-133-track-experiment.md` — § 1.2's measurement
- `modes/project.md`, `modes/pipeline.md`, `modes/queue.md`, `modes/inquiry.md`
- `perry/OKR.md` v2 § Objective 1 — KR-O1.1, KR-O1.2, KR-O1.3
