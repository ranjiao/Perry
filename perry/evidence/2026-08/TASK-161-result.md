# TASK-161 — a contract page can now tabulate a collection this project leaves empty

**Closed 2026-08-28 without its own dispatch.** Rung **V3**. It was resolved by
two rows that landed the same night from the other two directions, and the
verification below is the row's own case, measured.

## The row, and the two halves that closed it

*"A contract page cannot tabulate a collection this project's state leaves
empty"* has two obstacles, and each was somebody else's row tonight:

- **The page could not be written** — `place` refused a key table whose keys
  matched two identically-shaped collections, and silently mis-assigned it when
  only one happened to be non-empty. **TASK-176** taught it to honour a heading
  that names its collections, with the `[]` suffix as the whole syntax.
- **The page could not be checked** — keys inside a collection Perry leaves empty
  were `not_observable`: emitted, documented, never once compared. **TASK-132**
  removed that with a witness project the real tools read through `--root`.

Neither row was scoped as this one. Together they are exactly it.

## The verification is this row's own case

`conformance.in_progress_with_no_live_run` and
`conformance.depends_on_unknown` are **empty on this project right now**, and
`review_idle` has one entry:

```
in_progress_with_no_live_run     0 entries
review_idle                      1 entry
depends_on_unknown               0 entries

their keys still unobservable :  0
their keys undocumented       :  0
```

**Documented and checked while the collection is empty — which is the sentence
the row asks for.** Across all six contracts, `not_observable` is **0 keys**.

The idle-entry table is the sharpest instance: one key table serving two
collections, one of them empty, both named in the heading, all twelve keys
placed and compared.

## Why this is closed rather than dropped

The defect was real and is gone, and the mechanisms that removed it carry their
own guards — `test_the_named_table_reads_the_same_however_full_the_arrays_are`
pins the placement across all three fill states, and TASK-132's witness README
states the rule for extending it (*"add the state, never the finding"*).

**No new code was written for this row.** Recorded so the closure is auditable
rather than a row quietly disappearing.
