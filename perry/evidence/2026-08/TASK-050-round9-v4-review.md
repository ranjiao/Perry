# TASK-050 — V4 review round 9: **FAIL**

> Fresh-context reviewer, 2026-08-30, against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.
> Under review: `b5e7be3`, tip of `coding/task-050-header-index`, in the
> read-only worktree at `scratchpad/review-050r9`. **Every plant, mutation and
> suite run below happened on `git archive` exports and `cp -R` copies under
> `scratchpad/v4r9-rj/`**, never on the reviewed tree. No write-side Perry tool
> was run. No identifier was minted. The reviewed worktree was verified
> byte-identical to its commit at the start and again at the end.

**This is the ninth failed round, and it does not fail for round 8's reasons.**
All three of round 8's findings are genuinely closed: the corpus is rebuilt with
auditable provenance and I could not find a shape it pruned; the shape net is
gone; the retraction is now the whole document rather than a footnote. The
conversion is real, all ten of the round's mutations reproduce, and I could not
find a converted site the tree cannot see.

It fails because **deleting the shape net puts the entire static claim on the
drift half, and the drift half is not stated over the symbol — it is stated over
the symbol's spelling.** A one-line rebinding of `squash` to any name other than
`norm` maps the one rule across a header row, outside `header_index`, with every
guard this row ships reporting nothing.

---

## THE RULING THIS REVIEW EXISTS FOR: 0 of 41 on `SECOND_RULE` is ACCEPTABLE

I rule for the author on this, and the argument is not "the amendment lets him
off" — it is that the amendment *chose* this trade with its eyes open and round
9 is the first round to price it honestly.

1. **The amendment names the alternative and rejects it.** "Option A, widening
   the source-expression recognition for an eighth round" is explicitly
   rejected; "four rounds have now moved the defect this way." Catching a
   reader that writes `[c.strip("*` ").lower() for c in cells]` *is* source-
   expression recognition — there is no other way to see a fold that calls
   nothing. A reviewer who fails the round for 0 of 41 is ordering option A.
2. **The amendment defines the guard as a one-symbol check** — "no call to
   `squash` on a row cell exists outside `header_index()`. State it over the
   symbol, not over a shape." A symbol check is blind to a shape by
   construction. 0 of 41 is the arithmetic of that sentence, not a shortfall
   against it.
3. **The two halves are the same trade, and I measured that they are.** The
   amendment requires the criterion-4 false positive to "go away **as a
   consequence of the design**, not by adding exceptions." Mutation R9-9
   reproduces exactly: putting the `.split("|")` row inference back turns
   `test_each_clean_shape_is_left_alone` RED on `C06`, quoting
   `["bin/perry-probe-c06:4: [squash(t) for t in cell.split('|')]"] != []`. The
   inference that would let the net see more second rules is precisely the
   inference that reports correct code. You cannot have 41 of 41 and 0 of 12.
4. **The row's own subject is not left uncovered — it is covered dynamically.**
   The title is "one normalization, not two", and a reader that *writes* a
   second one stops reaching `header_index`. That is caught:
   `test_every_decorated_header_cell_reached_header_index` goes RED under R9-4
   (reverting `viewer/parsers.py:1833` to the historical rule) and it went RED
   under my own probe that replaced the same site with a *value-identical*
   alias fold, naming `['due', 'kr']`. So the second-rule class is seen at
   runtime for the readers the workload drives; it is the static net that is
   blind, and the static net is not what the amendment asked to close the row.
