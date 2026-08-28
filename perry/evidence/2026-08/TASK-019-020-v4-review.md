# V4 review — TASK-019 (`modes/pipeline.md`) and TASK-020 (`modes/queue.md`)

> Date: 2026-08-16
> Reviewer: independent agent, fresh context
> Criteria: `perry/design/DESIGN-003-work-modes.md § 1.3` and `§ 5.1` (the four-mode table)
> **VERDICT — pipeline: FAIL · queue: FAIL**

## Review conditions

The reviewer was given the two artifacts, `modes/project.md` as a format
reference, and §1.3 / §5.1 of DESIGN-003 as the acceptance criteria. It was
explicitly barred from `perry/journal/`, `git log`, `BOARD.md`, `evidence/` and
every other section of DESIGN-003 — i.e. from the reasoning that produced the
files. That bar is what makes this V4 rather than V1 (`schema/state-schema.json
§ verification`), and it is why the finding list below contains things the
author could not see.

**Criterion A passed on both files**: all eight §5.1 slots are present and no
cell contradicts the table. Both failed on **D (actionability)** and **C
(internal consistency)**: each file names a control it never makes computable,
and the two disagree with each other about where the same object lives.

## Blocking findings

**B1 · Item states have no recording location.** `pipeline` declares
`brief → draft → review → approved → published`; `queue` declares
`new → triaged → in_progress → resolved`. Neither file says *where on a
`BOARD.md` row a stage is written*. TASK-015 added one optional column
(`Track`), and `Status` is enum-validated against the project-mode vocabulary —
so writing `draft` there fails lint, and inventing a column no design authorizes
is the only alternative. **Every downstream rule in both files depends on this
and none of them can execute.**

**B2 · The arrival date is destroyed at the moment it becomes needed.**
`queue`'s Intake table records `Arrived`; routing moves the row out of intake
into "a normal row", which has no arrival field. Triage step 2 then requires
"items past their promised turnaround, oldest first, with the age". The mode's
second-highest-priority triage step is **uncomputable by construction**. Same
defect on "a row still sitting there after two triages" — there is no triage
counter, so *age* is computable and *"two triages"* is not.

**B3 · The WIP limit — pipeline's central control — has no home and no
default.** The file says where the *stage list* is declared and never where the
*limit numbers* are. Same for "the stage's expected dwell time". An agent
cannot evaluate "is this stage at its limit" for any track, which makes the
rule decorative. (Related: DESIGN-003 § 5.2's own example writes `WIP 3` as a
single per-track number, while the mode file specifies per-stage limits — the
design and the mode file disagree.)

**B4 · `OKR.md § Commitments` has no track key, no item link, and no declared
owner.** Both modes put their spine in a Commitments table inside `OKR.md`,
with no `Track` column — so two tracks write into one undifferentiated table
with no way to tell whose promise is whose. Neither file says which lane
**owns** that section, while both simultaneously disclaim the objectives
cascade. And no column links a commitment to the item that discharges it, which
is what makes pipeline triage step 3 and queue triage step 2 unrunnable.

## Significant findings

- **S5** · `queue`'s "Calendar: Binding" is asserted and never argued.
  `pipeline` does the work — concedes `okr/SKILL.md § Why phases, not months`,
  scopes it, inverts it. `queue` carries neither the argument nor a pointer to
  it.
- **S6** · `pipeline`'s "cycle" is never defined — no length, no boundary, no
  declaration site. "Items due in this stretch" is circular, so the horizon
  cannot close, which is the slot's whole job.
- **S7** · SLA has two homes: `.perry/config.md § Tracks` in `pipeline`, the
  `By when` column of Commitments in `queue`. No cross-reference, no precedence,
  in two modes the design expects to coexist.
- **S8** · **"Binding" has no enforcement anywhere, which makes it advisory with
  stronger adjectives.** V5 has a named check; the binding calendar has none —
  no lint for an overdue commitment, no check that a missed date produced the
  journal line `pipeline` requires. By `modes/project.md`'s own definition of
  advisory, both new modes are also nudges.
- **S9** · `dropped` contradicts pipeline's own stage rule: the mode ends on
  "ships or is explicitly dropped", but "an item is in exactly one stage" over a
  vocabulary with no `dropped` stage. `modes/project.md` handles this correctly
  by listing `dropped` in its state set.
- **S10** · `queue` mandates Dropped-with-a-reason and Deferred-with-a-condition
  and ships an Intake table with two columns and nowhere to put either.
- **S11** · The mode's self-declared highest-value move — convert a recurring
  request into a Cadence row with a runbook — has no table template and never
  says where a runbook lives.
- **S12** · `queue`'s WIP control has no number and no data source; the "trend"
  is computed from the arrival dates B2 shows are discarded. "Reviewed on a
  period" never says how long the period is.

## Minor

- **M13** · One tool, two names for its source list, across the two files; and
  the pipeline sentence is placed as if `--verification` enforced the V5 *mode
  default*, when what it describes is the high-stakes rule — so ordinary
  pipeline rows closing below V5 are unenforced.
- **M14** · `pipeline`'s banner advertises legal matters; its closing section
  says not to use it for them.
- **M15** · §5.1 claims the tier-0 cost is "one line in `.perry/config.md`";
  pipeline requires a per-track stage vocabulary, per-stage WIP limits,
  per-stage dwell times and a cycle definition. That is a config block.

## What the reviewer rated strongest

- **pipeline** — the calendar section is the one place in either file where a
  contested claim is *argued* rather than stamped: it concedes the opposing
  rule, scopes it, and converts the inversion into something someone can follow.
- **queue** — the two honest negatives ("Perry is not a scheduler"; "an intake
  that overflows the board is the finding, do not raise the cap") refuse
  overreach at exactly the two points where inventing a capability would have
  been easiest.

## Assessment

**The findings are correct and the FAIL is right.** B1–B3 are implementation
gaps: the mode files describe controls whose data has no declared location, and
the fix is schema plus prose. B4 is different in kind — "which lane owns
`OKR.md § Commitments`" is a **file-ownership question**, which is the hand-off
contract, which is TASK-026. It cannot be answered inside a mode file.

This is the first time Perry's verification ladder has rejected Perry's own
work, and it caught four blocking defects that the authoring session could not
see. That is the argument for the ladder, made at Perry's own expense.
