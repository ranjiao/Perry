# Phase #004 — guided

> **Owner**: `goals` lane (only writer). `work` reads this every standup.
> **Started**: 2026-09-15
> **Status**: active
> **Source**: `OKR.md` v4 (2026-09-15)
> **Predecessor**: `phase/003-storage-code.md` (scored 2026-09-15 — O1 1.0 · O2 0.75 · O3 0.33)
> **Tier 1 hard cap**: ≤ 300 lines.

## Phase Focus

**Phase 003 made the code live on the stores and deleted `BOARD.md`. Phase 004
makes Perry usable by the one person running a project.** They are told where
they stand and what to do next; their plans are asked for and approved rather
than typed into a checklist; what they must read and decide fits on one screen
and is recorded; and changing Perry itself gets cheaper instead of slower.

The phase is scored when `DESIGN-020`'s recommendation and its first planning
route run on this repository and on `~/proj/SkyTonight`, and when `DESIGN-021`'s
tiers and `DESIGN-017`'s structural rules gate every merge to `main`.

This phase does **not** target the storage tail (`ADR-011` Tiers B and C,
`viewer/parsers.py`), the aiMark write contract, or the roles runtime — all
three are in `OKR.md` v4 as stretch or withdrawn. The focus is guidance,
elicitation, user load and iteration cost.

## Operating Rules

- **Every user decision is recorded before it is acted on.** A decision the user
  makes — including one that lands in a spec amendment or a commit — has a
  `USER-` record in `asks.jsonl` first. Measured by `P004-O3-KR2`. User decision,
  2026-09-15.
- **Hygiene rows are throttled.** A row for an internal consistency defect with
  no user-visible failure: at most 2 in progress and at most 3 opened per ISO
  week. A review finding defaults to the evidence file, not a new row. User
  decision, 2026-09-15.
- **Objective 4 builds mechanisms, not cleanups.** The Python and test lines it
  adds, net of what it deletes, are ≤ 0; splitting an over-budget reference page
  is not counted. User decision, 2026-09-15.
- **Agent autonomy**: agents may implement the locked phases of `DESIGN-020`,
  `DESIGN-017` and `DESIGN-021` inside this repository, and write Perry's own
  stores through their tools.
- **User authorization required for**: everything in `.perry/hook.md §
  High-stakes operations` — including the claim-surface edits
  `schema/state-schema.json` needs for `DESIGN-020` phase D and `DESIGN-017` A1,
  `git push`, and any write into `~/proj/SkyTonight`, a project Perry does not own.
- **Evidence requirement**: every KR movement cites a command's output under
  `evidence/2026-09/` or later. A test is not evidence until reverting the fix
  has been shown to break it.

## Cost Ceiling (phase #004)

- Spend cap: **$0** in new paid APIs, models or infra. Perry stays stdlib Python.
- Wiring status: **doc-only** ⚠ — nothing in code refuses an import. Open risk,
  surfaced at every snapshot. `DESIGN-017` S3 (standard library only) is the
  guard that would wire it, and it is this phase's work.
- The cost this phase does measure is iteration time: `tests/durations.json`
  and `P004-O4-KR1`.

## User Commitments

- **Run the first-OKR interview on `~/proj/SkyTonight` and answer it yourself**,
  and authorize the writes Perry makes there (`P004-O2-KR1`).
- **Consent to the two claim-surface edits** when they are dispatched: `plans/`
  (`DESIGN-020` decision 5) and the architecture document's anchor
  (`DESIGN-017` A1).
- **Confirm the decided sections of `ARCHITECTURE.md`**: the first § 8 hash
  (`DESIGN-017` D2) and the § 3 `Forbidden` line that contradicts NN-6.
- **Decide when `main` is pushed** — it is more than 317 commits ahead of
  `origin/main`.
- Phase scope-reduction trigger review, and phase-scoring participation.

## User-Unavailable Degradation

