# PMO subcommands — full reference

The standup ritual + dispatch + delegate live in SKILL.md / `dispatch.md` / `delegate.md`. Everything else is here.

## Planning

### `plan-week`
Generate this ISO week's plan. Reads `phase/<current-NNN>-<slug>.md` (resolve via `phase/CURRENT`; if OKR present) and `BOARD.md` to see what's already on the board. Picks 3–5 highest-leverage open tasks for the week, marks them P0 (or proposes new P0 rows), confirms with user, updates `BOARD.md`, and writes the day's plan entry to `journal/<YYYY-MM>/<today>.md` under `## Notes`. Drafts the week's row in `weekly/<YYYY-WW>.md`.

### `triage`

**Step 0 — drain `BOARD.md § Intake`, before anything else.** Applies to every queue-mode track. If the track exists and the section does not, **create it** rather than skipping — a self-skipping step is indistinguishable from a step that has nothing to do. Walk it top to bottom; every row gets exactly one outcome, and none may be left as-is:

- **Routed** to a track → `"$PERRY_HOME/bin/perry-task" route <n> --track <track> [--priority P1]`, where `<n>` is the intake row's position. The tool carries `Arrived` onto the new row, sets `Stage` to the track's first post-intake stage, and writes the destination back into the intake row's `Outcome` so the request's record is complete. Carrying `Arrived` is not bookkeeping: `today − Arrived` is the number every SLA check measures, so a routing that drops it makes the mode's own breach check uncomputable and silently exempts the row from the only clock governing it (`modes/queue.md`). It was dropped, by this procedure, until the tool did it structurally.
- **Dropped**, with the reason in the intake row's `Outcome` cell. "We are not doing this" is a real answer, and an undropped request is one that gets re-asked.
- **Deferred**, with a **named condition** in `Outcome` — never a bare "later".

A row still sitting in intake for **more than 14 days** is reported by age. Not "after two triages": `Arrived` is recorded and nothing counts triages, so elapsed time is computable and a triage count is not. And if intake is pushing `BOARD.md` toward the 200-line cap, **say so as a finding** — a project taking on more than it discharges is exactly what that pressure means. Do not raise the cap and do not move the section somewhere it can grow unnoticed; if it recurs, that is a reason to revisit DESIGN-003 § 4 decision 3, not to relax it quietly.

Then walk `BOARD.md` top-to-bottom. For each open row:
- Stale? (P0 idle ≥3d, P1 idle ≥7d, P2 idle ≥14d) → flag
- Same dependency cited in ≥2 rows? → structural blocker
- `done` claim without evidence file in `evidence/<YYYY-MM>/` → revert to `review`
- Owner is an agent but no recent delegation prompt in chat? → flag
- Row inflated (long inline notes leaking into the board) → propose moving detail to `evidence/<YYYY-MM>/<TASK-ID>-*.md`, leaving only Status + Next action + Evidence path on the board.
- Spec has `Deployed: yes`, status `review`, but no `Runbook:` field or runbook file missing → flag with "blocks close" annotation (see `$PERRY_HOME/packs/software-ops/runbooks.md`).
- Spec's `Touches architecture:` non-empty, status `review`, but latest dispatch evidence has no `## Architecture review` PASS → flag with "blocks close — re-dispatch or override" annotation (see `$PERRY_HOME/packs/software-ops/architecture.md`).
- Latest `architecture/audit-history/<date>.md` has open drift items older than 7 days → flag with "audit drift open" annotation; not blocking but visible.
- Open `incidents/*.md` with status `open` for ≥3 days → surface as P0 attention items even if not on BOARD (see `$PERRY_HOME/packs/software-ops/incidents.md`).
- Cadence row past its `Next due` → surface by age, exactly the way a stale User Input Queue item is. In a queue-mode track this is the highest-value question triage asks: **what recurs?** A request seen three times is not a request, it is a process nobody has written down — propose converting it to a Cadence row with a runbook, or record an explicit decline.

**Every stage move goes through the tool — this is a global invariant, not a triage rule.**

```
"$PERRY_HOME/bin/perry-task" stage <TASK-ID> --stage <name>
```

