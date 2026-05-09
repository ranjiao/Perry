# Perry — your virtual project office

> *Perry runs the office. You run the project.*

A three-skill set for **Claude Code** and **Codex CLI** that captures the "virtual PMO + OKR + RFC steward" workflow so you don't have to re-instruct it every session.

## 🚀 One-paste install (Claude Code)

Copy the prompt below and paste it into a fresh Claude Code session. Claude will clone Perry into `~/.claude/skills/perry/` and verify that `/perry`, `/okr`, and `/pmo` are available.

```
Install the Perry Claude skill from https://github.com/ranjiao/Perry

Steps:
1. Run: mkdir -p ~/.claude/skills && git clone https://github.com/ranjiao/Perry.git ~/.claude/skills/perry
2. Verify the layout matches https://raw.githubusercontent.com/ranjiao/Perry/main/INSTALL.md
3. Confirm /perry, /okr, and /pmo are now available as slash commands.
```

> Already have Perry installed? Update with:
> `cd ~/.claude/skills/perry && git pull`

## 🚀 Install (Codex CLI)

Codex CLI uses the same `SKILL.md` frontmatter format as Claude Code, just from a different skills directory ([per the Codex Skills docs](https://developers.openai.com/codex/skills)): `~/.agents/skills/`. The same `setup` script handles both hosts:

```bash
git clone https://github.com/ranjiao/Perry ~/proj/Perry
~/proj/Perry/setup --codex          # installs to BOTH ~/.claude/skills/ AND ~/.agents/skills/
```

After install, inside `codex` invoke Perry via `/skills` (pick perry / okr / pmo / design), `$perry` / `$okr` / `$pmo` / `$design` (explicit mention), or just describe the task and let Codex match the description. See [INSTALL.md § Codex CLI](INSTALL.md#codex-cli) for verification + per-host fallbacks (free-text prompts replace `AskUserQuestion`, `Executor: claude-subagent` is refused, async dispatch uses shell `&`).

## What Perry does

Perry pairs **goal-setting** with **execution stewardship** and **design-doc stewardship** so a solo or small project gets the structure it needs without the bureaucracy that usually comes with it. Three skills, one mental model:

| Skill | Role | Owns | Reads from peer |
|-------|------|------|------------------|
| **`okr`** | The "why" — goal-setting partner | `OKR.md` (versioned, with Operating Principles + Anti-Goals), `monthly/<YYYY-MM>.md` (Focus, Rules, Cost Ceiling, User Commitments, Degradation, Scope Reduction, Objectives, DoD, Not Doing) | `BOARD.md`, `evidence/<YYYY-MM>/retro.md` |
| **`pmo`** | The "how" — execution steward | `BOARD.md` (live working memory, ≤200 lines), `journal/<YYYY-MM>/<YYYY-MM-DD>.md` (daily history, append-only), `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/<YYYY-MM>/`, `weekly/<YYYY-WW>.md`, `handoff/<YYYY-MM-DD>.md` | `OKR.md`, `monthly/<YYYY-MM>.md` |
| **`design`** | The "decided" — RFC steward | `design/<DESIGN-ID>-<slug>.md` (Problem, Goals, Non-Goals, User Decisions, Architecture, Implementation plan, Risks, Changes) | `OKR.md`, `monthly/<YYYY-MM>.md`, `BOARD.md` |

Both skills run a mandatory snapshot/standup the moment they're invoked, so you always start from the actual state of your files instead of vibes.

## How they cooperate

```
   ┌────────────────────────┐    ┌──────────────────────────┐    ┌────────────────────────┐
   │  OKR.md (versioned)    │ →  │  monthly/<YYYY-MM>.md     │ →  │ Weekly task proposals  │
   │  Operating Principles  │    │  Month Focus              │    │ tagged with KR ids,    │
   │  Anti-Goals            │    │  Operating Rules          │    │ Owner, Priority, DoD   │
   │  1–3 Objectives, KRs   │    │  Cost Ceiling             │    │                        │
   │                        │    │  User Commitments         │    └─────────┬──────────────┘
   └────────────────────────┘    │  Degradation rule         │              │ user approval
                                  │  Scope Reduction rule    │              ▼
                                  │  Definition of Done      │    ┌────────────────────────┐
                                  │  Not Doing               │    │  PMO appends to        │
                                  └──────────────────────────┘    │  BOARD + journal entry   │
                                                                  │  · runs standup        │
                                                                  │  · triages weekly      │
                                                                  │  · delegates to agents │
                                                                  │  · writes evidence/    │
                                                                  │  · publishes weekly/   │
                                                                  │  · writes handoff/     │
                                                                  └────────────────────────┘
```

**The hand-off rule (the most important contract):**
- `okr` **writes** `OKR.md` and `monthly/`. **Proposes** weekly tasks; never writes them.
- `pmo` **writes** `BOARD.md`, `journal/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`. **Reads** OKR and design files for context.
- `design` **writes** `design/<DESIGN-ID>-<slug>.md`. **Proposes** implementation tasks on lock; never writes them.
- Each skill reads the others' files freely; no skill writes outside its lane.

## Key concepts

**Status model (PMO):** `not_started · blocked · in_progress · review · done · dropped`. A task may not be marked `done` without an evidence file under `evidence/<YYYY-MM>/<TASK-ID>-*.md` or a citable artifact (commit hash, command output, dashboard route).

**Owner model (PMO):** `User · PMO Agent · Coding Agent · Research Agent · Review Agent · User + Agent`. The set is explicit so the PMO can write proper delegation prompts to other Claude sessions; user-only decisions are first-class items in the User Input Queue.

**Cadence (PMO):** Monday Planning → Midweek Check → Friday Review → Mid-Month Review → End-Month Retro. Each is a subcommand. Cadence work is tracked under `## Cadence` and does not consume P0 capacity.

**Evidence-required (PMO):** Every `done` claim points to a real artifact. "Looks good", "Should work", and "Agent thinks it is done" are explicitly rejected.

**Versioning (OKR):** `OKR.md` accumulates `## v1`, `## v2`, etc. with dates. `okr revise` appends a new version; old versions stay readable. Pivots are paid in friction, not silent edits.

**Anti-Goals (OKR):** First-class commitments at both overall and monthly cadence. Every retro checks if any were violated.

**Cost Ceiling (OKR monthly):** Numbers + soft fallback threshold + hard cap + wiring status (`wired in code` vs `doc-only`). Doc-only ceilings are flagged as open risks every snapshot until they're wired.

**Handoff doc (PMO):** `handoff/<YYYY-MM-DD>.md` is the bridge between sessions. The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc replaces having to scroll back through chat.

## Typical flow (first time, any project)

```
/okr        → init                          # interview: mission, Operating Principles,
                                              # 1–3 Objectives + KRs, Anti-Goals, version v1
/okr        → plan-month <YYYY-MM>          # full monthly OKR with all 10 mandatory sections
/okr        → plan-week                      # proposes 3–5 candidate tasks for this ISO week
                                              # user approves a subset

/pmo        → (auto) writes BOARD rows + full task definitions to journal/<YYYY-MM>/<today>.md, runs standup
... daily work ... /pmo close-task ... /pmo decide ... /pmo delegate <id> ...
/pmo        → friday-review                  # writes weekly/<YYYY-WW>.md
/pmo        → handoff                        # writes handoff/<today>.md before stopping

/pmo        → mid-month-review               # mid-month, applies scope-reduction if armed
/pmo        → end-month-retro                # at month-end, writes evidence/<YYYY-MM>/retro.md

/okr        → score <YYYY-MM>                # consumes the retro, fills monthly file's Retro section
/pmo        → rollover                       # archives previous month, hands off to OKR
/okr        → plan-month <next>              # next month begins
```

## Project file layout (after all skills bootstrap)

```
<project_root>/
├── .perry/
│   ├── config.md                       ← language + repo layout (single | split)
│   └── hook.md                         ← project-specific additions (optional)
├── OKR.md                              ← okr (overall, versioned)
├── monthly/
│   └── 2026-05.md                       ← okr (this month, full schema)
├── BOARD.md                             ← pmo (LIVE working memory; ≤200 lines; closed tasks leave)
├── journal/
│   └── 2026-05/
│       ├── 2026-05-01.md                ← pmo (day's status changes / new tasks / decisions)
│       ├── 2026-05-02.md
│       └── ...                          ← one file per day; append-only after the day ends
├── PROJECT_STATE.md                     ← pmo (cross-monthly dashboard)
├── DECISIONS.md                         ← pmo (ADR log, all months)
├── design/
│   └── DESIGN-001-process-mgmt.md       ← design (RFC)
├── evidence/
│   └── 2026-05/
│       ├── TASK-001-deliverable-name.md       ← pmo (per-task artifact)
│       ├── midmonth-review.md
│       └── retro.md                            ← consumed by okr `score`
├── weekly/
│   └── 2026-W18.md                      ← pmo (status report)
├── handoff/
│   └── 2026-05-01.md                    ← pmo (session bridge)
└── ... (your actual project files)
```

## Designing your own skills on top

Perry was built so you can extend it without breaking the core. Some natural additions:

- **`research-journal`** — owns `RESEARCH.md`; consumes a domain MCP; feeds findings to OKR pivots.
- **`risk-review`** — runs periodic checks via a domain MCP; raises P0 tasks via PMO when something trips.
- **`experiment-runner`** — coordinates batch jobs in a sub-session; reports KR-relevant numbers back to OKR.

Rule for adding a new skill to the family: declare the files you own and the files you only read in your `description:` frontmatter, and never write to files owned by another skill. That single discipline is what makes the set scale past two members.

## Origin

Perry was abstracted from a real workflow: someone was using a single long-running Claude Code conversation as a "virtual PMO" for a personal project, accumulating an OKR doc, a monthly OKR, a TODO board, an evidence folder, and a daily handoff doc by hand. The pattern worked, but it relied entirely on the user remembering to feed the right files to each new session. Perry's standup ritual, evidence-required completion, agent owner model, cadence rituals, and handoff doc are the abstraction of what made that workflow work — packaged so anyone can adopt it without reverse-engineering the pattern.