If user input is missing for more than 5 calendar days, work continues in this
order: `DESIGN-021` phase A (selector replay) → `DESIGN-020` phase A →
`DESIGN-017` D1 (structural rules) → `DESIGN-017` E1 (prose budgets) →
`TASK-264`. What waits for the user: the SkyTonight interview, both schema
edits, and the push. Agents never substitute their judgement for a missing user
answer on any of those.

## Phase Scope Reduction Rule

- **Phase-day trigger**: If by phase day 14 the first-OKR interview on
  `~/proj/SkyTonight` has not run, Objective 2 collapses to `TASK-264` plus the
  question bank scored on a scratch-project transcript; the SkyTonight run
  defers to phase 005 and `P004-O2-KR1` is scored partial.
- **KR-progress trigger**: If at phase day 21 fewer than half of the commit KRs
  carry a measured current value, Objective 3 collapses to its Must-Have — the
  decision-recording rule — and the snapshot and next-action budgets defer.

---

## Objective 1 — The user always knows where they are and what to do next

`DESIGN-020` phases A and B: a next step derived from state, shown at `/perry`
and after every state-changing command — and, on this repository, the cadence it
recommends actually happening.

### Key Results

> Declared in `linkage.jsonl`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **`DESIGN-020` phase A — the `next` section, rule file and passive block** (TASK-NNN, new at hand-off)
  - Owner: Coding Agent · User role: none
  - Deliverable: `perry-state --section next`, the rule file, `reference/next.md`; `/perry` and lane standups point at it
  - Verification: five fixture states yield their expected primary rule; deleting any rule reddens its fixture
- **`DESIGN-020` phase B — the closing step and its silence setting** (TASK-NNN, new at hand-off)
  - Owner: Coding Agent · User role: none
  - Deliverable: the closing step in `reference/next.md`, pointers in every state-changing procedure, a per-project setting
  - Verification: a guard enumerates the subcommands; removing one pointer turns it red; the setting silences the block

## Objective 2 — Plans are asked for, drafted and approved

`DESIGN-020` phases C and D, and the `goals` KR writer they need: one real
interview on a project with no OKR, a draft that survives interruption, and a
finalize that writes through tools.

### Key Results

> Declared in `linkage.jsonl`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **`TASK-264` — the `goals` KR writer**
  - Owner: Coding Agent · User role: none
  - Deliverable: `perry-goals` writes overall and phase KR records
  - Verification: a KR written by the tool renders through `perry-okr diff` identical; a malformed KR is refused
- **`TASK-190`, `TASK-191` — the question bank and the SkyTonight transcript** (re-pointed to `DESIGN-020`; parent `TASK-177`)
  - Owner: Coding Agent + User · User role: answering the interview
  - Deliverable: the first-OKR question bank; a transcript and its rubric score
  - Verification: `reference/input-quality.md § 1` run on the produced OKR
- **`DESIGN-020` phase D — draft file, resume and finalize** (TASK-NNN, new at hand-off)
  - Owner: Coding Agent · User role: consent to the `plans/` claim
  - Deliverable: the draft file, resume through the interrupted scan, finalize through writers
  - Verification: the two behaviours in `P004-O2-KR3`

## Objective 3 — What the user reads and decides fits on one screen, and is recorded

The snapshot, the questions Perry asks and the rows the user reads are held to a
size, and no decision the user makes goes unrecorded.

### Key Results

> Declared in `linkage.jsonl`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **Snapshot and decision-card specification** (TASK-NNN, new at hand-off)
  - Owner: Coding Agent · User role: approving the card format
  - Deliverable: the snapshot shape in `reference/snapshot.md`; the decision card in `reference/user-load.md`
  - Verification: a rendered `/perry` measured against `P004-O3-KR1`; new asks measured against `P004-O3-KR2`
