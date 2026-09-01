# Phase #001 — work-modes-live

> **Owner**: `okr` skill (only writer). PMO reads this every standup.
> **Started**: 2026-08-17
> **Status**: scored
> **Source**: `OKR.md` v1
> **Predecessor**: (none — first phase)
> **Tier 1 hard cap**: ≤ 300 lines. Overflow → move long Stretch trackers / project lists / narrative addenda to `evidence/<YYYY-MM>/phase-001-<topic>.md` and reference via link.

This file is a tactical commitment, not a smaller copy of the overall OKR. Every section below is mandatory. Phases end when KRs are largely hit, not when a date arrives — see `goals/SKILL.md § Why phases, not months`.

## Phase Focus

`DESIGN-003` shipped four work modes, four mode files, a track register and a verification ladder — and then nothing declared a `## Tracks` table, so `pipeline`, `queue` and `inquiry` have only ever run under `tests/test_work_modes.py`. Three tasks are in flight against that gap and all three are stuck on review debt: TASK-019 and TASK-020 each failed a V4 review with 3 blocking findings, and TASK-027 has been waiting on a fourth review round. TASK-021 and TASK-028 are blocked behind them. This phase clears that chain and ends with the three non-`project` modes declared and answering triage questions from real state rather than from fixtures.

The second half of the phase is smaller and is about Perry's own instrumentation: the `goals` lane is the one lane with no deterministic write tool, and this phase file is the first time in the project's history that `plan-phase` and the linkage graph have been exercised at all. Landing `perry-goals`' write path closes that.

This phase does not target the aiMark write contract or the event-log-canonical migration, and it adopts none of the three named real projects; the focus is making the modes reachable on a live track and giving `goals` a writer.

## Operating Rules

> Phase-scoped invariants. Subset / extension of overall Operating Principles.

- Agent autonomy: agents may edit mode files, lane procedures, `bin/` scripts and tests without asking, and may run the full test suite.
- User authorization required for: everything named in `.perry/hook.md § High-stakes operations` — in this phase, principally `git push`, any change to the claim surface (`schema/state-schema.json § claims[]`), and any write into a project Perry does not own.
- Review gate: a task carrying blocking findings may not move to `done`; it moves to `blocked` naming the finding, or stays `in_progress`. TASK-019 and TASK-020 are the live cases.
- A claim about verification must itself be verified: a test counts as evidence only after reverting the fix has been shown to break it.
- Evidence requirement: every KR movement cites a path under `evidence/2026-08/` or a commit SHA. No KR advances on a review comment alone.
- Retros must cite evidence files, not subjective judgments.

## Cost Ceiling (phase #001)

- Spend cap: **$0** in new paid APIs, models or infra. Perry is stdlib Python by Anti-Goal; there is nothing to bill.
- Real cost of this phase is agent tokens and review rounds, not dollars. Cap: **≤ 4 review rounds per task** before the task is escalated to the user instead of re-reviewed. Baseline for why this is a real limit: TASK-033's chain ran to five rounds.
- Soft fallback at 3 rounds on any one task: stop re-reviewing, write the open findings to `evidence/2026-08/<TASK-ID>-open-findings.md`, and surface the task in the next standup.
- Hard cap at 4 rounds: the task moves to `blocked` with the round count named.
- Wiring status: **doc-only** ⚠ — nothing in `bin/` counts review rounds. Carried as an open risk in every snapshot until wired or dropped.
- Visibility: round count is readable from the task's `next_action` and its evidence files; there is no command for it.

## User Commitments

> What the user must contribute during this phase. Each becomes a USER-id in PMO's User Input Queue.

- Decide which project carries the three non-`project` tracks — Perry's own `.perry/config.md`, or one of the three named real projects. P001-O1-KR1 is written against Perry itself; naming a real project instead pulls KR-O3.1 into this phase.
- V5 sign-off on TASK-028 (`diagnose`/`adopt` mode detection + both READMEs), which the board marks as needing it.
- Confirm the four-round review cap above, or replace it with a number you will actually hold to.
- Phase scope-reduction trigger review (decide whether to cut scope when the trigger fires).
- Phase-scoring participation (KR status + next-phase inputs).

