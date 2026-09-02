# TASK-181 — round 1, V4 review

> Reviewer: fresh context, own worktree
> `.claude/worktrees/agent-adacb1b3bf284eeeb`, branched from `main` at `d49964e`.
> Criteria: `perry/evidence/2026-09/TASK-181-spec.md`, read from
> `coding/task-247-config-predicate` (see § 0).
> Under review: `8f46cd6` on `coding/task-181-objective-records`.
> Measured on: a clean `git archive 8f46cd6 | tar -x` copy in scratch, verified
> byte-identical to the commit's `bin/perry_md_store.py` after every mutation
> was reverted.

## 0 · Which checkout this was measured on, and the re-point

The worktree was branched from `main` at `d49964e`. Neither the implementation
nor the criteria are on `main`, so `perry/evidence/2026-09/TASK-181-spec.md`
does not exist in the checkout and `review.md § 1` says to refuse. **The
dispatcher re-pointed me mid-run**, and this review records that: the criteria
were read with

    git show coding/task-247-config-predicate:perry/evidence/2026-09/TASK-181-spec.md

and everything measured below was measured on a scratch export of `8f46cd6`,
not on the worktree's own `main` tree. The scratch copy is where the mutations
and the destructive store edits were done, per `review-constraints.md § You are
a reader`; nothing in `/Users/bytedance/proj/Perry` was modified except this
review document.

One consequence to read past rather than act on: `perry-lint --reviews` run
from this worktree reports

    evidence/2026-09/TASK-181-round1-v4-review.md [citation-not-on-branch]
      `criteria:` cites perry/evidence/2026-09/TASK-181-spec.md — the branch
      does not carry it

That is the same fact as § 0's first paragraph — `main` does not carry the
spec — and not a broken citation. It clears the moment the review and the spec
sit on one branch. The block itself parses: the linter counted it among its 60
verdict blocks and raised no `verdict-malformed` against it.

## 1 · The bound, item by item

The spec's `## Bound` is size 3. All three check out.

### Item 1 — the `objective` record shape and its scanner

`STORED["objective"]` at `bin/perry_md_store.py:218` is
`("kind", "id", "version", "title", "heading", "order")`, and `perry-okr build`
emits records in that field order:

    {"kind": "objective", "id": "", "version": "v2: 2026-08-17",
     "title": "The four work modes are usable, not just declared",
     "heading": "Objective 1 — The four work modes are usable, not just declared",
     "order": 0}

The scanner reads its level and its ordinal matcher off
`schema/state-schema.json`'s own `{"level": 3, "match": "^(Objective|目标) \\d+",
"label": "### Objective <N> — <title>"}` entry (`okr_objective_heading`,
`:476`). The commit touches three files — `bin/perry_md_store.py`,
`perry/okr.jsonl`, `tests/test_md_store.py` — and nothing under `schema/`,
`perry/phase/`, or `perry/OKR.md`. Confirmed independently of the PMO's
pre-check with `git show --name-only --format= 8f46cd6`.

**`id` is carried and empty.** All 10 objective records in `perry/okr.jsonl`
have `"id": ""`; the distinct set of id values across them is `{''}`. No id is
minted.

Behaviour I checked directly on the scanner, on documents I wrote in scratch:

| input | result |
|---|---|
| `## Objective 1 — level two` | **no record** — the level-3 restriction holds |
| `#### Objective 1 — level four` | **no record** |
| `### Retro — v1` | no record (not the ordinal) |
| the same heading under two `##` version blocks | **two records, two keys** |
| `### Objective 1 —` (ordinal + separator only) | one record, `title: ""` |
| `###   Objective 1 — spaced out   ` | `heading` is the trimmed text; the hashes and the trailing run are layout and are put back by the renderer |

### Item 2 — `perry/okr.jsonl`

    perry-okr build --root <scratch>
    → 51 records · {"objective": 10, "kr": 38, "version": 3}

Independently counted: `grep -c '^### Objective' perry/OKR.md` → **10**.
Ten headings, ten records.

`git diff --numstat main 8f46cd6 -- perry/okr.jsonl` → **`10  0`**. Ten inserted
lines, zero deleted: the 38 `kr` and 3 `version` records are byte-identical in
content and in order. The author's claim is exact.

### Item 3 — `verify` clean, `OKR.md` byte-unchanged

    perry-okr verify --root <scratch>
    → records 51, lines_from_store 51, lines_the_store_does_not_hold [],
      records_not_in_the_file [], drift_count 0,
      cells_wearing_decoration {}, byte_identical true    rc 0

    perry-okr diff   → rc 0
    perry-lint       → "OKR store: 51 record(s), 0 row(s) drifted", 0 errors, rc 0

