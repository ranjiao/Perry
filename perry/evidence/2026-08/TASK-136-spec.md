# TASK-136 — a queue track's SLA is parsed, stored, and never measured against anything

> Source: `perry/evidence/2026-08/TASK-133-track-experiment.md`, sharpened by
> `perry/evidence/2026-08/TASK-135-result.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — it computes a number the register already declares
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O1.2 (`perry/OKR.md` v2) — *"each live track's mode-specific
  triage question produces real output — pipeline WIP, queue SLA age, inquiry
  provenance"*

## Measured 2026-08-20, and TASK-135 made it sharper rather than softer

This repository declares `intake`, mode `queue`, with `sla: 5d`.
`perry-state` computes `stage_counts` and `wip_breaches` for it **and nothing
else.** The only consumer of a track's SLA anywhere is
`lib/__init__.py § classify_due`, which governs a **Commitments `Due` cell** —
not a row clock. **`today − Arrived` is computed nowhere.**

`modes/queue.md` says a track *without* an SLA *"cannot run the breach step, and
triage reports that rather than skipping it."* **A track with one cannot run it
either, and nothing reports that.**

TASK-135 then landed the move: rows now reach a queue track carrying a real
`Arrived`, carried on a queue→queue move and cleared on the way off, with the
argument that *"`Arrived` is not provenance, it is a queue's clock."* **So the
clock this project now maintains correctly still has no consumer.**

## Deliverable

The queue breach step exists: `today − Arrived` computed per row against its
track's SLA and surfaced in `perry-state --json`, so triage can ask **what
breached** rather than being told it cannot.

Two things the surrounding documents already decided, which you inherit:

- **`rows_with_no_computable_age` is the report that must keep working.** A row
  with no clock at all is a different finding from a row inside its SLA, and
  `cmd_route` had to stop writing `Arrived` onto pipeline rows precisely so this
  report could still see them. **A breach check that treats "no `Arrived`" as
  "not breached" silently merges the two.**
- **No default SLA.** `modes/queue.md` is explicit: a track without one cannot
  run the step, and **triage reports that** rather than skipping it. Do not
  invent a fallback.

## Verification — V3

1. **Three states on one fixture, asserted separately**: a row inside its SLA, a
   row past it (named, with its age), and a row with **no `Arrived`** — which
   must appear in `rows_with_no_computable_age` and **not** in the breach list.
2. **A track with no SLA reports that it cannot run the step**, by name, rather
   than reporting zero breaches. Zero and *cannot compute* are different answers
   and this project has a rule about saying so.
3. **The arithmetic is the boring kind.** A row whose `Arrived` is exactly the
   SLA old is on one declared side of the boundary and a test says which. An SLA
   token this project already parses (`5d`, `2w`) is what you measure against —
   **do not add a second spelling**; `lib § classify_due` already reads them.
4. **Reverting reddens the breach case and not the no-clock case**, separately.
5. On this repository, the `intake` track is **declared and empty** — so the
   check must produce a defensible answer for a track with no rows, and a test
   must say what that answer is.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-state`
- `schema/task-list-contract.md` or the state payload's documentation, wherever
  the new field is declared — **document it in the same change**, or the parity
  check reports it
- `work/reference/subcommands.md` — triage's queue question, only if what it can
  ask changes
- focused tests and fixtures

## Out of scope

- **Moving any live row onto `intake`.** TASK-135 shipped that tool; using it is
  the user's act. `git diff -- perry/` must end empty.
- `classify_due` and the Commitments `Due` cell.
- WIP limits, and `cmd_stage`'s lack of a WIP gate (TASK-135's question 3).
