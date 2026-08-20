# TASK-140 — every mode contract slot is assigned to an axis

> Source: `perry/design/DESIGN-008-track-axes.md` § 5.2, § 6 step 1
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: DESIGN-008 § 5.2 — it completes that section; it changes no behaviour
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O1.1 / KR-O1.2 / KR-O1.3 (`perry/OKR.md` v2, Objective 1)

## Read this first

`perry/design/DESIGN-008-track-axes.md`, locked 2026-08-20, all six user
decisions resolved. **You are step 1 of its § 6, and the document says step 1
is its real payload rather than a preliminary.** Steps 2–5 are all functions of
your output, so they are not open and you are not writing code that consumes it.

Two of its decisions bind you and are not yours to revisit:

- **#1 — two axes.** `spine` and `flow`. `Default rung` is **not** a third
  axis; it is the plain per-track column it already is. Do not add a
  consequence axis, and do not assign any slot to one.
- **#2 — the unit is derived from the spine, never declared.** Each spine value
  implies exactly one unit. That is why the map below is part of this row.

## Deliverable

### 1 · The slot table

Every slot in the four mode contract tables — `modes/project.md`,
`modes/pipeline.md`, `modes/queue.md`, `modes/inquiry.md`, **10 / 14 / 12 / 14 =
50 slots, ~28 distinct** — assigned to exactly one of:

| Axis | Meaning |
|---|---|
| `spine` | what the work is accountable to |
| `flow` | how one row advances |
| `derived` | rendered from spine + flow; never declared |
| `field` | a plain per-track column, declared but not an axis |

A slot whose assignment is not obvious gets **one line of reason**. Do not
write a reason for the obvious ones — a table where every row carries prose is
one nobody reads.

The seed assignments in § 5.2 are a **sketch, not an answer**. Check each one.
If you disagree with one, say so with the argument; the document was written by
someone who had not yet gone slot by slot.

### 2 · The spine → unit map

An explicit table: each spine value → the unit that gets an ID. § 1.1 and § 4's
note give three (`objectives`→task, `commitments`→deliverable, question
tree→question) and queue's is the fourth. This exists because decision #2
deleted the declarable field, so **an unmapped spine value is unrepresentable
rather than merely awkward** (§ 7).

### 3 · Where it lives

`DESIGN-008 § 5.2`, replacing the sketch. **`decide` owns `design/`** — this is
the one row where writing a design file is the deliverable, and the design is
locked, so append a `## Changes` entry recording that § 5.2 moved from sketch to
complete. Do not change any other section.

## Verification — V3

1. **Coverage is mechanical, not eyeballed.** A check extracts the slot names
   from the four mode files' contract tables and fails on any slot the table
   does not mention. Deleting a slot from a mode file reddens it; adding one to
   a mode file reddens it. Both proved by doing it, then reverting.
2. **The presets round-trip.** Each of the four mode names expands to a
   (spine, flow) pair, and that pair reproduces that mode file's own contract
   table **value by value** — not "a pair exists". Where a value cannot be
   reproduced, that is a finding about the assignment, not a reason to relax
   the check.
3. **The spine → unit map is complete and one-to-one**: every spine value in
   the table has exactly one unit, and no unit appears under two spines. A
   spine added with no unit reddens.
4. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Baseline

Measure it in your own worktree. `test_diagnose` is expected red for a reason
that is not yours (TASK-126 — a check whose only live references are inside the
record describing its own fix). If anything else is red, say so; your
measurement wins over this line.

## Files in scope

- `perry/design/DESIGN-008-track-axes.md` § 5.2 and its `## Changes`
- the coverage check and its test module

## Out of scope

- **Any change to `bin/`, `modes/`, or `.perry/config.md`.** Steps 2–4 of § 6
  own those and they are not open. Annotating the mode files is step 3.
- Revisiting decisions #1 or #2. If you believe one is wrong, **say so in your
  result and stop at saying so** — a locked decision changes through `revise`,
  by a human, not inside the row that implements it.
- Any other section of the design.
