# TASK-419 — result

> Row: TASK-419 · Rung: V4 · Branch: `task-419-review-rounds-criteria`
> Base: `70458893` (main), branched 2026-09-11
> Design: `work/reference/review.md` § 6; `bin/perry-lint` `check_reviews`
> Scratch used: `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/task419-kestrel`

## 0 · The corpus, counted in this tree

`python3 bin/perry-lint --root . --reviews --json` on `70458893`:

```
verdict_blocks: 111
```

Parsed with the linter's own `parse_verdicts` over every `*.md` under
`perry/evidence/`:

| | count |
|---|---|
| verdict blocks | **111** |
| `result: PASS` | 46 |
| `result: FAIL` | **62** |
| neither (block carries `verdict:`, not `result:`) | 3 |

The 3 that carry neither are already reported as `verdict-malformed`; they are
not FAILs and this row does not change what happens to them.

`review-rounds-exhausted` fires on **2** rows at `70458893`: TASK-285 and
TASK-362.

## 1 · How many existing FAILs are regradeable: zero

**Not one of the 62 FAIL blocks names the criterion it was charged against in
any field a parser reads.** Measured, not asserted — the key census over all
111 blocks:

```
task 111 · rung 111 · criteria 111 · result 108 · proof 107
checked 99 · not-checked 99
```

and every one of the 62 `criteria:` values is a **file path** (sometimes with a
`§` anchor, sometimes prose naming a board cell), never a criterion. The
criterion is present only inside `checked:` and `proof:` as English —
TASK-360's round-4 block says *"criterion 3 PASSES … Criterion 2 swept as 76
`--help` invocations"*, and TASK-362's says *"criterion 5 by enumerating all 53
keys"*. That is prose, and a counter that reads it is a counter that a full
stop can flip.

So the split the Bound asks for is:

| | count |
|---|---|
| existing FAILs regradeable from the block | **0 of 62** |
| existing FAILs **not** regradeable | **62 of 62** |

### Why resolving against the criteria file does not rescue them

The spec offers "the counter resolves the criterion against the criteria file
the block cites" as an option. It was measured and it does not work, for a
reason that is structural rather than a missing parser:

`DESIGN-016-spec.md § "Which row each criterion decides"` maps **rows** to
criteria, not **rounds** to criteria. TASK-360's row maps to criteria `2, 3`;
criterion 2b is graded ROW and criterion 3 is graded FAIL. Its two FAILs were
one of each. A row→criteria map cannot say which round charged which, so
resolving through it yields either "this row has a FAIL-grade criterion,
count both" (TASK-360 stays exhausted — the bug is not fixed) or "this row has
a ROW-grade criterion, count neither" (the guard is loosened, which the spec
forbids twice).

**The criterion charged is a per-block fact and only the block can carry it.**
That is the finding this section exists to record, and it decides the shape.

## 2 · The shape chosen, and what a round now has to write

**`grade:` — one optional key on a FAIL block**, read only there, whose first
word is `ROW` or `FAIL` and whose remainder is the criterion reference.

```
result: FAIL
grade: ROW — criterion 2b, `--help` from a non-first argument position
```

`review.md § 3` gains a subsection declaring it (committed here, argued there,
not slipped in) and `§ 6` gains one sentence saying the count is by criterion.

### What a round now has to write down that it did not before

**One line, on a FAIL, and only when the reviewer is claiming the defect fails
no row.** A PASS writes nothing new. A FAIL that really does fail the row
writes nothing new, because silence already means *counted*.

That asymmetry is the argument for the cost being worth paying: **the field is
only ever needed by the person who wants the guard to be quieter about their
row**, and the finding tells them exactly what is missing and where. Nobody
pays for a field they do not need, and the direction the field can move the
guard is the direction someone is already arguing for in the open.

It is optional rather than a sixth required key for a measured reason: making
it required would put `verdict-malformed` on all **111** existing blocks,
including all 46 PASSes, which is how a check teaches people to ignore it.

### The default for the undeterminable, and its size

| `grade:` | counter |
|---|---|
| `ROW` (any case) | **not counted** — the round filed a row, it did not spend a round |
| `FAIL` (any case) | counted |
| absent | **counted** — undeterminable |
| unreadable (`row-grade`, `ROWS`, `2b`, `PASS`) | **counted** — undeterminable, *and* reported `verdict-malformed` |

**62 of 62 existing FAILs fall in the "absent" bucket** — the whole corpus. The
finding now states it rather than absorbing it:

> … 2 of the 2 counted carry no readable `grade:`, so the criterion they were
> charged against is undeterminable and they count by default
> (work/reference/review.md § 3).

