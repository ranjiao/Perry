# TASK-249 — bash tests/run WRITES PERRY STATE INTO THE REPOSITORY IT RUNS IN — four files, via an intake-sweep discharging a real board row

> Consolidated from the board row 2026-08-30. The row's own fields are the
> acceptance criteria; this file is where a V4 reviewer reads them.

## Why this row exists

Proved by a controlled experiment by the TASK-050 round 11 agent, 2026-08-30, and independently the cause of a stray event the PMO caught in TASK-241's merge an hour earlier. Running the suite modifies .perry/events.jsonl, perry/BOARD.md, perry/intake.jsonl and perry/journal/<today>.md in whatever repository it executes in, by running an intake-sweep that discharges one board row. The experiment: restore the four files, run the suite, and the same four move again. THE SWEEP IS IDEMPOTENT, WHICH IS WHY A SECOND RUN LOOKS CLEAN — that is why nobody noticed. It matters beyond tidiness: two of the suite's three standing failures are data-dependent on board state, so the suite perturbs the very state its own results depend on. It is also how a stray intake-sweep event with actor 'agent' ended up committed on a coding branch and was caught only because an append-only file conflicted at merge; a fast-forward would have carried it into main silently.

## Deliverable

—

## Verification — V4

V4

## Out of scope

—

## Where to start

Startable. Start from TASK-050 round 11's result, which carries the controlled experiment, and from the TASK-241 merge, where the stray event surfaced. The idempotence is the reason this survived: the first run in a fresh clone moves four files, and every run after it looks clean, so the natural way to check — run it twice and diff — reports nothing. Restore the four files first, then run once.
