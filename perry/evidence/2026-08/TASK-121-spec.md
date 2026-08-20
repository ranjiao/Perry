# TASK-121 — the sweep that finds checks reading live state runs once and is thrown away

> Source: `perry/evidence/2026-08/TASK-113-dispatch-2026-08-20-1813.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — it adds a guard over the test suite
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The class, and its eight known instances

A check that reads **the project living around it** as its expected value goes
red on ordinary progress, and green again for reasons that have nothing to do
with what it measures. Every instance below is real and dated within four days:

| # | check | what moved under it |
|---|---|---|
| 1–3 | `test_diagnose`, `test_one_line_break_rule`, `test_v5_signoff` | TASK-113 found and fixed three |
| 4 | a fourth, handed over mid-run | same row |
| 5 | a fifth the agent found itself — `DESIGN-900` | same row |
| 6 | `test_md_store § test_config_including_its_prose_section` | asserted every config record is a `setting`; **declaring one track reddened it** |
| 7 | `test_track_attribution § TestPerrysOwnProjectIsUnmoved` | asserted Perry itself has no track register; same declaration reddened it |
| 8 | `test_state_cost` ×2 | asserted `perry/tasks.jsonl` is unclaimed and `.perry/events.jsonl` rolls up under `.perry/` — **both true until PR #14 declared the two store files owned** |

TASK-113 fixed instances 1–5 **by hand, in one pass, and the pass was thrown
away.** Instances 6–8 arrived afterwards. There is no mechanism; there is a
memory of having looked.

## Deliverable

A guard that finds this class **mechanically**, so the next instance is reported
rather than discovered by a human running the suite after a merge.

**What "this class" is, precisely, is the hard part of this row** — and getting
it wrong in either direction makes the guard worthless:

- too broad, and it flags every test that reads a fixture, which is all of them;
- too narrow, and it is a list of the eight above wearing a regex.

The instances give you the shape to generalise from: each one asserted a
**literal about the project's current state** — a count, an id, a set membership,
a filename — where the *property* being tested was true independently of that
literal. Note that instance 8's literals were about **which paths the schema declares
Perry owns**, not about a board row — so a guard keyed only on `BOARD.md` or the
task store would have missed it.

Report what you decided the class is, in the guard's own docstring, in the voice
of the surrounding modules — and **name what it deliberately does not catch.**

## Verification — V3

1. **It finds instances it was not shown.** Reconstruct at least three of the
   eight from git history — `test_md_store` and `test_track_attribution` before
   their 2026-08-21 fixes, and one of TASK-113's — and show the guard flags them.
   Reconstruct, do not hand-write an approximation.
2. **It does not flag the fixes.** The same three, after their repairs, are
   clean. A guard that still flags the repaired form is measuring the wrong
   thing.
3. **False-positive floor, stated as a number.** Run it over the whole suite as
   it stands and report **every** hit. If the count is not zero, each survivor
   is either a real instance — open a row for it — or a false positive you must
   name and explain. **Do not silence one to reach zero.**
4. **Reverting the guard reddens its own test.**
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- the guard, as a new test module or a check under `tests/`
- its own tests and fixtures

## Out of scope

- **Fixing any instance you find.** Report them; each is its own row. This row
  ships the mechanism, not the repairs.
- `bin/perry-diagnose` and `tests/test_diagnose.py` — an unmerged branch (PR #22)
  is editing both. Cutting across it would conflict.
- `perry/` — no project state changes; `git diff -- perry/` must end empty.
