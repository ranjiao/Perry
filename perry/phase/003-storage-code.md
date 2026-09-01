# Phase #003 — storage-code

> **Owner**: `goals` lane (only writer). `work` reads this every standup.
> **Started**: 2026-08-28
> **Status**: active
> **Source**: `OKR.md` v2 (Objective 2 — every piece of state is queryable and writable by deterministic code)
> **Predecessor**: `phase/002-fields-are-typed.md` (scored 2026-08-28, mean 0.89)
> **Tier 1 hard cap**: ≤ 300 lines.

## Phase Focus

**Phase 002 made the stores exist. Phase 003 makes the code live on them.**

Six projection stores are declared in `schema/state-schema.json § claims[]`.
Four exist on disk — `tasks.jsonl`, `okr.jsonl`, `risks.jsonl`,
`.perry/config.jsonl`. Two were built and never imported: `intake.jsonl`
(TASK-196) and `asks.jsonl` (TASK-197). And `perry-lint`, the one command that
is supposed to make ADR-007's guarantee checkable, gives a drift verdict for
**two of the six** — tasks and risks. `okr.jsonl` and `.perry/config.jsonl`
each have a working `diff` tool that the census does not call.

Meanwhile the read side still treats rendered markdown as truth where a store
already exists: `parse_tracks` is called at four sites in `bin/` that use
`.perry/config.md` as the authority on a project's tracks, while
`.perry/config.jsonl` sits beside it holding the same nine records.

The phase is scored when a store's existence, its drift verdict, and the code
path that reads it are all one answer instead of three.

This phase does **not** migrate anyone else's project — `TASK-097` carries
forward untouched — and it does **not** stop Python parsing the document class
(`design/`, `DECISIONS.md`, `phase/`, `.perry/roles/`). Phase 002's Not Doing
deferred that to "a later phase"; this is not that phase either, and folding it
in would put a ten-section prose file in the same migration as a 35-column
table for the second time.

## Operating Rules

- **Count call sites, never names.** Phase 002's most expensive recurring
  defect was locating an implementation by grepping its name — it recurred
  roughly ten times, once over-counting and once missing a whole second
  reporter. Every KR below names the expression or the call and, where the
  baseline is small, the file and line.
- **A gate is not green until it has been shown able to go red.** Reverting the
  line that implements a check must break its test. A pass that was never
  falsifiable is not evidence (phase 002, lesson 4).
- **An absent store reports `unchecked`, never `clean`.** This is the property
  under test in `P003-O1-KR3`, and it is also a rule for anything written this
  phase.
- **Agent autonomy**: agents may delete, fence and re-point code paths inside
  this repository, and may import Perry's own stores. Agents may **not** touch
  any project other than Perry's own.
- **User authorization required for**: anything in `.perry/hook.md §
  High-stakes operations` — publishing, history rewrites, host skill
  installation, and writing into a project Perry does not own.
- **Evidence requirement**: every KR movement cites a command's output at
  `evidence/2026-08/` or later, never a claim.

## Cost Ceiling (phase #003)

- Spend cap: **$0** in new paid APIs, models or infra. Perry is stdlib Python
  and stays that way; a dependency is a decision, not an implementation detail.
- Wiring status: **doc-only**. Nothing in code refuses an import.
- ⚠ **Open risk, surfaced at every snapshot** per the goals-lane style rule:
  the ceiling is a convention, not a guard. The one thing that makes it cheap
  to hold is that the test suite already reads identically under
  `PYTHONNOUSERSITE=1 /usr/bin/python3`, so a new dependency shows up as a red
  suite rather than as silent drift.

## User Commitments

- **Decide the read-side promise for `.perry/config.md`.** `USER-903` settled
  the *write* side — the file became a projection. `P003-O2-KR1` changes who
  reads it: four call sites move from the markdown to `.perry/config.jsonl`.
  `SKILL.md` promises the user owns that file directly, and this is the half of
  that promise not yet decided.
- **V5 sign-off on the adoption-reader fence** (`P003-O2-KR2`). It changes
  which code path a foreign project goes through, and phase 002's carried DoD
  item exists because that path has never been tested on a real project.
- ~~**Attribution answers for the 40 rows still never asked** (`P003-O3-KR1`). Perry
  never guesses a KR; these can only be declared.~~ **Withdrawn 2026-08-31** —
  the backfill is phase 004's; see `## Changes / Pivots`.
- **`git push`.** `feat/work-modes` is several hundred commits ahead of
  `origin/main`; the remote and CI have seen none of this phase's predecessor.
