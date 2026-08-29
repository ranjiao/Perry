# TASK-050 round 8 — result

> Branch `coding/task-050-header-index`, commit `c158418`, forked from `main`
> at `6c0d041`. Written against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.

Seven rounds built a better DETECTOR and seven reviewers defeated it. This
round did not build an eighth. It shrank the surface.

---

## 1. `header_index()` — where it lives and what its contract is

**`viewer/tables.py § header_index(cells, alias=None) -> HeaderIndex`**, beside
`squash`, in the module both a writer and a reader can import without one
depending on the other.

```
header_index(cells, alias=None) -> HeaderIndex
```

- `cells` — a header row as `split_row` produced it. Raw, decoration and all.
- `alias` — optional `folded key -> canonical key`, run **after** the fold, on
  the squashed spelling. That is the only form `bin/perry-task`'s glossary is
  built in, and it is how `状态` and `Status` become one key.
- returns **`HeaderIndex`**, a `list[str]` subclass of the folded keys in
  column order. A `list` subclass on purpose: every site this replaced held
  `[squash(c) for c in cells]` and then did `zip`, `.index`, `in`, `set()`,
  `enumerate` or `==` with it, so the conversion carries no behaviour with it.
  It adds `.column(*names) -> int` (index of the first matching column, or -1;
  accepts strings or iterables of them), `.row(cells) -> dict` (pad short,
  truncate long), and `.raw` (the unfolded cells, for a caller that needs the
  spelling the project actually wrote).

**The contract is exclusivity, not convenience.** `header_index` is the only
function in this repository allowed to fold a header cell, and the check that
keeps it that way is stated over the symbol:

> `tests/test_one_header_rule.py §
> test_nothing_outside_header_index_maps_squash_across_a_row`
> — *nothing outside `header_index` maps `squash` (or its `norm` alias) across
> a row's cells.*

There is no list of variable names in that sentence and it cannot fire on a
value normalizer, because a value normalizer folds a value and not a row. That
is not an exception carved out for it; it is what the two words mean. Scalar
`squash` of a single VALUE (a `Status`, an `Outcome`) or of a canonical column
NAME being compared against a folded header is untouched and unchecked —
criterion 4.

`squash`'s own docstring now says "do not map this across a header row" and
names the test.

---

## 2. Every converted site

67 call sites across 10 files now reach `header_index`. The six the amendment
names are mutation-tested individually below; the rest are covered by the same
whole-tree scan, and two of them are mutation-tested as spot checks.

| file | sites | what they were |
|---|---|---|
| `viewer/parsers.py` | 16 | 6 row folds (3 × the parenthesised comprehension, the intake pair, `prev_cells`), 3 register-header set comprehensions, 6 scalar header tests, 1 `_column_keys` join |
| `bin/perry-task` | 23 | 21 × `[norm(h) for h in header]` / `{…}` / `[values.get(norm(h))…]`, behind a `header_keys(header)` wrapper that supplies the glossary alias; `header_language`'s per-cell loop |
| `bin/perry-lint` | 6 | the config-track header, 4 × `[norm(c) for c in header]`, the intake first-cell test |
| `bin/perry-goals` | 5 | `column_at`, `header_language`, `legacy_due_index`, `canonical_of`, the row-dict keys |
| `bin/perry_store.py` | 2 | `markdown_tables`'s fold and the drift report's |
| `bin/perry-state` | 2 | `parse_tracks`, the pack-glossary header test |
| `bin/perry-diagnose` | 1 | `md_table` |
| `bin/perry-explain` | 1 | the table-row scanner |
| `bin/perry-tasks` | 1 | the `n`-gate |
| `bin/perry-migrate` | 1 | `L.norm` over a header row |

`perry_store.markdown_tables(lines, start, end, norm)` kept its parameter and
changed its meaning: `norm` is now the alias step that runs after the one fold.
That is exact rather than approximate — `norm` is idempotent on an
already-squashed key for both callers (`squash` itself, and `perry-task`'s
`_ALIASES.get(squash(s), squash(s))`) — so the mapping it produces is
byte-for-byte the one it produced before.

