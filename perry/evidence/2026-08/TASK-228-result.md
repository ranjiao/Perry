# TASK-228 — result: the three attribution buckets are disjoint

> Branch `coding/task-228-attribution-buckets`, commit `2b01253`. Rung **V3**.
> Measured 2026-08-29.

## The defect

`bin/perry-state` built `unlinked` by asking *"did this row resolve to a KR?"*
That is false for a **declared** row as much as an undeclared one, so every id
in the register's `unlinked[]` was reported in both `unlinked` and
`declared_unlinked`.

Measured 2026-08-28 on Perry's own board after 48 rows were declared:
`linked=8, unlinked=48, declared_unlinked=48`, and the two sets were
byte-identical.

## Why it was not cosmetic

`unlinked` is the number the standup renders as *"N tasks awaiting KR
attribution"*.

**On 2026-08-29 this session read that number off the payload and reported to
the user that 52 rows owed an attribution answer. The true never-asked count
was 0.** Every one of those answers had been given the day before, through
`perry-goals link --unlinked`, with the user's own consent recorded in
`journal/2026-08/2026-08-28.md § OKR attribution sweep`. The payload turned
finished work back into outstanding work, and the person it misinformed was the
person who had done the work.

The correction was made by computing the set by hand — open `main`-track rows
minus linked minus declared — which is exactly the arithmetic the payload is
supposed to save a reader from doing.

## The fix

Both halves of the deliverable, which named the payload *and* the page:

- `bin/perry-state`: a row named in the register's `unlinked[]` is reported in
  `declared_unlinked` and **nowhere else**. `unlinked` is now the NEVER-ASKED
  set.
- `reference/okr-linkage.md`: the partition is stated explicitly. The page
  already distinguished *"`unlinked` (couldn't resolve)"* from
  *"`declared_unlinked` (the graph says outright that this work serves no
  KR)"* — it described three states while the code implemented two. Nothing
  enforced the agreement, which is how they drifted.

This is also what makes `P003-O3-KR1` measurable: that KR counts *"open
`main`-track rows in neither `objectives[].krs[].tasks[]` nor a declared
`unlinked[]`"*, and a bucket that folds the declared into the unresolved makes
the KR unmeasurable from the payload it is defined against.

## Verification

**The row's own Verification, run:** *"After the fix, `unlinked` must be 0 for
that same state. Mutation: leave one row undeclared and it must appear in
`unlinked` and nowhere else."*

```
linked            : 7
unlinked          : 0   []
declared_unlinked : 52
```

Both halves hold. `TestDeclaringARowMovesItBetweenBuckets` runs the mutation in
both directions on a copied fixture.

**Shown able to go red.** Deleting the `elif t.id in declared_unlinked` branch
→ 4 failures in `tests/test_attribution_buckets.py`. Restored, green.

**Suite**: 3 modules red before and after (`test_contract_key_parity` 2,
`test_diagnose` 2, `test_kr_progress_provenance` 1) — all pre-existing on
`main`, baselined in the same worktree. This change adds none.

## Two shipped tests converted, and what they revealed

- `tests/test_parsers.py::test_unlinked_task_is_surfaced_not_guessed` pinned
  `unlinked == ["REL-009"]` for an id the fixture **declares**. It now asserts
  the row is surfaced in `declared_unlinked` and never guessed into a KR —
  which is what the test is named for.
- `tests/test_linkage_writer.py::test_a_declared_unlinked_task_stops_being_drift_when_it_is_linked`
  carried a docstring ending *"and must not be reported as both afterwards"*
  directly above two assertions pinning the row into both buckets
  **beforehand**. The double-count had been seen and tolerated one line from
  the sentence objecting to it. Its actual subject is unchanged.

## One note on method

The first draft of `tests/test_attribution_buckets.py` hand-built a board and a
linkage register. It parsed **zero** rows, and every disjointness assertion
passed vacuously over two empty sets. The module now copies
`tests/fixtures/sample-project`, which already carries the shape under test,
and `TestTheFixtureIsTheShapeUnderTest` is the control that makes that failure
mode loud instead of silent.
