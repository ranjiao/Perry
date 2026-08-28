# Phase #002 — fields-are-typed

> **Owner**: `goals` lane (only writer). `work` reads this every standup.
> **Started**: 2026-08-19
> **Status**: scored
> **Source**: `decisions/ADR-007-fields-are-typed-prose-is-not.md`, decided 2026-08-19

## Phase Focus

**Stop parsing documents.** Three state files carry 55 typed columns between
them and no prose sections — `BOARD.md` (35), `OKR.md` (12), `.perry/config.md`
(8). They become stores that Python writes and reads, and the markdown becomes
rendered output.

The measure of success is not "the store exists". It is that **the defect
classes that produced five review rounds in one night cannot be expressed any
more**: no reader asks which column a cell is, no writer escapes a pipe, and no
regex asks prose whether it names a clock.

## Operating Rules

- **One migration, not three.** ADR-004's *a project migrates once* is the
  posture, so the three stores move together against the same real projects.
- **The agent protocol is the deliverable, not a side effect.** Call the tool
  for fields, then generate documents from what it returned. A procedure that
  still hand-edits a rendered file has not adopted this phase.
- **A deleted parser is the evidence.** Anything that survives the phase and
  still parses `BOARD.md`, `OKR.md` or `.perry/config.md` is unfinished work,
  not a fallback.
- Perry tracks itself (ADR-001), so Perry's own state is the first thing that
  migrates and the first thing that can break.

## Cost Ceiling (phase #002)

Spend cap: **$0** in new paid APIs, models or infra. Perry is stdlib Python and
stays that way. A dependency is a decision, not an implementation detail.

## User Commitments

- ~~Decide whether a **hand-edited rendered file** is a `warn` or an `error`
  (ADR-007 decision 2 says it becomes drift; the severity is unset).~~
  **DECIDED `warn` — Ran Jiao, 2026-08-21.** This confirms what ships rather
  than changing it: all nine drift findings in `bin/perry-lint`, across both
  the task store and the risks store, are already `Finding("warn", …)` and none
  is `error`. The reasoning the code gives for it is the reasoning accepted:
  *a drifted Board still has a valid Board shape*, and the conformance gate's
  boundary is that **warnings are quality signals while errors are shape
  violations**. The store stays authoritative, so drift can never change Task
  truth, and re-rendering restores the projection. Consequence accepted with
  it: a hand edit does not fail CI, and an emergency hand edit stays possible
  and is recorded rather than refused.
- Sign off the migration against a real project at **V5** — the same bar
  TASK-044 carried, because this rewrites the same files.

## User-Unavailable Degradation

If the user is unreachable, the store lands and the renderer lands, but
**migration of any project other than Perry's own does not run**. Rewriting
somebody's board without them is what ADR-004 exists to prevent.

## Phase Scope Reduction Rule

- **Phase-day trigger**: if by phase day 10 `BOARD.md` is not yet rendered from
  a store on Perry's own project, drop `OKR.md` and `.perry/config.md` from
  this phase and finish one file properly. One migrated store beats three
  half-migrated ones.

## Objective 1 — The three stores are stores

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P002-O1-KR1 | `BOARD.md` is rendered from `perry/tasks.jsonl`, which is the only thing writers write (baseline: the markdown is canonical) | 1 of 1 | — |
| P002-O1-KR2 | `OKR.md` and `.perry/config.md` likewise (baseline 0 of 2) | 2 of 2 | — |
| P002-O1-KR3 | A hand edit to a rendered file is reported rather than honoured, at the severity the user picks (baseline: it is honoured) | reported | — |

## Objective 2 — The defect classes cannot be expressed

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P002-O2-KR1 | `CLOCK_RE` deleted and `By when` split into `due` + `by_when_note` (baseline: one column, five failed review rounds) | 0 occurrences of `CLOCK_RE` | — |
| P002-O2-KR2 | Readers that resolve a header cell for the three stores (baseline 5 live copies across 4 rounds) | 0 | — |
| P002-O2-KR3 | Lines of markdown parser serving the three stores (baseline 3,320 across `viewer/parsers.py` and `viewer/tables.py`) | 0 for the three; adoption keeps what it needs | — |

