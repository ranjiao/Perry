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