It re-stamps `Stage since` in the same write and refuses a stage outside the track's declared vocabulary. The rule applies wherever `Stage` changes, including `close-task` and `dispatch`, neither of which loads this section — which is why it is stated as an invariant rather than a step. Hand-editing the cell leaves the clock reading from whenever the row was created, and pipeline triage's first question then measures nothing. Changing a row's `Stage` sets `Stage since` to today **in the same edit**, and writes the move into today's journal `## Status changes` line alongside any `Status` change. This is the rule that makes dwell time real: `Stage` and `Status` are orthogonal by design, so a `draft → review` move produces no `Status` change and would otherwise leave no trace anywhere. A stage moved without its timestamp is a clock that reads whatever it read last.

**Per-mode ordering.** The walk above is project-mode's. A track in another mode asks its own questions first, per its mode file: `pipeline` leads with oldest-item-per-stage and stages at their WIP limit (`modes/pipeline.md`); `queue` leads with SLA breaches and queue-depth trend after the intake drain (`modes/queue.md`); `inquiry` leads with open questions against the cap, then **`perry-lint --provenance`** — a dangling source id outranks everything else in that mode's list (`modes/inquiry.md`). Read the mode file for any track you are triaging.

Print the triage table. **For each row that needs a decision**, use `AskUserQuestion` (header = the TASK-ID, options = `Apply suggestion (Recommended) | Edit | Skip`). Batch up to 4 rows per call. Update `BOARD.md`, write a `## Status changes` block in today's journal entry summarizing what moved.

If `BOARD.md` is over the 200-line cap, triage MUST propose specific cuts before exiting.

## Cadence (recurring; never consume P0 slots)

### `status` (a.k.a. `friday-review`)
This week's PMO status report using the format in `reporting-format.md`. Reads `BOARD.md` + this week's journal entries. Save to `weekly/<YYYY-WW>.md`.

### `monday-plan`
Run at start of week. Reads `BOARD.md` + last week's `weekly/<YYYY-WW>.md` if any. Output: priorities, P0 set, blockers needing user input, scope cuts. Append to current week's `weekly/` file AND write a `## Notes` entry in today's journal.

### `midweek-check`
Mid-week pulse. Reads `BOARD.md` + journal entries since Monday. Output: P0 movement check, blocker escalations, cost-ceiling progress, tests/verification reminders. Write to today's journal.

### `mid-phase-review`
Triggered manually (or surfaced by the standup when ≥40–60% of phase day budget elapsed). Reads `BOARD.md` + journal entries since the current phase started (resolve start date from the phase file header). Mark each Objective `on_track | at_risk | off_track` based on KR progress. Apply any **Phase Scope Reduction Rule** declared in `phase/<NNN>-<slug>.md`. Recommend scope cuts. Save to `evidence/<YYYY-MM>/midphase-review-<NNN>-<slug>.md`.

**Inline health-check** (added to mid-phase-review): run `/pmo health-check` (see `reference/health-check.md`) and fold its findings — audit violations, runbook gaps, incident patterns — into the mid-phase-review report. The detailed report lives at `evidence/<YYYY-MM>/health-check-<YYYY-MM-DD>.md`; the mid-phase-review summarises the top decision items inline.

**Digest archive review** (added to mid-phase-review): if `knowledge/` exists, scan for active digests with no reference in `BOARD.md` / `journal/` / `evidence/` / `DECISIONS.md` / `phase/` for ≥ `archive_inactive_days` days (default 90; override per-project hook). For each candidate, use `AskUserQuestion` (header = digest basename, options): `Archive (Recommended) | Keep active — still relevant | Mark eternal — never propose archive | Delete entirely`. On Archive: flip `Status: archived` in the digest header + record `Archived: <date> (reason: <user input>)`. On Eternal: flip `Status: eternal`. On Delete: `git rm` source + digest. Update `knowledge/INDEX.md`. See `reference/digests.md § Archive lifecycle` for full detail. (Note: `health-check` already includes the digest stale scan; running it here is the same scan, surfaced for the user to act on.)

### `end-phase-retro`
Triggered when OKR `score-phase` is about to run (or explicitly by the user). Reads `BOARD.md` + all journal entries since the current phase started + `evidence/<YYYY-MM>/` for the calendar months the phase spanned. For each KR: mark `achieved | partial | missed | dropped`, link evidence file. Capture lessons. Identify carry-over candidates. Save to `evidence/<YYYY-MM>/retro.md` (using the calendar month at scoring time). This is OKR's input for `plan-phase` of the next phase.

