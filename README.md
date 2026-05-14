# Perry — your virtual project office

> *Perry runs the office. You run the project.*

A three-skill set for **Claude Code** and **Codex CLI** that captures the "virtual PMO + OKR + RFC steward" workflow so you don't have to re-instruct it every session.

## 🚀 One-paste install

`setup` auto-detects which agent host(s) you have (`claude` and/or `codex` in PATH) and installs Perry for whichever it finds. No flag needed if you only use one of them.

### Paste into a fresh Claude Code or Codex CLI session

```
Install the Perry skill set from https://github.com/ranjiao/Perry.

Steps:
1. Run: mkdir -p ~/proj && git clone https://github.com/ranjiao/Perry.git ~/proj/Perry && ~/proj/Perry/setup --yes-deps
2. Read setup's output. If it lists "Skipped installs" or asks for Xcode CLT / Homebrew, surface those to me as TODOs — those need my consent (GUI / sudo).
3. Confirm /perry, /okr, /pmo, /design are available.
```

The agent's Bash tool isn't a TTY, so `setup` automatically switches to **auto-skip mode** — runs the dep check, surfaces what's missing, but won't block on Y/N prompts or sudo passwords. Adding `--yes-deps` opts into auto-installing what's installable non-interactively. Items that need GUI (Xcode CLT) or sudo (Homebrew) are listed as TODOs at the end for the user to handle.

> Already have Perry installed? Update with:
> `cd ~/proj/Perry && git pull`

### Host selection

| Command | What gets installed |
|---|---|
| `~/proj/Perry/setup` | Auto-detect: install for whichever of `claude` / `codex` is in PATH. Both → both. Neither → fail with options. |
| `~/proj/Perry/setup --claude` | Force install for Claude Code only (`~/.claude/skills/`). |
| `~/proj/Perry/setup --codex` | Force install for Codex CLI only (`~/.agents/skills/`). |
| `~/proj/Perry/setup --claude --codex` | Install for both regardless of detection. |

See **[INSTALL.md](INSTALL.md)** for the agent-driven install flow, the fresh-Mac dependency matrix (Xcode CLT / Homebrew / Node / etc.), and per-host fallbacks for Codex (free-text prompts replace `AskUserQuestion`, async dispatch uses shell `&`, etc.).

## What Perry does

Perry pairs **goal-setting** with **execution stewardship** and **design-doc stewardship** so a solo or small project gets the structure it needs without the bureaucracy that usually comes with it. Three skills, one mental model:

| Skill | Role | Owns | Reads from peer |
|-------|------|------|------------------|
| **`okr`** | The "why" — goal-setting partner | `OKR.md` (versioned, with Operating Principles + Anti-Goals), `phase/<NNN>-<slug>.md` (current phase OKR — NOT calendar-bound; Focus, Rules, Cost Ceiling, User Commitments, Degradation, Scope Reduction, Objectives, DoD, Not Doing), `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md` (auto + manual snapshots) | `BOARD.md`, `evidence/<YYYY-MM>/retro.md` |
| **`pmo`** | The "how" — execution steward | `BOARD.md` (live working memory, ≤200 lines), `journal/<YYYY-MM>/<YYYY-MM-DD>.md` (daily history, append-only), `PROJECT_STATE.md`, `DECISIONS.md` (index) + `decisions/ADR-NNN-<slug>.md` (per-decision ADR files), `evidence/<YYYY-MM>/`, `weekly/<YYYY-WW>.md`, `handoff/<YYYY-MM-DD>.md`, `inputs/` + `knowledge/<topic>/` (external-doc digests) | `OKR.md`, `phase/<NNN>-<slug>.md` |
| **`design`** | The "decided" — RFC steward | `design/<DESIGN-ID>-<slug>.md` (Problem, Goals, Non-Goals, User Decisions, Architecture, Implementation plan, Risks, Changes) | `OKR.md`, `phase/<NNN>-<slug>.md`, `BOARD.md` |

Both skills run a mandatory snapshot/standup the moment they're invoked, so you always start from the actual state of your files instead of vibes.

## How they cooperate

