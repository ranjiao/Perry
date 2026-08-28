# DESIGN-012: Closing a phase is four commands and nothing owns their order

> Status: locked
> Date: 2026-08-28 · Locked: 2026-08-28
> Author: Perry maintainer   · Implementation owner: Coding Agent
> Linked OKR: KR-O2.3 (`perry/OKR.md` v2, Objective 2 — every piece of state is queryable and writable by deterministic code)
> Supersedes: —   · Superseded by: —
> Revisits: `goals/reference/phases.md`, `work/reference/subcommands.md`, `reference/snapshot.md`, `reference/router-subcommands.md`
> Sign-off: User Decisions 1-4 answered by Ran Jiao in session on 2026-08-28 (`/perry decide resolve DESIGN-012`), so this went `draft` -> `locked` without an `in_review` hold — the state `in_review` exists to await exactly that sign-off, and it had already happened.

## 1. Problem

Ending a phase takes four commands across two lanes:

```
goals score-phase  →  work end-phase-retro  →  work rollover  →  goals plan-phase <slug>
```

Nothing in Perry models that sequence. `reference/snapshot.md:153` already
suggests all four in one breath as a single next action, which is the smell:
a sequence the router recommends atomically but no code runs atomically is four
independent chances to get the order wrong.

**Four shipped pages describe two opposite orders.**

| page | what it says | implied order |
|---|---|---|
| `goals/SKILL.md:154` | `evidence/<YYYY-MM>/retro.md` \| pmo \| "Read by OKR `score-phase` **after PMO writes it**" | retro **before** score |
| `work/reference/subcommands.md:401` | "**Triggered when OKR `score-phase` is about to run**" | retro **before** score |
| `goals/reference/phases.md:229` (step 5) | "**Hand the retro summary to `work`; do not write it.** … let `/perry work` write it." | retro **after** score |
| `goals/reference/phases.md:155, 162` | `plan-phase` **reads** `evidence/retro.md` and its `§ Health metrics` | only constrains retro **before** `plan-phase` |

**It has already failed once, on this project, and the failure is on the
record.** Phase #002 closed on 2026-08-28:

- `goals score-phase` ran and wrote `phase/002-fields-are-typed.md § Retro —
  phase scored` (mean 0.89). It did **not** write `evidence/2026-08/retro.md`;
  that file did not exist until hours later.
- `goals plan-phase 003` then ran, so `phase/CURRENT` already read
  `003-storage-code`.
- `work end-phase-retro` was invoked **after both**. Its own procedure
  (`work/reference/subcommands.md:401`) says to read "journal entries since
  **the current phase** started" — by then a phase one day old. Executed
  literally it would have produced an empty retro for #003. It was aimed at
  #002 by hand.
- `work rollover` never ran at all. Its step 1 guarded on a file that, in the
  order actually taken, nothing had yet produced — and it named the wrong
  command to produce it (`work/reference/subcommands.md:902`, corrected
  2026-08-28).

