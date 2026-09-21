# PMO bootstrap procedure

Loaded only when `/pmo` is invoked in a project `perry-state --json` reports `installed: false` for and the user accepts the bootstrap prompt. One-time per project.

## Trigger

`work/SKILL.md`'s standup ritual detects missing state files at step 2 ("Read live state"). If `perry-state --json` reports `installed: false`, the agent asks:

> "No PMO state in `<project>`. Bootstrap it now? (yes/no)"

If the user declines, stop. If the user accepts, follow this procedure.

## Procedure

0. **Write `.perry/config.jsonl` first, when it does not exist.** Before any markdown: `PROJECT_STATE.md` and the other markdown alone do not make a project installed (`$PERRY_HOME/schema/README.md § installed`), so a bootstrap that wrote only those would be offered again on every session. If top-level `/perry` first-time setup has not run, ask its preference questions (`$PERRY_HOME/reference/first-run.md § The procedure` step 3) and write the answers with the tool:

   ```
   "$PERRY_HOME/bin/perry-config" set --root . "Document language" "<language>"
   "$PERRY_HOME/bin/perry-config" set --root . "Chat language" "follow user"
   "$PERRY_HOME/bin/perry-config" set --root . "Repo layout" "<single or split>"
   "$PERRY_HOME/bin/perry-config" set --root . "State root" "<state root>"
   ```

   When the store already exists, this step writes nothing.

1. **Detect project metadata** — folder name, README, any roadmap-looking markdown, git repo URL. These populate template placeholders.

2. **Create state files under the state root** — the `State root` step 0 wrote (`perry` is what setup writes); only `.perry/` sits at the project root:
   - **no `BOARD.md`.** The board is what `"$PERRY_HOME/bin/perry-tasks" board` prints from the stores (TASK-237 3c), and the first `perry-task` write creates the store it needs. This step used to write the board at the project root, beside `.perry/` and outside the state root step 0 had just declared.
   - `PROJECT_STATE.md` (from template)
   - **not** `decisions/` — that belongs to the `decide` lane (`$PERRY_HOME/SKILL.md § The hand-off contract`). `decide`'s own bootstrap creates it, including the ADR that records the bootstrap event. Two lanes writing one record was the state this contract exists to end.
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

   **Exception**: an approved `.perry/hook.md` `## Architecture profile` or `## Operational profile` can independently require eager creation. Apply `$PERRY_HOME/reference/config.md § Pack capabilities and controls`: disabled pack defaults create nothing, but an explicit project requirement remains binding. See `$PERRY_HOME/packs/software-ops/architecture.md` and `$PERRY_HOME/packs/software-ops/runbooks.md` only when applicable.

4. **Check `.gitignore`** — add any entries the project hook declares. Perry itself writes nothing into the project that needs ignoring: everything it writes is meant to be committed, and its one piece of pure runtime state (`perry-task`'s write lock) lives in the temp dir, keyed by a hash of the state root, precisely so no project has to maintain an ignore rule for it. The consumption layer (aiMark) reads the tracked files directly and generates nothing into the project.

5. **Populate detected fields** (project name, today's date, ISO week, current YYYY-MM) into the new files. Templates use `{{placeholder}}` syntax — replace each.

6. **Write the first journal entry**: `journal/<YYYY-MM>/<today>.md` with a `## Notes` section: "PMO bootstrapped".

7. **Run the standup**. Bootstrap is now complete; the rest of this session proceeds as a normal PMO interaction.

## Post-bootstrap

Subsequent `/pmo` invocations will find `perry-state --json` reporting `installed: true` — a `.perry/config.jsonl` alone is enough — and skip the bootstrap prompt entirely. The state files grow organically from there — see `reference/state-files.md` for the full inventory and size caps.

Top-level `/perry` setup confirms the project-wide preferences and writes them into `.perry/config.jsonl` with `perry-config set`, as its first write. When this bootstrap runs without it, step 0 writes the store the same way before anything else, because a project whose only files are markdown is not installed (`schema/README.md § installed`) and would be offered this bootstrap again on every session. PMO reads the store at every standup.

## Completion routing

After completed writes from `bootstrap`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work bootstrap -->
