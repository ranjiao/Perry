# `okr plan-week` — the PMO hand-off

Loaded when `/okr plan-week` fires. The most-used OKR subcommand, and the one place where OKR's output becomes PMO's input.

## Procedure

1. Read `phase/<current-NNN>-<slug>.md` (via `phase/CURRENT`). Identify the current ISO week's row in the week-by-week breakdown.

2. Translate each commitment into 1–2 concrete tasks. **Resolve each task's KR by ID through `phase/<NNN>-linkage.md`, never by guessing from the Project name** (resolution order + the ask in `$PERRY_HOME/reference/okr-linkage.md`). If the phase-file Project name differs from what the user says now, confirm they're the same Project and append the alias to the registry before tagging. If the KR can't be resolved to exactly one → `AskUserQuestion` (candidate KRs); never fuzzy-match.

   Each task gets:
   - Short slug id (e.g., `migrate_user_table_v2`)
   - Title
   - Linked Objective/KR (e.g., `kr:P-O1.2`) — the resolved ID, from the registry
   - Owner (`User`, `User + Agent`, `Coding Agent`, `Research Agent`, `Review Agent`, or `PMO Agent`)
   - Priority (`P0` if blocks a Must-Have, `P1` if advances, `P2` otherwise)
   - Deliverable + Verification (1 line each)
   - Out-of-scope notes if relevant (e.g., "do not touch production", "no access to prod credentials")

3. Print 3–5 candidate tasks in a table. Before printing, run `$PERRY_HOME/reference/input-quality.md § 4 Task` over each candidate (verification falsifiable, deliverable is an artifact, single owner, priority justified, `kr:` linked); fix or flag inline — don't hand PMO a task with "verify it works".

4. **If ≤ 4 candidates**: use `AskUserQuestion` with `multiSelect: true` (header `"Pick tasks"`) — each candidate is one option with the task title in `label` and the rationale + KR linkage in `description`. The user clicks the subset they approve.

   **If 5 candidates**: use `AskUserQuestion` (single-select, header `"Subset"`) with options `Approve all 5 | Pick subset (Recommended) | Edit before approving | Skip this week`. If "Pick subset", follow up with a free-text "which IDs to include?" prompt.

5. On approval, **hand off to PMO**: print the exact task block list. PMO `add-task` writes the BOARD row and the journal definition. OKR never writes `BOARD.md` or `journal/` directly.

6. Update the current week's row in `phase/<NNN>-<slug>.md` with the chosen TASK-IDs.

7. **Append each task id to its KR's `tasks[]`** in `phase/<NNN>-linkage.md`, and bump `updated`. This is what makes the edge *declared* rather than inferred — it is resolution step 1, ahead of any name matching. A task the user approved but whose KR is genuinely undecided goes in `unlinked[]` instead; never park it under a plausible-looking KR.

## Why the registry, not the name

A Project's human-readable name drifts; its ID doesn't. `"$PERRY_HOME/bin/perry-state" --section attribution` reports which open tasks currently resolve to exactly one KR and which are `unlinked`. Anything `unlinked` is a question for the user, never a guess — see `$PERRY_HOME/reference/okr-linkage.md § The one rule`.

If the user confirms a new name is the same Project, append it to that project's `aliases[]` (OKR owns `phase/`; PMO hands aliases over rather than writing them). `bin/perry-lint` refuses two projects claiming the same name or alias, and refuses a task listed under two KRs — those ambiguities are precisely what the graph exists to prevent.