A typo is safe but *silently* safe, so `verdict-malformed` gained one line for
it. `_GRADE_TOKEN` is `([A-Za-z]+)(?![-\w])`: `row-grade` must not read as
`ROW` by prefix, because that would quiet the guard by accident — the one
direction this row may not move.

## 3 · TASK-360 and TASK-362, before and after

### First, a correction to the spec's Verification item 1

The spec says *"360 stops being exhausted; 362 stays exhausted"* against the
live corpus. **Neither half is runnable there, and one was not runnable at the
spec's own bound commit.** Re-derived in this tree, not taken from the spec:

- **TASK-360 is `done`.** Not just today on `70458893` — it is `done` in
  `git show fe0292fb:perry/tasks.jsonl`, the spec's own Bound commit. The check
  skips it at `tid not in live`, which the comment above the loop calls out by
  name ("history is not a worklist"). It was never exhausted at `fe0292fb` and
  the fix cannot make it stop being so.
- **TASK-362 PASSed its round 11** on criteria 13 and 5. That PASS lives on
  the unmerged branch `task-362-round11-review` (`512df26d`), not on `main`, so
  in this tree the row is still `in_progress` with no PASS block and the guard
  still reports it. **The moment that branch merges, `"PASS" in results` ends
  the row's history and the finding goes silent for a reason that has nothing
  to do with this row.** "TASK-362 stays exhausted" is therefore an assertion
  with a fuse in it, and it must not be pinned as a test against the live
  corpus.

So the assertion was replaced, with the reason, by one that does not decay:

> **Both rows are reproduced from their REAL verdict blocks in a scratch
> project with the row made live, and TASK-362's is shown to be immune to the
> regrade** — graded honestly, it stays exhausted, because both its FAILs were
> charged against FAIL-grade criteria. The fix does not reach it.

That is the property the spec actually wants (the guard is right; the
numerator is lossy), it is checkable today, and it survives the round-11 merge
and the row's eventual close.

### The measurement

Blocks copied verbatim out of `perry/evidence/2026-09/DESIGN-016-round4-v4-review.md`
and `-round6-` into a scratch project; nothing in the corpus was edited. Grades
were added **on the copy** as the counterfactual "what the counter would say if
the round had written its grade".

| row | blocks | before (block count) | after, ungraded | after, grades written |
|---|---|---|---|---|
| **TASK-360** | round 4 (criterion 2 → ROW), round 6 (criterion 3 → FAIL) | EXHAUSTED | EXHAUSTED | **silent** |
| **TASK-362** | round 4 (criteria 5, 13 → FAIL), round 6 (criterion 5 → FAIL) | EXHAUSTED | EXHAUSTED | **EXHAUSTED** |

and the control, to show the ROW path is not a rubber stamp on either row:

| TASK-362, counterfactual: both graded `ROW` | silent |
|---|---|

TASK-360 stops being exhausted when its rounds say what they were charged
against. TASK-362 does not, and could not, because the grade its rounds would
honestly write is the one that counts.

## 4 · The whole corpus, before and after

`python3 bin/perry-lint --root . --reviews --json`, the two runs compared key
by key (`file`, `rule`, `line`, `message`):

```
blocks    111 -> 111
findings   29 ->  29
gone: []
new : []
```

**No row's finding changes on the live corpus, and that is the correct and
intended result.** Every one of the 62 FAIL blocks is ungraded, undeterminable
counts, so `review-rounds-exhausted` fires on exactly the two rows it fired on
before — TASK-285 and TASK-362 — with the same evidence files named.

What changed is what the finding SAYS. Both now end:

> … 2 of the 2 counted carry no readable `grade:`, so the criterion they were
> charged against is undeterminable and they count by default.

That is requirement 3 discharged: the undeterminable outcome is stated, its
default is the conservative one, and its size is on the finding rather than
absorbed into it.

**Rows whose finding changes: none. Rows that would change once their rounds
declare a grade: TASK-360 (measured above), and no other row in the corpus can
be predicted without re-reading its rounds, which § "Out of scope" forbids.**

### The requirements, one by one

1. **It must not raise the threshold.** `rounds_before_escalation` is not
   touched; `git diff 70458893 HEAD -- bin/perry-lint` contains no change to
   it, and `schema § thresholds.review_fail_rounds_before_escalation` is
   unchanged at 2. The existing precedence tests (env > store > schema) are
   green.
2. **It must not make the finding advisory or drop it.** Same `Finding("warn",
   …, "review-rounds-exhausted", …)`, same rule name, same severity, still
   under `--reviews`.
3. **It must not silently reclassify an undeterminable FAIL.** It is counted,
   the finding says how many and why, and an unreadable `grade:` additionally
   raises `verdict-malformed`.
4. **It must not edit an existing verdict block.** `git diff 70458893 HEAD
   --stat` touches four files: `bin/perry-lint`, `tests/`, `work/reference/
   review.md`, and this result. **No file under `perry/evidence/` other than
   this one is modified.** The TASK-360/362 counterfactual was run on copies in
   scratch.

