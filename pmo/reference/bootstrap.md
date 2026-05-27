# PMO bootstrap procedure

Loaded only when `/pmo` is invoked in a project that has no `BOARD.md` at the project root and the user accepts the bootstrap prompt. One-time per project.

## Trigger

`pmo/SKILL.md`'s standup ritual detects missing state files at step 2 ("Read live state"). If `BOARD.md` is absent, the agent asks:

> "No PMO state in `<project>`. Bootstrap it now? (yes/no)"

If the user declines, stop. If the user accepts, follow this procedure.

## Procedure

1. **Detect project metadata** — folder name, README, any roadmap-looking markdown, git repo URL. These populate template placeholders.

2. **Create state files at the project root**:
   - `BOARD.md` (from `state/BOARD_TEMPLATE.md`, empty tables)
   - `PROJECT_STATE.md` (from template)
   - `DECISIONS.md` (from `state/DECISIONS_TEMPLATE.md` — index only)
   - `decisions/ADR-001-pmo-bootstrap.md` from `state/ADR_TEMPLATE.md` (Type: Process, Status: active, records the bootstrap event). DECISIONS.md index gets the matching ADR-001 row added.
   - Empty directories: `journal/<current-YYYY-MM>/`, `evidence/<current-YYYY-MM>/`, `weekly/`, `handoff/`, `design/`, `inputs/`, `knowledge/`, `decisions/`
   - `knowledge/INDEX.md` from `state/knowledge_INDEX_TEMPLATE.md` (empty catalog)

3. **Do NOT eagerly create**:
   - `ARCHITECTURE.md` / `architecture/`
   - `runbook/`
   - `incidents/`

   These four trees are lazy-created on first use:
   - `ARCHITECTURE.md` → first `/pmo architecture init` or first task spec with `Touches architecture:`
   - `runbook/` → first task spec with `Deployed: yes`
   - `incidents/` → first `/pmo incident <slug>`

   **Exception**: if `.perry/hook.md` declares an `## Architecture profile` or `## Operational profile` block, those drive eager creation. See `reference/architecture.md` and `reference/runbooks.md`.

4. **Append `perry-views/` to `.gitignore`** — tier 3 HTML output lives there and is disposable, never tracked. If `.gitignore` already exists, append the line. If missing, create it with `perry-views/` (plus any other entries the project hook declares).

5. **Populate detected fields** (project name, today's date, ISO week, current YYYY-MM) into the new files. Templates use `{{placeholder}}` syntax — replace each.

6. **Write the first journal entry**: `journal/<YYYY-MM>/<today>.md` with a `## Notes` section: "PMO bootstrapped".

7. **Run the standup**. Bootstrap is now complete; the rest of this session proceeds as a normal PMO interaction.

## Post-bootstrap

Subsequent `/pmo` invocations will find `BOARD.md` present and skip the bootstrap prompt entirely. The state files grow organically from there — see `reference/state-files.md` for the full inventory and size caps.

Top-level `/perry` setup (if not yet run) confirms two project-wide preferences and writes `.perry/config.md` (document language, single vs split repo layout). Bootstrap doesn't write `.perry/config.md` directly — that's the top-level skill's job; PMO reads the file at every standup.
