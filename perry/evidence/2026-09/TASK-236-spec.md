# TASK-236 — spec

> Design: `DESIGN-009 § 6` steps 1–2 (the gate), `DESIGN-013 § 5.4` and its
> risk table (the read-surface report), `ADR-010`, `ADR-011` Tier C, `ADR-019`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: whether a CLI render is a good enough reading
> surface — **this is a deliverable of the row, not a by-product**
> Touches architecture: yes — `ARCHITECTURE.md § 2` describes `OKR.md` as a
> parsed file. Stop and ask before changing that section (`DESIGN-017`).
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: TASK-235 (done 2026-08-30), TASK-181 (done 2026-09-03),
  TASK-182 (done 2026-09-04). **All satisfied.** The row's own `Next action`
  said "Blocked" until 2026-09-11, which was stale text and not a live edge.
- **KR linkage**: declared unlinked. Phase 003 scores no KR against this row.
- **Verification rung**: **V4**, and it clears `ADR-020`'s gate rather than
  being given the rung by habit. `perry-okr render --write` puts bytes on a
  user's disk, so this is a write path. Of `review.md § 0`'s three questions
  the first answers yes: the deliverable **deletes 38 rows of a tier-1
  document** on the strength of a store, and if the store is wrong on any of
  them the rows are gone.

## Why

`OKR.md`'s KR tables and `okr.jsonl` hold the same facts. `ADR-019` states the
rule — a fact with a schema lives in the store, a document holds what has none
— and `ADR-011` Tier C names this row as one of the places it is not yet true.

**The precondition is not merely closed, it is live and re-measurable.** Run
`bin/perry-okr diff` on this repository today:

```
"kinds":     {"objective": 10, "kr": 38, "version": 3}
"identical": true
"every_line_and_cell_came_from_the_store": true
```

That is `DESIGN-009 § 6` step 2's gate, passing: the renderer rebuilds `OKR.md`
byte-for-byte from records, so the store demonstrably holds everything the
tables hold. **Re-derive it in your own tree before touching anything.** If it
does not come back `true` on both keys, stop — the gate is the whole reason
this row is allowed to delete anything.

`every_line_and_cell_came_from_the_store` is the load-bearing key, not
`identical`. `TASK-182` found that `identical` can be true while the store
produced none of the bytes, which is why the second key and exit code 3 exist.

## Files in scope

- `perry/OKR.md` — 187 lines, 63 table rows, of which **38 are KR rows**. The
  KR tables come out. Everything else stays.
- `bin/perry-goals` — where the render lands. It **parses nothing** today by
  deliberate design; a render is a new surface on it, not a second reader.
- `bin/perry-okr` — `render` / `diff` already exist and are the gate. Read.
- `viewer/parsers.py` — read, and report. See *What this row does not buy*.
- `tests/` — the guard and its mutations.
- `perry/evidence/2026-09/TASK-236-result.md` — written, and it carries the
  read-surface report as a named section.

## Bound

```
Enumeration: every KR row in perry/OKR.md, and the okr.jsonl record each one
             must be reproduced from
Size:        38 KR rows / 38 `kind: kr` records on 2026-09-12 — re-derive
Remainder:   10 `objective` records and 3 `version` records. NOT this row's
             scope: the `### Objective N` headings and the `## v<N>` blocks
             stay in the markdown, because `_parse_okr_objectives` reads the
             objective structure from those headings and attaches stored KRs
             to it. Deleting the tables does not touch that path.
Last element: the lowest-ranked KR id in your own enumeration's order
```

## Deliverable

1. `perry/OKR.md` no longer carries KR tables; `perry-goals` renders them.
2. **The read-surface report, in writing**, as a named section of the result.
   `DESIGN-013 § 5.4` risk 3 and its risk table are explicit: *the render has
   to be good enough that a human running one command sees what opening the
   file showed them*, and if the report is **negative, `TASK-237` STOPS and
   returns to the design** rather than proceeding because the decision was
   already made. Write it as a finding. Do not write it as a justification for
   having done the work, and do not write it after deciding the answer.
3. `perry/evidence/2026-09/TASK-236-result.md`: the re-run gate, the report,
   the mutations.

## What this row does not buy, and the spec says so to stop someone expecting it

Deleting the tables retires **one function in `viewer/parsers.py`**:
`_parse_krs`, 26 lines of code, and only for a project that has a store —
`_parse_okr_objectives` calls it exactly when `stored_krs is None`, which is a
project with no `okr.jsonl`. Nothing else in the reader retires. The large
parser collapse people associate with this direction is `TASK-237`'s and sits
behind `BOARD.md`, not here. Report the measured number; do not claim more.

## What it must not do

1. **It must not delete a table the render cannot reproduce.** The order is
   render first, byte-compare, then delete. Reversed, the gate evaporates —
   with the tables already gone there is nothing left to rebuild, the
   comparison passes vacuously, and nobody learns whether the store was
   complete. That is the class of defect this project has caught six times.
2. **It must not quietly change what `OKR.md` is.** `ADR-015` keeps `OKR.md`
   tier 1 — the user's, hand-editable, authored not projected. After this row
   it is a tier-1 document whose KR half is a render. **Argue that boundary in
   the report**; do not leave it to be discovered. If the argument does not
   hold, that is a finding and a reason to stop, not a detail.
3. **It must not touch `schema/state-schema.json`.** On `.perry/hook.md
   § High-stakes operations`; needs the user's authorization.
4. **It must not edit `ARCHITECTURE.md § 2`** without asking. `DESIGN-017`
   decisions 2 and 4: a change that contradicts a section stops and asks.
5. **It must not write the KR tables back.** `perry-okr render --write` would
   restore what this row removes; whatever guards that, say what it is.

## Verification

1. `perry-okr diff` re-run in your own tree **before** any edit, both keys
   `true`, quoted in the result.
2. Every one of the 38 KR rows is reachable through `perry-goals` after the
   deletion, enumerated and compared field by field against the 38 records —
   not sampled.
3. **Mutation.** Corrupt one `kind: kr` record and show a named test go red.
   Then delete a record entirely and show a different named test go red. A
   mutation that comes back green is the finding, not a footnote.
4. **The anti-vacuity check**, because this row is unusually exposed to it:
   empty `okr.jsonl` of its KR records and show the guard reddens. A guard that
   builds its expectation from the file it then compares against is the bar
   `TASK-182` already caught once.
5. The suite, with the pre-existing reds named rather than counted.

## Out of scope

- `TASK-237` (`BOARD.md` stops existing). It is gated on this row's report.
- `TASK-262`, which waits on the surface this row and `TASK-237` create.
- The objective headings and the version blocks. See Bound / Remainder.
- `phase/<NNN>-<slug>.md`'s own KR tables. Different file, different row.