5. **Round 8's supporting argument for the deletion holds, and I verified its
   reach rather than taking it.** `tests/test_row_integrity.py §
   test_no_tool_splits_a_row_on_a_raw_pipe` really is receiver-blind and really
   does cover the whole of `bin/` and `viewer/`: `SPLIT_RE =
   re.compile(r"\.split\((['\"])\|\1\)")`, `_tools()` is `rglob("*")` over both
   directories with `EXEMPT = {"viewer/tables.py"}` and no other exclusion.
   Appending round 8's exact declared false positive to a copy:

   ```
   $ # appended to bin/perry-explain in scratchpad/v4r9-rj/fp-probe (a copy):
   $ #   def owners_of(cell):
   $ #       return [t.strip().lower() for t in cell.split("|") if t.strip()]
   $ python3 -m unittest discover -s tests -p 'test_row_integrity.py'
   FAIL: test_no_tool_splits_a_row_on_a_raw_pipe
   AssertionError: Lists differ: ['bin/perry-explain:796'] != []
   Ran 33 tests in 1.102s
   FAILED (failures=1)
   ```

   Round 8's false positive was on code the repository already forbids for an
   unrelated reason. Keeping the shape net for it bought nothing.

**So 0 of 41 is a stated limit and the row does not fail on it.** But accepting
it has a corollary, and the corollary is the finding: with the shape net gone,
the *whole* static claim of this row is the drift half. It must therefore
actually be what it says it is.

---

## Finding — the FAIL. `offenders_by_symbol` is defeated by a one-line alias, and the corpus plants the two harder indirections but not the easy one

### The escape

`BLESSED` / `THE_RULE` recognise the rule by the names `squash` and `norm`.
`_RowLocals` resolves a fold reached through a `def` wrapper and through a
name-bound `lambda` — the two indirections earlier reviews named — but nothing
resolves a plain rebinding. Planted into copies of the round 9 tree
(`scratchpad/v4r9-rj/rj_probe2.py`, one plant at a time, control included):

```
$ python3 scratchpad/v4r9-rj/rj_probe2.py scratchpad/v4r9-rj/tree-r9
CAUGHT  A  fold = lambda s: squash(s)   (== corpus D10)
ESCAPED B  fold = squash               (ONE character simpler)
ESCAPED C  fold = squash, SCALAR on a cell
CAUGHT  D  def fold(s): return squash(s)  (== corpus D09)
ESCAPED E  from tables import squash as fold
ESCAPED F  import tables; fold = tables.squash
ESCAPED G  the repo's OWN idiom, renamed: `keyof = squash` in a real reader shape
```

Each escaped body is `[fold(c) for c in split_row(line)]` — the one rule, the
same function object, mapped across a row's cells, outside `header_index`. That
is `DRIFT` by the corpus's own definition, not `SECOND_RULE`: it invents no
rule and it is not covered by the declared 0-of-41 limit. The corpus reports
**24 of 24**, and it contains D09 and D10 — the two *harder* spellings — and
not B/E/F/G.

**This is not an exotic spelling: it is the repository's own idiom.**
`bin/perry-lint:250` is literally `norm = squash`. `norm` happens to be in
`BLESSED`, so that one site is seen; the same line written with any other name
is not. Round 4's review already mutated that exact line, so the idiom is on
this row's record.

**And the round did think about import aliasing.** Corpus entry `D06` is
`from tables import squash as norm` — aliasing that happens to land on a name
already in `BLESSED`, and it is caught. The case where the alias lands anywhere
else is the one that is neither planted nor handled. The check is not
alias-blind by oversight of the whole category; it is alias-blind exactly where
being alias-blind matters.

Two further escapes fall out of the same per-function scoping and are worth
recording rather than charging: a fold inside a nested `def` closing over the
enclosing function's row variable escapes (`RJ10`), and so does the scalar form
of the alias (`C` above). Everything else I planted — a class method, a
subdirectory two levels deep, a module-level constant row, `tables.squash(c)`
through the module object, a row from `self.section_table(...)`, and a
`{squash(c): v for c, v in zip(cells, vals)}` dict comprehension — is **caught**.
The drift half is strong. It is not what its own docstring calls it.

### The live demonstration: a converted reader, unguarded by both legs

