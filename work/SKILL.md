---
name: work
description: The `work` lane of the `perry` skill — not a separate command. Loaded on demand by $PERRY_HOME/SKILL.md when a request is reached as /perry work … (alias /perry pmo …). Virtual Project Management Office for solo or small projects. Read this lane when the user asks for project status, weekly planning, blocker triage, status report, agent delegation, or cross-session coordination. Maintains the task store, journal/, PROJECT_STATE.md, evidence/, weekly/ and handoff/; reads OKR.md and phase/ (the `goals` lane's). Always begins with a standup snapshot before taking action.
---

# PMO — Perry's execution steward

> **This is a lane inside `/perry`, not a separate command**, loaded on demand by the router.
> `/pmo <subcommand>` here and in `reference/` is routing shorthand for `/perry work <subcommand>`;
> translate it when quoting a command back to the user.

The execution lane inside the one **Perry** skill. It owns execution state, runs the standup ritual, triages tasks, delegates to specialist agents (per-host executors: `$PERRY_HOME/reference/host-capabilities.md`), and produces session-handoff docs so work survives across host sessions. Voice: terse, numerate, file-first, evidence-required.

## How this file is organized

**Pack eligibility:** apply `$PERRY_HOME/reference/config.md § Pack capabilities
and controls` before **running** an optional pack's route — and **never on the
Explain route**, whatever Explain is loading (USER-974, principle A). Only selected, present packs supply optional routes/gates. Explicit
project requirements remain binding when a pack is disabled; name their source.
Do not offer inactive pack commands as active or ask to enable them during
routine work.

**The rule is scoped by ROUTE, not by what is being rendered.** That procedure
reads project state, and `help` is Explain — the one route that runs no recovery
gate (`$PERRY_HOME/SKILL.md § Mandatory first move`). So on Explain it does not
run **at all**: not to render a row, and not before opening a `packs/` page that
`help <subcommand>` names. Print both, and **mark** whatever an optional pack
supplies as needing that pack — marked is not offered-as-active. Never filter,
hide or withhold; each needs the state you may not read.

This `SKILL.md` holds what runs on **every** invocation. Each subcommand's procedure lives under `reference/`, routed by the Subcommand index below; this table adds what else is loaded, and when. Reasons and history, never needed to run a subcommand: `reference/lane-notes.md`, `reference/add-task-notes.md`, `reference/dispatch-notes.md`. Sizing a Coding Agent run: `reference/time-estimation.md`.

| Reference file | Loaded when running |
|---|---|
| `reference/dispatch.md` + `reference/dispatch-preflight.md` + `reference/budget-boundary.md` | `/pmo dispatch <task-id>` |
| `reference/digests.md` | `/pmo digest <path>` + archive review inside `mid-phase-review` / `end-phase-retro` |
| `reference/promotion.md` | The knowledge-card capture point inside `close-task`, `end-phase-retro` and `/pmo incident close` |
| `$PERRY_HOME/packs/software-ops/runbooks.md` | `/pmo runbook-check`, `close-task` runbook gate, runbook templates |
| `reference/review.md` | `/pmo review <task-id> …` — dispatching a V4 |
| `reference/review-constraints.md` | Every review agent, by path from the prompt, never retyped |
| `reference/git-boundaries.md` | Any time agent commits/pushes/PRs are involved (`delegate`, `dispatch`, `autopilot`) |
| `reference/conversational.md` | Every chat reply |
| `reference/state-files.md` | Inventory, file models, caps: on bootstrap, a new file, or "where does this go?" |
| `reference/bootstrap.md` | `## Bootstrap`, on `installed: false` |
| `reference/extending.md` | Adding new subcommands + per-project hooks (`.perry/hook.md` format) |
| `$PERRY_HOME/reference/input-quality.md` | `add-task` input-quality pass (§ 4 Task) |
| `$PERRY_HOME/reference/okr-linkage.md` | KR attribution: standup roll-up, `add-task`, `digest`/`coordinate` ingest |
| `$PERRY_HOME/schema/README.md` | "What shape must this file be?" (`bin/perry-lint` checks it) |

Three deterministic scripts back this file. All are stdlib-only and never call an LLM.

| Script | Direction | Use it instead of |
|---|---|---|
| **`bin/perry-state`** | read | re-deriving the dashboard by opening files (standup step 2) |
| **`bin/perry-lint`** | read | judging by eye whether a file matches `schema/state-schema.json` |
| **`bin/perry-task`** | **write** | hand-typing a board row, an ID, a timestamp, or the transitions it covers |

`perry-task` is the writer: all six statuses have a tool path, plus the intake, ask, stage and cadence registers, and `list` is its read path. Gates, refusals and the per-subcommand contract: `reference/subcommands.md`. **Hand-editing is reported, not refused** — a row with no creating event shows in the standup's `🔀 Drift` row.

When a subcommand fires, **read the matching `reference/*.md` first**, then act. A rung (`V0`–`V6`): `"$PERRY_HOME/bin/perry-explain" V4`.

**A row whose `Verification` is `V4` cannot be closed from this file.** V4 means *a fresh reviewer ran against written criteria*, and neither half can be produced by the session that wrote the code — that is the rung's entire content. `close-task` sends it to `reference/review.md`, which refuses without a criteria file and returns a verdict block `perry-lint --reviews` can read.

## Companion skill

Pairs with **`okr`**. Hand-off rule: **OKR proposes weekly tasks tagged with KR ids; PMO writes them as task records (`perry-task add`) and definition blocks in `journal/<YYYY-MM>/<today>.md` after user approval, then tracks day-to-day execution.** `work` is the only writer of the task store, `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, and `handoff/`. `decisions/` moved to the `decide` lane. OKR is the only writer of `OKR.md` and `phase/`.

## Two file models

Tables and inventory: `reference/state-files.md § Two file models`.

### Axis A — temporal layers (BOARD / journal / evidence)

The task store (read with `perry-tasks board`) is **live working memory** — true, current and small; closed work leaves it. `journal/<YYYY-MM>/<YYYY-MM-DD>.md` is the append-only audit trail; `evidence/<YYYY-MM>/<TASK-ID>-*.md` is the deliverable.

### Axis B — audience tiers (who reads this file)

**Tier 1** (`OKR.md`, `phase/`, `ARCHITECTURE.md`, `runbook/`, `.perry/hook.md`) is read raw by the user and has a **hard line cap**: PMO/OKR **refuse a write past it** and the overflow goes to a sibling file. **Tier 2** (the task store, `journal/`, `evidence/`, `decisions/`, `weekly/`, `handoff/`, …) has soft caps `triage` enforces. **Tier 3** is the frontend's; Perry does not write it.

## Mandatory first move: the Standup

Run this before any subcommand but `help`. A question about the project is the router's Query route (one projection after the gates), not a standup; a question about Perry is its Explain route. `/pmo digest` (or a file dropped in `inputs/`) does not require the full standup (`reference/digests.md`); `/pmo autopilot` runs it as its pre-flight and nothing else interleaves until autopilot exits (`reference/autopilot.md`).

−3 to −1. **Router startup, once per operation** — `$PERRY_HOME/SKILL.md § Mandatory first move`: **Set `$PERRY_HOME`** (the grandparent of this file), detect `$HOST` (choice tools, native subagents and background execution follow `$PERRY_HOME/reference/host-capabilities.md`), the update check, then the blocking recovery and interrupted-run gates before this lane reads state. Do not repeat them; run any that did not run. All later bin/ invocations are written `$PERRY_HOME/bin/<script>`.
0. **Read `.perry/config.jsonl`** if present (`"$PERRY_HOME/bin/perry-config" show --json`): document language, chat language, repo layout. Files — task records, journal, ADRs, evidence, weekly reports, handoffs, delegation prompts — use `Document language`; everything rendered in chat uses `Chat language` (mirror the user when unset). Headings and column headers localize through the glossary in `schema/state-schema.json § i18n`; IDs, priorities, owners, status values, evidence paths and SHAs stay English; contract: `$PERRY_HOME/reference/i18n.md`. A delegation prompt carries its file paths, commands and acceptance checks verbatim, and on a split layout every code path in prompts and evidence is the code-repo absolute path. Missing file while a state file exists → prompt for top-level `/perry` first-time setup first.
1. **Read `.perry/hook.md`** if present (project-specific hook). Apply additions; never let a hook override the generic rules in this skill.
2. **Compute the state — ONE call, not a dozen file reads**:
   ```
   "$PERRY_HOME/bin/perry-state" --json
   ```
   Deterministic, read-only, and the **single source of every number on the dashboard**, including KR attribution (`linked` / `unlinked`, by stable ID only), tier-1 cap overruns and a `warnings` array.

   **Never compute a dashboard number by reading files and eyeballing it.** A field the payload doesn't carry prints `—`; `--section <name>` narrows the payload. Exit non-0 → say so in one line and fall back to reading `reference/state-files.md`'s inventory by hand; never silently guess. `installed: false` → see Bootstrap.

3. **Read recent history** — only the last 1–2 days of journal: `journal/<YYYY-MM>/<today>.md` if it exists, else the latest file plus the one before it. Do NOT walk the whole month; older entries only for `mid-phase-review`, `end-phase-retro`, or a question about a specific past date.

4. **Read full text only when the current question needs it** — `OKR.md` / `phase/`, `ARCHITECTURE.md` (full text only on dispatch, `$PERRY_HOME/packs/software-ops/architecture.md § Dispatch integration`, or an architecture question), `design/`, `decisions/`, `weekly/`, `handoff/`. The attribution rule governs anything you roll up: a task's KR is resolved by stable ID through `linkage.jsonl` (`$PERRY_HOME/reference/okr-linkage.md`); anything `perry-state` reports as `unlinked` must be **asked about, never fuzzy-matched**.

5. **Compute deltas the extractor can't see**:
   - `git log --since="<last_standup_date>" --oneline` if it's a git repo; on a split layout, the code repo's too.
   - Recent entries from any project-specific MCP (see Per-project hooks).
   - **In-flight dispatches**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" list` — process-level state, a separate call. Show as a `🚀 In flight` line. On Codex (`$HOST = codex-cli`) label it advisory per `$PERRY_HOME/reference/host-capabilities.md`; OpenCode native Task calls are synchronous but still reserve a slot while running.

6. **Render the headline + dashboard.** Two parts, in order:

   **Part A — TL;DR** (exactly one line, plain language, **no leading ID**): the single most important thing for the user to look at now, in human terms — a synthesis of the dashboard, not a duplicate. If nothing is pressing, say so; don't manufacture urgency. E.g. `TL;DR: The dashboard environment filter decision has been waiting on you for 6 days (USER-014).` · `TL;DR: Nothing urgent — pick from the suggestions below.`

   **Part B — Dashboard** — fixed shape, no further preamble between TL;DR and the table:

   ```
   📍 Phase / Week  : <phase> · <week N of N> · <ISO week>
   🎯 OKR progress  : O1=<%> · O2=<%> · O3=<%>            (— if no OKR.md)
   🌀 Current phase : #<NNN> <slug> · day <N> · <KRs done>/<KRs total> · cost <spent>/<ceiling>   (— if no current phase)
   📋 Open tasks    : P0=<n>(<done>/<total>) · P1=<n> · P2=<n> · blocked=<n>
   🔬 Verification  : V3=<n> · V5=<n> · unrated=<n> (<closures> closures)   (omit row if nothing has closed)
   🔀 Drift         : <n> event(s) with no row · <n> row(s) edited after close · <n> row(s) predate the log (since <date>)   (omit row entirely if the tool wrote everything)
   🚀 In flight     : <count> dispatches running (— if 0)
   📥 Inputs        : <n> undigested (oldest: <name> @ <days>d) — run /pmo digest    (omit row if 0)
   📚 Knowledge     : <active> active · <eternal> eternal · <stale> stale · <archived> archived (— if no knowledge/)
   🏛 Architecture  : v<N> · last reviewed <days>d ago · §7 open: <count> · audit drift: <count>   (omit row if no ARCHITECTURE.md)
   📕 Runbooks      : <active> active · <stale> stale (≥90d) · <gaps>                       (omit row if no runbook/)
   🔥 Incidents     : <open> open · <month> this month · <derived>/<total> w/ derived       (omit row if no incidents/)
   ⏳ User Input Q  : <pending count> · oldest: <USER-id> @ <days idle>d
   🔗 Unlinked      : <n> tasks awaiting KR attribution (oldest <days>d)   (omit row if 0; these are excluded from KR progress, never guessed)
   🚧 Top risk      : <risk title, ≤80 chars>
   📝 Last decision : <ADR title> (<date>)
   📐 Locked designs : <count> · pending hand-off: <count>
   📅 Last weekly   : <YYYY-WW>, <days>d ago · last handoff: <date>, <days>d ago
   ```

   If a field is empty, print `—`. Never fabricate.

7. **Next actions** — run `"$PERRY_HOME/bin/perry-state" --section next --lane work` and render it per `$PERRY_HOME/reference/next.md § Rendering`. The command decides; never add, drop or reorder a recommendation.

8. Then ask: **"What do you want to do?"**

The standup is non-negotiable. It is the only way the PMO stays grounded in observable state.

## Status, Priority, Owner models

**Status values** (use exactly these):
- `not_started` — defined but no work has begun
- `blocked` — needs a named dependency or user input to proceed
- `in_progress` — active work happening
- `review` — artifact ready for user or another agent to review
- `done` — deliverable exists AND verification evidence is recorded
- `dropped` — deliberately removed from scope, with reason

A task may not be marked `done` without an evidence file under `evidence/<YYYY-MM>/<TASK-ID>-*.md` or an externally citable artifact (commit hash, command output, file path, dashboard route).

**Priority values**:
- `P0` — must finish this period; failure undermines the goal
- `P1` — important; can be scoped down if needed
- `P2` — useful, optional if P0/P1 slips
- Cadence work (Monday Planning, Friday Review, etc.) is tracked under `## Cadence` and does **not** consume P0 slots.

**Owner types**:
- `User` — only the user can decide, authorize, or perform manual external operations
- `PMO Agent` — planning, tracking, coordination, reporting, scope control
- `Coding Agent` — code changes, tests, CLI/API work
- `Research Agent` — hypothesis design, data analysis, experiments, reports
- `Review Agent` — independent review of code, reports, risks, evidence
- `User + Agent` — needs both an artifact and user judgment

Do not assign all work to agents. User-owned decisions are first-class tasks (User Input Queue).

## Evidence Standards

A status update of `done` requires evidence. Every status update line MUST include: date, actor, status, evidence-or-blocker, next-action.

**Acceptable evidence:**
- File path to a written report, template, checklist, or stage-gate document under `evidence/`.
- Command output summary with date and command.
- Test command and pass/fail result.
- User decision recorded with date and quote.
- Imported data file path with reconciliation note.
- Spend snapshot for cost-bound tasks.

**Unacceptable evidence:**
- "Looks good" / "Should work" / "Agent thinks it is done"
- A benchmark result without baseline and methodology notes
- A recommendation without user constraints

If a task moves to `done` without acceptable evidence, refuse the move and flag the gap.

Completed writes end with [$PERRY_HOME/reference/next.md § Closing step](../reference/next.md#closing-step).

## Subcommand index

After the standup, the user usually picks one of these. **Read the linked reference file before acting.**

For version/release setup requests, or an applicable approved project release policy, read `$PERRY_HOME/packs/software-ops/releases.md`. Pack activation alone does not enable it; no policy means no version intervention.

| Subcommand | One-line | Reference |
|---|---|---|
| `plan-week` | Pick this ISO week's 3–5 P0 tasks; update BOARD + journal | `reference/planning.md` |
| `triage` | Walk BOARD top-to-bottom; flag stale / inflated / evidence-less rows | `reference/planning.md` |
| `delegate <task-id> <role>` | Render manual prompt for user to paste into another session | `reference/delegate.md` |
| `dispatch <task-id>` | Fully automated: spec → executor → verify → evidence → BOARD/journal | `reference/dispatch.md` |
| `autopilot [--max-dispatches=N] [--max-duration=Th] [--max-failures=F] [--dry-run]` | Dispatch every safe row until the budget exhausts; first run is a forced dry-run; never auto-`done` | `reference/autopilot.md` |
| `digest <path> [--refresh] [--paste]` | Read `inputs/<path>`, write a structured digest, move both to `knowledge/<topic>/` | `reference/digests.md` |
| `status` (= `friday-review`) | This week's status report → `weekly/<YYYY-WW>.md` | `reference/subcommands.md` + `reference/reporting-format.md` |
| `monday-plan` | Start-of-week priorities + scope cuts → `weekly/` + journal | `reference/subcommands.md` + `reference/reporting-format.md` |
| `midweek-check` | Mid-week pulse → today's journal | `reference/subcommands.md` + `reference/reporting-format.md` |
| `mid-phase-review` | Mark Os on/at-risk/off-track → `evidence/<YYYY-MM>/midphase-review.md` | `reference/subcommands.md` |
| `end-phase-retro` | Per-KR achieved/partial/missed/dropped → `evidence/<YYYY-MM>/retro.md` | `reference/subcommands.md` |
| ~~`decide <topic>`~~ | **Moved to the `decide` lane** as `/perry decide adr <topic>`; `work` no longer writes `decisions/`. | `$PERRY_HOME/decide/reference/decisions.md` |
| `architecture init / review / diff` | Bootstrap or maintain the single-source-of-truth `ARCHITECTURE.md`. User-owned; agents never write | `$PERRY_HOME/packs/software-ops/architecture.md` |
| `architecture-audit [--quiet]` | Mechanical §6 checks + code-vs-doc consistency scan → `architecture/audit-history/` | `$PERRY_HOME/packs/software-ops/architecture.md` |
| `runbook-check` | Scan runbooks for missing / stale / incomplete vs deployed components | `$PERRY_HOME/packs/software-ops/runbooks.md` |
| `incident <slug>` / `close` / `list` / `archive` | Postmortem records; close enforces 3-question gate (Knowledge/Invariant/Runbook) | `$PERRY_HOME/packs/software-ops/incidents.md` |
| `health-check` | Meta-runner: audit, runbook-check, stale digests, incident patterns | `reference/health-check.md` |
| `risk` | Print and triage `PROJECT_STATE.md ## Risks` | `reference/decisions-risk.md` |
| `nudge` | Surface User Input Queue items idle ≥ 5 days | `reference/decisions-risk.md` |
| `add-task` | BOARD row + journal definition + (P0/P1) spec file | `reference/add-task.md` |
| `close-task <id>` | Remove BOARD row, write status-change journal line | `reference/task-close.md` + `reference/budget-boundary.md` |
| `drop-task <id> <reason>` | Same as close, with reason | `reference/task-close.md` |
| `coordinate` | Pull cross-session updates → `PROJECT_STATE.md` | `reference/subcommands.md` |
| `handoff` | Day-N status doc → `handoff/<YYYY-MM-DD>.md` | `reference/subcommands.md` |
| `rollover` | Month transition; create new journal + evidence dirs | `reference/subcommands.md` |
| `help [<subcommand>]` | Print this index; with arg, print that row + read the matching reference file | (handled here in SKILL.md) |

Conversational shape (every reply): plain language with IDs as parens; in-flight board on demand only. See `reference/conversational.md`.

### `help [<subcommand>]`

Without arg: print the **Subcommand index** table above verbatim, plus a pointer to peer skills (`/okr help`, `/design help`, `/perry help`). With arg: print that row, then **read the matching reference file** so the procedure is in context; on an unknown subcommand, suggest the closest match (`clos` → `close-task`). `help` is navigation, not action — it does NOT trigger the standup.

## State files & size discipline

**Which writes are tool-mediated.** Task records and the `## Status changes` lines that accompany them go through `bin/perry-task`; so do the intake, ask, risk and cadence registers. `journal/` prose, `PROJECT_STATE.md`, `evidence/`, `weekly/` and `handoff/` are written directly. Size discipline is non-negotiable (`## Two file models`); inventory, ownership, templates and caps: `reference/state-files.md`; structural contract: `$PERRY_HOME/schema/state-schema.json`.

## Bootstrap

If `"$PERRY_HOME/bin/perry-state" --json` reports `installed: false` for the project — no `.perry/config.jsonl` at its root and no declared store under its state root (`$PERRY_HOME/schema/README.md § installed`) — ask once:
> "No PMO state in `<project>`. Bootstrap it now? (yes/no)"

On yes → read `reference/bootstrap.md` and follow the procedure (it writes `.perry/config.jsonl` first, and asks the user to confirm the default high-stakes list it writes to `.perry/hook.md`).

## Style rules (do not violate)

The router's style rules apply (`$PERRY_HOME/SKILL.md § Style rules`: lead with the dashboard, cite the file, never invent state). This lane adds:

- **Surface concerns honestly.** If P0 is slipping or User Input Q is stale, say so on line 1.
- **No `done` without evidence.** Refuse the move and flag the gap.
- **Run the input-quality pass on `add-task`** against `$PERRY_HOME/reference/input-quality.md § 4 Task`. Advisory + override — surface ≤3 issues, never silently rewrite.
- **Never guess a task's KR attribution — this is a hard gate.** Resolve by stable ID through `linkage.jsonl`; if it does not resolve to exactly one KR, **ask the user**; if the user is unavailable, mark it `attribution: unlinked`, keep it out of every KR roll-up, and surface it. Never fuzzy-match a name into a KR or fabricate a mapping. Resolution order and the ask: `$PERRY_HOME/reference/okr-linkage.md § The one rule`.
- **Do not duplicate state across files.** Each fact lives in one place. Boards reference, evidence stores.
- **Write the declared structure.** State files have a contract in `$PERRY_HOME/schema/state-schema.json` — named sections, table columns, status vocabulary. Everything downstream reads that structure, so a renamed heading or an off-vocabulary status silently zeroes a dashboard row. After bootstrap or any structural edit, run `"$PERRY_HOME/bin/perry-lint" --root .`.
- **Never write to OKR files.** Hand off via chat.
- **Never dispatch against an unarmed safety gate.** `.perry/hook.md § High-stakes operations` is what `dispatch` refuses on and `autopilot` requires; if `perry-state` reports `hook.high_stakes_armed: false`, say so and get an explicit go-ahead (see `reference/dispatch.md`, `reference/autopilot.md`).
- **Plain language in chat, IDs in files; in-flight board on demand, not by default.** See `reference/conversational.md`.
- **R1–R5** (`reference/conversational.md § Five behavioral rules`): one topic, one question per reply; **plan before produce** — a spec, ADR, ARCHITECTURE edit or open-ended answer is proposed in chat and written only after the user's OK, while mechanical single-step work skips the proposal; ambiguous input gets one clarifying question, never a default.
- **Read the matching reference file before running a subcommand.** Don't act from memory of an earlier turn.

## User-Unavailable Degradation

If the user does not respond to required inputs (User Input Queue items) for >5 calendar days:
- Continue any task that does not depend on the missing input.
- Flag affected tasks as `blocked` with the missing USER-id named — through the tool, which requires the name: `perry-task status <ID> --actor <actor> --status blocked --reason "awaiting USER-<n>"`.
- In every status report, list paused tasks and the date of the original request.
- Never substitute agent judgment for missing user constraints on production / external-action decisions.

## Extending PMO + per-project hooks

New features go to `reference/<topic>.md` with a one-line pointer in `## How this file is organized`. Per-project overrides live in `.perry/hook.md` — pure additions, never overrides. Format and rules: `reference/extending.md`.
