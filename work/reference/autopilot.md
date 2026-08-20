# `/pmo autopilot` — autonomous BOARD-driving loop

> **Status changes go through `bin/perry-task`.** Autopilot always lands a row
> at `review`, never at `done` — that is `perry-task status <ID> --status
> review`, not a hand edit. This file is loaded on its own, so the invariant in
> `reference/subcommands.md` does not reach it; a loop that hand-edits rows
> would generate one post-tool edit per dispatch and drown the drift signal in
> output it produced itself.
>
> **Stage moves go through the tool too** — `perry-task stage <ID> --stage
> <name>`, which re-stamps `Stage since` in the same write. On a `pipeline`- or
> `queue`-mode track a completion often moves the stage as well as the status,
> and the two are orthogonal: a `draft → review` stage move produces no status
> change and would leave no trace at all if hand-edited. A hand-edited cell
> leaves the dwell clock reading from whenever the row was created, so triage's
> first question — what is aging in which stage — measures nothing.


Walks the BOARD top-to-bottom and dispatches every task that's safe to dispatch without user input, until budget exhausts or no actionable tasks remain. Designed for "user goes to lunch / sleep / out for the day, comes back to a wall of `review` rows".

The executor enum is `claude-subagent | opencode-subagent | codex | manual`. Autopilot skips `manual`; it enforces the host matrix without substitution: Claude Code native = `claude-subagent`, OpenCode native = synchronous `opencode-subagent`, Codex CLI has no native subagent, and `codex` works on all three.

**Autopilot does NOT close tasks.** Per the project's standing rule (subjective verification = human), every successfully-completed dispatch lands at `review`, not `done`. The user reviews on return.

## When to use

- You have ≥ 3 P0/P1 specs ready to dispatch (`Dispatch mode: auto`, all dependencies resolved).
- You're about to be away long enough that synchronous dispatch + babysit is wasteful.
- The work is well-scoped — specs are in good shape, executors are pinned, hook safety list is well-curated.

## When NOT to use

