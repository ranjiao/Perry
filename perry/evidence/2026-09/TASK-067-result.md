# TASK-067 — result

> Branch `coding/task-067-one-choke-point`, from `main` at `267abb1`.
> Rung: **V3** — every claim below is a run, reproduced here.
> Implements `USER-915`'s reading **(B)**. It does not re-derive the choice.

## The worktree was cut at an ancestor, and it mattered

The tool cut this worktree at **`d49964e`** — the same commit the brief says
five agents got — **134 commits behind `main`**. Verified before any work:

```
HEAD  d49964e  chore: consolidate test suite and project state
main  267abb1  TASK-067 in_progress before dispatch, not after
git merge-base --is-ancestor HEAD main -> yes;  git rev-list --count HEAD..main -> 134
```

At `d49964e` **neither criteria file exists**: `git ls-tree -r --name-only HEAD`
returns `TASK-067-finding.md` but **not** `perry/evidence/2026-09/TASK-067-spec.md`
and **not** `perry/evidence/2026-09/TASK-323-bound.py`. Both resolve at `main`.
The branch was therefore cut fresh at `267abb1` before anything was read, and
every number below is measured on that baseline. Nothing was reconstructed.

## Bound, re-derived — not inherited

`python3 perry/evidence/2026-09/TASK-323-bound.py .` at `267abb1`:

```
--- 88 member(s); 8 excluded ---
W1: 27 · W2: 18 · R1: 37 · R2: 6      last element: viewer/tables.py:280
```

**88, matching the spec's `## Bound` exactly** — the census's 89 at `5720730`
minus the one `TASK-283` deleted. The 8 exclusions split 6×E1 / 1×E2 / 1×E3.

The eight W2 separator-row builders, **at the lines measured today**, all eight
identical to the spec's list:

| site | shape |
|---|---|
| `bin/perry-goals:327` | `body + "\|" + last + "\|"` (widen, no trailing pipe) |
| `bin/perry-goals:328` | `body + last + "\|"` (widen, trailing pipe) |
| `bin/perry-goals:3093` | `"\|" + "\|".join("---" for _ in columns) + "\|"` |
| `bin/perry-task:985` | `"\|" + "\|".join(["---"] * len(widened)) + "\|"` |
| `bin/perry-task:1034` | same, `len(columns)` |
| `bin/perry-task:1112` | same, `len(widened)` |
| `bin/perry-task:5174` | same, `len(header)` |
| `bin/perry_md_store.py:774` | `"\|" + "---\|" * len(columns)` |

**One line number in the census has moved and the spec did not say so:**
`perry-lint:887` (the `" | ".join(row)[:60]` finding message) is **`:958`**
today, with no change to the code it names. It is a false positive either way.
This is why the guard's allowlist is keyed on `(file, what)` and never on a
line number.

## Before-state — and a correction to the brief

The brief asks what a `|` and a newline *did* at each site, unfixed. Reproduced
on a `git archive` copy of `267abb1`, driving each site's expression verbatim:

| plant | what landed, unfixed |
|---|---|
| column name carrying `\|` | header `\| ID \| audit \\\| then ship \| Status \|` — **3 cells**; separator `\|---\|---\|---\|` — **3 cells**. **Match.** `render_row` escapes, so the count never diverges. |
| column name carrying `\n` | `render_row` **refuses** (`cell 1: contains a line break`). The separator expression would have produced a 3-cell row, but never runs. |
| separator whose last cell holds `\\\|`, widened | header 3 cells, separator 3 cells. **Match.** |

**So the honest before-state is: no plant through the eight sites corrupted a
file.** At all six fresh-separator sites `render_row` is evaluated *before* the
separator — `perry_md_store.py:773` before `:774`, `perry-task:5173` before
`:5174`, and at `perry-task:1033` / `perry-goals:3092` inside the same list
literal — so a value it refuses takes the separator down with it.

