# TASK-236 — round 4, V4 review

> Criteria: `perry/evidence/2026-09/TASK-236-spec.md` — the only authority.
> Under review: `3d2ec784`, with `70b83f7f` read for the round-3 verdict it
> answers, and `88fea9fe` / `991e3c32` read for the two rounds before that.
> Reviewer: fresh context; did not write this code, and wrote none of rounds
> 1, 2 or 3.
> Prior rounds: round 1 FAIL, round 2 FAIL, round 3 FAIL (`USER-927` answered
> (B) on 2026-09-13, which is why round 4 exists rather than a fourth review —
> `review.md § 6`).

## 0. Base check — done first, and it was NOT already correct

The dispatch predicted this and the prediction held. The worktree was cut by a
tool at a commit that contained none of the work.

```
git log --oneline -1                          → 583f024f Merge bin-contract-phase-a: …
git merge-base --is-ancestor 3d2ec784 HEAD    → non-zero: HEAD did NOT contain 3d2ec784
git status --porcelain                        → empty (clean)
git rev-parse main                            → 3d2ec78406988c2fac30f484d48d97b0b12d70d8
                                                (exactly the tip named at dispatch)
git merge-base --is-ancestor HEAD main        → 0, so a fast-forward was legal
git rev-list --count 583f024f..3d2ec784       → 135
```

`3d2ec784` is `main`'s tip rather than a strict ancestor of it, so the
dispatch's "strict ancestor" wording is satisfied in the direction that
matters — HEAD was a strict ancestor of `3d2ec784`, and nothing later than the
round's own tip exists on `main` to import. Conditions met, so I
fast-forwarded **my own branch only**
(`worktree-agent-a23623fc92abf5d9a`), never `main` and never another branch:

```
git merge --ff-only 3d2ec784   → 583f024f..3d2ec784, 131 files changed
git log --oneline -1           → 3d2ec784 TASK-236 round 4: a blank join key is not a wildcard
git merge-base --is-ancestor 3d2ec784 HEAD  → 0  (re-asserted)
git status --porcelain         → empty
```

So the tree reviewed is the round's own tip and nothing else. **Recorded here
rather than only in the reply**, because "I checked and it was wrong, and here
is what I did about it" is evidence and "I did not check" is not.

**The repository under review was not modified.** Every destructive check ran
in a `git archive` export of `3d2ec784` under the session scratchpad, against
fixture projects built there. Closing state, by the project's own helper
against the ref rather than against bytes I snapshotted:

```
$ python3 bin/perry-restore-check 3d2ec784 bin/perry-goals \
      tests/test_okr_krs_render.py bin/perry_md_store.py \
      perry/okr.jsonl perry/OKR.md viewer/parsers.py
  ✓ bin/perry-goals matches 3d2ec784 (22688cfbea17…)
  ✓ tests/test_okr_krs_render.py matches 3d2ec784 (61fa1cc1c6da…)
  ✓ bin/perry_md_store.py matches 3d2ec784 (503c6219f55a…)
  ✓ perry/okr.jsonl matches 3d2ec784 (788fc04093b5…)
  ✓ perry/OKR.md matches 3d2ec784 (d2aefd748217…)
  ✓ viewer/parsers.py matches 3d2ec784 (9562ca4bc913…)
  rc=0
```

## 1. What the change does, confirmed by driving it rather than by reading it

The condition is real and it works on the input it was written for. Driving
the module's own fixture store through `krs --level overall --json` in the
scratch copy:

