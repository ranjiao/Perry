# TASK-050 round 9 — result

> Branch `coding/task-050-header-index`, forked from `main` at `6c0d041`.
> Written against `perry/evidence/2026-08/TASK-050-spec.md § Amendment
> 2026-08-29 — USER-904, option C`, which binds.
>
> **This document supersedes `TASK-050-round8-result.md`**, which is now a
> retraction note pointing here. There is one result of record.

**Every number below is labelled.** A number with a runner and a tree beside it
was measured in this round, by me, and the file it came out of is named. A
number carried from another document says so in the same sentence. That
labelling is not decoration: round 8 failed in part for a retraction that added
a footnote and left the retracted sentence standing one section up, and for a
"67 call sites" that its own table contradicted.

Round 8 was FAILed on three things. **Two of the three fixes are deletions**,
and the reviewer had already measured the way out of both.

---

## 0. What changed, in one list

| # | change | why |
|---|---|---|
| 1 | `tests/header_rule.py § offenders` — **the shape net — is deleted**, with `ROW_NAMES`, the `("header","headers","hdr")` subscript test, `_local_folders`, `FOLDING_METHODS`, `_string_constants` and `_splits_on_pipe` | it is what rounds 5–7 were failed for, and round 8 kept it gating the suite next to the check that replaces it |
| 2 | `offenders_by_symbol` gained a **scalar half** and lost every heuristic | round 8's reviewer: the scalar class was outside both nets *by construction* |
| 3 | two **live** sites converted, found by (2): `bin/perry-lint:339`, `bin/perry-task:1339` | the one rule was still being applied to a header cell outside `header_index` |
| 4 | `is_python` asks the parser; `readers_under` walks the whole tree | round 4's hole, carried untouched through rounds 5, 6, 7 and 8 |
| 5 | `tests/test_header_rule_harness.py` **rebuilt** from the round 4, 5 and 7 reviews' prose, every entry quoting its source line, no re-used labels | the pruned denominator is what failed round 8 |
| 6 | `bin/perry-diagnose § md_table` stops pre-stripping decoration; the runtime watch drives five readers round 8 never executed; `WATCHED` is asserted | round 8's Findings 3 and 4 |

---

## 1. Failure 2 — the defeated shape net is DELETED

Round 8 shipped two nets. The reviewer's finding, quoted:

> Appending an ordinary multi-value-cell normalizer to a real reader turns
> `bash tests/run` RED, and one of the two failing tests is named
> `test_value_normalizers_are_not_flagged`.

and, in the same review, the exit the round never took:

> **Net 1 alone is clean on all eight shapes.**

`offenders()` is gone. `tests/test_one_header_rule.py §
test_no_reader_folds_a_header_cell_by_a_second_rule` is gone with it, and
`test_value_normalizers_are_not_flagged` now asserts `offenders_by_symbol` over
the same ~30 folding comprehensions.

### Does any allowlist survive? No allowlist of variable names, anywhere.

Round 8's result said *"`ROW_NAMES` is no longer the gate and has not been
extended"*, and round 8's reviewer measured that it was still load-bearing for
eight of thirty catches. It is now **deleted**, along with the second one the
reviewer found at `header_rule.py:357-360`.

`grep -rn "ROW_NAMES" tests/ bin/ viewer/` on the round 9 tree returns **four
lines, all prose saying it was deleted, and no code.** These are the name sets
that remain, in full, so the answer can be checked rather than believed:

| set | contents | what kind of name |
|---|---|---|
| `BLESSED` | `squash`, `norm`, `header_index`, `header_keys` | **function** names — the design |
| `THE_RULE` | `squash`, `norm` | the one rule and its alias |
| `ROW_PRODUCERS` | `split_row`, `header_index` | the two functions this repository is allowed to have |
| `ITERABLE_WRAPPERS` | 9 Python builtins (`enumerate`, `zip`, …) | builtin names |
| `NOT_A_READER` | `tests`, `.git`, `__pycache__`, `.perry` | directory names, each with a stated reason |
| inline, in `source()` / `cell()` / `_mapping_sites` | `strip`, `lower`, `map`, `append`, … | `str`/`list` **method** names, for following a value through a chain |