The round states (§ 4, § 6.2) that `bin/perry-tasks` is "the one converted
reader still not driven" by the runtime watch. That makes it the file where the
static hole is not backstopped. Planted into `scratchpad/v4r9-rj/tasks-alias`,
a full copy:

```python
# bin/perry-tasks:80-81
 from tables import header_index, squash  # noqa: E402
 _fold = squash

# bin/perry-tasks:926-928  (was: keys = header_index(...["header"], alias=ops.norm))
     _hdr = perry_store.intake_table(board, ops)["header"]
     keys = [ops.norm(_fold(c)) for c in _hdr]
```

```
$ python3 -c "import sys; sys.path.insert(0,'tests');
              from header_rule import offenders_by_symbol; print(offenders_by_symbol('.'))"
offenders_by_symbol: []

$ python3 -m unittest discover -s tests -p 'test_header_index_is_the_only_fold.py'
Ran 7 tests in 4.287s
OK
$ python3 -m unittest discover -s tests -p 'test_one_header_rule.py'
Ran 13 tests in 6.029s
OK
$ python3 -m unittest discover -s tests -p 'test_row_integrity.py'
Ran 33 tests in 2.849s
OK
```

And the whole suite, on that same planted copy:

```
$ bash tests/run
99 modules · 2895 tests · 183.9s · 8 workers
✗ 2 module(s) red
```

— the **same three pre-existing failures and no others**
(`test_diagnose` ×2, `test_kr_progress_provenance` ×1), byte-for-byte the set
the unplanted tree reports. Nothing in this repository notices.

The amendment's sentence is *"no call to `squash` on a row cell exists outside
`header_index()`."* Here such a call exists, on a live converted reader, and the
check reports nothing about it. By the round's own standard this is the defect
it says it closed: its justification for converting `bin/perry-lint:339` and
`bin/perry-task:1339` is that a redundant re-application of the one rule to a
header cell is *"one edit away from `.strip(\"*` \").lower()` and the divergence
this row exists to close."* A guard that cannot see such a site written as
`fold = squash` cannot hold the surface it just shrank.

### Why this fails the round rather than being recorded

Rounds 3 through 7 were failed for a check that recognises a **spelling**: a
regex alternation, then `ROW_NAMES`, then the `("header","headers","hdr")`
subscript test. Round 9 deleted every allowlist of variable names — I verified
that, it is real, and it is the best work this row has produced. What survives
is recognition of the rule by the **function's name**, and the escape is one
line long, uses an idiom already in the tree, is absent from a corpus that
plants both harder cousins, and is not among the nine limits § 6 declares. That
is the same failure mode in a new place, which is exactly the standard the
previous eight rounds were held to.

It is also small to fix: resolve module-level `NAME = <blessed>` and
`from tables import squash as NAME` bindings into the blessed set (`_RowLocals`
already does the analogous thing for `f = lambda`), then add B/E/F to `DRIFT`
with their provenance.

---

## What holds, measured independently

**The tree matches its commit exactly.** The brief flagged the hand-restored
mutation as the one place this could have gone wrong silently. I recomputed the
git blob SHA of every tracked file in the worktree against `git ls-tree -r
HEAD`: **688 files checked, 0 mismatches**, `git status --porcelain` empty,
`git ls-files -o --exclude-standard` empty. The hand restore left no residue.

**No allowlist of variable names survives, under any spelling.** Checked every
name set in `tests/header_rule.py`, not only the ones the result's table lists:

| set | contents | kind |
|---|---|---|
| `BLESSED` | `squash`, `norm`, `header_index`, `header_keys` | function names |
| `THE_RULE` | `squash`, `norm` | function names |
| `ROW_PRODUCERS` | `split_row`, `header_index` | function names |
| `ITERABLE_WRAPPERS` | 9 builtins | builtin names |
| `NOT_A_READER` | `tests`, `.git`, `__pycache__`, `.perry` | directories, each with a reason |
| `source()` | `strip`, `copy` | `str`/`list` methods |
| `cell()` | `strip`, `lstrip`, `rstrip`, `lower`, `casefold`, `upper`, `replace`, `title` | `str` methods |
| `offenders_by_symbol` (b) | `append`, `add`, `update`, `insert`, `setdefault` | container methods |
| `_mapping_sites` | `map`, `filter`, `sorted`, `min`, `max` | builtin names |

