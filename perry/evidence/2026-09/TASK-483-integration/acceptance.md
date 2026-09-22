# TASK-483 — integration acceptance, 2026-09-22 (V4)

DESIGN-020 H (§ 5.10 batch 2): next-step rules for the execution loop.
Attributed to P004-O1-KR1.

| Step | Result | Record |
|---|---|---|
| Rounds | R1 FAIL (latest verdict misread for unnumbered round 1), R2 **PASS** (verdicts ordered by review round; 120/120 git-ordered pairs agree) | `../TASK-483-review/round{1,2}-v4.md` |
| Candidate | `18c8d50b` (base `eab1f3f7`), net +300 Python/test (Bound +300, moves net to zero; spec note) | — |
| Release | `release/manage.py patch` → **0.1.21** (`TASK-483-execution-next-rules`) on the candidate as `5651f26d`; `check --base eab1f3f7` → new `0.1.21` | — |
| Architecture review | triggers: listed boundary paths TRUE, contract-version change TRUE (neither in root § 5); fresh reviewer **PASS**, no user decision | `architecture-review.md` |
| Full gate | green on tree `ccebce22`, base `771164ad`, 158 modules / 4,477 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-483` `28f35a3f` + durations `048e531a`; receipt VERIFIED | commits |
| Slow gate | 162 modules · 4,580 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only` → main `048e531a`; `VERSION` 0.1.21; `release/manage.py check --base origin/main --ref HEAD` exit 0; live `--section next` (perry-next/1.3): primary R-closable-row → close-task TASK-483, alternates R-sla-breach, R-dispatchable (TASK-218) | — |

**Integrated, unpublished.**

Follow-ups, no rows opened: undeclared round-name shapes (capitalised
`Round4`, `round4a`, a bare trailing number); `close-task`'s V4 gate does not
re-check the latest verdict; seven green mutants (round-2 review § 4); lint's
`check_reviews` duplicates `P.verdict_blocks`' file walk.
