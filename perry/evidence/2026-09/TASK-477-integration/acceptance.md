# TASK-477 — integration acceptance, 2026-09-21 (V4)

perry-diagnose matches Perry-owned paths at each one's own schema anchor
(USER-988; found by TASK-452's round-2 V4 review).

| Step | Result | Record |
|---|---|---|
| Candidate | `2e690db4` on `coding/task-477-diagnose-code-anchor`, base `558ca2ac`; `bin/perry-diagnose` +10/−8, `tests/test_diagnose.py` +13; net +15 (Bound limit) | author RESULT, session |
| V4 | fresh reviewer **PASS**: 13 layouts, 7 mutants (5 killed; M5 `.perry` exemption and M6 extra-directory default survived — test gaps, behaviour correct) | `../TASK-477-review/v4.md` |
| Architecture trigger | none — diff touches `bin/perry-diagnose` and `tests/` only: no listed boundary path, no new directory or executable, no contract or architecture document | — |
| Full gate | `merge-check --base main delivery=coding/task-477-diagnose-code-anchor --tier full`: green on tree `068843f4`, base `d4990347`, 158 modules / 4,462 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-477` `9259f0c6` (`--no-ff` onto `d4990347`) + durations `a2a12a8f`; `--verify-receipt` VERIFIED | commits |
| Slow gate | `tests/run --tier slow` at `a2a12a8f`: 162 modules · 4,565 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only integ/task-477` → main `a2a12a8f` | `git log -2 main` |

Follow-ups, no rows opened: the two surviving mutants (M5, M6) name untested
behaviour; ARCHITECTURE.md's preamble comment (26-29) and OQ-1's "one remaining
reader … is TASK-477" sentence are now stale.