| store shape | rc | result |
|---|---|---|
| correct, default / `--version all` / `--version v1` | 0 | 2 / 5 / 3 krs, all placed once |
| all ids and `objective_id`s blank (step-1 shape), default | 1 | REFUSED, 2 named |
| all blank, `--version all` | 1 | REFUSED, 5 named |
| all blank, `--version v1` | 1 | REFUSED, 3 named |
| all blank, `--version v2` | 1 | REFUSED, 2 named |
| `objective_id` whitespace-only (`"   "`, `"\t"`) | 1 | REFUSED |
| objective `id` whitespace-only | 1 | REFUSED |
| `objective_id` lower-cased against an upper-case `id` | 1 | REFUSED |
| one `kr` `version` blank / absent | 1 | REFUSED by `validate_records` (round 3's layer) |
| one `kr` `version` unknown | 1 | REFUSED by the residual |
| one objective `version` blank | 1 | REFUSED by `validate_records` |

**Rule 3 applied to the residual, which round 4 did not touch and relies on.**
The lead asked whether a record made unplaceable by the new condition reaches
the residual on every path. It does: the residual is scoped to `wanted`, and
all three spellings of that — default (`order[-1:]`), an explicit
`--version <v>`, and `--version all` — refuse. `--version current` falls
through to the default branch. No path renders the cross product for a blank
key.

So round 4's own claim, on its own input, holds. What follows is not a dispute
about that.

## 2. Finding 1 — the blank value was excluded from the key space; the join is still not an identity, and the tool mints the colliding key itself

Round 4 fixed **a value**. The defect is **a shape**: `overall_kr_model` loops
over objectives and collects every `kr` whose key matches, and nothing
anywhere asserts that an objective id identifies *one* objective record inside
a version. Excluding `""` removes one member from the space of keys that can
collide. Every other collision still produces the cross product.

Rule 1 says the deliverable is the enumeration, so here it is. **Three ways
two objective records in one version come to share a key:**

1. **`mint_objective_ids` assigns it.** `bin/perry_md_store.py:474-499`:
   `by_title` is a single dict keyed on `title` with **no version in the key**,
   because DESIGN-009 § 5.2 wants one id to survive across version blocks. The
   same property gives two objectives with equal titles **inside one block**
   one id. The mint refuses an untitled heading (`:463`) and refuses two
   records that share a title and carry *different stated* ids (`:490`); it
   does not look at whether the group it is about to collapse sits in one
   version.
2. **A hand-edited store repeating an id** — which is the edit the refusal
   message itself instructs (*"give each one an `objective_id` that exists, or
   give the objective a record"*), and the same class round 3 enumerated when
   it listed "objective `id` blank" as user-producible.
3. **New with `3d2ec784`:** ids differing only in surrounding whitespace now
   collide, because both sides are `.strip()`ed. Before this commit `" O-1 "`
   matched nothing; after it, it is a twin of `"O-1"`. Measured: the twin
   objective takes the real one's 2 key results, count 2 → 4.

### The measurement, through the documented adoption path, no hand edit of the store

An `OKR.md` with two objectives inside one `## v1:` block whose titles are the
same string (`### Objective 1 - Reliability`, `### Objective 2 - Reliability`),
three KR rows between them. Then DESIGN-009 § 6 step 1, then step 3:

```
perry-okr write --from-file   rc=0   wrote okr.jsonl (6 records)
                                     objective ids: '' , ''
perry-goals krs --level overall
                              rc=1   REFUSED — correct, this is round 4 working
perry-okr migrate-ids         rc=0   "minted 1 objective id(s) (O-1), reused 1
                                      on a repeated version, and answered 3 KR
                                      record(s)"
                                     objective ids: 'O-1' , 'O-1'
perry-goals krs --level overall
                              rc=0   counts = {versions: 1, objectives: 2, krs: 6}
                                     store holds THREE kr records
```

The rendered surface:

```
### Objective 1 - Reliability
| O1-KR1 | … |   | O1-KR2 | … |   | O2-KR1 | … |

### Objective 2 - Reliability
| O1-KR1 | … |   | O1-KR2 | … |   | O2-KR1 | … |

6 key result(s) under 2 objective(s) across 1 version block(s).
```

**Three records, six rows, each one printed twice, and the count beneath
reports six as the whole.** The same store with the second objective's title
changed to anything else renders 3.

Every gate is clean, and clean in the same way it is clean on the correct
store — I ran the duplicate and non-duplicate documents side by side so the
comparison is not against memory:

| | duplicate title | distinct title |
|---|---|---|
| `perry-goals krs --level overall` | **rc 0, krs: 6** | rc 0, krs: 3 |
| `perry-okr verify` | rc 0 | rc 0 |
| `perry-okr diff` | `identical: true`, `every_line_and_cell_came_from_the_store: true` | identical |
| `perry-lint` | `OKR store: 6 record(s), 0 row(s) drifted` | byte-identical line |

`perry-lint`'s non-zero exit in both columns is the fixture document missing
`## Operating Principles` and `## Anti-Goals`; it is **identical in both
columns**, so nothing in the linter distinguishes the corrupted case.

This is the spec's Verification 2 (*every one of the 38 KR rows is reachable
through `perry-goals`*) and its "What it must not do" 1, failed on an input a
user produces. It answers yes to `review.md § 0`'s second question — a tool
reporting a wrong count on the only surface that carries these rows, to a
reader with no way to tell — and it is the **same category** round 3 charged in
its § 3 and round 4 restates in its own § 1: *a count printed as fact over a
table that is not the store*. Round 2 lost one row. Round 3 invented
seventy-five. Round 4 invents three.

`test_every_kr_is_placed_exactly_once` is exactly the right property and it is
asserted on a fixture with no duplicate ids, so it cannot see this. The test
that would have found it is the one that already exists, pointed at a store
`migrate-ids` produces.

**Not a suggestion about where the fix goes**, but the finding is about the
join being a containment test rather than an identity, and a residual that
counts unplaced records cannot see over-placement — round 3 said that about
blanks and it is still true about duplicates.

## 3. Finding 2 — two green mutations, and the `.strip()` they exonerate is load-bearing

Rule 2, on `bin/perry-goals` in the scratch copy, against
`tests/test_okr_krs_render` (baseline **33 tests, OK** — the round's number
reproduces). Anchored by line number, never `str.replace`; `__pycache__`
cleared and 1.1 s waited before every run; every restore written from
`git show 3d2ec784:bin/perry-goals` bytes and re-compared against them.

| # | mutation | line | result |
|---|---|---|---|
| M1 | `and oid` → `and True` (the blank guard neutralised) | 2965 | RED — 4 |
| M2 | `.strip()` removed from the objective side | 2963 | **GREEN** |
| M2b | `.strip()` removed from the KR side | 2966 | **GREEN** |
| M3 | refusal's "not a wildcard" reworded | 3009 | RED — 1 |
| M4 | refusal's "is blank" reworded | 3008 | RED — 1 |
| M5 | residual disabled (`stranded = [k for k in []]`) | 2998 | RED — 11 |

M3 and M4 redden separately, so round 4's re-assertion of its own disclosed M4
green did work — those two sentences are each held by their own check.

**M2 and M2b are green and they are not redundant code.** Applying both and
re-driving the stores:

```
                                   as shipped        .strip() removed
both sides whitespace-only "   "   rc=1 REFUSED      rc=0  krs: 8   (store holds 5)
both sides a single TAB            rc=1 REFUSED      rc=0  krs: 8   (store holds 5)
kr objective_id padded " O-1 "     rc=0  krs: 5      rc=1 REFUSED
```

So the `.strip()` is the entire reason a whitespace-only join key is not a
wildcard — the first of the dispatch's own leads — and **the whole 33-test
module stays green when it is deleted**, while the render goes from refusing to
printing eight rows for five records at exit 0. Round 4's § 5 says M4's green
was "the useful one"; the lead asked whether there were others of that shape.
There are two, and they sit on the new line itself.

## 4. Finding 3 — one of the seven new tests does not hold the claim its docstring makes

Per-test matrix, same harness, each test run alone:

```
test                                                      BASELINE   M1(and oid)  M2(.strip)
test_it_refuses_rather_than_rendering_the_cross_product      PASS        RED         PASS
test_the_refusal_names_every_unplaced_record                 PASS        RED         PASS
test_the_refusal_says_a_blank_key_is_not_a_wildcard          PASS        RED         PASS
test_no_table_is_printed_at_all                              PASS        RED         PASS
test_a_blank_objective_id_alone_is_enough                    PASS       PASS         PASS
test_the_correct_store_still_renders                         PASS       PASS         PASS
test_every_kr_is_placed_exactly_once                         PASS       PASS         PASS
```

`test_a_blank_objective_id_alone_is_enough` is green when the rule it names is
removed. Its docstring says *"Without this the fix could have been 'both blank
is special', which is a rule about a coincidence rather than about the key"* —
but the store it drives blanks only the `kr` side and leaves the objective ids
intact, which is round 2's plain **orphan** case: `"" != "O-1"` strands the
record whether or not `and oid` is there. It pins round 2's rule, not round
4's, and the docstring says otherwise. The last two are anti-vacuity cases and
are correctly green under both; this one is presented as discriminating and is
not.

## 5. Finding 4 — § 3's correction to round 3 is false, and it is written to stop the next round looking

Round 4 § 3 and the commit message both say: *"The reviewer reported
`perry-goals list` printing '18 of 19 at rc=0' on the damaged store. It does
not: that reader's output is **byte-identical** to the clean one."*

Measured on a copy of **this repository's own** `perry/okr.jsonl` (51 records,
38 `kr`, versions `v2: 2026-08-17` and `v3: 2026-09-01`) with one `kr` of the
current block damaged three ways, clean and damaged projects built side by
side:

```
                                  clean              one kr version BLANK
perry-goals list                  rc=0  2333 bytes   rc=0  2226 bytes   DIFFERS
perry-goals list --level overall  rc=0  2333 bytes   rc=0  2226 bytes   DIFFERS
perry-goals list … --json         rc=0  krs[] = 19   rc=0  krs[] = 18
perry-state --section okr         rc=0  8299 bytes   rc=0  7766 bytes   DIFFERS
perry-state --compact             rc=0                rc=0              DIFFERS
perry-goals krs --level overall   rc=0                rc=1  REFUSED
```

and the diff of the text render is the row and the footer:

```
-  O1-KR1     overall   —   Non-`project` modes running on a live track …
-  19 KR(s) · 19 with no target/current pair
+  18 KR(s) · 18 with no target/current pair
```

Identical for `version` absent and `version` unknown. **Round 3's report
reproduces exactly**, on the bare command and on `--level overall` alike; the
only `list` spelling that is byte-identical is `--level phase`, which reads
`linkage.jsonl` and not this store at all.

This matters beyond tidiness because of what it was written for. Round 4 says
the correction exists *"so the next round does not chase it"*, and it
re-describes an open defect — F-1, which this round deliberately did not fix —
as *"two readers disagree about whether the store is usable, not one silently
dropping a row"*. It is one silently dropping a row, and it drops it while
printing a count of the survivors as the whole: the same category as
everything else on this row. A future round told not to chase it would leave
the more serious half of F-1 undescribed.

