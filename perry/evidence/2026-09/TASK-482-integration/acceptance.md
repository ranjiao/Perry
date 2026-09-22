# TASK-482 — integration acceptance, 2026-09-22 (V4)

R-midweek reads a typed fact from the cadence register (USER-999; DESIGN-020
§ 5.10 stage 4). Attributed to P004-O1-KR1.

| Step | Result | Record |
|---|---|---|
| Candidate | `004260d6` (base `e4e3d7bf`): design (b), a cadence row titled `midweek-check`; one schema line (`reserved_titles` on the `cadence.jsonl` claim); `week.midweek_checked` replaces `today.journal_has_midweek`; `perry-next/1.2`; net +62 Python/test | — |
| V4 | fresh reviewer **PASS**; a surviving mutant M9 (title check → `True`) is unpinned | `../TASK-482-review/v4.md` |
| Release | `release/manage.py patch` → **0.1.20** (`TASK-482-midweek-fact`) committed on the candidate as `5843caf1`; `check --base e4e3d7bf` → new `0.1.20` | — |
| Architecture review | triggers: listed boundary paths TRUE (schema/), contract-version change TRUE (neither version is declared in root § 5); fresh reviewer **PASS**, no user decision | `architecture-review.md` |
| Full gate | green on tree `6cb8fd5f`, base `bb55bb02`, 158 modules / 4,473 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-482` `09ac81c3` + durations `0e14ae3a`; receipt VERIFIED | commits |
| Slow gate | 162 modules · 4,576 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only` → main `0e14ae3a`; `VERSION` 0.1.20; `release/manage.py check --base origin/main --ref HEAD` exit 0; live `--section next` is `perry-next/1.2` with `week.midweek_checked` no longer unknown | — |

**Integrated, unpublished.** Follow-up (no row opened): pin the exact-title match
(V4 M9, M7/M8) and the unsearchable-parent path (M4).
