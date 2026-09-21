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

## Round 2 — the V4 FAIL, and main red a second time

Round 1's V4 (`TASK-475-v4-review.md`) FAILed on one input: with an
unparseable line in `linkage.jsonl`, `objective add O1` read the store as
empty through `kr_store_records`, so the reused-id refusal never fired — exit
0, a duplicate O1 record and an event. Every other linkage writer refuses that
input. Fixed on `coding/objective-add-r2` (`c6d706ea`): an existing store that
will not parse is refused, as `resolve_kr_for_writer` refuses it, with
`test_an_unreadable_store`. Mutation on a `git archive` copy: the guard deleted
→ red, on that test; restore checked with `git show`.

**Main was red again, from `a0e5e51a`.** The verdict quoted the fixture's KR id
`P<NNN>-O1-KR1` with NNN = 005 in concrete form; merged to main, it failed
`test_diagnose`'s dangling-id check. The PMO merged the verdict without a suite
run. The id was replaced by the placeholder in the verdict file, with a note at
its top; no finding changed.

Not changed, recorded by the reviewer: `krs` on a phase with objectives and no
KR still refuses with a message that points to `plan-phase`; `goals/SKILL.md`
has no index row for `objective add`.

## Round 3 — USER-979, after two V4 FAILs

Round 2's V4 (`TASK-475-round2-v4-review.md`) FAILed on F2: `objective add`
matched a record's phase by exact slug, while every reader groups a phase's
records by number. After a hand rename of the phase document with `CURRENT`
repointed, a second O1 was written, `krs` listed it twice and `perry-state`
double-counted. Two older sites in `kr add` had the same comparison: its
objective lookup (a false "it has none") and its per-objective KR cap (which a
rename let a fifth KR past). review.md § 6 stopped a third round; the user
authorised one covering all three sites (USER-979).

All three now compare `parsers.linkage_phase_number` on both sides. Not
`linkage_records_for_phase`, the readers' selector: it answers `None` for a
phase with objectives and no KR yet, which is exactly the state `objective add`
creates — tried first, and it turned five existing tests red.

Tests, one per site (`TestARenamedPhaseIsTheSamePhase`): objective add refuses
an id filed under the old slug; kr add finds an objective filed under it; the
cap counts KRs filed under it. All three fail against the round-2 code on a
`git archive` copy and pass on the fix.

Full suite on the branch head with main merged in: 158 modules / 4459 tests, green.

## Architecture trigger: none

Listed boundary paths: false (`bin/perry-goals`, `goals/reference/phases.md`,
`tests/` — none of `viewer/parsers.py`, `bin/lib/`, `schema/`, a `SKILL.md`).
New top-level directory: false. New bin executable: false. Contract-version
change: false. Root `ARCHITECTURE.md`: unchanged. Module architecture
document: none changed.

## Not claimed

- No V4 of round 3 yet.
- The schema's `objective` record note still says "Written by `goals` at
  `plan-phase`"; not edited (schema edits need consent). It remains true of the
  lane, not of a single step.
- `phases.md` grew 774 bytes, inside the plan-phase bill; its cap holds.
