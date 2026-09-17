# Phase 004 check declaration proposal — not approved, not written

Prepared 2026-09-17 from `bin/perry-goals krs --json --phase 004`. DESIGN-022 §5.6 requires user approval per Objective before any `perry-goals check` write. This evidence document proposes a measurable decomposition of the existing twelve KRs; it does not change their targets or report them met. No `check` or `measure` command has run. Approval questions are queued behind the three already-open decisions, following the user-load cap.

| Objective / KR | Proposed named checks | Evidence boundary |
|---|---|---|
| O1 / KR1 | fixtures: at_least 5; reverting-rule-proof: done 1 | Exactly the five declared selector states and their negative mutations, including the closable-phase fixture under typed checks |
| O1 / KR2 | closing-coverage-percent: at_least 100; pointer-removal-red: done 1 | Numerator and denominator from the existing guard's enumeration, preserved with its output |
| O1 / KR3 | weekly-lag-iso-weeks: at_most 1; handoff-age-days: at_most 7 | A timestamped `perry-state` history read at each snapshot; historical baseline is not current lag |
| O2 / KR1 | real-first-interview-completed: done 1; input-quality-issues: at_most 0 | User answers the real first-OKR interview and authorizes foreign writes; a scratch fixture alone cannot satisfy this check |
| O2 / KR2 | supported-kr-writer-delivered: done 1; subsequent-hand-appends: at_most 0 | Exact writer merge establishes the audit start; a traceable commit/event census supports the later zero, not absence of a test failure |
| O2 / KR3 | behaviors-proven: at_least 2; negative-proofs: done 1 | Resume at question 3 and missing-writer finalize preserves store bytes |
| O3 / KR1 | rendered-lines: at_most 12; rendered-characters: at_most 1200 | Actual first-screen rendering, including whitespace/links and next block, with Unicode-code-point measurement |
| O3 / KR2 | decisions-recorded-percent: at_least 100; median-card-characters: at_most 600 | Agent-reviewed phase decision census paired with USER records; count typed facts only after semantic classification. Existing 21-commit baseline must be reconciled, not silently omitted |
| O3 / KR3 | next-action-p90-characters: at_most 400 | Complete open `perry-task list --json`, Python len, nearest-rank p90. Latest live TASK-447 receipt: 344 over 99 rows; still no KR measurement written |
| O4 / KR1 | affected-round-median-seconds: at_most 60; full-on-merge-percent: at_least 100; total-module-seconds: at_most 1054 | Retained executor round timings, actual merge receipts and canonical duration artifact; wall time and sum of module times remain distinct |
| O4 / KR2 | validated-structural-rules: target pending explicit restatement; each-rule-negative-proof: done 1 | USER-936 deferred S2. User must choose six in this phase or seven with S2 carried into phase 005. S1 expected failure and S7 skip do not count as pass; S5 gap stays visible |
| O4 / KR3 | over-budget-l2-pages: at_most 0; budgeted-context-bills: at_least 5; one-byte-over-red: done 1 | Final tier census, five declared subcommand bills and the bounded negative threshold proof |

The per-Objective confirmation must include check IDs, directions, targets and these evidence boundaries before tool writes. Boolean proof checks use direction `done` and target 1; percentage checks require a retained numerator/denominator and cannot be reported when the population is unknown. Current values above are cited observations only. No phase completion claim follows from completed tasks alone.