### The mutations

Method for every one: anchor by **line number and exact old text**, `assert`
the old text matches before replacing (a mutation whose anchor missed reports a
meaningless OK — that has happened on this row), write, delete every
`__pycache__` in the tree, sleep 1.2s past the whole-second boundary, run the
named test, restore, and **verify the restore by `md5` against the pre-mutation
digest**. All nine restores verified. The tree after the run showed only the
intended conversion.

| # | site (verified by content) | revert | test that went RED |
|---|---|---|---|
| M1 | `viewer/parsers.py:1828` `header = header_index(prev_cells)` | `[c.strip("*` ").lower() for c in prev_cells]` | `test_header_index_is_the_only_fold::test_a_bolded_kr_header_still_yields_the_KR`, `::test_every_decorated_header_cell_reached_header_index`, `test_one_header_rule::test_no_reader_folds_a_header_cell_by_a_second_rule` |
| M2 | `bin/perry-task:6107` `row = dict(zip(header_keys(ihdr), cells))` | `[h.strip("*` ").lower() for h in ihdr]` | `test_one_header_rule::test_no_reader_folds_a_header_cell_by_a_second_rule` — offender reported: `perry-task:6107` |
| M3 | `bin/perry-task:6278` (same shape, second site) | same | same test; offender `perry-task:6278` |
| M4 | `bin/perry-tasks:926-927` `keys = header_index(…["header"], alias=ops.norm)` | the two-line comprehension | same test; offender `perry-tasks:926` |
| M5 | `bin/perry-diagnose:1825` `low = header_index(cells)` | `[c.strip("*` ").lower() for c in cells]` | same test; offender `perry-diagnose:1825` |
| M6 | `bin/perry-state:590` `low = header_index(cells)` | same | `test_one_header_rule::test_no_reader_folds_a_header_cell_by_a_second_rule`, `::test_a_header_with_decoration_on_half_the_cell_still_resolves`, `test_header_index_is_the_only_fold::test_every_decorated_header_cell_reached_header_index` |
| M7 | `bin/perry-explain:394` (spot check, not a named site) | `.strip("*` ").lower()` | `test_one_header_rule::test_no_reader_folds_a_header_cell_by_a_second_rule`; offender `perry-explain:394` |
| M8 | `bin/perry-lint:653` (spot check) | `.strip("*` ").lower()` | same test; offender `perry-lint:653` |
| M9 | `bin/perry-diagnose:1825` → **`[squash(c) for c in cells]`** — the DRIFT case: the right rule, a second copy | | `test_one_header_rule::test_nothing_outside_header_index_maps_squash_across_a_row` RED. The shape net stayed green, correctly: it is the same rule. This is the mutation that proves the symbol check is load-bearing rather than decorative. |

### `viewer/parsers.py:1828` specifically

The amendment's proof case. On `main` at `6c0d041` this line can be reverted to
the historical rule and **2882 tests stay green while a KR silently
disappears**. It cannot now, for two independent reasons and one of them is
behavioural:

```
pristine  _table_rows("| **KR** id | Text | … |")  ->  [('KR-1', 'ship it')]
mutated                                            ->  []
```

`test_header_index_is_the_only_fold §
test_a_bolded_kr_header_still_yields_the_KR` asserts exactly that pair, and
went red under M1. `test_every_decorated_header_cell_reached_header_index` went
red for the accounting reason — `**KR**` and `**Due**` stopped reaching the one
fold — and the static net went red for the shape.

---

## 3. The planting harness, in full

```
planted readers caught    : 30 of 30
legitimate shapes flagged : 1 of 8
  FLAGGED: round 7 FP1 · a MULTI-VALUE CELL split on `|`
```

