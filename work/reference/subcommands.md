# PMO subcommands — full reference

The standup ritual + dispatch + delegate live in SKILL.md / `dispatch.md` / `delegate.md`. Everything else is here.

## Planning

See `planning.md § Planning`.

### `plan-week`

See `planning.md § plan-week`.

### `triage`

See `planning.md § triage`.

## Cadence (recurring; never consume P0 slots)

### `status` (a.k.a. `friday-review`)
This week's PMO status report using the format in `reporting-format.md`. Reads `perry-task list --json` + this week's journal entries. Save to `weekly/<YYYY-WW>.md`.

### `monday-plan`
Run at start of week. Reads `perry-task list --json` + last week's `weekly/<YYYY-WW>.md` if any. Output: priorities, P0 set, blockers needing user input, scope cuts. Append to current week's `weekly/` file AND write a `## Notes` entry in today's journal.

### `midweek-check`
Mid-week pulse. Reads `perry-task list --json` + journal entries since Monday. Output: P0 movement check, blocker escalations, cost-ceiling progress, tests/verification reminders. Write to today's journal.

### `mid-phase-review`
Triggered manually (or surfaced by the standup when ≥40–60% of phase day budget elapsed). Reads `perry-task list --json` + journal entries since the current phase started (resolve start date from the phase file header). Mark each Objective `on_track | at_risk | off_track` based on KR progress. Apply any **Phase Scope Reduction Rule** declared in `phase/<NNN>-<slug>.md`. Recommend scope cuts. Save to `evidence/<YYYY-MM>/midphase-review-<NNN>-<slug>.md`.

**Inline health-check** (added to mid-phase-review): run `/pmo health-check` (see `reference/health-check.md`) and fold its findings — audit violations, runbook gaps, incident patterns — into the mid-phase-review report. The detailed report lives at `evidence/<YYYY-MM>/health-check-<YYYY-MM-DD>.md`; the mid-phase-review summarises the top decision items inline.

**Digest archive review** (added to mid-phase-review): if `knowledge/` exists, scan for active digests with no reference in the task store / `journal/` / `evidence/` / `decisions/` / `phase/` for ≥ `archive_inactive_days` days (default 90; override per-project hook). For each candidate, use `AskUserQuestion` (header = digest basename, options): `Archive (Recommended) | Keep active — still relevant | Mark eternal — never propose archive | Delete entirely`. On Archive: flip `Status: archived` in the digest header + record `Archived: <date> (reason: <user input>)`. On Eternal: flip `Status: eternal`. On Delete: `git rm` source + digest. Update `knowledge/INDEX.md`. See `work/reference/digests.md § Archive lifecycle` for full detail. (Note: `health-check` already includes the digest stale scan; running it here is the same scan, surfaced for the user to act on.)

### `end-phase-retro`
Triggered when OKR `score-phase` is about to run (or explicitly by the user). Reads `perry-task list --all --json` + all journal entries since the current phase started + `evidence/<YYYY-MM>/` for the calendar months the phase spanned. For each KR: mark `achieved | partial | missed | dropped`, link evidence file. Capture lessons. Identify carry-over candidates. Save to `evidence/<YYYY-MM>/retro.md` (using the calendar month at scoring time). This is OKR's input for `plan-phase` of the next phase.

**Inline health-check** (added to end-phase-retro): run `/pmo health-check` (see `reference/health-check.md`). The retro additionally folds in:
- **Incident feedback-loop ratio**: of all incidents resolved during this phase, how many produced derived changes (architecture / runbook / digest)? A low ratio + recurring components = a structural problem worth a KR in next phase's OKR.
- **Audit drift trend**: how many `ARCHITECTURE.md`-vs-code drift items from the last audit are still open at phase-end? Carry them into next phase's OKR as either resolution KRs, deferral ADRs, doc edits, or `Not Doing` lines (see `goals/reference/phases.md § plan-phase <slug>`).
- **Runbook coverage**: count of deployed components without runbook, vs same count at phase start. Drift in this number is a red flag.

These three numbers go into `evidence/<YYYY-MM>/retro.md` § "Health metrics" section so OKR's `plan-phase` for next phase can read them directly.

**Knowledge promotion** (DESIGN-006 § 5.4; procedure in `reference/promotion.md`): **at most one question for the whole retro**, and only for a lesson the retro itself already identified as recurring across two or more tasks. Run `"$PERRY_HOME/bin/perry-knowledge" propose --source "evidence/<YYYY-MM>/retro.md" --root . --json` first — `fires: false` means ask nothing — and write it with `perry-knowledge promote`, never by hand. Batching is the named risk (DESIGN-006 § 7): a retro that offers six cards produces six rubber stamps. If the phase produced several durable claims, promote one and note the rest as candidates in the retro; the next `close-task` will offer them where they belong.

**Digest archive review** (same procedure as `mid-phase-review`; second pass per phase): re-scan archive candidates and process via `AskUserQuestion`. Phase-end is the safer gate — anything still un-referenced after a full phase is more likely truly inactive. Also at phase-end, **rebuild `knowledge/INDEX.md` fully** (not just incrementally): re-grep all references for `Last referenced` dates, recompute counts, alphabetize within topics. Cheap operation (~2-3 sec for 30 digests).