None is a variable name. `ROW_NAMES` and the `("header","headers","hdr")`
subscript test are gone from code. (Minor: the result says
`grep -rn "ROW_NAMES" tests/ bin/ viewer/` returns **four** prose lines; it
returns **two**. The load-bearing half — no code — is true.)

**`header_index` is the only thing that folds a header cell — checked by a means
the author did not use.** Rather than the AST net or the runtime watch, I
enumerated *every* call to `squash`/`norm` under `readers_under(.)` with my own
AST walk (`scratchpad/v4r9-rj/rj_allcalls.py`) — **39 sites in 7 files** — and
classified each by reading its enclosing function. Every one is a value
normalizer (`squash(was)`, `squash(outcome or "")`, `squash(cell or "")` on a
*track* cell), a canonical column name (`norm("ID")`, `norm(c)` for `c` in a
`needed` list, `squash(LEGACY_DUE_COLUMN)`), a glossary spelling
(`squash(spelling)`, `squash(name)`), a `##`-heading test
(`squash(line[3:])`, `squash(head)`), or a slug (`squash(label)`). **None is a
header cell.** My grep-based first pass missed `bin/perry-migrate:647
L.norm('By when')`; the AST pass caught it and it is a constant. So no third
live site exists — subject to the alias caveat above, which is about what could
be written, not about what is there.

**Both live conversions are real and semantically equal.**
`bin/perry-lint § canonical_column`: its only caller is `_track_context:667`,
`canonical_header = [canonical_column(cell) for cell in header]` where
`header = header_index(split_row(line))` — the input is already folded, and
`norm = squash` (line 250, `assertIs`-guarded) is idempotent on its own output,
so `value = key` is exact. `bin/perry-task § header_language`:
`folded = header_index(header)` replaces round 8's `zip(keys.raw, keys)` +
`squash(cell)`, and `header_index(h)[i] == squash(h[i])` by construction
(`viewer/tables.py:384`), so the comparison is unchanged. The round 9 code diff
over `68e63cf` is exactly three files and nothing else.

**All ten mutations reproduced, on `cp -R` copies, each anchored by line and
asserted against the exact old text before replacing.** All ten anchor lines
contain what the result says they contain, and each reddens exactly the named
test(s) — no more and no fewer.

| # | site | result |
|---|---|---|
| R9-1 | `bin/perry-lint:348` `value = key` → `norm(key)` | `test_nothing_outside_header_index_maps_squash_across_a_row` + `test_value_normalizers_are_not_flagged` RED (and `test_the_static_net_is_the_one_that_sees_dead_code`) |
| R9-2 | `bin/perry-task:1343/1346` back to `keys.raw` + `squash(cell_key)` | same two RED, plus `test_every_fold_of_a_header_cell_came_from_header_index` |
| R9-3 | `bin/perry-diagnose:1836` `header_index(raw)` → `(cells)` | `test_every_reader_this_module_claims_to_watch_actually_folds_one` RED, subtest `[md_table]` |
| R9-4 | `viewer/parsers.py:1833` → the historical rule | exactly the three named tests RED, incl. `test_a_bolded_kr_header_still_yields_the_KR` |
| R9-5 | `tests/header_rule.py:522` scalar half disabled | `test_each_drift_shape_is_caught` ×5 — `D04`, `D05`, `D09`, `D10`, `D11`, exactly as claimed |
| R9-7 | `readers_under` narrowed to `bin/`+`viewer/` | `D22` **and** `test_the_control_is_caught_at_every_path_the_corpus_uses [packs/…]` RED |
| R9-9 | the `.split("|")` row inference put back | `test_each_clean_shape_is_left_alone` RED naming **`C06`** — criterion 4 is a consequence of the design, confirmed |
| R9-6 | `is_python` back to round 8's `if p.suffix: return False` | `test_each_drift_shape_is_caught` — **`D21` only** |
| R9-8 | `by_name` lookup back to round 8's `self.funcs` lookup | `test_each_drift_shape_is_caught` — `D10` |
| R9-10 | label `S41` re-used as `S01` | `test_no_label_is_re_used_for_a_different_shape` RED on the label KEY |

