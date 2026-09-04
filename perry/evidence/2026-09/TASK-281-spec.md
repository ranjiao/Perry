# TASK-281 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: (none) — the number is computed or it is asserted
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Dependencies**: `TASK-279`
- **KR linkage**: `P003-O3-KR2` — this row is what makes that KR measurable

## Why this row exists

`DESIGN-015 § 6` step F: *"`perry-state` computes `P003-O3-KR2` from store +
events instead of an asserted `current`."* The design adds one sentence about
ordering that this row inherits — **E is separable and can lag; F is what turns
the KR from asserted into measured and should not.**

**The KR reads 0% today, and the reason matters.** Measured on `main`
2026-09-04: **180 rows opened since the phase started on 2026-08-28, and not one
carries a `kr` or `linked` field.** The target is 100%. But the metric is not
computed from anything — it lives as prose in `phase/003-linkage.md`'s `metric:`
field, because `goals/reference/linkage.md` states that nothing there writes a
`target` or a `current`. So the phase currently scores itself on a number a
person typed.

That is the defect. A KR whose value is asserted cannot be wrong in a way
anything detects.

## What the number actually is

`P003-O3-KR2`: *rows opened during phase 003 that take a KR edge or an
`unlinked` declaration **in the same action as `add`***.

Three parts, and the third is where rounds go wrong:

1. **The population** — rows opened during phase 003. The phase started
   2026-08-28; use the store, not a file's mtime.
2. **The numerator** — rows with an `edge` or `unlinked` record in
   `linkage.jsonl`, which TASK-277 imported and TASK-279 now writes.
3. **"In the same action as `add`"** — this is an *event* property, not a store
   property. A row linked an hour later by a separate `perry-goals link` call
   satisfies parts 1 and 2 and **must not** count. `DESIGN-015 § 5.2` is
   explicit that the record of the question being asked lives on the event:
   `add` without `--kr` writes `kr: null` on the `add` event and warns.

**So the computation reads both `linkage.jsonl` and `.perry/events.jsonl`, and a
round that reads only the store will produce a number that looks right and
measures something else.**

## Files in scope

- `bin/perry-state` — where the computation goes.
- `phase/003-linkage.md` — the `metric:` prose for this one KR, only to stop it
  asserting a number now computed elsewhere.
- `tests/` — the guards.

## Deliverable

`P003-O3-KR2` is computed from `linkage.jsonl` and `.perry/events.jsonl`, and
the register stops carrying an asserted value for it. Where a reader used to
find a typed number they find the computed one, and the two cannot disagree
because only one exists.

## Verification

1. **Report the number before you change anything.** Today's asserted value and
   today's computed value, side by side. The PMO measured 180 rows and 0 carrying
   a link; if your computation disagrees with either figure, say so — that is a
   finding about the computation or about my measurement, and both are worth
   more than a matching number.
2. **The same-action property is tested directly.** Construct a row linked *in*
   the `add` action and a row linked by a later separate call. The first counts,
   the second does not. **A computation that cannot tell them apart fails this
   row**, however plausible its total looks.
3. **A control**: a phase with no rows opened reports no denominator rather than
   dividing by zero or reporting 100%.
4. **The register no longer asserts it.** Show the `metric:` prose before and
   after, and show that nothing else reads the old asserted value.
5. **Mutation**: revert the computation to the asserted value and show a named
   test go red. Anchor by line number *with an assert on the old text*; clear
   `__pycache__`; wait past the whole-second boundary; **verify restores against
   your branch's own base, never `main`, which moves.** A green mutation is the
   finding.
6. Full suite via `tests/run` no redder than the baseline **you measure**, and
   `bin/perry-lint --root .` at 0 errors. If the machine is loaded, timing
   figures are meaningless — a bare `python3 -c pass` measured 4,467ms here at
   load 114 — so say what the load was if you record a duration.

## Bound

```
Enumeration: the six KR ids in phase/003-linkage.md
Size:        6 on 2026-09-04 — P003-O1-KR1, KR2, KR3, P003-O2-KR1, KR3,
             P003-O3-KR2. (Seven at the design's writing; P003-O2-KR2 was
             withdrawn by USER-911.)
This row:    P003-O3-KR2 only — one of the six.
Remainder:   the other five keep their asserted `metric:` prose. Whether they
             should also be computed is TASK-231's question, not this row's.
             The last element is P003-O3-KR2 itself.
```

## Out of scope

- Computing any other KR. Five stay asserted, and that is `TASK-231`.
- `phase/<NNN>-linkage.md` shedding its schema'd half — that is step E,
  `TASK-280`, and the design says E may lag while F may not.
- Backfilling links onto the 180 unlinked rows. **This row measures; it does not
  improve the number it measures.** A round that also backfills has made its own
  verification unfalsifiable.
- `bin/perry-task add --kr` — that is step D, `TASK-279`, and this row depends
  on it rather than doing it.