**Inline health-check** (added to end-phase-retro): run `/pmo health-check` (see `reference/health-check.md`). The retro additionally folds in:
- **Incident feedback-loop ratio**: of all incidents resolved during this phase, how many produced derived changes (architecture / runbook / digest)? A low ratio + recurring components = a structural problem worth a KR in next phase's OKR.
- **Audit drift trend**: how many `ARCHITECTURE.md`-vs-code drift items from the last audit are still open at phase-end? Carry them into next phase's OKR as either resolution KRs, deferral ADRs, doc edits, or `Not Doing` lines (see `goals/SKILL.md § plan-phase`).
- **Runbook coverage**: count of deployed components without runbook, vs same count at phase start. Drift in this number is a red flag.

These three numbers go into `evidence/<YYYY-MM>/retro.md` § "Health metrics" section so OKR's `plan-phase` for next phase can read them directly.

**Digest archive review** (same procedure as `mid-phase-review`; second pass per phase): re-scan archive candidates and process via `AskUserQuestion`. Phase-end is the safer gate — anything still un-referenced after a full phase is more likely truly inactive. Also at phase-end, **rebuild `knowledge/INDEX.md` fully** (not just incrementally): re-grep all references for `Last referenced` dates, recompute counts, alphabetize within topics. Cheap operation (~2-3 sec for 30 digests).

## Decisions & risk

### ~~`decide <topic>`~~ — moved to the `decide` lane

ADR recording left this lane on 2026-08-16, when the signed hand-off contract
(`$PERRY_HOME/SKILL.md § The hand-off contract`) gave `DECISIONS.md` and
`decisions/` to `decide`. It is now **`/perry decide adr <topic>`**, with the
same `--supersede` / `--expire` / `--archive` lifecycle, and the full procedure
lives at `$PERRY_HOME/decide/reference/decisions.md`.

**`work` no longer writes `DECISIONS.md` or `decisions/` at all.** If a request
lands here that would, route it — do not write and mention it afterwards. That
is the refusal case the contract names.

The old-monolithic-`DECISIONS.md` migration moved with it.

### `risk`
Print and triage risks in `PROJECT_STATE.md ## Risks`. For each: still valid? severity changed? mitigation in place? owner? Update accordingly.

### `nudge`
For every User Input Queue item idle ≥5 days, surface a one-line reminder in chat with: USER-id, what's needed, what it blocks, days idle, original ask context.

## Task lifecycle

### `add-task` (interactive)
After OKR `plan-week` (or any other source) proposes a task and the user approves, PMO does THREE things — the third is conditional on priority.

**First, an input-quality pass** (`$PERRY_HOME/reference/input-quality.md § 4 Task`): check the task's Verification is falsifiable (not "looks good"), Deliverable is an artifact (not an activity), Owner is a single value from the Owner model, Priority is justified (P0 only if it blocks a Must-Have), and a `kr:` linkage is present when the task came from `plan-week`. Surface ≤3 issues, advisory + override — fix with the user or write as-is with a one-line journal reason. Never silently rewrite. (Tasks arriving already-clean from `plan-week`, which ran the same §4 pass, usually pass with `✓ Input quality: clean`.)

**Then, the KR-attribution gate** (`$PERRY_HOME/reference/okr-linkage.md`) — hard, not advisory: resolve the task's KR by stable ID through `phase/<NNN>-linkage.md` (explicit `kr:` → Project ID → registered alias). If it resolves to exactly one KR, set `kr:` and continue. If it resolves to zero or many — a drifted/ambiguous name, or a Project no registry row claims — **do NOT fuzzy-match**: ask the user (`AskUserQuestion`, header `"KR attribution"`, options = the candidate KR IDs + text, plus "Other → new/none"). Record the chosen KR in the spec, then **hand the result to `okr`**, which is the only writer of `phase/` (`goals/reference/linkage.md`):