## User-Unavailable Degradation

If user input is missing for >5 calendar days, PMO continues non-blocking work in this order: TASK-019 → TASK-020 → TASK-027 → TASK-037. None of the four depends on a user decision; all four are blocking-findings work or a writer with a declared spec. Tasks blocked on missing inputs are flagged with the USER-id named, in every status report. TASK-028 does **not** enter this order — it needs a V5 signature, and a V5 rung recorded without the user is a label rather than a record. Agents NEVER substitute their judgment for missing user constraints on real-world / external / authorized actions.

## Phase Scope Reduction Rule

Choose **one or both** triggers (whichever fires first cuts scope). NO calendar-date triggers — phases are not bound to dates.

- **KR-progress trigger**: If at phase day 14, commit KRs are <50% achieved, Objective 1 collapses to TASK-019 and TASK-020 only; TASK-021, TASK-027 and TASK-028 defer to the next phase.
- **Phase-day trigger**: If by phase day 10 the tracks-host decision (first User Commitment above) is still open, P001-O1-KR1 collapses to declaring the three tracks on Perry itself, and the real-project variant defers to the phase that adopts one.

---

## Objective 1 — The three non-`project` modes run on a live track

Close the review debt blocking the mode work, then declare and exercise a `pipeline`, a `queue` and an `inquiry` track outside the test fixtures. A mode nobody can reach is a mode that does not exist.

### Key Results

> Declared in `phase/001-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **TASK-019 — `modes/pipeline.md`**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: mode file where a stage has a column, the WIP limit has a declared home and default, and `## Commitments` rows carry a track key
  - Verification: V4 re-review returns 0 blocking findings; evidence at `evidence/2026-08/TASK-019-020-v4-review.md`

- **TASK-020 — `modes/queue.md` + `BOARD.md § Intake` + triage drain**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: `Arrived` survives routing so queue SLA age is computable, plus the stage column and Commitments ownership fixes
  - Verification: V4 re-review returns 0 blocking; a queue triage run prints a non-`—` SLA age

- **TASK-027 — Lane rename goals/work/decide + aliases**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: router naming only directories that exist, `decide` routed to its own lane, withdrawn commands unquoted
  - Verification: 4th review round passes; `TestRouterNamesOnlyRealThings` green

- **TASK-021 — Recurrence register + `OKR.md § Commitments`**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: the recurrence register and the Commitments spine, per `DESIGN-003` phase D
  - Verification: a `queue`-mode track's commitments round-trip through `perry-state`

- **TASK-028 — `diagnose`/`adopt` mode detection + both READMEs**
  - Owner: User + Agent
  - User role: V5 sign-off — the rung the board already records for this row
  - Deliverable: mode detection in both pipelines, `README.md` and `README_cn.md` describing the four modes
  - Verification: `adopt` on a non-software folder proposes a non-`project` track; V5 record names what was checked

---

## Objective 2 — The `goals` lane can write its own state

`goals` is the one lane of three with no deterministic write tool, which is why this phase file was hand-written. Close that, and prove the write path cannot damage an existing `OKR.md` before it ships.

### Key Results

> Declared in `phase/001-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects

- **TASK-037 — `perry-goals` writer**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: `perry-goals` write subcommands per `DESIGN-005` step 3
  - Verification: byte-identity test against the existing `perry/OKR.md` passes, and reverting the writer breaks it

---

## Objective 3 — A real project can become Perry-shaped, once

Added mid-phase on 2026-08-17 by `ADR-004`. Until that decision, landing on a
real project meant teaching every tool one more shape, and the round-5 review
showed where that ends: two tolerance branches disagreeing with each other and
losing a project's live risks between them. The strategy changed from *adapt
forever* to *migrate once*, which turns an unbounded surface into one pipeline —
and creates work that serves no KR this phase had.

### Key Results

> Declared in `phase/001-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

`ADR-004`'s own reopening criterion is that migration proves unbuildable to its
five guarantees. P001-O3-KR2 is that criterion, made measurable — it is the KR whose
failure retires the decision rather than the phase.

### Projects