```
   ┌────────────────────────┐    ┌──────────────────────────┐    ┌────────────────────────┐
   │  OKR.md (versioned)    │ →  │ phase/<NNN>-<slug>.md     │ →  │ Weekly task proposals  │
   │  Operating Principles  │    │  Phase Focus              │    │ tagged with KR ids,    │
   │  Anti-Goals            │    │  Operating Rules          │    │ Owner, Priority, DoD   │
   │  1–3 Objectives, KRs   │    │  Cost Ceiling             │    │                        │
   │                        │    │  User Commitments         │    └─────────┬──────────────┘
   └────────────────────────┘    │  Degradation rule         │              │ user approval
                                  │  Scope Reduction rule    │              ▼
                                  │  Definition of Done      │    ┌────────────────────────┐
                                  │  Not Doing               │    │  PMO appends to        │
                                  │  (NOT calendar-bound;    │    │  BOARD + journal entry │
                                  │   phase ends on KRs hit) │    │                        │
                                  └──────────────────────────┘    │
                                                                  │  · runs standup        │
                                                                  │  · triages weekly      │
                                                                  │  · delegates to agents │
                                                                  │  · writes evidence/    │
                                                                  │  · publishes weekly/   │
                                                                  │  · writes handoff/     │
                                                                  └────────────────────────┘
```

**The hand-off rule (the most important contract):**
- `okr` **writes** `OKR.md` and `phase/`. **Proposes** weekly tasks; never writes them.
- `pmo` **writes** `BOARD.md`, `journal/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`. **Reads** OKR and design files for context.
- `design` **writes** `design/<DESIGN-ID>-<slug>.md`. **Proposes** implementation tasks on lock; never writes them.
- Each skill reads the others' files freely; no skill writes outside its lane.

## Key concepts

**Status model (PMO):** `not_started · blocked · in_progress · review · done · dropped`. A task may not be marked `done` without an evidence file under `evidence/<YYYY-MM>/<TASK-ID>-*.md` or a citable artifact (commit hash, command output, dashboard route).

**Owner model (PMO):** `User · PMO Agent · Coding Agent · Research Agent · Review Agent · User + Agent`. The set is explicit so the PMO can write proper delegation prompts to other Claude sessions; user-only decisions are first-class items in the User Input Queue.

**Cadence (PMO):** Monday Planning → Midweek Check → Friday Review → Mid-Phase Review → End-Phase Retro. Each is a subcommand. Cadence work is tracked under `## Cadence` and does not consume P0 capacity.

**Evidence-required (PMO):** Every `done` claim points to a real artifact. "Looks good", "Should work", and "Agent thinks it is done" are explicitly rejected.

**Versioning (OKR):** `OKR.md` accumulates `## v1`, `## v2`, etc. with dates. `okr revise` appends a new version; old versions stay readable. Pivots are paid in friction, not silent edits.

**Anti-Goals (OKR):** First-class commitments at both overall and phase cadence. Every retro checks if any were violated.

**Cost Ceiling (OKR per phase or overall):** Numbers + soft fallback threshold + hard cap + wiring status (`wired in code` vs `doc-only`). Doc-only ceilings are flagged as open risks every snapshot until they're wired.

**Handoff doc (PMO):** `handoff/<YYYY-MM-DD>.md` is the bridge between sessions. The first line of every PMO session after a handoff exists is: "Read `handoff/<latest>.md` and tell me your status." The handoff doc replaces having to scroll back through chat.

**External-doc digests (PMO):** `inputs/` is the raw drop zone for PDFs / Excels / screenshots / pasted text the user hands PMO. `/pmo digest <path>` reads the source, drafts a structured summary (TL;DR + Key facts with citations + Open questions + What PMO must remember + Section map), verifies key facts with the user via `AskUserQuestion`, then moves both source and digest into `knowledge/<topic>/`. Subsequent specs / decisions / journal cite the digest by path instead of re-reading the source. Digests carry a `Status: active | eternal | archived | superseded` field; archive review runs automatically inside `mid-phase-review` and `end-phase-retro`. **Bounded scope** — design target is 5–30 active digests per project; this is human-style note-taking, not RAG. See `pmo/reference/digests.md` for the full spec.

**Decisions split (PMO):** `DECISIONS.md` at the project root is **an index only** (≤200 lines): a table of all ADRs with ID / Title / Type / Date / Status + link to the per-decision file. The full reasoning lives in `decisions/ADR-NNN-<slug>.md` — one file per ADR with Context / Options / Chosen / Consequences / Evidence / Sunset criteria. `/pmo decide <topic>` creates new ADRs in the configured document language; `--supersede` / `--expire` / `--archive` manage the lifecycle (files never move on status change, only header flips). Standup reads index-only — per-decision content loaded on demand. Same scaling pattern as BOARD.md vs `journal/`. See `pmo/reference/decisions.md`.

