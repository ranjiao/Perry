---
name: perry
description: Perry — your virtual project office. A three-skill set: goal-setting (okr) + execution stewardship (pmo) + design-doc stewardship (design) for solo or small projects. Use /perry for a combined snapshot of where the project is, or invoke /okr, /pmo, /design directly for specific subcommands. okr owns OKR.md (versioned, with Operating Principles + Anti-Goals) and monthly/<YYYY-MM>.md. pmo owns BOARD.md (live working memory, ≤200 lines), journal/<YYYY-MM>/<YYYY-MM-DD>.md (daily history), PROJECT_STATE.md, DECISIONS.md, evidence/<YYYY-MM>/, weekly/<YYYY-WW>.md, handoff/<YYYY-MM-DD>.md. design owns design/<DESIGN-ID>-<slug>.md. They cooperate through file ownership; no skill writes outside its lane. Project-wide preferences (document language, single vs split repo layout) live in .perry/config.md and are confirmed at first-time setup.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry is a coordinated **skill set** with three children that share a project's state files at the project root. This top-level skill is the entry point: a combined snapshot, a brief intro for new users, and a router to whichever child you actually want.

## Children of this skill

This folder contains three child skills. They live under `${PERRY_HOME:-$HOME/.claude/skills/perry}/<child>/SKILL.md` and are invocable on their own. Read each child's SKILL.md for full subcommand detail.

> **Host portability**: Perry runs on **Claude Code** and **Codex CLI**. The standup ritual below detects which host is live and reads `reference/host-capabilities.md` for the fallback rules (free-text prompts instead of `AskUserQuestion` on Codex, refusal of `Executor: claude-subagent` on Codex, etc.). Where this file or a child SKILL.md names a Claude-Code-specific tool (`AskUserQuestion`, `Agent()`, `Bash run_in_background`), that capability page owns the per-host translation; SKILL.md prose stays single-sourced.

| Child | Invoke as | Owns | What it does |
|-------|-----------|------|--------------|
| **`okr`** | `/okr` | `OKR.md`, `monthly/<YYYY-MM>.md` | Goal-setting: overall versioned OKR, monthly OKR with 10 mandatory sections, weekly task proposals (handed off to PMO) |
| **`pmo`** | `/pmo` | `BOARD.md` (live), `journal/<YYYY-MM>/<DD>.md` (daily), `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/` | Execution stewardship: standup ritual, task triage, agent delegation, status reports, cadence rituals, monthly rollover |
| **`design`** | `/design` | `design/<DESIGN-ID>-<slug>.md` | Design-doc stewardship: RFC drafting, user-decision tables, lock workflow, hand-off of implementation tasks to PMO |

## The hand-off contract (the most important rule)

- `okr` is the **only writer** of `OKR.md` and `monthly/`. It **proposes** weekly tasks but never writes them.
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

−1. **Detect host once** — silently:
   ```
   bash "${PERRY_HOME:-$HOME/.claude/skills/perry}/bin/perry-detect-host"
   ```
   Output: `claude-code` | `codex-cli` | `unknown`. Remember as `$HOST` for the rest of the conversation. Then read `${PERRY_HOME:-$HOME/.claude/skills/perry}/reference/host-capabilities.md` for fallback rules. If output is `unknown`, default `$HOST=claude-code` but tell the user once and recommend setting `PERRY_HOST` in their shell profile.

0. **Run the weekly auto-update check** — silently in the background:
   ```
   bash "${PERRY_HOME:-$HOME/.claude/skills/perry}/bin/perry-update-check"
   ```
   The script throttles itself to once per 7 days; most invocations exit immediately with no output. When it does run, output is one line (or zero). Surface its output to the user verbatim if non-empty (the user wants to know about updates), then continue with the snapshot.

1. **Read `.perry/config.md`** if present, to pick up document language and repo layout. If absent and any state file exists, prompt the user to run first-time setup so the config is recorded.

2. **Detect installation state**:
   - `OKR.md` exists? `monthly/<current-YYYY-MM>.md` exists? `BOARD.md` exists? `journal/<current-YYYY-MM>/` non-empty? `evidence/<current-YYYY-MM>/` exists? `design/` non-empty? `handoff/` non-empty?
   - If none of these exist → jump to **First-time setup** below.
   - If only some exist → flag the missing pieces.

