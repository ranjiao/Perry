# Install — Perry

Perry is a four-skill set: a top-level `/perry` plus three children (`/okr`, `/pmo`, `/design`). All four need to be discoverable as siblings under your skills directory so each one is invocable on its own.

The `setup` script handles this. It links the parent `perry/` once, then creates one relative symlink per child so Claude Code surfaces each as a top-level slash command.

```
~/.claude/skills/
├── perry      → <source dir>/Perry         # top-level (real symlink to source)
├── okr        → perry/okr                  # child (relative)
├── pmo        → perry/pmo                  # child (relative)
└── design     → perry/design               # child (relative)
```

## One-shot install

```bash
git clone <perry repo> ~/proj/Perry         # or wherever you want the source
~/proj/Perry/setup                          # global install: ~/.claude/skills/
```

That's it. Re-run the script anytime; it's idempotent.

### Per-project install

If you want Perry available only inside one project (not globally):

```bash
cd /path/to/your/project
~/proj/Perry/setup --local                  # installs to ./. claude/skills/
```

### Verify

```bash
ls ~/.claude/skills | grep -E '^(perry|okr|pmo|design)$'
# Expect all four
```

In a Claude Code session, `/perry`, `/okr`, `/pmo`, and `/design` are all available.

## Update later

If you installed via symlink (the default), Perry tracks the source folder live — `git pull` in the source folder is enough.

If you installed by copy:

```bash
rsync -a --delete ~/proj/Perry/ ~/.claude/skills/perry/
~/.claude/skills/perry/setup     # refresh child symlinks if any new children were added
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
rm ~/.claude/skills/{perry,okr,pmo,design}
```

State files (`OKR.md`, `tasks/`, `evidence/`, etc.) live in each project folder — nothing is left behind in your home directory.

## Distributing Perry

Perry is just files. `git clone` the source onto a new machine, then run `setup`. No package manager, no daemon, no sync state.
