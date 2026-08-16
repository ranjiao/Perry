---
name: perry
description: Perry — your virtual project office. A three-skill set: goal-setting (okr) + execution stewardship (pmo) + design-doc stewardship (design) for solo or small projects. Use /perry for a combined snapshot of where the project is, or invoke /okr, /pmo, /design directly for specific subcommands. okr owns OKR.md (versioned, with Operating Principles + Anti-Goals) and phase/<NNN>-<slug>.md (current phase, NOT calendar-bound). pmo owns BOARD.md (live working memory, ≤200 lines), journal/<YYYY-MM>/<YYYY-MM-DD>.md (daily history), PROJECT_STATE.md, DECISIONS.md, evidence/<YYYY-MM>/, weekly/<YYYY-WW>.md, handoff/<YYYY-MM-DD>.md. design owns design/<DESIGN-ID>-<slug>.md. They cooperate through file ownership; no skill writes outside its lane. Project-wide preferences (document language, single vs split repo layout) live in .perry/config.md and are confirmed at first-time setup.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry is a coordinated **skill set** with three children that share a project's state files at the project root. This top-level skill is the entry point: a combined snapshot, a brief intro for new users, and a router to whichever child you actually want.

## Children of this skill

This folder contains three child skills. They live under `$PERRY_HOME/<child>/SKILL.md` and are invocable on their own. Read each child's SKILL.md for full subcommand detail.

> **Host portability**: Perry runs on **Claude Code** (default install at `~/.claude/skills/perry/`) and **Codex CLI** (default install at `~/.agents/skills/perry/`). Both hosts read SKILL.md frontmatter natively for skill discovery — no AGENTS.md or other routing file is needed. The standup ritual below sets `$PERRY_HOME` from the install location, detects which host is live, and reads `$PERRY_HOME/reference/host-capabilities.md` for the fallback rules (free-text prompts instead of `AskUserQuestion` on Codex, refusal of `Executor: claude-subagent` on Codex, etc.). Where this file or a child SKILL.md names a Claude-Code-specific tool (`AskUserQuestion`, `Agent()`, `Bash run_in_background`), that capability page owns the per-host translation; SKILL.md prose stays single-sourced.

| Child | Invoke as | Owns | What it does |
|-------|-----------|------|--------------|
| **`okr`** | `/okr` | `OKR.md`, `phase/<NNN>-<slug>.md` | Goal-setting: overall versioned OKR, current phase OKR with 10 mandatory sections (NOT calendar-bound; phases end when KRs hit), weekly task proposals (handed off to PMO) |
| **`pmo`** | `/pmo` | `BOARD.md` (live), `journal/<YYYY-MM>/<DD>.md` (daily), `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/` | Execution stewardship: standup ritual, task triage, agent delegation, status reports, cadence rituals, phase rollover |
| **`design`** | `/design` | `design/<DESIGN-ID>-<slug>.md` | Design-doc stewardship: RFC drafting, user-decision tables, lock workflow, hand-off of implementation tasks to PMO |

## The hand-off contract (the most important rule)

- `okr` is the **only writer** of `OKR.md` and `phase/`. It **proposes** weekly tasks but never writes them.
- `pmo` is the **only writer** of `BOARD.md`, `journal/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`. It **reads** OKR and design files for context.
- `design` is the **only writer** of `design/<DESIGN-ID>-<slug>.md`. On lock it **proposes** implementation tasks but never writes `BOARD.md` or `journal/`.
- Each skill reads the others' files freely; no skill writes outside its lane.

This single rule is what keeps the set composable and lets you drop in a fourth child later (e.g., `research-journal`, `risk-review`) without breakage.

## When this skill activates

Trigger on any of:
- The user invokes `/perry` or types "Perry".
- The user types "/perry help" or "/perry help <child>" — see `## /perry help` below; do NOT trigger the combined snapshot for help.
- The user opens a session and wants a "where are we" overview without specifying OKR vs PMO.
- The user is new to Perry and asks how it works or what to do first.
- A new session opens in a project that contains both `OKR.md` and `BOARD.md` and the user wants the combined view.

If the user clearly wants only goal-setting → route to `/okr`. If clearly only execution → route to `/pmo`. The coordinator is for the cases in between.

## Mandatory first move: combined snapshot

When `/perry` is invoked, always run this before doing anything else.