That is not a reason to leave them; it is precisely the reason to route them.
**The agreement was an accident, not an invariant**: each site derived its count
from the same list it handed `render_row`, and `render_row` happened to run
first. Nothing enforced either fact, nothing tested either fact, and a reordered
statement or a seventh site copied from the six would have broken it silently —
which is what "(B) covers them by construction" means and what it was worth.

Anyone reporting a corrupted file from these eight sites at `267abb1` has not
run it. The finding's own census says `uncaught`, which classifies the
*builder*, not a demonstrated corruption — and the two are not the same claim.

## After-state

`viewer/tables.py` gains two functions, both routing through the choke point:

- **`render_separator(n)`** — `"|" + "".join(c + "|" for c in split_row(render_row(["---"] * n)))`.
  The count comes from `render_row`'s own output, not from `n` a second time.
- **`append_separator_cell(line)`** — moved out of `bin/perry-goals`, beside the
  `append_cell` it has to agree with, and its count is now **asserted**:
  widening adds exactly one cell or the row is refused.

**Bytes are unchanged.** All three old spellings produce identical output, and
`render_separator` reproduces it for n=1..15 (asserted). Confirmed end-to-end:
`perry-lint --root .` reports **0 row(s) drifted** in all six stores, so no
state file was rewritten and `perry_md_store`'s byte comparison does not move.
A separator rendered as `| --- | --- |` would have rewritten every table in the
repository, which is why routing was done without restyling.

The observable consequence of routing — the only one, since the bytes match —
is that the refusals are inherited: `render_separator(0)` now raises, where
`"|" + "---|" * 0` returned `"|"`.

## The guard: `tests/test_one_choke_point.py`

A rule on **one enumerable surface**, not a detector for row-shaped strings.
The classifier is `TASK-323-bound.py`'s **W2** — an AST walk that resolves
`NAME = "..."` bindings — reproduced in the test rather than imported, because
a guard that stops working when an evidence file is archived is not a guard;
`test_the_guard_agrees_with_the_census_rule` keeps the two in step and *skips*
rather than fails when the script is absent.

This is deliberately **not** an extension of `test_row_integrity.py`'s
`HAND_ROW_RE` / `SPLIT_RE`, whose own docstring records that a first version
"reported 14 offenders of which 11 were fine". `USER-904`, `USER-906` and
`TASK-285` each chose the one-symbol move over a denylist; this is the fourth.

The two W2 nodes outside the choke point that are not rows are **named with
reasons**, keyed on `(file, what)`, and `test_the_two_exempt_nodes_still_exist_and_are_still_not_rows`
fails if either stops matching — so a dead exemption cannot sit as cover for a
future real row in the same file.

- **Fires on**: the ninth hand-built row, `bin/perry-ninthrowprobe` →
  `"| " + " | ".join(cells) + " |"` — the exact join shape `test_row_integrity`
  says grep cannot tell from an alternation. Also on all three separator
  spellings, on a `SEP = "|"` indirection, and on `bin/lib/rowprobe.py` in a
  subdirectory.
- **Silent on**: `bin/perry-callerprobe`, every legitimate caller shape —
  `render_row(cells)`, `render_separator(n)`, `append_cell(line, v)`,
  `append_separator_cell(line)`, and `render_row(split_row(line) + [extra])`.

Run against the pre-fix archive copy the guard returns **13 findings across
exactly the 8 distinct `(file, line)` sites** and nothing else.

## Declared limits — where a reader of the rule finds them

**`viewer/tables.py`, module docstring, § "What `ragged-row` does NOT cover —
declared, because it is measured"**, and again in
**`tests/test_one_choke_point.py`, module docstring, § "Declared limits"**.
Those are the two files someone reading or editing the rule opens. Not filed as
caveats in an evidence document, per the spec.