**The ownership statements drifted for a release, in the same seam.**
`goals/SKILL.md:126` said `score-phase` produces `evidence/<YYYY-MM>/retro.md`
— a directory the signed hand-off contract gives to `work`. The correction had
**already landed** one level down in `goals/reference/phases.md:229` ("this
step instructed writing into it for a release") and never reached the index
table. Corrected 2026-08-28. The guard that should have caught it,
`tests/test_ownership.py`, cannot see lane `SKILL.md` files at all — that is
**TASK-216**, filed the same day.

**The content split held only because a human did it by hand.** `score-phase`
writes scores, what-went-well, lessons and carry-overs into the phase file;
`end-phase-retro` is specified to produce per-KR status, lessons and
carry-overs too. On 2026-08-28 the overlap was resolved live — `goals` kept
scores and goal-level narrative, `work` took evidence paths, board metrics,
health check and carry-over rows — and **no rule anywhere states that split.**
The next operator has no reason to repeat it.

## 2. Goals

1. **One invocation closes a phase.** Measured: the operator issues one
   command, and `.perry/events.jsonl` shows all four stages executed, in the
   declared order, within one session.
2. **The retro reads the phase being closed, never `phase/CURRENT`.** Measured
   by mutation: advance `CURRENT` to the next phase before the retro stage runs
   and the retro still targets the closing phase. The 2026-08-28 failure is the
   fixture — reproduce it, then show it fixed.
3. **Exactly one page states the order; every other page cites it.** Measured:
   `grep -rn "retro\.md"` over the skill returns no two hits describing
   opposite orders. (Baseline 2026-08-28: 23 hits, of which 8 are the
   `okr-vN-retro.md` decoy and 4 are the contradiction table in §1.)
4. **The `goals` / `work` retro split is declared where the order is
   declared.** Measured: a reader can name, without running anything, which
   sections of a phase close each lane produces.
5. **No fourth writer.** Measured: the orchestrator writes no state file of its
   own; every write is performed by an existing lane subcommand, and
   `tests/test_ownership.py` — as widened by **TASK-216** — stays green.
6. **A close interrupted midway is visible and resumable**, rather than leaving
   a scored phase with no retro and a `CURRENT` nobody moved. Measured: kill
   the run after each stage in turn and show the next `/perry` invocation
   reports the half-closed phase — resolved from state, with no new file, per
   the five-row table in § 5.3.

## 3. Non-Goals

- **Not merging the four subcommands into one lane.** The sequence spans two
  writers — `goals` owns `phase/` and `OKR.md`, `work` owns `evidence/` and
  `journal/` — so a merged subcommand inside either lane would violate the
  signed contract on its first run. `goals/SKILL.md:126` is the proof that this
  mistake is easy to make and survives review.
- **Not removing the four subcommands.** Each stays individually invocable. A
  phase can be re-scored, a retro re-run, a rollover repeated; the orchestrator
  is a sequence over them, not a replacement.
- **Not changing what a phase is**, nor the scoring arithmetic, nor the ten
  mandatory sections of a phase file.
- **Not fixing attribution.** The retro's headline finding — 10 of 100 closed
  rows resolved to a phase KR — belongs to `P003-O3` and to making linkage part
  of `add`. This design must not silently absorb it.
- **Not widening the ownership guard.** That is **TASK-216**, a prerequisite
  rather than a part.
- **Not `mid-phase-review`.** It shares the health-check runner and nothing
  else; it does not end anything, so it has no ordering problem.
- **Not a new state file.** Whether a resumability dossier is an exception is
  User Decision 3; the default is no.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where the retro sits relative to scoring | Retro before score / Retro after score / Split around score | **Retro after score** | 2026-08-28 |
| 2 | Whether the next phase's slug is required up front | Required to start / Asked at the end / Optional — may close phase-less | **Asked at the end** | 2026-08-28 |
| 3 | What an interrupted close leaves behind | Resumable dossier / Detected from state, no new file (Recommended) / Nothing — re-run stages by hand | **Detected from state, no new file** | 2026-08-28 |
| 4 | Where the two-lane retro split is declared | A `cross_file` check (Recommended) / One prose page, cited / A `files[]` spec for `retro.md` / Not declared — convention only | **A `cross_file` check** | 2026-08-28 |

**Row 1** is the contradiction in §1 and cannot be settled by reading the
files, because both orders shipped. The trade-off:

- *Retro before score* makes the retro the input to scoring — `goals` scores
  against per-KR outcomes `work` already established. Cost: both lanes produce
  a per-KR verdict, and they can disagree.
- *Retro after score* makes the retro the record of a decided phase and the
  input to `plan-phase` only. Cost: `phases.md` step 5's hand-off writes a
  summary into a file `work` is also writing, and `rollover`'s guard then
  depends on a file with two possible producers.
- *Split around score* — `work` establishes evidence and board metrics, `goals`
  scores, `work` then writes the retro — is what actually happened on
  2026-08-28. It is the most faithful and the most machinery.

**Row 2** decides whether `phase/CURRENT` may be empty between phases.
`goals/reference/phases.md` step 7 already clears it at scoring, so today the
gap exists and is simply short.

**Row 3** is the `adopt` / `diagnose` question asked of a shorter pipeline.
Those two carry a dossier because their stages are hours of user answers; a
phase close is four mechanical stages whose progress is already legible from
`phase/<NNN>` status, `evidence/retro.md` existence, `CURRENT` and the event
log — which is why *detected from state* is marked recommended and a fifth
claimed path is not.

**Row 4** is what stops goal 4 from decaying back into a habit. Its options
were sharpened on 2026-08-28, before it was answered: "in `state-schema.json`"
turned out to be two different things — a `cross_file` **check**, which reports
and gates nothing, and a `files[]` **spec**, which under
`Conformance gate: enforce` would make a non-matching retro unwritable in every
Perry project. Those costs are too far apart to sit behind one label.

### Consequences accepted, 2026-08-28

Recorded here because each choice above had a named cost, and a cost chosen
without being written down is one the next reader will rediscover as a defect.

**Decision 1 settles TASK-217.** The order is
`score-phase → end-phase-retro → rollover → plan-phase`.
`goals/reference/phases.md:229` already describes it; the two pages that
disagree — `goals/SKILL.md:154` ("Read by OKR `score-phase` after PMO writes
it") and `work/reference/subcommands.md:401` ("Triggered when OKR
`score-phase` is about to run") — are wrong under this decision and are what
TASK-217 changes.

**Decision 1's accepted cost, and what it now requires.** The trade-off named
*two possible producers of `evidence/retro.md`*: `phases.md` step 5 hands a
retro summary over while `work` also writes that file. Accepting *retro after
score* accepts that hand-off — so the requirement it creates is that
**`goals` hands prose and `work` performs every write to that path.** One
producer, one writer, and `rollover`'s step-1 guard then has an unambiguous
thing to guard. It does not become "whoever gets there first".

**Decision 1 constrains Decision 4.** `phases.md` step 1 already collects a
per-KR `achieved | partial | missed | dropped` from the user during scoring.
With the retro running *after* that, the retro must **cite those verdicts, not
re-derive them** — otherwise the two lanes each produce a per-KR judgement and
the design has reintroduced the disagreement it just avoided. Whatever form
Decision 4 takes, it has to say that.

**Decision 2** makes the close block once, at the end, for the next slug. The
window in which `phase/CURRENT` is empty is bounded by a single run, between
`rollover` and `plan-phase` — narrower than today, where
`goals/reference/phases.md` step 7 clears it at scoring and nothing bounds how
long it stays clear.

**Decision 4 is enforceable because Decision 1 made it mechanical.** With the
retro running after scoring, "the retro cites the verdicts rather than
re-deriving them" is a comparison between two files that both exist:
`evidence/<YYYY-MM>/retro.md`'s per-KR status against
`phase/<NNN>-<slug>.md § Retro`'s scores table. Divergence *is* the defect,
and it is checkable. Under *retro before score* it would not have been — there
would be nothing to compare against yet.

Three constraints the implementing row inherits:

- **Name the surface exactly.** `cross_file` id `linkage-objective-agrees` is
  declared at `error` and **is** implemented, and the 002-linkage misnesting
  still passed at 0 errors — because it reads a linkage row's `Objective`
  column, not the frontmatter's `objectives[].id` nesting. A check implemented
  against a narrower surface than its description implies reads as coverage it
  does not have. Write down which two spans are compared.
- **Prove it can go red.** Phase #002's lesson 4: a gate whose green is a
  tautology is worse than no gate. Mutate one per-KR status in a retro and the
  check must fail.
- **Severity is `warn`, not `error`, unless the implementing row argues
  otherwise.** The boundary this project settled on 2026-08-21
  (`phase/002-fields-are-typed.md § User Commitments`) is that **errors are
  shape violations and warnings are quality signals**. A retro disagreeing with
  the scores is a content disagreement in a well-shaped file.

**It also keeps `evidence/` out of the conformance gate.** A `cross_file`
check adds no `files[]` entry, so no retro anywhere becomes unwritable for
failing to match a declared heading set — the same restraint Decision 3 chose,
applied to the shape surface instead of the claim surface.

**Decision 3 adds no path to `claims[]`.** The resume point is computed from
what the stages already leave behind: the phase file's `Status:`, whether
`evidence/<YYYY-MM>/retro.md` exists, where `phase/CURRENT` points, and
`.perry/events.jsonl`. This extends the shape `perry-state --section
interrupted` already has rather than minting a fifth pipeline artifact — and
`.perry/hook.md` lists changes to the claim surface as a high-stakes
operation, so not needing one is worth the constraint.

## 5. Architecture

### 5.1 · The orchestrator, and the two invariants

A **router-level orchestrator**, on the precedent `$PERRY_HOME/SKILL.md §
Router subcommands` already states for `adopt` and `diagnose`: *"orchestrated
here and materialized through the lanes' own subcommands — neither is a fourth
writer."*

```
/perry close-phase                       ← router. Writes nothing itself.
   │
   ├─ resolve the CLOSING phase from phase/CURRENT, ONCE, and hold it
   │
   ├─ stage 1  goals score-phase        (scores; hands a retro summary over)
   ├─ stage 2  work  end-phase-retro    (writes evidence/<YYYY-MM>/retro.md)
   ├─ stage 3  work  rollover           (carries rows; CLEARS phase/CURRENT)
   │
   ├─ ask for the next slug here, and only here          ← Decision 2
   └─ stage 4  goals plan-phase <slug>  (new phase file + linkage graph; sets CURRENT)
```

Two invariants carry most of the value, and both are data-flow properties
rather than documentation:

**I1 — the closing phase id is resolved once, at entry, and threaded.** Today
every stage re-reads `phase/CURRENT`, so the moment one stage advances it,
every later stage is aimed at the wrong phase. That is exactly the 2026-08-28
failure in § 1: `plan-phase 003` had already run, `CURRENT` read
`003-storage-code`, and `end-phase-retro` executed literally would have
produced an empty retro for a phase one day old.

**I2 — `phase/CURRENT` is written in exactly one place.** Any second stage that
can move it is a second writer of the sequence's own control state, and I1
then only holds by luck. This costs a real edit:
`goals/reference/phases.md` step 7 currently clears `CURRENT` **at scoring**,
and must stop — clearing belongs to `rollover`, stage 3.

### 5.2 · The four stages, and what each writes

Order per Decision 1. Every row is an existing lane subcommand; the
orchestrator adds no writer.

| # | Stage | Reads | Writes | Moves `CURRENT` |
|---|---|---|---|---|
| 1 | `goals score-phase` | phase file, `phase/<NNN>-linkage.md`, `BOARD.md` | `phase/<NNN>-<slug>.md § Retro`, `phase/snapshots/*-final.md` | **no** (changed — see I2) |
| 2 | `work end-phase-retro` | the phase file's `§ Retro` scores, `BOARD.md`, `journal/`, `evidence/` | `evidence/<YYYY-MM>/retro.md`, `evidence/<YYYY-MM>/health-check-<date>.md`, a journal `## Notes` entry | no |
| 3 | `work rollover` | `evidence/<YYYY-MM>/retro.md`, `BOARD.md` | journal `## Notes`; **clears `phase/CURRENT`** | **yes, and only here** |
| 4 | `goals plan-phase <slug>` | `OKR.md`, the retro's `§ Health metrics` | `phase/<NNN+1>-<slug>.md`, `phase/<NNN+1>-linkage.md`, `phase/CURRENT` | yes (sets it) |

**`goals` hands prose; `work` performs every write into `evidence/`.** This is
Decision 1's accepted cost turned into a rule: `phases.md` step 5 prints a
retro summary and a target path, stage 2 writes it, and `evidence/retro.md`
therefore has exactly one producer. `rollover`'s step-1 guard then has an
unambiguous thing to guard instead of "whoever got there first".

**Stage 4 writes the linkage graph in the same action as the phase file.**
That is not a convenience: `knowledge/goals/linkage-graph-before-first-add.md`
— promoted from the phase #002 retro on 2026-08-28 — records that a graph
written after the phase opens leaves every row added in between resolvable to
no KR, permanently. Phase #002 lost two days that way and closed with 10 of
100 rows attributable.

### 5.3 · Resuming a close that stopped

Per Decision 3, no new file. The resume point is a function of four facts the
stages already leave behind:

| phase `Status:` | `evidence/<YYYY-MM>/retro.md` | `phase/CURRENT` | resume at |
|---|---|---|---|
| `active` | — | the closing phase | stage 1 — nothing ran |
| `scored` | absent | the closing phase | stage 2 |
| `scored` | present | the closing phase | stage 3 |
| `scored` | present | empty / `(none)` | stage 4 |
| `scored` | present | a *newer* phase | complete |

The bottom two rows are the state phase #002 was actually left in, and the
table is why row 4 is distinguishable from row 5 at all — `CURRENT` empty means
`rollover` ran and `plan-phase` did not.

This extends `bin/perry-state --section interrupted`, which already exists and
already renders one row per pipeline someone walked away from. A half-closed
phase becomes another such row, surfaced at the next `/perry` snapshot. It is
**not** a `claims[]` entry and not a dossier.

### 5.4 · The check that keeps the retro citing rather than re-deriving

Per Decision 4, one `cross_file` row plus its implementation in `bin/perry-lint`:

```
{ "id": "retro-cites-phase-scores", "severity": "warn",
  "description": "Each per-KR status in evidence/<YYYY-MM>/retro.md must equal
                  the status for that KR id in phase/<NNN>-<slug>.md § Retro." }
```

The two spans are named on purpose — `linkage-objective-agrees` is declared,
implemented, and still missed the 002-linkage misnesting because it reads a
linkage row's `Objective` column rather than the frontmatter nesting. A check
whose surface is left implicit reads as coverage it does not have.

`warn`, not `error`: the boundary this project settled on 2026-08-21
(`phase/002-fields-are-typed.md § User Commitments`) is that errors are shape
violations and warnings are quality signals. A retro disagreeing with the
scores is a content disagreement inside a well-shaped file.

### 5.5 · Alternatives considered

Four, all rejected, and the fourth is the one that makes the case:

- **(a) Merge the sequence into `goals score-phase`.** No new command surface,
  one entry point, and scoring is where a phase visibly ends. **Rejected: it
  violates the signed contract on its first run** — the merged command would
  write `evidence/` and `journal/`, both `work`'s. This is not hypothetical.
  `goals/SKILL.md:126` claimed exactly that for a release, the correction had
  already landed one level down in `phases.md:229`, and no test could see the
  difference (TASK-216).
- **(b) Merge it into `work end-phase-retro`.** Symmetric, and `work` already
  owns the two files most of the sequence touches. **Rejected symmetrically:**
  it would write `phase/` and `OKR.md`, both `goals`'.
- **(c) Keep four commands and fix only the documentation.** The cheapest
  option, and **the one actually attempted on 2026-08-28** — two ownership
  statements corrected (`goals/SKILL.md:126`, `work/reference/subcommands.md:902`),
  the contradiction table written down, TASK-216 and TASK-217 filed.
  **Rejected because it was tried and is demonstrably not sufficient.** After
  those corrections, nothing still prevents `plan-phase` from running before
  the retro, because the defect is that every stage re-reads `phase/CURRENT`
  (I1). Prose cannot enforce an order between four commands a human invokes in
  whatever sequence they remember. It remains a **prerequisite** — the pages
  must agree before an orchestrator encodes one of them — but it is step B of
  § 6, not the design.
- **(d) A fourth lane owning phase transitions.** Would give the sequence a
  home with a single owner. **Rejected:** it adds a writer to a contract whose
  entire value is that there are three, and it would have to own files split
  across two existing lanes — the ownership question gets harder, not easier.
  `adopt` and `diagnose` already established that a cross-lane pipeline lives
  in the router and materializes through the lanes.

**Chosen: the router-level orchestrator (§ 5.1).** It is the only option that
adds no writer, and the precedent for it is already declared in the router.

### 5.6 · Blast radius

What this changes outside its own new command, so review and phase sequencing
can see it. Decisions 1 and 4 drive most of it; I2 drives the one edit nobody
would predict from the decision list.

| Surface | Change | Driven by |
|---|---|---|
| **`goals/reference/phases.md` step 7** | **Stops clearing `phase/CURRENT`.** Clearing moves to `rollover`. This is the least obvious edit in the plan and the one that makes I1 hold by construction rather than by luck | I2 |
| `goals/reference/phases.md` step 5 | The hand-off becomes the *only* path into `evidence/retro.md`: print the summary, `work` writes it | D1 |
| `goals/SKILL.md:154` | The `evidence/retro.md` row's *"Read by OKR `score-phase` after PMO writes it"* is wrong under D1 | D1 · TASK-217 |
| `work/reference/subcommands.md:401` | `end-phase-retro`'s trigger sentence (*"when `score-phase` is about to run"*) is wrong under D1; its "since the current phase started" becomes "since the **closing** phase started" | D1 · I1 |
| `work/reference/subcommands.md § rollover` | Gains "clears `phase/CURRENT`". Step 1's guard was already corrected on 2026-08-28 | I2 |
| `SKILL.md § Router subcommands` + `reference/router-subcommands.md` | A `close-phase` row and its procedure, beside `adopt` / `diagnose` / `relocate` | § 5.1 |
| `reference/snapshot.md:153` | The suggested next action stops naming four commands and names one | § 5.1 |
| `schema/state-schema.json § cross_file` | One new check row, `retro-cites-phase-scores` | D4 |
| `bin/perry-lint` | Implements that check, with a mutation proving it can go red | D4 |
| `bin/perry-state § interrupted` | Gains the half-closed-phase row and its five-state resolution table | D3 |
| `tests/test_ownership.py` | Must stay green throughout — and must first be widened, or it cannot see a regression in the lane index tables this design edits | TASK-216 |
| `README.md:163, 305` · `README_cn.md:165, 307` | Both list `end-phase-retro` in the command tables and the worked example | § 5.1 |

**Unchanged, deliberately:**

- **`claims[]` gains nothing** (D3). `.perry/hook.md` lists changes to the
  claim surface as a high-stakes operation; not needing one is worth the
  constraint.
- **`files[]` gains nothing** (D4). `evidence/` stays outside the conformance
  gate, so no project's retro becomes unwritable for failing to match a
  declared heading set.
- **The four lane subcommands stay individually invocable**, with their own
  tests, exercised individually and not only through the orchestrator.
- **`mid-phase-review`** shares the `health-check` runner and nothing else. It
  ends nothing, so it has no ordering problem and is not touched.

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| — | **Prerequisite**: widen the ownership guard, so a drifted lane index cannot pass again while this design edits several of them | **TASK-216** | Coding Agent |
| A | ✅ **Done 2026-08-28** — User Decisions 1–4 resolved (`/perry decide resolve DESIGN-012`) | (this document) | Perry maintainer |
| B | Bring the four disagreeing pages onto Decision 1's order, **and stop `goals/reference/phases.md` step 7 clearing `phase/CURRENT`** (I2) | **TASK-217** | Coding Agent |
| C | Thread the closing-phase id (I1): every stage takes it as input; no stage re-reads `phase/CURRENT` | TASK-NNN | Coding Agent |
| D | `retro-cites-phase-scores` — the `cross_file` row plus its `perry-lint` implementation, with the mutation that proves it can go red | TASK-NNN | Coding Agent |
| E | The `close-phase` router subcommand over the four unchanged stages, asking for the next slug at the end | TASK-NNN | Coding Agent |
| F | Half-closed-phase detection in `perry-state --section interrupted`, per § 5.3's table | TASK-NNN | Coding Agent |

**Sequencing.** B and C both precede E — an orchestrator that encodes an order
the pages contradict, or that threads an id the stages still re-read, ships the
bug it exists to fix. D and F are independent of E and of each other. The
prerequisite precedes everything, because B edits two lane index tables and the
guard that watches them is currently blind to that file class.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The orchestrator becomes a fourth writer — the easiest way to "fix" an awkward stage boundary is to write the file directly | `tests/test_ownership.py` as widened by TASK-216, plus a test asserting the orchestrator module opens no state file for writing | Keep every write inside a lane subcommand; the orchestrator only sequences and passes the phase id |
| The order is decided, then restated on four pages again, and drifts again | `grep -rn "retro\.md"` in goal 3, run as a test rather than by hand | Two layers, and the strong one is code: the **orchestrator** sequences the stages, so the runtime order cannot drift from a document at all. The pages then state it once and cite — the *one document, one owner, one copy* rule `reference/project-archetypes.md` already carries |
| A half-run close is invisible, so the next session re-scores a scored phase | The next `/perry` snapshot reports a phase with `Status: scored` and no `evidence/retro.md`, or a `CURRENT` pointing at a scored phase | User Decision 3; the `interrupted` gate in `perry-state` is the existing shape to extend |
| The four subcommands rot because everyone uses the orchestrator, then break when someone needs one alone | Each subcommand keeps its own tests; CI exercises them individually, not only through the orchestrator | Non-Goal: they remain individually invocable, and that is tested |
| **I2 lands by halves** — `phases.md` step 7 stops clearing `phase/CURRENT` in the docs but a stage still clears it, or the reverse. § 5.3's resume table then cannot tell stage 2 from stage 3, and the recovery path is wrong exactly when it is needed | The five rows of § 5.3 become a test fixture: construct each state and assert the resolved stage. A partially-applied I2 makes two rows collide and the fixture fails | Land B before C and E; assert in one test that `phase/CURRENT` has exactly one writer across `bin/` |
| `retro-cites-phase-scores` sits at `warn` and nobody ever clears it — a signal that never goes green, which `reference/diagnose.md` names as strictly worse than having no check | The warn count at each phase close, carried in the retro's own `§ Health metrics` alongside the store-drift coverage number | It is reported where it is read: at the close, in the retro, next to the other trend numbers — not in a lint run nobody opens. If it is still standing two closes later, that is the argument to raise it to `error`, and the design says so rather than leaving it to erode |
| Merging the sequence hides the attribution gap it sits next to — a smoother close makes a 10-of-100 KR coverage rate easier to not notice | The retro already prints the ratio; keep it printed by the orchestrator's summary | Explicit Non-Goal, plus the ratio stays a required line of the retro |

## 8. Open questions

- ~~Does `close-phase` belong in `reference/router-subcommands.md` alongside
  `adopt` / `diagnose` / `relocate`?~~ **Answered 2026-08-28** in § 5.6: yes,
  one row there and the procedure on that page, same as the other three.
- `mid-phase-review` and `end-phase-retro` share the `health-check` runner.
  If the retro moves inside an orchestrator, does `health-check` stay callable
  standalone? Expected yes; confirm at phase D.

## 9. Changes (append-only after lock)

## 10. References

- `perry/evidence/2026-08/retro.md` — the phase #002 retro that surfaced this, 2026-08-28
- `perry/evidence/2026-08/TASK-217-spec.md` — the ordering contradiction, filed as a decision rather than a patch
- `perry/evidence/2026-08/TASK-216-spec.md` — the ownership guard's two holes, mutation-proven
- `$PERRY_HOME/SKILL.md § The hand-off contract` — the signed file-ownership rule this design must not break
- `$PERRY_HOME/SKILL.md § Router subcommands` — the `adopt` / `diagnose` precedent for router-level orchestration
- `goals/reference/phases.md § score-phase` steps 5–9 · `work/reference/subcommands.md § end-phase-retro`, `§ rollover`
- `reference/snapshot.md:153` — the suggested-action line that already names all four commands