## Objective 3 — Agents work the new way

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P002-O3-KR1 | Lane procedures that hand-edit a rendered file (baseline: unmeasured) | 0 | — |
| P002-O3-KR2 | The read contracts survive the move unchanged — a consumer pinned at `perry-task/list/1.9` needs no edit (baseline: 1.9 live, aiMark pinned at 1.5) | 0 breaking changes | — |

## Week-by-week breakdown

| Week | Focus | KRs | Notes |
|---|---|---|---|
| 2026-W34 | `tasks.jsonl` as truth; `BOARD.md` rendered from it | P002-O1-KR1, P002-O3-KR2 | TASK-038 is this |
| 2026-W35 | `By when` split; `CLOCK_RE` deleted | P002-O2-KR1 | independent of the rest |
| 2026-W36 | `OKR.md` + `.perry/config.md`; parser removal | P002-O1-KR2, P002-O2-KR2, P002-O2-KR3 | one migration |

## Definition of Done

Every one of these, measured:

1. `grep -c CLOCK_RE bin/` returns 0.
2. No reader resolves a header cell for the three stores —
   `tests/test_one_header_rule.py` has nothing left to check on them.
3. A hand edit to a rendered `BOARD.md` produces a finding, not a state change.
4. `perry-task/list` still reports `1.9` or higher with no breaking change, and
   the three read contracts pass their own tests unchanged.
5. gimegime-pmo and PolyForge migrate on a copy, at V5, with the user signing
   what was actually checked.

## Not Doing in this phase

- `design/*.md`, `DECISIONS.md`, `.perry/roles/*.md`, `phase/*.md`. They are
  documents under ADR-007 § 5b and they stay documents. **Python stops parsing
  them too, but that is a later phase**, and conflating it with this one would
  put a 10-section prose file in the same migration as a 35-column table.
- Adoption of foreign projects. That is parsing by definition and survives.
- The decision-status vocabulary (TASK-085) and the `NS-01` inversion
  (TASK-086). Real, small, and not this.

## Process Note

Phase 001 was scored at day 3 rather than when its KRs hit, because ADR-007
changed the premise of two of them. That is recorded in 001's retro, and the two
are re-expressed here against the shapes that will actually exist.

## Changes / Pivots     <!-- append-only -->

## Mid-phase check     <!-- filled by `okr dashboard` or `pmo mid-phase-review` -->

## Retro — phase scored     <!-- filled by `okr score-phase` when the phase closes -->

> Scored 2026-08-28 · started 2026-08-19 · phase day 9
> Snapshots: `phase/snapshots/2026-08-28-002-fields-are-typed-final.md` and
> `phase/snapshots/2026-08-28-002-linkage-final.md`

### Scores

| KR | metric | status | score |
|---|---|---|---|
| `P002-O1-KR1` | 1 of 1 | achieved | 1.00 |
| `P002-O1-KR2` | 2 of 2 | achieved | 1.00 |
| `P002-O1-KR3` | 1 of 3 rendered files report through `perry-lint` | **partial** | 0.33 |
| `P002-O2-KR1` | `grep -c CLOCK_RE bin/` = 0 | achieved | 1.00 |
| `P002-O2-KR2` | 0 readers resolve a header cell for the three stores | achieved | 1.00 |
| `P002-O2-KR3` | 3,320 → 1,048 parser lines (target 0) | **partial** | 0.68 |
| `P002-O3-KR1` | 0 lane procedures hand-edit a rendered file | achieved | 1.00 |
| `P002-O3-KR2` | 0 breaking contract changes; `perry-task/list/1.18` | achieved | 1.00 |

**Objective 1: 0.78 · Objective 2: 0.89 · Objective 3: 1.00 · phase mean 0.89**