### The ask still clears it (Verification 4)

`review.md § 6`'s escalation path is untouched: the `asks.jsonl` reader, the
`answered` skip, the `blocks` id extraction and the `tid in escalated`
continue are all byte-identical — the diff over `bin/perry-lint` contains no
change to any line mentioning `escalated`, `asks` or `answered`. Four existing
tests still cover it, and one was added for the graded case:

- `test_an_open_ask_blocking_the_row_clears_it`
- `test_an_ANSWERED_ask_does_not_clear_it`
- `test_an_ask_blocking_a_DIFFERENT_row_does_not_clear_it`
- `test_an_open_ask_still_clears_a_FAIL_graded_row` *(new)*

### The guard still fires (Verification 3)

- `test_two_FAIL_grade_fails_exhaust_the_row` — two FAIL-grade FAILs, reported.
- `test_two_ROW_grade_fails_do_not_exhaust_the_row` — two ROW-grade, silent.
- `test_an_ungraded_fail_counts_because_undeterminable_is_conservative` — the
  one that matters, because it is the shape all 62 existing FAILs have.

## 5 · Mutations — 15 run, 14 red, 1 provably equivalent

Each mutation is one edit to `bin/perry-lint`, applied against an anchor that
must appear exactly once or the mutation is refused rather than skipped; the
module is re-run and the file restored between each.

| # | mutation | result |
|---|---|---|
| M1 | count blocks again (`charged = list(fails)`) — **the revert** | 5 red |
| M2 | every criterion reads as `FAIL` — **the grade lookup** | 7 red |
| M3 | every criterion reads as `ROW` (the dangerous direction) | 4 red |
| M4 | silence reads as `ROW` instead of undeterminable | 6 red |
| M5 | the grade token may be a prefix (`row-grade` → `ROW`) | 2 red |
| M6 | the grade is case-sensitive | 1 red |
| M7 | the finding stops saying what it could not determine | 2 red |
| M8 | the message names every FAIL again, not just the charged | 1 red |
| M9 | an unreadable grade is no longer reported malformed | 1 red |
| M10 | `undeterminable` measured over `fails`, not `charged` | **GREEN** |
| M11 | the `aside` denominator is every FAIL | 2 red |
| M12 | the denominator is `len(fails)` | 1 red |
| M13 | the headline count is `len(fails)` again | 2 red |
| M14 | filed ROW-grade blocks are never named | 1 red |

**Verification 5 asks for two, and asks that they be different tests.** They
are:

- **The revert (M1)** reddens `test_one_of_each_is_one_failure_the_TASK_360_shape`,
  `test_two_ROW_grade_fails_do_not_exhaust_the_row`,
  `test_one_ROW_grade_and_one_ungraded_still_leaves_one_counted`,
  `test_the_finding_names_the_ROW_grade_fails_it_did_not_count` and
  `test_the_named_rounds_are_the_charged_ones_only`.
- **The grade lookup forced to FAIL (M2)** reddens all five of those *plus two
  the revert does not touch*:
  `test_fail_grade_returns_None_for_everything_it_cannot_read` and
  `test_fail_grade_reads_the_first_token_and_ignores_the_criterion`.

### M10 came back green, and it is the one worth reading

`undeterminable = [b for b in charged if fail_grade(b[1]) is None]` swapped for
the same comprehension over `fails` killed nothing, twice, including after a
test was added aimed at it.

**It is an equivalent mutant and the proof is one line.** The blocks in `fails`
but not in `charged` are exactly those whose `fail_grade` is `"ROW"`, and
`"ROW" is not None`, so no block in that difference can satisfy the filter. The
two expressions denote the same set for every input. No test can kill it, and
one written to try would be asserting something untrue.

**But the denominator standing next to it is not equivalent, and nothing was
holding it.** A row with one filed ROW-grade FAIL and two ungraded ones would
have read *"2 of the 3 counted"* while only 2 were counted — a finding
disagreeing with its own headline.
`test_the_undeterminable_denominator_is_the_counted_rounds` was added for it,
and M12 and M13 are red because of it.

## 6 · Test baseline, taken in this tree

`python3 tests/parallel`, base `70458893`, extracted clean to scratch so the
measurement is not taken in a tree that has uncommitted changes:

```
124 modules · 3576 tests · 3 modules red · 4 tests failed
```

| red at base | mine? |
|---|---|
| `test_contract_key_parity` ×2 | no — declared known |
| `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` | no — declared known |
| `test_one_header_rule.…test_git_tracks_answers_both_ways` | **no — an artifact of my baseline method.** The scratch tree is a `git archive` extract and is not a git repository, so `git` answers nothing there. Green when the module is re-run alone in this worktree, which is a git repo. Not attributable to `70458893`. |

