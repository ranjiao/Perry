# Host capabilities matrix

Perry runs on **Claude Code**, **OpenCode**, and **Codex CLI**. It registers **one** skill, `perry`, on every host; `goals`, `work`, and `decide` are lanes loaded on demand. OpenCode is an explicitly added host adapter after DESIGN-003 decision 8; this support does not reinterpret that older Claude+Codex decision as having already authorized OpenCode.

> **This page is outside the shorthand carve-out.** It owns host translation, so all commands and directories below use the live vocabulary. This is a source-review requirement; the retired shipped-vocabulary byte pins no longer enforce it.

## Detect once per session

After deriving `$PERRY_HOME`, run:

```
bash "$PERRY_HOME/tools/detect-host.sh"
```

The result is `claude-code`, `opencode`, `codex-cli`, or `unknown`. Remember it as `$HOST`; do not re-run per subcommand or when the router hands to a lane. An explanation needs no detection unless its answer or a choice prompt depends on the host (`reference/startup.md`). If it is `unknown`, retain the original `claude-code` fallback, mention the ambiguity once, and recommend an override:

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

This matrix describes Perry's existing CLI adapters and executor identifiers.
A desktop/session environment may expose additional input, job or agent tools.
Inspect the actual available tools and their instructions; use a native choice
UI when available and permitted, otherwise the fallback below. Tool availability
is not delegation or messaging authority. Environment/user restrictions win;
never invent a new Perry executor ID or bypass a strict existing adapter check.


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
| Session usage telemetry | none Perry can bind: subagents carry the main session's `CLAUDE_CODE_SESSION_ID`, so `unknown` | none Perry can read: `unknown` | `CODEX_THREAD_ID` names `~/.codex/sessions/*/*/*/rollout-*-<id>.jsonl` |

The executor enum is `claude-subagent | opencode-subagent | codex | manual`. The host matrix is strict:

| Host | Allowed automated executors |
|---|---|
| `claude-code` | `claude-subagent`, `codex` |
| `opencode` | `opencode-subagent`, `codex` |
| `codex-cli` | `codex` |

If a spec pins a native executor for another host, refuse rather than silently reroute. `manual` routes to `/perry work delegate`; it is never registered with `tools/dispatch_limit.sh`. When an auto spec omits `Executor`, offer only executors valid for `$HOST`, plus `manual`.

`tools/context_budget.py` binds its optional usage report to that identity, never
to the newest transcript. Missing identity, ambiguous matches and unsupported hosts
report `unknown`. Claude Code is always unknown here because its session identity
is not verified; `--session` is only an explicit caller-asserted reading. Neither
unknown nor a large token count blocks work or requires a handoff. Session changes
belong to the agent environment and user. Details: `work/reference/budget-boundary.md` and the current `tools/context_budget.py --help`.

## Prompt rendering

An instruction to use `AskUserQuestion` means the host's native choice UI. Claude Code uses `AskUserQuestion`; OpenCode uses `question` with equivalent labels, options and recommendation. Translate Claude's `multiSelect: true` to OpenCode's `multiple: true` exactly; passing the Claude field name to OpenCode is invalid. For the baseline Codex CLI fallback, print numbered options and wait for free text (a provided session choice tool takes precedence):

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

OpenCode and Codex do not expose Claude's Bash background parameter. For a host with a native job/completion API, use it and retain the completion
result. Where no such API exists, follow `work/reference/dispatch.md` for an
explicit background process, unique project-owned scratch logs/PID, and bounded
polling. Never put logs in shared task-ID-only `/tmp` paths. A PID or fresh native
event alone does not prove liveness or successful completion.

## What Perry does not depend on

- No scheduled wakeup or cron host feature.
- No plan-mode host feature.
- No host-provided memory.
- No network fetch for core project-state behavior.

When adding another host capability, add a matrix column, define its fallback, and test its detection and installation path.
