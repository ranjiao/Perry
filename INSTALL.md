# Install Perry

Perry is **one skill** with three lanes: `goals`, `work`, and `decide`. It supports Claude Code, OpenCode, and Codex CLI; multiple hosts may coexist. OpenCode support is an explicitly added adapter after DESIGN-003 decision 8, not a reinterpretation of that older decision.

## Install

Clone Perry anywhere. `setup` symlinks the source into each selected host's canonical skill directory.

```bash
git clone https://github.com/ranjiao/Perry.git ~/perry
~/perry/setup
```

Host selection:

| Command | Target |
|---|---|
| `setup` | Auto-detect `claude`, `opencode`, and `codex` in `PATH`; install every detected host |
| `setup --claude` | `~/.claude/skills/perry` |
| `setup --opencode` | `~/.config/opencode/skills/perry` |
| `setup --codex` | `~/.agents/skills/perry` |
| `setup --claude --opencode --codex` | All three global targets |

`--local` changes Claude Code and OpenCode targets to `./.claude/skills/perry` and `./.opencode/skills/perry`. Codex remains global. Setup installs only `perry`; it removes legacy Perry-created sibling links for old lane names and never creates new sibling skills.

## Dependencies

Setup checks `git`, `curl`, `bash`, and `perl`, plus each explicitly selected host binary. Codex remains an optional executor on **all** hosts and needs Node.js/npm when it is not already installed.

```bash
~/perry/setup --check-deps-only
~/perry/setup --no-deps          # skip checks; only create skill links
~/perry/setup --yes-deps         # accept supported non-interactive installs
```

In a non-TTY agent shell, setup reports missing optional dependencies but does not block waiting for interactive confirmation. GUI, sudo, and external host installation remain user actions.

## Verify

```bash
test -L ~/.claude/skills/perry                  # Claude Code global
test -L ~/.config/opencode/skills/perry         # OpenCode global
test -L ~/.agents/skills/perry                  # Codex global
```

Only the targets selected for your machine should exist. In any host, invoke the one `perry` skill and pass lanes as arguments, for example `/perry goals init` or `/perry work triage`. Codex users can open `/skills`, select **perry**, or mention `$perry`.

## Host behavior

- Claude Code choices use `AskUserQuestion`; its native executor is `claude-subagent`.
- OpenCode choices use `question`; its native executor is synchronous `Task(subagent_type: general)`, represented by `opencode-subagent`.
- Codex CLI choices use numbered free text and has no native subagent executor.
- The `codex` executor remains available on all hosts.
- OpenCode and Codex use shell backgrounding for the asynchronous Codex executor and viewer because they have no Claude background-shell tool parameter.

The complete matrix and strict host/executor mismatch behavior are in [`reference/host-capabilities.md`](reference/host-capabilities.md).

## First run

From a project directory, invoke `/perry`. New projects are guided through:

```text
/perry goals init
/perry goals plan-phase <slug>
/perry work
/perry decide init
/perry goals plan-week
```

## Update and uninstall

A symlink install tracks the clone, so update with `git pull` in the source directory. The weekly update check also searches the OpenCode global path.

Remove only the one skill link for each host you installed:

```bash
rm ~/.claude/skills/perry
rm ~/.config/opencode/skills/perry
rm ~/.agents/skills/perry
```

Project state is not removed.
