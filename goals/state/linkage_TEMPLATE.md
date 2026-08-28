---
linkage: 1
phase: "{{NNN}}-{{slug}}"
updated: "{{YYYY-MM-DD}}T{{HH:MM:SS}}Z"
objectives:
  - id: O1
    title: "{{phase objective 1 title}}"
    krs:
      - id: P{{NNN}}-O1-KR1
        title: "{{kr text}}"
        metric: "{{metric as written in the phase file}}"
        # `target` is a NUMBER or absent — omit it for a prose target
        # ("≤ 15% drawdown"), whose words live in `metric`.
        target: 0
        # **`current` is absent on purpose, and stays absent until an author
        # asserts a number.** It used to be written here as `current: 0`, and
        # TASK-120 measured what that costs: six of eight phase KRs on this
        # project carry `target: 0`, because most real KRs drive a count DOWN
        # — so a `current` defaulted to `0` makes every one of them read as
        # met on the day the register is created. Nothing re-derives these
        # numbers; an unasserted one is absent, and Perry reports it as
        # `unasserted` rather than as zero.
        stretch: false
        tasks: []
      - id: P{{NNN}}-O1-KR2
        title: "{{kr text}}"
        metric: "{{metric}}"
        stretch: false
        tasks: []
  - id: O2
    title: "{{phase objective 2 title}}"
    krs:
      - id: P{{NNN}}-O2-KR1
        title: "{{kr text}}"
        metric: "{{metric}}"
        stretch: false
        tasks: []
unlinked: []
agents: []
projects:
  - id: "{{PROJ-001}}"
    serves: P{{NNN}}-O1-KR1
    objective: O1
    name: "{{project name}}"
    aliases: []
    status: active
---

# Phase #{{NNN}} — O→KR→task linkage

> **Owner**: `okr` skill (only writer — this file lives under `phase/`), and within it
> **`bin/perry-goals link` performs every write** — the edge, the alias, the declared
> `unlinked`, the new Project — in place, refusing anything that does not resolve to
> exactly one KR. PMO reads it for roll-up + task→KR resolution; PMO never writes it. Both Perry and the frontend read the
> **frontmatter above** — this body is documentation, never a second source of truth.
> **Tier**: 2 (agent-state, no line cap). One entry per Project, so name drift and large
> O→KR→Project fan-out never touch the phase file's 300-line tier-1 cap.
> **Spec**: `linkage: 1`. Contract in `$PERRY_HOME/schema/README.md § The linkage contract`.

## What each part is for

| Key | Read by | Purpose |
|---|---|---|
| `objectives[].krs[].tasks[]` | both | The **task → KR edge**. A task listed here resolves to that KR with no inference. |
| `objectives[].krs[].target` / `current` | frontend | Progress. **Numbers only** — a KR whose target is "≤ 15% drawdown" carries no `target`, because rendering a ceiling as completion is worse than rendering nothing. Omit rather than coerce. **`current` is an author's assertion and is absent until one is made** — it is not defaulted to `0`, because most KRs here drive a count down and a zero would read as met on day one. Perry reports an absent one as `unasserted`. |
| `objectives[].krs[].metric` | both | The metric as prose, always safe to show. |
| `unlinked[]` | both | Work that serves no KR. **Declared, never inferred** — set arithmetic over the board would report the whole un-triaged backlog as drift the day this file is created. |
| `agents[]` | frontend | Who is carrying which tasks. |
| `projects[]` | Perry | The attribution registry: stable Project ID ↔ KR ↔ former names. This is what stops a drifted name from being fuzzy-matched into the wrong KR. |

## Rules (do not violate)

- A Project **serves** exactly one KR. If it genuinely serves two, split it into two Projects.
- A project's `objective` must agree with its `serves` KR id (`P{{NNN}}-O1-KR2` → `O1`).
- Add an **alias** only after the user confirms two names are the same Project.
- A KR may legitimately carry zero tasks — that is a completeness signal worth showing, not an error.
- Work seen in execution that no Project claims goes in `unlinked[]`, and is resolved by
  **asking the user**. Never guess. See `$PERRY_HOME/reference/okr-linkage.md`.

Validate after every write: `"$PERRY_HOME/bin/perry-lint" --root .`
