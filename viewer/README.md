# Perry viewer — optional live web console

A read-only local web UI for browsing a Perry project's state (BOARD, OKR,
phase, decisions, risks, architecture, evidence, journal, handoff). It ships
inside the Perry skill but renders the **project you point it at**, not the
skill directory.

**Opt-in.** Lightweight Perry users never run it and carry zero extra
dependencies. It's for power users who want to glance at live state during
active work, with no LLM cost and nothing to install into the project.

It is the **fallback** consumption surface. The primary one is **aiMark**
(`~/proj/aimark`), which watches the project directory and renders it live.
Reach for this viewer when aiMark isn't running or isn't wanted. Both read the
same tier 1/2 markdown; neither writes to the project.

## Run

**Easiest (no shell needed):** just ask the agent — **`/perry work viewer`** (alias
`/perry work browse`). It starts the server in the background, waits until it's up
(first run installs deps, ~60s), and opens your browser at the address. Stop it
with `/perry work viewer stop`. This is the recommended path for non-technical users;
see `../work/reference/viewer.md`.

Or run it yourself, from inside your project directory (the one containing
`BOARD.md`):

```bash
bash "$PERRY_HOME/bin/perry-viewer"
```

First run auto-creates a private venv at `~/.cache/perry/viewer-venv`,
installs Flask + markdown, and starts the server. Subsequent runs just start
it. Open <http://127.0.0.1:8080>. Stop with Ctrl-C — nothing runs when it's
not started.

Flags:
- `--port 9000` — serve on a different port (or set `PERRY_VIEWER_PORT`).
- `--root /path/to/project` — render a specific project (default: walk up
  from the current dir to the nearest `BOARD.md`/`OKR.md`; or set
  `PERRY_PROJECT`).
- `--reinstall` — rebuild the venv from scratch.

## Pages

- **`/` Today** — phase + KPI strip + P0 critical path + user-input queue +
  risk console + recent decisions/journal. Auto-refreshes every 30s.
- **`/board`** — the whole board as priority lanes (P0/P1/P2) + User Input
  Queue + Cadence + Backbone. "See the whole board" (vs Atlas's "find a task").
- **`/okr`** — overall OKR: mission, objectives + KRs, Operating Principles,
  Anti-Goals, version history.
- **`/phase`** — current phase OKR, trip-wires, cost ceiling, plus cross-phase
  state folded in from PROJECT_STATE.md (carry-forwards, external deps,
  cross-session work).
- **`/risks`** — top-risk callout, value-meter gauges, armed trip-wires,
  resolved list.
- **`/atlas`** — unified search/browse across tasks / evidence / decisions /
  journal / handoff, with priority + status filters.
- **`/pulse`** — charts: ADR cadence, BOARD status mix, journal/evidence
  cadence.
- **`/architecture`** — ARCHITECTURE.md with a metadata header (version /
  status / last-reviewed / open questions) + rendered body with mermaid
  diagrams + section TOC.
- **`/file/<rel>`** — any project markdown file rendered (mermaid + TOC).

## Design

Read-only by deliberate choice — every mutation goes through `/perry work`,
`/perry goals` and `/perry decide` in chat. Each HTTP request re-parses the source markdown (no cache,
no DB), so the view is always live; parsing is sub-millisecond on typical
projects. Theme (light/dark) is applied pre-paint and persists via
localStorage. The brand name shown in the nav is derived from the BOARD.md
title (`# Board — <name>`), falling back to the project directory name.

## Files

```
viewer/
├── serve.py          # Flask routes + filters
├── parsers.py        # markdown → dataclasses (BoardState, OKR, Phase, ADR, …)
├── requirements.txt  # Flask + markdown (installed into ~/.cache/perry/viewer-venv)
├── templates/        # base + per-page Jinja templates + _macros
└── static/           # ds.css design tokens + favicon.svg
```

## What it does NOT do

- **No writes.** No forms; it never edits project files.
- **No auth.** Localhost only. Never expose beyond `127.0.0.1` — these files
  hold private project state.
- **No daemon.** Runs only while you have it open; no boot-time service, no
  watcher, no PID file.
- **No DB / cache.** Source markdown is the single source of truth.
