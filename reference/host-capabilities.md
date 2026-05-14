# Host capabilities matrix

Perry runs on two hosts: **Claude Code** (full tool surface) and **Codex CLI** (narrower). All four Perry skills branch on `$HOST` at standup; this file is the single source of truth for what differs. SKILL.md files name the capability and link here; they do not inline per-host fallbacks.

## Detect once per session

The standup ritual of every Perry skill (`/perry`, `/okr`, `/pmo`, `/design`) sets `$PERRY_HOME` first (derived from the SKILL.md path it just read; see § `$PERRY_HOME` below), then runs:

```
bash "$PERRY_HOME/bin/perry-detect-host"
```

The script prints one of: `claude-code`, `codex-cli`, `unknown`. Remember the result as `$HOST` for the rest of the conversation; do not re-run per subcommand.

If `unknown`, default behavior to `claude-code` (the original target host) but mention the ambiguity to the user once and recommend they set `PERRY_HOST` in their shell profile.

**Manual override (always wins, recommended for both hosts):**
```
export PERRY_HOST=claude-code      # or codex-cli
```

### Auto-detection details (verified 2026-05 against codex-cli 0.130.0 + Claude Code 2.1.137)

The script uses env-var sniffing in this order:

1. **`CODEX_*` first** — `CODEX_SANDBOX`, `CODEX_THREAD_ID`, or any var starting with `CODEX_`. Codex sets these; Claude Code does not.
2. **`CLAUDE*` second** — `CLAUDECODE=1`, `CLAUDE_CODE_ENTRYPOINT=cli`. Claude Code sets these.
3. **Parent-process name** — best-effort fallback (`ps -p $PPID -o comm=`). Useful when env vars aren't set; **does not work in Codex's seatbelt sandbox** (process inspection is blocked → `ps` returns empty).

**Why CODEX_ before CLAUDE_**: when Claude Code launches `codex exec` (e.g., `/pmo dispatch` with `Executor: codex`), the nested shell inherits `CLAUDECODE=1` from the parent and *also* gets `CODEX_SANDBOX=seatbelt` from Codex itself. The innermost active runtime is Codex, so CODEX_* must win the tie. Standalone Codex sessions don't have CLAUDECODE; standalone Claude Code sessions don't have CODEX_*. The ordering is correct in all four scenarios.

**`CODEX_HOME` is NOT auto-set** — it's a user-level pointer to `~/.codex`. The script does not rely on it; the verified sentinels are `CODEX_SANDBOX` and `CODEX_THREAD_ID`.

If a future Codex version stops setting `CODEX_*` vars (or Claude Code starts setting them), the manual `PERRY_HOST` override is the durable contract.

## `$PERRY_HOME` — where Perry's bin/ + reference/ live

The perry/ root directory — contains `bin/`, `reference/`, `okr/`, `pmo/`, `design/`, and the top-level `SKILL.md`.

**Default install locations** (host-canonical):
- Claude Code: `$HOME/.claude/skills/perry`
- Codex CLI: `$HOME/.agents/skills/perry`

**Resolution at runtime**:
1. If `$PERRY_HOME` is set in env → use it (works for any custom install location, e.g., `$HOME/proj/Perry`).
2. Otherwise the standup ritual derives it from the path of the SKILL.md the agent just read: parent dir for the top-level `SKILL.md`, grandparent for `okr/SKILL.md` / `pmo/SKILL.md` / `design/SKILL.md`.
3. The bin scripts (`perry-update-check`, etc.) self-locate via `$0` as a third fallback for command-line invocations outside a Perry session.

Every bin/ invocation in SKILL.md and reference files is written as `bash "$PERRY_HOME/bin/<script>"` — the standup step that sets `$PERRY_HOME` is the precondition.

## Capability matrix

| Capability | claude-code | codex-cli |
|---|---|---|
| `AskUserQuestion` button choices | use the tool as documented | fall back to numbered free-text prompt (see below) |
| `Agent()` tool with `subagent_type` | use it for `claude-subagent` executor | not available — refuse `Executor: claude-subagent` and route to `codex` or manual delegate |
| `Bash` `run_in_background: true` parameter | pass it on the tool call | not a tool param — wrap in `&` background-shell pattern (see below) |
| `perry-dispatch-limit` concurrency cap | enforced (cross-task within session) | enforced filesystem-wide, but **advisory only** across separate codex sessions; surface as "local-only on Codex" |
| Skill discovery | reads `SKILL.md` frontmatter from `~/.claude/skills/<name>/` | reads `SKILL.md` frontmatter from `~/.agents/skills/<name>/` (also `$CWD/.agents/skills/`, `/etc/codex/skills/`). Both hosts use the same SKILL.md files; install paths differ. See `INSTALL.md` |
| Skill invocation | `/perry`, `/okr`, `/pmo`, `/design` slash commands | `/skills` then pick perry/okr/pmo/design, or `$perry` / `$pmo` / `$okr` / `$design` to mention, or implicit triggering on description match |
| `ScheduleWakeup` / `/loop` / `/schedule` | available (host-provided) | not available — Perry does not depend on these |
| Plan mode / `ExitPlanMode` | available | not available — Perry does not depend on these |