**No entry in any of them is a variable name**, which is what the amendment
forbids: *"It must not need an allowlist of variable names."* A row is now what
`split_row` or `header_index` produced, followed through local dataflow, and
nothing else.

### What the deletion loses, measured

The shape net saw a reader that invents its **own** rule
(`[c.strip("*` ").lower() for c in cells]`). The symbol net cannot: such a
reader calls no blessed symbol. That loss is not described, it is planted:
`SECOND_RULE` in the rebuilt harness is 41 shapes, each quoting the review that
named it, each asserted to escape. **0 of 41 caught** (§ 3).

What covers that class instead:

1. **The function.** There is one `header_index`, so there is nothing for a
   second rule to be a second copy *of*. That is the amendment's whole thesis
   and it is not a net.
2. **`tests/test_header_index_is_the_only_fold.py`**, which asks the
   complementary question — *did every decorated header cell reach
   `header_index`?* A reader that grows its own rule stops reaching it.
   Measured: reverting `viewer/parsers.py:1833` to the historical rule reddens
   three named tests (§ 2, R9-4), and on `main` the same revert is silent.
3. **Criterion 3's own guard**, for the one shape the deletion is most often
   asked about. `tests/test_row_integrity.py §
   test_no_tool_splits_a_row_on_a_raw_pipe` reports a bare `.split("|")`
   anywhere in `bin/` or `viewer/` — receiver-blind, so it covers both
   `line.split("|")` and `cell.split("|")`. **Round 8's declared false positive
   was therefore on code this repository already forbids for an unrelated
   reason**, which is a further argument that keeping the net bought nothing.
   `tests/test_header_rule_harness.py §
   test_the_row_splitter_half_is_owned_by_criterion_3` asserts that lean so it
   cannot rot.

### The false-positive test now asserts what it claims

Round 8's reviewer:

> The test that "asserts undecidability" only asserts the two cases get the
> SAME verdict — which any name-blind check satisfies, including one that flags
> neither.

`test_it_is_undecidable_and_that_is_asserted_not_argued` is deleted. In its
place, `test_the_multi_value_cell_normalizer_is_not_reported_either_way`
asserts the stronger and now-true thing: **both are silent**, each checked
individually, because neither is a row unless `split_row` produced it. And the
whole of `CLEAN` — 12 shapes — is asserted individually rather than one being
excused.

**Measured that the deletion is what buys it (R9-9):** putting the
`.split("|")` row inference back — five lines — turns
`test_each_clean_shape_is_left_alone` RED, naming `C06`. The criterion-4
property is a consequence of the design, not a declaration.

---

## 2. The mutations

`scratchpad/r9work/mut_r9_uniq.py`, run once, on the worktree, against
`git status --porcelain` empty. Uniquely named and lock-guarded: two nights ago
an agent ran two instances of its own harness against one worktree and each
took the other's mutation as its `original`. Every mutation is **anchored by
line number and asserted against the exact old text** before replacing; every
``__pycache__`` cleared; 1.2 s past the whole-second boundary;
`PYTHONDONTWRITEBYTECODE=1`; restored and **`md5`-verified against the
pre-mutation digest**. **All ten restores verified.** Full log:
`scratchpad/r9work/mutations-run.txt`.

An earlier attempt was killed by a 10-minute tool timeout **with a mutation
still applied**; it was found by `git status`, reverted by hand against the
exact text (not by `git checkout`), and the harness now arms an `atexit` +
`SIGTERM` restore before each mutation. Reported because it is the failure the
brief names.

| # | site | revert | named test(s) that went RED |
|---|---|---|---|
| R9-1 | `bin/perry-lint:348` `value = key` | `value = norm(key)` | `test_nothing_outside_header_index_maps_squash_across_a_row`, `test_value_normalizers_are_not_flagged` |
| R9-2 | `bin/perry-task:1343` `zip(folded, keys)` / `== cell_key` | `zip(keys.raw, keys)` / `== squash(cell)` | same two |
| R9-3 | `bin/perry-diagnose:1836` `header_index(raw)` | `header_index(cells)` | `test_every_reader_this_module_claims_to_watch_actually_folds_one` |
| R9-4 | `viewer/parsers.py:1833` `header = header_index(prev_cells)` | `[c.strip("*` ").lower() for c in prev_cells]` | `test_a_bolded_kr_header_still_yields_the_KR`, `test_every_decorated_header_cell_reached_header_index`, `test_every_reader_this_module_claims_to_watch_actually_folds_one` |
| R9-5 | `tests/header_rule.py:522` the scalar half | disabled | `test_each_drift_shape_is_caught` ×5 — `D04`, `D05`, `D09`, `D10`, `D11` |
| R9-6 | `tests/header_rule.py:131` `is_python` | round 8's `if p.suffix: return False` | `test_each_drift_shape_is_caught` — `D21` |
| R9-7 | `tests/header_rule.py:163` `readers_under` | round 8's `bin/` + `viewer/` walk | `test_each_drift_shape_is_caught` — `D22`; `test_the_control_is_caught_at_every_path_the_corpus_uses` |
| R9-8 | `tests/header_rule.py:338` `by_name` lookup | round 8's `self.funcs` lookup | `test_each_drift_shape_is_caught` — `D10` |
| R9-9 | `tests/header_rule.py:372` (add) the `.split("|")` row inference | put back | `test_each_clean_shape_is_left_alone` — `C06` |
| R9-10 | `tests/test_header_rule_harness.py:715` label `S41` | re-used as `S01` | `test_no_label_is_re_used_for_a_different_shape` |

Which entries each mutation loses was measured separately, on a `git archive`
export at `scratchpad/r9work/mutcopy`, by running the harness's own `measure()`
under each mutation. That is where the per-label attribution in the table comes
from; it is not inferred from the subtest count.

### The two LIVE sites the scalar half found

Round 8's reviewer said the scalar class was outside both nets by construction
and asked whether the guard is meant to cover it. **It is, it now does, and
covering it found two live sites round 8 left converted-looking and unconverted:**

- **`bin/perry-lint § canonical_column`** read `value = norm(header)`. Its one
  caller, `_track_context:658`, already hands it `header_index`'s own output, so
  the fold was a redundant re-application of the one rule to a header cell — one
  edit away from `.strip("*` ").lower()` and the divergence this row exists to
  close. Now `value = key`.
- **`bin/perry-task § header_language`** read
  `for cell, key in zip(keys.raw, keys)` and then `squash(cell)` — folding the
  raw header cell a second time instead of reading the fold it had just made.
  Now `folded = header_index(header)` and the comparison is against
  `cell_key`. `header_index(header)[i]` **is** `squash(header[i])` by
  construction (`viewer/tables.py:384`), so the value is identical; the glossary
  alias is deliberately *not* applied on this side, which is why a second index
  is built rather than `keys` reused.

Neither was visible to round 8's nets: `canonical_column` folds through one
level of indirection with no comprehension at the fold site, and
`header_language` folds a scalar.

---

## 3. Failure 1 — the corpus, rebuilt with its provenance

Round 8 reported *"30 of 30"* against a corpus it called *"the UNION of every
shape the round 5 and round 7 reviews name"* and *"a superset of round 7's
corpus"*. Its reviewer measured that it was neither, and put the honest
denominator at **30 of at least 33**.

The corpus is rebuilt **from the reviews' own prose**, not from the previous
corpus, under three rules that are themselves asserted:

1. **Every entry quotes the review line it comes from** —
   `test_every_entry_carries_its_provenance`.
2. **No label is ever re-used** — `test_no_label_is_re_used_for_a_different_shape`,
   over both the full label and its key. That is the exact mechanism that hid
   round 8's pruning (`P23`–`P25` re-used for three different shapes), and
   R9-10 mutation-tests it.
3. **No two entries are planted at the same path** —
   `test_no_two_entries_are_planted_at_the_same_path`.

### The three fractions, measured

Run: `python3 tests/test_header_rule_harness.py` on the round 9 worktree.

```
DRIFT       caught  : 24 of 24
CLEAN       flagged : 0 of 12
SECOND_RULE caught  : 0 of 41 (+2 the reviews do not name)
                      — zero is the DECLARED limit, not a failure
```

- **`DRIFT` 24 of 24** — the one rule applied to a header row, or to a cell of
  one, outside `header_index`. This is the class the amendment writes the
  requirement about. It includes both shapes round 8's reviewer planted and
  found escaping (`D04`, `D05`, and the scalar test on a `header` variable is
  `S40`'s drift twin `D11`) and all three of round 4's `_is_python` /
  scope holes (`D20`, `D21`, `D22`).
- **`CLEAN` 0 of 12** — up from round 8's 1 of 8, and the corpus is larger:
  round 7's eight, plus `C06` (the same multi-value cell folded through
  `squash` itself — the harder version, which only the row inference could get
  wrong), plus `C10`/`C11` (scalar `squash` of a canonical name and of a value,
  which the new scalar half must not touch), plus `C01` and `C12`.
- **`SECOND_RULE` 0 of 41** — every shape the round 4, 5 and 7 reviews name,
  asserted to escape, each entry naming its source. This is the cost of
  deleting the shape net and it is stated as a number.

### The denominator, and what is not in it

| source | shapes planted |
|---|---|
| round 2 / round 3 findings | 3 |
| round 4 verdict (incl. both `_is_python` holes) | 10 |
| round 5 review, Finding 1 (cases A, C, D, E, F, G, H) | 7 |
| round 5 review, Finding 2 (the decisive case) + `map()` | 2 |
| round 7 review, Finding 2 (its full escape list, incl. P21) | 17 |
| round 8 review, Finding 1 (the shapes it re-derived) | 2 |
| **planted total (`SECOND_RULE`)** | **41** |
| named in a review but **not reconstructible** | **2** |

The two are round 5's probe cases `B` and `I`: its Finding 1 says *"a nine-case
probe and five escaped both nets"* and its table names seven of the nine.
Cases `B` and `I` appear in no sentence of that review, so there is nothing to
derive. They are **counted in the denominator and not planted**, and
`UNRECOVERABLE = 2` says so in the file. Inventing a shape and labelling it `B`
is exactly the substitution that hid round 8's pruning.

So: **41 planted, at least 43 named, against round 8's claimed 30 and honest
33.**

### The controls, which is what makes a zero readable

`test_the_control_is_caught_at_every_path_the_corpus_uses` plants one offending
body — the same one — at **every distinct directory the corpus uses**
(`bin/`, `bin/lib/`, `viewer/`, `packs/`) and requires each to be caught. Round
8's reviewer used exactly this method to expose the pruning; without it,
"escaped" and "the scan never looked here" are the same result. R9-7
mutation-tests it: narrowing `readers_under` back to `bin/` + `viewer/` turns
that control red.

Offender strings are now `path:line: source` with the path **relative to the
scanned root** rather than the bare filename, because this corpus plants the
same shape at four directories and a basename match cannot tell them apart.

### Is the guard meant to cover scalar folds? Yes — and the limit is stated

The **drift** half covers them: `squash(cells[0])`, `squash(row[0])`, a scalar
fold of a loop variable, a fold through a file-local helper or a `lambda` — all
in `DRIFT`, all caught, and R9-5 shows the code that catches them is
load-bearing for five of the twenty-four.

The **second-rule** scalar shape — `cells[0].strip("*` ").lower()`, the exact
shape of the "fifth copy" — is `S39`/`S40` and it **escapes**, like every other
second-rule shape. It is not a special case; it is the same declared limit.
Round 8's reviewer named a live instance at `viewer/parsers.py:2582`
(`parse_decisions`): rounds 3 and 4 established it is dead code, and I have not
changed it — it is out of this row's scope and is recorded here so the next
round does not have to rediscover it.

---

## 4. Failure 3 — the runtime watch stops listing readers it cannot see

**Finding 3, fixed rather than removed.** `bin/perry-diagnose § md_table` was
one of twelve readers round 8's evidence said the closing test watches, and it
recorded **zero** folds, because it pre-stripped decoration with its own
`c.strip("*` ")` before calling `header_index`. It now hands `header_index` the
**raw** cells and keeps the stripped ones for the values. Same keys — `squash`
treats `*` and a backtick as whitespace, so `squash(c.strip("*` ")) ==
squash(c)`, which is round 8's reviewer's own observation — and the reader is
visible: **4 recorded folds, up from 0.** R9-3 mutation-tests it.

**Finding 4, narrowed.** Round 8's reviewer measured that the workload never
executed `bin/perry-task`, `bin/perry-goals`, `bin/perry-tasks`,
`bin/perry_store.py` or `bin/perry-migrate` *at all*. Five of those are driven
now: `perry-task.header_language`, `perry-goals.header_language`,
`perry_store.markdown_tables`, `perry_md_store.scan_okr` and
`perry-migrate.fix_tables`. `bin/perry-migrate` could not be loaded at all
before — its `@dataclass` resolves the class's own module out of `sys.modules`
— which is why `load()` now registers before `exec_module`.

**And the list is now an assertion.** `WATCHED` names 15 functions and
`test_every_reader_this_module_claims_to_watch_actually_folds_one` requires
every one to appear in the recorded call stacks. A reader cannot be claimed as
watched without being watched. Measured census on the round 9 tree, by function
(this is a measurement, not an assertion — the counts move with the fixtures):

```
8 harvest (perry-explain)      2 is_risk_register_header    1 _parse_task_table
4 _parse_cadence               2 _table_rows                1 read_conformance
4 md_table (perry-diagnose)    2 _parse_intake              1 _track_context (perry-lint)
2 header_language (task+goals) 2 _parse_user_input          1 parse_tracks (perry-state)
1 header_keys (perry-task)     1 markdown_tables            1 fix_tables (perry-migrate)
```

`bin/perry-tasks` is the one converted reader still not driven: its site needs a
live `Board` and an `ops` module. Stated, not glossed.

---

## 5. Baselines — every one measured here, with its runner and its tree

Nobody had measured `python3 -m unittest discover -s tests` on either tree.
It is measured now, on both, and it settles the sentence round 8 retracted.

| runner | tree | how | modules | tests | failures |
|---|---|---|---|---|---|
| `bash tests/run` | `main` @ `6c0d041` | `git archive` export | 98 | 2882 | 3 |
| `bash tests/run` | round 9 (`HEAD` of this branch) | the worktree, clean | 99 | 2895 | 3 |
| `python3 -m unittest discover -s tests` | `main` @ `6c0d041` | `git archive` export | — | 2882 | **6** |
| `python3 -m unittest discover -s tests` | round 8 @ `68e63cf` | `git archive` export | — | 2893 | **6** |
| `python3 -m unittest discover -s tests` | round 9 (`HEAD`) | `git archive` export | — | 2895 | **6** |

Outputs: `scratchpad/r9work/run-main-6c0d041.txt`,
`run-r9-worktree.txt`, `discover-main.txt`, `discover-branch-68e63cf.txt`,
`discover-r9.txt`.

**The two runners differ by exactly 3, on every tree, and the three are named.**
`bash tests/run` reports:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

`discover` reports those three plus
`test_risks_store.TestTheReadersAreOneFunction` × 3
(`test_the_bullet_and_placeholder_rules_are_one_object`,
`test_the_columns_are_one_list`,
`test_the_register_header_predicate_is_one_object`).

Round 8's § 5 asserted this disagreement and round 8's reviewer failed the round
because it was carried, not measured, and because `68e63cf`'s § 6.9 retracted it
in a footnote while leaving the sentence standing. **It is now measured, on
three trees, and it is true**; the module is `test_risks_store`, which is the
same module round 5's reviewer independently identified as a `discover`
double-import artefact. Not caused by this change: identical on `main`.

**The +13.** 2895 − 2882 = 13 over `main`, and it reconciles exactly against
round 8's +11: `tests/test_header_index_is_the_only_fold.py` 6 → 7 (the census
test), `tests/test_header_rule_harness.py` 10 → 12, and
`tests/test_one_header_rule.py` 14 → 13 (the deleted shape-net test).
11 + 1 + 2 − 1 = 13.

**The three failures are pre-existing and identical on both trees** — measured,
not assumed, on the two `bash tests/run` rows above. The two `test_diagnose`
failures are board-state-dependent; both trees here carry the same committed
board, which is why they appear on `main` too.

### Call sites — the number round 8 got wrong

Round 8's § 2 prose said *"67 call sites across 10 files"* while its own table
summed to 58. **Measured on `git archive` exports of both trees**, counting
`header_index(` and `header_keys(` outside `def`/`import`/comment lines:

| tree | total | of which |
|---|---|---|
| round 8 @ `68e63cf` | **58** | `perry-task` 23, `parsers.py` 16, `perry-lint` 6, `perry-goals` 5, `perry_store.py` 2, `perry-state` 2, `perry-tasks`/`perry-migrate`/`perry-explain`/`perry-diagnose` 1 each |
| round 9 (`HEAD`) | **59** | the same, plus `header_language`'s new `header_index(header)` in `perry-task` |

So round 8's **table was right and its prose was wrong**; 67 is not derivable
from anything. One of the 58 is `header_keys`'s own call to `header_index`, so
57 are call sites in readers and one is the wrapper's hop.

`readers_under` returns **20** files on the round 9 tree (18 under round 8's
`bin/`+`viewer/` scope, plus `templates/knowledge-base/bin/kb-lint` and
`templates/ops/bin/deliverable-lint`).

---

## 6. What was NOT done, and what is not proven

Stated plainly, because eight rounds of this row were reported as more complete
than they were.

1. **The static net cannot see a second RULE, and that is now 0 of 41
   measured**, not a sentence. If the next reviewer's position is that a static
   category check is required by criterion 1, this round does not provide one
   and says so — the amendment replaced that requirement with a symbol check
   and this is the symbol check.
2. **The runtime watch only sees code a parse reaches.** Five more readers are
   driven than in round 8 and the reader list is asserted, but a fold in a
   branch these fixtures do not take, or for a **ninth** column beyond the eight
   in `HEADER_KEYS`, is still invisible. `bin/perry-tasks` is converted and not
   driven.
3. **Round 5's probe cases `B` and `I` are unrecoverable** and are counted, not
   invented. § 3.
4. **`viewer/parsers.py:2582` (`parse_decisions`) is untouched** — a live
   instance of the scalar second-rule class, established as dead code by rounds
   3 and 4. Not in scope; recorded so it is not rediscovered.
5. **`bin/perry-state § cells_of` was not removed** and `viewer/` was not
   renamed (TASK-232). Unchanged from round 8.
6. **The three pre-existing failures were not investigated**, only measured as
   identical on both trees under both runners.
7. **No reader was driven end-to-end from `argv` in this round.** Round 8's
   reviewer did that himself across four CLIs on a 64-cell half-bolded fixture
   and found it byte-identical; that result is **carried from the round 8
   review**, not re-measured here. `bash tests/run`'s `--help` sweep, template
   drift guard and the two sample-project lints did run, on the round 9 tree.
8. **The mutation harness's own "TREE AFTER" line printed `DIRTY`.** That is
   the harness's lockfile, which it deletes after the check — a bug in the
   scratch tool, not a tree state. `git status --porcelain` on the worktree
   immediately afterwards was empty, and all ten `md5` restores verified.
9. **`squash`'s docstring still says "do not map this across a header row"**,
   which after this round is half the rule; the scalar half is not mentioned
   there. A one-line docs edit, not made, so that this round's diff stays what
   it says it is.
