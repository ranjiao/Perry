# TASK-021 — closed at V4

> Rung: V4. Reviewer: fresh-context agent, 2026-08-17, scoring against
> `TASK-021-spec.md`. Verdict: **PASS**.

The recurrence register's second review. All three MAJOR findings and all three
MINOR findings from `TASK-021-v4-review.md` are fixed, and the reviewer
confirmed each by reverting exactly the line it names:

| Prior finding | Confirmed fixed by |
|---|---|
| `parse_due` reading a date out of a file path | four live cells re-checked on a gimegime-pmo copy |
| the overdue sort had no test that could fail on it | deleting `bin/perry-state:435` now reds `test_overdue_rows_are_reported_by_age_oldest_first` |
| `done` refusing with a false "not a row on the board" | the refusal is true and names the rule |
| `###` sub-groups; `unreadable_frequency` unreachable; two procedures disagreeing | each verified |

**16 of 18 mutations reproduced.** The two survivors are recorded as `m-1` in
`TASK-021-v4-review-round2.md`: two of `parse_due`'s three guards can be deleted
with all 813 tests green. The behaviour is correct — the reviewer re-verified
every live cell — but it is carried by the `_NO_DATE` early return and the
anchored match, not by the two mechanisms the docstring presents as central.

**That is a test-quality gap in a correct fix, not a behavioural defect**, which
is why this row closes at V4 rather than waiting. It is carried forward as
TASK-050 rather than dropped.

On a copy of `~/proj/gimegime-pmo`: all five real `Frequency` cells parse
(`continuous` and `hourly` → aperiodic, none dropped), the three prose
`Next due` cells resolve correctly, `unreadable_frequency` and `undated` are
both empty, and `perry-lint` reports zero findings about `## Cadence` among that
project's 59 pre-existing errors.
