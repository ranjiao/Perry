# TASK-348 — spec

> Design: `design/DESIGN-014-how-much-python.md` § 5.1 and § 6 step 1, the
> remainder of the step `TASK-263` began
> Dispatch mode: manual
> Executor: claude-subagent — read-only measurement over Perry's own source
> Estimated cycle: large
> Subjective verification: whether the category boundary follows ADR-007, and
> whether a destination named for a file another row is deleting is a real
> destination or a deferral
> Touches architecture: (none — this row writes one report)
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: `TASK-263` — done, V3, `evidence/2026-09/TASK-263-result.md`
- **KR linkage**: declared unlinked — this serves `DESIGN-014`, not a phase-003 KR
- **Verification rung**: V4

## Why

`DESIGN-014 § 6` step 1 is "measure the split by call site", and `TASK-263`
measured two files of twenty-four. Everything else in `§ 5.1`'s three tables is
still a whole-file number, and a whole-file number cannot say which lines are
typed operations and which are re-deriving a fact out of a rendering.

`TASK-263`'s headline is what makes the remainder worth measuring rather than
assumed: across `perry-task` and `perry-lint`, **OBSOLETE REPRESENTATION was the
largest category at 2,082 lines, three times the AGENT-OWNED total of 683.**
`ADR-007` is remembered as "no regex asks prose a question", and in the two
largest files that was the smallest problem. If that ratio holds outward, the
project's remaining work is different from what `§ 5.1` assumes; if it does not,
`§ 5.1`'s tables are wrong in a way only this row can show.

**This is also `ADR-011` Tier B's measurement.** `§ 5.1`'s category B lists
`viewer/parsers.py`, `bin/perry-tasks` and `bin/perry_md_store.py` as condemned
in full. Condemned in full is a claim, and no call-site evidence stands behind
it today.

## Files in scope

This row measures; it changes no behaviour. The only file it creates is its own
report.

Read, at the commit pinned under Bound: the **22 files** below, which are every
`.py` and every executable under `bin/` and `viewer/` **except** the two
`TASK-263` already covered.

```
viewer/parsers.py 4902   bin/perry-goals 3138      bin/perry-diagnose 2818
bin/perry-state 2657     bin/lib/__init__.py 2154  bin/perry-tasks 1928
bin/perry_md_store.py 1675  bin/perry_store.py 1667   bin/perry-explain 920
bin/perry-churn 745      bin/perry-knowledge 688   bin/perry-decide 620
bin/perry-state-cost 604 viewer/tables.py 496      bin/perry-context-budget 460
bin/perry-dispatch-limit 448  bin/perry-config 386  bin/perry-restore-check 315
bin/perry-update-check 192    bin/perry-codex-preflight 150
bin/perry-detect-host 101     bin/perry-okr 68
```

Their direct tests and importers are read only to identify callers and
behaviour. They are **not** added to the line-count denominator, the same rule
`TASK-263` used.

Written: `perry/evidence/2026-09/TASK-348-result.md`.

## Bound

```
Commit:      583f024f — pin it in the report's first line and measure nothing else
Enumeration: every line, and every document-handling call site, in the 22 files
             listed above
Size:        27,132 lines. Re-derive this number in the agent's own tree before
             starting; the row was filed on 2026-09-04 against 24,005 lines
             across 21 files and the tree has grown 13% since, which is why the
             count belongs to a commit and not to the row
Denominator: the 22 files only. `bin/perry-task` (8,540) and `bin/perry-lint`
             (5,905) are TASK-263's and are excluded
Last element: the final line of `viewer/tables.py` in the sorted file list
```

## Deliverable

`perry/evidence/2026-09/TASK-348-result.md`: a per-call-site attribution of all
22 files into `ADR-007`'s four categories, in the shape `TASK-263-result.md`
already established, so the two reports compose into one census.

- **TYPED / DETERMINISTIC** — remains in Python.
- **OPAQUE DOCUMENT TRANSPORT** — may remain if it preserves the full body.
- **AGENT-OWNED INTERPRETATION** — moves to an agent workflow.
- **OBSOLETE REPRESENTATION** — moves to a typed store or manifest, or is deleted.

For every non-typed path the report names its owning function, its downstream
callers, its replacement store/manifest or agent workflow, and its deletion
dependency. Line counts per category per file, and a total.

Every line lands in exactly one category or in an explicitly named support
bucket (imports, CLI plumbing, docstrings). **The category counts plus the
support bucket sum to each file's line count.** An unexplained remainder fails.

Two questions the report must answer in prose, because they are why the row is
P0 and not a chore:

1. **Does `TASK-263`'s ratio hold outward?** Give the four totals across all 22
   files and compare them with `TASK-263`'s. Say plainly whether OBSOLETE is
   still the largest category and by what factor.
2. **Is "condemned in full" true?** `§ 5.1` category B says `viewer/parsers.py`,
   `bin/perry-tasks` and `bin/perry_md_store.py` are representation layer
   entire. Report how many of each file's lines actually land in OBSOLETE
   REPRESENTATION. If a condemned file carries typed operations nothing else
   implements, that is a finding and it changes what `ADR-011` Tier B can
   delete.

## What it must not do

1. **It must not classify by grep over a name.** `TASK-263`'s V4 recorded a
   defect for exactly one such slip. State the method used per file.
2. **It must not label a whole file.** A mixed function is split by call site.
3. **It must not name "deleted by DESIGN-013" as a destination and stop there.**
   `BOARD.md` and `OKR.md` are being deleted, so some of this code has a real
   and near destination — but a reader needs the row that deletes it and what
   happens to the call site if that row does not land. Name both.
4. **It must not change behaviour, thin anything, or delete anything.**
5. **It must not re-measure `perry-task` or `perry-lint`.** If a call site in
   scope calls into one of those, name the callee and leave it in
   `TASK-263`'s denominator.

## Verification

- By call site, never by grep. The method is stated per file.
- The four category counts plus the support bucket sum to each file's total
  line count, and the 22 totals sum to the figure re-derived under Bound.
- Every attribution is reproducible from concrete line ranges and callers. A
  reviewer picks any ten at random and can follow each one.
- Ambiguous regions are listed explicitly rather than resolved silently. Mixed
  functions are split.
- Every non-typed entry names a concrete destination. Retaining or expanding a
  prose regex is not a destination.
- **Negative control**: name at least one call site you expected to be OBSOLETE
  and found to be TYPED, or say that none was, and why that is credible.

## Out of scope

- Changing behaviour anywhere, including obvious small fixes found while reading.
  File them as rows.
- `bin/perry-task` and `bin/perry-lint` — `TASK-263`'s.
- `tests/` as a denominator.
- Acting on the census. Every move it names is a later row.