**`test_diagnose`'s dangling-id test was GREEN at base and stayed green.** The
dispatch said it may or may not be red; in this tree, on this baseline, it is
not.

### Two reds I did cause, both found and both fixed

1. **`test_pointers_resolve.TestEveryPointerResolves.test_no_pointer_names_a_section_that_is_not_there`**
   — my new `review.md § 3` subsection cited `DESIGN-016-spec.md` by bare
   filename, and `work/reference/` is not where that file lives. Confirmed
   green at base by checking out the base `review.md` and re-running the
   module. Fixed by qualifying the path.
2. **`test_handed_back_root.TestTheFlagReachesTheTemplateThatNamesIt.test_every_call_to_one_of_them_passes_a_real_flag`**
   — and this one is a finding about the test, not about my change.
   `NO_ROOT_TO_GIVE` keys its one exemption by **line number**:
   `("bin/perry-lint", "check_file", 5495)`. Adding lines to `check_reviews`
   moved that call to 5604, **unchanged**, and the exemption stopped matching.
   Any edit anywhere above it reddens an unrelated module. Re-stamped to 5604
   with the reason written at the constant; re-keying it by something stable is
   filed as its own row rather than smuggled in here.

Both were caught only because the suite was re-run and each red was re-run
alone before being attributed. **The first full run of this row was
contaminated** — started before the edits, finished after them — and is used
for nothing above.

### After the change

`python3 tests/parallel` in this worktree at `4f85b1a3`:

```
124 modules · 3594 tests · 2 modules red · 3 tests failed
```

and those three are exactly `test_contract_key_parity` ×2 and
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — the declared known
reds, and nothing else. 18 tests added, all green.

## 7 · What I did not check

Named, because a bound that is not written is a bound that gets re-discovered
at a round's price.

- **I did not re-review TASK-360 or TASK-362** — `§ Out of scope` forbids it.
  The grades used in § 3's counterfactual are read off
  `DESIGN-016-spec.md § "What a criterion may do to a row"` and the criteria
  its own `checked:` lines name; I did not independently re-judge whether
  criterion 2b really deserves ROW.
- **I did not grade the other 60 existing FAILs.** Doing so would mean reading
  62 rounds' prose and deciding what each was charged against, which is a
  judgement the round that ran it should have recorded and I am not the author
  of any of them. They stay undeterminable and counted. The only row I can say
  changes once graded is TASK-360.
- **I did not make `grade:` reachable from any writer.** `perry-task` gains no
  flag and no template emits the field; a reviewer types it. Whether the
  review prompt in `review.md § 2` should tell the agent to write it is a real
  question and I did not answer it — the field is inert until somebody does,
  which is why the corpus is unchanged.
- **A `grade:` on a `result: PASS` block is silently ignored**, not reported.
  A PASS ends the row's history anyway, so it cannot affect the count; but a
  reviewer who wrote one has misunderstood something and is not told.
- **I did not check `--reviews --strict`'s exit code** against a corpus with
  graded blocks, only the default advisory run.
- **Other readers of verdict blocks: I did sweep, and there are none.**
  `grep -rn "parse_verdicts" bin viewer modes work` returns callers only inside
  `bin/perry-lint`, and `grep -rln "END VERDICT" bin viewer modes` returns
  `bin/perry-lint` alone. So no second parser drifts from this one. What I did
  NOT check is `tests/fixtures/` and the `packs/` trees for a third copy of the
  block's shape.
- **The `test_one_header_rule` red in my base measurement is explained, not
  eliminated** — I attributed it to the non-git scratch tree by re-running the
  module alone in this worktree. I did not prove the module is green at
  `70458893` *inside a git repository*, because doing that would need a second
  checkout of the base and this tree is the only one I may write.
- **`review.md § 6`'s rule and the threshold are untouched**, as required —
  so I did not measure whether 2 is still the right number now that the
  numerator has changed. That is a real question this row creates and does not
  answer: counting fewer FAILs with the same limit is, in effect, a small
  loosening in aggregate, and whether the measured "20 rows, 74 rounds" that
  bought the limit would have been the same under a per-criterion count is
  unknown. It is a row, not a finding.

## 8 · Verdict on my own work

The deliverable was "a count that reflects the bar the row is actually held to,
and a `review-rounds-exhausted` finding that is true." What landed:

- The count is by criterion, and the criterion is a per-block fact the block
  now carries.
- The finding is true in the strong sense the spec asked for: it no longer
  reports a number it cannot justify, because when it cannot justify one it
  says so and counts anyway.
- **The guard did not get quieter.** Not on one row, on the whole corpus: 111
  blocks in, 29 findings out, before and after, identical.