`perry/OKR.md` sha256 is `22abe9ea24a1b1026218ed681c06c11a7b64a45dbf6385f107568ab0db292d31`
on `main` at `d49964e` **and** in the `8f46cd6` tree — compared against the
BEFORE value, as the spec asks, not against bytes the tool just wrote. The
commit does not contain the file at all.

## 2 · Mutations

Every mutation was applied by line number to `bin/perry_md_store.py` in the
scratch copy, `__pycache__` removed, and a **2.2 s** wait taken before the run
so CPython could not serve a stale `.pyc` on a same-size edit. After the last
revert the scratch file `diff`s clean against `git show 8f46cd6:bin/perry_md_store.py`.

Baseline before any mutation: `test_md_store` **48 tests, OK**.

| # | mutation | line | result |
|---|---|---|---|
| M1 | the objective branch disabled — `if not m or not obj_ordinal.match(...)` → `if True:` | `:610` | **RED**, 8 failures / 2 errors, including all three the author named: `TestThisRepositoryIsReproducedByteForByte.test_okr` (`0 != 10`), `TestAnObjectiveIsARecord.test_every_objective_heading_becomes_one_record_and_nothing_else_does`, `TestTheSecondProjectFixture.test_okr_with_bullet_krs_and_a_commitments_register` |
| M2 | the title/heading split collapsed — `rest = heading[m.end():] if m else heading` → `rest = heading` | `:507` | **RED**, exactly one failure: `test_the_heading_and_the_title_are_two_different_fields` |
| M3 | the slot swallows the hashes — `(len(m.group(1)),` → `(0,` | `:623` | **RED**, 16 failures |
| M4 | `version` dropped from the objective key | `:281` | **RED**, 6 failures / 1 error, including `test_the_same_heading_in_two_versions_is_two_records` and `test_a_renamed_heading_is_reported_and_never_guessed_at` |
| M5 | the accepted heading depth widened — `r"^(#{%d}\s+)…" % obj_level` → `r"^(#{2,6}\s+)…"` | `:607` | **GREEN — the whole 48-test module still passes** |

M1 and M2 reproduce the author's two mutations exactly, on the tests they
named. M3 and M4 are mine and both redden.

### M5 is green, and here is what it does and does not mean

`okr_objective_heading`'s docstring says a scanner that accepted any depth
*"would record `## Objective 1` — a shape `OKR.md` does not declare — as an
Objective whose `version` is itself"*, and
`test_a_level_three_heading_that_is_not_an_objective_mints_nothing`'s docstring
repeats the claim. **No test exercises it.** The fixture
`OBJECTIVE_FORMS` carries no `## Objective <N>` and no `#### Objective <N>`
line, so widening the depth changes nothing any assertion looks at.

I then checked the property directly rather than through the suite: on the
unmutated code, `## Objective 1 — level two` and `#### Objective 1 — level four`
each mint **zero** records, and under M5 the level-2 form mints a record whose
`version` and `heading` are the same string — the docstring's claim, confirmed
in both directions.

So the **shipped code is correct** and the mutation is green because the test
does not test that half of what its docstring asserts. Under `review.md § What
V4 does not judge` this is a guard-coverage gap on correct code, not a
behaviour a user can hit, and I am not failing the row over it. It belongs in a
new row (§ 4).

## 3 · The load-bearing attack: is the record shape right, or does it only round-trip?

`heading` is the only objective field with a render slot. `title`, `id` and
`order` have none, and `record_key` covers `version` and `heading` only. So I
asked whether `title` can be wrong without `verify` noticing, and it can:

    # scratch copy: objective order 0's title replaced with
    # "COMPLETE GARBAGE THE FILE DOES NOT SAY"
    perry-okr verify → drift_count 0, byte_identical true, rc 0
    perry-okr diff   → rc 0

**A store whose `title` disagrees with `OKR.md` passes `verify` clean.** That is
real, and it is why I looked for the same hole elsewhere before deciding what
it means:

- the same is already true of `kr`'s `form` field — flipping a stored `kr` from
  `"form": "table"` to `"form": "bullet"` also yields `drift_count 0,
  byte_identical true, rc 0`;
- a genuinely compared `kr` field behaves as expected — a garbage `metric`
  produces `drift_count 1`, `byte_identical false`, rc 1.

