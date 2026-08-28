# DESIGN-008: `Mode` is two axes wearing one name

> Status: locked
> Date: 2026-08-20 · Locked: 2026-08-20
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
| Default min. rung | how much verification the *consequence* needs | **neither** — see #1 |
| Signature failure | derived | derived |

Counted across the four mode files, that is **10 / 14 / 12 / 14 = 50 contract
slots**, ~28 distinct. The draft read that as three axes; walking § 4 resolved
it to **two axes, one plain field and four derived slots** — the `Axis` column
above is the observation, and § 5.2 is what it settled into.

### 1.2 The coupling is prose, not mechanism — measured, not assumed

This was tested on 2026-08-20 rather than argued (`evidence/2026-08/TASK-133-track-experiment.md`).
A `queue`-mode track was declared on this repository, a row created on it, and
that row attached to `P002-O1-KR3`, a KR of a `project`-mode phase:

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
| 1 | How many axes | Two — spine, flow / Three — spine, flow, consequence / **Two plus rung as a plain per-track field** | **Two plus rung as a field** | 2026-08-20 |
| 2 | Which side owns "the unit that gets an ID" | Spine / Flow / **Neither — it is derived from spine** | **Derived from spine** | 2026-08-20 |
| 3 | Whether `Mode` survives | **As a preset name** / As a deprecated alias / Removed, axes only | **Preset name** | 2026-08-20 |
| 4 | What an unspecified leg means | **Inherit from the preset** / Inherit from `project` / Refuse the row | **Inherit from the preset** | 2026-08-20 |
| 5 | Whether a mode file stays one file per mode | **One per mode, annotated** / One per spine + one per flow / A single matrix page | **One per mode, annotated** | 2026-08-20 |
| 6 | Whether existing declarations migrate | **Never — presets are permanent** / On next write / A one-time `perry-config` migration | **Never** | 2026-08-20 |

Notes on the resolved rows, written after they were walked:

- **#1 went against this document's own draft, and the reason is a
  measurement.** The draft bolded *three axes* on the argument that "how much
  verification does this need" is independent of both spine and flow — which is
  true. What killed it is that the independence **needs no axis to express it**:
  `Default rung` is already a column in the track register, already overridable
  per track and per row, and this repository's first real declaration overrode
  queue's V2 to V3 on 2026-08-20 without any axis machinery existing. A rung
  floor is a scalar, not a dimension with a vocabulary; promoting it would have
  meant inventing a set of consequence values (`internal` / `outward-facing` /
  …) that nothing today asks for. **Two axes, and `Default rung` stays the
  plain field it already is.**

- **#2 was the one genuinely contested slot, and it resolved to "do not declare
  it at all".** The tension was real: "the deliverable, not the task" reads
  like a statement about what the work is *for* (spine), but it decides what a
  board row **is**, which drives `Stage`, `Arrived` and the WIP denominator
  (flow). What settled it is that each spine value implies exactly one unit —
  objectives→task, commitments→deliverable, question tree→question — so the
  field would be one-to-one with a field that already exists. **A declarable
  field that can only ever hold one correct value is a field that can hold a
  wrong one**, and the wrong value would only surface when someone mixes two
  presets, which is precisely the new case this design creates.

  It also gives the right answer on the motivating case. "Goals decomposed
  through `project`, tasks advanced as a `queue`" has an `objectives` spine, so
  its unit is a **task** — not a "request", which is what flow-ownership would
  have renamed it to. Changing how work is advanced must not change what a row
  is.

- **#3, #4 and #6 are one decision in three places, and Goal 2 forced all
  three.** The preset name survives, an unstated leg inherits from the preset,
  and nothing migrates. Together they mean a project that wrote `Mode: project`
  a year ago is untouched, reads the same, and behaves the same. #6's rejected
  options are both rewrites of a line the user hand-wrote, which
  `perry/OKR.md § Anti-Goals` forbids: *no automatic rewrite of a project's
  existing structure.*

- **#5 follows #3.** If the preset is the front door, the documentation is
  organised by preset. Each of the ~28 slots gains a label naming its axis; no
  rule moves file. The cost is accepted and named: reading "what is queue's
  flow" means selecting the labelled lines out of one mixed file, and the
  router keeps loading exactly one mode file per track.

