# ADR-017 step 2 — the rename, in one commit

<!-- [[old-form]] · This document is ABOUT the pre-ADR-017 overall-KR form.
     Every `KR-O<n>.<m>` below is the artifact under discussion, not a live
     cross-reference. Per `reference/style.md`, it must not be migrated.
     Document-level marker, following the precedent set by
     `ADR-017-corpus-result.md`; see § 8 for why that is weaker than a
     same-line marker and what it costs. -->

> Task: ADR-017 step 2 — the atomic rename of the overall KR ids
> Date: 2026-09-07
> Base SHA: **`e928ed4`** ("Move TASK-280 to blocked: its round stopped with two blockers, and the board said in_progress")
> Branch: `worktree-agent-abd5fcbedbbd30f6a`
> Result: **136 occurrences renamed in one commit. 20 ids move; 18 quotations survive, every one marked.**

## 0. Base verification

The worktree was handed **`d49964e`**, **557 commits behind `main`** with **zero
commits of its own** and a clean tree — the `TASK-381` defect, now on its tenth
instance. `main` was exactly `e928ed4`, so it was reset:

    $ git reset --hard main
    $ git log --oneline -1
    e928ed4 Move TASK-280 to blocked: …
    $ git merge-base --is-ancestor e928ed4 HEAD && echo OK
    OK

Step 1 confirmed present at that base, both halves:

    $ python3 -c "…; print(bool(P._RE_KR_ID.match('O3-KR1')))"
    True
    $ grep -n id_pattern schema/state-schema.json
    1303:  "id_pattern": "^(?:KR-O\\d+\\.\\d+|O\\d+-KR\\d+)$"
    1412:  "id_pattern": "^P\\d{3}-O\\d+-KR\\d+$",

### Baseline, verified rather than trusted

Full suite in this worktree at `e928ed4`, `PERRY_PROJECT`/`PERRY_HOME` unset:

    120 modules · 3448 tests · 111.3s · 8 workers
    ✗ 3 of 120 MODULE(S) red
    ✗ 4 of 3448 TEST(S) failed

**The dispatch's arithmetic was right: 3 modules, 4 tests**, and they are the
three named — `test_contract_key_parity` (2, `TASK-335`), `test_diagnose` (1,
`TASK-380`), `test_linkage_import` (1, `TASK-383`). Worth recording that round
2 measured a **fourth** red module at `1c26ec9`, `test_spec_scannability`; it is
**green at `e928ed4`**, so that one closed between the two bases and the count
returning to 3 is real rather than a mis-count.

`perry-lint --root .` — **0 errors, 29 warnings**.
`perry-diagnose` finding ids — `{CON-02, CON-03, DOC-03, DOC-05, LOAD-03, NS-01}`,
`user_load.dangling` `[]`, `untitled` `[]`.

**The linkage store is NOT at 0 drifted at baseline.** It reports
`123 record(s), 1 row(s) drifted`, and the drifting row is
`P003-O3-KR2 differs between the store and phase/003-linkage.md` — its
`tasks[]`, the `TASK-383` defect whose test is one of the four baseline reds.
The dispatch asked for "0 drifted" on both stores; that was not reachable for
the linkage store before this commit and is not reachable after it. What this
commit can and does show is that the count did not move and the drifting row is
the same one. See § 5.

## 1. Before and after — the id list

`perry-goals list --root . --level overall --json`, 19 ids both sides (the
current `v3` block; the 20th unique id, `O3-KR4`, lives only in `v2`):

| before | after |
|---|---|
| `KR-O1.1 KR-O1.2 KR-O1.3` | `O1-KR1 O1-KR2 O1-KR3` |
| `KR-O2.1 KR-O2.2 KR-O2.3 KR-O2.4 KR-O2.5` | `O2-KR1 O2-KR2 O2-KR3 O2-KR4 O2-KR5` |
| `KR-O3.1 KR-O3.2 KR-O3.3` | `O3-KR1 O3-KR2 O3-KR3` |
| `KR-O4.1 KR-O4.2 KR-O4.3 KR-O4.4` | `O4-KR1 O4-KR2 O4-KR3 O4-KR4` |
| `KR-O5.1 KR-O5.2 KR-O5.3 KR-O5.4` | `O5-KR1 O5-KR2 O5-KR3 O5-KR4` |