R9-6 reddening `D21` **and not `D20`** is itself the evidence for the D20 note
below: under round 8's `is_python`, a suffix-less file with a shebang is still
seen, and `D20` is planted with one.

**The corpus: rebuilt independently from the round 4, 5 and 7 reviews, and I
found no pruning.** I read all three reviews and enumerated the shapes each
names, then mapped them onto the corpus:

- round 5 Finding 1's nine-case probe names seven — A/C/D/E/H/F/G → `S15`–`S21`.
  **Cases `B` and `I` genuinely appear in no sentence of that review**; I looked.
  `UNRECOVERABLE = 2` is honest and the refusal to invent them is right.
- round 5 Finding 2 → `S23` (the decisive case) and `S22` (`map()`).
- round 5's "latent risk, recorded not charged" → `C05`, and `C06` is its harder
  twin.
- round 7 Finding 2's escape list — `cells[1:]`, dict-assignment index, lambda,
  two-level indirection, class attribute, in a dict, aliased row parameter,
  `sorted(key=str.lower)`, `filter`, `out.add`, `out +=`, `zip`, walrus,
  `functools.partial`, scalar header-row test, `str.translate`, and P21 — all
  seventeen are present as `S24`–`S39`, `S41`.
- round 4's nine green plants and both `_is_python` holes → `S04`–`S14`,
  `D20`–`D22`.
- Round 4's shapes 1 (two levels deep) and 2 (class method) are named but not
  planted; both were RED at the time. I planted the drift form of each myself
  and both are **CAUGHT** (`bin/lib/parse/rjprobe5.py`, `viewer/rjprobe4.py`),
  so nothing hides there.

My per-source attribution differs from the result's table by one or two entries
(I make it 3 + 11 + 7 + 2 + 17 + 1; the table says 3 + 10 + 7 + 2 + 17 + 2). The
total, 41, and the "at least 43" are right. The three auditability tests are
live: blanking one `source` reddens `test_every_entry_carries_its_provenance`;
pointing `S02` at `S01`'s path reddens
`test_no_two_entries_are_planted_at_the_same_path`; truncating `SECOND_RULE` to
20 reddens `test_the_denominator_is_at_least_round_8s_honest_one`.

**Baselines reproduce exactly, on `git archive` exports, runner and tree named.**

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | `main` @ `6c0d041` (export at `v4r9-rj/tree-main`) | 98 | 2882 | 3 |
| `bash tests/run` | round 9 `HEAD` = `b5e7be3` (export at `v4r9-rj/tree-r9b`) | 99 | 2895 | 3 |
| `python3 -m unittest discover -s tests` | `main` @ `6c0d041` | — | 2882 | **6** |
| `python3 -m unittest discover -s tests` | round 9 `HEAD` | — | 2895 | **6** |