- resolved → `/perry goals link <TASK-ID> <KR-ID>` (appends the edge to that KR's `tasks[]`)
- a name confirmed as an existing Project → `/perry goals link --alias <PROJECT-ID> "<name>"`
- unresolved, or the user is unavailable → `/perry goals link --unlinked <TASK-ID>`, and write the BOARD row with `attribution: unlinked` so it stays out of every KR roll-up until the standup surfaces it

Print the exact command — **in its `/perry <lane> …` form**, since this string is quoted to the user and `/okr` is a withdrawn host command that `setup` deletes and that collides with `lark-okr`. Don't edit `phase/` yourself.

**Mode columns — the write path, not just the column.** A column nobody writes is not a control. For a row on a track whose mode is not `project`, `add-task` sets these in the same edit that creates the row:

| Track mode | Set at creation |
|---|---|
| `pipeline` | `Track`, `Stage` = the first stage of the track's `Stages`, `Stage since` = today, `Commitment` if the row discharges one |
| `queue` | `Track`, `Stage` = first post-intake stage, `Arrived` = the date it arrived (carried from `## Intake`, or today for a row raised directly), `Commitment` if applicable |
| `inquiry` | `Track`, `Stage` = `open`, `Stage since` = today, `Parent` = the question this was split from, or blank for a root |
| `project` | nothing extra — this is today's behavior, unchanged |

**Add the column if the board has none.** You cannot set a cell in a column with no header, and `BOARD_TEMPLATE.md` ships six columns — so the first non-`project` row on a board also adds the headers it needs, in the same edit. Same clause `close-task` already has for `Verification`, applied to the five columns that were given a home and no creator.

A pipeline- or inquiry-mode board must carry `Stage` and `Stage since`; a queue-mode board must carry `Stage` and `Arrived`. They are optional in the schema so that no pre-DESIGN-003 board is invalidated, **not** so a mode track can skip them — a track that does is missing the clock its own triage reads.

**Creating a queue-mode row also creates `BOARD.md § Intake` if it is absent**, with its three columns (`Arrived`, `Request`, `Outcome`). Intake is the organ queue mode is built on and the first thing `triage` walks; a section nothing creates means step 0 no-ops forever, and `modes/queue.md`'s warning about a track "whose intake is always empty while work is clearly happening" would describe the guaranteed default rather than a risk.

1. **Create the row with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" add --title "<title>" --owner "<owner>" \
       --priority <P0|P1|P2> [--track <track>] [--next "<next action>"] \
       [--parent <ID>] [--commitment <Id>]
   ```

   It mints the ID from board ∪ events (never reused, never accidentally
   gapped), stamps the timestamp at call time, sets `Stage` / `Stage since` /
   `Arrived` for the track's mode, **creates any column or section the mode
   needs and the board lacks**, and writes the board row, the journal line and
   the event atomically — none of the three if any would fail.

   Do not hand-write the row. Every field above was one an agent supplied and
   got wrong at least once: malformed pipes, a reused ID, a timestamp that was
   an assertion, a clock nobody wound. `perry-state` reports a hand-written row
   as `unrecorded` at the next standup — reported, not refused, because editing
   your own markdown is legitimate; but it is visible, and that visibility is
   the point.

   **Refusals are outcomes, not errors.** The tool exits 1 and writes nothing on
   a missing title, an undeclared track, or a stage outside a track's
   vocabulary. Read the message and fix the call; do not fall back to editing
   the file.

2. **Append the full definition** to `journal/<YYYY-MM>/<today>.md` under `## New tasks added`, including full schema (Owner, Priority, Deliverable, Verification, Dependencies, Out of scope, KR linkage). The tool writes the one-line status change; this block is the rich record and is still written by hand.
3. **For P0 and P1 tasks**, ALSO write `evidence/<YYYY-MM>/<TASK-ID>-spec.md` containing the same schema PLUS the dispatch-routing fields below. BOARD's Evidence column points at this spec file. P2 / backlog / watch may rely on the journal entry alone — promote a P2 to P1 → write the spec at promotion time.

   **Required header fields in every spec file** (used by `dispatch` and `close-task`):
   ```
   > Dispatch mode: auto | manual               # default 'manual'; 'auto' is explicit opt-in
   > Executor: claude-subagent | codex | manual # only consulted when Dispatch mode = auto
   > Estimated cycle: small | medium | large    # informs sync vs async + cycle-time tracking
   > Subjective verification: <list, or '(none)'>
   > Touches architecture: <comma-separated §-section refs (§2, §3, §6.NN-3), or '(none)'>   # used by dispatch pre-flight + review agent; see $PERRY_HOME/packs/software-ops/architecture.md
   > Deployed: yes | no                          # default 'no'; 'yes' triggers runbook + observability gate at close
   > Runbook: runbook/<slug>.md                  # required ONLY when Deployed: yes; path must exist before close-task
   ```

   **When `Deployed: yes`, the spec ALSO requires an `## Observability` section** with three sub-fields (see `$PERRY_HOME/packs/software-ops/runbooks.md § Spec contract`):
   ```
   ## Observability
   - Success signal:   <log line / metric / endpoint / `command` output that proves it's working>
   - Failure diagnosis: `<single command>` — one line that answers "what's broken right now"
   - Runbook path:     runbook/<slug>.md
   ```

   **Choosing executor (spec writer responsibility)**:
   - `claude-subagent`: small task, needs MCP tools the parent session has, needs codebase familiarity.
   - `codex`: medium/large self-contained, no MCP dependency, save Claude Code quota.
   - `manual`: high-stakes per project hook (production deploys, prod credentials, .env, paid APIs, cost ceiling raise) OR subjective decision-making (research candidate selection, design choices).

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
Reject if no evidence path provided.

**Pre-close gate 1 — `Touches architecture:` requires review agent PASS** (see `$PERRY_HOME/packs/software-ops/architecture.md § close-task gate`):
1. Open `evidence/<YYYY-MM>/<TASK-ID>-spec.md`. If header has `Touches architecture:` non-empty:
   - Find the latest dispatch evidence file for this task (`evidence/<YYYY-MM>/<TASK-ID>-dispatch-*.md`, latest mtime).
   - Verify it contains an `## Architecture review` section ending with `PASS`. `FAIL` or missing → refuse close.
2. **If review missing or FAIL**, use `AskUserQuestion` (header = TASK-ID, options): `Re-dispatch to fix (Recommended) | Override — close without arch review (NOT recommended) | Keep as review`. "Override" requires written reason; logged as `architecture-override: <reason>` in journal.
3. `Touches architecture: (none)` or field absent → skip this gate.

**Pre-close gate 2 — `Deployed: yes` requires a runbook** (see `$PERRY_HOME/packs/software-ops/runbooks.md § close-task gate`):
1. Open the spec. If header has `Deployed: yes`:
   - `Runbook:` field must be present AND point at an existing file.
   - The referenced runbook file must have all four mandatory sections (What / Healthy / Failures / Escalation), non-empty.
   - The spec must contain an `## Observability` section with non-empty Success signal / Failure diagnosis / Runbook path.
2. **If any check fails**, refuse close. Use `AskUserQuestion` (header = TASK-ID, options): `Add runbook now (Recommended) | Keep as review until runbook exists | Override — close without runbook (NOT recommended)`. "Override" requires a written reason; the override is logged under `## Status changes` as `runbook-override: <reason>`.
3. `Deployed: no` or field absent → skip this gate.

**Pre-close gate 3 — record the verification rung** (DESIGN-003 § 5.3; `schema/state-schema.json § verification`):

Before flipping status, capture **how** this was verified, not just that evidence exists. Pre-select the track's `Default rung` from `.perry/config.md § Tracks` (V3 for `project`, V5 for `pipeline`, V2 for `queue`, V4 for `inquiry`), so the ordinary case costs the user no decision at all — they confirm rather than choose.

Two rules override the default, and neither is optional:

- **Consequence beats mode.** If the task matches `.perry/hook.md § High-stakes operations` — outward-facing, irreversible, or carrying money, legal or safety exposure — the rung is **V5 minimum** whatever the mode default says. `perry-lint --verification` reports the mismatch as `consequence-needs-signoff`, so a close below V5 on a high-stakes row will surface at the next standup regardless.
- **V4 needs a rubric, V5 needs a signature.** A `V4` close must cite the acceptance-criteria file the reviewer scored against, and that reviewer must not have seen the reasoning that produced the artifact. A `V5` close must record **name, date, and what was checked** — "reviewed" is not what was checked.

Write the chosen rung into the BOARD row's `Verification` column (add the column if the board has none) and into the journal status-change line. **Advisory this release** by DESIGN-003 § 4 decision 4: a missing or unsatisfiable rung is reported, never refused, because a hard gate on day one would retroactively invalidate every `done` row written before rungs existed. The number to watch is `unrated` in `perry-state`'s `board.verification` — it is what should shrink before the gate hardens.

**Pre-close gate 4 — inquiry mode** (`modes/inquiry.md`). On an inquiry-mode track:
1. `evidence/<YYYY-MM>/<ID>-answer.md` must exist — the question restated, the answer, the claims with their `[SRC-n]` citations, and what would change the answer. The mode's signature failure is re-deriving the same synthesis every session, and its one cause is the answer living in chat.
2. `perry-lint --provenance --root .` must report no `citation-dangling` for that file. This is the half of the bar `modes/inquiry.md` calls the mode's test suite; the rung is the other half, and shipping only the rung leaves the script unrun.
3. **A parent may not close before its children.** Any row whose `Parent` is this ID must be `done` or `dropped` first. An answered parent over an open child means either the child was not load-bearing — drop it and say why — or the answer is premature.

If the task spec lists `Subjective verification` items, **use `AskUserQuestion`** (header = TASK-ID, options = `Verified — close (Recommended) | Partial — keep as review | Reject — needs rework`) before flipping status. On `Verified — close`:
1. **Close it with the tool, not by hand.**

   ```
   "$PERRY_HOME/bin/perry-task" done <TASK-ID> --evidence "<path or citation>" --rung <V1..V6>
   ```

   It removes the board row, writes the journal status-change line with the rung
   in it, and records the close event — atomically. `--rung` defaults to the
   track's `Default rung`, then the mode default, so the ordinary case needs no
   flag. **`--evidence` is required and the tool refuses without it**: Perry's
   oldest rule, enforced at write time rather than reported afterwards.

   `V0` is refused by name — it is what is being rejected, never a rung a row
   may carry.

   On a pipeline track, check the row reached the terminal stage of its `Stages`
   first: `approved` is not `published`, and closing short of the last stage is
   that mode's signature failure wearing a green checkmark.

2. The tool wrote the status-change line. Anything more the close deserves — a
   paragraph of what was learned, a correction, a finding — goes in today's
   `## Notes` by hand.
3. If the task was a Must-Have item in `phase/<NNN>-<slug>.md`, tick it there too.
4. The original task definition (creation-day journal entry) stays untouched — that's the historical record.
5. **If `Deployed: yes`**: bump the runbook's `Last verified: <today>` field (the close is evidence the user reviewed the runbook against reality at this moment).

To find a closed task later: `grep "TASK-007" journal/` returns its creation entry, all status changes, and its close entry.

### `drop-task <id> <reason>`
Symmetric to `close-task`:
1. Remove the row from `BOARD.md`.
2. Append a `## Status changes` line to today's journal: `[ID] <prev-status> → dropped · reason: <reason>`.
3. The original task definition in its creation-day journal entry stays untouched.

## Cross-session

### `coordinate`
Pull a snapshot of work from other Claude sessions/terminals tagged for this project (use a session-listing MCP tool if the project hook declares one; otherwise ask the user to paste summaries). Append a consolidated update to `PROJECT_STATE.md` under `## Recent cross-session work`. Distribute follow-ups by appending new tasks.

When an incoming update references a Project by **name** (progress reports usually do, and the name may have drifted), resolve it to a KR **by ID through `phase/<NNN>-linkage.md`** before rolling any progress up — explicit `kr:` → Project ID → registered alias (`$PERRY_HOME/reference/okr-linkage.md`). Ambiguous or unmatched → ask the user which Project/KR it is; never attribute by fuzzy name. Hand the answer to `okr` (`/okr link …`) rather than editing `phase/`. Unresolvable while the user is away → `/okr link --unlinked <id>` rather than pinning it to a guessed KR.

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

## Phase transition

### `rollover`
Runs when a phase has been scored via `okr score-phase` and the user is ready to start the next phase. With the BOARD/journal split, rollover is mostly informational — `BOARD.md` is already current; previous phase's journal entries are intact. Steps:

1. Confirm `evidence/<YYYY-MM>/retro.md` exists (the phase score from OKR). If not, prompt to run `okr score-phase` first.
2. **Calendar-month directories** — `journal/<YYYY-MM>/` and `evidence/<YYYY-MM>/` are calendar-bound; create new month dirs only if the calendar month rolled (most rollovers do NOT need this — phases can span multiple calendar months OR fit inside one).
3. **`BOARD.md` is left alone.** Open carry-forward tasks already live there; no "carry forward" step is needed because the board never had a phase boundary in the first place. If a row's task ID encodes a date or phase prefix, leave it untouched — it's the canonical handle.
4. For each unresolved task on BOARD: **use `AskUserQuestion`** (header = TASK-ID, options = `Carry forward (Recommended) | Drop with reason`). Batch up to 4 per call. For "Drop with reason", follow up with a free-text prompt for the reason, then run `drop-task`.
5. Hand off to OKR: print "OKR `plan-phase <new-slug>` is needed — pick the next phase's slug." Do **not** create the new phase file yourself — that's OKR's lane.
6. Append a `## Notes` entry to today's journal: "rollover from phase #<old-NNN>-<old-slug>; <n> rows carried; see evidence/<YYYY-MM>/retro.md".

`git log -- journal/` shows the full history per day; `git log -- BOARD.md` shows the live board's evolution; `git log -- phase/` shows phase progression.