`perry-goals list` (all levels) returns **25 ids both sides** — the 19 above
plus `P003-O1-KR1`, `P003-O1-KR2`, `P003-O1-KR3`, `P003-O2-KR1`,
`P003-O2-KR3`, `P003-O3-KR2`, **byte-identical**. The phase form does not move,
which is the property the grammar `[P<NNN>-]O<n>-KR<m>` exists to give.

The store's full id set is **exactly 20**, matching `ADR-017`'s Consequences:

    O1-KR1 O1-KR2 O1-KR3
    O2-KR1 O2-KR2 O2-KR3 O2-KR4 O2-KR5
    O3-KR1 O3-KR2 O3-KR3 O3-KR4
    O4-KR1 O4-KR2 O4-KR3 O4-KR4
    O5-KR1 O5-KR2 O5-KR3 O5-KR4

## 2. Occurrence counts, reconciled to the dispatch's table

Measured over all 917 tracked files at `e928ed4`: **557 occurrences** of
`KR-O<n>.<m>` repo-wide. After: **421**. **136 renamed.**

| where | dispatch said | measured at `e928ed4` | renamed | left |
|---|---|---|---|---|
| `perry/OKR.md` | 41 (20 unique ids) | **41**, 20 unique | 41 | 0 |
| `perry/okr.jsonl` | 40 | **40** | 40 | 0 |
| `perry/phase/*-linkage.md` | 39 | **16** — see below | 16 | 0 |
| `perry/linkage.jsonl` | 6 | **6** | 6 | 0 |
| `perry/design/` + `perry/decisions/` | 51, only the 30 live | **51** | **33** | 18 |
| | | | **136** | |

**The dispatch's `39` for `perry/phase/*-linkage.md` is the count for the whole
`perry/phase/` tree, not for that glob.** The glob matches two files —
`001-linkage.md` (10) and `003-linkage.md` (6) = **16**; `002-linkage.md`
carries none. The other 23 are `phase/snapshots/okr-v1.md` (15),
`phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md` (7) and
`phase/001-work-modes-live.md` (1). All 23 are **left**, and deliberately:
the two snapshots are frozen records of a past state, and the third is prose in
a closed phase's body — `ADR-017` Consequences: *"A stale reference in an old
row is history."*

**Two of `001-linkage.md`'s 16 are body prose, not `linked:` fields**, and
renaming them goes past `ADR-017`'s literal wording (*"every `linked:` field"*).
They read *"**v2 KR-O3.3** — content present in a project's files…"* and
*"**v2 KR-O2.2** — the log becomes canonical"*. Both are version-qualified
pointers into `OKR.md` v2, and this commit renames the `v2` block — so leaving
them would have left two references pointing at ids that exist nowhere. They
now read `v2 O3-KR3` and `v2 O2-KR2`, and both resolve.

**Renaming the `v2` block at all is the other judgement worth naming.**
`OKR.md` says versions are append-only, so `v2` looks like history. It is not
treated as history by anything that reads it: the OKR store projects **all 51
records including `v2`**, `perry-lint`'s drift comparison covers them, and
`ADR-017`'s own count of *"20 ids in `perry/OKR.md`"* is only reachable as the
**union of `v2` and `v3`** — `v3` alone is 19. § 9 records the test that
independently confirms it.

`perry/okr.jsonl`'s 40 against `perry/OKR.md`'s 41 is not a discrepancy: 38 are
the KR ids in both, the document carries one extra in `v3`'s rationale prose
(`KR-O2.5`), and both carry the two in the versioning-log row for `v3`.

### The 33 in `design/` + `decisions/`, against the corpus round's 30

The corpus round classified **30 live / 14 quotation / 6 grammar** at
`c545152`. Re-measured here, **all 50 line numbers were still exact** — the
rename script asserted the expected occurrence count on every targeted line and
every assertion passed, which is itself the check that the classification is
still addressed at the right text.

I renamed **33**, not 30. The 3 extra are **not** a reclassification; each is a
case the corpus round itself flagged as *conditional on the data half*, and
this commit is the data half:

