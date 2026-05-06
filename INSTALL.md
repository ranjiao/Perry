# Install — Perry

Perry installs as **one folder** at `~/.claude/skills/perry/`, containing four skill files at nested paths. Claude Code discovers each one and makes them invocable as `/perry`, `/okr`, `/pmo`, and `/design`.

```
~/.claude/skills/perry/
├── SKILL.md            ← /perry (top-level coordinator)
├── README.md
├── INSTALL.md
├── okr/
│   ├── SKILL.md        ← /okr (goal-setting child)
│   └── state/          (templates: OKR_TEMPLATE.md, monthly_TEMPLATE.md)
├── pmo/
│   ├── SKILL.md        ← /pmo (execution stewardship child)
│   └── state/          (templates: PROJECT_STATE_, TASKS_, DECISIONS_, weekly_, handoff_, evidence_TEMPLATE.md)
└── design/
    ├── SKILL.md        ← /design (design-doc steward child)
    └── state/          (template: design_TEMPLATE.md)
```

This nested layout is the same pattern used by gstack and other multi-skill packages — one folder on disk, multiple invocable skills.

## One-shot install

### Option 1 — symlink (recommended for development)

If you keep this repo as a working git checkout and want changes you push to take effect immediately:

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/perry ~/.claude/skills/perry
```

### Option 2 — copy (snapshot install)

If you'd rather pin a copy that doesn't move when you edit the source:

```bash
mkdir -p ~/.claude/skills
SRC=/path/to/perry
cp -R "$SRC" ~/.claude/skills/perry
```

Verify either option:

```bash
ls ~/.claude/skills/perry
# Expect: SKILL.md  README.md  INSTALL.md  okr/  pmo/  design/

ls ~/.claude/skills/perry/{okr,pmo,design}/SKILL.md
```

In a Claude Code session, `/perry`, `/okr`, `/pmo`, and `/design` should all be available.

## Update later

If you used the symlink: `git pull` in the source folder; changes apply immediately.

If you used the copy: re-sync with `rsync`:

```bash
SRC=/path/to/perry
rsync -a --delete "$SRC/" ~/.claude/skills/perry/
```

## First run in a project

In Claude Code, from inside any project directory:

```
/perry          # combined snapshot + recommends next steps for the project
```

If this is a new project (no `OKR.md` / `tasks/` yet), `/perry` will run first-time setup, which:
1. Confirms your **document language** (English / 中文 / other) and writes it to `.perry/config.md`.
2. Confirms your **repo layout** — single repo (default for non-code projects) or split (PMO docs ↔ code) — and writes it to `.perry/config.md`.

The recommended first-run order is:

```
/okr init                       # interview: mission, Operating Principles,
                                # 1–3 Objectives + KRs, Anti-Goals, version v1
/okr plan-month <YYYY-MM>       # full monthly OKR (10 mandatory sections)
/pmo                            # bootstraps execution files, runs first standup
/okr plan-week                  # proposes first batch of weekly tasks
                                # → /pmo writes them to tasks/<YYYY-MM>.md after approval
```

After that, daily/weekly use is whichever of `/perry`, `/okr`, `/pmo`, or `/design` matches the moment.

Project-specific additions (custom agents, MCP tools, domain constraints, promotion stages, cost ceiling source) live at `<project_root>/.perry/hook.md`. The skill folder itself stays project-agnostic.

## Uninstall

```bash
rm -rf ~/.claude/skills/perry      # if you used cp
# or
rm ~/.claude/skills/perry          # if you used the symlink
```

State files (`OKR.md`, `tasks/`, `evidence/`, etc.) live in each project folder — nothing is left behind in your home directory.

## Distributing Perry

Perry is just files. Copy or `git clone` the `perry/` folder onto a new machine, then run the install commands above. No package manager, no daemon, no sync state.
