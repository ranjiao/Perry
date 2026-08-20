# TASK-135 — a track can be declared but no existing row can be moved onto it

> Source: `perry/evidence/2026-08/TASK-133-track-experiment.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one subcommand, on a field the row already carries
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O1.1 (`perry/OKR.md` v2, Objective 1)

## Measured 2026-08-20

`--track` is accepted by exactly two commands: `add`, at creation, and `route`,
which turns an intake row into a task. There is **no** `perry-task track <id>`,
and `status --track` is refused.

So a project that declares a second track **starts it empty and cannot move any
existing work onto it.** This repository declared `intake` (mode `queue`) that
day and it is still empty, while the six rows that genuinely arrived rather than
being decomposed — TASK-124, 125, 126, 130, 131, 132 — belong on it and cannot
get there.

That is why KR-O1.1 was **not** met by the declaration: a track with no rows is
not a mode running on a live track.

## Deliverable

An existing row can change track. `--track` is accepted by a subcommand that
operates on a row that already exists — not only at creation and not only from
intake.

Two behaviours the move must get right, because `route` already does and a
second path that does not would make `Arrived` mean one thing per entrance:

1. **Moving onto a queue-mode track stamps `Arrived` and the track's first
   post-intake `Stage`**, the same way `route` does. `today − Arrived` is the
   number every SLA check measures, so a move that omits it silently exempts the
   row from the only clock governing it.
2. **Moving off a track does not silently strand those fields.** Decide what
   happens to `Stage` and `Arrived` when the destination track has no use for
   them, and say why in the code — dropping them loses history, keeping them
   leaves a queue's clock on a row no queue governs.

A move to a track the project has not declared is **refused by name**, listing
the declared tracks — the same shape as `delegate`'s refusal for an undeclared
role card.

## Verification — V3

1. **Six rows move.** Against a fixture whose register declares a `queue` track,
   six existing rows move onto it and the board renders them with `Arrived` and
   `Stage` populated; `perry-state --json` reports them under that track's
   `stage_counts`.
2. **The refusal is by name.** Moving to an undeclared track names the track and
   lists the declared ones; it does not create it and does not fail with a
   traceback.
3. **Both directions of the field question.** Whatever you decided in
   deliverable 2, a fixture proves it: move onto a queue track, then off it, and
   assert the resulting record — including the case where the row had an
   `Arrived` before the move.
4. **An event is written per move.** A track change nothing recorded is
   TASK-139's shape, and this project has that row open already.
5. **`perry-lint` reports no drift after a move** — the board is a projection,
   so a move that leaves the rendered file disagreeing with the store is a
   half-landed write.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-task`
- `schema/task-list-contract.md` **only if** the payload changes shape; adding a
  subcommand does not.
- focused tests and fixtures

## Out of scope

- **Moving the six live rows.** This row ships the tool; using it on this
  project's board is a separate act the user takes. `git diff -- perry/` must
  end empty.
- Declaring or changing a track's mode — that is `.perry/config.md`, the user's
  file.
- `conformance` checks about tracks (TASK-142's neighbourhood).