1. **`ADR-003:39`** (2 occurrences, rows 43–44, classed `H`). The corpus round's
   own "why" reads: *"**coupled** — a present-tense claim about `DESIGN-006`'s
   literal header text (rows 4–5). True only if it and the header change
   together, or neither does."* Rows 4–5 are `DESIGN-006`'s header, classed
   `L`, renamed here. The sentence says *"`DESIGN-006`'s header now links
   `O5 / …`"*; leaving it would ship a statement this same commit falsifies.
2. **`DESIGN-015:154`** (1 occurrence, row 39, classed `H`). Its stated reason
   is *"depicts a real record — `perry/linkage.jsonl` carries
   `"linked": "KR-O2.1"` on **3** rows today, so the block is accurate and
   rewriting it would make the doc wrong about the store."* This commit renames
   those 3 rows. The justification inverts: **leaving** it is now what makes
   the doc wrong about the store.

I am **not** overruling any classification silently, and I have left the four
`?` rows (37, 40, 41, 42) exactly as classified, toward leaving — including
`ADR-003:35`–`36`, which sit two lines from the coupled `:39` and stay in the
old form because their claim is about what `OKR.md` v2 *did on a date*, not
about another file's current text.

### Where the other 421 are, and why this commit does not touch them

The dispatch's verification item 1 — *"`grep -rn "KR-O[0-9]*\.[0-9]*"` over the
whole repo returns only the 14 quotations, the 6 grammar mentions, and whatever
`tests/` still holds"* — **is not achievable, and was not achievable before I
started.** Nobody had counted the corpus outside `design/` and `decisions/`;
the corpus round said so explicitly in its own § 6. The census:

| area | after | disposition |
|---|---|---|
| `perry/evidence/` | 224 | history; 107 of them are the corpus round's own document |
| `tests/` | 80 | **step 3 owns these; untouched** |
| `perry/phase/snapshots/` | 22 | frozen snapshots of a past state |
| `perry/journal/` | 19 | dated history |
| `.perry/events.jsonl` + other | 15 | append-only event log |
| `perry/design/` | 12 | the marked survivors |
| `perry/handoff/` | 11 | dated history |
| `goals/` | 8 | **authoring templates — a real open dependency, § 7** |
| `perry/BOARD.md`, `tasks.jsonl`, `asks.jsonl` | 8 | `ADR-017`: *"a stale reference in an old row is history"* |
| `bin/` / `viewer/` | 11 | code comments and docstring examples |
| `perry/decisions/` | 6 | the marked survivors |
| `schema/` / `reference/` | 4 | prose invariant lists and i18n examples |
| `perry/phase/001-work-modes-live.md` | 1 | prose in a closed phase's body |
| **total** | **421** | |

That 421 is measured **without this file**. This document itself carries 43
more (it is about the old form), taking the committed tree to **463**; the
`perry/evidence/` row becomes 267. Both numbers are given because the first is
the one that describes the rename and the second is the one a reader will
reproduce. `perry-lint --root .` was re-run with this file in place and is
unchanged — 0 errors, 29 warnings, OKR store 0 drifted, linkage store 1
drifted — so no measurement here rests on the file being absent.

The achievable form of that check, and the one that holds: **within
`perry/design/` and `perry/decisions/`, every surviving occurrence is a
deliberate one and 17 of the 18 carry an inline `[[old-form]]`** (the
eighteenth is inside a fenced block, § 4).

## 3. The 33 renamed, by line

Line numbers as measured at `e928ed4`. Only these lines were touched in these
files; every other line is byte-identical, which is what protects the
quotations.

| file | lines | n |
|---|---|---|
| `DESIGN-005-state-and-contracts.md` | 6 | 3 |
| `DESIGN-006-roles-and-knowledge.md` | 6, 363, 373, 382, 390, 402, 410 | 8 |
| `DESIGN-008-track-axes.md` | 6, 448 | 6 |
| `DESIGN-009-the-objective-is-a-record.md` | 6 | 2 |
| `DESIGN-010-autopilot-writes-its-own-specs.md` | 6 | 2 |
| `DESIGN-011-the-okr-is-elicited-not-collected.md` | 6 | 1 |
| `DESIGN-012-close-phase.md` | 6 | 1 |
| `DESIGN-013-one-place-per-fact.md` | 6 | 1 |
| `DESIGN-014-how-much-python.md` | 6, 119 | 2 |
| `DESIGN-015-linkage-is-a-store.md` | 154 | 1 |
| `ADR-003-okr-v2-runtime-objective.md` | 39, 56 | 3 |
| `ADR-011-the-representation-layer-comes-out.md` | 87, 88 | 3 |

