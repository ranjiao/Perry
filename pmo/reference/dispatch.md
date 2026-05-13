# `/pmo dispatch <task-id>` — fully automated end-to-end

Same goal as `delegate` (see `delegate.md`) but **fully automated**. PMO renders the prompt, fires it at an executor, watches for completion, parses the result, runs any objective verification commands declared in the spec, writes an evidence file, updates BOARD + journal, and reports back. Subjective verification stays with the user (status moves to `review`, not `done`).

## Pre-flight (any failure → refuse and fall back to `delegate`)

1. `evidence/<YYYY-MM>/<TASK-ID>-spec.md` exists.
2. Spec contains `Dispatch mode: auto` (default `manual` — explicit opt-in required).
3. Spec contains `Executor: claude-subagent | codex` (not `manual`). **If spec is `Dispatch mode: auto` but `Executor` is missing**, use `AskUserQuestion` (header `"Executor"`, options = `claude-subagent | codex (if installed) | manual — fall back to delegate`) for a one-shot choice this run; do NOT silently default. Persist the answer back into the spec only if the user explicitly says "save this for next time". On Codex (`$HOST = codex-cli`) **omit** the `claude-subagent` option (the executor isn't available) — see `../../reference/host-capabilities.md`. If a spec already pins `Executor: claude-subagent` on Codex, refuse the dispatch and tell the user to switch to `codex` or fall back to `/pmo delegate`.
4. **Safety re-validation**: scan spec's `Files in scope`, `Deliverable`, `Out of scope` against the project hook's high-stakes operations list (in `.perry/hook.md`). Any positive match in `Files in scope` or `Deliverable` (i.e. the task touches it) → refuse. Any positive match in `Out of scope` (task explicitly avoids it) → that's a green light for the line in question.
5. Spec contains a `Subjective verification:` section (may be `(none)`); items there will be surfaced to the user at completion, never auto-validated.
5a. **Invariant pre-check** (see `../../reference/architecture.md § Dispatch integration`): read spec's `Touches invariants:` field. For each listed INV-NNN, look it up in `architecture/INVARIANTS.md`:
    - **Hard** invariants touched → use `AskUserQuestion` (header = `INV-NNN`, options): `Proceed — change has been reviewed (Recommended only with reason) | Refuse — revise spec first | Refuse — escalate to manual delegate`. "Proceed" requires a written one-line justification; it gets copied into the dispatch evidence file's header. If the user picks Refuse, abort dispatch.
    - **Soft** invariants touched → one `AskUserQuestion` (header = `Invariants`, multiSelect): each soft INV-NNN as an option with description = the rule text. Selecting an option = acknowledgement, recorded in the dispatch evidence.
    - Field is `(none)` or absent → no friction. (Absent is a spec-quality issue surfaced by `triage`, not a dispatch blocker.)
5b. **Deployed-task pre-check**: if spec has `Deployed: yes`, verify the spec contains a non-empty `## Observability` section (Success signal / Failure diagnosis / Runbook path). If missing → refuse and ask user to fix the spec first. The runbook file itself is not required to exist yet at dispatch time (often the dispatched task creates it) — only the observability spec field is mandatory.
6. **Concurrency check**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" register <task-id> <executor>`. Exit 0 = slot reserved, proceed. Exit 1 = limit hit; stderr lists what's currently in flight. On limit-hit, ask the user via `AskUserQuestion` (header `"Dispatch full"`, options): `Wait — show in-flight (Recommended) | Switch to other executor (if it has slots) | Fall back to /pmo delegate (manual paste)`. Default limits: 2 codex, 2 claude-subagent, 3 total — overridable via env (`PERRY_MAX_DISPATCH_CODEX`, `PERRY_MAX_DISPATCH_SUBAGENT`, `PERRY_MAX_DISPATCH_TOTAL`). On Codex the cap is advisory across separate sessions — see `../../reference/host-capabilities.md § perry-dispatch-limit`.

## Dispatch — per executor

### `Executor: claude-subagent` (Claude Code only)

- **Host gate**: requires `$HOST = claude-code`. On Codex this executor is unavailable — refuse and route per `../../reference/host-capabilities.md § Agent / subagent_type`.
- Use the `Agent` tool with `subagent_type: general-purpose`.
- Build prompt = spec full text + project hook safety constraints + Git expectation block (see `git-boundaries.md`) + RESULT format (below).
- Async-ness from spec's size hint: `Estimated cycle: small` → `run_in_background: false`; `medium | large` → `run_in_background: true`.
- Sub-agent shares parent cwd. For split-repo projects: instruct sub-agent to use `git -C <code-repo-path> ...` for every git command (do NOT `cd`; preserves parent cwd state).

### `Executor: codex`

- **MANDATORY pre-flight** before the first codex dispatch in any session (or after the 6h smoke cache expires):
  ```
  bash "$PERRY_HOME/bin/perry-codex-preflight"
  ```
  The script: (a) `codex --version` ≥ `PERRY_CODEX_MIN_VERSION` (default `0.100.0`); (b) smoke test (`codex exec "Reply with just: PERRY_OK"`, 60s timeout if `timeout` / `gtimeout` is installed). Cached 6h at `~/.cache/perry/codex-smoke-pass`. Exit non-0 → **refuse + surface stderr verbatim + fall back to delegate**. Catches stuck CLI / broken auth / version-rejected-by-API BEFORE we fire async dispatch that would silently hang.
- Then: Bash → `cd <code-repo-path> && codex exec "<prompt>"`.
- Always async (codex is its own session). On Claude Code, pass `run_in_background: true`. On Codex (`$HOST = codex-cli`), wrap in shell backgrounding (`codex exec "..." > /tmp/perry-dispatch-<id>.log 2>&1 &`); see `../../reference/host-capabilities.md § Bash run_in_background → shell &`.
- Prompt MUST be self-contained (codex doesn't see the journal, BOARD, or any prior context). Include: spec full text + relevant project hook excerpts + git expectation + RESULT format + the explicit list of files codex can read for context.
- Capture stdout to a temp file; on completion, parse for the RESULT block.
- If the long-running codex call fails (non-0 exit / no RESULT block / timeout), per the failure handling below, mark task `review` and surface raw output. Pre-flight is the cheap pre-check; this is the post-check.

## Common (post-dispatch, before completion)

- Append `## Status changes` line to today's journal: `[TASK-X] not_started → in_progress · dispatched HH:MM · executor=<name> · async=<bool>`.
- Update BOARD row: status → `in_progress`; Next action → "dispatched <time>; awaiting completion".
- Reply to user: `Dispatched <TASK-X> via <executor>. Will report when done.` Do NOT block waiting for sync; rely on runtime notification.

## On completion (notification arrives)

0. **Release the concurrency slot first thing**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`. Do this BEFORE any verification work, so a slow verification step doesn't keep blocking other dispatches. (Stale markers auto-clean after `PERRY_DISPATCH_STALE_TTL` seconds — default 1h — covering the case where PMO crashed mid-completion.)
1. Read the agent's RESULT block. Required fields:
   - `PR URL:` (or "n/a — direct push" with explicit reason)
   - `Files changed: <count>` + bullet list
   - `Tests: <pass>/<total>` + command used
   - `Cycle time: <minutes>` (for calibration)
   - `Notes:` (anything unusual)
2. Run **objective verification** from the spec's `Verification` section. Anything that looks like a runnable command (starts with `$`, names a CLI like `pytest` / `gh` / `gim`, or has a clearly executable shape) — run it. Capture output.
3. Cross-check against `Out of scope` — if the agent's `Files changed` list contains paths declared out-of-scope, raise a hard failure (likely scope creep or safety violation).
4. **Status decision**:
   - All objective verifications pass + no scope violation + RESULT block has all required fields → status `review` (NEVER auto-`done`; subjective verification is the user's, per the project's standing rule).
   - Anything fails → status `review` with failure annotation; no auto-retry, no auto-rollback.
5. Write `evidence/<YYYY-MM>/<TASK-ID>-dispatch-<YYYY-MM-DD-HHMM>.md`:
   - Header (date, executor, async, cycle time)
   - Full agent RESULT block verbatim
   - Objective verification commands + their outputs
   - Subjective verification items (copied from spec, marked `[user-verify]`)
   - PR URL + branch + commit SHA
6. Update BOARD row: status → `review`; Next action → "user verifies subjective items: <…>"; Evidence → path of dispatch file.
7. Append `## Status changes` to today's journal: `[TASK-X] in_progress → review · executor=<name> · cycle=<min> · evidence: <path>`.
8. Surface to user: pass/fail summary + 1-line subjective verification ask.

## Failure handling (mark `review`, no auto-retry)

- Executor crashed / non-zero exit / timeout → release the slot (`bash "$PERRY_HOME/bin/perry-dispatch-limit" release <task-id>`), write evidence with raw output, status `review`, surface failure summary, ask user retry / fix manually / drop.
- ff-only PR push failed → same, with manual-resolution hint.
- Agent declared `done` but tests failed → same.
- The release call MUST run on every failure path, not just success — otherwise a failed dispatch leaks a slot until stale-TTL expires.

## Cost / quota awareness

- Each `claude-subagent` call counts against the parent CC session quota (5-hour Sonnet caps, weekly Opus caps).
- Each `codex` call counts against OpenAI quota.
- PMO does not enforce a per-call dollar cap; spec writer chooses executor as a quota-routing hint.
- Hooks may declare project-specific quota limits (e.g., "no more than 5 dispatches per day") — PMO honors those if present.

## RESULT block format (required from any dispatched agent)

```
=== RESULT ===
PR URL: <url>           # or "n/a — direct push" with reason
Files changed: <count>
  - path/file1.py
  - path/file2.py
  ...
Tests: <pass>/<total> (command: <pytest ...>)
Cycle time: <minutes>
Notes: <anything unusual>
=== END RESULT ===
```
