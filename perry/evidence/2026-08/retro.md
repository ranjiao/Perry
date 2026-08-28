# Retro — phase #002 `fields-are-typed`

> Written by the `work` lane (`end-phase-retro`), 2026-08-28.
> Phase started 2026-08-19, scored 2026-08-28, **phase day 9**.
> Sources read: `BOARD.md`, `journal/2026-08/` (2026-08-19 → 2026-08-28,
> 5 entries, 2,540 lines), `evidence/2026-08/` (288 files),
> `.perry/events.jsonl` (744 events in the phase window),
> `phase/002-linkage.md`, `phase/002-fields-are-typed.md`.
>
> **The scores are the `goals` lane's** — `phase/002-fields-are-typed.md §
> Retro — phase scored`, phase mean **0.89**. This file does not re-derive them.
> What it adds is the half `score-phase` could not see: the evidence path behind
> each KR, what the board actually did for nine days, and the carry-over set.
>
> Filename is `retro.md` per `work/reference/subcommands.md § end-phase-retro`.
> Two phases closing in one calendar month would collide on it; #002 is the only
> one that closed in 2026-08.

## Per-KR outcome, with the evidence

| KR | outcome | score | rows | evidence |
|---|---|---|---|---|
| `P002-O1-KR1` `BOARD.md` rendered from `tasks.jsonl` | **achieved** | 1.00 | TASK-038 (V5), TASK-088 (V3), TASK-089 (V4), TASK-090 (V4) | `evidence/2026-08/TASK-038-v5-signoff-request.md`, `TASK-088-renderer.md`, `TASK-089-v4-review-r4.md`, `TASK-090-v4-review.md` |
| `P002-O1-KR2` `OKR.md` and `.perry/config.md` likewise | **achieved** | 1.00 | TASK-092 (V4) | `evidence/2026-08/TASK-092-dispatch-2026-08-20-1654.md` |
| `P002-O1-KR3` a hand edit is reported, not honoured | **partial** | 0.33 | TASK-093 (V4) · **TASK-209 open** | `evidence/2026-08/TASK-093-final-v4-review.md` |
| `P002-O2-KR1` `CLOCK_RE` deleted, `By when` split | **achieved** | 1.00 | TASK-091 (V4) | `evidence/2026-08/TASK-091-v4-review-r3.md` |
| `P002-O2-KR2` 0 readers resolve a header cell | **achieved** | 1.00 | TASK-094 (V3) · **TASK-050 open** | `evidence/2026-08/TASK-094-result.md` |
| `P002-O2-KR3` parser lines for the three stores | **partial** | 0.68 | **TASK-095, TASK-099 both open** | — (3,320 → 1,048 measured at scoring; no closed row) |
| `P002-O3-KR1` 0 lane procedures hand-edit a rendered file | **achieved** | 1.00 | TASK-096 (V4) | `evidence/2026-08/TASK-096-v4-review-r3.md` |
| `P002-O3-KR2` read contracts survive unchanged | **achieved** | 1.00 | TASK-087 (V3) | `tests/test_contract_invariance.py` |

**Nothing was `missed` and nothing was `dropped`.** Six achieved, two partial.

**One KR's progress has no closed row behind it.** `P002-O2-KR3` scored 0.68 on
a line count measured at scoring time, while both rows attributed to it —
TASK-095 and TASK-099 — are still `not_started`. The reduction happened as a
side effect of other work. That is not fraud and the number is real, but a KR
whose evidence is a measurement rather than a deliverable is one nobody can
re-run next phase, and it is the second reason (after the wrong target) that
this KR is the least trustworthy number on the board.

## What the board actually did

| | count |
|---|---|
| tasks closed in the phase window | **100** |
| tasks added | **131** |
| tasks dropped | 3 (TASK-042, TASK-070, TASK-134) |
| net change in open rows | **+28** |
| closed rows attributable to a phase KR | **10 of 100** |
| `done` events with no evidence citation | **0 of 100** |
| verification rungs on closed work | V3 ×78 · V4 ×14 · V5 ×6 · V2 ×2 |
| asks raised / answered | 5 / 5 |
| intake arrivals / resolutions | 68 / 65 |

Closes by day: 08-19 ×15 · 08-20 ×21 · 08-21 ×29 · 08-27 ×4 · 08-28 ×31.
Adds by day: 08-19 ×22 · 08-20 ×40 · 08-21 ×32 · 08-28 ×37. **The phase added
more work than it closed on every single working day.**

### The number this retro exists to put on the record

**10 of 100 closed tasks resolve to a phase KR.**

`score-phase` reported the same defect from the other end — *43 open rows
resolve to no KR, against 3 that do* — and concluded that phase 003 should
either declare KRs the live work serves or make linkage part of `add`. The
execution side makes it sharper: the gap is not a backlog of untriaged rows
waiting to be attributed. **Ninety of the hundred things this project finished
in nine days were outside its own stated phase.** A phase whose KRs describe
10% of the work that ran is not measuring the project; it is measuring a
sample, and it scored 0.89 on the sample.

This does not invalidate the 0.89. It bounds what the 0.89 is a claim about.

## Lessons

The four durable ones are already written in `phase/002-fields-are-typed.md §
Lessons for phase 003` — grep the expression not the name; a locked decision
with no row does not ship (5-for-5 with rows, 0-for-9 without); a check that
reads its surroundings as its expected value; a tautological gate is worse than
no gate. They are not restated here.

Three the execution record adds:

1. **The linkage graph was written a day late and the cost was measurable.**
   `002-linkage.md` says it plainly: `plan-phase` should have written it on
   2026-08-19 and wrote it on 08-20, "which is why every task on the board
   reported `unlinked` for two days". Those are the two highest-add days of the
   phase (40 and 32 rows). Rows arriving with no graph to resolve against are
   exactly the rows that end up in the 90.

2. **A malformed linkage graph passed lint for eight days.** Three O2 KRs were
   nested under `- id: O1` and no `O2` objective existed in the graph at all;
   `linkage-kr-exists` only fires on an *absent* id, so 0 errors, 0 warnings.
   It was found by hand during `plan-phase 003` and mutation-proven the same
   day. The retro's own arithmetic had been right and the graph wrong — **the
   prose caught what the checker could not**, which is the inverse of the
   posture this project runs on and worth remembering as such.

3. **Every close carried evidence, unprompted, 100 times out of 100.** No
   `done` event in the window has an empty `evidence` field and no rung is
   unrated. This is the one process invariant that held under a 31-close day.

## Carry-overs

`score-phase` proposed five. All five are open and confirmed here, with the
board state at phase close:

| row | P | status | why it carries |
|---|---|---|---|
| **TASK-097** | P1 | not_started | DoD item 5 — migrate two real projects at V5. **The phase's own argument, untested.** |
| **TASK-209** | P1 | not_started | `P002-O1-KR3`'s real subject: the drift census covers one store of five. |
| **TASK-050** | **P0** | not_started | Open under `P002-O2-KR2`; measures wider than that KR's metric, so the KR hitting 0 does not close it. |
| **TASK-095** | P1 | not_started | `P002-O2-KR3` — remove the parser for the three stores. |
| **TASK-099** | P1 | not_started | `P002-O2-KR3` — sweep for document handling ADR-007 made dead. |

Two more the board surfaces that the scores did not:

| row | P | status | why |
|---|---|---|---|
| **TASK-067** | **P0** | **blocked** | The only blocked row on the board. "The writer can destroy the table it writes to, and `perry-lint` cannot see it" — a store-integrity defect crossing into phase #003, whose whole subject is stores. |
| **TASK-139 / TASK-155 / TASK-157** | P1–P2 | triaged, **past SLA** | The `intake` track's first cycle ended with three rows over its 5d SLA. Queue debt does not belong to a phase, so it carries by default and nothing notices. |

**Not carried, recorded instead**: `P002-O2-KR3`'s target of 0 parser lines was
unreachable from the start — `TASK-094` proved the adoption reader must stay.
Phase #003 restates it correctly as `P003-O2-KR2`, a fenced module with a guard,
rather than a line count.

## Health metrics

From `evidence/2026-08/health-check-2026-08-28.md`, run inline.

- **Incident feedback-loop ratio: not available.** This project has no
  `incidents/` organ and closed 0 incidents this phase. Perry is a skill, not a
  deployed service. Printed as unavailable rather than as `0 of 0`, which would
  read as a ratio.
- **Audit drift trend: not available.** No `ARCHITECTURE.md`, so the audit did
  not run and there is no drift series. The nearest real number: `perry-lint`
  ends the phase at **0 errors, 4 warnings**, all four `NS-01`, all four
  pre-existing — and two of them fire on files `goals score-phase` wrote during
  this very close (`phase/snapshots/`).
- **Runbook coverage: not available.** No `runbook/`, no deployed components.
- **Store-drift coverage — the substitute metric this project actually has:**
  **4 of 6** declared stores exist; **2 of 6** produce a drift verdict from
  `perry-lint` (tasks, risks); `intake.jsonl` and `asks.jsonl` report
  *unchecked, not clean*. This is the number phase #003 is named after, and it
  is the one to trend at the next retro.
- **BOARD hygiene**: 113/200 lines · 0 rows drifted · 0 stale rows · 0
  evidence-less `done` claims.

## Feeds `plan-phase` for #003

Phase #003 is already open (started 2026-08-28). Two findings above are **not**
represented in it and should be read against it before its first `plan-week`:

1. The 10-of-100 attribution gap. `P003-O3` ("The phase's KRs cover the work that
   actually runs", 2 KRs) is aimed at exactly this — this retro supplies its
   baseline: **10%**.
2. `TASK-067`, blocked, P0, store-integrity, and unlinked to any #003 KR.
