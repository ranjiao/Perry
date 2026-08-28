# TASK-036 — `perry-goals/list/1.0`

> Design: `perry/design/DESIGN-005-state-and-contracts.md` § 6 step 2
> Rung: V3 (reproducible run)

## What shipped

`bin/perry-goals` (read-only), `schema/goals-list-contract.md`,
`tests/test_goals_contract.py` (12 tests).

It composes `viewer/parsers.py § load_snapshot` and parses nothing of its own —
the same decision as `perry-decide`, for the same reason: a second parser of one
file is the defect this project has hit twice.

## The defect found in its own first run

`present`, `day` and `kr_total` are not fields on the parser dataclasses;
`perry-state` derives them in its own builder. Reading them as
`getattr(okr, "present", False)` returned the default on every project and
reported nothing — a live OKR with three objectives came back
`okr_present: false` inside a payload that was otherwise well-formed.

This is the recurring shape: **a defaulted `getattr` on a field that does not
exist is a silent wrong answer.** Fixed by deriving each explicitly, with tests
that assert the values are real rather than defaults — mutation-verified by
restoring the `getattr` form, which fails
`test_a_project_with_an_okr_reports_it_present`.

## Verified against a real project

`~/proj/gimegime-pmo`, a Perry project with a year of history:

| | |
|---|---|
| OKR | v5, present, 3 objectives |
| phase | #004, day 68, 7 KRs, status written in Chinese |
| KRs | 12 |
| `krs_without_metric` | **12 of 12** — no KR carries a metric the parser recognizes |
| `krs_without_progress` | **12 of 12** — no linkage register, so no target and no current |
| `duplicate_kr_ids` | **4** — `KR1`, `KR2`, `KR3`, `KR6` reused |

Every one of those is reported rather than smoothed. A front-end that assumed
unique ids would render one row twice; one that read `progress: null` as `0`
would assert no progress on work it knows nothing about. Both are now stated in
the contract as things a consumer must not assume.

## What is deliberately absent

- **Task→KR attribution** — a derived join already computed by
  `perry-state --json § attribution` from the same snapshot. Recomputing it here
  is how the two would come to disagree.
- **Writes.** `OKR.md` and `phase/` are still hand-authored; the writer is
  DESIGN-005 § 6 step 3.

## Why V3 and not V4

No fresh-context reviewer has read it. Recording V4 ahead of the review is the
false-record mistake this project made earlier and corrected; a review is
warranted before step 3 writes into `OKR.md`.
