# OKR — {{project_name}}

> **Owner**: `okr` skill (only writer). PMO and other skills read for snapshots.
> **Period**: {{period_label}} (e.g., "lifetime", "Q2 2026", "6 months")
> **Status**: {{Active | Closed}}
> **Tier 1 hard cap**: ≤ 200 lines. Overflow → move historical `## v<N>` retro blocks to `evidence/<YYYY-MM>/okr-vN-retro.md`; main file keeps current version + version log only.

This document is the long-term reference for the system. The `okr` skill uses it to derive phase OKRs (`phase/<NNN>-<slug>.md`) and weekly task proposals (handed off to `pmo`). Versions are append-only — never overwrite an old version block.

## Mission

{{One sentence: why this project exists.}}

## Operating Principles

> Invariants the system must hold across all Objectives, all versions, all months.
> Edit only via `/perry goals revise` (which bumps the version).

- {{principle 1}}
- {{principle 2}}
- {{principle 3}}
- {{principle 4}}
- {{principle 5}}

## Commitments

> Promises to a named party by a date — the spine for `pipeline`- and
> `queue`-mode tracks (`modes/pipeline.md`, `modes/queue.md`). Omit this
> section entirely on a project whose tracks are all `project` mode; a KR is
> the special case where the party is the project itself.
>
> The clock is **two columns**. `Due` is typed — an ISO date (`2026-09-30`) or
> an SLA token (`3d`, `2w`) — so triage can compare it against today and sort
> by it. `By when note` is prose, records how the deadline was worded to the
> party it was promised to ("within the track SLA"), and is **never
> validated**. Board rows point here by putting this table's `Id` in their
> `Commitment` cell — the link runs from the board side, so this table never
> accumulates ids that rot as rows close.

| Id | Track | Promise | To whom | Due | Status | By when note | Discharged by |
|---|---|---|---|---|---|---|---|
| {{track}}/1 | {{track}} | {{what was promised}} | {{who is waiting}} | {{YYYY-MM-DD or 3d}} | active | {{how it was worded, or empty}} | {{how, in prose}} |

## Anti-Goals

> Things this project will NOT do. First-class commitments — checked at every retro.

- {{anti-goal 1}}
- {{anti-goal 2}}
- {{anti-goal 3}}
- {{anti-goal 4}}

---

## v1: {{date}}

### Objective 1 — {{title}}

{{1–2 sentences explaining the goal.}}

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O1.1 | {{kr text}} | {{metric}} ≥ {{target}} | no | {{date}} |
| KR-O1.2 | {{kr text}} | {{metric}} ≥ {{target}} | no | {{date}} |
| KR-O1.3 | {{kr text}} | {{metric}} ≥ {{target}} | yes | {{date}} |

### Objective 2 — {{title}}

{{1–2 sentences explaining the goal.}}

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O2.1 | {{kr text}} | {{metric}} ≥ {{target}} | no | {{date}} |
| KR-O2.2 | {{kr text}} | {{metric}} ≥ {{target}} | no | {{date}} |

### Objective 3 — {{title}}     <!-- delete this block if only 2 Os -->

{{1–2 sentences.}}

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR-O3.1 | {{kr text}} | {{metric}} ≥ {{target}} | no | {{date}} |

### Retro — v1     <!-- filled when version closes; until then, leave empty -->

- **Period score**: —
- **Achieved**:
- **Partial**:
- **Missed**:
- **Lessons**:
- **Triggered new version**: —

---

<!--
## v2: YYYY-MM-DD

(Same structure as v1. Append a new block when revising. Old block stays for audit.)

-->

## Versioning log

- v1: {{date}} — initial draft.