### Definition of Done — 4 of 5

1. ✅ `grep -c CLOCK_RE bin/` = 0
2. ✅ `test_one_header_rule.py` passes; nothing left to check on the three stores
3. ✅ a hand edit to `BOARD.md` produced 2 rows drifted, measured 2026-08-28
4. ✅ `perry-task/list/1.18`, contract invariance green
5. ❌ **gimegime-pmo and PolyForge migrate at V5** — **carried to phase 003**

**Item 5 is carried, not waived.** The user decided on 2026-08-28 that the
target project's current state is not suitable for migration and that the
features land first. **So this phase's argument — that the abstraction survives
contact with a real project — was not tested.** Every one of the other four
items was measured on Perry itself, and Perry is the only project that grew up
under these rules from the start. `TASK-097` stays open and carries forward.

### What went well

**All five stores `claims[]` declares now exist**, three of them created on the
final day: `.perry/config.jsonl`, `perry/risks.jsonl`, and the intake and ask
stores built but not yet imported. The migration direction the phase was named
for is real rather than declared.

**The mutation-proof habit became the norm and it repeatedly found the gap.**
Three separate rows reported that a mutation site reddened *nothing* on the
first pass — including one where the check the agent had just written to make a
rejection real was itself unfalsifiable. Each added tests rather than counting
the pass.

**A precedent was measured rather than inherited, three times.** The byte-for-
byte render gate is load-bearing for risks and for asks, and a **tautology** for
intake — six malformed inputs came back byte-identical either way, so a
row-count gate was built instead. Same precedent, opposite conclusions, each
measured.

### What underperformed

**`P002-O1-KR3` at 0.33** is the honest one. Its metric said "reported" without
saying by what, and the phase ran nine days before anyone edited a cell in each
of the three files to find out. `perry-lint` — the tool the KR names — reports
one of three. `TASK-209` carries it.

**`P002-O2-KR3`'s target was probably wrong from the start.** Driving parser
lines to 0 would delete the adoption reader, which `TASK-094` proved must stay.
68% is real progress against a number that could not have been reached.

### Lessons for phase 003

1. **Counting implementations by grepping a name is the defect that cost most.**
   It recurred roughly ten times: a call site located once where there were two
   or three, once *over*-counted, and once a whole second reporter missed because
   a spec's file list named one of two. Grep the expression, or the call, never
   the name.
2. **A locked decision that gets no task row does not ship.** DESIGN-007's plan
   went **5-for-5** on steps that had rows and **0-for-9** on steps that did not.
   That is the mechanism, not a coincidence — and it is why the twelve decisions
   locked on the final day were each given a row in the same action.
3. **A check that reads the project living around it as its expected value** is
   still arriving. It was found in a fixture whose comment claimed the opposite,
   in a corpus that ran on one machine, and in an assertion that encoded a moment
   rather than its rule.
4. **A gate whose green is a tautology is worse than no gate**, because it reads
   as a guarantee. Measure whether a gate can fail before trusting its pass.

### Carry-overs proposed

| row | why |
|---|---|
| **`TASK-097`** | DoD item 5. The phase's own argument, untested. |
| **`TASK-050`** | Open under `P002-O2-KR2`; measures wider than that KR's metric. |
| **`TASK-095`, `TASK-099`** | Open under `P002-O2-KR3`; the parser reduction. |
| **`TASK-209`** | `P002-O1-KR3`'s real subject — the drift census covers one store of five. |

### Unlinked at scoring

**43 open rows resolve to no KR**, against 3 that do. They are **not averaged
into any KR score**, per `okr-linkage.md`'s rule that attribution is resolved by
id or asked for, never guessed.

This is the phase's largest single signal and it is not a bookkeeping lapse:
the phase declared 13 tasks and the board ran 47. **Phase 003 should either
declare KRs the live work actually serves, or the linkage step has to become
part of `add`.**