Round 7 was **4 of 25 caught and 6 of 8 falsely flagged**.

**The denominator is 30, not 25, and that is a difference to read carefully.**
Round 7's twenty-five planted readers live in that round's verdict and not in
this tree, so they could not be re-run — only re-derived. What
`tests/test_header_rule_harness.py` plants is the **union** of every shape the
round 5 and round 7 reviews name: the fourteen the file already carried plus
the sixteen round 7 enumerated as escaping (`cells[1:]`, a dict-assignment
header index, a `lambda` folder, two levels of local indirection, a splitter on
a class attribute, a splitter in a dict, `cs = cells`, `sorted(key=str.lower)`,
`filter`, `out.add`, `out +=`, `zip`, a walrus, `functools.partial`,
`str.translate`, and **P21** — `parts = split_row(line)` on one line and the
comprehension on the next, the one round 7 called "the most ordinary spelling
there is"). That is a superset, so the fraction is measured against a harder
denominator than the amendment quotes. It is not the same 25 and is not
reported as if it were.

Four controls hold under it: an unplanted copy reports `[]`, the copy carries
the readers, and the round 5 decisive case (appended to `viewer/parsers.py`
itself) is reported.

### The one false positive, declared rather than excused

`[t.strip().lower() for t in cell.split("|")]` — a multi-value CELL split — is
still reported. It is left reported, and it is declared:

`tests/test_header_rule_harness.py § TestTheOneFalsePositiveIsDeclared` asserts
it fires, and `test_it_is_undecidable_and_that_is_asserted_not_argued` runs it
beside `[t.strip().lower() for t in line.split("|")]` — a home-made row
splitter, which is round 5's decisive case and what criterion 3 forbids — and
asserts the two get the **same** verdict. They differ only in the receiver's
name. Separating them means reading variable names, which is what rounds 5
through 7 did and what the amendment forbids. So it is stated as a result. The
day the design makes it decidable, that test goes red and the entry is deleted.

`TestWhatTheCheckStillCannotSee` carries the other two, with the round 7
wording finding fixed: gap 2 no longer says "and never split locally" (P21 is
split locally), it says "no provenance in this file", and
`test_the_second_gap_is_undecidable_and_that_is_the_whole_argument` runs
`def read(stuff): [c.lower() for c in stuff]` beside
`def read(aliases): [a.lower() for a in aliases]` and asserts they get the same
verdict — they are the same program up to a parameter name.

**`test_the_cross_module_case_is_the_price_of_a_file_local_walk` is deleted.**
It asserted that a phrase in its own docstring appeared in its own source file.

---

## 4. What actually closes the row, and it is not the walk

`tests/test_header_index_is_the_only_fold.py` (new, 6 tests). It wraps
`tables.squash` — one object, because there is one rule, so every alias
(`squash`, `norm`, `L.norm`, `ops.norm`) is watched by the one patch — records
each call's full stack, and runs the real readers over decorated fixtures:
`perry-state.parse_tracks`, `parsers.parse_board`, `parse_okr`,
`read_conformance`, `_parse_intake`, `_parse_user_input`, `_parse_cadence`,
`_table_rows`, `parse_top_risks`, `perry-diagnose.md_table`,
`perry-lint._track_context`, `perry-explain.harvest`.

Two assertions, and the second is the one that matters:

1. every fold of a header cell came from inside `header_index`;
2. **every decorated header cell in the fixtures REACHED `header_index`** — a
   reader that grows its own rule calls nobody, so assertion 1 alone stays
   green while the defect is live.

A cell is identified as a header cell by `arg.lower() != squash(arg)` — true
exactly when it carries `*`, a backtick or padding. Nobody writes a canonical
column name in bold, so anything that survives that test came off the document.
No function names, no variable names. `test_the_watch_is_not_vacuous` guards
the zero: it asserts more than five folds and more than three distinct cells
were seen, so "nobody else folded one" cannot be confused with "nothing was
folded" — the failure round 5's complement test died of.

The static net changed too: **`ROW_NAMES` is no longer the gate** and has not
been extended. A row is recognised by local dataflow from `split_row` —
assignment, aliasing, slicing, subscript, walrus, wrapper calls, one
element-preserving comprehension unwrap, a parameter this file passes a row to,
and **what a file-local function RETURNS**. That last one is what closes
`_, ihdr = board.section_table("Intake")` (both of round 7's `perry-task`
sites) and the `cells_of` escape the amendment names — with `cells_of` in no
list at all. `TestTheFileLocalSplitterEscapeIsClosed` plants a comprehension
over `cells_of(s)` whose result is named `probe`, so the old accident (that the
result happened to be called `cells`) cannot be what makes it pass.

`ROW_PRODUCERS` is two entries — `split_row` and `header_index` — and they are
the two functions this repository is allowed to have.

Round 7's smaller findings: `tests/test_one_header_rule.py` no longer imports
`header_rule` twice.

---

## 5. Baselines — runner and tree, before and after

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | `main` @ `6c0d041` | 98 | 2882 | 3 |
| `bash tests/run` | `c158418` (this branch) | 99 | 2893 | 3 |

The three failures are identical before and after and are pre-existing:
`test_diagnose` × 2 (`test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_perry_itself_passes_its_own_id_checks`) and
`test_kr_progress_provenance` × 1
(`test_no_current_in_the_payload_claims_to_be_a_measurement`).

+1 module is `tests/test_header_index_is_the_only_fold.py`. +11 tests is that
module's 6, `test_one_header_rule`'s 2 and the harness's 3.

`python3 -m unittest discover -s tests` disagrees with `bash tests/run` by 3 on
this repository (a module-double-import artefact identified in the TASK-095
round 1 review, not caused by this change). Both numbers above are `bash
tests/run`, the documented runner, and say so.

No write-side Perry tool was run. Nothing outside this worktree was touched.

---

## 6. What was NOT done, and what is not proven

Stated plainly, because seven rounds of this row were reported as more complete
than they were.

1. **1 of 8 legitimate shapes is still flagged**, and it is not fixed — it is
   declared, with a test asserting it is undecidable. That is one short of the
   amendment's "zero of the 8".
2. **The harness denominator is 30, not round 7's 25.** It is a re-derived
   superset, not the reviewer's corpus. A shape round 7 planted that neither
   review's prose names would not be in it.
3. **The static net is still defeasible and is not what closes the row.** Two
   gaps are asserted as escaping: a folding helper defined in another module,
   and a fold over an iterable with no local provenance. The second is provably
   undecidable and the harness asserts it against a legitimate twin.
4. **The runtime guard only sees code a parse reaches.** A planted function
   nothing calls is invisible to it. That is why both nets exist and neither is
   claimed to be complete.
5. **`bin/perry-state § cells_of` was not removed.** It delegates to
   `split_row`, so it is not a second row splitter, and the escape it created
   is closed by dataflow rather than by deleting it. Deleting it is a separate,
   larger edit to `parse_tracks`.
6. **`viewer/` was not renamed** — explicitly out of scope for this row.
7. **`perry-explain.harvest` and `perry-lint._track_context` are exercised
   through the watch, not through their CLIs.** The `--help` sweep and template
   drift guard in `bash tests/run` passed, but no reader was driven end to end
   from `argv` for this round.
8. **The three pre-existing failures were not investigated**, only measured as
   identical on both trees.
9. **No `python3 -m unittest discover -s tests` count was measured on either
   tree.** The run was started and its summary was lost to output capture, and
   it was launched against an intermediate tree rather than `f1eb3f5`, so it
   would not have described the committed state either. The statement in § 5
   that the two runners disagree by 3 is carried from the round's brief and
   from the TASK-095 round 1 review, **not** from a measurement taken here.
   Every number in § 5 is `bash tests/run`.