−2. **Set `$PERRY_HOME`** — if the env var is not already set, derive it from the path of the SKILL.md you just read. `$PERRY_HOME` is the directory containing this top-level SKILL.md (it also contains `bin/`, `reference/`, `okr/`, `pmo/`, `design/`). For child SKILL.md (`<PERRY_HOME>/<child>/SKILL.md`), use the grandparent directory. All later bin/ invocations in this file and the reference files are written as `$PERRY_HOME/bin/<script>` — they only work if this step ran.

−1. **Detect host once** — silently:
   ```
   bash "$PERRY_HOME/bin/perry-detect-host"
   ```
   Output: `claude-code` | `codex-cli` | `unknown`. Remember as `$HOST` for the rest of the conversation. Then read `$PERRY_HOME/reference/host-capabilities.md` for fallback rules. If output is `unknown`, default `$HOST=claude-code` but tell the user once and recommend setting `PERRY_HOST` in their shell profile.

0. **Run the weekly auto-update check** — silently in the background:
   ```
   bash "$PERRY_HOME/bin/perry-update-check"
   ```
   The script throttles itself to once per 7 days; most invocations exit immediately with no output. When it does run, output is one line (or zero). Surface its output to the user verbatim if non-empty (the user wants to know about updates), then continue with the snapshot.

1. **Read `.perry/config.md`** if present, to pick up document language and repo layout. If absent and any state file exists, prompt the user to run first-time setup so the config is recorded.

2. **Compute the state — one call**:
   ```
   "$PERRY_HOME/bin/perry-state" --json
   ```
   Deterministic, read-only, stdlib-only. `installed: false` → jump to **First-time setup** below. Otherwise the payload carries everything the combined dashboard needs across all three children — OKR version + objectives, phase number / day / KR totals, board counts, User Input Queue, top risk, last ADR, locked designs and their hand-off status, plus a `warnings` array. **Every number below comes from this payload**; a field it doesn't carry prints `—`. Flag any child whose files are missing (no `OKR.md`, no `BOARD.md`, empty `design/`).

3. **Render the combined dashboard** — exactly this shape, no preamble:

   ```
   🅿  Perry · <project name> · <today's date>

   🎯 OKR (vN, <period>) · <days_elapsed>/<days_total>d
      O1 · <title> ............ <%>
      O2 · <title> ............ <%>
      O3 · <title> ............ <%>          (omit unused Os)

   🌀 Current phase #<NNN> <slug> · day <N> · cost <spent>/<ceiling>
      P-O1 · <title> .......... <KRs done>/<KRs total>
      P-O2 · <title> .......... <KRs done>/<KRs total>

   📋 Open tasks  : P0=<n>(<done>/<total>) · P1=<n> · P2=<n> · blocked=<n>
   ⏳ User Input Q: <pending count> · oldest: <USER-id> "<title>" @ <days idle>d
   🚧 Top risk    : <risk title, ≤80 chars>
   📝 Last decision: <ADR-id> "<title>" (<date>)
   📅 Last weekly : <YYYY-WW>, <days>d ago · last handoff: <date>, <days>d ago
   ```

   Use `—` for empty fields. Never fabricate values.

   **Every ID printed here carries its title**, per `## Style rules` — a
   dashboard line naming `USER-014` and nothing else tells the user they are
   blocked and not what on. If the payload has an ID but no title for it, run
   `bash "$PERRY_HOME/bin/perry-explain" <ID>` rather than printing the bare ID
   or inventing a name.

4. **Suggest 1–3 next actions** combining OKR, PMO, and design concerns:
   - "phase #002 commit KRs ≥80% → run `/pmo end-phase-retro`, `/okr score-phase`, `/pmo rollover`, `/okr plan-phase <new-slug>`"
   - "USER-014 (\"Confirm staging env default\") idle 6d, weekly is 8d old → run `/pmo nudge` then `/pmo friday-review`"
   - "no current phase → run `/okr plan-phase <slug>`, then `/okr plan-week`, then `/pmo` to add the tasks"
   - "DESIGN-002 (\"Flake scoring\") in_review for 8d → run `/design lock` or `/design revise`"

5. Then ask: **"What do you want to do?"**