Anything in the SKILL.md files that mentions one of these capabilities by name is implicitly `claude-code`-shaped; the fallback below applies on Codex.

## Fallback patterns

### `AskUserQuestion` → numbered free-text prompt (codex-cli)

Whenever a SKILL.md says: *use `AskUserQuestion` (header `X`, options = `A | B (Recommended) | C`)*, on Codex print this in chat instead and wait for the user reply:

```
[X]
  1) A
  2) B  ← Recommended
  3) C
Reply with a number (1–3), or describe a different choice.
```

For `multiSelect: true`, append: *"Reply with comma-separated numbers (e.g. 1,3) or `all` / `none`."*

For `Other` follow-ups: take the user's free-text reply verbatim.

The chosen value is the same; only the rendering differs. All downstream logic (writing to `BOARD.md`, `phase/<NNN>-<slug>.md`, `design/<id>-*.md`, etc.) is unchanged.

### `Agent` / `subagent_type` → refuse `claude-subagent` executor (codex-cli)

`/pmo dispatch` and `/pmo autopilot` allow `Executor: claude-subagent | codex`. On Codex:

- If the spec pins `Executor: claude-subagent` → refuse the dispatch. Print: *"This spec pins `Executor: claude-subagent`, which only runs under Claude Code. On Codex, switch to `Executor: codex` (edit the spec) or fall back to `/pmo delegate` (manual paste)."* Do not silently re-route.
- If the spec pins `Executor: codex` → proceed normally; `codex exec` is host-agnostic.
- If the spec is `Dispatch mode: auto` with `Executor` missing → the standard `AskUserQuestion` for executor choice (see above) is rendered as the numbered free-text prompt; offer only `codex` and `manual` (omit `claude-subagent`).

Autopilot's eligibility scan should treat `Executor: claude-subagent` rows as **Skipped — host mismatch** on Codex, listed in the skip section with that reason.

### `Bash run_in_background: true` → shell `&` (codex-cli)

For `Executor: codex` dispatches (the only async executor on either host), Claude Code uses Bash's `run_in_background: true`. On Codex, run the same command via shell backgrounding:

```
codex exec "<prompt>" > "/tmp/perry-dispatch-<task-id>.log" 2>&1 &
echo $! > "/tmp/perry-dispatch-<task-id>.pid"
```

PMO writes the `🚀 In flight` BOARD line and the journal `## Status changes` line as usual. Completion is detected by the user telling PMO "it finished" (or by re-invoking `/pmo status`, which `tail`s the log file and parses the `=== RESULT ===` block). Codex has no automatic completion notification.

### `perry-dispatch-limit` → advisory on Codex

The script (`bin/perry-dispatch-limit`) writes marker files under `~/.cache/perry/in-flight/`, so it works on any host. The `register` / `release` / `list` / `check` semantics are unchanged. The caveat is observability: a separate Codex session sharing the same cache dir would honor the count, but Codex doesn't notify on completion, so a stale marker is more likely than under Claude Code. The 1h `PERRY_DISPATCH_STALE_TTL` already covers the worst case; just label the in-flight count as advisory in the standup `🚀 In flight` line when `$HOST = codex-cli`.

## What Perry does NOT depend on

For clarity (so future skill additions don't accidentally couple to host features):

- No `ScheduleWakeup` / `CronCreate`. Cadence rituals (`monday-plan`, `friday-review`, etc.) are user-triggered.
- No `EnterPlanMode` / `ExitPlanMode`. Plan-style flows are explicit chat sequences.
- No `WebFetch` / `WebSearch`. Perry never reaches the internet.
- No host-provided memory (Claude Code's `MEMORY.md` system). Perry's persistence is its own state files at the project root.

## Adding a new capability

If a future Perry feature requires a host capability not in the matrix:
1. Add the row above with `claude-code` and `codex-cli` columns.
2. If one column is empty, document the fallback inline below.
3. If neither host can do it, the feature does not belong in Perry.
