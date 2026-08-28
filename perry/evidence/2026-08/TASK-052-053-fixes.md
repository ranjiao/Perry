# TASK-052 and TASK-053 — the two V4 FAILs, fixed and guarded

> Rung: **V3**. Every claim below is a run or a mutation. The original rows were
> V4; **a fresh V4 on these fixes has not been done** and is owed — see the last
> section. Recorded rather than quietly closed at the old rung.

## TASK-053 — the drain bricked the queue after one row, at exit 0

**Reproduced before fixing**, on a board with no `## P0`/`## P1` — the shape
`--group` exists for, and `~/proj/gimegime-pmo`'s actual shape:

```
## Intake
| Arrived | Request | Outcome |        ← separator row gone
| 2026-08-18 | a request | routed → ENG-002 |
| 2026-08-18 | a request | — |          ← same request, still undischarged

next intake → route:  refused — `## Intake` has no table
```

**Cause.** `ensure_section` anchors `## Intake` before `## P0` *or at the end of
the file*, so with no priority heading Intake lands **below** every landing
site. `cmd_route` captured the intake row's line index, `append_row` then
inserted a line above it, and the outcome was written to the now-stale index —
one line up, onto the separator.

**Fix.** The intake row is written back **before** the new row is appended, so
no index is held across a mutation at all. Plus an index-validity check that
refuses rather than deleting the wrong line, for the day a widening function
starts inserting.

**Guard.** `test_the_intake_table_survives_the_drain` and
`test_a_second_drain_still_works`. Reverting the ordering turns three tests red,
including two that were previously blind. The pre-existing tests all passed
throughout the bug, because they only asserted `"routed → <id>" in board` — the
corruption is one line above the row they were looking at.

## TASK-052 — migration wrote an id its own reader cannot read

`fix_missing_fields` matched the surrounding block's bold style, so a digest
whose neighbours are bolded got `> **Id**：SRC-n`, while
`perry-lint --provenance` anchors `^>\s*Id\s*[:：]` literally.

**Measured on a migrated copy of gimegime-pmo:** 3 of 15 provenance findings
were files migration had **just given an id to**, every one then declared
conformant. Migration minted an id nothing could cite, which is the one thing
the id is for.

`header_block_end`'s docstring already named the hazard and named it **one case
too narrow** — *"a digest whose neighbours are plain must get a plain line"* —
when the dangerous case is neighbours who are bold. A comment below it claimed
the joining path applied "the same rule", which was false: it did the opposite.
Both corrected, and the code changed rather than the sentences being softened.

**After:** provenance 15 → 1 finding on the same copy; lint 59 → 15 unchanged;
73 → 75 migrate tests, all passing.

**Guard.** `TestAMigratedIdIsReadableByItsOwnReader`, with a fixture that is
deliberately **not** Perry-generated — a block Perry starts is never bolded, so
a Perry-shaped fixture cannot reach the branch at all. That is
`TASK-044-spec.md`'s governing sentence, and it is why 30 mutations walked past
this.

## What is not done

Both fixes are **V3**: reproduced, fixed, guarded, mutation-verified. Neither
has had a **fresh V4** — a reviewer who did not build the fix, scoring it
against written criteria. For TASK-052 the fix was proposed by the V4 reviewer
and applied by the builder, which is not the same as being reviewed. That is
owed on both, and closing these rows at V3 rather than re-asserting V4 is the
honest record of it.
