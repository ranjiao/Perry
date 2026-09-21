# P004-O3-KR2 · `decisions-recorded-pct` — census, 2026-09-21

Measured by a read-only fresh-context subagent on the PMO's brief; report copied
here by the PMO (the subagent could not write files). Semantic census: the agent
judged which items are user decisions. **Value recorded: 83.6** — the population
from phase 004's opening commit `15369956` (2026-09-15 19:49), because the KR's
own baseline ("2026-09-14→15: 21 commit subjects … against 0 new asks") counts
the morning of 09-15 as pre-phase. The whole-day reading is 66.2% and is kept
below; the choice of window is the PMO's and is stated here, not hidden.

## Window

Start 2026-09-15 00:00 +0800; end main `6d471770` (2026-09-21 16:41). USER-984
and USER-985 were uncommitted at measurement and are excluded.

## Counts

| Population | Decisions | Covered | % | Covered and recorded before acting |
|---|---|---|---|---|
| 09-15 00:00 → HEAD | 77 (16 A + 61 B) | 51 | 66.2 | 49 (63.6%) |
| **Phase opening 19:49 → HEAD (recorded)** | **61** | **51** | **83.6** | 49 (80.3%) |

Recorded after acting: USER-954 (dispatch 11:45:18 at `0ed39d11`, record
11:47:37). Timing unknown: USER-951 (merge `3a9a2f7c` 17:33:13 between ask
17:32:57 and answer 17:33:20).

## Group A — 09-15 before 19:49, none recorded (phase 003 work)

A1 TASK-262 F1 in-row, Amendment 2 (`37fb4405`, `c3ccd7b5`) · A2 retire held
BOARD.md, Amendment 3 (`c026744f`, `09ea1376`) · A3 full retirement, pins lifted
(`81a0e808`, `e8f92541`) · A4 F14 re-pointed, two state-schema edits, NN-2 wording
(`2c8bae07`) · A5 F17 "import before delete" (`b968de89`) · A6 F34 no `--strict`
exemption (`7ae21bed`) · A7 NN-2/§5 edit confirmed (`38192b15`) · A8 close
TASK-262 at V3 (`227d99f1`) · A9 phase 003 KR statuses (`7bffe58e`) · A10 accept
known red, clear CURRENT, fix in TASK-441 (`7bffe58e`, `f6e61b4d`) · A11 close
TASK-441 at V3 (borderline, journal 09-15) · A12 DESIGN-017 decisions (`b2aaa83d`)
· A13 DESIGN-021 decisions 1–5 (`b2aaa83d`) · A14 DESIGN-020 §9 (`15369956`) ·
A15 OKR v4 (`15369956`, ADR-021) · A16 phase 004 plan and rules (`15369956`).

## Group B — covered (51): USER-933 to USER-983

Each a user decision answered by the user, counted once. All recorded before
acting except USER-954 (after) and USER-951 (unknown).

## Group B — not covered (10)

| # | When | Decision | Sources |
|---|---|---|---|
| B1 | 09-16 ~13:26 | TASK-448's two cleanups under that row | `21c4052a`, `a26b6ee7`, journal 09-16 |
| B2 | 09-16 18:51 | Approve TASK-462 versioning proposal | TASK-462-spec.md l.6–7, `bccc15f8` |
| B3 | 09-16 19:20 | TASK-463: build release logic into the skill | TASK-463-spec.md l.7 |
| B4 | 09-17 11:09 | Approve dedup and task adjustments (TASK-464/465) | TASK-464/465 specs, `272c5605` |
| B5 | 09-17 ~13:17 | Authorise autonomous work while away | autonomous-2026-09-17.md l.3 |
| B6 | 09-17 17:32 | Prioritise interactive OKR design | interactive-okr-priority-20260917.md, `3779eeae` |
| B7 | 09-18 ~12:13 | PythonPlayground as interview project (USER-955 names none) | `7c16e920`, journal 09-18 |
| B8 | 09-20 12:05 | TASK-474: full phase lifecycle | `8a081790`, TASK-474-spec l.14 |
| B9 | 09-21 09:25 | Close TASK-469 and TASK-474 at V3 with known defects | `1c28cce7` |
| B10 | 09-21 15:34 | Close TASK-473 at V3, acceptance open | `81150fb2` |

## Borderline

Group A counted only in the whole-day reading. A11 inferred from a journal line.
A9 counted as one. TASK-262 Verification 5 reading (`40b21476`) not counted —
observations, not a choice. B1, B4, B7 counted as uncovered decisions. USER-977
(3)'s TASK-475 opening not counted as a user decision. Units are question sets;
splitting sub-decisions gives about 66/103 (~64%). Pre-window DESIGN-020
decisions 1–8 not counted.

## Limits

- `git log --since=2026-09-15` drops the 54 morning commits (git stops at
  older-dated commits); the census filtered `%ci >= 2026-09-15` over
  `git log -n1500` (525 commits).
- Candidates came from keyword greps then reading; a decision made only in chat
  and never written anywhere is invisible, so N is a lower bound and the percent
  an upper bound.
- 619 evidence paths grepped; only hits were read.
- First-act commits and decision units are the agent's judgement.

`VALUE decisions-recorded-pct = 66.2` (whole day) · **recorded: 83.6** (from phase opening)
