# Phase 004 — O4 checks declared and first measurements, 2026-09-22

Checks declared under USER-1000 (DESIGN-022 § 5.6; P004-O4-KR2 target 6 per
USER-983). Values below are command output at main `e4e3d7bf`.

| KR · check | Value | Command and output |
|---|---|---|
| P004-O4-KR1 · total-module-seconds | 1058.7 | Sum of `sec` over `tests/durations.json`: 162 modules, 161 with a value, total 1,058.7 module-seconds. Target ≤ 1,054: **not met** by 4.7. |
| P004-O4-KR3 · l2-pages-over-budget | 0 | `tests/test_router_budget.budget_overflows()` → `[]` over every L2 page (`reference/`, `<lane>/reference/`) against the 32,768-byte cap. |
| P004-O4-KR3 · context-bills | 5 | `bin/perry-context-budget --bill all` exit 0: snapshot 75,526/80,000 B, add-task 68,283/100,000, close-task 64,913/95,000, dispatch 95,861/115,000, plan-phase within. All five bills compute; none is unknown. |

Not measured here, pending an evidence census: P004-O4-KR1
`affected-median-seconds` and `full-suite-per-merge`; P004-O4-KR2
`structural-rules`.
