# TASK-404 — result

> Status: complete, merged at `574ac16d` on 2026-09-10.
> **Written after the fact by the PMO on 2026-09-12**, from the merge commit
> and the merged diff, because the round produced no result document at the
> time and `perry-task done` refuses a close that cites nothing. Everything
> below is quoted from `574ac16d` or re-derived from the diff; nothing here is
> a fresh measurement, and the suite figures are the commit's claim rather
> than a run performed on 2026-09-12. Whoever needs the numbers again should
> re-derive them.

## 0. What the row claimed, and what the census found

The row's title asserts three figures. **All three are wrong, in different
directions**, and that is the round's main finding rather than a footnote.

| The title said | The census found |
|---|---|
| 36 test modules | 19 name the live `perry/` path; 53 reach it by any route; **25** have live data flowing into an assertion |
| 614 dates | 656 counting comments; 531 as code literals; **5** inside a live-reading test method |
| 191 ids | 3,267 raw; 1,360 literals; 8 inside such a method; **0** that were live-board expected values |

Under a bounded criterion — *a date or id literal in code, inside a test method
whose data comes from this repository's own `perry/` tree* — the set is
**12 sites in 8 modules**. One was churn. Ten are load-bearing and were listed
with a reason each, `test_shipped_vocabulary` among them, which asserts about
the shipped repository on purpose.

So the row was **a one-site problem wearing a six-hundred-site title**.

## 1. The one site, and the conversion

`tests/test_risks.py::TestPerrysOwnBoard::test_the_risk_cleared_on_2026_08_16_no_longer_counts`
read the live `perry/BOARD.md` and asserted that the count of cleared risks was
`1` and the date was `2026-08-16`. Neither is a fact about the reader under
test. Clearing a second risk, or clearing the first one a day later, turned it
red with no line of code changed — and **its name had to be edited to match**.

The merged change, `tests/test_risks.py`, 74 insertions and 5 deletions:

- The live-board test is renamed to
  `test_every_cleared_risk_is_dated_and_no_longer_counts` and **quantifies over
  the rows** instead of counting them, so it is silent about how many there are.
- The exact count and the exact date move into `TestClearedRisksStopCounting`,
  onto a `DATED` fixture the module owns, **deliberately not `2026-08-16`** —
  a fixture that borrows the live board's day reads as though it were checking
  the real thing, which is how the old name arose.
- Two assertions are added that the live-board test never made:
  `test_a_cleared_row_carries_the_date_its_status_cell_states` pins
  `cleared_on`, the field the whole row exists for, and
  `test_an_open_row_carries_no_cleared_date` pins its complement.

All four are present in `tests/test_risks.py` on `main` today.

## 2. Mutation

Verified in the commit rather than taken on the executing agent's word: **both
mutations the old test caught still redden, and two it missed now do too.**

One replay came back **green** and was judged an equivalent mutant rather than
a gap: an open `Status` cell has no date to find, so suppressing the search
changes nothing.

## 3. What was deliberately not done

`TASK-418` is the sharper half. `tests/live_state_expectations.py` exists to
catch this class and **missed this row's own headline exhibit**, because taint
does not cross `setUp` into test methods and a comprehension over a tainted
iterable reads as clean. It was left alone on purpose: a guard change
re-records a baseline fixture other agents may be holding. `TASK-418` has since
been **dropped**, so this half currently has no owner — recorded here because
the commit left it as a live follow-up and it no longer is.

## 4. Suite, as claimed by the commit

```
122 modules, 3,481 tests, the three declared reds, tree guard clean.
```

## 5. Rung

Closed at **V2** under `ADR-020` (2026-09-11). The gate question is whether the
row touched a write path or `schema/state-schema.json`; `574ac16d` touched
`tests/test_risks.py` and nothing else, so the answer is no. The rung recorded
on the row before this close was V3.
