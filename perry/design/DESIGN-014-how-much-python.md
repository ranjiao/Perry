# DESIGN-014: Perry is 90% Python and the product is the 10%

> Status: locked
> Date: 2026-09-01 · Locked: 2026-09-01
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: O2-KR1 (`perry/OKR.md` v2, Objective 2 — every piece of state is queryable and writable by deterministic code). **`OKR.md` v3 is downstream of this doc, not upstream**: the user directed on 2026-09-01 that v3's third Objective becomes "the skill is the product", and that this question is settled before v3 is written.
> Supersedes: —   · Superseded by: —
> Revisits: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`, `perry/decisions/ADR-011-the-representation-layer-comes-out.md`, `perry/design/DESIGN-011-the-okr-is-elicited-not-collected.md`, `goals/reference/setup.md`
> Sign-off: User Decisions 1-3 answered by Ran Jiao in session on 2026-09-01, so this went `draft` → `locked` without an `in_review` hold — that state exists to await exactly this sign-off (the `DESIGN-013` precedent, 2026-08-29). **All three took the recommendation**, so the option notes in § 4 stand as written rather than being restated; § 5.1 is amended for decision 1, which moves `perry-state` between categories.

## 1. Problem

**Perry is a skill. It is shipped as 97,474 lines of Python and 9,810 lines of
prose.** Measured 2026-09-01, `wc -l`:

| | lines |
|---|---|
| `bin/` | 30,043 |
| `viewer/` | 4,990 |
| `tests/` | 62,441 |
| **the skill itself** — `SKILL.md`, three lane `SKILL.md`, every `reference/`, `modes/`, `packs/` | **9,810** |

The thing a user installs and an agent reads is the last row. Everything above
it exists to serve that row, and it outweighs it 10:1.

`ADR-011` already removed 10,663 lines on the ground that one architectural
layer — markdown-as-canonical and its parsers, drift census and conformance
ledger — produced eleven of the fourteen rows that had been kicked back two or
more times in V4 review. That argument was scoped to the representation layer.
**This doc asks the question the answer implies: of what remains, what has to
be code at all?**

### The instance that prompted it

On 2026-09-01 the `goals` lane needed to append a new `OKR.md` version. There
is no write path. `perry-goals` has exactly three command functions — `link`,
`commit`, `krs` — and none of them writes a KR. `okr.jsonl` is canonical, so
the only route is to hand-append JSON records and run `perry-okr render
--write`.

That is the worst of both: **no tool determinism, and no prose either.** The
`goals` lane's authoring surface, `goals/reference/setup.md § init`, is a
ten-field checklist containing zero `AskUserQuestion` calls — measured by
`DESIGN-011`, which was locked 2026-08-28 and whose first sentence is *"Perry
has a quality check that grades a draft. It has nothing that produces one."*

`DESIGN-011`'s architecture is a question bank in `goals/reference/`. **It is
pure prose and needs no Python at all.** Its implementation row, `TASK-177`, is
`not_started` and sits in `phase/003-linkage.md`'s `unlinked[]` — linked to no
KR. Across five Objectives and nineteen KRs, `OKR.md` v2 contains **no KR about
the quality of the skill's prose**. What is not in the OKR does not get worked.

### Why the ratio is not self-correcting

Every defect found in Python produces a row, a V4 round and a test. Every
defect in prose produces nothing — there is no runner for it. So the
measurement pressure runs one way, and the 10:1 is what a year of that looks
like. `perry-lint`'s own live signal-to-noise on this repository is 0 errors to
4 warnings, and all four warnings are files the user placed deliberately.

## 2. Goals

1. **Every tool in `bin/` and `viewer/` is placed in exactly one of three
   categories** — *determinism-bearing*, *representation layer* (already
   condemned by `ADR-011`), or *code standing in for prose that was never
   written* — with the reason stated per tool, not per category.
2. **Every tool that stays can state what it computes that an agent reading the
   stores could get wrong.** A tool that cannot is in category three.
3. **The split inside `bin/perry-task` (7,522) and `bin/perry-lint` (4,483) is
   measured by call site, not by grep.** Together they are 40% of `bin/` and
   neither is homogeneous; phase 002's most expensive recurring defect was
   locating an implementation by grepping its name, and this doc must not repeat
   it.
4. **The `goals` lane gets one authoring path**, whichever of the two it is, so
   that adding a KR is neither a hand-edited JSONL file nor a hand-edited
   markdown table.
5. **`OKR.md` v3 can be written against a settled answer**, with a third
   Objective about the skill that has at least one KR a prose change can move.

## 3. Non-Goals

- **Not a line-count target.** A number as the goal makes deletion the
  objective and invites cutting a check because it is long. The goals above are
  per-tool justifications; the line count is a symptom being explained, not a
  KR.
- **Not re-litigating `ADR-011`.** Tiers B and C are decided in direction and
  keep their preconditions. This doc does not re-open them, and does not wait
  for them either.
- **Not deleting the determinism core.** Id minting that never reuses,
  call-time timestamps, the multi-file transaction with crash recovery, and the
  refusals are the reason Perry's state is trustworthy. They are the answer to
  the question, not a candidate for it.
- **Not weakening "never compute a number by reading files and eyeballing it".**
  That Operating Principle is what makes an agent's numbers checkable. Anything
  proposed here that would let an agent assert a count it did not compute is out
  of scope by construction.
- **Not rewriting the prose in this pass.** Naming what should be prose is this
  doc; writing it is `TASK-177` and its successors.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | How an agent learns project state | keep `perry-state` as the one payload (2,747 lines) / **thin it to a query over the stores now that they are JSONL** / let agents read the stores directly and delete it | **thin it to a query over the stores** | 2026-09-01 |
| 2 | The `goals` authoring path | **build the missing KR writer, closing `KR-O2.1`** [[old-form]] / stop making KRs a store fact and let the elicitation write the markdown, reopening `ADR-007` for this file | **build the KR writer** | 2026-09-01 |
| 3 | `bin/perry-diagnose` (2,691 lines), which audits any folder | **keep — it is independent of adoption and works on any project** / fold its findings into `perry-lint` / drop it with adoption | **keep** | 2026-09-01 |

**On decision 1.** This is the largest non-representation item and the least
obvious. `perry-state` exists because of the Operating Principle above, and it
was right when `BOARD.md` was canonical and counting meant parsing a table.
With six JSONL stores the counting is a `json.loads` loop, and the question is
whether the payload's value is now the *shape* it publishes — which is a
contract three lanes and a front-end read — rather than the counting. If it is
the shape, it stays and shrinks; if it is the counting, it is category three.

**On decision 2.** These are opposite directions and both are defensible.
`O2-KR1` has been open since 2026-08-17 with `goals` as the named gap, and
`DESIGN-013 § 5.1` says a fact with a schema lives in the store — which a KR
has. Against that: the elicitation bank is where the KR's *content* is decided,
and a writer that takes ten fields from an agent that just ran a good interview
may be a form re-appearing one layer down.

**On decision 3.** `perry-diagnose` is not adoption and does not depend on the
deleted migrator. But `USER-910` answered that Perry is never pointed at a
foreign project, and `diagnose`'s whole subject is a folder that is not yet
Perry-shaped.

## 5. Architecture

### 5.1 The three categories

**A — determinism-bearing.** The tool computes something an agent would get
wrong, or performs a write an agent cannot make safely.

| Tool | lines | what only code can do |
|---|---|---|
| `bin/perry-task` (write core) | part of 7,522 | id minting that never reuses (reads the full store plus every `purge`), call-time timestamps, the store+journal transaction with a durable recovery marker, the refusals |
| `bin/perry-decide` | 590 | ADR id minting, status enum validated against the schema, bidirectional supersede |
| `bin/perry-goals link` | part of 3,380 | refuses anything that does not resolve to exactly one KR, and names the candidates |
| `bin/lib`, `bin/perry_store.py` | 1,035 + 1,537 | one cell model under every tool; a second one is the defect `ADR-007` exists to remove |
| `bin/perry-lint` (schema pass) | part of 4,483 | validating a file against `schema/state-schema.json` |
| `bin/perry-state` | part of 2,747 | **decision 1, 2026-09-01**: the payload SHAPE stays — three lanes and a front-end read it as a contract — and the counting is a `json.loads` loop over six JSONL stores. It moves here from category C, to be thinned rather than deleted, and what it publishes does not change |
| `bin/perry-diagnose` | 2,691 | **decision 3, 2026-09-01**: kept. It is not adoption, it does not depend on the deleted migrator, and auditing how a folder is structured for agent work is product surface under "the skill is the product" rather than packaging |

**B — representation layer.** Condemned by `ADR-011`, preconditions unchanged.

| Tool | lines |
|---|---|
| `viewer/parsers.py` | 4,603 |
| `bin/perry-tasks` | 1,500 |
| `bin/perry_md_store.py` | 1,155 |
| the drift census inside `perry-lint` | ~918 |
| their tests (`test_md_store`, `test_store_drift`, `test_one_header_rule`, `test_header_index_is_the_only_fold`, `test_store_is_canonical`, `test_last_updated_header`, `test_stranded_rows`) | 4,601 |

**C — code standing in for prose.** The candidates, each a User Decision or an
open question above.

| Tool | lines | the prose it stands in for |
|---|---|---|
| the `goals` authoring gap | 0 lines today | **decision 2, 2026-09-01**: the gap is closed by building the KR writer, not by removing the store. `DESIGN-011`'s elicitation decides a KR's CONTENT and the writer puts it in `okr.jsonl` — two layers, each doing one thing. This is the only row in this category that is answered by ADDING code, and it is answered that way because the missing 200 lines are what force a hand-edited JSONL file today |
| `bin/perry-explain` (792), `perry-knowledge` (659), `perry-state-cost` (576), `perry-context-budget` (444), `perry-dispatch-limit` (404) | 2,875 | open question 1 — still the only unanswered category-C population |

**Decisions 1 and 3 emptied this category of its two largest entries**, and that
is the doc's most surprising result. The question "how much of this has to be
code?" was asked expecting deletion, and on the three items put to the user it
returned: thin one, keep one, and BUILD the missing one. The 10:1 ratio is not
mostly made of tools that should not exist — it is made of one condemned layer
(category B) and one authoring surface that was never written at all.

### 5.2 What the answer looks like when it is right

A reader opening `bin/` finds tools that each answer "what would an agent get
wrong here?" in one sentence, and a reader opening `goals/reference/` finds the
questions that produce a good OKR. Today the second half is a ten-field
checklist and the first half contains 4,603 lines of parser for a file the
project has decided to delete.

## 6. Implementation plan

Ordered. Each step's precondition is checkable, and none of them is "delete N
lines".

1. **Measure the split inside `perry-task` and `perry-lint` by call site.**
   40% of `bin/` is two files and neither is one thing. Until this exists, § 5.1
   says "part of 7,522" and that is an admission, not a measurement. Proposed
   row: one, V4, evidence citing the call sites per category.
2. **Resolve the three User Decisions** (`/perry decide resolve DESIGN-014`).
3. **Write `OKR.md` v3** with the third Objective the user directed on
   2026-09-01, and at least one KR that a prose change moves.
4. **`TASK-177` — the elicitation question bank** (`DESIGN-011`, locked
   2026-08-28, never started), and link it to that KR at `add` time per
   `P003-O3-KR2`.
5. **Whatever decisions 1-3 land**, each as its own row, each with the "shown
   able to go red" rule.

`ADR-011` Tier B runs on its own precondition (phase 003 Objective 2) and does
not wait for any of this.

## 7. Risks & mitigations

- **Deleting a check whose determinism was load-bearing.** Detected by the phase
  Operating Rule that a gate is not green until it has been shown able to go
  red: removing a check must turn a named test red, and if nothing goes red the
  check was already dead. Mitigated further by category A being out of scope by
  construction (§ 3).
- **Line count becomes the goal.** This is the failure mode of every deletion
  program and `ADR-011` is already one. Mitigated by § 3's first Non-Goal and by
  KRs phrased as per-tool justifications; detected at retro by asking whether
  any row's evidence was a line count and nothing else.
- **The prose has no test runner, so its quality regresses silently.** Real and
  not fully mitigable. `DESIGN-011` goal 3 is the closest thing to a test — an
  OKR produced through the elicitation passes `reference/input-quality.md § 1`
  with zero issues surfaced — and `tests/test_procedures_call_the_tool.py`
  already guards one narrow prose property mechanically.
- **This doc becomes a rewrite.** Mitigated by § 3: no rewrite, and the
  implementation plan's first step is a measurement rather than a change.

## 8. Open questions

1. **The five auxiliary tools** (`perry-explain`, `perry-knowledge`,
   `perry-state-cost`, `perry-context-budget`, `perry-dispatch-limit`, 2,875
   lines together). Each is small and each was built for a real complaint. They
   are listed in category C because none of them has been asked the § 2 goal-2
   question, not because an answer is expected to be no.
2. **The test-to-product ratio (62,441 : 35,033) after the representation layer
   goes.** `ADR-011` removes tests faster than product code, which improves the
   ratio without anyone deciding what it should be.
3. **Whether `tests/` should be measured the same way as `bin/`.** A test for a
   deleted tool goes with it; a test for a prose rule mostly does not exist.

## 9. Changes     <!-- append-only after lock -->

- **2026-09-02 — `§ 1`'s 10:1 headline counts the test suite as product. The
  arithmetic is right; the denominator is not. `§ 5.1`'s conclusion survives on
  the honest number.** The opening sentence — *"It is shipped as 97,474 lines of
  Python and 9,810 lines of prose"* — sums `bin/` + `viewer/` + `tests/`, and
  the table below it says so plainly. But a test suite is not shipped and is not
  the thing "the product is the 10%" is about, and **this document already
  argues against its own framing twice**: `§ 3`'s first Non-Goal (*"Not a
  line-count target"*) and `§ 8` open question 2, which quietly uses the right
  denominator (`62,441 : 35,033`, i.e. `tests/` against `bin/` + `viewer/`).
  `§ 8` question 3 then asks whether `tests/` should be measured the same way as
  `bin/` at all — the question `§ 1` answered by assumption.

  **Re-measured 2026-09-02** on `coding/task-247-config-predicate`.
  *Instrument, stated because the number depends on it*: every path
  `git ls-tree -r` reports under `bin/`, `viewer/` and `tests/` that is Python
  source — `*.py`, plus extensionless files whose first line is a `python`
  shebang — with `__pycache__` excluded, counted by newline. Not a working-tree
  `find`.

  | | lines | files |
  |---|---|---|
  | `bin/` | 29,258 | 16 |
  | `viewer/` | 4,993 | 2 |
  | `tests/` | 65,360 | 124 |
  | **shipped product** — `bin/` + `viewer/` | **34,251** | 18 |
  | **prose** — `§ 1`'s own definition, re-walked | **9,887** | 53 |

  On `main` at `d49964e` the same instrument returns `bin/` 29,233 ·
  `viewer/` 4,990 · `tests/` 65,229 — 99,452 total, 34,223 product; **prose is
  9,887 / 53 files on both**, none of `§ 1`'s prose paths having changed today,
  so both ratios below round the same either way. Both trees are given because
  the code figures differ, and a number that reproduces on only one checkout is
  the defect this entry is about.

  A note on `§ 1`'s own figures, since this entry corrects the framing and not
  the arithmetic: `viewer/ 4,990` reproduces *exactly* under this instrument on
  `main`, which is evidence `§ 1` counted Python source rather than sweeping the
  directory. `bin/ 30,043` and `tests/ 62,441` are one day older and are not
  re-derivable from this checkout; they are not disputed here.

  - **With `tests/`, as `§ 1` has it: 99,611 : 9,887 — still 10:1.** The
    headline is not saved by the test suite and does not need it.
  - **Product against prose: 34,251 : 9,887 — 3.5:1.** This is the ratio
    `§ 5.1` is actually about, and the one `§ 8` question 2 was already using.

  Two instrument warnings, because this document's numbers get re-cited:

  1. **`find bin -type f -exec wc -l` is the wrong instrument for this claim,
     because it walks the filesystem and git does not.** It counts
     `__pycache__/*.pyc` — **untracked machine-local build artefacts**, present
     on a developer's disk and in no commit — and it also picks up
     `bin/README.md` (296) and 842 lines of `bash`. Compiled artefacts and
     shell are not "lines of Python".

     The reproducible figure comes from git rather than from a disk: at
     `d3f9f4b`, every tracked file under `bin/` totals **30,396** lines, of
     which **29,258** are Python. At `d49964e` the same instrument gives
     30,371. A `find` sweep on any particular machine will differ by however
     much bytecode happens to be sitting there, which is why no such number is
     quoted here.

     **Corrected 2026-09-02 after a V4 FAIL.** This warning first said the
     `.pyc` were *tracked*, and cited 5,994 and 36,390 on that basis. They are
     not tracked: `git ls-files` returns none, no `.pyc` appears in any commit
     in the repository's whole history, and `.gitignore` lines 11-12 cover
     them. The reviewer's proof was that the false claim sat inside a warning
     written *"because this document's numbers get re-cited"* — so the wrong
     part was the part written to be reused, in a locked append-only file.
  2. **Four `bin/` tools are `bash`, not Python** — `perry-codex-preflight`
     (150), `perry-detect-host` (101), `perry-dispatch-limit` (404),
     `perry-update-check` (187). `§ 5.1` places `perry-dispatch-limit` in
     category C with a line count, so goal 1's scope is *tools*, not Python
     files. The categories and the ratio are counting two different populations,
     and that is fine as long as nobody adds them together.

  `§ 1`'s table is left exactly as written.

- **2026-09-02 — goal 1 is not met by this document. Six tools in `bin/` and
  `viewer/` are placed in no category at all.** Goal 1 requires that *"Every
  tool in `bin/` and `viewer/` is placed in exactly one of three categories …
  with the reason stated per tool."* Re-derived 2026-09-02 by taking every tool
  in `bin/` and `viewer/` (excluding `bin/README.md` and `__pycache__`) and
  checking it against all three `§ 5.1` tables:

  | unplaced tool | lines | appears in § 5.1? |
  |---|---|---|
  | `bin/perry-okr` | 44 | no — named once in `§ 1` prose (*"run `perry-okr render --write`"*), never categorized |
  | `bin/perry-config` | 46 | no — absent from the document |
  | `bin/perry-codex-preflight` | 150 | no — absent from the document |
  | `bin/perry-detect-host` | 101 | no — absent from the document |
  | `bin/perry-update-check` | 187 | no — absent from the document |
  | `viewer/tables.py` | 387 | no — `§ 5.1` names `viewer/parsers.py` only |

  **Six tools, 915 lines.** Small, which is why they were missed, and none of
  them is obviously category A: an unplaced tool is one nobody has asked goal 2's
  question of, and goal 2 says a tool that cannot answer it *is* category three.

  Seventh, and different in kind: **`bin/perry-goals` (3,380) is placed only by
  the fragment `perry-goals link`.** `§ 5.1` writes it *"part of 3,380"* — the
  same admission it makes for `perry-task` and `perry-lint` — but `§ 6` step 1,
  which is the commitment to *retire* those admissions by measuring the split at
  the call site, names **`perry-task` and `perry-lint` only**. So `perry-goals`
  carries the admission with nothing scheduled to discharge it, and it is the
  third-largest file in `bin/`. `§ 6` step 1's *"40% of `bin/` is two files"*
  reproduces on both trees: 7,522 + 4,493 = 12,015 of 29,258 on
  `coding/task-247-config-predicate` (41%), and 7,522 + 4,483 = 12,005 of
  29,233 on `main` (41%). The six line counts in the table above are identical
  on both.

  Goal 1's text stays as written; it is a goal this document did not meet, not a
  goal that was wrong.

- **2026-09-02 — decision 3's stated objection is still unanswered, and `§ 5.1`
  does not answer it.** `§ 4`'s note on decision 3 raises it sharply and against
  the decision it then takes:

  > `perry-diagnose` is not adoption and does not depend on the deleted
  > migrator. But `USER-910` answered that Perry is never pointed at a foreign
  > project, and `diagnose`'s whole subject is a folder that is not yet
  > Perry-shaped.

  `§ 5.1`'s category-A justification replies: *"auditing how a folder is
  structured for agent work is product surface under 'the skill is the product'
  rather than packaging."* **That answers a different question.** The objection
  is not what *category* `diagnose` belongs to — it is whether the subject it
  operates on still exists. A tool can be product surface and still have no
  folder to point at.

  `§ 2` goal 2 requires every tool that stays to *"state what it computes that
  an agent reading the stores could get wrong"*, and for `diagnose` the answer
  depends on the premise the objection puts in doubt. **Marked unanswered
  rather than answered here**, deliberately: the answer is a user decision and
  this entry is not the place it gets made.

  One thing that can be settled by measurement, and is: **`USER-910` does not
  say what the note attributes to it.** Its recorded answer, in
  `perry/asks.jsonl`, is *"A — delete migration too. `perry-migrate`,
  `perry_schema.py` and `test_migrate.py` are out; `TASK-097` drops with
  them."* That deletes the migrator. *"Perry is never pointed at a foreign
  project"* is a wider claim, and the ask on file does not carry it — see
  `DESIGN-001 § 9`, 2026-09-02, which measures that both `/perry adopt` and
  `/perry diagnose` still have callers. Decision 3 is unaffected as a decision;
  what is unresolved is the ground the objection stands on.

- **2026-09-11 — every line count in `§ 5.1` is stale, and `TASK-348`'s census
  supersedes them. The conclusions do not move; two of them get sharper.**
  Appended rather than edited in place, because this document is locked.

  `§ 5.1`'s figures were taken at lock. Re-measured at `583f024f`:

  | file | `§ 5.1` says | measured |
  |---|---|---|
  | `viewer/parsers.py` | 4,603 | 4,902 |
  | `bin/perry-tasks` | 1,500 | 1,928 |
  | `bin/perry_md_store.py` | 1,155 | 1,675 |
  | `bin/perry-task` | 7,522 | 8,540 |
  | `bin/perry-lint` | 4,483 | 5,905 |
  | `bin/perry-state` | 2,747 | 2,657 |
  | `bin/perry-diagnose` | 2,691 | 2,818 |

  **Read `perry/evidence/2026-09/TASK-348-result.md` for the current numbers,
  not this section.** It measures the 22 files `TASK-263` did not, by call
  site, 27,132 lines at that commit.

  Two of its findings bear directly on `§ 5.1`:

  1. **`§ 5.1` category B's "condemned in full" is false, by about five times.**
     Of the 8,505 lines in `viewer/parsers.py`, `bin/perry-tasks` and
     `bin/perry_md_store.py`, **1,775 are OBSOLETE REPRESENTATION — 20.9%**. In
     `parsers.py` that is not even the largest category; TYPED is, at 870. And
     those files hold the **only** implementation of the `.perry/config.jsonl`
     reader and validator and of root resolution, which every tool runs before
     it can do anything, plus the YAML parser behind `perry-lint`'s spec
     frontmatter, the ADR reader, and the linkage store reader. `ADR-011`
     Tier B can delete 1,775 lines inside these files; **it cannot delete the
     files.**
  2. **`TASK-263`'s headline was a two-file result, not a project-wide one.**
     Its `OBSOLETE : AGENT-OWNED` ratio holds and strengthens — 4.19:1 across
     these 22 files against 3.05:1 there — but *"OBSOLETE is the largest
     category"* does not survive: project-wide, TYPED is 6,440 against
     OBSOLETE's 3,546. `perry-task` and `perry-lint` are the two files whose
     job **is** the board, so measuring only them was close to selecting on the
     outcome.

  `bin/perry-dispatch-limit`, which `§ 5.1` files under category C, measures
  223 of 297 lines TYPED with **zero** OBSOLETE.

## 10. References

- `perry/decisions/ADR-011-the-representation-layer-comes-out.md` — the tier plan this doc extends past
- `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md` — "Python owns typed fields; agents own prose"
- `perry/design/DESIGN-011-the-okr-is-elicited-not-collected.md` — the prose half, locked and unstarted
- `perry/design/DESIGN-013-one-place-per-fact.md` § 5.1 — a fact with a schema lives in the store
- `perry/evidence/2026-08/2026-08-31-representation-layer-delete-list.md` — the measurement `ADR-011` rests on
- `perry/phase/003-storage-code.md` § Changes / Pivots, 2026-09-01
