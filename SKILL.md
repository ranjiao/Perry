---
name: perry
description: Perry — your virtual project office. A two-skill set that pairs goal-setting (okr) with execution stewardship (pmo) for solo or small projects. Use /perry for a combined snapshot of where the project is, or invoke /okr and /pmo directly for specific subcommands. okr owns OKR.md (versioned, with Operating Principles + Anti-Goals) and monthly/<YYYY-MM>.md. pmo owns TASKS.md, PROJECT_STATE.md, DECISIONS.md, evidence/<YYYY-MM>/, weekly/<YYYY-WW>.md, handoff/<YYYY-MM-DD>.md. They cooperate through file ownership; neither writes outside its lane.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry is a coordinated **skill set** with two children that share a project's state files at the project root. This top-level skill is the entry point: a combined snapshot, a brief intro for new users, and a router to whichever child you actually want.

## Children of this skill

This folder contains two child skills. They live under `~/.claude/skills/perry/<child>/SKILL.md` and are invocable on their own. Read each child's SKILL.md for full subcommand detail.

| Child | Invoke as | Owns | What it does |
|-------|-----------|------|--------------|
| **`okr`** | `/okr` | `OKR.md`, `monthly/<YYYY-MM>.md` | Goal-setting: overall versioned OKR, monthly OKR with 10 mandatory sections, weekly task proposals (handed off to PMO) |
| **`pmo`** | `/pmo` | `TASKS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/` | Execution stewardship: standup ritual, task triage, agent delegation, status reports, cadence rituals, monthly rollover |

## The hand-off contract (the most important rule)

- `okr` is the **only writer** of `OKR.md` and `monthly/`. It **proposes** weekly tasks but never writes them.
- `pmo` is the **only writer** of `TASKS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`. It **reads** OKR files for context.
- Each skill reads the other's files freely; neither writes outside its lane.

This single rule is what keeps the set composable and lets you drop in a third child later (e.g., `research-journal`, `risk-review`) without breakage.

## When this skill activates

Trigger on any of:
- The user invokes `/perry` or types "Perry".
- The user opens a session and wants a "where are we" overview without specifying OKR vs PMO.
- The user is new to Perry and asks how it works or what to do first.
- A new session opens in a project that contains both `OKR.md` and `TASKS.md` and the user wants the combined view.

If the user clearly wants only goal-setting → route to `/okr`. If clearly only execution → route to `/pmo`. The coordinator is for the cases in between.

## Mandatory first move: combined snapshot

When `/perry` is invoked, always run this before doing anything else.

1. **Detect installation state**:
   - `OKR.md` exists? `monthly/<current-YYYY-MM>.md` exists? `TASKS.md` exists? `evidence/<current-YYYY-MM>/` exists? `handoff/` non-empty?
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

3. **Suggest 1–3 next actions** combining OKR and PMO concerns:
   - "month-end in 3 days → run `/pmo end-month-retro`, then `/okr score`, then `/pmo rollover`, then `/okr plan-month`"
   - "USER-014 idle 6d, weekly is 8d old → run `/pmo nudge` then `/pmo friday-review`"
   - "no monthly OKR for current month → run `/okr plan-month`, then `/okr plan-week`, then `/pmo` to add the tasks"

4. Then ask: **"What do you want to do?"**

If the user picks an OKR-flavored action (plan, score, pivot, revise), invoke the `okr` skill via the Skill tool. If a PMO-flavored action (triage, status, delegate, handoff, rollover, decide, risk), invoke `pmo`. If unclear, ask which, then route.

## First-time setup

When `/perry` is run in a project with no Perry state files at all:

1. Briefly explain Perry (≤3 sentences).
2. Recommend the order:
   - First, run `/okr init` — interview to create `OKR.md` (mission, Operating Principles, 1–3 Objectives + KRs, Anti-Goals, version v1).
   - Then, run `/okr plan-month <YYYY-MM>` — creates the monthly OKR with all 10 mandatory sections.
   - Then, run `/pmo` — bootstraps the execution files (`TASKS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`) and runs the first standup.
   - Finally, run `/okr plan-week` — proposes the first batch of weekly tasks, which `/pmo` then writes to `TASKS.md`.
3. Ask: "Run `/okr init` now?" — if yes, invoke the `okr` skill. If no, stop and let the user proceed at their own pace.

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
- Cross-session work · `coordinate`, `delegate`, `handoff`
- Decisions and risks · `decide`, `risk`, `nudge`
- Monthly transition · `rollover`

**Handle here in `/perry` (without routing):**
- The combined snapshot itself.
- "Explain Perry" / "what is this skill" — short pointer to README.
- Recommending the next action when the choice spans both children.

## Style rules

- **Lead with the dashboard, not narration.**
- **Numbers, IDs, file paths.** Not paragraphs.
- **Cite the file** for every claim.
- **Never invent state.** Print `—` and ask.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.

## Per-project hooks (optional)

If your project has specific roadmap files, MCP tools, agent roles, cost ceilings, or promotion stages, add a hook block to **the children's** `SKILL.md` files (`okr/SKILL.md` and `pmo/SKILL.md` each have a `## Per-project hooks` section). The top-level Perry skill stays project-agnostic.

## See also

- [README.md](../README.md) — full overview, file layout, design rationale.
- [INSTALL.md](../INSTALL.md) — install instructions.
- [okr/SKILL.md](okr/SKILL.md) — full goal-setting subcommands and templates.
- [pmo/SKILL.md](pmo/SKILL.md) — full execution stewardship subcommands and templates.
