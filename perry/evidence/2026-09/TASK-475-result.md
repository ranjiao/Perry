# TASK-475 result — `perry-goals objective add`

Date: 2026-09-21. Author: PMO Agent (Claude Opus 5). Not reviewed: V4 is owed.

## The gap

`phase new` writes a phase's prose and `phase/CURRENT` and no objective record;
`kr add --objective O` refuses an objective the phase does not declare; and
`goals/reference/phases.md` forbids appending one by hand. So a phase opened by
the writer could never carry a KR. Found live: `~/proj/SkyTonight` phase
`003-experience-polish`, opened with `phase new` on 2026-09-21, has zero
objectives, and `perry-goals kr add` refuses with "it has none".

## What shipped

- `perry-goals objective add <O-ID> --text "<title>" --reason "<why>" --actor <who>`
  appends one `{kind: objective, phase, id, title}` record to `linkage.jsonl`
  for the current phase (fields read from the schema's declaration) and one
  `objective_add` event, through `write_kr_change` — the phase KR writer's path,
  not a second one. `append_linkage_records` now accepts an absent store (a
  project's first phase objective).
- Refused, writing nothing: op other than `add`; missing `--text`; missing or
  multi-line `--reason`; no current phase; a scored phase; an id not matching
  the schema pattern `^O\d+$`; an id the phase already declares. `--actor`
  missing and foreign flags exit 2.
- `goals/reference/phases.md`: the step between `phase new` and `kr add`.
  No objective restate/withdraw: the store declares no objective revision kind.

## Evidence

- `tests/test_goals_objective_add.py`, 13 tests: on a phase with no objectives,
  `objective add` then `kr add` succeed and `krs` lists the KR; the append keeps
  every prior byte; file order is objective order; dry-run writes nothing; the
  first objective creates the store; every refusal moves no byte of the store
  or the event log.
- Mutation, on a `git archive` copy of `72e819c2`, `__pycache__` purged and a
  second waited each side, restore checked with `git show`: seven guards
  deleted one at a time (reuse, id pattern, scored phase, reason, reuse scoped
  to phase, dry run, event) — **all seven red**, each on the test named for it.
- Also exercised on a disposable copy of SkyTonight: O1, O2, then
  `kr add P003-O1-KR1` and `krs`. The live project was not written.
- Registered in `test_a_write_refuses_where_nothing_is_installed` (refuses on
  all three uninstalled shapes) and `test_actor_required`.

## The merge was red, and I merged it

`b9680b8f` went onto main with 2 red modules. The suite was launched as
`… > log; echo EXIT=$?`, so the background task reported exit 0, and the merge
ran in the same command that printed `✗ failures above`. The two reds were
this row's: `test_okr_store_is_the_source` pins every write site in
`perry-goals` and I had added a second one; `test_claims` requires the entry
point to be the file's last statement. Both fixed on `coding/objective-add-fix`,
full suite **158 modules / 4447 tests green** (log last line read before
merging), merged at `3ba47d05` — whose tree is byte-identical to the one tested.
Main was red between `b9680b8f` and `3ba47d05`.

## Architecture trigger: none

Listed boundary paths: false (`bin/perry-goals`, `goals/reference/phases.md`,
`tests/` — none of `viewer/parsers.py`, `bin/lib/`, `schema/`, a `SKILL.md`).
New top-level directory: false. New bin executable: false. Contract-version
change: false. Root `ARCHITECTURE.md`: unchanged. Module architecture
document: none changed.

## Not claimed

- No V4.
- The schema's `objective` record note still says "Written by `goals` at
  `plan-phase`"; not edited (schema edits need consent). It remains true of the
  lane, not of a single step.
- `phases.md` grew 774 bytes, inside the plan-phase bill; its cap holds.
