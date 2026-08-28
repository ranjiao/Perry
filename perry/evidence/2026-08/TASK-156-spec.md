# TASK-156 — a linkage edge to a task that never existed is invisible

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `9653156`

## The measurement

`phase/<NNN>-linkage.md` names task ids at `objectives[].krs[].tasks`:

```yaml
      - id: P002-O1-KR1
        tasks: ["TASK-038", "TASK-088", "TASK-089", "TASK-090"]
```

```
perry/phase/001-linkage.md → 18 task ids;  dangling: none
perry/phase/002-linkage.md → 13 task ids;  dangling: none
```

`perry-lint` ships **four** linkage codes:

```
linkage-kr-exists        linkage-names-unique
linkage-objective-agrees linkage-task-single-kr
```

`linkage-kr-exists` proves a **KR** the graph names is in the phase file.
`linkage-task-single-kr` proves a task is not claimed by two KRs. **Nothing
proves a task the graph names exists at all.** A typo in an id, or a row removed
after the edge was written, produces an edge pointing at nothing, and every
tool stays green.

That matters because the edges are load-bearing: `kr_for_task` is the reverse
index, and TASK-120 folds these edges into KR progress. **An edge to a
nonexistent task is a KR crediting work that does not exist.**

## The trap, and it is the one this project keeps paying for

**Zero edges dangle today.** So a test that asserts "`perry-lint` reports no
dangling linkage task on this repository" is green now, would be green with the
guard deleted, and is another instance of *a check that reads the project living
around it as its expected value* — the exact class `tests/live_state_expectations.py`
exists to catch, and the class that has cost this project four rows.

**Construct the failing case in a fixture project.** `tests/fixtures/witness-project/`
(TASK-132) exists for precisely this and is read through the real `--root` seam.
The case cannot be produced by any writer — `perry-goals link` presumably will
not write an edge to a row it cannot resolve — so the fixture's linkage file is
authored directly, the same reason TASK-163's fixture writes `BOARD.md` by hand.

## What to build

A fifth code — name it in the same family — that reports a linkage edge naming a
task id absent from the task store. Decide and **state** three things:

1. **Severity.** `linkage-kr-exists` is `warn`. Argue whether this is the same
   or stronger, given that a KR's number can be wrong because of it.
2. **What "the task store" means when there isn't one.** A project with no
   `tasks.jsonl` **has not been adopted** — `viewer/parsers.py:876` says exactly
   this and says `None` is not "no tasks". A guard that reads absence as "every
   edge dangles" would fire on every unadopted project. This is the same
   inversion TASK-117 found in `perry-lint`, which called 175 of 175 rows drifted
   when the only thing missing was the log. **Do not repeat it.**
3. **Whether an old phase's linkage file is judged against today's store.**
   `bin/perry-lint:1082` carries a comment about this precise bug for KRs: a
   linkage file belongs to **its** phase, and judging `001-linkage.md` against
   the current phase reported correct edges as dangling. A task id, unlike a KR,
   is global — so the answer here may differ. **Read that comment and say
   whether its reasoning applies.** A row removed by TASK-167 would make an old
   phase's edge dangle correctly.

## Files in scope

`bin/perry-lint`, `tests/`, `tests/fixtures/`, `schema/state-schema.json` (only
if a new finding code must be registered there).

## Out of scope

- `perry/phase/*-linkage.md` — the `goals` lane owns these and nothing needs
  changing; they are clean.
- The KR-side checks. Do not alter `linkage-kr-exists`.
- `perry-goals link`'s writer.

## Verification

1. The fixture case: an authored linkage file with one edge to an absent id →
   exactly one finding, naming the id and the KR it hangs on.
2. **Mutation proof**: delete the guard, the fixture test goes red. Report the
   assertion count that reddens.
3. A second fixture case with **no** `tasks.jsonl` → **zero** findings, not N.
   This is decision 2 and it must have its own test.
4. `perry-lint` on this repository is unchanged: 0 errors, 3 warnings, 0 rows
   drifted. If your guard changes that number, you have found something — report
   it rather than adjusting the guard to fit.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