I am grading this **ROW, not FAIL**: `review.md § 0` puts *a false statement in
something nobody executes* below the line and says to file the correction as a
row. The executable defect it misdescribes is round 3's F-1, which round 4
correctly leaves open and which is not this round's to fix.

## 6. Leads checked and not charged

- **An objective with a blank `id` and no KRs at all.** Renders at rc 0 as an
  objective with an empty table (`objectives: 1, krs: 0`). Under the new rule
  that is a true statement about that record — a blank-keyed objective can
  hold nothing — and nothing is over- or under-counted. Not charged.
- **Case.** `o-1` against `O-1` strands and refuses. Loud, correct.
- **A blank on one side only.** Both directions refuse (kr side blank: orphan;
  objective side blank: every kr in that version stranded).
- **The adoption path still completes.** DESIGN-009 § 6's own gate between step
  1 and step 3 is step 2 — `perry-okr render` / `verify` / `diff` — and all of
  those still return 0 on the step-1 store. `perry-goals krs` refusing in
  between is new, but nothing in the documented sequence requires that surface
  to render before `migrate-ids` runs. The refusal is not a break in the path.
- **F-1 left open deliberately.** I confirmed `viewer/parsers.py:2556
  load_okr_store` still calls no validator at `3d2ec784`, and did not re-run
  round 4's `test_contract_key_parity` probe. Leaving a contract change to the
  user is a defensible call and I am not charging it.

## 7. Verdict reasoning

The change is a real improvement and should be kept: the condition is correct
on the store it was written for, it refuses on every version path, the residual
still bites (M5, 11 red), and two of the three refusal sentences are each held
by their own assertion after round 4 caught its own green.