### The headers — nine documents, not seven

`ADR-017`'s `## Changes` settles the field as **metadata** and says *"the seven
headers are edited directly"*, correcting Context's "six". Both counts are
about `DESIGN-008`–`DESIGN-014`. The corpus round measured the true corpus-wide
figure and it is **nine documents / 16 header occurrences** — `DESIGN-005` and
`DESIGN-006` carry one too, and both were classed `L`. All 16 are renamed.
Read directly, because `TASK-390` establishes `Linked OKR` has no consumer and
therefore dangles silently:

| document | `Linked OKR:` after |
|---|---|
| `DESIGN-005` | `O2-KR1, O2-KR2, O4-KR2 (perry/OKR.md v2)` |
| `DESIGN-006` | `O5 / O5-KR1–O5-KR4` |
| `DESIGN-008` | `O1-KR1, O1-KR2, O1-KR3` |
| `DESIGN-009` | `O4-KR1, O4-KR2` |
| `DESIGN-010` | `O5-KR3, O5-KR4` |
| `DESIGN-011` | `O1-KR2` |
| `DESIGN-012` | `O2-KR3` |
| `DESIGN-013` | `O2-KR1` |
| `DESIGN-014` | `O2-KR1` |

Every header cites `perry/OKR.md` **v2**, and every id above is in the renamed
`v2` block. Checked mechanically as well as by eye: **144** new-form overall
ids across `perry/` outside `evidence/`, `journal/` and `handoff/` were
resolved against `okr.jsonl`'s id set — **0 unresolvable**.

## 4. The 18 quotations left, and their markers

`reference/style.md`'s rule became applicable in this commit and not before:
the old form is obsolete as of this commit, which is exactly why the corpus
round could not apply the markers and handed them here.