- **`TASK-434` — answered asks leave the queue**
  - Owner: Coding Agent · User role: none
  - Deliverable: the asks sweep
  - Verification: an answered ask is swept; an open one is not

## Objective 4 — Changing Perry gets cheaper, and its architecture holds

`DESIGN-021`'s tiers and merge gate, and `DESIGN-017`'s structural rules, prose
budgets and the file the tooling can finally see.

### Key Results

> Declared in `linkage.jsonl`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **`DESIGN-021` phases A–C — selector replay, tiers, merge gate** (TASK-NNN, new at hand-off; phase C absorbs `TASK-238`)
  - Owner: Coding Agent · User role: none
  - Deliverable: `COVERS` on every module and the 50-merge replay; `--tier`; the full suite on the merge result before merge
  - Verification: the replay's gate; the printed selection; one full run per merge in the merge evidence
- **`DESIGN-017` A2, D1–D3, E1–E2** (TASK-NNN, new at hand-off)
  - Owner: Coding Agent · User role: confirming § 8's first hash
  - Deliverable: the resolver; S1–S7; the hash; the merge-time review; L2 budgets and five context bills
  - Verification: each row's Verification column in `DESIGN-017 § 6`
- **`TASK-312`, `TASK-401`** — `test_tree_guard.py` at 62.5 s; extensionless entrypoints recompiled on every call

---

## Definition of Done

**Must-Have** (failure = phase missed):

1. `perry-state --section next` passes its five fixture states and `/perry`
   renders its block (`P004-O1-KR1`).
2. `TASK-264`'s KR writer lands, and the first-OKR interview on
   `~/proj/SkyTonight` scores 0 issues — or the phase records that the day-14
   trigger fired (`P004-O2-KR1`, `P004-O2-KR2`).
3. Every user decision made during the phase has a `USER-` record
   (`P004-O3-KR2`).
4. `DESIGN-021` phase A's replay passes its gate, and the full suite runs once
   per merge on the merge result (`P004-O4-KR1`).
5. `DESIGN-017`'s seven structural rules run before merge, each shown red under
   its mutation (`P004-O4-KR2`).

**Nice-to-Have** (failure allowed, explained in retro):

6. The closing step on every state-changing subcommand (`P004-O1-KR2`).
7. Planning drafts resume and finalize through writers (`P004-O2-KR3`).
8. A snapshot of ≤ 12 lines and a next-action p90 of ≤ 400 characters
   (`P004-O3-KR1`, `P004-O3-KR3`).
9. Prose tier budgets and five context bills (`P004-O4-KR3`).

## Not Doing in this phase

- **The storage tail**: `ADR-011` Tiers B and C, `viewer/parsers.py`
  (v4 `O3-KR4`, stretch).
- **The aiMark write contract** (`TASK-396`; v4 `O4-KR3`, stretch).
- **`DESIGN-020` phases E and F** — the phase, week and commitments routes, and
  `/perry plan` — unless the mid-phase review pulls them in.
- **`DESIGN-010`, `DESIGN-009`, `DESIGN-012`'s router, `DESIGN-019`.**
- **Behavioural evaluation of the skill prose** (`DESIGN-017` decision 6).
- **Migrating any existing project.** SkyTonight is initialized from zero;
  nothing already in it is rewritten.

## Process Note

Cadence work — weekly status, handoffs, journal — belongs to `work` and takes no
Objective slot; `P004-O1-KR3` measures whether it happens, not the work itself.

At hand-off, `DESIGN-020`, `DESIGN-017` and `DESIGN-021` open their rows
against these KRs, and the 40 rows phase 003 filed without an attribution are
re-declared here (retro carry-over) — in batches, each with a default answer,
never as forty questions.

## Changes / Pivots     <!-- append-only -->

## Mid-phase check     <!-- filled by `okr dashboard` or `pmo mid-phase-review` -->

## Retro — phase scored     <!-- filled by `okr score-phase` when the phase closes -->
