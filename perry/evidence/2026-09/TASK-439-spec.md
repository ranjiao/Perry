# TASK-439 — spec

`perry-task add` refuses without an answer.

> The row is `TASK-439`, opened 2026-09-12 **with `--kr P003-O3-KR2` passed at
> `add` time** — the row that builds the gate answered the gate's own question
> in its own creating action, which is the property it exists to enforce.
>
> Design: `phase/003-storage-code.md § Definition of Done` item 5,
> `DESIGN-015 § 6` row F, `ADR-020` (the rung), `ADR-013` (ids are terminal)
> Dispatch mode: auto · Executor: claude-subagent · Estimated cycle: small
> Subjective verification: what OMISSION means after this change, because the
> tool currently tells the caller that omission is the supported answer
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Verification rung**: **V4**. `ADR-020`'s gate answers yes — `perry-task
  add` writes `tasks.jsonl`, `linkage.jsonl`, the journal and the event log —
  and of `review.md § 0`'s three questions the third answers yes: this row
  BUILDS a gate, on the path every row in the project is created through, and
  a defect in it either blocks every `add` or lets through the thing it exists
  to catch.

## Why

`P003-O3-KR2` measures rows that answered the KR question **in their own
`add`**. Measured 2026-09-12: **18 of 58, 31%**, against a target of 100.

The reason it is 31% is that **the gate warns and does not refuse.** Verified
by running it: `perry-task add` with neither `--kr` nor `--unlinked` prints a
warning naming three remedies and then creates the row. The `add` event carries
a `kr` key with value `null` — so the row enters the KR's denominator as *asked
and unanswered*, and the denominator is *"rows whose own `add` event carries a
`kr` key"*.

`phase/003-storage-code.md § Definition of Done` item 5 asks for *"every
`main`-track row opened after the gate lands"* to carry an edge or a
declaration. **That gate was never built.** What exists is the question; the
refusal is this row.

## What this row does NOT do, and it must be said first

**It does not move `P003-O3-KR2`'s number, and anyone who expects it to will
mis-read the result.** The 40 rows already in `never_answered` are permanent:
a later `perry-goals link` writes `via: "link"`, which the KR excludes by
design — that exclusion IS the KR's *"in the same action as"* clause.

The arithmetic, so nobody re-derives it wrong: each new answered row adds 1 to
numerator and denominator, so the ratio is `(18+n)/(58+n)`. Reaching 50% needs
22 new rows; 90% needs 342. **Re-baselining the denominator to rows opened
after this refusal lands is the second half of the decision and is a KR change
— the `goals` lane's and the user's, not this row's.** This row makes the
number *honest going forward*; it does not repair the past.

## The semantic change, which is the whole judgement

Today there are three states and the tool teaches the third:

| what the caller passes | today |
|---|---|
| `--kr <ID>` | edge written |
| `--unlinked` | `unlinked` record written, `via: "add"` |
| neither | **warning, row created**, counted as never-answered |
| `--kr ""` | **refused**, and the refusal says *"omit `--kr` for that, which files the row and warns"* |
| `--kr <ID>` **and** `--unlinked` | refused as contradictory |

**After this row, omission stops being an answer.** That contradicts the
blank-`--kr` refusal message quoted above, which currently directs the caller
to do the thing that will now refuse. **Rewriting that message is part of this
row, not a follow-up** — a refusal that gives advice which also refuses is
worse than no advice.

Decide and argue in the report: once omission refuses, is the separate
blank-`--kr` refusal still earning its place, or does it collapse into the new
one? Do not delete it silently either way.

## The sequencing constraint, now LIFTED

`bin/perry-task`'s `add` path was under review when this spec was written.
**`TASK-281` round 3 PASSed on 2026-09-12**, so the file is free and this row
is dispatchable. The constraint is kept in the record rather than deleted,
because the round it waited for is the round that answers its central
question — see the section below.

## What `TASK-281` round 3 settled, and it lands squarely on this row

Round 3 PASSed on 2026-09-12 and was asked to press this row's core question.
Its answer is on the record and this row starts from it rather than re-deriving
it.

**The blank `--kr` refusal is right, and the trap runs the OTHER way.**
Refusing `--kr ""` makes it mean *nothing* — no row, no event, no record —
rather than a competing third meaning. Blank-means-omission is the actual
hazard: `--kr "$KR"` with `KR` unset would silently file a never-answered row
behind a stderr warning. Verified end to end by nine probes driving the real
binary. **So do not collapse the blank refusal into the new one on the ground
that it is redundant.** The § *The semantic change* question above still has to
be argued, but this is the evidence it must be argued against.

**One correction the round handed this row.** The blank-`--kr` refusal points
the caller at `perry-goals link --unlinked`, not at `perry-task add
--unlinked`, which `TASK-394` shipped afterwards and which is the faster
remedy at creation time. Fix that in the same change.

**One exposure this row enlarges, and it must be named in the report.**
Round 3's first finding: `bin/lib/__init__.py:1438` reads `unlinked_at_add`
only *inside* the event loop, so a **half-landed** `unlinked`-at-add is dropped
from the KR's population and named by **no diagnostic** — where its edge twin
at `:1484-1486` is named by `store_edge_without_event`. It went live when
`TASK-394` shipped the writer. This row makes `--unlinked` the ONLY way to say
"serves no KR", so traffic through that path goes up and so does the blind
spot's exposure. It is `TASK-281`'s finding to fix, not this row's; what this
row owes is to say in its report how much bigger it made it.

**`bin/lib/__init__.py` is out of scope** for the same reason it was during
round 3: a fix there belongs to the row that found it.

## Files in scope

- `bin/perry-task § cmd_add` and its `parse` — the refusal, and the
  blank-`--kr` message that must be reconciled with it.
- `bin/perry-task`'s `--help` / `SURFACE` text for `add`, if it describes
  omission.
- `work/reference/subcommands.md` and any lane page telling an agent to open a
  row — a page instructing a call that now refuses is a defect this row
  creates.
- `tests/` — the refusal, its remedies, and the negative controls.
- The result document.

## Bound

```
Enumeration: every documented or scripted call of `perry-task add` in this
             repository — bin/, work/, goals/, decide/, modes/, packs/,
             templates/, tests/