- Phase scope-reduction trigger review, and phase-scoring participation.

## User-Unavailable Degradation

If user input is missing for >5 calendar days, work continues in this order:
**TASK-209 → TASK-095 → TASK-099 → TASK-050 → TASK-199**. Objectives 1 and 2
are fully reachable without the user.

~~**Objective 3 stalls by design, and that is not a defect.** `P003-O3-KR1` is
resolved by declaring an attribution, and `reference/okr-linkage.md` forbids
guessing one. An agent that filled `unlinked[]` to clear the number would be
recording a decision nobody made.~~ **Rewritten 2026-08-31, and the conclusion
inverts.** With `P003-O3-KR1` withdrawn, Objective 3 is the `add`-time gate
alone and it does **not** stall on an absent user: declaring a row unlinked at
`add` time is the author's own statement about their own row, so the gate is
reachable by an agent working through the degradation order above.

## Phase Scope Reduction Rule

- **KR-progress trigger**: ~~if at phase day 10 the commit KRs of Objectives 1
  and 2 are <50% achieved, Objective 3 collapses to its Must-Have — the
  `add`-time linkage gate (`P003-O3-KR2`) — and the backfill of the existing
  never-asked rows defers to phase 004.~~ **Spent 2026-08-31, phase day 4.**
  The user took this exact collapse deliberately rather than waiting for the
  condition; it cannot fire again. Recorded so a day-10 reader does not evaluate
  a trigger whose cut has already been applied.
- **Phase-day trigger**: if by phase day 14 the read-side decision on
  `.perry/config.md` is still open, `P003-O2-KR1` collapses to the two call
  sites that are unambiguously internal (`bin/perry-state:139`,
  `bin/perry-goals:2102`) and the two user-facing readers defer.

---

## Objective 1 — Every declared store exists, and one command checks all of them

ADR-007's guarantee is only as wide as the census that checks it. Today the
guarantee is checked for tasks and risks, unchecked for four, and the
difference is invisible unless you read the tail of a lint run.

### Key Results

> Declared in `phase/003-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **TASK-209 — the drift census covers one store of five**
  - Owner: Coding Agent · User role: none
  - Deliverable: `check_store_drift` reports every declared projection store
  - Verification: remove each store in turn; lint prints `unchecked` six times

## Objective 2 — The code reads a store, not a rendered file

### Key Results

> Declared in `phase/003-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

**Two exclusions in `P003-O2-KR1`, both deliberate.** `bin/perry-tasks:1473`
parses `BOARD.md` to *compare* it against the store — a drift check must read
the rendered file by definition. `bin/perry-migrate:1177` / `:1188` parse a
foreign project's board and OKR, which is what adoption is. Phase 002's
`P002-O2-KR3` set a target of 0 parser lines and scored 0.68 against a number
that could not have been reached, because `TASK-094` had already proved the
adoption reader must stay. The exclusions are what make this target real.

### Projects (seed for PMO TASK-IDs)

- **TASK-095 — remove the parser for the three stores; keep what adoption needs**
  - Owner: Coding Agent · User role: the read-side decision on `.perry/config.md`
  - Deliverable: four `parse_tracks` call sites read `.perry/config.jsonl`
  - Verification: the four named lines no longer call a markdown parser
- **TASK-099 — sweep `bin/`, `viewer/` and `tests/` for handling ADR-007 made dead**
  - Owner: Coding Agent · Deliverable: the fence and its guard
  - Verification: restoring one removed call site turns the guard red
- **TASK-050 — one normalization for a header cell, not two**
  - Owner: Coding Agent · Deliverable: re-scoped to the adoption reader
  - Verification: a mutation harness, not another regex
- **TASK-199 — `BOARD.md` carries two truth models and nothing marks the boundary**
  - Owner: Coding Agent · Verification: the boundary is readable from the file

## Objective 3 — The phase's KRs cover the work that actually runs

Phase 002 declared 13 tasks and the board ran 47. At scoring, **43 open rows
resolved to no KR against 3 that did** — the phase's largest single signal, and
the retro's own conclusion was that phase 003 must either declare KRs the live
work serves or make the linkage step part of `add`. This Objective does both.
Re-measured at phase start the set is **45**, not 43 — the board opened 14 rows
between 002's scoring and this file. 43 is 002's number and is not carried.

The number to drive to zero is not "unlinked rows". Work that serves no KR is a
legitimate, declarable state. The number is rows in **neither** state — never
linked, never declared — because that is the set nobody has ever been asked
about.

### Key Results

