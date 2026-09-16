# TASK-289 — spec, round 1

> Row: perry-task's --actor is optional and defaults, so a write to a lane-owned file can have no owner any session can claim
> Priority P1 · Owner Coding Agent · Rung V3 · Track intake
> Written 2026-09-16 by the PMO. Base: main's tip at dispatch.
> Touches architecture: `bin/ARCHITECTURE.md` § 5 (argument surface)
> Decision in force: `USER-950` — `--actor` becomes mandatory on every write; a write without it is refused; the skill documents' command examples carry it.

## Why

Re-measured 2026-09-16: all 27 of `perry-task`'s write subcommands accept
`--actor` and none requires it; an absent actor is recorded as `"agent"`
(`bin/perry-task` ~line 2822). So a write to a lane-owned store can carry an
owner no session can claim — the row's original incident was five link edges,
correct in themselves, that the session filing the row could not account for.
40 command examples in `SKILL.md`, the three lanes and `reference/` call a
`perry-task` writer without `--actor`.

## Round 1 — `perry-task`, and the documents

1. **Every `perry-task` subcommand that writes requires `--actor <value>`.** A
   write without it is refused before anything is read for writing: the tool's
   usage exit code (per `bin/ARCHITECTURE.md`), nothing written, and a message
   naming the flag and what a value should be (the session or lane that is writing,
   e.g. `pmo-agent`, `goals`). Derive the set of writing subcommands from the
   tool's own `SURFACE` (a subcommand that declares `writes`), not from a list you
   type — the 27 above is a measurement, not the rule.
2. **Read-only subcommands** (`list`, `events`, `asks`, `signoff-offer`, and any
   other with no `writes`) are unchanged and must not demand an actor.
3. **An empty value is refused too** (`--actor ""` is not an owner).
4. **No default remains** in the write path. The `"agent"` fallback that reads old
   events may stay for READING history written before this change — say which
   lines you kept and why.
5. **The documents:** every `perry-task` write example in `SKILL.md`, `goals/`,
   `work/`, `decide/` and `reference/` carries `--actor`. Keep each file within its
   byte budget (`tests/test_router_budget.py` and the lane budgets); the router
   `SKILL.md` must stay net bytes ≤ 0 — if an example cannot gain the flag without
   growing it, shorten nearby prose rather than dropping the example.

## Not this round

- **`bin/perry-goals`** (`commit`, `link`, and the `check`/`measure` verbs
  `TASK-264` is adding). `TASK-264` is changing that file now; it has been told to
  make its new verbs require `--actor`. `commit` and `link` are round 2, after
  `TASK-264` merges. **Do not edit `bin/perry-goals`.**
- `perry-decide`, `perry-config`, `perry-okr`, `perry-tasks` take no actor today;
  out of scope.

## Files in scope

- `bin/perry-task`
- `bin/lib/__init__.py` only for a shared helper
- `SKILL.md`, `goals/**/*.md`, `work/**/*.md`, `decide/**/*.md`, `reference/*.md` — examples only
- tests: every existing test that calls a `perry-task` writer without `--actor` must pass one; a new `tests/test_actor_required.py` with `COVERS` declared; `tests/durations.json` for it
- `perry/evidence/2026-09/TASK-289-result.md`

## What it must not do

1. Must not change what an existing event or record means, or rewrite history.
2. Must not edit `bin/perry-goals` (see above) or `schema/state-schema.json`.
3. Must not make a read-only subcommand demand an actor.
4. Tests write under temporary roots only (`NN-5`).

## Verification

1. Base check as the brief states.
2. `bash tests/run --tier affected --base <base>` each round; the full
   `bash tests/run` **and** `bash tests/run --tier slow` on the final commit with
   `PERRY_PROJECT` and `PERRY_HOME` unset, result committed first. Quote both.
3. **For every writing subcommand**, a test that it refuses without `--actor` and
   with `--actor ""`, writes nothing, and names the flag; and one representative
   write that succeeds with it and records that actor in the event.
4. **Every read-only subcommand** still runs without `--actor`.
5. **A document check**: no `perry-task <writing subcommand>` example in the
   shipped documents lacks `--actor` — as a test, so it cannot regress.
6. **Mutations**, each on a fresh scratch copy, each red on a named test:
   - one writing subcommand's requirement removed;
   - the empty-string value accepted;
   - a read-only subcommand made to demand the flag;
   - one document example with `--actor` removed.

## Subjective verification

(none)

## Out of scope

Round 2 (`perry-goals commit`/`link`), `TASK-291` (deferred to phase 005).
