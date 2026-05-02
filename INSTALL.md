# Install — Perry

Perry installs as **two peer skills** in `~/.claude/skills/`:
`~/.claude/skills/okr/` and `~/.claude/skills/pmo/`. They're independent skill folders that cooperate by convention (file ownership), not by being nested.

## One-shot install

From wherever you keep this repo on disk (`git clone`, download, or local copy), set `SRC` to that folder and run:

```bash
mkdir -p ~/.claude/skills
SRC=/path/to/perry            # change to your local copy
cp -R "$SRC/okr" ~/.claude/skills/okr
cp -R "$SRC/pmo" ~/.claude/skills/pmo
```

Verify:

```bash
ls ~/.claude/skills
# Expect at minimum: okr  pmo

ls ~/.claude/skills/okr ~/.claude/skills/pmo
# okr: SKILL.md  state/   (state has OKR_TEMPLATE.md, monthly_TEMPLATE.md)
# pmo: SKILL.md  state/   (state has PROJECT_STATE_/TASKS_/DECISIONS_/weekly_/handoff_/evidence_TEMPLATE.md)
```

## Update later

When you tweak files in the source folder, re-sync with:

```bash
SRC=/path/to/perry
rsync -a --delete "$SRC/okr/" ~/.claude/skills/okr/
rsync -a --delete "$SRC/pmo/" ~/.claude/skills/pmo/
```

## First run in a project

In Claude Code, from inside any project directory:

```
/okr           # → bootstraps OKR.md via interview, then plan-month
/pmo           # → bootstraps TASKS.md, PROJECT_STATE.md, DECISIONS.md, evidence/, weekly/, handoff/
```

Order matters once: run `/okr init` first so PMO's standup can show OKR progress on day one. After that, either order works.

## Uninstall

```bash
rm -rf ~/.claude/skills/okr ~/.claude/skills/pmo
```

State files (`OKR.md`, `TASKS.md`, etc.) live in each project folder — nothing is left behind in your home directory.

## Distributing Perry

Perry is just files. Copy or `git clone` the `perry/` folder onto a new machine, then run the install commands above. No package manager, no daemon, no sync state.
