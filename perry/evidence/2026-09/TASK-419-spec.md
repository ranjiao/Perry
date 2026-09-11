# TASK-419 — spec

> Design: `work/reference/review.md` § 6, whose rule this row makes countable
> Dispatch mode: auto
> Executor: claude-subagent — touches `bin/perry-lint`'s review pass only
> Estimated cycle: small
> Subjective verification: what a round must write down for the count to be
> readable, and whether that cost is worth paying
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P2 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`review.md § 6` is the most expensive rule Perry has and it was bought with the
whole board: 20 rows entered V4 and 74 rounds were burned, ten rows needed three
or more, two reached round 11. The rule says the second FAIL is not a third
round, it is a fork nobody has taken, and the deliverable becomes an ask.

`perry-lint --reviews` enforces it by reporting `review-rounds-exhausted`.
**It counts the wrong thing.** At `bin/perry-lint:2881` the pass reads

```python
results = [f.get("result") for _, f, _ in blocks]
```

— it counts verdict BLOCKS and not the criterion each block was charged
against. Two FAILs are two FAILs whatever they were about.

Measured on TASK-360, 2026-09-10. Its two FAILs were round 4 on criterion 2,
help from a non-first argument position on `perry-restore-check`, whose worst
outcome is exit 2 and a line naming `--help`; and round 6 on criterion 3, a
positional accepted, dropped and reported as success.
`DESIGN-016-spec.md § "What a criterion may do to a row"`, added and committed
2026-09-10, grades criterion 2b as **ROW** and criterion 3 as **FAIL**. By the
bar that now governs that row it has failed **once**.

**This is not an argument for loosening the guard**, and a fix that makes it
fire less often has missed the point. The guard fired correctly on TASK-362,
which really did fail repeatedly on FAIL-grade criteria, and the ask it forced —
`USER-924` — was a real fork that the user answered and that closed a category
in one round. The guard is right. Its input is lossy.

## Files in scope

- `bin/perry-lint` — the `--reviews` pass, `review-rounds-exhausted` and
  whatever reads a verdict block.
- `work/reference/review.md` § 3 — the verdict block's declared shape. **Read
  first.** If the count needs a field the block does not carry, changing § 3 is
  part of this row and must be argued, not slipped in.
- `perry/evidence/2026-09/` — the corpus of existing verdict blocks, read.
- `tests/` — the module that covers the reviews pass.
- `perry/evidence/2026-09/TASK-419-result.md` — written.

## Bound

```
Commit:      fe0292fb
Enumeration: every V4 verdict block under perry/evidence/. Count them in your
             own tree and state the number; `perry-lint --reviews --json` reads
             them today and is the cheapest way to enumerate
Of those:    the FAILs, and for each, whether the criterion it names is
             gradeable at all. Some rows have no criteria file — those are the
             hard case and the report must say what the counter does with them
Last element: the most recent FAIL block in the corpus
```

## Deliverable

A count that reflects the bar the row is actually held to, and a
`review-rounds-exhausted` finding that is true.

**The shape is yours to choose and to argue**, and the choice is the row:

- the verdict block names the criterion and its grade, and the counter reads it;
- or the counter resolves the criterion against the criteria file the block
  cites;
- or something else you can defend.

Whichever you pick, **say what a round now has to write down that it did not
before**, and be honest about that cost: `review.md § 1` already refuses a round
without written criteria, so a block that cannot name its criterion is a round
that should not have run — but many existing blocks are exactly that, and the
counter has to do something sane with them.

`perry/evidence/2026-09/TASK-419-result.md`: the corpus count, how many existing
FAILs are regradeable, what the counter says before and after for every affected
row, and TASK-360 and TASK-362 shown side by side — one must stop being
exhausted and the other must stay exhausted.

## What it must not do

1. **It must not raise the threshold.** `schema § thresholds.review_fail_rounds_before_escalation`
   is 2 and it is measured, not chosen. This row fixes the numerator.
2. **It must not make the finding advisory or drop it.**
3. **It must not silently reclassify a FAIL whose criterion cannot be
   determined.** Undeterminable must be a stated outcome with a stated default,
   and the default must be the conservative one — still counted.
4. **It must not edit an existing verdict block to make the new counter agree
   with it.** The corpus is evidence.

## Verification

1. **TASK-360 and TASK-362, both, before and after.** 360 stops being exhausted;
   362 stays exhausted. If either moves the wrong way the fix is wrong.
2. **The whole corpus, enumerated.** Every row whose finding changes, listed
   with the reason. A row that changes for a reason you cannot state is a
   finding.
3. **The guard still fires.** Construct two FAIL-grade FAILs on one row and show
   `review-rounds-exhausted`. Construct two ROW-grade ones and show it silent.
4. **The ask still clears it.** `review.md § 6` says the finding is cleared only
   by an open ask naming the row in `blocks`. Show that unchanged.
5. **Mutation.** Revert the counting change and show a named test go red. Then
   mutate the grade lookup — make every criterion read as FAIL — and show a
   different named test go red.

## Out of scope

- `review.md § 6`'s rule itself, and the threshold.
- The other `--reviews` findings (`v4-close-without-verdict`,
  `fail-verdict-left-at-review`, `review-with-no-verdict`).
- Re-reviewing TASK-360 or TASK-362.
