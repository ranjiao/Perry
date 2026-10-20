# Perry hook — Perry

> **Tier 1** (user-read-and-edit). Owned by you, not by Perry.
> Hooks are **pure additions** to Perry's generic behavior — they never override a core rule.
> Read at every standup by `/perry`, and by every lane.

## High-stakes operations

The canonical screening policy is `.perry/safety.json`. The reviewed2026-10-20
migration preserves every literal rule from the former list and adds the actual
SQLite store/database and policy-update boundaries. Project and role rules form
an additive union; hook prose cannot remove a structured restriction. A match
requires the actual user authority for that operation, not just a filled string.
The pre-cutover hook is retained in the activation backup and source receipt.

## Project specifics

If the project is **Perry**:
- Roadmap source-of-truth: native kernel query/items/events through `bin/perry` — + `perry/design/` (locked designs are the plan of record)
- Prefer MCP tools: —
- Decision tag types: Process | Architecture | Tooling | Design
- Cost ceiling source: current native goal/phase facts; unknown if no typed value is declared.
- Special agents available: —
- Promotion / staging path: — (a skill repo; `main` is the only stage)

## Autopilot defaults

> Recognized by `work/reference/autopilot.md`.

```
Autopilot defaults:
- max_dispatches: 10
- max_duration_min: 120
- max_failures: 3
- excluded_tasks:
```

`excluded_tasks` is deliberately empty. The four DESIGN-003 tasks that must not
be automated (TASK-015, TASK-018, TASK-024, TASK-026) already carry
`Dispatch mode: manual` in their specs, which is the gate that actually holds —
listing them here too would create a second copy to keep in sync, and Perry's
own rule is one fact, one place.

## Configuration notes (historical rationale)

The rendering commands and legacy lane names described below are historical.
Current settings/document anchoring follow `reference/config.md`; structured
project state lives in kernel items/events and owned narratives remain attachments.


> **Moved here from `.perry/config.md` on 2026-08-30 (TASK-233), verbatim.**
> That file is a projection of `.perry/config.jsonl` now: `perry-config render`
> rebuilds it from the store with no copy of it on disk, and what a store holds
> is settings and track rows — never prose. Prose in the projection survives a
> render only while a file is there to copy it out of, which is a guarantee
> that ends the first time the file is deleted or a project is cloned without
> it. This file is not rendered from anything, so it cannot lose them.
> `reference/config.md § Prose in this file is layout` is the general rule.

### What the two tracks carry

`intake` carries the work that ARRIVES — a defect an agent found mid-run, a
sibling a sweep turned up, a review finding. It is not decomposed from a goal,
it shows up, and its useful questions are queue questions: what has been
waiting longest, how deep is the backlog, what keeps recurring.

`main` carries the work that is DECOMPOSED — the phase, its KRs, the rows that
serve them.

Declared 2026-08-20 as the experiment in TASK-133. `Default rung` is V3 rather
than queue mode's V2 default: an arriving row here is a code defect, and a
resolution note is not evidence that it is fixed.

### Why the state root is not `.`

Perry's own `design/` directory is the **design lane skill**
(`decide/SKILL.md`, `decide/state/design_TEMPLATE.md`), not a folder of design
documents. Pointing the state root at the project root would make Perry claim
its own source tree, and every lint run would report `decide/SKILL.md` as a
malformed design doc.

`okr/` and `pmo/` are lane skills for the same reason. `.perry/` stays at the
project root: it holds this pointer, so it cannot sit behind it.

This is the collision described in `perry/design/DESIGN-002-namespace-collision.md`
— Perry is its own proof case, and this file is the escape hatch that document
argues should be offered automatically rather than written by hand.

For the current layout see `reference/config.md` and `work/reference/kernel.md`.