If the user picks an OKR-flavored action (plan, score, pivot, revise), invoke the `okr` skill. If a PMO-flavored action (triage, status, delegate, handoff, rollover, decide, risk), invoke `pmo`. If a design-flavored action (RFC, architecture, lock, supersede), invoke `design`. If unclear, ask which, then route.

## First-time setup

When `/perry` is run in a project with no Perry state files at all:

1. Briefly explain Perry (≤3 sentences).
2. **Confirm two project-wide preferences before any file is written** — record both in `.perry/config.md` (create the file if missing) so every subsequent session and every child skill reads from one source. Ask both via a single `AskUserQuestion` tool call (two questions, structured options):
   - **Document language** (header `"Language"`): options = `English (Recommended if user typed English) | 中文 (Recommended if user typed 中文) | other`. The "Recommended" tag goes on whichever matches the user's recent chat language.
   - **Repo layout** (header `"Repo layout"`): options = `Single repo (Recommended for non-code projects) | Split repo (PMO ↔ code; only if both exist and you've seen branch contention)`. See **Repo layout options** below for the trade-off explanation that goes into each option's `description`.

   All subsequent skill output (snapshots, dashboards, generated docs, delegation prompts) uses the configured language. If the user mixes languages later, keep using the configured language for written artifacts but mirror the user's language in chat replies.
3. **Ask whether this is a new project or an existing one** — one `AskUserQuestion` (header `"Starting point"`, options: `New project — start from goals (Recommended if the folder is nearly empty) | Existing project — analyze what's here first`). The second option routes to **`/perry adopt`**: Perry reads the project's own evidence (README, roadmap, git history, existing design/ADR docs, TODOs, issues) and proposes candidates the user confirms, instead of interviewing from a blank slate. Read `reference/adoption.md` before running it. Adoption writes no state file directly — it produces a dossier, the user confirms it, and the normal subcommands materialize the result.

   For a new project, recommend the order below.
4. Recommend the order:
   - First, run `/okr init` — interview to create `OKR.md` (mission, Operating Principles, 1–3 Objectives + KRs, Anti-Goals, version v1).
   - Then, run `/okr plan-phase <slug>` — creates the first phase OKR (`phase/001-<slug>.md`) with all 10 mandatory sections.
   - Then, run `/pmo` — bootstraps the execution files (`BOARD.md`, `journal/<current-YYYY-MM>/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`) and runs the first standup.
   - Finally, run `/okr plan-week` — proposes the first batch of weekly tasks, which `/pmo` then writes as BOARD rows + a journal entry under `## New tasks added`.
5. Ask: "Run `/okr init` now?" — if yes, invoke the `okr` skill. If no, stop and let the user proceed at their own pace.

## `/perry adopt` — converting an existing project

For a project that already exists — code, docs, git history, an issue tracker — the blank-slate `init` chain above throws away the answers the project already contains. `/perry adopt` reads them instead.

```
/perry adopt [--depth=quick|standard|deep] [--only=okr,board,design,knowledge,arch] [--resume] [--recheck]
```

**Read `reference/adoption.md` before running it.** The one rule that governs the whole pipeline: **evidence proposes, the user declares.** Adoption writes exactly one file of its own — `.perry/adoption/<YYYY-MM-DD>-dossier.md` — and everything that reaches `OKR.md` / `BOARD.md` / `design/` gets there through the normal subcommands after the user accepted it. File ownership is unchanged: adoption is an orchestrator, not a fourth writer.

Five stages, each resumable: **scan** (read-only report) → **harvest** (cited evidence) → **infer** (candidates, clustered) → **confirm** (goals authored by the user from a strawman; tasks triaged by cluster; designs/ADRs transcribed only where a source doc exists) → **commit** (materialize, then `perry-lint` must pass). `--recheck` re-runs the harvest against an adopted project and reports drift — work that landed in the repo but never on the board.

Sources, trust tiers, and the depth matrix (including non-code projects) are in `reference/adoption-sources.md`.

## `/perry diagnose` — auditing how a project works with agents

`adopt` converts a project **into** Perry. `diagnose` asks the prior question: **is this project's working structure sound at all?** It runs on any folder, including one that has never heard of Perry, and the right answer is often "leave it alone" or "you need three files" rather than "adopt Perry".

```
/perry diagnose [--depth=quick|standard|deep] [--only=<lanes>] [--dry-run] [--recheck]
```

