# Phase #{{NNN}} — O→KR→Project linkage registry

> **Owner**: `okr` skill (only writer — this file lives under `phase/`). PMO reads it for roll-up + task→KR resolution; PMO never writes it.
> **Tier**: 2 (agent-state, no hard line cap). Holds one row per Project so name drift and large O→KR→Project fan-out never touch the phase file's 300-line tier-1 cap.
> **Purpose**: stable-ID source of truth for which KR each Project serves. Progress reports are resolved to a Project **by ID or registered alias, never by fuzzy name**. See `$PERRY_HOME/reference/okr-linkage.md`.

## Rules (do not violate)

- A Project **Serves** exactly one KR. If it genuinely serves two, split it into two Projects.
- `Objective` must agree with `Serves KR`'s Objective (`P-O1.2` → `O1`).
- Add an **Alias** only after the user confirms two names are the same Project.
- A Project/Task seen in execution that no row claims → add a row with status `unlinked`; resolve via the user, then set its real `Serves KR`.

## Registry

| Project ID | Serves KR | Objective | Current name | Aliases (former / other names; `;`-separated) | Status |
|------------|-----------|-----------|--------------|------------------------------------------------|--------|
| {{PROJ-001}} | {{P-O1.1}} | {{O1}} | {{project name}} | {{— or alias; alias}} | active |
| {{PROJ-002}} | {{P-O1.2}} | {{O1}} | {{project name}} | {{—}} | active |
| {{PROJ-003}} | {{P-O2.1}} | {{O2}} | {{project name}} | {{—}} | active |

<!--
Status values: active | done | dropped | unlinked
'unlinked' = seen in execution, no confirmed KR yet — a User-Input-Queue item.
Never leave a rolled-up progress number depending on an 'unlinked' row.
-->
