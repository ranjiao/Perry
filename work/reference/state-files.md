# State files & size discipline

The fixed set of files PMO maintains, plus the hard / soft caps on each. Loaded by the agent when:
- Running `/pmo` bootstrap (which files to create).
- Answering "where should this go?" (which file owns this kind of content).
- Touching ARCHITECTURE.md, runbooks, incidents (the optional lazy-created trees).
- Adding a per-project hook that introduces a new file or directory.

## Two file models

Moved here from `work/SKILL.md § Two file models` on 2026-09-21 (TASK-470), unchanged; the lane keeps the one-line form of each axis and the tier-1 refusal rule. Why two axes: `lane-notes.md § Why two file models`.

### Axis A — temporal layers (BOARD / journal / evidence)

PMO **state** files split across three layers with different lifecycles:

| Layer | File(s) | Lifetime | Read frequency | Write pattern |
|---|---|---|---|---|
| **Live** | the task store — read with `perry-tasks board` | now (closed work leaves the board) | every standup | mutated by `perry-task` as state changes |
| **History** | `journal/<YYYY-MM>/<YYYY-MM-DD>.md` | append-only per day | only on demand or by weekly/retro subcommands | one file per day; **append-only after the day ends** |
| **Artifact** | `evidence/<YYYY-MM>/<TASK-ID>-*.md` | per task | only when verifying a `done` claim or writing a retro | one file per task deliverable (incl. `<TASK-ID>-spec.md` for P0/P1 — see `reference/subcommands.md` § add-task) |

The task store is the PMO's **working memory**; `perry-tasks board` is how it is read. It must always be true, current, and small. The journal is the audit trail. Evidence is the deliverable.

### Axis B — audience tiers (who reads this file)

EVERY Perry file falls into exactly one of three tiers based on **who reads it**. Tier determines size cap, format, and edit pattern.

- **Tier 1 — user-read-and-edit** (`OKR.md`, `phase/<NNN>-<slug>.md`, `ARCHITECTURE.md`, `runbook/<component>.md`, `.perry/{config,hook}.md`). Strategic; the user must read it raw, so each has a **hard line cap**. When a write would exceed it, OKR / PMO **refuses the write** and forces the overflow into a sibling file (typically `evidence/<YYYY-MM>/<topic>-appendix.md` or `architecture/sections/§N-<topic>.md`), leaving the main file as a §-index + 1-paragraph summaries. This preserves tier 1's "readable in one sitting" property.
- **Tier 2 — agent-internal state** (the task store, `journal/`, `evidence/`, `decisions/`, `incidents/`, `weekly/`, `handoff/`, `PROJECT_STATE.md`, `phase/snapshots/`, `architecture/audit-history/`, `knowledge/`). No user-read constraint, so no hard cap — only the soft SKILL.md ~300 limit, which are context-budget driven, not readability driven.
- **Tier 3 — the consumption surface.** Perry does **not** write this tier. Reading state richly is the frontend's job, and the frontend is **aiMark** (`~/proj/aimark`), which watches the project directory and renders it live. Perry's obligation to tier 3 is to write tier 1/2 in the declared structure so a reader can parse it — see `$PERRY_HOME/schema/README.md`.

**Per-file caps and the structural contract each file must satisfy** live in `$PERRY_HOME/schema/state-schema.json` (checked by `bin/perry-lint`); the full inventory is in `reference/state-files.md`. `bin/perry-state` reports current cap usage in `operations.tier1_caps`, so the standup sees an overrun before the next write hits it.

## File inventory

All at the **project root** unless noted. Greppable, version-controlled.

