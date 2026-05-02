# Install — Perry

Perry installs as **one folder** at `~/.claude/skills/perry/`, containing three skill files at nested paths. Claude Code discovers each one and makes them invocable as `/perry`, `/okr`, and `/pmo`.

```
~/.claude/skills/perry/
├── SKILL.md            ← /perry (top-level coordinator)
├── README.md
├── INSTALL.md
├── okr/
│   ├── SKILL.md        ← /okr (goal-setting child)
│   └── state/          (templates: OKR_TEMPLATE.md, monthly_TEMPLATE.md)
└── pmo/
    ├── SKILL.md        ← /pmo (execution stewardship child)
    └── state/          (templates: PROJECT_STATE_, TASKS_, DECISIONS_, weekly_, handoff_, evidence_TEMPLATE.md)
```

This nested layout is the same pattern used by gstack and other multi-skill packages — one folder on disk, multiple invocable skills.

## One-shot install

From wherever you keep this repo on disk (`git clone`, download, or local copy):

```bash
mkdir -p ~/.claude/skills
SRC=/path/to/perry            # change to your local copy
cp -R "$SRC" ~/.claude/skills/perry
```

Verify:

```bash
ls ~/.claude/skills/perry
# Expect: SKILL.md  README.md  INSTALL.md  okr/  pmo/

ls ~/.claude/skills/perry/okr ~/.claude/skills/perry/pmo
# okr: SKILL.md  state/
# pmo: SKILL.md  state/
```

In a Claude Code session, `/perry`, `/okr`, and `/pmo` should all be available.

## Update later

When you tweak files in the source folder, re-sync with:

```bash
SRC=/path/to/perry
rsync -a --delete "$SRC/" ~/.claude/skills/perry/
```

## First run in a project

In Claude Code, from inside any project directory:

```
/perry          # combined snapshot + recommends next steps for the project
```

If this is a new project (no `OKR.md` / `TASKS.md` yet), `/perry` will offer first-time setup. The recommended first-run order is:

```
/okr init                       # interview: mission, Operating Principles,
                                # 1–3 Objectives + KRs, Anti-Goals, version v1
/okr plan-month <YYYY-MM>       # full monthly OKR (10 mandatory sections)
/pmo                            # bootstraps execution files, runs first standup
/okr plan-week                  # proposes first batch of weekly tasks
                                # → /pmo writes them to TASKS.md after approval
```

After that, daily/weekly use is whichever of `/perry`, `/okr`, or `/pmo` matches the moment.

## Uninstall

```bash
rm -rf ~/.claude/skills/perry
```

State files (`OKR.md`, `TASKS.md`, `evidence/`, etc.) live in each project folder — nothing is left behind in your home directory.

## Distributing Perry

Perry is just files. Copy or `git clone` the `perry/` folder onto a new machine, then run the install commands above. No package manager, no daemon, no sync state.