> Declared in `phase/003-linkage.md`; `bin/perry-goals krs` prints them. Not written
> here — TASK-157 / DESIGN-013 § 5.1, a fact with a schema lives in one store.

### Projects (seed for PMO TASK-IDs)

- **PROJ-003-LINK — attribution becomes part of opening a row**
  - Owner: Coding Agent + User
  - User role: declaring which KR a row serves — never guessed
  - Deliverable: `add` resolves to exactly one KR or writes a declared `unlinked`
  - Verification: ~~`perry-state --section attribution` reports 0 never-asked
    rows~~ **restated 2026-08-31** — every `main`-track row opened after the gate
    lands carries a `link-edge` or `link-unlinked` event in `.perry/events.jsonl`
    written by the same action as its `add`

## Definition of Done

**Must-Have** (failure = phase missed):

1. `perry-lint --root .` prints a drift verdict for six stores, and prints
   `unchecked` for each one whose file is removed.
2. `intake.jsonl` and `asks.jsonl` exist, imported by their own commands.
3. The four named `parse_tracks` call sites read `.perry/config.jsonl`.
4. The adoption-reader guard exists **and has been shown to go red**.
5. ~~`perry-state --section attribution` reports 0 never-asked `main`-track
   rows.~~ **Restated 2026-08-31**: every `main`-track row opened after the gate
   lands carries a KR edge or an `unlinked` declaration written by its own `add`.
   The rows that were never asked before the gate are phase 004's.

**Nice-to-Have** (failure allowed, explained in retro):

6. `BOARD.md`'s truth-model boundary is marked in the file (TASK-199).
7. `TASK-050`'s mutation harness replaces the regex round.

## Not Doing in this phase

- **Migrating gimegime-pmo or PolyForge** (`TASK-097`). Carried from phase
  002's DoD item 5, not waived. The user decided on 2026-08-28 that the target
  project's state is not suitable yet and the features land first. The
  consequence stands and is worth restating: **phase 002's own argument — that
  the abstraction survives contact with a real project — is still untested, and
  phase 003 does not test it either.**
- **The document class.** `design/*.md`, `DECISIONS.md`, `phase/*.md`,
  `.perry/roles/*.md` stay documents, and Python keeps parsing them for now.
- **Counting parser lines.** `P002-O2-KR3`'s target was unreachable by
  construction; this phase measures call sites instead and says so in the KR.
- **Raising the `BOARD.md` 200-line cap** to make room for intake. Phase 002's
  queue-mode argument holds: an overflowing intake is a finding, not a cap
  problem.

## Process Note

Cadence work — weekly status, handoffs, journal entries — lives under
`BOARD.md § Cadence` and does not consume a phase Objective slot.

Three intake rows are past the `intake` track's 5d SLA as of 2026-08-28:
`TASK-139` (8d, over by 3), `TASK-155` (7d, over by 2), `TASK-157` (7d, over by
2). They belong to `/perry work triage`, not to a phase Objective, and are
noted here only so the phase is not planned as though the queue were empty.

`TASK-157` — *plan-phase still authors the KR block by hand in a file
documented as machine-written* — is about the command that wrote this file.

## Changes / Pivots     <!-- append-only -->

2026-08-31 — **`P003-O3-KR1` withdrawn; Objective 3 keeps `P003-O3-KR2` only.**
*What*: the backfill KR — open `main`-track rows in neither `tasks[]` nor
`unlinked[]` — is removed from `phase/003-linkage.md`; the `add`-time linkage
gate stays. Phase KR count 8 → 7. *Why*: the gate is the mechanism that makes
attribution happen as ordinary project work; the backfill is a one-off cleanup
that the gate makes cheap afterwards. Doing the cleanup first spends the phase
on 45 answers and leaves the next 45 rows arriving the same way. The population
moved 45 → 7 during phase 003 **without the backfill being worked at all**, and
those 7 (TASK-253…TASK-259) are exactly the rows the gate would have caught at
`add`. *Who*: the user, asked directly and answering "去掉 KR1, 留下 KR2". The
cut is the one this phase's own KR-progress trigger already describes, taken at
day 4 instead of day 10. *Consequences*: DoD Must-Have 5 restated above;
PROJ-003-LINK's verification restated; the KR-progress trigger marked spent.
Pre-pivot state preserved at
`phase/snapshots/2026-08-31-003-storage-code.md`.

## Mid-phase check     <!-- filled by `okr dashboard` or `pmo mid-phase-review` -->

## Retro — phase scored     <!-- filled by `okr score-phase` when the phase closes -->
