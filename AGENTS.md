# Perry — virtual project office (Codex AGENTS.md)

This file makes Perry discoverable inside **Codex CLI**, which loads `AGENTS.md` from the current working directory (and `~/.codex/AGENTS.md` globally) instead of Claude Code's `SKILL.md` frontmatter. Claude Code users do not need this file — they read `SKILL.md` directly.

Install (Codex):
```
git clone https://github.com/ranjiao/Perry ~/proj/Perry
export PERRY_HOME="$HOME/proj/Perry"           # add to your shell profile
export PERRY_HOST=codex-cli                    # add to your shell profile
mkdir -p ~/.codex
ln -sf "$PERRY_HOME/AGENTS.md" ~/.codex/AGENTS.md   # OR cat into existing file
```

After install, inside any project directory, address Perry by typing one of: `perry`, `okr`, `pmo`, `design`, `/perry`, `/okr`, `/pmo`, `/design`. Codex doesn't have native slash commands, but treat any of those tokens as the corresponding skill invocation.

## Routing rules

| User says (any of) | Read this file first, then follow it |
|---|---|
| `perry`, `/perry`, "where are we", "Perry status" | `$PERRY_HOME/SKILL.md` |
| `okr`, `/okr`, "set goals", "plan the month", "OKR" | `$PERRY_HOME/okr/SKILL.md` |
| `pmo`, `/pmo`, "standup", "delegate this", "what's blocked", "rollover", "PMO" | `$PERRY_HOME/pmo/SKILL.md` |
| `design`, `/design`, "RFC", "design doc", "lock the architecture" | `$PERRY_HOME/design/SKILL.md` |
| `pmo dispatch <id>`, `pmo autopilot` | `$PERRY_HOME/pmo/SKILL.md` then the matching reference under `$PERRY_HOME/pmo/reference/` |
| `pmo help`, `okr help`, `design help`, `perry help` | The matching SKILL.md `## help` section (this is a navigation command — do NOT trigger the standup) |

## Mandatory pre-read for every Perry invocation

Always read `$PERRY_HOME/reference/host-capabilities.md` before acting. It documents the per-host fallbacks Perry expects under Codex (free-text prompts instead of `AskUserQuestion`, refusal of `Executor: claude-subagent`, shell-backgrounded `codex exec`, etc.). Without that file's rules, the SKILL.md prose assumes the Claude Code tool surface and will mis-fire.

## Path convention

All bin/ invocations in SKILL.md and reference files are written as `bash "${PERRY_HOME:-$HOME/.claude/skills/perry}/bin/<script>"`. With `PERRY_HOME` set in your shell, the same prose works under both hosts.

## File ownership rules (do not break)

Inherits from `$PERRY_HOME/SKILL.md`. The short version:
- `okr` is the only writer of `OKR.md` and `monthly/`.
- `pmo` is the only writer of `BOARD.md`, `journal/`, `PROJECT_STATE.md`, `DECISIONS.md`, `evidence/`, `weekly/`, `handoff/`.
- `design` is the only writer of `design/<DESIGN-ID>-*.md`.
- Each skill reads the others' files freely; no skill writes outside its lane.

This boundary is what keeps the set composable across sessions and hosts.
