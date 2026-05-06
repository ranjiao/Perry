# PMO subcommands — full reference

The standup ritual + dispatch + delegate live in SKILL.md / `dispatch.md` / `delegate.md`. Everything else is here.

## Planning

### `plan-week`
Generate this ISO week's plan. Reads `monthly/<current-YYYY-MM>.md` (if OKR present) and `BOARD.md` to see what's already on the board. Picks 3–5 highest-leverage open tasks for the week, marks them P0 (or proposes new P0 rows), confirms with user, updates `BOARD.md`, and writes the day's plan entry to `journal/<YYYY-MM>/<today>.md` under `## Notes`. Drafts the week's row in `weekly/<YYYY-WW>.md`.

### `triage`
Walk `BOARD.md` top-to-bottom. For each open row:
- Stale? (P0 idle ≥3d, P1 idle ≥7d, P2 idle ≥14d) → flag
- Same dependency cited in ≥2 rows? → structural blocker
- `done` claim without evidence file in `evidence/<YYYY-MM>/` → revert to `review`
- Owner is an agent but no recent delegation prompt in chat? → flag
- Row inflated (long inline notes leaking into the board) → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only Status + Next action + Evidence path on the board.

Print the triage table. **For each row that needs a decision**, use `AskUserQuestion` (header = the TASK-ID, options = `Apply suggestion (Recommended) | Edit | Skip`). Batch up to 4 rows per call. Update `BOARD.md`, write a `## Status changes` block in today's journal entry summarizing what moved.

If `BOARD.md` is over the 200-line cap, triage MUST propose specific cuts before exiting.

## Cadence (recurring; never consume P0 slots)

### `status` (a.k.a. `friday-review`)
This week's PMO status report using the format in `reporting-format.md`. Reads `BOARD.md` + this week's journal entries. Save to `weekly/<YYYY-WW>.md`.

### `monday-plan`
Run at start of week. Reads `BOARD.md` + last week's `weekly/<YYYY-WW>.md` if any. Output: priorities, P0 set, blockers needing user input, scope cuts. Append to current week's `weekly/` file AND write a `## Notes` entry in today's journal.

### `midweek-check`
Mid-week pulse. Reads `BOARD.md` + journal entries since Monday. Output: P0 movement check, blocker escalations, cost-ceiling progress, tests/verification reminders. Write to today's journal.

### `mid-month-review`
Reads `BOARD.md` + ALL journal entries for the current month (one of the few legit cases for full-month reading). Mark each Objective `on_track | at_risk | off_track` based on KR progress. Apply any **Mid-Month Scope Reduction Rule** declared in `monthly/<YYYY-MM>.md`. Recommend scope cuts. Save to `evidence/<YYYY-MM>/midmonth-review.md`.

### `end-month-retro`
At month-end. Reads `BOARD.md` + ALL journal entries for the month + `evidence/<YYYY-MM>/`. For each KR: mark `achieved | partial | missed | dropped`, link evidence file. Capture lessons. Identify carry-over candidates. Save to `evidence/<YYYY-MM>/retro.md`. This is OKR's input for `plan-month` of the next month.

## Decisions & risk

### `decide <topic>`
ADR-style. Walk Context → Options → Chosen → Consequences. Append to `DECISIONS.md` (`state/DECISIONS_TEMPLATE.md`). Tag with `Type:` (e.g., `Process`, `Architecture`, `Trading`).

### `risk`
Print and triage risks in `PROJECT_STATE.md ## Risks`. For each: still valid? severity changed? mitigation in place? owner? Update accordingly.

### `nudge`
For every User Input Queue item idle ≥5 days, surface a one-line reminder in chat with: USER-id, what's needed, what it blocks, days idle, original ask context.

## Task lifecycle

### `add-task` (interactive)
After OKR `plan-week` (or any other source) proposes a task and the user approves, PMO does THREE things — the third is conditional on priority.

1. **Add a row to `BOARD.md`** — terse: `ID | Title | Owner | Status | Next action | Evidence path`.
2. **Append the full definition** to `journal/<YYYY-MM>/<today>.md` under `## New tasks added`, including full schema (Owner, Priority, Deliverable, Verification, Dependencies, Out of scope, KR linkage). Journal entry is the canonical historical record.
3. **For P0 and P1 tasks**, ALSO write `evidence/<YYYY-MM>/<TASK-ID>-spec.md` containing the same schema PLUS the dispatch-routing fields below. BOARD's Evidence column points at this spec file. P2 / backlog / watch may rely on the journal entry alone — promote a P2 to P1 → write the spec at promotion time.

   **Required header fields in every spec file** (used by `dispatch`):
   ```
   > Dispatch mode: auto | manual               # default 'manual'; 'auto' is explicit opt-in
   > Executor: claude-subagent | codex | manual # only consulted when Dispatch mode = auto
   > Estimated cycle: small | medium | large    # informs sync vs async + cycle-time tracking
   > Subjective verification: <list, or '(none)'>
   ```

   **Choosing executor (spec writer responsibility)**:
   - `claude-subagent`: small task, needs MCP tools the parent session has, needs codebase familiarity.
   - `codex`: medium/large self-contained, no MCP dependency, save Claude Code quota.
   - `manual`: high-stakes per project hook (live trading, broker creds, .env, paid sources, cost ceiling raise) OR subjective decision-making (research candidate selection, design choices).

   Commit to the choice with one inline reason: `> Executor: codex (high confidence — pure analytics task, no MCP needed)`.