The three `bash tests/run` failures are identical on both trees and are the
three the result names:
`test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
`test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`.
I did not see the two `test_contract_key_parity` witness failures the brief
warned of, which is consistent with them being live-board artefacts — these are
committed-state exports.

**The retracted § 5 sentence is measured and it is true.** Nobody had run
`discover` on either tree before round 9; I ran it on both, serially, on the
same exports. It is 2882 / 6 on `main` and 2895 / 6 on round 9 — **exactly 3
more than `bash tests/run` on each tree**, and the three extra are exactly the
three the result names:

```
FAIL: test_risks_store.TestTheReadersAreOneFunction.test_the_bullet_and_placeholder_rules_are_one_object
FAIL: test_risks_store.TestTheReadersAreOneFunction.test_the_columns_are_one_list
FAIL: test_risks_store.TestTheReadersAreOneFunction.test_the_register_header_predicate_is_one_object
```

identical on both trees, so not caused by this change. I corroborated round 5's
diagnosis independently: `python3 -m unittest discover -s tests -p
'test_risks*.py'` on the round 9 tree is `Ran 134 tests … OK`, so the three
failures are a `discover`-mode double-import artefact and nothing else. The
`+13` also reconciles: 2895 − 2882 = 13, and the round's accounting of it
(`test_header_index_is_the_only_fold` 6→7, `test_header_rule_harness` 10→12,
`test_one_header_rule` 14→13, over round 8's +11) is arithmetically right.

**Call sites — the number round 8 got wrong is settled, and the result's figures
are exact.** Counted by AST (`ast.Call` whose callee is `header_index` or
`header_keys`) over `git archive` exports, excluding `tests/`:

```
68e63cf : 58   perry-task 23, parsers.py 16, perry-lint 6, perry-goals 5,
               perry-state 2, perry_store.py 2, perry-diagnose/-explain/
               -migrate/-tasks 1 each