2. **Render the combined dashboard** — exactly this shape, no preamble:

   ```
   🅿  Perry · <project name> · <today's date>

   🎯 OKR (vN, <period>) · <days_elapsed>/<days_total>d
      O1 · <title> ............ <%>
      O2 · <title> ............ <%>
      O3 · <title> ............ <%>          (omit unused Os)

   📅 This month (<YYYY-MM>, week <n>/<weeks_in_month>) · cost <spent>/<ceiling>
      M-O1 · <title> .......... <KRs done>/<KRs total>
      M-O2 · <title> .......... <KRs done>/<KRs total>

   📋 Open tasks  : P0=<n>(<done>/<total>) · P1=<n> · P2=<n> · blocked=<n>
   ⏳ User Input Q: <pending count> · oldest: <USER-id> @ <days idle>d
   🚧 Top risk    : <risk title, ≤80 chars>
   📝 Last decision: <ADR title> (<date>)
   📅 Last weekly : <YYYY-WW>, <days>d ago · last handoff: <date>, <days>d ago
   ```

   Use `—` for empty fields. Never fabricate values.

3. **Suggest 1–3 next actions** combining OKR, PMO, and design concerns:
   - "month-end in 3 days → run `/pmo end-month-retro`, then `/okr score`, then `/pmo rollover`, then `/okr plan-month`"
   - "USER-014 idle 6d, weekly is 8d old → run `/pmo nudge` then `/pmo friday-review`"
   - "no monthly OKR for current month → run `/okr plan-month`, then `/okr plan-week`, then `/pmo` to add the tasks"
   - "DESIGN-002 in_review for 8d → run `/design lock` or `/design revise`"

4. Then ask: **"What do you want to do?"**

If the user picks an OKR-flavored action (plan, score, pivot, revise), invoke the `okr` skill. If a PMO-flavored action (triage, status, delegate, handoff, rollover, decide, risk), invoke `pmo`. If a design-flavored action (RFC, architecture, lock, supersede), invoke `design`. If unclear, ask which, then route.

## First-time setup

When `/perry` is run in a project with no Perry state files at all:

1. Briefly explain Perry (≤3 sentences).
2. **Confirm two project-wide preferences before any file is written** — record both in `.perry/config.md` (create the file if missing) so every subsequent session and every child skill reads from one source. Ask both via a single `AskUserQuestion` tool call (two questions, structured options):
   - **Document language** (header `"Language"`): options = `English (Recommended if user typed English) | 中文 (Recommended if user typed 中文) | other`. The "Recommended" tag goes on whichever matches the user's recent chat language.
   - **Repo layout** (header `"Repo layout"`): options = `Single repo (Recommended for non-code projects) | Split repo (PMO ↔ code; only if both exist and you've seen branch contention)`. See **Repo layout options** below for the trade-off explanation that goes into each option's `description`.

   All subsequent skill output (snapshots, dashboards, generated docs, delegation prompts) uses the configured language. If the user mixes languages later, keep using the configured language for written artifacts but mirror the user's language in chat replies.
3. Recommend the order:
   - First, run `/okr init` — interview to create `OKR.md` (mission, Operating Principles, 1–3 Objectives + KRs, Anti-Goals, version v1).
   - Then, run `/okr plan-month <YYYY-MM>` — creates the monthly OKR with all 10 mandatory sections.
   - Then, run `/pmo` — bootstraps the execution files (`BOARD.md`, `journal/<current-YYYY-MM>/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`) and runs the first standup.
   - Finally, run `/okr plan-week` — proposes the first batch of weekly tasks, which `/pmo` then writes as BOARD rows + a journal entry under `## New tasks added`.
