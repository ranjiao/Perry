# PMO bootstrap procedure

Loaded only when `/pmo` is invoked in a project that has no `BOARD.md` at the project root and the user accepts the bootstrap prompt. One-time per project.

## Trigger

`work/SKILL.md`'s standup ritual detects missing state files at step 2 ("Read live state"). If `BOARD.md` is absent, the agent asks:

> "No PMO state in `<project>`. Bootstrap it now? (yes/no)"

If the user declines, stop. If the user accepts, follow this procedure.

## Procedure

1. **Detect project metadata** — folder name, README, any roadmap-looking markdown, git repo URL. These populate template placeholders.

2. **Create state files at the project root**:
   - `BOARD.md` (from `state/BOARD_TEMPLATE.md`, empty tables)
   - `PROJECT_STATE.md` (from template)
   - **not** `DECISIONS.md` or `decisions/` — those belong to the `decide` lane (`$PERRY_HOME/SKILL.md § The hand-off contract`). `decide`'s own bootstrap creates them, including the ADR that records the bootstrap event. Two lanes writing one pair of files was the state this contract exists to end.
   - Empty directories: `journal/<current-YYYY-MM>/`, `evidence/<current-YYYY-MM>/`, `weekly/`, `handoff/`, `inputs/`, `knowledge/` — **not** `decisions/` and **not** `design/`, for the reason in the bullet above: both belong to `decide`, and `decide`'s own bootstrap creates them. This list used to contain both, three lines under the sentence forbidding one of them.
   - `knowledge/INDEX.md` from `state/knowledge_INDEX_TEMPLATE.md` (empty catalog)
   - **`.perry/hook.md` from `state/hook_TEMPLATE.md`** — do NOT skip this, and do NOT write it empty. Its `## High-stakes operations` list is the only thing `/pmo dispatch`'s safety re-validation and `/pmo autopilot`'s safety scan match specs against; with no list, both gates have nothing to catch and autopilot refuses to run. The template ships a conservative default list (prod deploys, credentials, infra, money, destructive data ops, outbound messages, history rewrites).

     After writing it, **show the user the default list and ask them to confirm or amend it** — one `AskUserQuestion` (header `"High-stakes"`, options: `Keep the defaults (Recommended) | Add project-specific entries | Review the list with me`). This is the one bootstrap step the user should actually look at; everything else is scaffolding.

3. **Do NOT eagerly create**:
   - `ARCHITECTURE.md` / `architecture/`
   - `runbook/`
   - `incidents/`

   These four trees are lazy-created on first use:
   - `ARCHITECTURE.md` → first `/pmo architecture init` or first task spec with `Touches architecture:`
   - `runbook/` → first task spec with `Deployed: yes`
   - `incidents/` → first `/pmo incident <slug>`

   **Exception**: if `.perry/hook.md` declares an `## Architecture profile` or `## Operational profile` block, those drive eager creation. See `$PERRY_HOME/packs/software-ops/architecture.md` and `$PERRY_HOME/packs/software-ops/runbooks.md`.

4. **Check `.gitignore`** — add any entries the project hook declares. Perry itself writes nothing that needs ignoring; the consumption layer (aiMark, or `bin/perry-viewer`) reads the tracked files directly and generates nothing into the project.

5. **Populate detected fields** (project name, today's date, ISO week, current YYYY-MM) into the new files. Templates use `{{placeholder}}` syntax — replace each.

6. **Write the first journal entry**: `journal/<YYYY-MM>/<today>.md` with a `## Notes` section: "PMO bootstrapped".

7. **Run the standup**. Bootstrap is now complete; the rest of this session proceeds as a normal PMO interaction.

## Post-bootstrap

Subsequent `/pmo` invocations will find `BOARD.md` present and skip the bootstrap prompt entirely. The state files grow organically from there — see `reference/state-files.md` for the full inventory and size caps.

Top-level `/perry` setup (if not yet run) confirms two project-wide preferences and writes `.perry/config.md` (document language, single vs split repo layout). Bootstrap doesn't write `.perry/config.md` directly — that's the top-level skill's job; PMO reads the file at every standup.
