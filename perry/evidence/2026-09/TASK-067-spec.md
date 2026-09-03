# TASK-067 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: large
> Subjective verification: (none) — every acceptance is a plant with an observed outcome
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: `TASK-094` (done), `TASK-095` (done)
- **KR linkage**: `P003-O1-KR2`
- **Criteria**: this file **and** `evidence/2026-08/TASK-067-finding.md` §§ `Bound`, `Census`, `The two readings`

## The principle is chosen. This row implements it, and does not re-derive it.

The row FAILed two V4 rounds. `perry-lint --reviews` reported
`review-rounds-exhausted` — *"a row that has failed 2 times is failing on a
PRINCIPLE nobody has picked, and each further round re-derives it differently"*.

`TASK-323` measured the population so the choice could be made against numbers,
and PASSed V4 on 2026-09-03. **`USER-915` then chose reading (B):**

> **One choke point plus one detector.** Nothing outside `render_row` builds a
> table row.

**Do not re-open the choice.** Reading (A) — every write path refuses — was
considered and not taken. A round that argues for (A) is arguing with the user.

## What (B) buys, and what it does not — measured, not assumed

`USER-915`'s answer carries three consequences and this spec inherits all three.

### 1 · Routing the separator-row builders is PART of (B), not an extra

(B) covers them *by construction* only if separator rows go through the choke
point. **Today they do not.** Re-derived on `fd9df3b` with the census's own
script, `evidence/2026-09/TASK-323-bound.py`:

```
bin/perry-goals:327   `+`-concat onto a `|` literal
bin/perry-goals:328   `+`-concat onto a `|` literal
bin/perry-goals:3093  `+`-concat  and  `|`.join()
bin/perry-task:985    `+`-concat  and  `|`.join()
bin/perry-task:1034   `+`-concat  and  `|`.join()
bin/perry-task:1112   `+`-concat  and  `|`.join()
bin/perry-task:5174   `+`-concat  and  `|`.join()
bin/perry_md_store.py:774  `+`-concat onto a `|` literal
```

**Note the neighbours at `perry_md_store.py:773` and `:775`: both are `W1`
`render_row()` calls.** A separator built by hand between two choke-point calls
is the shape this row is about, in one screen.

### 2 · `bin/perry-decide:332` is out of (B)'s reach

It builds no row, so a rule about who builds rows does not touch it. It guards
with a **third, weaker spelling** — `len(_value.splitlines()) > 1`, still there
on `fd9df3b` — which misses a trailing newline where
`viewer/tables.py § line_break_at` catches it. **Leave it. File it as its own
row** and say so in the result.

### 3 · `bin/perry-task:7431` is covered by neither reading

`_v.strip() == exc.value` — matching a flag by value. Message quality, not a
corruption path. Out of scope, already stated in `TASK-323 § 2`.

## The detector is NOT the deliverable's backstop, and must not be sold as one

**This is the part of `USER-915`'s answer most likely to be lost.** `ragged-row`
was measured by the census and by two V4 rounds:

- **present** for the write shapes w4–w7;
- **absent** for the read shapes r2, r3, r4, r7, r8 — and `.split("|", 6)`
  returns the right cell count with truncated content, so **no count-based
  check can ever cover the read side**;
- **four demonstrated blind spots** on the read half — `maxsplit`, `re.split`,
  a `SEP` constant, `.rsplit`/`.partition` — because `SPLIT_RE` is
  `\.split\((['\"])\|\1\)` and matches none of them;
- **fires only inside a schema-recognised table.** Round 1 confirmed with a
  control: the identical 8-cell row is silent in an unrecognised section. A
  project filing work under its own headings via `add --group` — which Perry
  explicitly supports — **has no net at all**.

**Write these into the deliverable as declared limits**, in the file a reader
of the rule will actually open. Not as caveats in an evidence document. A
backstop presented as working where it is measured absent is worse than none,
because the next round stops looking.

## Deliverable

1. **One symbol.** Nothing outside `viewer/tables.py § render_row` builds a
   table row. The eight sites above are routed through it — **including the
   separator rows**, which is where the shape actually leaks.
2. **A guard on the symbol, not on the shape.** The check is *"nothing outside
   the choke point builds a row"* — one enumerable surface — not a detector
   that tries to recognise row-shaped strings. `USER-904` and `USER-906` both
   chose this move; `TASK-285` chose it a third time today after a denylist
   over English lost twice. **Do not build a cleverness detector.**
3. **The declared limits** from the section above, written where the rule is.

## Verification

1. **Reproduce the leak first.** On a `git archive` copy, plant a value
   containing `|` and one containing a newline through each of the eight sites,
   and show what lands. That before-state must be in the evidence.
2. **After the change**, the same plants are refused or escaped, and the table
   round-trips.
3. **The guard goes red when the choke point is bypassed.** Add a ninth
   builder that constructs a row by hand and show the guard fires. This is the
   test that makes (B) a rule rather than a cleanup.
4. **A control**: legitimate `render_row` callers are not flagged. A guard that
   fires on the choke point itself is useless.
5. **Mutation**: revert each routing one at a time and show a named test go
   red. Anchor by line number *with an assert on the old text* — a non-matching
   anchor silently no-ops. Clear `__pycache__`, wait past the whole-second
   boundary, restore against **pre-mutation** bytes, verified with `git show`
   rather than the harness's own output. **A green mutation is the finding.**
6. `perry-lint --root .` at 0 errors; full suite no redder than baseline.
   **Measure the baseline yourself** — it has not been green all day.

## Bound

```
Enumeration: python3 perry/evidence/2026-09/TASK-323-bound.py
Size:        88 members on fd9df3b — 27 W1 · 18 W2 · 37 R1 · 6 R2
             (the census measured 89 at 5720730; TASK-283 removed one W2 by
             deleting perry-lint's inline track-register parser. Re-derive
             rather than inherit either number.)
This row:    the 8 W2 separator-row builders listed above
Out:         bin/perry-decide:332 (builds no row) · bin/perry-task:7431
             (message quality) · all 43 read-side members — (B) is a rule about
             who WRITES a row, and the census proved no count-based check
             reaches the read side
```

A 89th member found by the round is **a new row**, not a widening of this one.

## Out of scope

- Reading (A), in whole or in part. The user considered "(B) plus fixing (A)'s
  eight corruption sites" and **did not take it**.
- Making `ragged-row` cover the read side. Measured impossible for
  `.split("|", 6)`; a count-based check cannot do it.
- `perry/phase/` and `OKR.md`. Other lanes' files.