Size:        DERIVE IT, and say which callers you had to change. A number is
             deliberately not given: TASK-236's spec asserted one from a grep
             and was wrong by its whole value.
Remainder:   `perry-task intake` and `route`, which open a row by a different
             path. If they reach `cmd_add`, they are IN — check, do not assume.
Last element: the lowest-ranked call site in your own enumeration's order
```

## Deliverable

1. `perry-task add` refuses when neither `--kr` nor `--unlinked` is passed, and
   the refusal names both remedies and says which one means "serves no KR".
2. The blank-`--kr` refusal reconciled, per the judgement above.
3. Every in-repo caller that would now refuse, found and fixed.
4. The result document, carrying the semantic argument as a named section.

## What it must not do

1. **It must not make `--unlinked` the easy default.** `reference/okr-linkage.md`
   forbids a guessed attribution, and a refusal that pushes every caller to
   `--unlinked` to make it go away buys a worse number than the one it fixes.
   Say in the report why the refusal does not do that.
2. **It must not touch `schema/state-schema.json`.** High-stakes list.
3. **It must not change the KR, its metric or the register.** Half two is the
   goals lane's.
4. **It must not break `add` on a project with no linkage register at all.**
   A fresh project has no KRs to name; the refusal must have an answer for it,
   and that answer must be argued rather than defaulted.

## Verification

1. The three states, before and after, each run and quoted.
2. A project with **no register** — `add` must still work, and the report says
   how.
3. **Mutation.** Remove the refusal and show a named test go red. Then weaken
   it to accept an empty `--unlinked`-equivalent and show a different named
   test go red.
4. **Anti-vacuity.** A test that would pass if the refusal never fired is the
   defect this project has caught six times; show yours reddens on a row
   created without either flag.
5. The enumerated caller set, each one judged, including the ones left alone.
6. The suite, with the pre-existing reds named rather than counted.

## Out of scope

- Re-baselining `P003-O3-KR2`'s denominator. Second half, goals lane.
- The 40 rows already unanswered. They are permanent by the KR's own rule.
- `perry-goals link` and `link --unlinked`, which are the after-the-fact path
  and are not what this row gates.
