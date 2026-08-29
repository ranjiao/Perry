# TASK-050 — V4 review round 7: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-050-spec.md`.
> Under review: `c67e5a4`. All destructive work on `git archive` exports and
> `tempfile` copies; the worktree ended clean at `c67e5a4`.

**This is the seventh failed round.** The verdict below is why the row is now
escalated to a user decision rather than a round 8.

## What holds — and it is the first round whose numbers survive independently

**The five claimed mutations reproduce exactly** — 1, 1, 1, 1, 14, each anchored
by line, `__pycache__` cleared, `PYTHONDONTWRITEBYTECODE=1`, 1.2s past the
second boundary, each reverted and SHA-verified.

**Both baselines are accurate in both runners**, against `45a355d`:

| | `bash tests/run` | `unittest discover` |
|---|---|---|
| `45a355d` | 91 modules · 2786 tests · 5 failures | 2786 · 8 failures |
| `c67e5a4` | 92 modules · 2793 tests · 5 failures | 2793 · 8 failures |

Identical failure sets. *"This is the first round of this row where the reported
numbers survive independent measurement without qualification."* Round 5's
Finding 3 is discharged.

**The shared-module claim is real.** One net, root-parameterised, both callers
pointed at planted copies. Round 5's structural defect is gone.

**`readers_under` scoping holds** — the reviewer set out to break it and could
not. 18 readers; the four skipped `bin/` files are bash; both shipped
`templates/*/bin/*` scripts were read in full and neither parses a table header.

## Finding 1 — the FAIL. Four LIVE header resolutions revert to the defect, suite green

The reviewer inverted the question: not *"does the check see a file I invent?"*
but *"of the header resolutions this tree already contains, how many can it
see?"*

| live site | what it is | guard |
|---|---|---|
| `viewer/parsers.py:1827` | `header = [squash(c) for c in prev_cells]` in `_table_rows` | **GREEN** |
| `bin/perry-task:6029` | `dict(zip([norm(h) for h in ihdr], cells))` | **GREEN** |
| `bin/perry-task:6200` | same, second site | **GREEN** |
| `bin/perry-tasks:925` | `keys = [ops.norm(h) for h in …["header"]]` | **GREEN** |
| `bin/perry-state:180` | scalar glossary header test | **GREEN** |
| `viewer/parsers.py:428` | scalar — **the fifth copy** | **GREEN** |
| `bin/perry-state:584` | `low = [squash(c) for c in cells]` | red |
| `bin/perry-diagnose:1825` | `low = [squash(c) for c in cells]` | red |

Two of eight. *"The reason is visible and it is not a shape"* — the two red ones
iterate a variable literally named `cells`, which is in `ROW_NAMES`.
`prev_cells` and `ihdr` are not.

**`viewer/parsers.py:1827` is not hypothetical and it loses data.** Its own
docstring says *"Header keys are `squash`ed — the one rule every Perry tool
normalizes a header cell by."* It feeds `_parse_krs` and the `Top risks` parser
— user-authored documents. Reverted to the historical rule:

```
pristine  _parse_krs -> [('KR-1', 'ship it')]
mutated   _parse_krs -> []
```

The KR is silently gone — the spec's own opening defect, in a live file — and
`bash tests/run` reports 2793 tests with the same 5 failures as the unmutated
tree.

**The measured denominator:** of **829** mapping constructs in the 18 readers,
the check classifies **59** as a row-cell source, and **35 of those 59 are the
single identifier `header`**.

> Round 3's diagnosis was *"it matches a spelling, not a shape."* The spelling
> has moved from a regex alternation into `ROW_NAMES`, an eleven-name
> `frozenset`. Everything downstream of it is a genuine AST walk; the gate in
> front of it is still an allowlist of variable names.

## Finding 2 — 21 of 25 planted readers escape, and round 5's case still works

Four controls planted at the identical paths were all red, so every escape is
about the shape. Escapes include: `cells[1:]`; a dict-assignment header index; a
`lambda` folding helper; two-level local indirection; a splitter on a class
attribute or in a dict; an aliased row parameter (`cs = cells`);
`sorted(key=str.lower)`; `filter`; `out.add`; `out +=`; `zip`; a walrus;
`functools.partial`; a scalar header-row test; `str.translate`; and P23–P25,
round 4's `_is_python` hole, carried forward untouched.

**P21 is the one that matters:**

```python
def parse_foreign_header_v2(line):
    parts = split_row(line)
    return [c.strip("*` ").casefold() for c in parts]
```

`split_row` on its own line — *"the most ordinary spelling there is, and the one
the tree itself uses at `bin/perry-state:579`"* — and round 5's decisive case is
back, in the same file, against the same rule.

## Finding 3 — my declared gap carries a false qualifier

Both `UNCAUGHT` assertions are honest, and stating gaps as executable assertions
is *"a real improvement over round 5"*. The reviewer failed the round on the
**wording**: gap 2 says *"an iterable named nothing like a row **and never split
locally**"*. P21 is split locally and escapes; so do `cs = cells`, `cells[1:]`,
`zip(cells, values)`. That is a bound written as a description — a smaller
instance of exactly what round 5 failed for.

Worse: `test_the_cross_module_case_is_the_price_of_a_file_local_walk` asserts
that a phrase appears in its own source file. *"That is structurally the test
round 5 condemned … reintroduced. The commit message says the docstring-grep
test is DELETED; a different one is present."*

## Finding 4 — the check now reports CORRECT code

Criterion 4's stated failure mode. Six of eight legitimate shapes flagged,
including **FP1**, `[t.strip().lower() for t in cell.split("|")]` — verbatim the
*"latent risk, recorded not charged"* round 5 wrote down. *"It moved from latent
to live in the version that was supposed to answer that review."*

And one character from firing on live code: adding `.lower()` to
`bin/perry-knowledge:242`'s prose tokenizer would report a keyword extractor
that has never seen a table as *"header cells folded by a second rule"*.

> So the check is simultaneously **blind to four of this tree's own header
> resolutions** and **loud about a keyword tokenizer**. Those are the two
> failure modes the spec names, in one artefact.

## Smaller, reported because they are results

- The commit message says *"17 planted shapes … 13 flagged, 4 clean"*; the
  shipped corpus is 14 + 4 = 18 plus the decisive-case class. The tests pass;
  the prose does not match the file.
- `tests/test_one_header_rule.py` imports `header_rule` twice.
- `bin/perry-state:568` defines a file-local splitter `cells_of`;
  `is_row_cell_source` resolves local helpers on the folding side but not the
  source side, so a comprehension over `cells_of(s)` would escape — safe today
  only because the result is assigned to a variable named `cells`.

## Verdict

```
=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md
proof: viewer/parsers.py:1827 — `header = [squash(c) for c in prev_cells]`, in
       `_table_rows`, whose docstring calls it "the one rule every Perry tool
       normalizes a header cell by". Reverted to `.strip("*` ").lower()` it is a
       second header rule on live user documents, `offenders()` returns [], and
       `bash tests/run` reports the same 5 failures as the unmutated tree.
       Behaviourally `| **KR** id | … |` yields [('KR-1','ship it')] pristine and
       [] mutated. The cause is tests/header_rule.py:86-88, ROW_NAMES, an
       eleven-name allowlist not containing `prev_cells`; the same gate leaves
       bin/perry-task:6029, :6200 and bin/perry-tasks:925 green under the
       identical revert, and lets 21 of 25 planted readers through — including
       `parts = split_row(line)` on one line and the comprehension on the next.
       In the other direction the same check reports correct code:
       `[t.strip().lower() for t in cell.split("|")]` is flagged.
=== END VERDICT ===
```
