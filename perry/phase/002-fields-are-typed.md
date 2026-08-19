# Phase #002 — fields-are-typed

> **Owner**: `goals` lane (only writer). `work` reads this every standup.
> **Started**: 2026-08-19
> **Status**: active
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

- Decide whether a **hand-edited rendered file** is a `warn` or an `error`
  (ADR-007 decision 2 says it becomes drift; the severity is unset).
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
| P-O1.1 | `BOARD.md` is rendered from `perry/tasks.jsonl`, which is the only thing writers write (baseline: the markdown is canonical) | 1 of 1 | — |
| P-O1.2 | `OKR.md` and `.perry/config.md` likewise (baseline 0 of 2) | 2 of 2 | — |
| P-O1.3 | A hand edit to a rendered file is reported rather than honoured, at the severity the user picks (baseline: it is honoured) | reported | — |

## Objective 2 — The defect classes cannot be expressed

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P-O2.1 | `CLOCK_RE` deleted and `By when` split into `due` + `by_when_note` (baseline: one column, five failed review rounds) | 0 occurrences of `CLOCK_RE` | — |
| P-O2.2 | Readers that resolve a header cell for the three stores (baseline 5 live copies across 4 rounds) | 0 | — |
| P-O2.3 | Lines of markdown parser serving the three stores (baseline 3,320 across `viewer/parsers.py` and `viewer/tables.py`) | 0 for the three; adoption keeps what it needs | — |

## Objective 3 — Agents work the new way

| Id | KR text | Metric / Target | Linked overall KR |
|---|---|---|---|
| P-O3.1 | Lane procedures that hand-edit a rendered file (baseline: unmeasured) | 0 | — |
| P-O3.2 | The read contracts survive the move unchanged — a consumer pinned at `perry-task/list/1.9` needs no edit (baseline: 1.9 live, aiMark pinned at 1.5) | 0 breaking changes | — |

## Week-by-week breakdown

| Week | Focus | KRs | Notes |
|---|---|---|---|
| 2026-W34 | `tasks.jsonl` as truth; `BOARD.md` rendered from it | P-O1.1, P-O3.2 | TASK-038 is this |
| 2026-W35 | `By when` split; `CLOCK_RE` deleted | P-O2.1 | independent of the rest |
| 2026-W36 | `OKR.md` + `.perry/config.md`; parser removal | P-O1.2, P-O2.2, P-O2.3 | one migration |

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