So "a `STORED` field with neither a slot nor a place in the key is not
field-compared" is a **pre-existing property of this store's design**, not a
hole this row opens, and the field the renderer actually reads (`heading`) *is*
compared — I confirmed that with the anti-echo leg: `slot_descriptor` +
`render_line` fed a record that disagrees with the line prints the record's
heading and reports the disagreement, and that is what
`test_a_stored_heading_is_what_the_renderer_prints` asserts. The spec's bound
asks for `verify` clean, and it is; it does not ask for `title` to be compared,
and the spec names step 2 (`TASK-182`'s renderer) as the declared judge of
whether this shape was right. Recorded in § 4 rather than failed.

## 4 · A sixth document shape, and four things for new rows

The author cross-checked five other OKR documents. I swept **every** `OKR*.md`
in the `8f46cd6` tree — six files — deriving, validating and re-rendering each:

| document | headings | records | byte-identical | verbatim lines | store findings |
|---|---|---|---|---|---|
| `goals/state/OKR_TEMPLATE.md` | 3 | 3 | true | 0 | 0 |
| `perry/OKR.md` | 10 | 10 | true | 0 | 0 |
| `tests/fixtures/sample-project/OKR.md` | 2 | 2 | true | 0 | 0 |
| `tests/fixtures/sample-project-zh/OKR.md` | 2 | 2 | true | 0 | 0 |
| `tests/fixtures/second-project/OKR.md` | 3 | 3 | true | 0 | 0 |
| `tests/fixtures/witness-project/OKR.md` | 1 | 1 | true | 0 | 0 |

Heading counts came from a regex written here, not from `scan_okr`. Every one
round-trips.

I then wrote shapes the suite does not carry. Four produce something worth a
row. **None of them is this round's failure**: the spec's bound is deliberately
not "the record shape is right for every OKR document anywhere", and three of
the four are pre-existing properties of the store that this row inherits rather
than introduces. Filed here so the next round does not re-derive them.

1. **`title` is not field-compared** (§ 3). Same shape as `kr.form`. Worth a row
   against the store as a whole — "a `STORED` field with no slot and no place in
   the key is unverifiable" — rather than against this one kind.
2. **`objective_title`'s `lstrip(" \t—–-:：·")` eats a title that legitimately
   starts with one of those characters.** `### Objective 1 — --strict is
   documented` stores `title: "strict is documented"`. This is the same category
   as the `OKR_TEMPLATE.md` trailing-HTML-comment leak the spec already puts out
   of the set, and `heading` still round-trips, so nothing breaks — but it is a
   second instance and the pair is what makes it a row.
3. **A fenced code block is invisible to the scanner.** A ```` ``` ````-fenced
   `### Objective 9 — inside a fence` mints a record. Pre-existing: a fenced KR
   table mints `kr` records today too, on `8f46cd6` and before it.
4. **Two identical headings in one version block produce a store the tool
   cannot read back** — `validate_records` reports `… is not unique` and
   `verify`/`render`/`diff` exit 2. Pre-existing: two `kr` rows with the same id
   under one objective collide the same way. Note that headings differing only
   in *trailing* whitespace collapse to one key, because the scanner trims;
   headings differing in *internal* whitespace stay distinct.

On the spec's other two out-of-set items: the `record_key` reasoning **is**
recorded — `bin/perry_md_store.py:264-279`, with the branch itself at
`:280-281` — and those 16 comment lines state the alternative
(the `O<n>` ordinal), name what refuses it (`schema/goals-list-contract.md §
Not here`), and say which design step removes the cost. I reviewed it as the
spec asks — whether the reasoning is sound and recorded — and it is. The
`OKR_TEMPLATE.md` comment leak I reproduced and left as the author's declared
new row.

## 5 · The suite, and the one red the author flagged

I ran the whole suite on the scratch copy of `8f46cd6`:

    python3 tests/parallel -j 4
    → 108 modules · 3011 tests · 576.0s · 4 workers · all green   rc 0

**All green**, including
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`,
the one red in the author's report. That is consistent with their load-induced
judgement and is not proof of it — one green run does not settle a concurrency
race, and `TASK-272` tracks it. Treated as the spec says: an open question, not
a settled pass.

The module counts match the author's numbers (3011 total; the 8 new tests are
the 8 methods of `TestAnObjectiveIsARecord`, and 3003 + 8 = 3011). I did **not**
run the `main` baseline myself, so the 3003 figure is arithmetic and the
author's, not mine.

Downstream readers of `okr.jsonl` survive the new kind: `viewer/parsers.py §
_krs_from_store` skips any record whose `kind` is not `"kr"`, and
`bin/perry-task:4502` reads only `linked`, which an objective record carries as
`""`. `perry-lint` reports the store at 51 records, 0 drifted, 0 errors.

## 6 · One documentation defect, for a row and not for this verdict

The commit message says *"`heading` is the line byte for byte"*. It is not: it
is the line **minus** the `### ` prefix and **minus** any trailing whitespace —
`"Objective 1 — The four work modes…"`, not `"### Objective 1 — …"`. The
`STORED` comment at `bin/perry_md_store.py:207` repeats it — *"`heading` is
what the markdown line says, byte for byte"* — but the comment on the slot
itself, at `:618-622`, states it correctly ("The hashes and the space after
them are literal, and so is any trailing whitespace the author left"), and the
slot at `:623-624` is built that way. So the behaviour is right and two pieces
of prose overstate it. The PMO's summary of the author's claim inherits the
same wording and should be corrected with them. `review.md` puts a commit message that misstates
something at "file a row, never a FAIL on this one", and that is what this is.

## 7 · Verdict

All three bounded items check out under mutation, not under reading. The two
mutations the spec required redden the tests the author named, and two more of
my own redden as well. The one green mutation I found is a test-coverage gap on
code I then verified correct by direct probe, and the strongest attack — a
`title` that lies without `verify` noticing — turns out to be a property of the
store predating this row, on a field the renderer does not read, in a round
whose criteria ask for `verify` clean and get it.

=== VERDICT ===
task: TASK-181
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-181-spec.md
checked: measured on a scratch `git archive 8f46cd6` copy, reverted byte-clean against the commit after every mutation; criteria read from coding/task-247-config-predicate after a mid-run re-point; bound item 1 — STORED["objective"] is (kind,id,version,title,heading,order) and the scanner reads level 3 and `^(Objective|目标) \d+` off schema/state-schema.json, commit touches 3 files and nothing under schema/ or perry/phase/, all 10 ids empty; bound item 2 — build emits 51 records {objective 10, kr 38, version 3} against an independent grep count of 10 `^### Objective` headings, okr.jsonl diff vs main is +10/-0 so kr and version are untouched; bound item 3 — verify rc 0 with drift_count 0 and byte_identical true, diff rc 0, perry-lint "OKR store: 51 record(s), 0 row(s) drifted" rc 0, perry/OKR.md sha256 22abe9ea… identical on main d49964e and in the 8f46cd6 tree and absent from the commit; five mutations by line number with __pycache__ cleared and a 2.2s wait — objective branch disabled (:610) RED on all three named tests, title/heading split collapsed (:507) RED on exactly test_the_heading_and_the_title_are_two_different_fields, slot swallowing the hashes (:623) RED 16, version dropped from the objective key (:281) RED 6, heading depth widened to #{2,6} (:607) GREEN; direct probe that `## Objective 1` and `#### Objective 1` each mint zero records on the unmutated code; planted a garbage `title` in the store and confirmed verify still returns rc 0 / drift 0, and confirmed the same is already true of kr.form while a garbage kr.metric gives drift 1 / rc 1; swept all six OKR*.md in the tree — every one round-trips byte-identically with record count equal to an independently-regexed heading count, 0 verbatim lines, 0 store-validation findings; probed a fenced code block, a title beginning with a hyphen, a duplicate heading in one version block, a duplicate differing only in trailing whitespace, an ordinal-only heading, and an Objective above any `##` block; checked viewer/parsers.py _krs_from_store and bin/perry-task:4502 tolerate the new kind; full suite on the branch tree `python3 tests/parallel -j 4` → 108 modules · 3011 tests · 576.0s · all green rc 0
not-checked: I did not run the `main` baseline suite, so the author's "3003 tests, all green" figure is unverified arithmetic rather than a measurement of mine; I did not re-run the flaky test_host_support concurrency test in isolation or under load, so its greenness here neither confirms nor refutes the author's load-induced judgement (TASK-272); I did not review TASK-182's renderer or whether this record shape is the one it will need — the spec names that as the declared gate and it does not exist yet; I did not check `~/proj/gimegime-pmo` or any project outside this repository, so the author's claim about its nine `Objective 1:` headings is checked only through tests/fixtures/second-project; I did not check any Windows path, any CRLF document, or any OKR.md with a BOM; I did not audit `perry-goals`, `perry-state --json` or the viewer's rendered output beyond the two okr.jsonl call sites named above and the green suite; I did not evaluate whether `(version, heading)` is the right record key — the spec puts that out of the set and I reviewed only that the reasoning is recorded and sound; I did not chase the four new-row candidates in § 4 to an enumeration, and three of them are pre-existing store properties rather than defects of this row
proof: n/a — PASS
=== END VERDICT ===