## Decisions & risk

See `decisions-risk.md § Decisions & risk`.

### ~~`decide <topic>`~~ — moved to the `decide` lane

See `decisions-risk.md § ~~decide <topic>~~ — moved to the decide lane`.

### `risk`

See `decisions-risk.md § risk`.

### `nudge`

See `decisions-risk.md § nudge`.

## Task lifecycle

### `add-task` (interactive)

See `add-task.md § add-task (interactive)`.

`close-task <id>` and `drop-task <id> <reason>`: see `task-close.md`.

## Cross-session

### `coordinate`
Pull a snapshot of work from other Claude sessions/terminals tagged for this project (use a session-listing MCP tool if the project hook declares one; otherwise ask the user to paste summaries). Append a consolidated update to `PROJECT_STATE.md` under `## Recent cross-session work`. Distribute follow-ups by appending new tasks.

When an incoming update references a Project by **name** (progress reports usually do, and the name may have drifted), resolve it to a KR **by ID through `linkage.jsonl`** before rolling any progress up — explicit `kr:` → Project ID → registered alias (`$PERRY_HOME/reference/okr-linkage.md`). Ambiguous or unmatched → ask the user which Project/KR it is; never attribute by fuzzy name. Hand the answer to `okr` (`/perry goals link …`) rather than editing `phase/`. Unresolvable while the user is away → `/perry goals link --unlinked <id>` rather than pinning it to a guessed KR.

### `handoff`
Generate the **Day-N Status doc** — a single self-contained document a future PMO session can read instead of re-walking the conversation. Save to `handoff/<YYYY-MM-DD>.md` from `state/handoff_TEMPLATE.md`. Always include:
1. Must-Have progress count (e.g., "4/5 done")
2. Today's deliverables (code/decisions/finance)
3. User Input Queue with recommendations
4. Next ISO week's day-by-day milestones
5. Open risks with mitigations
6. BOARD snapshot — paste what `perry-tasks board` prints (or summarize if too long)
7. "Read these N files first when you resume" pointer (typically: `handoff/<this-doc>.md`, `perry-tasks board`, last 1–2 journal entries, `PROJECT_STATE.md`)

The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc is the bridge.

#### Budget boundary

See `budget-boundary.md § Budget boundary`: the checkpoint that decides whether a handoff is needed, and what it must carry.

## Phase transition

### `rollover`
Runs when a phase has been scored via `okr score-phase` and the user is ready to start the next phase. With the BOARD/journal split, rollover is mostly informational — the task store is already current; previous phase's journal entries are intact. Steps:

1. Confirm `evidence/<YYYY-MM>/retro.md` exists — **this lane's own file, written by `end-phase-retro`**, not by `okr score-phase`, which hands over a summary and does not write `evidence/` (`goals/reference/phases.md` step 5). If it is absent, prompt to run `end-phase-retro`; prompting for `score-phase` cannot produce it.
2. **Calendar-month directories** — `journal/<YYYY-MM>/` and `evidence/<YYYY-MM>/` are calendar-bound; create new month dirs only if the calendar month rolled (most rollovers do NOT need this — phases can span multiple calendar months OR fit inside one).
3. **The task store is left alone.** Open carry-forward tasks already live there; no "carry forward" step is needed because the board never had a phase boundary in the first place. If a row's task ID encodes a date or phase prefix, leave it untouched — it's the canonical handle.
4. For each unresolved task on BOARD: **use `AskUserQuestion`** (header = TASK-ID, options = `Carry forward (Recommended) | Drop with reason`). Batch up to 4 per call. For "Drop with reason", follow up with a free-text prompt for the reason, then run `perry-task drop <ID> --actor <actor> --reason "<reason>"` — the reason the user just gave, verbatim, not a paraphrase.
5. Hand off to OKR: print "OKR `plan-phase <new-slug>` is needed — pick the next phase's slug." Do **not** create the new phase file yourself — that's OKR's lane.
6. Append a `## Notes` entry to today's journal: "rollover from phase #<old-NNN>-<old-slug>; <n> rows carried; see evidence/<YYYY-MM>/retro.md".

`git log -- journal/` shows the full history per day; `git log -- tasks.jsonl` shows the task store's evolution; `git log -- phase/` shows phase progression.

## Completion routing

After completed writes from `plan-week`, `triage`, `status`, `friday-review`, `monday-plan`, `midweek-check`, `mid-phase-review`, `end-phase-retro`, `risk`, `add-task`, `coordinate`, `handoff`, `rollover`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: work plan-week --> <!-- next-close: work triage --> <!-- next-close: work status --> <!-- next-close: work friday-review --> <!-- next-close: work monday-plan --> <!-- next-close: work midweek-check --> <!-- next-close: work mid-phase-review --> <!-- next-close: work end-phase-retro --> <!-- next-close: work risk --> <!-- next-close: work add-task --> <!-- next-close: work coordinate --> <!-- next-close: work handoff --> <!-- next-close: work rollover -->