**Autopilot (PMO):** `/pmo autopilot` walks BOARD top-to-bottom and dispatches every safe-to-dispatch row until budget exhausts (default 10 dispatches / 2h / 3 failures). First run per project is forced dry-run + briefing. Hard safety rails: never auto-`done`, never modify specs, never override hook safety list, never auto-retry. Stop signals: close session OR `touch ~/.cache/perry/autopilot.stop`. See `pmo/reference/autopilot.md`.

**Anti-drift discipline — ARCHITECTURE.md / runbooks / incidents (PMO):** When agents write the code, the user loses both architectural grip and operational grip. Perry's countermeasures (all **optional, lazy-created** — they materialise on first use, not at bootstrap):

- **`ARCHITECTURE.md` (the central one)** — a single, user-owned, agent-read-only document at project root. Fixed 8-section structure (Mission & scope / Components / Boundaries & dependencies / Data flow / Contracts / Non-negotiables / Open questions / Change log). Every dispatched agent gets the full document injected into its prompt and must produce an `ARCHITECTURE COMPLIANCE` attestation listing touched §-sections. Before `close-task` can flip to `done`, an **independent review agent** (separate Claude subagent or codex call) reads the same document plus the diff and adversarially rebuts the primary agent's attestation — `PASS` or `FAIL`. `close-task` refuses on `FAIL`. This is the guarantee mechanism: an architecture-touching task cannot close without the doc-vs-diff consistency check passing. The cost is one extra small LLM call per dispatch. See `pmo/reference/architecture.md`.
- **`runbook/<component>.md`** — one file per deployed component, four mandatory sections (What it does / How to tell it's healthy / Common failures + canned ops / Escalation). Task specs declare `Deployed: yes | no`; `close-task` refuses to close a `Deployed: yes` task without a matching runbook. See `pmo/reference/runbooks.md`.
- **`incidents/<YYYY-MM-DD>-<slug>.md`** — postmortem record per production failure. `/pmo incident close` enforces a 3-question gate (Knowledge / **Architecture** / Runbook): each question must produce a concrete artifact OR an explicit skip-with-reason. The "Architecture" question asks whether the incident reveals that `ARCHITECTURE.md` is wrong, missing, or out of date. See `pmo/reference/incidents.md`.
- **`/pmo health-check`** — meta-runner that composes `architecture-audit` + `runbook-check` + digest stale + incident patterns into one report at `evidence/<YYYY-MM>/health-check-<date>.md`. Called inline by `mid-phase-review` and `end-phase-retro`. See `pmo/reference/health-check.md`.

These four work together: `ARCHITECTURE.md` is the user-controlled spine; incidents reveal where the spine is wrong; runbooks keep the user able to operate without reading agent-written code; health-check is the periodic reality check. None of them is mandatory, but each is a contract Perry uses to keep an agent-built project under user control.

**OKR cross-phase firewall:** `okr plan-phase` reads the latest `architecture/audit-history/<date>.md` and `ARCHITECTURE.md § Open questions`. It refuses to write the new phase's OKR until every unresolved drift item is explicitly addressed — resolve as a KR, accept by editing `ARCHITECTURE.md`, defer with an ADR, or list under `Not Doing` with rationale. The architecture doc is the lever; OKR is the recurring forcing function.

## Typical flow (first time, any project)

```
/okr        → init                              # interview: mission, Operating Principles,
                                                 # 1–3 Objectives + KRs, Anti-Goals, version v1
/okr        → plan-phase <slug>                 # full phase OKR; auto-assigns #NNN
/okr        → plan-week                          # proposes 3–5 candidate tasks for this ISO week
                                                 # user approves a subset

/pmo        → (auto) writes BOARD rows + full task definitions to journal/<YYYY-MM>/<today>.md, runs standup
... daily work ... /pmo close-task ... /pmo decide ... /pmo delegate <id> ...
/pmo        → digest <inputs/...>                # whenever user drops external docs (PDF/Excel/notes)
/pmo        → autopilot                          # batch-dispatch eligible specs while you're away
/pmo        → friday-review                      # writes weekly/<YYYY-WW>.md
/pmo        → handoff                            # writes handoff/<today>.md before stopping

/okr        → snapshot                           # heartbeat snapshot (or auto-prompted after 14d)
/pmo        → mid-phase-review                   # phase-midpoint; applies scope-reduction if armed
/pmo        → end-phase-retro                    # when KRs largely hit; writes evidence/<YYYY-MM>/retro.md

/okr        → score-phase                        # consumes the retro, fills phase file's Retro, snapshots
/pmo        → rollover                           # cleans BOARD carry-forwards, hands off to OKR
/okr        → plan-phase <next-slug>             # next phase begins (auto #NNN+1)
```

## Project file layout (after all skills bootstrap)

```
<project_root>/
├── .perry/
│   ├── config.md                       ← language + repo layout (single | split)
│   └── hook.md                         ← project-specific additions (optional)
├── OKR.md                              ← okr (overall, versioned)
├── phase/
│   ├── CURRENT                          ← okr (one-line pointer: <NNN>-<slug> of current phase)
│   ├── 001-system-build.md              ← okr (phase #001, scored)
│   ├── 002-cash-deployment.md           ← okr (phase #002, active — current)
│   └── snapshots/
│       ├── 2026-05-01-001-system-build-final.md    ← terminal snapshot at score-phase
│       └── 2026-05-13-002-cash-deployment.md       ← heartbeat snapshot
├── BOARD.md                             ← pmo (LIVE working memory; ≤200 lines; closed tasks leave)
├── journal/
│   └── 2026-05/
│       ├── 2026-05-01.md                ← pmo (day's status changes / new tasks / decisions)
│       ├── 2026-05-02.md
│       └── ...                          ← one file per day; append-only after the day ends
├── PROJECT_STATE.md                     ← pmo (cross-phase dashboard)
├── DECISIONS.md                         ← pmo (INDEX only, ≤200 lines)
├── decisions/
│   ├── ADR-001-pmo-bootstrap.md         ← pmo (one file per decision; Context/Options/Chosen/Consequences)
│   ├── ADR-002-r1z-alphabet.md          ← Status: active | superseded | expired | archived (header field; files don't move)
│   └── ...
├── design/
│   └── DESIGN-001-process-mgmt.md       ← design (RFC)
├── evidence/
│   └── 2026-05/
│       ├── TASK-001-deliverable-name.md          ← pmo (per-task artifact)
│       ├── midphase-review-002-cash-deployment.md
│       └── retro.md                              ← consumed by okr `score-phase`
├── weekly/
│   └── 2026-W18.md                      ← pmo (status report)
├── handoff/
│   └── 2026-05-01.md                    ← pmo (session bridge)
├── inputs/                              ← raw drop zone for external docs (ephemeral)
│   └── 2026-05-07-look-cap-q1-report.pdf      ← waiting for /pmo digest
├── knowledge/                           ← post-digest organized library
│   ├── INDEX.md                                ← pmo (auto-maintained catalog)
│   ├── _shared/
│   │   └── USER-002-constraints-digest.md     ← project-constitution (eternal)
│   ├── gavi/
│   │   ├── 2025-12-09-term-sheet.pdf          ← moved from inputs/
│   │   └── 2025-12-09-term-sheet-digest.md    ← PMO's structured summary
│   └── research/
│       └── jegadeesh-titman-1993-digest.md
│
│   # The four below are OPTIONAL — created lazily on first use, not at bootstrap.
├── ARCHITECTURE.md                      ← USER-OWNED single source of truth for system design.
│                                         Injected into every dispatched agent's prompt.
│                                         Independent review agent verifies every code change against it.
├── architecture/
│   └── audit-history/
│       └── 2026-05-13.md                        ← per-run audit report (mechanical + LLM consistency scan)
├── runbook/                             ← operability of deployed components (only if any spec has `Deployed: yes`)
│   ├── INDEX.md                                 ← auto-maintained catalog
│   └── trader-daemon.md                         ← per-component: What / Healthy / Failures / Escalation
├── incidents/                           ← postmortem records (only if you use /pmo incident)
│   ├── INDEX.md
│   └── 2026-05-12-trader-stuck.md               ← timeline + root cause + fix + derived changes
│
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