- **TASK-043 — Conformance marker**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: a declared, versioned, per-file marker plus the gate every writer calls
  - Verification: a writer refuses on an unmarked file and names the way forward; reading is unaffected; the three published contracts do not change shape

- **TASK-044 — Migration is dry-runnable, lossless, recoverable, user-declared**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: `/perry adopt` gains the five guarantees `ADR-004` names
  - Verification: run against copies of `gimegime-pmo` and `PolyForge` — the dry run shows the whole diff, every pre-existing id survives, a dirty tree refuses

- **TASK-045 — Retire the runtime tolerance branches**
  - Owner: Coding Agent
  - User role: none
  - Deliverable: the steady-state tools stop carrying fallbacks the marker makes unnecessary
  - Verification: each removal is its own commit whose test proves the strict path refuses rather than mis-parses. **Blocked by construction** — nothing may be removed before TASK-043 ships.

---

## Week-by-week breakdown

> `okr plan-week` reads the row for the current ISO week, proposes tasks, and (after user approval) PMO appends them to `BOARD.md`. Fill `TASK-IDs` as the week unfolds. Weeks below are loose ISO-week labels — they do NOT bound the phase; the phase ends on `score-phase`, not when the table runs out.

| ISO week | Focus | Target KRs to advance | TASK-IDs (filled by `plan-week`) |
|----------|-------|------------------------|------------------------------------|
| 2026-W34 | Clear the blocking findings on TASK-019 / TASK-020; land TASK-027's 4th review | P001-O1-KR4 | — |
| 2026-W35 | Declare the three tracks; make each mode's triage question answer from real state | P001-O1-KR1, P001-O1-KR2 | — |
| 2026-W36 | Mode-switch revert test; TASK-021; mid-phase review | P001-O1-KR3 | — |
| 2026-W37 | `perry-goals` writer + byte-identity test; TASK-028 V5; `score-phase` | P001-O2-KR1, P001-O2-KR2 | — |

---

## Definition of Done

### Must-Have (failure = phase missed)

- [ ] `.perry/config.md` carries a `## Tracks` table with a `pipeline`, a `queue` and an `inquiry` track, and `perry-state` loads all three mode files (P001-O1-KR1)
- [ ] TASK-019 and TASK-020 each pass V4 re-review with 0 blocking findings (P001-O1-KR4)
- [ ] TASK-027 passes its 4th review round (P001-O1-KR4)
- [ ] Each of the three live tracks answers its mode-specific triage question with a non-`—` value (P001-O1-KR2)
- [ ] `perry-goals` has a write path, and the byte-identity test against `perry/OKR.md` passes and fails when the writer is reverted (P001-O2-KR1, P001-O2-KR2, TASK-037)
- [ ] `phase/001-linkage.md` resolves every currently-open board task — each one either carries a phase-KR edge or sits in a declared `unlinked[]`, with none left unresolved
- [ ] `perry-lint --root .` reports zero errors after every write above

### Nice-to-Have (failure allowed; explained in retro)

- [ ] TASK-021 — recurrence register + `OKR.md § Commitments` lands
- [ ] TASK-028 — `diagnose`/`adopt` mode detection + both READMEs lands with a V5 record
- [ ] The review-round cap in `## Cost Ceiling` moves from doc-only to counted by a script

## Not Doing in this phase

> Anti-goals scoped to this phase. Often more concrete than overall Anti-Goals.

- No aiMark write contract and no aiMark-driven task lifecycle — TASK-034 defers whole, and Objective 4 of `OKR.md` gets no movement this phase.
- No event-log-canonical migration — TASK-038 defers; `BOARD.md` stays canonical for tasks until `perry-goals` proves the writer pattern.
- No adoption of PolyForge or gimegime-pmo, and no attempt on the 61 lint errors — Objective 3 of `OKR.md` is untouched.
- No User Input Queue tool (TASK-039) and no risk table (TASK-040), **despite TASK-039 being P1 on the board.** That priority and this deferral disagree; `work triage` owns the reconciliation, because `goals` does not write `BOARD.md`.
- No new `bin/` script for anything the four-round cap needs — the cap stays doc-only unless it becomes a Nice-to-Have deliverable.

