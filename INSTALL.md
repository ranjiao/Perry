# Install — Perry

Perry is a four-skill set: a top-level `/perry` plus three children (`/okr`, `/pmo`, `/design`). It runs on **Claude Code** (default) and **Codex CLI**. Pick the install path for your host below; both can coexist on the same machine.

## Fresh Mac? Read this first

The `setup` script runs a Phase 0 **dependency check** before symlinking. Status icons in the output: ✅ present, ⚠️ recommended but missing, ❌ required and missing.

What a brand-new Mac will be missing (and how setup handles it):

| Dep | What it's for | Auto-installable? | How |
|---|---|---|---|
| **git** (Xcode CLT) | Cloning Perry + `perry-update-check` | ❌ GUI prompt | Setup fails fast and tells you to run `xcode-select --install` |
| **Claude Code CLI** | The default install target reads `~/.claude/skills/` | ❌ external download | Setup fails fast with a link to `claude.com/download` |
| **Homebrew** | Mac package manager (gates several others) | ✅ via the official curl-install script | Interactive prompt; `--yes-deps` auto-installs |
| **coreutils** (provides `gtimeout`) | Soft: `perry-codex-preflight` uses `timeout` if present, degrades gracefully if not | ✅ `brew install coreutils` | Interactive prompt; `--yes-deps` auto-installs |
| **Node.js** | Only needed if you use the **codex** executor in `/pmo dispatch` | ✅ `brew install node` | Interactive prompt; `--yes-deps` auto-installs |
| **codex CLI** | Same — only for codex executor | ✅ `npm install -g @openai/codex` | Interactive prompt; `--yes-deps` auto-installs |

Default behavior is **interactive prompts** for each missing optional/soft dep. Pass `--yes-deps` to accept all auto-installs without prompting, `--no-deps` to skip Phase 0 entirely, or `--check-deps-only` to see the report and exit without installing or symlinking.

```bash
~/proj/Perry/setup --check-deps-only      # see what's present / missing; exit
~/proj/Perry/setup                         # default: prompt per missing dep
~/proj/Perry/setup --yes-deps              # auto-install everything that can be
~/proj/Perry/setup --no-deps               # skip dep check, just symlink
```

## Claude Code

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

## Codex CLI

Codex CLI discovers skills the same way Claude Code does — by reading `SKILL.md` frontmatter (`name` + `description`) from a canonical skills directory. The path is different: Codex scans `$HOME/.agents/skills/` (per the [Codex Skills docs](https://developers.openai.com/codex/skills)), not `~/.claude/skills/`.

The same `setup` script handles both hosts. Add `--codex` to also install for Codex:

```bash
git clone https://github.com/ranjiao/Perry ~/proj/Perry      # or wherever
~/proj/Perry/setup --codex                                    # installs to BOTH ~/.claude/skills/ AND ~/.agents/skills/
```

The script creates the same symlink layout under each host's skills dir:

```
~/.agents/skills/                                             # Codex
├── perry      → <source dir>/Perry         # top-level (real symlink to source)
├── okr        → perry/okr                  # child (relative)
├── pmo        → perry/pmo                  # child (relative)
└── design     → perry/design               # child (relative)
```

Setup also prints the recommended shell exports for unambiguous `$PERRY_HOME` resolution:

```bash
export PERRY_HOME="$HOME/.agents/skills/perry"   # or wherever Perry lives for you
export PERRY_HOST=codex-cli                      # or omit and let auto-detect handle it
```

Reload your shell (`exec $SHELL`) and start `codex` inside any project. Invoke Perry via:
- **`/skills`** — list available skills, pick `perry` / `okr` / `pmo` / `design`
- **`$perry`** / **`$okr`** / **`$pmo`** / **`$design`** — explicit mention in your prompt
- **Implicit** — Codex picks the skill when your task matches the description

Per-host fallbacks (free-text prompts in place of `AskUserQuestion`, refusal of `Executor: claude-subagent`, shell-backgrounded `codex exec` instead of Bash `run_in_background`) are documented in `reference/host-capabilities.md`, which the SKILL.md standup ritual reads on every invocation.

### Verify (Codex)

```bash
ls ~/.agents/skills | grep -E '^(perry|okr|pmo|design)$'      # expect all four
~/.agents/skills/perry/bin/perry-detect-host                  # expect: codex-cli (when run inside codex)
```

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

If this is a new project (no `OKR.md` / `BOARD.md` yet), `/perry` will run first-time setup, which:
1. Confirms your **document language** (English / 中文 / other) and writes it to `.perry/config.md`.
2. Confirms your **repo layout** — single repo (default for non-code projects) or split (PMO docs ↔ code) — and writes it to `.perry/config.md`.

The recommended first-run order is:

```
/okr init                       # interview: mission, Operating Principles,
                                # 1–3 Objectives + KRs, Anti-Goals, version v1
/okr plan-month <YYYY-MM>       # full monthly OKR (10 mandatory sections)
/pmo                            # bootstraps execution files, runs first standup
/okr plan-week                  # proposes first batch of weekly tasks
                                # → /pmo writes them to BOARD.md + today's journal entry after approval
```

After that, daily/weekly use is whichever of `/perry`, `/okr`, `/pmo`, or `/design` matches the moment.

Project-specific additions (custom agents, MCP tools, domain constraints, promotion stages, cost ceiling source) live at `<project_root>/.perry/hook.md`. The skill folder itself stays project-agnostic.

## Uninstall

```bash
rm ~/.claude/skills/{perry,okr,pmo,design}     # Claude Code
rm ~/.agents/skills/{perry,okr,pmo,design}     # Codex (if --codex was used)
```

State files (`OKR.md`, `BOARD.md`, `journal/`, `evidence/`, etc.) live in each project folder — nothing is left behind in your home directory.

## Distributing Perry

Perry is just files. `git clone` the source onto a new machine, then run `setup`. No package manager, no daemon, no sync state.
