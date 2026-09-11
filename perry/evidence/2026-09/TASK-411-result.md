# TASK-411 — result

> Branch: `task-411-declaration-both-ways`, merged to `main` at `a5b718b1`
> Baseline: `488cf079`
> Status: DELIVERED, awaiting V4

**Written by the PMO from the executing agent's final report, 2026-09-11, after
the row was moved to review and no evidence file existed.** The agent produced
tests and no document, so every measurement below lived only in a transcript.
That is the same gap that cost TASK-348 a complete 22-file census earlier the
same day, and it is recorded here rather than quietly repaired.

## What shipped

Nothing under `bin/` changed. Two test-side files:

- `tests/surface_reads.py` — new, 662 lines.
- `tests/test_bin_surface.py` — +306.

## One reader, three chain bodies

The four tools reduce to three dispatch bodies: `bin/perry-tasks`,
`bin/perry-config`, and `bin/perry_md_store.py` (which *is* `perry-okr` —
`DOCS` holds exactly one `Doc`, so there is one `surface(doc)` and one
`main(doc, argv)`, covered per-`Doc` rather than by name).

One derivation works because all three read a flag **by its literal spelling**
out of the `lib.parse_surface` result. So "does this subcommand read this flag"
becomes "can that spelling reach code this subcommand runs". Four mechanisms:

1. **Branch narrowing** — `if cmd == "render":` / `cmd in (…)`, nested.
2. **Fall-through** — a matched branch that always returns removes its names
   from what follows. This is the only reason `perry-tasks`' unguarded `verify`
   tail belongs to `verify`.
3. **Lazy argument binding** — a flag travels *into* a parameter and is read
   where the parameter is *used*. Without it, `cmd_render(…, write_board="--write" in flags)`
   would say `diff` reads `--write`.
4. **Discriminator propagation** — `byte_compare=cmd == "diff"` narrows inside
   the callee exactly as `cmd ==` does.

**Population is derived, nothing hard-coded**: tools by scanning `bin/` for a
`SURFACE`; the dispatch function as "the one that calls `lib.parse_surface`",
followed through `perry-okr`'s hand-off; the subcommand variable as "the local
`read["sub"]` lands in" — which is also what *excludes* `perry-task`, since it
writes an attribute and dispatches from a `COMMANDS` table.

## Two read sets, because the directions need different ones

Direction B (declared and unread) uses the permissive set. Direction A (read and
undeclared) uses the **exclusive** set — flags read where no other subcommand
goes. Asserting the permissive set for A would have demanded 15 exemptions on an
unmutated tree, which is the table-of-holes shape this row exists to remove.

## Over-report census, run in-test and exhaustive

| | |
|---|---|
| (subcommand, flag) pairs in the universe | 149 |
| pairs the declarations carry | 48 |
| pairs the reader calls read | **63 — 42.3%** |
| a vacuous reader would call read | 149 — 100% |
| false positives among the 63 | **0**, audited against source |
| direction B's blind spot | 15, all `perry-tasks` |

The 15 are `--register` on the twelve prefixed verbs and `--write` on the three
`*-diff` verbs: shared-region reads, all true. **None is § 1.4's defect, and
that is probed rather than asserted** — declaring `--register` on `risks-build`
leaves direction B green, and the tool then exits **2** with `the 'intake'
register has no 'risks-build'`. Honoured loudly, not accepted and dropped.

Separately, the exhaustive negative-space census that removes the ten-row hand
table's monopoly: **1,279 probes, 1,279 refused, 0 accepted**, now a test.

## Mutations

Ten, all reddening a named test. Four were **silent** under the pre-existing
suite: `perry-config show` gaining `--dry-run`, `perry_md_store verify` gaining
`--from-file`, and `perry_md_store write` and `render` losing theirs.

**The agent corrected the row's own claim.** The row said the suite was at
baseline for the `perry-config track` / `--wip` case; it is not —
`test_the_generated_usage_line_names_the_same_flags` catches that one. "Suite at
baseline" holds for four of the ten, not for that one.

Two supplementary mutations were chosen to land **outside** the ten-row hand
table: `risks-build` gaining `--dry-run` and `render` losing `--write`. Both red.

**Thirteen mutations of the reader itself**, all red. Three survived and were
treated as findings rather than passes: two were equivalent mutations of dead
code, removed or re-documented; the third is the unexercised half of a rule
whose other half is red, noted in the file.

## What was left, and named

`perry-state` and `perry-diagnose` declare zero subcommands, so `is_chain_tool`
skips them **structurally, not by name**. Measured clean in both directions
today — `perry-state`'s four own flags and `perry-diagnose`'s three all have
literal reads, and `perry-diagnose`'s `--porcelain`, `--name-only` and
`--is-inside-work-tree` are `git` arguments, not its own — **and nothing holds
them there.** The same gap, one level up.

`ELSEWHERE`'s ten rows were kept: they run the real tools end to end and assert
the refusal's wording. The exhaustive census removes their monopoly, not them.
`INDIRECT` is empty and a test asserts the emptiness.

## Suite

| | modules | tests | reds |
|---|---|---|---|
| before (`488cf079`) | 124 | 3556 | 3 known |
| after | 124 | 3567 | the same 3 |

`perry-lint --root .`: 0 errors. Tree guard clean.
