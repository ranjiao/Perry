# Host capabilities matrix

Perry runs on **Claude Code**, **OpenCode**, and **Codex CLI**. It registers **one** skill, `perry`, on every host; `goals`, `work`, and `decide` are lanes loaded on demand. OpenCode is an explicitly added host adapter after DESIGN-003 decision 8; this support does not reinterpret that older Claude+Codex decision as having already authorized OpenCode.

> **This page is outside the shorthand carve-out.** It owns host translation, so all commands and directories below use the live vocabulary. `tests/test_shipped_vocabulary.py::TestHostCapabilitiesNamesTheOneLiveEntrance` enforces that boundary.

## Detect once per session

After deriving `$PERRY_HOME`, run:

```
bash "$PERRY_HOME/bin/perry-detect-host"
```

The result is `claude-code`, `opencode`, `codex-cli`, or `unknown`. Remember it as `$HOST`; do not re-run per subcommand. If it is `unknown`, retain the original `claude-code` fallback, mention the ambiguity once, and recommend an override:

```
export PERRY_HOST=claude-code      # or opencode or codex-cli
```

Detection priority is deliberate:

1. `PERRY_HOST` override, if valid.
2. A verified Codex runtime sentinel: `CODEX_SANDBOX`, `CODEX_THREAD_ID`, `CODEX_CI`, or `CODEX_MANAGED_BY_NPM`.
3. `OPENCODE=1` or `OPENCODE_PID`.
4. Claude sentinels (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_PROJECT_DIR`).
5. Parent-process names, walking outward: `opencode`, `codex`, `claude`.

Codex must beat OpenCode and Claude because `codex exec` inherits its parent's environment. OpenCode must beat Claude because an OpenCode process can inherit Claude variables. `CODEX_HOME` is not a runtime sentinel. Invalid `PERRY_HOST` values produce `unknown`; the override contract never guesses.

## `$PERRY_HOME`

The Perry root contains `bin/`, `reference/`, `goals/`, `work/`, `decide/`, and top-level `SKILL.md`.

Default global installs:

- Claude Code: `$HOME/.claude/skills/perry`
- OpenCode: `$HOME/.config/opencode/skills/perry`
- Codex CLI: `$HOME/.agents/skills/perry`

Project-local installs are `.claude/skills/perry` for Claude Code and `.opencode/skills/perry` for OpenCode. Codex remains global. Runtime resolution is `$PERRY_HOME`, then the loaded SKILL.md path, then a bin script's own location.

## Capability matrix

| Capability | claude-code | opencode | codex-cli |
|---|---|---|---|
| User choices | `AskUserQuestion` | `question` tool | numbered free-text fallback |
| Native subagent | `Agent(subagent_type: general-purpose)` for `claude-subagent` | `Task(subagent_type: general)` for `opencode-subagent` | none |
| Native completion | small may be sync; medium/large may be background | always synchronous; process the result immediately | n/a |
| Background shell tool parameter | Bash `run_in_background: true` | unavailable; use the no-background-shell-tool fallback | unavailable; use the no-background-shell-tool fallback |
| Codex executor | available | available | available |
| Dispatch cap | enforced | enforced | filesystem-wide but completion cleanup is advisory across sessions |
| Skill discovery | `~/.claude/skills/perry` | `~/.config/opencode/skills/perry` or `.opencode/skills/perry` | `~/.agents/skills/perry` |
| Skill invocation | `/perry` | invoke `perry`; lanes are arguments to the one skill | `/skills`, pick **perry**, or mention `$perry` |

The executor enum is `claude-subagent | opencode-subagent | codex | manual`. The host matrix is strict:

| Host | Allowed automated executors |
|---|---|
| `claude-code` | `claude-subagent`, `codex` |
| `opencode` | `opencode-subagent`, `codex` |
| `codex-cli` | `codex` |

If a spec pins a native executor for another host, refuse rather than silently reroute. `manual` routes to `/perry work delegate`; it is never registered with `perry-dispatch-limit`. When an auto spec omits `Executor`, offer only executors valid for `$HOST`, plus `manual`.

## Prompt rendering

An instruction to use `AskUserQuestion` means the host's native choice UI. Claude Code uses `AskUserQuestion`; OpenCode uses `question` with equivalent labels, options and recommendation. Translate Claude's `multiSelect: true` to OpenCode's `multiple: true` exactly; passing the Claude field name to OpenCode is invalid. Codex prints numbered options and waits for free text:

```
[Header]
  1) A
  2) B  <- Recommended
  3) C
Reply with a number (1-3), or describe a different choice.
```

For multi-select on Codex, request comma-separated numbers or `all` / `none`. Rendering changes; the selected value and downstream writes do not.

## OpenCode native dispatch

For `Executor: opencode-subagent`, call `Task` with `subagent_type: general`. Pass the same self-contained prompt, architecture preamble, safety constraints, git expectation, and RESULT contract used by other executors. The call is synchronous: when it returns, release the dispatch slot and run verification immediately. Do not promise a later background notification and do not write an "awaiting completion" state after the result already exists.

Architecture review on OpenCode is another synchronous `Task(subagent_type: general)` call after objective verification. It receives the architecture, diff, and primary compliance block, and its PASS/FAIL is appended exactly like other hosts.

## No-background-shell-tool fallback

OpenCode and Codex do not expose Claude's Bash background parameter. For the asynchronous `codex` executor and long-lived viewer, use explicit shell backgrounding with logs and a PID where relevant:

```
codex exec "<prompt>" > "/tmp/perry-dispatch-<task-id>.log" 2>&1 &
echo $! > "/tmp/perry-dispatch-<task-id>.pid"
```

Poll the RESULT log/process for dispatch completion. Neither host has a Claude background-task notification. The same fallback applies to `perry-viewer` via `nohup`; see `work/reference/viewer.md`.

## What Perry does not depend on

- No scheduled wakeup or cron host feature.
- No plan-mode host feature.
- No host-provided memory.
- No network fetch for core project-state behavior.

When adding another host capability, add a matrix column, define its fallback, and test its detection and installation path.