The spec uses the same template as the journal `## New tasks added` block; not duplication, two surfaces with different access patterns:

| File | Purpose | Lifetime |
|---|---|---|
| `journal/<YYYY-MM>/<creation-day>.md` | Historical "this was created here" record | Frozen after the day ends |
| `evidence/<YYYY-MM>/<TASK-ID>-spec.md` | Live schema for dispatch / re-dispatch / audit | Mutable as scope refines (subsequent edits must add `## Changes` log inside the file) |
| `evidence/<YYYY-MM>/<TASK-ID>-*.md` (other names) | Deliverable artifacts: reports, drill records, checklists | Per-deliverable |

When the task closes, leave the spec file in place — it's the canonical scope record.

Slug IDs are never reused or recycled across months.

If the task needs a working artifact from day one (checklist, design ladder, subtasks), the working artifact lives at `evidence/<YYYY-MM>/<TASK-ID>-<slug>.md` (separate file from the spec).

### `close-task <id>`
Reject if no evidence path provided. If the task spec lists `Subjective verification` items, **use `AskUserQuestion`** (header = TASK-ID, options = `Verified — close (Recommended) | Partial — keep as review | Reject — needs rework`) before flipping status. On `Verified — close`:
1. **Remove the row from `BOARD.md`**.
2. Append a `## Status changes` line to `journal/<YYYY-MM>/<today>.md`: `[ID] <prev-status> → done · <one-line> · evidence: <path>`.
3. If the task was a Must-Have item in `monthly/<YYYY-MM>.md`, tick it there too.
4. The original task definition (creation-day journal entry) stays untouched — that's the historical record.

To find a closed task later: `grep "TASK-007" journal/` returns its creation entry, all status changes, and its close entry.

### `drop-task <id> <reason>`
Symmetric to `close-task`:
1. Remove the row from `BOARD.md`.
2. Append a `## Status changes` line to today's journal: `[ID] <prev-status> → dropped · reason: <reason>`.
3. The original task definition in its creation-day journal entry stays untouched.

## Cross-session

### `coordinate`
Pull a snapshot of work from other Claude sessions/terminals tagged for this project (`mcp__session_info__list_sessions` if available; otherwise ask user to paste summaries). Append a consolidated update to `PROJECT_STATE.md` under `## Recent cross-session work`. Distribute follow-ups by appending new tasks.

### `handoff`
Generate the **Day-N Status doc** — a single self-contained document a future PMO session can read instead of re-walking the conversation. Save to `handoff/<YYYY-MM-DD>.md` from `state/handoff_TEMPLATE.md`. Always include:
1. Must-Have progress count (e.g., "4/5 done")
2. Today's deliverables (code/decisions/finance)
3. User Input Queue with recommendations
4. Next ISO week's day-by-day milestones
5. Open risks with mitigations
6. BOARD snapshot — copy the current `BOARD.md` table contents (or summarize if too long)
7. "Read these N files first when you resume" pointer (typically: `handoff/<this-doc>.md`, `BOARD.md`, last 1–2 journal entries, `PROJECT_STATE.md`)

The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc is the bridge.

## Monthly transition

### `rollover`
With the BOARD/journal split, rollover is nearly trivial — `BOARD.md` is already current, the previous month's journal entries already exist as the historical record. Steps:

1. Confirm `evidence/<previous-YYYY-MM>/retro.md` exists; if not, prompt for `end-month-retro` first.
2. **Create `journal/<new-YYYY-MM>/`**. The first journal entry will be created the next time `add-task` / `triage` / `close-task` writes one.
3. **Create `evidence/<new-YYYY-MM>/`**.
4. **`BOARD.md` is left alone.** Open carry-forward tasks already live there; no "carry forward" step is needed because the board never had a month boundary in the first place. If a row's task ID convention encodes a month (e.g., `PAPER-007` from 2026-05), leave the ID untouched — it's the canonical handle.
5. For each unresolved task on BOARD: **use `AskUserQuestion`** (header = TASK-ID, options = `Carry forward (Recommended) | Drop with reason`). Batch up to 4 per call. For "Drop with reason", follow up with a free-text prompt for the reason, then run `drop-task` which writes the close to `journal/<old-YYYY-MM>/<last-day>.md` AND removes from BOARD.
6. Hand off to OKR: print "OKR `plan-month <new-YYYY-MM>` is needed". Do **not** create the new monthly OKR yourself — that's OKR's lane.
7. Append a `## Notes` entry to the first day of the new month's journal: "rollover from <prev-YYYY-MM>; <n> rows carried; see evidence/<prev-YYYY-MM>/retro.md".

`git log -- journal/` shows the full history per day; `git log -- BOARD.md` shows the live board's evolution.