| File / dir | Owner | Purpose | Template |
|------------|-------|---------|----------|
| `BOARD.md` | pmo | **Not written since TASK-237 3c** — the board is what `perry-tasks board` prints from `tasks.jsonl` and its four register stores, and a project that still holds a `BOARD.md` imports a register it holds with `perry-tasks <register>-write --from-board`. What the printed board is: **live working memory.** Current open work only — terse rows, no narrative. P0 / P1 / P2 / Cadence tables + User Input Queue + 1-line risk pointers. Closed tasks leave this file. **Hard cap: ≤200 lines.** | `state/BOARD_TEMPLATE.md` |
| `journal/<YYYY-MM>/<YYYY-MM-DD>.md` | pmo | **Daily append-only history.** One file per day. Sections: Status changes / New tasks added / Decisions / Notes / Carry to tomorrow. Frozen after the day ends. | `state/journal_TEMPLATE.md` |
| `PROJECT_STATE.md` | pmo | Cross-phase living dashboard: current phase #, week, top risks, recent cross-session work, multi-phase carry-forwards | `state/PROJECT_STATE_TEMPLATE.md` |
| `decisions/ADR-NNN-<slug>.md` | **decide** (moved 2026-08-16 by the signed hand-off contract; `work` reads it, never writes it). The whole decision record — there is no index file, `perry-decide list` is the view (TASK-235). | One ADR per file: Context / Options / Chosen / Consequences / Evidence / Sunset criteria. Append-only after creation (status flips append `## Status change` entries; never edit Chosen/Consequences in place). | `decide/state/ADR_TEMPLATE.md` |
| `evidence/<YYYY-MM>/<TASK-ID>-*.md` | pmo | Per-task artifacts: spec files, reports, checklists, drill records, gap lists, retros | `state/evidence_TEMPLATE.md` |
| `weekly/<YYYY-WW>.md` | pmo | One ISO week's status report | `state/weekly_TEMPLATE.md` |
| `handoff/<YYYY-MM-DD>.md` | pmo | Session resumption doc | `state/handoff_TEMPLATE.md` |
| `inputs/<filename>` | (raw drop zone) | User puts external docs (PDFs, Excels, screenshots, pasted markdown) here for PMO to digest. PMO consumes via `/pmo digest`; ideally drained to 0 between sessions. | — |
| `knowledge/<topic>/<source>` + `<source>-digest.md` | pmo | Topic-organized library of digested sources. Source moves here from `inputs/` on digest; digest is PMO's structured summary (TL;DR + Key facts + Open questions). Referenced by spec / journal / decisions to avoid re-reading source. | `state/digest_TEMPLATE.md` |
| `knowledge/<topic>/<slug>.md` (a **card**) | pmo | One claim the project made and can re-check — *how to do this correctly*, the third kind of memory (DESIGN-006 § 5.3). Told from a digest by its `Kind:` field. Written only by `bin/perry-knowledge promote` at a capture point, never by hand: all five provenance fields are mandatory **at write time** and a sourceless card is refused. See `reference/promotion.md`. | `state/knowledge_card_TEMPLATE.md` |
| `knowledge/INDEX.md` | pmo | Auto-maintained catalog of all digests by status (active / eternal / archived) and topic, plus `## Cards by topic`, which `perry-knowledge` re-renders and nothing else touches | `state/knowledge_INDEX_TEMPLATE.md` |
| `ARCHITECTURE.md` | **user** | **Optional, lazy-created. User-owned — agents never write to it.** Single source of truth for system design. Fixed 8-section structure (Mission / Components / Boundaries / Data flow / Contracts / Non-negotiables / Open questions / Change log). Injected into every dispatch's agent prompt; independent review agent verifies every code change against it. | `state/ARCHITECTURE_TEMPLATE.md` |
| `architecture/audit-history/<YYYY-MM-DD>.md` | pmo | Per-run audit reports (mechanical §6 NN check results + LLM consistency scan findings). Append-only. | (no template — generated by `/pmo architecture-audit`) |
| `runbook/<component>.md` | pmo | **Optional, lazy-created.** One file per deployed component: What it does / How to tell it's healthy / Common failures + canned ops / Escalation. Required when a task spec has `Deployed: yes`. | `state/runbook_TEMPLATE.md` |
| `runbook/INDEX.md` | pmo | Auto-maintained catalog of all runbooks (active / stale / gaps). | `state/runbook_INDEX_TEMPLATE.md` |
| `incidents/<YYYY-MM-DD>-<slug>.md` | pmo | **Optional, lazy-created.** One file per production incident with timeline / root cause / fix / derived changes. | `state/incident_TEMPLATE.md` |
| `incidents/INDEX.md` | pmo | Auto-maintained catalog of incidents (open / resolved / with-derived-changes ratio). | `state/incidents_INDEX_TEMPLATE.md` |
| `.perry/hook.md` | **user** (written once at bootstrap) | Per-project additions. Its `## High-stakes operations` list is a **safety gate**: `dispatch` refuses specs that match it and `autopilot` refuses to run without it. Written at bootstrap with a conservative default, then user-owned. Tier 1. | `state/hook_TEMPLATE.md` |
| `OKR.md`, `phase/` | okr | Read by PMO; never written by PMO | (in okr skill) |
| `design/<DESIGN-ID>-*.md` | design | Read by PMO to know which locked designs need implementation tasks; never written by PMO | (in design skill) |

## Size discipline (non-negotiable)

### Tier 1 caps (PMO/OKR REFUSES to write past these)

Tiers are about **who reads the file**: tier 1 the user reads raw (hard caps), tier 2 the agent reads for its own purposes (soft caps), tier 3 is the consumption surface — which Perry does not write. See `§ Two file models` above and `$PERRY_HOME/schema/README.md`.

- `OKR.md` ≤ **200** lines. Overflow → move historical `## v<N>` retro blocks to `phase/snapshots/okr-vN.md`; main file keeps current version + version log.
- `ARCHITECTURE.md` ≤ **500** lines. Overflow → split per-§ to `architecture/sections/§<N>-<topic>.md`; main file keeps §-section TOC + 1-paragraph summaries.
- `phase/<NNN>-<slug>.md` ≤ **300** lines. Overflow → move long narrative / Stretch trackers / project lists to `evidence/<YYYY-MM>/phase-<NNN>-<topic>.md`.
- `runbook/<component>.md` ≤ **150** lines. Overflow → split troubleshooting matrix to `runbook/<component>-troubleshooting.md` (still tier 1; just chaptered).

### Tier 2 caps (existing soft limits, agent-context-budget driven)

- A `BOARD.md` a project still holds is ≤ 200 lines; past that, `triage` cuts it before the next standup ends. The board `perry-tasks board` prints is not a file and has no line cap.
- `PROJECT_STATE.md` ≤ 200 lines.
- `work/SKILL.md` itself ≤ ~300 lines. New features → write to `reference/<topic>.md` first, add a one-line pointer in the SKILL.md `## How this file is organized` table. See `reference/extending.md`.
- Individual `journal/<YYYY-MM>/<YYYY-MM-DD>.md` files have no cap (a busy day might be 300+ lines), but they're append-only and rarely re-read in full — only when answering "what happened on X".
- Long task content (rich definitions, audit checklists, drill records) lives in `evidence/`, not in BOARD or journal.