| file:line (at `e928ed4`) | id(s) | class | marker |
|---|---|---|---|
| `DESIGN-006:467` | `KR-O5.1`, `KR-O5.4` | H | inline |
| `DESIGN-007:102` | `KR-O1.1` | H — **the control** | inline |
| `DESIGN-007:258` | `KR-O1.1` | G | inline |
| `DESIGN-009:35` | `KR-O1.1` | H | **introducing sentence** (fenced ```json) |
| `DESIGN-009:49` | `KR-O1.1` | G | inline |
| `DESIGN-009:51` | `KR-O1.1` | G | inline |
| `DESIGN-009:127` | `KR-O1.1` | G | inline |
| `DESIGN-009:130` | `KR-O1.1` | G | inline |
| `DESIGN-009:160` | `KR-O1.1` | H | inline |
| `DESIGN-009:216` | `KR-O1.1` | H | inline |
| `DESIGN-014:107` | `KR-O2.1` | H `?` | inline |
| `ADR-003:35` | `KR-O5.1`, `KR-O5.4` | H `?` | inline |
| `ADR-003:36` | `KR-O5.4` | H `?` | inline |
| `ADR-017:19` | `KR-O1.1` | H | inline, **outside** the closing quote |
| `ADR-017:28` | `KR-O2.1` | G | inline |
| `ADR-017:108` | `KR-O2.1` | G | inline, **outside** the closing quote |

**`ADR-017:108` is the 51st occurrence** — it did not exist at the corpus
round's base. It is inside the `## Changes` entry, quoting Context's own
grammar mention, so it is the same class as row 50 and is left and marked.

**The control held.** `DESIGN-007:102` — the sentence saying
`phase/001-work-modes-live.md` *"holds"* a table row containing `KR-O1.1`,
where that file contains zero occurrences of it — is unchanged apart from the
appended marker. The naive sweep would have rewritten it, fabricating a row
that has never existed in either grammar, and would have turned
`DESIGN-007:258` into *"the new form replaces the new form."* Neither happened,
because the rename was applied to an enumerated list of lines rather than by
substitution over a file.

**Two markers sit outside a verbatim quotation rather than inside it.**
`reference/style.md` says the marker goes in the introducing sentence *"where
an inline marker would corrupt what is being shown"*. On `ADR-017:19` and
`:108` the quotation closes partway through the line, so the marker can sit on
the same line and still outside the quoted text — satisfying the same-line grep
guard **and** *"never reword a verbatim quotation to avoid needing the
marker."* Only `DESIGN-009:35` needed the introducing-sentence form, because it
is strict JSON inside a fence.

## 5. Drift — the document and its projection agree

Neither projection was regenerated. Both were edited in place, which is what
keeps `TASK-155` out of this: **the linkage register's `updated:` field was not
bumped**, and the rename script asserted that line byte-identical after writing
each register (`001-linkage.md:4` = `2026-08-18T00:00:00Z`,
`003-linkage.md:4` = `2026-09-03T06:06:45Z`). No `declared_at` was re-dated on
any of the 115 imported records.

| instrument | before | after |
|---|---|---|
| `perry-lint --root .` | 0 errors, 29 warnings | **0 errors, 29 warnings** |
| **OKR store** | 51 records, **0 drifted** | 51 records, **0 drifted** |
| **linkage store** | 123 records, **1 drifted** | 123 records, **1 drifted** |
| the drifting row | `P003-O3-KR2 differs` | **`P003-O3-KR2 differs` — same row** |
| `perry-diagnose` finding ids | `{CON-02,CON-03,DOC-03,DOC-05,LOAD-03,NS-01}` | **identical — no `LOAD-02`** |
| `user_load.dangling` | `[]` | **`[]`** |
| `user_load.untitled` | `[]` | **`[]`** |

The linkage store's 1 is the pre-existing `TASK-383` defect — `P003-O3-KR2`'s
`tasks[]` array holds `TASK-382` and `TASK-383` in the store and not in the
register. It is **not** a `linked` difference and this commit neither caused
nor fixed it.

And the edge resolves end to end, which is the 121-edge chain `ADR-017` worries
about: `perry-goals krs` renders `| P003-O1-KR1 | … | O2-KR1 |` where it
rendered `| … | KR-O2.1 |` before. All three readers answer with exit 0 and
**zero** old-form ids in their output.

## 6. Mutation — and it is not green

Per `knowledge/verification/mutate-every-fix-and-distrust-green.md`. The claim
under test is *"the projections are actually compared against the documents"*.
Rename an id in the document and not in the projection; if the linter stays
green the comparison is decorative.

| # | mutation | `okr_drifted` | `linkage_drifted` |
|---|---|---|---|
| — | post-rename, unmutated | 0 | 1 |
| M1 | `OKR.md`: `O2-KR5` → `O2-KR9`, **document only** | **2** | 1 |
| M2 | `003-linkage.md`: `P003-O1-KR1`'s `linked` `O2-KR1` → `O2-KR9`, **document only** | 0 | **2** |
| — | after revert | 0 | 1 |

Both went red, each in **its own store and not the other's**, and both files
were restored byte-identical (asserted, not eyeballed). M2 is the sharper of
the two: it proves the `linked` field specifically is inside the compared tuple,
which is the field this whole commit moves. Had either come back green, that
would have been the finding and this rename would have shipped with no
instrument behind it.

## 7. What I did NOT do, and one open dependency

**`goals/` still mints the old form, and that is a real dependency of this step
that this commit does not close.** Round 2 named it and I am repeating it
rather than letting it be discovered later: `goals/state/OKR_TEMPLATE.md` (6
concrete old-form ids) and `goals/state/linkage_TEMPLATE.md` mint ids;
`goals/SKILL.md:193` and `goals/reference/setup.md:25` tell an agent that KR
ids match `KR-O<n>.<m>`. **Perry will keep minting old-form ids into a renamed
project until those move.** I left them because they are outside the dispatch's
scope table, because the two `SKILL.md`/`setup.md` sites are *placeholder*
forms — the class `reference/style.md` requires and the corpus round explicitly
excluded from the 50 — and because changing an authoring template is a
behavioural change to the `goals` lane rather than a data rename. It needs its
own row.

## 8. What I did not check

- **I did not verify the 30 live references point at the *right* KR.** Same gap
  the corpus round declared: I checked every id resolves, not that each design
  is about the KR it names. A header pointing at the wrong live KR passes
  everything here — and, per `TASK-390`, would pass everything anywhere.
- **The document-level `[[old-form]]` marker on this file is weaker than a
  same-line one.** Every `KR-O<n>.<m>` in the tables above is a bare line under
  a strict same-line grep. I followed `ADR-017-corpus-result.md`'s precedent
  rather than inventing a third convention, but the honest statement is that
  `perry/evidence/` as a whole is outside the guard, and nobody has decided
  whether it should be inside it.
- **I did not re-run the corpus round's `LOAD-02` experiment.** I took its
  measurement — that `Linked OKR` is never resolved — as given, and checked the
  nine headers by reading instead. `user_load.dangling` being `[]` after this
  commit is therefore *not* evidence the headers are right.
- **I touched `tests/` in exactly one place**, which § 9 names. The other 80
  old-form occurrences there are step 3's and are untouched.
- **I did not check aiMark**, which reads these ids through `perry-goals list`.
  The contract shape and id count are unchanged (25 ids, same keys), but the
  id *values* all changed, and a consumer that stored them is broken by this
  commit. `ADR-017`'s "What would reopen this" names it and it is not mine.
- **I did not settle the four `?` rows**, and I did not re-derive any
  classification I disagreed with — the two I departed from (§ 2) are departures
  the corpus round's own text licenses, both stated in the open.
- **I did not enumerate the 421 survivors one by one.** They are counted by
  area and disposed of by rule, not read individually.
- **The three concurrent V4 rounds** on `bin/` and `viewer/` measure against
  live state, and this commit changes that state under them. Expected, per the
  dispatch; not coordinated by me.

## 9. Full suite after the change — and the one test the rename broke

The first run after the rename was **redder than baseline: 4 modules / 5
tests**. The extra red was real and mine:

    FAIL  test_md_store.TestAHandEditIsReportedAndNeitherHonouredNorOverwritten.test_an_okr_hand_edit
    AssertionError: 'KR-O1.1' not found in
      'kr/v2: 2026-08-17/Objective 1 — The four work modes are usable, not just declared/O1-KR1'

Re-run alone before attributing it, per
`knowledge/verification/rerun-a-red-module-alone-before-attributing-it.md`: it
fails alone, and `test_md_store` was green at the baseline run. The fixture
copies **this project's own `perry/OKR.md`**, so the drift key moved with the
rename. This is the one case the dispatch allows — *"a test you break must be
updated to keep the suite no redder, in which case name each one"* — and it is
the only one:

    tests/test_md_store.py:1466
    -   self.assertIn("KR-O1.1", drift[0]["key"])
    +   self.assertIn("O1-KR1",  drift[0]["key"])

Incidentally, this red is also the independent confirmation that renaming the
**`v2`** block was required and not optional: the key the store computes is
`kr/v2: 2026-08-17/…`, so the fixture, the store and `perry-lint`'s drift
comparison all read `v2` as live data rather than as history.

**The repaired assertion was mutated** rather than trusted: replacing `O1-KR1`
with `O9-KR9` turns the test red, and reverting turns it green, so it is still
measuring the id and not passing vacuously. (One trap worth recording: the
revert *looked* red until `tests/__pycache__` was cleared — the mutate-and-
revert cycle wrote the file inside one mtime tick and Python reused the
mutated bytecode. A stale `.pyc` is an excellent way to misattribute a red.)

| | baseline (`e928ed4`, clean tree) | after |
|---|---|---|
| modules | 120 | 120 |
| tests | 3448 | 3448 |
| red modules | 3 | **3 — the same three** |
| failed tests | 4 | **4 — the same four** |

`test_contract_key_parity` (2), `test_diagnose` (1), `test_linkage_import` (1).
Same modules, same test names, nothing traded.

## 10. References

- `perry/decisions/ADR-017-one-kr-id-grammar.md` — the decision and its `## Changes`
- `perry/evidence/2026-09/ADR-017-corpus-result.md` — the per-occurrence classification
- `perry/evidence/2026-09/ADR-017-readers-round2-result.md` — step 1, and the `goals/` dependency
- `reference/style.md` — the `[[old-form]]` rule
- `perry/knowledge/verification/mutate-every-fix-and-distrust-green.md`
- `perry/knowledge/verification/a-single-baseline-run-is-not-a-baseline.md`