What fails is the same thing that failed in rounds 1, 2 and 3, and round 4
names the pattern in its own first paragraph without escaping it: **the round
fixed the instance it was handed rather than the category.** Round 2 fixed the
orphan. Round 3 fixed the validator. Round 4 fixed the blank. The join is still
not an identity, and the project's own migration tool mints a colliding key
from a document a user can write, after which the only surface carrying these
rows prints twice as many as the store holds, at exit 0, with `verify`, `diff`
and `lint` reporting exactly what they report on a correct store.

## What I did not check

- **The full suite.** I did not run `tests/run`, so the round's
  `130 modules · 3796 tests · 3 red` and its attribution of those three reds
  are unverified. I ran `tests/test_okr_krs_render` (33 OK — the round's number
  reproduces) in the scratch copy only. Not run in the worktree: the suite
  writes and other sessions share this machine
  (`review-constraints.md § The repository is live`).
- **Round 4's `load_okr_store` probe.** I did not re-apply it and so did not
  verify "15 of 35 in `test_contract_key_parity`". I confirmed only that
  `load_okr_store` still calls no validator.
- **Whether a duplicate-title `OKR.md` exists in any real project.** I showed
  the shape is producible through the documented path on a fixture I wrote; I
  did not check Perry's own `OKR.md`, `gimegime-pmo` or `PolyForge` for one.
  Perry's own store has 5 distinct objectives per version and does not exhibit
  it today.
- **`perry-okr render --write`**, the write path "must not do" 5 is about. I
  ran `render`, `verify` and `diff` read-only and never `--write`, on any tree.
- **`mint_objective_ids` beyond the duplicate-title path.** I read its passes
  and drove one input through it; I did not sweep its refusals, its
  idempotence, or what it does when a duplicate title spans versions *and*
  repeats within one.
- **The viewer, `bin/perry-task:6513` and `bin/perry-task:5320`.** Round 3
  named these as unvalidated readers; I did not open them. They are round 3's
  F-1 surface, not round 4's change.
- **Non-string `id` / `objective_id` values.** `str(... or "")` coerces an int
  or a list; I drove strings only, so I do not know what `[1]` or `0` does to
  the join.
- **Rounds 1, 2 and 3's verdicts as claims.** I read all three for the defect
  shape and re-derived everything I charge here myself. I checked exactly one
  of their claims against measurement — round 3's `18 of 19`, in § 5 — because
  round 4 contradicted it.
- **The three tests I did not mutate individually.** `test_the_correct_store_
  still_renders` and `test_every_kr_is_placed_exactly_once` were run under M1
  and M2 only; I did not mutate the renderer itself to confirm they redden on a
  broken correct-store path.

