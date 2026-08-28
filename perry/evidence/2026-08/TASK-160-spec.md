# TASK-160 — the dispatch limiter reaps a live slot after an hour

> Source: found on 2026-08-21 by the counter disagreeing with reality
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one marker's lifetime
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured 2026-08-21

`PERRY_DISPATCH_STALE_TTL` defaults to **3600s**. TASK-142 was **72 minutes**
into its run when its marker was reaped, and `perry-dispatch-limit list`
reported **2 of 3 while three agents were live**.

Observed cycles the same night: **TASK-148 2h15m**, TASK-146 55m, TASK-119 45m,
TASK-159 55m, TASK-136 55m. **The longest real cycle is more than double the
TTL**, so the cap has not been the cap for a while — silently, because nothing
says a slot was reaped.

## Why the sweep is not the thing to delete

It exists for a real reason: **a crashed agent would otherwise hold a slot
forever**, and this project has had agents die at a 600s watchdog. Removing it
trades a silent over-count for a silent under-count.

So the shape is one of:

1. **tie the marker to something that knows whether the agent is alive** — a pid,
   a process handle, a heartbeat the dispatcher touches;
2. **raise the TTL past the longest real cycle *and* make the sweep say out loud
   that it reaped a slot** — cheaper, and it converts a silent failure into a
   loud one, which this project generally prefers to a clever fix.

Take one and **say what the other would have cost.** If you take (2), the number
you pick must be justified from the measurements above, not chosen.

## Verification — V3

1. **A live dispatch keeps its slot for its whole run.** Reproduce the failure
   first: a marker older than the TTL whose dispatch is still live is currently
   reaped and the count drops — show that, then show your change holding it.
2. **A dispatch whose process is genuinely gone still frees one.** This is the
   half that must not regress; a fix that keeps every marker forever fails here.
3. **A reap is reported, never silent** — whichever shape you took. The reason
   the defect ran for hours is that nothing said anything.
4. **`bin/perry-task § live_dispatch_ids` still works.** TASK-142 landed a
   *reader* of this marker directory that honours the same TTL and deliberately
   never calls the tool, *"because a `list --json` that could delete another
   session's slot is a read command with a side effect on shared state."* If your
   change moves what a marker means, that reader has to follow — and its
   `in_progress_with_no_live_run` check must keep both halves.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-dispatch-limit`
- `bin/perry-task § live_dispatch_ids` **only** if the marker's meaning changes
- `work/reference/dispatch.md` where it states the cap's behaviour
- focused tests

## Out of scope

- The cap's default value, and `PERRY_MAX_DISPATCH_SUBAGENT`.
- The executor axis (`codex` / `claude-subagent` / `opencode-subagent`).
- Anything under `perry/`.