4. Ask: "Run `/okr init` now?" — if yes, invoke the `okr` skill. If no, stop and let the user proceed at their own pace.

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
- PMO repo path: <absolute path>
- Code repo path: <absolute path or — if single>
- Last updated: <YYYY-MM-DD>
```

Children read this file before any output. If the file is missing, prompt the user to run first-time setup.

## Routing reference

When the user types something inside a `/perry` session, route to the right child rather than answering ad-hoc.

**Route to `/okr` for:**
- Setting or revising goals · `init`, `revise`, `pivot`
- Monthly planning · `plan-month`, `score`, `dashboard`
- Weekly task proposals · `plan-week` (the hand-off step)
- Anything about Operating Principles, Anti-Goals, OKR versions, Cost Ceiling, KR scoring

**Route to `/pmo` for:**
- The standup itself, status, triage, blocker check
- Task lifecycle · `add-task`, `close-task`, `drop-task`
- Cadence rituals · `monday-plan`, `midweek-check`, `friday-review`, `mid-month-review`, `end-month-retro`
- Cross-session work · `coordinate`, `delegate` (manual prompt), `dispatch` (auto end-to-end via claude-subagent or codex), `handoff`
- Decisions and risks · `decide`, `risk`, `nudge`
- Monthly transition · `rollover`

**Route to `/design` for:**
- Anything called RFC / architecture / design doc · `new`, `decide`, `lock`, `revise`, `supersede`, `drop`, `handoff`, `status`
- "Should we design this before building it?" → yes if multi-system, irreversible, or has multiple open user decisions

**Handle here in `/perry` (without routing):**
- The combined snapshot itself.
- "Explain Perry" / "what is this skill" — short pointer to README.
- Recommending the next action when the choice spans more than one child.
- Confirming or updating `.perry/config.md` (document language, repo layout).
- `help` — see below.

## `/perry help [<child>]`

Without arg: print a compact overview of the three children + when to use each + a pointer to each child's own `help`. This is the navigation entry point for users who don't know what's available yet.

Suggested format:

```
Perry — virtual project office (3 invocable skills)

  /okr      Goal-setting (overall + monthly OKR + weekly task proposals)
            Use when: setting goals, planning the month, scoring KRs,
            pivoting strategy.
            Common: /okr init, plan-month, plan-week, score, dashboard
            Full list: /okr help

  /pmo      Execution stewardship (BOARD, journal, dispatch, cadence)
            Use when: standup, planning the week, delegating to agents,
            tracking blockers, writing weekly status, monthly rollover.
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
            Common: /perry, /perry help

First-time setup: /perry in a new project → confirms language + repo layout.
Read more: ${PERRY_HOME:-~/.claude/skills/perry}/README.md
```

With arg `okr`, `pmo`, or `design`: route to that child's `help` subcommand (the children own the detail). Don't re-render their tables here.

`help` does NOT trigger the combined snapshot ritual.

## Style rules

- **Lead with the dashboard, not narration.**
- **Numbers, IDs, file paths.** Not paragraphs.
- **Cite the file** for every claim.
- **Never invent state.** Print `—` and ask.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.

## User-prompt convention (AskUserQuestion)

Whenever a Perry skill (top-level or any child) needs the user to make a choice with **2–4 distinct options**, prefer the `AskUserQuestion` tool over free-text "what do you want?" prompts. The Claude Code / Desktop UI renders `AskUserQuestion` as clickable button choices with an automatic "Other" free-text fallback — much faster for the user than typing.

> **Codex host**: `AskUserQuestion` is not available. Render the same option set as a numbered free-text prompt per `reference/host-capabilities.md § AskUserQuestion → numbered free-text prompt`. The chosen value, downstream writes, and conventions below are unchanged — only the rendering differs.

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
- Throttles itself to **once per 7 days** via `${PERRY_HOME:-$HOME/.claude/skills/perry}/.update-check` mtime; most invocations exit immediately with no output.
- Detects "dev mode" — symlink install, dirty working tree, or non-`main` branch — and in that case **only fetches and reports**; it never auto-pulls (so it can't trample your WIP if you're editing Perry source).
- For "consumer mode" (real directory, clean tree, on `main`), does an ff-only `git pull` from `origin/main`.
- Always exits 0 (network failure, unresolved merge, etc. → notify and continue; never block the standup).

Manual trigger: `bash "${PERRY_HOME:-$HOME/.claude/skills/perry}/bin/perry-update-check" --force` (bypasses throttle).

The script is invoked from the standup ritual of every child (`okr` / `pmo` / `design`), so triggering any of `/perry`, `/okr`, `/pmo`, `/design` covers it. If the skill source is not a git checkout (e.g., extracted from a tarball), the check exits silently.

## See also

- [README.md](../README.md) — full overview, file layout, design rationale.
- [INSTALL.md](../INSTALL.md) — install instructions.
- [okr/SKILL.md](okr/SKILL.md) — full goal-setting subcommands and templates.
- [pmo/SKILL.md](pmo/SKILL.md) — full execution stewardship subcommands and templates.
- [design/SKILL.md](design/SKILL.md) — full design-doc stewardship subcommands and templates.