```
=== VERDICT ===
task: TASK-236
rung: V4
result: FAIL
grade: FAIL — Verification 2 and "What it must not do" 1: a KR row reachable
         through perry-goals, and a table the render reproduces rather than
         multiplies
criteria: perry/evidence/2026-09/TASK-236-spec.md
checked: base check first — HEAD was 583f024f and did NOT contain 3d2ec784,
         tree clean, main's tip exactly 3d2ec784 as dispatched and HEAD a
         strict ancestor of it, so my own branch was fast-forwarded to
         3d2ec784 and re-asserted. All destructive work in a `git archive`
         export of 3d2ec784 in the scratchpad; the repository under review is
         unmodified, shown by bin/perry-restore-check 3d2ec784 over six paths.
         The new condition driven on 13 store shapes including whitespace-only,
         tab, case, one-side-blank, and all three version paths (default,
         explicit, --version all) — it refuses on every one, so round 4's own
         claim holds and the residual is reached on every path (rule 3).
         The category enumerated instead: three ways two objective records in
         one version share a key, one of them minted by perry-okr migrate-ids
         itself. Six line-anchored mutations on bin/perry-goals against
         test_okr_krs_render (baseline 33 OK), __pycache__ cleared and 1.1s
         waited, each restore written from and re-verified against `git show
         3d2ec784:bin/perry-goals`. Per-test matrix for the seven new tests.
         Round 3's "18 of 19" claim re-measured on a copy of this repository's
         own okr.jsonl.
not-checked: the full suite (tests/run) and so the round's 130/3796/3-red
         figures; round 4's load_okr_store probe and its "15 of 35"; whether
         any real project's OKR.md carries two objectives with one title;
         perry-okr render --write; mint_objective_ids beyond the duplicate-
         title path; the viewer and bin/perry-task's reader paths; non-string
         id values; rounds 1-3's verdicts as claims, apart from round 3's
         "18 of 19" which round 4 contradicted.
proof: bin/perry-goals:2963-2966 excludes one VALUE from the join key and
         leaves the join a containment test, while bin/perry_md_store.py:474
         keys `by_title` with no version in it, so two objectives with equal
         titles inside one `## v<N>` block are minted ONE id. Through the
         documented path with no hand edit of the store — `perry-okr write
         --from-file` (rc 0), `perry-okr migrate-ids` (rc 0, "minted 1
         objective id(s) (O-1), reused 1") — a store holding THREE kr records
         renders at bin/perry-goals:2964 under both objectives: `perry-goals
         krs --level overall` prints six rows and "6 key result(s) under 2
         objective(s) across 1 version block(s)" at rc 0, with perry-okr
         verify rc 0, perry-okr diff `identical: true` and
         `every_line_and_cell_came_from_the_store: true`, and perry-lint's
         output byte-identical to the same document with a distinct title.
         And bin/perry-goals:2963 and :2966 — both `.strip()` calls — can each
         be deleted with all 33 tests of tests/test_okr_krs_render.py green,
         while a whitespace-only join key goes from rc 1 REFUSED to rc 0 with
         eight rows printed for five records.
=== END VERDICT ===
```

## 8. What this verdict costs, said out loud

This is the fourth FAIL. `USER-927` was the decision `review.md § 6` asks for
and it has been answered and implemented, so round 4 was an allowed step — but
§ 6's guard was already right about rounds 1 to 3 and the reason it gave still
applies here. Each round has moved the rule one layer or one value further and
declared the category closed without enumerating it: the orphan, then the
validator, then the blank. A fifth round scoped the same way would find the
next value.

What is different this time is that the enumeration exists in § 2 and the
generating mechanism is named: the join has never been required to be an
identity, and `mint_objective_ids` groups by title with version outside the
key. Whether that becomes a narrower row, a second ask, or TASK-236 closing
with this filed separately is the PMO's and the user's call. I have not touched
the board, `perry/tasks.jsonl` or `perry/asks.jsonl`, and I have minted no
identifier.

## Rows to file — the PMO's call, not mine; no identifier minted here

1. **`TASK-0NN`** — `overall_kr_model`'s join must be an identity: an objective
   id must select exactly one objective record within a version, or the render
   must refuse. Today two records sharing an id — minted by `perry-okr
   migrate-ids` from two equal titles in one version block — place every key
   result under both and publish the doubled count at exit 0.
2. **`TASK-0NN`** — `mint_objective_ids` collapses a title group with no
   version in the key. Deliberate across version blocks (DESIGN-009 § 5.2);
   undefined within one. Either refuse two equal titles inside one block the
   way it already refuses two untitled headings, or say in the report that the
   reuse was intra-version — the current report says "reused 1 on a repeated
   version" when the version was not repeated.
3. **`TASK-0NN`** — `tests/test_okr_krs_render.py` has no case for a
   whitespace-only join key, so both `.strip()` calls in `bin/perry-goals`
   are untested while being the only thing that stops a whitespace key acting
   as a wildcard; and `test_a_blank_objective_id_alone_is_enough` stays green
   when `and oid` is removed, so its docstring's claim is not held.
4. **`TASK-0NN`** — the correction in `TASK-236-round4-result.md § 3` is wrong:
   `perry-goals list` (bare and `--level overall`) drops the row and prints
   "18 KR(s)" where the clean store prints "19 KR(s)". Round 3's description
   stands. Correct it before a later round is steered away from it.
5. **`TASK-0NN`** — the refusal tells the reader to *"give each one an
   `objective_id` that exists"*, which for a DESIGN-009 step-1 store means
   hand-editing a store that `perry-okr migrate-ids` is built to fill. Name the
   command in the message.