## Process Note

PMO cadence (Monday Planning, Midweek Check, Friday Review, Mid-Phase Review, End-Phase Retro, weekly status reports) is owned by the `pmo` skill and does not consume phase Objective slots. See `work/SKILL.md` for the cadence definition.

---

## Changes / Pivots     <!-- append-only -->

- 2026-08-17 — **Objective 3 added mid-phase, and confirmed by the user the same day.** `ADR-004` changed how a real project gets landed — migrate once rather than adapt forever — and opened TASK-043/044/045, which served no KR this phase had. The alternative offered was to drop O3 and declare the three `unlinked`; the user kept it, accepting that the phase's Definition of Done grows and that it scores later.
- 2026-08-17 — Phase created. Slug written as `work-modes-live`, not the `helloworld` given on the command line — reason: the slug is the searchable half of the filename and `helloworld` describes no work. Focus chosen by the user from three evidence-backed options.

## Mid-phase check     <!-- filled by `okr dashboard` or `pmo mid-phase-review` -->

- **Pace**: —
- **Risks surfaced**:
- **Adjustments**:
- **Scope-reduction rule status**: armed

## Retro — phase scored     <!-- filled by `okr score-phase` when the phase closes -->

**Scored 2026-08-19 by Ran Jiao**, on the decision to roll to phase 002 for
ADR-007. Every score below was **measured**, and the command is given so the
number can be re-derived rather than trusted.

| KR | Score | Measured |
|---|---|---|
| P001-O1-KR1 | **missed** | `parse_tracks` on `.perry/config.md` returns `[('main','project')]` — 0 of 3 non-`project` modes on a live track |
| P001-O1-KR2 | **partial** | The code ships — `perry-state` carries `stage_counts`, `wip_breaches` and `intake`. Two of the three report empty **because no track is declared to exercise them**, so the capability is built and unproven |
| P001-O1-KR3 | **missed** | No revert test for a mode switch exists in `tests/test_work_modes.py` |
| P001-O1-KR4 | **partial** | Baseline 6, target 0. Two of three closed on TASK-019; TASK-020's round-6 finding is open (`route` ignores `--group`) |
| P001-O2-KR1 | **achieved** | `bin/perry-goals`, `bin/perry-task`, `bin/perry-decide` all exist and write — 3 of 3 |
| P001-O2-KR2 | **achieved** | The byte-identity test lives in `tests/test_goals_writer.py` and runs against all four `OKR.md` files |
| P001-O3-KR1 | **achieved** | `perry-conform status` reports **13/14 declared and matching**, and all three writers gate on it (ADR-004) |
| P001-O3-KR2 | **achieved** | TASK-044: dry-run byte-identical, 365 → 380 ids with none lost, 59 → 15 errors on gimegime-pmo, PolyForge refused in one sentence. Guarantee 3 FAILed on three unguarded write sites and was fixed; **its re-review has not run** |

**4 achieved · 2 partial · 2 missed.**

### Why the phase ends here rather than when its KRs hit

Perry's own model says a phase ends when its KRs hit, not on a calendar, and
this one ends at day 3 with two missed. That is a deliberate exception, and the
reason is `ADR-007`: it **changes the premise of two of these KRs** rather than
merely competing with them.

- **P001-O1-KR1** wants three non-`project` modes live on a real track. A track is
  declared in `.perry/config.md`, which ADR-007 turns into a store — so the
  file that KR is measured against is being replaced.
- **P001-O3-KR1** wants a state file to declare it is Perry-shaped at a version.
  That declaration is about **markdown shape**, and three of the files it
  covers stop being markdown.

Carrying them forward unchanged would have scored the same work twice under two
different meanings. They are re-expressed in phase 002 against the shapes that
will actually exist.

**P001-O2-KR1 was already met and unscored** — 3 of 3 write tools — which is what
the check for this rollover found first.


- **Scored on**: —
- **P-O1 score**: —
- **P-O2 score**: —
- **What went well**:
- **What underperformed**:
- **Anti-Goals violations** (if any):
- **Lessons**:
- **Carry-over to next phase**:
