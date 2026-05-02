# Perry — your virtual project office

> *Perry runs the office. You run the project.*

A two-skill set for Claude Code that captures the "virtual PMO + OKR steward" workflow so you don't have to re-instruct it every session.

## What Perry does

Perry pairs **goal-setting** with **execution stewardship** so a solo or small project gets the structure it needs without the bureaucracy that usually comes with it. Two skills, one mental model:

| Skill | Role | Owns | Reads from peer |
|-------|------|------|------------------|
| **`okr`** | The "why" — goal-setting partner | `OKR.md` (versioned, with Operating Principles + Anti-Goals), `monthly/<YYYY-MM>.md` (Focus, Rules, Cost Ceiling, User Commitments, Degradation, Scope Reduction, Objectives, DoD, Not Doing) | `TASKS.md`, `evidence/<YYYY-MM>/retro.md` |
| **`pmo`** | The "how" — execution steward | `TASKS.md` (rich task blocks, User Input Queue, Cadence, Change Log), `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/<YYYY-MM>/`, `weekly/<YYYY-WW>.md`, `handoff/<YYYY-MM-DD>.md` | `OKR.md`, `monthly/<YYYY-MM>.md` |

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
                                  └──────────────────────────┘    │  TASKS.md (rich block) │
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
- `pmo` **writes** `TASKS.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`. **Reads** OKR files for context.
- Each skill reads the other's files freely; neither writes outside its lane.

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

/pmo        → (auto) appends rich task blocks to TASKS.md, runs standup
... daily work ... /pmo close-task ... /pmo decide ... /pmo delegate <id> ...
/pmo        → friday-review                  # writes weekly/<YYYY-WW>.md
/pmo        → handoff                        # writes handoff/<today>.md before stopping

/pmo        → mid-month-review               # mid-month, applies scope-reduction if armed
/pmo        → end-month-retro                # at month-end, writes evidence/<YYYY-MM>/retro.md

/okr        → score <YYYY-MM>                # consumes the retro, fills monthly file's Retro section
/pmo        → rollover                       # archives previous month, hands off to OKR
/okr        → plan-month <next>              # next month begins
```

## Project file layout (after both skills bootstrap)

```
<project_root>/
├── OKR.md                              ← okr (overall, versioned)
├── monthly/
│   └── 2026-05.md                       ← okr (this month, full schema)
├── TASKS.md                             ← pmo (board)
├── PROJECT_STATE.md                     ← pmo (cross-monthly dashboard)
├── DECISIONS.md                         ← pmo (ADR log)
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