They record, as measurements: `ragged-row` **fires only inside a
schema-recognised table** (control: the identical 8-cell row in an unrecognised
section gives 0 errors, so a project using `add --group` has no net at all);
present for w4–w7 and **absent** for r2/r3/r4/r7/r8; **no count-based check can
ever reach the read side**, because `.split("|", 6)` returns the right count
with truncated content; and `SPLIT_RE`'s four demonstrated blind spots —
`maxsplit`, `re.split`, a `SEP` constant, `.rsplit`/`.partition`.

`ragged-row` is named there as **not this rule's backstop**.

## Mutations — 9 planted, 7 red, **2 GREEN on the first pass**

Harness `mutate_t067_ae3e.py` (uniquely named). Every mutation anchors by line
number **with an assert on the old text** and aborts on a miss rather than
reporting a meaningless OK; `__pycache__` cleared around every run; restore
waits past the whole-second boundary and is verified byte-for-byte against
`git show HEAD:<path>`, never against the harness's own copy. Final check:
every mutated file byte-identical to `HEAD`.

| # | reverted | first pass | test that goes red |
|---|---|---|---|
| M1 | `perry-task:984` routing | red | `test_no_tool_builds_a_table_row_outside_viewer_tables` |
| M2 | `perry-task:1033` routing | red | same |
| M3 | `perry-task:1110` routing | red | same |
| M4 | `perry-task:5171` routing | red | same |
| M5 | `perry-goals:3080` routing | red | same |
| M6 | `perry_md_store.py:775` routing | red | same |
| M7 | `perry-goals:439` → private `append_separator_cell` | red | same |
| M8 | `render_separator` → hand-built `"\|" + "---\|" * n` | **GREEN** | *(none)* |
| M9 | `append_separator_cell`'s count assert → `if False:` | **GREEN** | *(none)* |

### M8 and M9 are the findings

**M8.** Replacing `render_separator`'s body with the hand-built string it exists
to remove turned **nothing** red across the whole affected suite. Two reasons,
both structural: the bytes are identical for every `n` a real caller passes, so
no round-trip or byte test can tell them apart; and **the guard exempts
`viewer/tables.py` by name — it must, or the choke point would flag itself — so
the rule cannot see inside its own module.** A choke point's interior is exactly
where a rule about choke points has no reach.

**M9.** Replacing the count assertion with `if False:` turned nothing red. The
assertion is **not** dead code: a brute-force sweep of **50526** separator-shaped
lines fires it on **9399** of them (`|`, `|---|---\`, and every line whose last
cell copied yields a different count). It was green because nothing exercised it.

Both now have tests, in `TestTheChokePointsOwnInterior`:
`test_render_separator_inherits_render_rows_refusal` (M8 → red),
`test_a_separator_row_that_cannot_be_widened_is_refused` (M9 → red, 2 subtests).
**Re-run of all nine: 9 planted, 9 red, 0 green.**

## Out of scope, confirmed still open

- **`bin/perry-decide:332`** — still present, unchanged, at line 332:
  `if isinstance(_value, str) and len(_value.splitlines()) > 1:`. It builds no
  row, so a rule about who builds rows does not reach it. **Filed as its own
  row: `TASK-327`**, as the spec directs.
- **`bin/perry-task:7431`** — `_v.strip() == exc.value`, message quality.
  Untouched, covered by neither reading.
- All 43 read-side members. (B) is a rule about who *writes* a row.

## Verification

```
python3 bin/perry-lint --root .    ->  0 error(s), 16 warning(s)
                                       0 row(s) drifted in all six stores
python3 tests/parallel -j 4        ->  3126/3126, 111 modules   (baseline 3112/3112, 110)
```

Baseline **measured, not assumed**: `3112/3112 green` at `267abb1`, 110 modules,
215.8s. **The brief's claim that "the suite has not been green all day" does not
hold at this baseline** — it was fully green before any change.

`tests/durations.json` gains `test_one_choke_point.py` at **1.52s** under a new
`task-067-one-choke-point` source stamped `ref 47ffa26`, three serial runs
(1.49 / 1.54 / 1.52) at load1 3.16, `__pycache__` cleared before each. Listing
it as `never-measured` would have been the easy path and would have been false.