b5e7be3 : 59   the same, +1 in perry-task (header_language's header_index)
```

The per-file breakdown matches the result's table cell for cell. 67 is not
derivable from anything. `readers_under` returns **20** files; the four `bin/`
files it skips (`perry-codex-preflight`, `perry-detect-host`,
`perry-dispatch-limit`, `perry-update-check`) are `#!/usr/bin/env bash`, and
`viewer/` holds only `parsers.py` and `tables.py`. The scope claim holds.

**The undecidability test is genuinely replaced.**
`test_it_is_undecidable_and_that_is_asserted_not_argued` is gone;
`test_the_multi_value_cell_normalizer_is_not_reported_either_way` asserts
`_hits(...) == []` for `cell.split("|")` and for `line.split("|")` **in separate
`subTest`s**, which is the stronger property round 8's reviewer asked for, not
"same verdict".

**Round 8's retraction is now complete.** `TASK-050-round8-result.md` is
replaced in its entirety by a retraction note listing all five wrong claims and
pointing at round 9. There is no surviving sentence asserting the retracted
`discover` figure.

**No new test is green in a way I could show to be vacuous.** The runtime watch
fixtures parse real rows (`_table_rows(OKR)` → 2 rows, `parse_top_risks` → 1,
`_parse_user_input` → 1); `test_the_watch_is_not_vacuous` asserts >5 folds and
>3 distinct decorated arguments; none of the three modules greps its own source;
none reaches a CLI, so `tests/gate.py`'s `GATE_OFF` is not involved;
`test_value_normalizers_are_not_flagged`'s `> 20` floor is backed by the tree's
~30 folding comprehensions.

---

## Smaller results, reported because they are results

- **Corpus entry `D20` does not plant what it is labelled.** `_plant` writes
  `SHEBANG + body` unconditionally, so `D20 "no suffix and NO SHEBANG"` — and
  `S12`, same label — are planted **with** `#!/usr/bin/env python3`. The entry
  cannot discriminate the round 4 hole it names, and R9-6's own attribution
  (only `D21` goes red) shows it. The property itself is fine: I planted a
  drift reader at `bin/perry-rjprobe2` with no suffix and no shebang, and one
  at `bin/perry-rjprobe3` whose first line is `# -*- coding: utf-8 -*-`
  (round 4's shape 6e), and **both are CAUGHT**. So this is a corpus-accuracy
  defect, not a guard defect — but it is a mislabelled entry in the file whose
  whole point this round is that its labels are trustworthy.
- **A guard that survives its own deletion.** `Watch.__enter__`'s module
  rebinding loop carries the comment *"Rebind every one of them, or the patch
  watches nothing and the test is vacuous — which `test_the_watch_is_not_vacuous`
  is here to catch."* I replaced `for attr in ("squash", "norm"):` with
  `for attr in ():` and **all 7 tests in the module stayed green**, including
  `test_the_watch_is_not_vacuous`. The loop is dead weight today (every fold
  reaches the patched `tables.squash` through `header_index`), and the comment
  claims a protection that does not exist.
- **`test_the_row_splitter_half_is_owned_by_criterion_3` asserts half its
  docstring.** It checks that `SPLIT_RE` matches both spellings; it does not
  assert *"and its scan covers `bin/` and `viewer/`"*, which is the half the
  lean actually depends on. I verified that half by planting instead.
- **`test_value_normalizers_are_not_flagged` and
  `test_nothing_outside_header_index_maps_squash_across_a_row` now end in the
  same assertion** (`offenders_by_symbol(PERRY_HOME) == []`). The first plants
  nothing; its distinct content is the `folding > 20` floor. That is why R9-1
  and R9-2 redden both. Not wrong, but the pair reads as two checks and is
  one and a half.
- **`test_each_second_rule_shape_escapes` asserts blindness**, so an
  improvement to the net turns it red. Its failure message gives the migration
  instruction, which is the right way to do it; noted so the next round is not
  surprised.
- `viewer/parsers.py:2582 § parse_decisions` is still a live instance of the
  scalar second-rule class and still dead code, as rounds 3, 4 and 8 all found.
  Agreed out of scope; recorded so round 10 does not rediscover it.

---

## Verdict

```
=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
         option C (binds)
checked: Worktree verified byte-identical to b5e7be3 (688 tracked blobs
         re-hashed, 0 mismatches; porcelain and ls-files -o both empty) at
         start and end. bash tests/run on git-archive exports: main @6c0d041
         98 modules/2882 tests/3 failures; round 9 @b5e7be3 99/2895/3, same
         three names. python3 -m unittest discover -s tests on both trees:
         2882/6 and 2895/6, differing from bash tests/run by exactly 3 on each,
         the three being test_risks_store.TestTheReadersAreOneFunction —
         the retracted section 5 sentence measured and true.
         All ten mutations reproduced on cp -R copies, each anchored by line
         and asserted on the exact old text; all ten anchors verified to
         contain what the result says, and each reddens exactly the named
         test(s). R9-9 confirmed:
         restoring the .split("|") row inference reddens
         test_each_clean_shape_is_left_alone on C06, so criterion 4 is a
         consequence of the design. Corpus rebuilt independently from the round
         4, 5 and 7 reviews and mapped entry by entry — no pruning found; round
         5's cases B and I confirmed unnameable in that review's prose. Round
         4's two named-but-unplanted shapes (class method, two-level
         subdirectory) planted by me: both CAUGHT. All squash/norm call sites
         under readers_under enumerated by my own AST walk (39 sites, 7 files)
         and classified by reading: none folds a header cell. Call sites
         re-counted by AST: 58 on 68e63cf, 59 on b5e7be3, per-file table exact.
         readers_under = 20; the four skipped bin/ files confirmed bash.
         test_row_integrity's reach verified by planting round 8's exact
         declared false positive into a copy of bin/perry-explain: RED, so the
         author's argument for the deletion holds. Round 8's retraction is now
         the whole document. Every plant and every run on copies under
         scratchpad/v4r9-rj; no write-side Perry tool; no identifier minted.
not-checked: did not drive any reader end-to-end from argv —
         round 8's four-CLI byte-identical differential is carried, not
         re-measured; did not investigate the three pre-existing failures,
         only that they are identical on both trees under bash tests/run; did
         not audit the write side, localized headers, or non-Python readers
         beyond confirming readers_under's scope; did not run the full suite
         on any tree carrying live board state.
proof: With the shape net deleted, the drift half carries the whole static
       claim, and it recognises the one rule by the FUNCTION'S NAME rather than
       by the symbol. A one-line rebinding walks past. Planted one at a time
       into copies of the round 9 tree, control included
       (scratchpad/v4r9-rj/rj_probe2.py), every body being
       `[fold(c) for c in split_row(line)]`:
         CAUGHT  fold = lambda s: squash(s)      (== corpus D10)
         CAUGHT  def fold(s): return squash(s)   (== corpus D09)
         ESCAPED fold = squash
         ESCAPED from tables import squash as fold
         ESCAPED import tables; fold = tables.squash
       The corpus plants both HARDER indirections and neither easy one, and
       reports DRIFT as 24 of 24. `norm = squash` at bin/perry-lint:250 is the
       repository's own idiom for this line; it is seen only because `norm`
       happens to be in BLESSED.
       Demonstrated on a live converted reader that the round itself states the
       runtime watch does not drive (§ 4, § 6.2), in a full copy at
       scratchpad/v4r9-rj/tasks-alias — bin/perry-tasks, `_fold = squash` at
       :81 and `keys = [ops.norm(_fold(c)) for c in _hdr]` at :928, replacing
       `header_index(...)`:
         offenders_by_symbol('.')                                  -> []
         test_header_index_is_the_only_fold.py    Ran 7 tests   OK
         test_one_header_rule.py                  Ran 13 tests  OK
         test_row_integrity.py                    Ran 33 tests  OK
       and `bash tests/run` on that same planted copy: 99 modules / 2895 tests
       / the SAME three pre-existing failures and no others (183.9s, 8
       workers) — byte-for-byte the failure set of the unplanted tree.
       That is the one rule mapped across a header row, outside header_index,
       on a converted reader, with every guard this row ships reporting
       nothing — the amendment's sentence, "no call to `squash` on a row cell
       exists outside `header_index()`", falsified by one line. It is DRIFT and
       not SECOND_RULE, so the declared 0-of-41 limit does not cover it, and it
       is in none of the nine limits § 6 declares.
       RULING ON THE QUESTION THE ROUND TURNS ON: 0 of 41 on SECOND_RULE is
       ACCEPTABLE under option C and is NOT why this fails. The amendment
       rejects option A by name, defines the guard as a one-symbol check, and
       requires criterion 4's false positive to go away as a consequence of the
       design — and R9-9 shows the row inference that would raise 0 of 41 is
       the same inference that reports C06, so 41 of 41 and 0 of 12 cannot both
       be had. The second-rule class is covered dynamically instead, and that
       cover is live: reverting parsers.py:1833 reddens
       test_every_decorated_header_cell_reached_header_index, as does a
       value-identical alias fold at the same site. The round fails on the
       corollary of accepting that: the half that is left must be over the
       symbol, and it is over the spelling.
       Supporting: corpus entry D20 ("no suffix and NO SHEBANG") is planted
       WITH a shebang, because _plant writes SHEBANG + body unconditionally, so
       it cannot discriminate the hole it names (the property nonetheless
       holds — I planted the real shape and it is caught); Watch.__enter__'s
       module-rebinding loop can be emptied with all 7 tests still green,
       contradicting its own comment that test_the_watch_is_not_vacuous catches
       that; test_the_row_splitter_half_is_owned_by_criterion_3 asserts the
       regex but not the scan coverage its docstring leans on; and
       `grep -rn "ROW_NAMES" tests/ bin/ viewer/` returns two prose lines, not
       the four the result claims (no code, which is the half that matters).
       The fix is small: resolve module-level `NAME = <blessed>` and
       `import squash as NAME` bindings into BLESSED — _RowLocals already does
       the analogous thing for `f = lambda` — and add the three escapes to
       DRIFT with their provenance.
=== END VERDICT ===
```
