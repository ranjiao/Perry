# TASK-431 — spec

> Design: none. `schema § i18n.blank_cell` is the declaration this row enforces,
> and its own note records the last time this defect shipped
> Dispatch mode: auto
> Executor: claude-subagent — touches three tools' readers
> Estimated cycle: small
> Subjective verification: whether a fourth caller should be forced through the
> rule or left alone, where the cell is not a document cell
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P2 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`schema § i18n.blank_cell` exists because there were three lists in `bin/` with
three different contents, and its note says so in the schema itself: `n/a`,
`TBD`, `none`, `?` and `—` were refused by the writer and linted clean, while
`无`, `待定` and `不适用` were refused by the writer **and** reported. Same
meaning, two verdicts, split on language.

**The declaration landed and two of the three lists did not go away.** Measured
at `fe0292fb`:

| site | what it accepts as nothing |
|---|---|
| `bin/lib/__init__.py § is_blank_cell` | the schema's list, 17 spellings across two languages |
| `bin/perry-lint:354 § UNDECLARED_CELL` | a hardcoded set of 10, no Chinese |
| `bin/perry-state:301 § split_stages` | `""` and the em dash, nothing else |

V4 round 8 measured the consequence: a store record whose `stages` cell holds
`-`, an en dash, `n/a`, `N/A`, `none` or `无` makes `--compact` report
`stage_list: ['无']` with `stages_declared: true` — **a stage named after the
blank marker** — and `perry-lint`'s suspect-separator guard skips exactly those
cells, so nothing reports it.

**Why it was filed rather than failing the row**: it is not reachable through
the shipped writer. `perry-config track --stages` normalises all three blanks
to empty before they reach the store, which round 8 measured rather than
assumed. It needs a hand-edited store. That is what makes it a P2 and not a
P0; it is not what makes it safe, because a hand-edited store is a supported
state and `perry-lint` exists to read one.

## Files in scope

- `bin/perry-state` — `split_stages`, and any other site this row's sweep finds.
- `bin/perry-lint` — `UNDECLARED_CELL` and its two readers at `:1129` and `:1175`.
- `bin/lib/__init__.py` — `is_blank_cell`, read; changed only if the sweep shows
  it must.
- `tests/test_blank_cell_is_one_rule.py` — the module that already holds this
  rule's tests, and where the new ones belong.
- `perry/evidence/2026-09/TASK-431-result.md` — written.

## Bound

```
Commit:      fe0292fb — re-derive every figure in your own tree first
Enumeration: every site in bin/ and viewer/ that decides whether a cell means
             nothing. DERIVE the set: search for a comparison against any
             spelling in schema § i18n.blank_cell, and for any literal set or
             tuple of such spellings. Do not work from the three named above —
             the row was filed by a round that found three, and the row exists
             because a previous fix also believed it had found them all
Size:        3 known. State the number YOUR sweep returns, and if it is still
             3, say how you established that
Last element: the lowest-ranked site in your sweep's own order
```

## Deliverable

One rule. Every site that decides "does this cell mean nothing" answers through
`lib.is_blank_cell`, which reads `schema § i18n.blank_cell`, or the report says
which site is exempt and why the exemption is not the defect returning.

A test that fails when a **fourth** list appears. A test that enumerates the
three known sites is the same shape as the thing being removed; derive the site
set the way the Bound does and assert over it.

`perry/evidence/2026-09/TASK-431-result.md`: the sweep's method and result, the
before and after for each site, and the mutations.

## What it must not do

1. **It must not add a spelling to a list.** The schema is the declaration; a
   code edit that teaches one more tool one more word is the defect.
2. **It must not widen `is_blank_cell`'s meaning to fit a caller.** If a caller
   needs a narrower rule — `split_stages` may genuinely want only the marker,
   for a reason — say that in prose and make the narrowness explicit and
   tested, rather than leaving a second list that merely looks like an
   oversight.
3. **It must not touch `--compact`'s or `--json`'s shape.** `USER-924` assigned
   the value's correctness to the producing function, not to the projection.
   This row is that function.
4. **It must not rely on the writer's normalisation.** The whole finding is
   about a store the writer did not produce.

## Verification

1. **The reported consequence, reproduced first and then gone.** Build a store
   whose `stages` cell holds each of the six spellings round 8 named, show
   `--compact` reporting a stage named after the marker, then show it empty
   with `stages_declared: false`. Before and after, both printed.
2. **Every spelling in the schema, not a sample.** All 17, at every site.
3. **`perry-lint` reports what it used to skip.** The suspect-separator guard
   skipped exactly those cells; show it does not now.
4. **Mutation.** Restore each site's old literal one at a time and show a named
   test go red for each. A site whose restoration is green has no test.
5. **The fourth-list guard bites.** Add a new hardcoded list somewhere in `bin/`
   and show the sweep test find it.

## Out of scope

- `viewer/parsers.py`'s document parsing, unless the sweep lands there.
- Any change to `schema § i18n.blank_cell`'s contents.
- `--compact`'s field selection — that is `TASK-432`.