**Read `reference/diagnose.md` before running it.** The governing rule: **every prescription traces to a finding, and every finding traces to a measurement or an answer the user gave.** Nothing may be prescribed because Perry prefers it — diagnosis is inherently judgmental, and without that gate this subcommand becomes a machine that converts every project into a heavier project. It writes exactly one file of its own — `.perry/diagnose/<YYYY-MM-DD>-diagnosis.md` — and changes to Perry state still go through the owning child skill.

Six stages: **scan** (`bin/perry-diagnose`, deterministic and read-only) → **read** (what a script can't measure — the gap between what the docs say and what `git log` shows) → **interview** (≤6 outcome-framed questions; the user's answers override the scan) → **prescribe** (the smallest change set, hard-capped by the user's stated maintenance tolerance) → **execute** (gated per item, restore point first, moves and never deletes) → **recheck** (drift, with declined items remembered rather than re-proposed).

It targets the three ways agent projects actually fail — concurrent sessions interfering, documents growing past the budget where they stop being obeyed, and goals drifting with no runnable check to say what is done. The research behind each, the isolation ladder, and the three archetypes are in `reference/project-archetypes.md`; runnable scaffolds are in `templates/`.

Two outcomes are first-class and must stay available: **zero findings**, and a prescription of pure **subtraction**. A diagnostic that has to find something to justify the run is one the user stops reading by the third invocation.

## Repo layout options

Perry supports two layouts. Pick one at first-time setup; record the choice in `.perry/config.md`.

### Option A — single repo (default for non-code projects)

Everything (OKR, TASKS, evidence, design, handoff, weekly) lives in one repo at the project root. Use this when:
- The project does not produce code (research notes, ops runbooks, business planning, personal projects without a codebase).
- The project ships code but the volume of code commits is low and PMO commits will not pollute the history.

This is the simplest layout. No cross-repo references; everything is one `git log` away.

### Option B — two-repo split (PMO docs ↔ code)

PMO docs live in `<project>-pmo/` (this repo, where Perry's state files sit); code lives in `<project>/`. Use this when:
- The project ships code AND has been observed to suffer from branch contention between PMO doc commits and code commits, OR PMO commits visibly pollute code commit history.
- The user explicitly prefers the separation.

Cross-reference convention:
- PMO docs reference code via `<commit-SHA> path/to/file.py` (commit SHA pinned, not branch — survives rebases).
- Code commits reference PMO task IDs in commit messages (e.g., `Closes TASK-007`).
- Each repo has its own `.git/`; neither repo is a submodule of the other.

Trigger to migrate from A → B: ≥ 2 incidents of branch contention or commit-history pollution within a month. Capture the trigger as a `DECISIONS.md` ADR (`Type: Process`) before splitting.

When B is in effect, `.perry/config.md` records both paths so every child skill knows where to look. Delegation prompts to Coding Agents must explicitly state which repo their work targets.

### `.perry/config.md` shape

```
# Perry configuration

- Document language: <English | 中文 | ...>
- Repo layout: <single | split>
- State root: <. | relative path>
- PMO repo path: <absolute path>
- Code repo path: <absolute path or — if single>
- Last updated: <YYYY-MM-DD>
```

Children read this file before any output. If the file is missing, prompt the user to run first-time setup.

### `State root` — where Perry's files live

Default `.` (the project root), which is what every Perry project written before this field existed assumes. **Ask the user** when the project already uses a directory Perry claims — `design/` is the usual collision, and a project's own design docs are not Perry design docs. Setting `State root: perry` puts `OKR.md`, `BOARD.md`, `phase/`, `design/`, `journal/` and the rest under `perry/`, leaving the project's own tree untouched.

`.perry/` itself **never moves**: it is the anchor that marks the folder as a Perry project and it holds this pointer, so it cannot sit behind the pointer. Every reader resolves the root the same way — `viewer/parsers.py § resolve_state_root` is the one implementation, and `schema/state-schema.json` declares which files are anchored at the project root (`anchor: project`) rather than the state root.

Adoption asks this question during `confirm`, before anything is materialized (`reference/adoption.md`).

## Routing reference

When the user types something inside a `/perry` session, route to the right child rather than answering ad-hoc.

**Route to `/okr` for:**
- Setting or revising goals · `init`, `revise`, `pivot`
- Phase planning · `plan-phase`, `score-phase`, `snapshot`, `dashboard`
- Weekly task proposals · `plan-week` (the hand-off step)
- Anything about Operating Principles, Anti-Goals, OKR versions, Cost Ceiling, KR scoring

**Route to `/pmo` for:**
- The standup itself, status, triage, blocker check
- Task lifecycle · `add-task`, `close-task`, `drop-task`
- Cadence rituals · `monday-plan`, `midweek-check`, `friday-review`, `mid-phase-review`, `end-phase-retro`
- Cross-session work · `coordinate`, `delegate` (manual prompt), `dispatch` (auto end-to-end via claude-subagent or codex), `handoff`
- Opening the project in a browser / live web console · `viewer` (= `browse`) — agent starts it and opens the browser for you
- Decisions and risks · `decide`, `risk`, `nudge`
- Phase transition · `rollover`

**Route to `/design` for:**
- Anything called RFC / architecture / design doc · `new`, `decide`, `lock`, `revise`, `supersede`, `drop`, `handoff`, `status`
- "Should we design this before building it?" → yes if multi-system, irreversible, or has multiple open user decisions

**Handle here in `/perry` (without routing):**
- The combined snapshot itself.
- `adopt` — converting an existing project into Perry state. It spans all three lanes, so it is orchestrated here and materialized through the children's own subcommands (`reference/adoption.md`).
- `diagnose` — auditing and refactoring how a project works with agents. Also an orchestrator, and the one subcommand that must be able to conclude the project needs *less* structure, or none of Perry's (`reference/diagnose.md`).
- "Explain Perry" / "what is this skill" — short pointer to README.
- Recommending the next action when the choice spans more than one child.
- Confirming or updating `.perry/config.md` (document language, repo layout).
- `help` — see below.

## `/perry help [<child>]`

Without arg: print a compact overview of the three children + when to use each + a pointer to each child's own `help`. This is the navigation entry point for users who don't know what's available yet.

Suggested format:

```
Perry — virtual project office (3 invocable skills)

  /okr      Goal-setting (overall + current phase OKR + weekly task proposals)
            Use when: setting goals, planning the month, scoring KRs,
            pivoting strategy.
            Common: /okr init, plan-phase, plan-week, score-phase, snapshot, dashboard
            Full list: /okr help

  /pmo      Execution stewardship (BOARD, journal, dispatch, cadence)
            Use when: standup, planning the week, delegating to agents,
            tracking blockers, writing weekly status, phase rollover.
            Common: /pmo, plan-week, triage, dispatch, friday-review
            Full list: /pmo help

  /design   Design-doc / RFC stewardship (locked decisions before building)
            Use when: drafting an RFC, locking user decisions, handing off
            implementation tasks to PMO.
            Common: /design new, decide, lock, handoff
            Full list: /design help

  /perry    This skill — combined snapshot across all three.
            Use when: starting a fresh session, one-stop "where are we",
            unsure which child you want.
            Common: /perry, /perry help, /perry adopt

  /perry adopt   Convert an EXISTING project into Perry state.
            Use when: the project already has code, docs, git history, or a
            tracker, and starting from a blank OKR would throw that away.
            Evidence proposes; you declare. Nothing is written until you accept.
            Common: /perry adopt, --depth=quick, --recheck

  /perry diagnose  Audit how a project works with agents, then refactor it.
            Use when: sessions keep interfering, the md files have become a
            jungle nobody can navigate, or there's no way to say what's done.
            Works on ANY folder — Perry not required, and "your structure is
            fine" is a valid result. Measures, interviews, prescribes the
            smallest fix, then executes it with your approval per item.
            Common: /perry diagnose, --dry-run, --recheck

First-time setup: /perry in a new project → confirms language + repo layout,
then asks new-vs-existing and routes to /perry adopt for existing projects.
Read more: $PERRY_HOME/README.md
```

With arg `okr`, `pmo`, or `design`: route to that child's `help` subcommand (the children own the detail). Don't re-render their tables here.

`help` does NOT trigger the combined snapshot ritual.

## Style rules

- **Lead with the dashboard, not narration.**
- **Numbers, IDs, file paths.** Not paragraphs.
- **An ID never travels alone.** The first time an ID appears in any user-facing output, it carries its human name: `REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")`, never `REL-002 blocked on USER-014`. Later mentions in the same response may use the bare ID, and a table with a Title column already satisfies this. Perry mints `REL-`, `ADR-`, `DESIGN-`, `P-O1.2`, `USER-`, `CAD-`, `SRC-`, `CL-`, `RX-` and phase numbers — that is a private vocabulary issued to someone who never agreed to learn it, and an unresolvable ID is a dead end in the middle of a sentence the user is trying to act on. Use `bin/perry-explain <ID>` to resolve one, `--all` for the glossary. Full rule in `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Before offering options, check whether the user can predict what will be different for them under each. If not, reframe in consequences, or decide it yourself and say so, or narrow to two — see `reference/user-load.md § The three exits`. Depth of analysis and usefulness of a question come apart completely once the subject leaves the user's expertise, and this gets *worse* as the agent gets better.
- **Cite the file** for every claim.
- **Never invent state.** Print `—` and ask.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.

## User-prompt convention (AskUserQuestion)

Whenever a Perry skill (top-level or any child) needs the user to make a choice with **2–4 distinct options**, prefer the `AskUserQuestion` tool over free-text "what do you want?" prompts. The Claude Code / Desktop UI renders `AskUserQuestion` as clickable button choices with an automatic "Other" free-text fallback — much faster for the user than typing.

> **Codex host**: `AskUserQuestion` is not available. Render the same option set as a numbered free-text prompt per `$PERRY_HOME/reference/host-capabilities.md § AskUserQuestion → numbered free-text prompt`. The chosen value, downstream writes, and conventions below are unchanged — only the rendering differs.

### When to use it

- Any subcommand that branches based on a user choice with a small bounded option set (e.g., `okr score` per-KR `achieved | partial | missed | dropped`, `pmo triage` per-row `apply | edit | skip`, `design decide` per-User-Decision row).
- First-time setup choices (document language, repo layout).
- Per-spec dispatch choice when the spec doesn't pin an executor (`pmo dispatch` → falls back to asking `claude-subagent | codex | manual`).
- Multi-select when you offer up to 4 candidate items the user may approve all/some/none of (use `multiSelect: true`).

### When NOT to use it

- Open-ended questions that need a sentence or paragraph (e.g., "What is this project's mission?"). Free-text only.
- Choice sets larger than 4 options. Either narrow first (recommend 1–4 + leave "Other" as the auto-filled fallback), or split into two `AskUserQuestion` calls.
- Confirmations that should always block on explicit user words (e.g., authorizing a high-stakes operation per the project hook). The auto-update check, `pmo dispatch` pre-flight refusals, and similar safety gates STILL ask in chat — `AskUserQuestion` is not a permission grant.

### Conventions

- **2–4 options per question.** No more, no fewer.
- **Label ≤ 5 words.** The tool enforces this; long descriptions go in the `description` field, not `label`.
- **Recommended option first.** Append `(Recommended)` to the label so the user sees which one Perry suggests.
- **Header chip ≤ 12 chars** (e.g., "Executor", "Status", "KR-1.2").
- **Each option's `description` carries the trade-off** — what happens, what it implies, what's lost. Don't make the user guess.
- **The trade-off is stated in consequences, not mechanism.** "Runs on your laptop with no setup, but breaks if two people use it at once" is decidable. "SQLite vs Postgres" is not, unless the user already knows. If an option cannot be expressed in something the user will experience, that is the signal it should not be a question — see `reference/user-load.md`.
- **Offer the escape hatch on anything the user may not be equipped for.** "Or I pick and tell you what I picked" as an explicit option. If they take it, don't re-ask a variant later. Two deferrals in a session means stop offering choices and switch to recommendations they can veto — and say that's what you're doing.
- **Cap open decisions at three at a time.** Past that, queue and say so. A decision backlog stalls everything downstream or lets it proceed on a guess, and afterwards nobody can tell which happened.
- **Anything decided on the user's behalf gets logged** as agent-decided, with what would trigger a revisit. Asking less is only acceptable if those calls stay visible and reversible.
- **Optional `preview`** for showing a code/template snippet (e.g., showing what the rendered task block will look like before they approve).
- Mutually exclusive options unless `multiSelect: true`.

### Concrete pattern: child skills with structured option lists

For child skills whose state files already enumerate options (notably `design/<DESIGN-ID>-*.md`'s `User Decisions` table), write the Options column in **pipe-separated short labels** so `decide` can map each cell directly to `AskUserQuestion` options without rephrasing:

```
| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Cache backend | Redis | Memcached | DynamoDB | TBD | — |
```

Each piped token becomes one `AskUserQuestion` option label.

## Per-project hooks (optional)

If your project has specific roadmap files, MCP tools, agent roles, cost ceilings, or promotion stages, add a hook block to **the children's** `SKILL.md` files (`okr/SKILL.md`, `pmo/SKILL.md`, `design/SKILL.md` each have a `## Per-project hooks` section). The top-level Perry skill stays project-agnostic.

Project hook files live at the project root (not in the skill folder), so a single Perry installation can serve many projects without entanglement. The recommended location is `<project_root>/.perry/hook.md`; children read it on every invocation.

## Auto-update

Every Perry skill invocation runs `bin/perry-update-check` as the first action. The script:
- Throttles itself to **once per 7 days** via `$PERRY_HOME/.update-check` mtime; most invocations exit immediately with no output.
- Detects "dev mode" — symlink install, dirty working tree, or non-`main` branch — and in that case **only fetches and reports**; it never auto-pulls (so it can't trample your WIP if you're editing Perry source).
- For "consumer mode" (real directory, clean tree, on `main`), does an ff-only `git pull` from `origin/main`.
- Always exits 0 (network failure, unresolved merge, etc. → notify and continue; never block the standup).

Manual trigger: `bash "$PERRY_HOME/bin/perry-update-check" --force` (bypasses throttle).

The script is invoked from the standup ritual of every child (`okr` / `pmo` / `design`), so triggering any of `/perry`, `/okr`, `/pmo`, `/design` covers it. If the skill source is not a git checkout (e.g., extracted from a tarball), the check exits silently.

## See also

- [README.md](README.md) — full overview, file layout, design rationale.
- [INSTALL.md](INSTALL.md) — install instructions.
- [schema/README.md](schema/README.md) — the state-file contract every skill, template, and parser must agree with; validated by `bin/perry-lint`.
- [reference/adoption.md](reference/adoption.md) — `/perry adopt`: the five-stage pipeline that converts an existing project into Perry state. The governing rule (**evidence proposes, the user declares**), the asymmetry between what may be inferred and what may not, cluster triage, the cluster→KR attribution pass, and the list of things adoption never does.
- [reference/user-load.md](reference/user-load.md) — the shared contract for all four skills on **how much a human can carry**: never ask a question the user cannot evaluate (and the three exits when the honest answer is that they can't), cap open decisions, log what was decided on their behalf, and the rule that **an ID never travels alone**. Perry mints nine ID families; this is what stops them becoming a private vocabulary.
- [reference/diagnose.md](reference/diagnose.md) — `/perry diagnose`: the six-stage pipeline that audits and refactors how a project works with agents. The governing rule (**every prescription traces to a finding**), the six-question interview, the prescription patterns, and the execution safety rules.
- [reference/project-archetypes.md](reference/project-archetypes.md) — the research diagnose applies: the three failure modes of agent projects, the isolation ladder, the tier discipline for documents, the minimum viable spine, three archetypes, and an explicit account of where the evidence is thin.
- [templates/](templates/) — runnable scaffolds for the three archetypes, including a verification loop for the two that have none natively (`kb-lint`, `deliverable-lint`).
- [reference/adoption-sources.md](reference/adoption-sources.md) — the harvest catalog: source detectors, A/B/C trust tiers (which cap derived confidence), the depth matrix, scale limits, non-code projects, and the citation forms every piece of evidence must produce.
- [reference/input-quality.md](reference/input-quality.md) — shared input-quality rubric run by okr / design / pmo before writing user-authored content to tier 1 files (advisory + override).
- [reference/okr-linkage.md](reference/okr-linkage.md) — shared O→KR→Project attribution gate: resolve a Project/Task's KR by stable ID via `phase/<NNN>-linkage.md`, and when it's unclear **ask the user, never guess** (hard gate; unresolved → `unlinked`, excluded from roll-up).
- [okr/SKILL.md](okr/SKILL.md) — full goal-setting subcommands and templates.
- [pmo/SKILL.md](pmo/SKILL.md) — full execution stewardship subcommands and templates.
- [design/SKILL.md](design/SKILL.md) — full design-doc stewardship subcommands and templates.