- Specs are unclear or evolving (autopilot's safety pre-flight will refuse most of them anyway).
- High-stakes work (anything matching the hook's high-stakes list — autopilot will skip these by design).
- You expect to want mid-run intervention more than just `Ctrl-C`.

## First-run vs subsequent-run

**First time `/pmo autopilot` is invoked in a given project** (detected by absence of marker file at `~/.cache/perry/autopilot/<sha-of-project-root>.first-run-done`):

1. Print the **first-run briefing** verbatim (see below).
2. **Force `--dry-run` mode** for this invocation regardless of flags. Print the full plan (would-dispatch list + skip list + reasons) but do NOT call any dispatch.
3. After printing the plan, use `AskUserQuestion` (header `"First run"`, options): `Run this plan for real now (Recommended) | Edit task list before running | Cancel — review specs first`. The Recommended option is "for real now".
4. If user picks "Run for real" → mark first-run-done file, then re-execute the same plan as a real run.
5. If user picks "Edit" or "Cancel" → exit; do NOT mark first-run-done. Next invocation is still treated as first-run.

**Subsequent invocations in the same project**: skip the briefing + dry-run gate; go straight to the standard pre-flight + AskUserQuestion confirm + execute.

The first-run marker exists at `~/.cache/perry/autopilot/<sha-of-project-root>.first-run-done` (gitignored, machine-local). To force a re-briefing in a project: `rm ~/.cache/perry/autopilot/<sha>.first-run-done` (or compute sha via `echo -n "$(pwd)" | shasum`).

### First-run briefing (print verbatim before the dry-run)

```
🤖 /pmo autopilot — first run in this project

What this command does:
  Walks the BOARD top-to-bottom (P0 → P1 → P2). For each open row that
  is auto-dispatchable, runs the full /pmo dispatch flow with all
  existing safety pre-flight gates (codex preflight, dispatch-limit,
  hook safety scan, spec re-validation). Repeats until budget exhausts
  or no candidates remain.

What it CAN do:
  - Dispatch tasks marked `Dispatch mode: auto` with a host-valid executor:
    `claude-subagent | opencode-subagent | codex`
  - Run objective verification commands declared in spec
  - Write evidence files, update BOARD rows to `review`, append journal entries
  - Wait when dispatch concurrency cap is hit (poll up to 10 min)

What it CANNOT do:
  - Close any task as `done` (subjective verification = human, always)
  - Modify spec files (no scope changes, no priority bumps, no executor swaps)
  - Touch the hook's high-stakes list (production deploys / prod credentials / .env / paid APIs / cost ceiling)
  - Make ADR decisions (`/pmo decide` requires user)
  - Run `triage` aggressively or generate cadence reports
  - Retry the same task ≥ 2 times (one failure → flag for review, move on)

Default budget (override via flags):
  --max-dispatches=10    cumulative dispatches per run
  --max-duration=2h      wall clock
  --max-failures=3       cumulative failures (any kind)
  --dry-run              print the plan, don't execute

How to stop autopilot mid-run:
  (a) Close the host session — the autopilot loop dies; partial
      progress already on disk is preserved (BOARD rows, evidence, journal
      entries). In-flight dispatches keep running in their own processes.
  (b) From a separate shell:
        touch ~/.cache/perry/autopilot.stop
      Autopilot checks for this file before every iteration; if present,
      it deletes the file and exits cleanly with a partial summary.

What you'll come back to:
  - evidence/<YYYY-MM>/autopilot-<YYYY-MM-DD-HHMM>.md (the run report)
  - Each dispatched task at status `review` with subjective verification
    items listed for your eyes
  - BOARD updated; journal entries written
  - Failed tasks (if any) at status `review` with failure annotation

First-run protection:
  This run is forced to --dry-run mode. After you see the plan, you'll
  be asked whether to execute for real. Subsequent runs skip this gate.
```

## Pre-flight (every invocation, before AskUserQuestion confirm)

0. **Safety-list gate — refuse if the high-stakes list is missing or empty.**
   Autopilot's central safety property is "never auto-dispatch a task that
   touches something dangerous". That property is implemented entirely by
   matching spec fields against `.perry/hook.md § High-stakes operations`. With
   no list, the scan matches nothing and every `Dispatch mode: auto` row looks
   safe — the gate fails open, silently. So:

   ```
   "$PERRY_HOME/bin/perry-state" --section project
   ```
   If `project.hook.high_stakes_armed` is `false` → **refuse to run autopilot.**
   Print:
   > "Autopilot needs a high-stakes list to refuse against. `.perry/hook.md` has
   > none, so the safety scan would pass everything. Run `/pmo` bootstrap to
   > write the default list, or add a `## High-stakes operations` section, then
   > re-run."

   This is a hard refusal, not a warning, and it is not overridable by a flag.
   `/pmo dispatch` on a single task stays available — one dispatch is a
   deliberate act the user is watching; a 10-dispatch unattended loop is not.

1. Run the standup ritual (per `SKILL.md § Mandatory first move`).
2. Check stop signal: if `~/.cache/perry/autopilot.stop` exists, refuse and ask user to delete it.
3. Read the BOARD top-to-bottom. For each open row, classify:
   - **Eligible**: status ∈ {`not_started`, `blocked` with all blockers resolved}, has `evidence/<YYYY-MM>/<TASK-ID>-spec.md` with `Dispatch mode: auto` + non-`manual` Executor, hook safety scan passes, all listed dependencies resolved.
   - **Skipped — manual**: `Dispatch mode: manual` (intended) — these are listed in the skip section but never auto-dispatched.
   - **Skipped — high-stakes**: hook safety scan flags a match → never auto-dispatched even if `Dispatch mode: auto` (safety > flag). The scan is `"$PERRY_HOME/bin/perry-state" --escalation-scan <spec>` and its exit code is the verdict (`dispatch.md` pre-flight step 4) — autopilot runs unattended, so this is the one place the match must never be performed by reading a fragment list and judging by eye.
   - **Skipped — no spec**: P0/P1 missing `<TASK-ID>-spec.md` → never auto-dispatched (spec is the safety contract).
   - **Skipped — blocked**: open dependency.
   - **Skipped — already in flight**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" list` shows it as currently running.
    - **Skipped — host mismatch**: the spec pins a native executor unavailable on `$HOST`. Claude Code permits `claude-subagent`; OpenCode permits `opencode-subagent`; Codex CLI permits neither. Every host also permits `codex`. The spec must be edited explicitly; autopilot never reroutes it.
   - **Skipped — review/done**: already past dispatch.
4. Apply priority order: P0 first, then P1, then P2 (within each, oldest-pending first).
5. Truncate eligible list to `max-dispatches` (default 10).
6. Compute estimated total cycle time using each spec's `Estimated cycle` field (small=1m, medium=5m, large=15m baseline; per-project hook may override). Compare to `max-duration` (default 2h).
7. Print the plan:
   - Title, current time, project name
   - **Will dispatch** (numbered list with TASK-ID / Title / Executor / Estimated cycle)
   - **Skipped** (grouped by reason)
   - **Budget**: dispatches=X/10, duration=~Ym estimated / 120m cap, failures=0/3
   - **Stop signals reminder**: close session, or `touch ~/.cache/perry/autopilot.stop`
8. **First run only**: this is the dry-run; proceed to AskUserQuestion `First run` (see above).
9. **Subsequent runs**: AskUserQuestion (header `"Autopilot"`, options): `Proceed (Recommended) | Edit task list | Cancel`.

## Run loop (after user confirms)

Initialize counters: `dispatches_done = 0`, `failures = 0`, `start_time = now`. Open run summary file at `evidence/<YYYY-MM>/autopilot-<YYYY-MM-DD-HHMM>.md` and write the plan + decisions log header.

Repeat:

1. **Stop checks** (any failure → exit cleanly with summary):
   - File `~/.cache/perry/autopilot.stop` exists → delete it + exit
   - `dispatches_done >= max_dispatches` → exit
   - `now - start_time >= max_duration` → exit
   - `failures >= max_failures` → exit
   - No remaining eligible tasks → exit (success)

2. **Saturate dispatch slots**:
   - Run `bash "$PERRY_HOME/bin/perry-dispatch-limit" list` to see current concurrency.
   - While slots available AND eligible tasks remain:
     - Pick next task (P0 > P1 > P2; oldest first).
     - Run full `/pmo dispatch <task-id>` flow (see `dispatch.md`):
       - Pre-flight (codex preflight if codex; safety re-validation; concurrency register)
        - Apply dispatch.md's mandatory `in_progress` transition, then dispatch via the selected executor. Claude native medium/large work and `codex` are async; OpenCode native `Task(subagent_type: general)` is synchronous and completes this item before another native Task starts.
       - Increment `dispatches_done`. The journal status-change line is already written — `dispatch` ran `perry-task start`, which writes row, journal and event together. Appending one here duplicates it.
       - Append a row to the run summary's per-task table: dispatched at, executor.

3. **Process completion**:
    - OpenCode native Task returns synchronously: release its slot and process its RESULT immediately. Do not wait for or promise a background notification.
    - Claude Code background calls use the runtime completion notification. OpenCode/Codex `codex` calls use the no-background-shell-tool fallback: poll `/tmp/perry-dispatch-<id>.log` and its PID every 30s; completion is `=== END RESULT ===` or process exit.
   - For each completion, run the standard post-completion routine (see `dispatch.md` § "On completion"): release slot, parse RESULT, run objective verification, write evidence file, then move the row with `perry-task status <ID> --status review` — one call that updates `BOARD.md` and appends the journal line. Do not do either by hand: an autopilot run that hand-edits the board on every completion drowns the drift signal in output it produced itself, which is the failure this file's own header warns about.
   - Append result to the run summary's per-task table: completed at, status, evidence path.
   - If completion was a failure (executor error / verification fail / scope creep) → `failures += 1`. Mark the task `review` with the failure named: `perry-task status <ID> --status review --reason "<what failed>"`. **Never auto-retry.**

4. If concurrency cap is fully occupied and no completion arrives within 10 min → log "stalled" + exit. (Likely a stuck background process; user investigates.)

## What autopilot CANNOT do (enforced)

- **Close any task** (`done`). Even if all objective verifications pass, status stops at `review`.
- **Modify any spec file**. Specs reflect user intent; autopilot is an executor, not a planner.
- **Override hook safety**. If the spec's `Files in scope` / `Deliverable` matches a hook high-stakes pattern, refuse + skip + log; do not "rationalize" overrides.
- **Auto-retry a failed task**. One attempt per autopilot run.
- **Run `triage`** in a way that moves rows. Read-only "what's stale" reporting is OK; rewriting BOARD is not.
- **Generate cadence reports requiring user input** (`mid-phase-review`, `end-phase-retro`). These pause autopilot to wait for user.
- **Make ADRs**. `/pmo decide` is human.
- **Reorder BOARD priority**. P0/P1/P2 reflect user intent.
- **Issue `AskUserQuestion`** mid-run. The pre-flight confirmation is the single consent point. Inside the loop, autopilot only logs and proceeds; it never blocks waiting for user.

## Run summary file

`evidence/<YYYY-MM>/autopilot-<YYYY-MM-DD-HHMM>.md` — written incrementally so a session crash mid-run leaves a partial summary.

Sections:

```markdown
# Autopilot run — <YYYY-MM-DD HH:MM> → <ended at>

## Plan (frozen at start)
- Will dispatch: <list>
- Skipped: <grouped by reason>
- Budget: dispatches=X/10, duration=~Ym/120m, failures=0/3

## Per-task timeline
| Task | Executor | Dispatched | Completed | Status | Evidence | Notes |
|---|---|---|---|---|---|---|
| DATA-008-B | codex | 14:23 | 14:31 | review | evidence/...md | tests pass; subjective: pipeline-002 reproducibility |
| ... |

## Decisions made by autopilot
- 2026-05-07 14:23 — picked codex executor for DATA-008-B (per spec)
- 2026-05-07 14:31 — DATA-009 verification step `pytest tests/integration/test_vendor_api_health.py` failed; marked review; did NOT retry per blacklist
- ...

## Stop reason
<one of: All eligible tasks dispatched / max-dispatches hit / max-duration hit / max-failures hit / autopilot.stop signal / session closed mid-run / stalled (no completion in 10m)>

## Left for user
- DATA-008-B (review): user verifies pipeline-002 §1.2.A R-2 result reproducibility
- DATA-009 (review, FAILED): pytest failed with <one-line summary>; user investigates
- TECH-001 (skipped — manual): waiting for user to flip Dispatch mode after spec review
- ...

## Counters
- Dispatches: 7/10 attempted, 6 reached review, 1 failed
- Wall clock: 1h23m / 2h cap
- Failures: 1/3
```

## Per-project flags / overrides

If a project's `.perry/hook.md` includes an `## Autopilot defaults` section, those defaults override the skill defaults. Recognized keys:

```
Autopilot defaults:
- max_dispatches: 5         # tighter than the global default
- max_duration_min: 60
- max_failures: 2
- excluded_tasks: TASK-X    # always skip these even if eligible
```

This lets project hooks tune autopilot to their actual quota / risk tolerance without skill PRs.

## Stop-signal cleanup

If autopilot exits via the `autopilot.stop` signal, it deletes the file before exiting (so the next invocation isn't pre-stopped). If autopilot exits any other way, the file is left untouched.
