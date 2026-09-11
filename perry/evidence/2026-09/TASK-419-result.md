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