## 5. Architecture

*Written against § 4's six resolved decisions, 2026-08-20. Every claim below
cites the decision it rests on.*

### 5.1 The declaration

```markdown
## Tracks

| Track  | Mode     | Spine      | Flow        | Stages  | WIP | SLA | Cycle    | Default rung |
|--------|----------|------------|-------------|---------|-----|-----|----------|--------------|
| core   | project  | —          | —           | —       | —   | —   | —        | —            |
| ops    | project  | —          | queue       | new→…   | 6   | 5d  | weekly   | V3           |
| kb     | pipeline | —          | —           | brief→… | 3   | —   | 2026-W34 | V5           |
```

**Row 1 is what every project writes today and it parses identically** (goal 2).

**Row 2 is the motivating case** and shows what decisions #3 and #4 buy: it
declares one leg. `Mode: project` still supplies the spine — objectives and a
phase — and `Flow: queue` overrides only how a row advances. `Spine` is blank
because the preset already answers it; blank means *inherit from the preset*,
never *inherit from `project`* (#4), which is why row 3 can leave both blank and
still be a pipeline in full.

`Default rung` is **not an axis** (#1). It is the column it already is, and
row 2 overrides it for a reason that belongs to neither axis — an arriving row
on that track is a code defect, and a resolution note is not evidence.

### 5.2 The slot table — where the work is

*Completed slot by slot on 2026-08-20 (`TASK-140`), and counted rather than
estimated. The four contract tables hold **10 / 14 / 12 / 14 = 50 slots, 21
distinct** — `tests/test_track_axes.py` asserts both numbers against the mode
files. §§ 1.1 and 2 say "~28"; that figure was written before anyone counted
and 21 is what is there. The sections that carry it are not edited, because a
locked document does not get quietly corrected in passing — this is the count.*

**How to read a row.** A slot sits on an axis when its value follows that leg
and is unchanged by the other. The test is a mixed track, not a preset.

| Axis | A slot belongs to it when |
|---|---|
| `spine` | its value follows the spine leg and the flow leg does not move it |
| `flow` | its value follows the flow leg and the spine leg does not move it |
| `derived` | it is written nowhere, and is rendered at read time — from the spine alone (`Unit`, #2) or from both legs |
| `field` | it is declared per track in the register, independently of both legs |

`In` names the mode files that carry the slot; `tests/test_track_axes.py` checks
that column against the four files, so deleting a slot from one of them reddens
this table even when three others still carry it.

| Slot | In | Axis | Why |
|---|---|---|---|
| **Spine** | project · pipeline · queue · inquiry | `spine` | |
| **Ends when** | project · pipeline · queue · inquiry | `spine` | the container ends when the thing it is accountable to concludes; changing how a row advances does not move it |
| **Horizon** | project · pipeline · queue · inquiry | `spine` | the horizon's *kind* is spine-fixed — phase, cycle, review period, root question. `Tracks` → `Cycle` holds the instance, and that cell is a field |
| **Commitment link** | pipeline | `spine` | |
| **Question tree** | inquiry | `spine` | `BOARD.md` → `Parent` does not accompany the spine, it constitutes it: inquiry's spine cell is defined as the rows whose `Parent` is empty |
| **The answer** | inquiry | `spine` | the artifact the spine's unit closes into. A question answered under any flow still writes one answer file |
| **Sources** | inquiry | `spine` | |
| **Claim → source** | inquiry | `spine` | not part of the rung despite sharing a sentence with it — the rung is a scalar `V0`–`V6` and "clean provenance" is not one of its values, so it cannot live in the field |
| **Item states** | project · pipeline · queue · inquiry | `flow` | |
| **Stage vocabulary** | pipeline | `flow` | |
| **Stage clock** | pipeline | `flow` | |
| **Question clock** | inquiry | `flow` | the same `BOARD.md` → `Stage since` column as `Stage clock`, under a second name. The sketch omitted it; it is the one slot no group named |
| **Arrival** | queue | `flow` | |
| **SLA** | queue | `flow` | the *promise* of a turnaround sits in queue's spine cell; this slot is the clock the flow runs against it, which is why pipeline reads the same `Tracks` → `SLA` column under the name `Dwell time` |
| **Dwell time** | pipeline | `flow` | see `SLA` — one register column, two flow readings |
| **WIP control** | project · pipeline · queue · inquiry | `flow` | |
| **Unit that gets an ID** | project · pipeline · queue · inquiry | `derived` | from the spine alone (#2). One-to-one with the spine value by the map below, and never declared, so it cannot contradict it |
| **Calendar** | project · pipeline · queue · inquiry | `derived` | moved off `flow`; the argument is below |
| **Triage asks** | project · pipeline · queue | `derived` | |
| **Signature failure** | project · pipeline · queue · inquiry | `derived` | reads the rung as well as both legs — project's "`done` rows with no evidence" is a rung clause, so the rendering is over (spine, flow, rung) rather than the two legs alone |
| **Default rung** | project · pipeline · queue · inquiry | `field` | unchanged from today (#1). Under #4 a blank cell inherits the **preset's** default rather than either leg's, which is what holds a mixed track's rung floor still |

Eight spine, eight flow, four derived, one field.

**`Calendar` is `derived`, and that is a disagreement with § 1.1.** Both § 1.1's
`Axis` column and this section's sketch put it on flow. It cannot sit there,
because binding-ness has two independent sources that coincide on the four
diagonals and only there: the **spine** may name a date promised to a party
(pipeline's `Due`, queue's standing SLA), and the **flow** may run a breach
clock (pipeline's dwell, queue's arrival + SLA). Their independence is visible
without leaving the presets — `inquiry`'s flow carries a stage clock exactly as
`pipeline`'s does, yet inquiry's calendar is advisory and pipeline's is binding.
**A clock is not what makes a date binding; a promise is.** Each single-leg
assignment then breaks a live case in the opposite direction: on flow,
`Mode: pipeline · Flow: project` reports a dated promise to a client as
advisory, dropping an enforcement somebody was actually given; on spine,
`Mode: project · Flow: queue` — § 1.3's case, this repository — reports a real
SLA on an arriving row as a nudge. Derived answers both, because it is binding
when **either** leg says so. It also settles this section's own arithmetic,
which claimed four derived slots while listing three.

**The five slots the sketch marked "spine, provisionally" are all spine.**
`Commitment link`, `Question tree`, `The answer`, `Sources` and `Claim → source`
each survive the mixed-track test: run an inquiry spine under any flow and it
still needs sources, a parent and an answer file; run a commitments spine under
an inquiry flow and it needs none of them, because what it owes is a shipped
thing. The provisional mark comes off.

**The spine → unit map** (#2). § 7's third risk is that a spine value with no
unit is unrepresentable rather than merely awkward, so this table is where a new
spine finds a row it has to fill.

| Spine | What the work is accountable to | Unit that gets an ID |
|---|---|---|
| `project` | `OKR.md` objectives → `phase/<NNN>-<slug>.md` | **task** |
| `pipeline` | `OKR.md § Commitments` — a dated promise to a named party | **deliverable** |
| `queue` | `OKR.md § Commitments` — standing promises + an SLA, no objectives cascade | **request** |
| `inquiry` | the open root questions — `BOARD.md` rows with an empty `Parent` | **question** |

Complete over the four spine values and one-to-one over the four units.
`tests/test_track_axes.py` reddens on a spine with no unit and on one unit
appearing under two spines.

**`queue`'s unit is the `request`, and it was not a free choice.**
`modes/queue.md` writes "the request — or the incident", which is two nouns
where #2 allows one. Three things pick the same one: `schema/state-schema.json §
work_modes.modes.queue.unit` already reads `request`; § 4's note on #2 uses
"request" as queue's unit when arguing that flow-ownership would wrongly rename
a task to one; and one ID is minted per arrival either way, so *incident* names
an arrival nobody filed rather than a second unit.

**`pipeline` and `queue` do not share a spine, and the map is why.** Both cells
cite `OKR.md § Commitments`, which is what invited the sketch to group them.
One spine value has one unit, and queue's is not `deliverable` — so they are two
values that happen to be backed by one file. Giving them one value is not a
style choice that reads oddly; it makes `Spine`, `Ends when`, `Horizon` and
`Unit` disagree across two presets claiming a single value, and the round-trip
check reddens on all four at once.

**The presets** (#3, #4). Each mode name expands to its diagonal pair, and a
blank leg in `## Tracks` inherits from the preset — never from `project`.

| Mode | Spine | Flow |
|---|---|---|
| `project` | `project` | `project` |
| `pipeline` | `pipeline` | `pipeline` |
| `queue` | `queue` | `queue` |
| `inquiry` | `inquiry` | `inquiry` |

**What a mixed pair can and cannot render yet.** The eight spine slots and the
eight flow slots compose for all sixteen pairs, and the field follows the
preset. The four `derived` slots are recorded here only for the four diagonals:
rendering `Triage asks`, `Signature failure` and `Calendar` for an off-diagonal
pair is step 4's job, and § 6 depends on this table for exactly that. `Unit` is
the exception among the derived four — it reads the spine alone, so it is
already total over all sixteen pairs, which is what lets § 4's worked example
(`Mode: project · Flow: queue` has a **task**, not a request) be checked rather
than asserted.

**One gap this walk found in a mode file, left for step 3.** `modes/inquiry.md`
has no `Triage asks` row, where the other three do; and `modes/queue.md` has no
`Commitment link`, though its spine is a set of promises. Neither is an axis
question and neither is fixed here — annotating the mode files is § 6 step 3,
and this row does not touch `modes/`.

### 5.3 What is not changing

`BOARD.md` gains no column — `Track`, `Stage`, `Stage since`, `Arrived`,
`Parent`, `Commitment` and `Role` already exist and are already created on
demand. The linkage graph is untouched: § 1.2 measured that it never consulted
the mode.

### 5.4 Blast radius

Every surface that reads a track's shape, and what this does to it. Added at
lock pre-flight (`reference/input-quality.md § 3.6`), the same step at which
DESIGN-003 gained its § 5.9.

| Surface | Reads | Effect |
|---|---|---|
| `bin/perry-state § parse_tracks` | the register's columns | **Changes.** Two optional columns, each defaulting from the preset. A row with neither parses exactly as today |
| `$PERRY_HOME/SKILL.md` step 3b | one mode file per distinct `mode` | **Unchanged** by #5 — still one file per track, still keyed on the preset name |
| `work` triage | the track's mode | **Changes** at step 4: the question is rendered from (spine, flow) instead of from the mode name. A track with no override renders the same question it does today |
| `bin/perry-config` | the register as a store | **Changes** only in that two more columns round-trip. `## Tracks` is already a `track` record kind — measured 2026-08-20, `{'setting': 7, 'track': 2}` |
| `BOARD.md` | `Track`, `Stage`, `Stage since`, `Arrived`, `Parent`, `Commitment`, `Role` | **Unchanged.** Every column already exists and is already created on demand |
| `phase/<NNN>-linkage.md` | nothing about tracks | **Unchanged.** § 1.2 measured that it never consulted the mode |
| `schema/task-list-contract.md` | `tasks[].track` | **Unchanged.** The track name is what a row carries; its shape is not on the row |
| aiMark and any other consumer | `perry-state --json § project.config.tracks[]` | **Additive.** Two keys appear; none is removed or retyped, so it is a `1.x` change under `tests/test_contract_invariance.py` |
| A project that never declares a register | — | **Nothing.** `modes/project.md`'s no-op property is goal 2 and is what step 5 exercises |

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
  4×4 grid. *Detect:* count declared tracks that override a leg; if most do,
  the presets no longer describe real work. *Mitigate:* goal 2 and decision #3 —
  the preset name stays the documented way in, and the axes are an override,
  not the front door.
- **A combination that cannot work.** `inquiry` spine with `pipeline` flow may
  be incoherent. *Detect:* the parser refuses the pair by name, so it surfaces
  at declaration rather than as a track that half-works. *Mitigate:* step 1
  must enumerate the illegal pairs; an unenumerated pair is allowed, so the
  list being wrong shows up as a bad track rather than as a silent refusal.
- **The unit is derived, so a spine with no obvious unit has none.** #2 removed
  the field on the ground that each spine value implies exactly one unit. A
  spine added later that does not is then unrepresentable rather than merely
  awkward. *Detect:* adding a spine value means adding a row to the spine→unit
  map, and an empty cell there is the signal. *Mitigate:* step 1 records that
  map explicitly, so a new spine has a row it must fill rather than a
  convention to infer.
- **A preset that is half-overridden reads as the preset.** #4 makes a blank
  leg inherit, so `Mode: pipeline · Flow: queue` still says "pipeline" at a
  glance. *Detect:* the snapshot renders the resolved pair, not the preset
  name, wherever a track's shape is reported — so a half-overridden track reads
  as one on sight. *Mitigate:* same line; the rendering is the mitigation.
- **This document becomes a second account of work modes.** *Detect:* a rule
  stated here that is not also in a `modes/` file or a test. *Mitigate:* it
  revisits DESIGN-003 rather than superseding it, and #5 keeps the rules in the
  mode files; on lock, DESIGN-003 § 9 gains a `## Changes` entry pointing here.

## 8. Open questions

1. **Does `phase/` survive on a mixed track?** DESIGN-003 § 8 already asks this
   for non-`project` modes and defers it to a fixture. A spine axis makes the
   question sharper — a track with an `objectives` spine has a phase whatever
   its flow is — but does not answer it.
2. ~~**Is "consequence" one axis or a property of the row?**~~ **Closed by
   decision #1 on 2026-08-20**, not deferred: a floor is a scalar, it is
   already an overridable column, and no vocabulary of consequence values is
   wanted by anything. It stays the field it is.
3. **What does a track with no flow mean?** `project` mode's flow is "Status
   only", which is a real answer. Whether that is a fourth flow value or the
   absence of one changes whether `Flow` can be blank.

## 9. Changes (append-only after lock)

- 2026-08-20 — created. Raised by the user against DESIGN-003 § 5.1; § 1.2's
  measurement run first, as `TASK-133`, so the document opens with what is true
  rather than with what is argued.
- 2026-08-20 — § 5.4 blast radius added and every § 7 risk given a detection
  signal, at `lock` pre-flight (`reference/input-quality.md` § 3.6, § 3.7) —
  the same step at which DESIGN-003 gained its § 5.9. One advisory point was
  **overridden rather than fixed**: decision #5 (how `modes/` is organised) is
  arguably a choice an agent could have made alone rather than a user-only
  one (§ 3.5). It was asked anyway, because #3 had just made the preset the
  front door and the documentation shape follows from that — the two answers
  had to be given by the same person.
- 2026-08-20 — locked.
- 2026-08-20 — all 6 User Decisions resolved. **#1 was chosen against this
  document's own draft**, which had bolded three axes; the argument that beat it
  is in § 4's notes and it is a measurement, not a preference. § 5.1's example,
  § 5.2's slot table, one § 7 risk and § 8's second open question all moved as a
  consequence, and the title's "three axes" is now the position the document
  argues *against*.
- 2026-08-20 — **§ 5.2 moved from sketch to complete** (`TASK-140`, § 6 step 1).
  All 50 contract slots across the four mode files are assigned, the spine →
  unit map is written, and the preset expansion is stated. Three things changed
  against the sketch, each argued in the section: `Calendar` moved from `flow`
  to `derived`, which is a disagreement with § 1.1's own `Axis` column and which
  reconciles this section's claim of four derived slots with its list of three;
  `Question clock` was added, the one slot no group had named; and `pipeline`
  and `queue` were separated into two spine values rather than the one
  `commitments` the sketch implied, because the map gives them different units.
  The distinct-slot count is **21**, measured — §§ 1.1 and 2 estimate "~28" and
  are left as written, since a locked document is not corrected in passing.
  `tests/test_track_axes.py` is the mechanical check: coverage against the four
  mode files in both directions, the preset round-trip value by value, and the
  map's completeness and one-to-one-ness. No other section is touched, and
  `modes/` is untouched — annotating the mode files is step 3.

## 10. References

- `perry/design/DESIGN-003-work-modes.md` § 5.1, § 5.2, § 8 — the design this revisits
- `perry/evidence/2026-08/TASK-133-track-experiment.md` — § 1.2's measurement
- `modes/project.md`, `modes/pipeline.md`, `modes/queue.md`, `modes/inquiry.md`
- `perry/OKR.md` v2 § Objective 1 — KR-O1.1, KR-O1.2, KR-O1.3
