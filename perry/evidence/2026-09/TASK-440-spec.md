# TASK-440 — spec

> Design: none. A defect found by hitting it three times in one session, and
> measured across every writer rather than at the site that bit.
> Dispatch mode: auto · Executor: claude-subagent · Estimated cycle: small
> Subjective verification: where the rule belongs so that a FIFTH writer of
> this cell inherits it without anyone remembering to wire it
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P2 · **Track / mode**: main / project
- **KR linkage**: declared unlinked at `add`. This serves no phase 003 KR.
- **Verification rung**: **V3**. `ADR-020`'s gate answers yes — `perry-task`
  writes `tasks.jsonl`, `BOARD.md`, the journal and the event log. Of
  `review.md § 0`'s three questions none answers yes: an over-long cell is
  untidy, not unrecreatable, and it misleads nobody about a number. V3, the
  default above the gate, not V4.

## Why

`Next action` has **four** writers and **two** guards.

Measured 2026-09-12 by driving the real binary with a 1,050-byte `--next`:

| subcommand | 1,050 bytes |
|---|---|
| `perry-task add` | **REFUSED** |
| `perry-task next` | **REFUSED** |
| `perry-task start` | **ACCEPTED** |
| `perry-task status` | **ACCEPTED** |

`check_next_action_length` is wired at exactly two sites: `cmd_next`'s
`cell_writer` (`bin/perry-task:4919`) and `cmd_add` (`:3641`).

**The code already states the principle it is breaking, and believes the
problem is solved.** At `:3637`, four lines above the `add` guard:

> Same limit as `cmd_next`, **at the other site that writes this cell**. A
> refusal that only one of two writers performs is a refusal a caller routes
> around without meaning to.

There is no "other site". There are three, and two of them refuse nothing.
An older comment at `:4913` makes the same mistake in the other direction:
*"`status` is the only other writer of that cell"*.

**It was hit three times in one session**, on 2026-09-12, always the same way:
`next` refuses, the session shortens the text, and the identical string goes in
through `status --next` or `start --next` because that is the call that also
moves the row. The board's cells stayed compliant because the refusal was
obeyed each time; the hole did not.

## What the fix must NOT be

**Not "add `validate=` to `cmd_status` and `cmd_start`."** That is a third and
fourth enforcement point for one rule, which is the shape this repository keeps
finding: `TASK-040` had four implementations of "where is this section" giving
three answers in one call; `TASK-431` had three tools carrying three lists of
what a blank cell looks like; `TASK-382` had four publishers of one number.
A fifth writer added later would inherit nothing.

**The rule belongs where the field is written**, so that any future writer of
`next_action` gets it without anyone remembering. Where exactly that is —
the record builder, the projection writer, `commit()` — is this row's judgement
and must be argued in the report, not chosen silently.

## Files in scope

- `bin/perry-task` — the four writers and wherever the rule lands.
- `tests/` — the guard, and the negative controls.
- The result document.

## Bound

```
Enumeration: every subcommand in `bin/perry-task § SURFACE` that accepts
             `--next`, driven against the real binary with an over-length
             value
Size:        4 on 2026-09-12 — add, start, next, status. DERIVE IT rather than
             copying this list; the surface is declared data and a fifth may
             exist by the time you run.
Remainder:   subcommands that write other cells. `--reason` and `--summary`
             have their own limits or none, and whether they need the same
             treatment is a QUESTION this row may raise and must not answer.
Last element: the lowest-ranked subcommand name in your own enumeration
```

## Deliverable

1. All four writers refuse an over-length `Next action`, enforced from ONE
   place.
2. A test that fails if a **fifth** writer is added without the rule — derived
   from `SURFACE`, not from a hand-written list of four.
3. The two false comments at `:3637` and `:4913` corrected. Each asserts a
   writer count that was wrong when written.
4. The result document, with the where-does-the-rule-live argument as its own
   section.

## What it must not do

1. **It must not change the limit.** 1,000 bytes is not this row's question.
2. **It must not silently relax any existing refusal.** `add` and `next` refuse
   today; both must still refuse, and a test must say so.
3. **It must not touch `schema/state-schema.json`.** High-stakes list.
4. **It must not widen to other cells.** See Bound / Remainder.

## Verification

1. The four-row table above, re-derived before and after, in your own tree.
2. **Mutation.** Remove the rule from its single home and show a NAMED test go
   red **for every one of the four**, not for one of them.
3. **The fifth-writer test, shown able to fail**: add a throwaway subcommand
   accepting `--next` without the rule, in a scratch copy, and show the guard
   reddens. A test that only re-checks today's four cannot catch tomorrow's
   fifth, and that is the whole deliverable.
4. An under-limit value still writes, through all four. A refusal that refuses
   everything passes every test above.
5. The suite, with the three pre-existing reds named rather than counted.

## Out of scope

- The limit's value, and whether a board cell should have one at all.
- `--reason`, `--summary`, `--evidence` and every other cell.
- `bin/perry-tasks`, `bin/perry-goals` and the other writers of other stores.
