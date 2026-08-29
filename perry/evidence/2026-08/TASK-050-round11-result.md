# TASK-050 round 11 — result

> Branch `coding/task-050-header-index`, forked from `main` at `6c0d041` and
> merged with `main` by the PMO at `4c2f07a`. **PASSED V4 review; corrected
> after it in three places, all marked `[review correction N]` below and all
> re-measured rather than edited.** Written against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.
>
> **This document supersedes `TASK-050-round10-result.md` for everything it
> restates**, and in particular replaces its § 7 limit 1 in full, which is the
> sentence round 10 was failed for. Round 10's result stays in place as the
> record of what round 10 did. There is one result of record and it is this
> one.

Round 10's review was a FAIL and largely a ruling in the round's favour. It
ruled **for** the mechanism the round turns on — *"closing a static hole with a
runtime watch DOES satisfy the amendment"* — verified round 9's charge fully
closed across ten alias shapes with both criterion-4 controls silent,
reproduced nine mutations including four that redden exactly one corpus entry,
confirmed the fixpoint earns its place, confirmed the corpus was not pruned,
and ruled that the round's counter-claim about the round 9 reviewer's plant was
TRUE.

It failed the round on one sentence — § 7 limit 1:

> *"every converted reader is now driven, so the uncovered set is empty today"*

and on the rule behind it:

> *"A dynamic cover discharges a static hole only if the round MEASURES which
> sites it reaches and STATES the remainder. This round states the remainder as
> empty; it is twelve."*

**Round 11 is that measurement, the local half of the hole closed statically,
and a `WATCHED` list that no longer survives its own deletion.** No production
code changed: `git diff --stat 4c2f07a..HEAD -- bin/ viewer/ schema/ templates/
packs/ modes/` is empty. The code diff is the same three files under `tests/` —
863 insertions, 15 deletions.

---

## 0. What changed, in one list

1. **A row carried on a DICT KEY is a row.** `_RowLocals` gains one more
   `source()` case, in the bookkeeping `returns` already used for tuple
   positions. The reviewer's exact plant at `bin/perry_store.py:855` is now
   reported and reddens three named tests (§ 1).
2. **The round 10 sentence is corrected.** The escape is not interprocedural.
   The local case is closed; a genuinely cross-module case remains, and it is
   described as what it is and counted (§ 1.2, § 7).
3. **The remainder is MEASURED, not asserted.** `header_rule.header_sites()`
   enumerates 76 sites; `Reach` records what the workload enters;
   `test_the_uncovered_remainder_is_the_measured_one` recomputes the
   difference. It was 20 under round 10's tree and workload. **It is 8** (§ 2).
4. **Nine of the twelve functions the reviewer named are DRIVEN**, not named
   (§ 2.2).
5. **`WATCHED` is asserted in both directions.** The reviewer's own deletion —
   removing `cmd_intake_write` — now reddens a named test, and so does
   converting a reader, driving it, and not listing it. `WATCHED` was short by
   eight and one of the eight was already being driven (§ 3).
6. **The corpus plants the shape.** Fourteen new `DRIFT` entries and two new
   `CLEAN` controls: `DRIFT` 33 → 47, `CLEAN` 12 → 14 (§ 4).
7. **Twenty-seven mutations, all red, nine of them single-entry** (§ 5).
8. **The machinery was swept for branches that survive their own deletion —
   first by hand (18 probes, 10 deleted) and then MECHANICALLY from the diff
   (128 candidates, 20 green, none a detection branch)** (§ 1.5).
9. **R10-2's count is corrected to eight**, as the round 10 review said (§ 8),
   and the round 11 review's three corrections are applied and re-measured
   (§ 2.3, § 5, § 1.5).

---

## 1. The FAIL — a row carried on a dict key

### 1.1 What escaped

`bin/perry_store.py § risk_plan` reads its header out of a dict key at line
854. One inserted line, bare `squash`, no alias, no wrapper:

```
     header, keys = table["header"], table["keys"]
+    keys = [squash(c) for c in header]
```

On round 10's tree `offenders_by_symbol` returned `[]`, all three header
modules were green, and `bash tests/run` was byte-for-byte the failure set of
the unplanted tree. `["header"]` is this repository's dominant idiom for
holding a header row: **17 live sites** across `bin/perry-task`,
`bin/perry-tasks`, `bin/perry_store.py` and `bin/perry_md_store.py`.

### 1.2 It is NOT interprocedural — round 10's own reason did not apply

Round 10's § 7 limit 1 attributed the gap to a module boundary:

> *"closing that statically would be interprocedural row-source recognition
> across module and dict boundaries — the widening the amendment rejects by
> name."*

The reviewer measured that this is wrong, and the measurement is reproduced
here: the shape escapes with the dict literal built two lines above, **inside
one function**. That is local dataflow, and `_RowLocals` already resolves
strictly harder local shapes — a `def` wrapper, a name-bound `lambda`, a
transitive alias chain bound out of order, a parameter this file passes a row
to, and what a file-local function RETURNS, including
`_, ihdr = ctx["board"].section_table("Intake")`.

**The correct statement of the limit, which § 7 now carries, is that a header
row whose producing chain crosses a MODULE boundary is not resolved — and that
statement comes with a size.** Of the 17 carried sites, the six inside
`bin/perry_store.py` itself now resolve; the other eleven are each rooted in a
call into another module (`perry_store.markdown_tables`,
`perry_store.intake_table`, `board.task_tables()`).

### 1.3 The fix — one more `source()` case

A **path** says where a row sits inside a value, read left to right:
`("key:header",)` — subscript by that string; `("elem", "key:header")` — index
or iterate first; `("pos:1", …)` — a tuple position first; `("attr:header",)` —
an object attribute. The empty path is the row itself and stays in
`self.scope`, so nothing is answered twice.

**It is provenance, not recognition.** A path exists only because an expression
in *this file* put a row there. `ROW_NAMES` stays deleted; no key name is
consulted by `offenders_by_symbol`. The controls prove the difference: a dict
whose value is a value (`{"status": rec.get("status")}`) folded by `squash` is
silent, and so is the generator that yields one — `C13` and `C14`.

The four links of `bin/perry_store.py` now resolve end to end: `markdown_tables`
APPENDS `{"header": split_row(...)}` to `out`; `risk_section_shape` returns
`("table", tables)`; `risk_table` INDEXES `tables[0]`; `risk_plan` UNPACKS
`header, keys = table["header"], table["keys"]`.

A second local case was open one function further on and is also closed:
`bin/perry-task § _section_tables` is *"the ONE walk over the board's
task-bearing sections"* and hands its tables over by `yield`, which fed nothing.

### 1.4 The reviewer's exact plant, replayed on `9d00f1b`

On a `git archive` export with the same line inserted at `perry_store.py:855`:

```
offenders_by_symbol('.')
  -> ['bin/perry_store.py:855: [squash(c) for c in header]',
      'bin/perry_store.py:855: squash(c)']

test_header_index_is_the_only_fold   Ran 10  FAILED (failures=1)
    test_the_static_net_is_the_one_that_sees_dead_code
test_one_header_rule                 Ran 13  FAILED (failures=2)
    test_nothing_outside_header_index_maps_squash_across_a_row
    test_value_normalizers_are_not_flagged
test_row_integrity                   Ran 33  OK   (not its criterion)
```

Three named tests, which is the amendment's own verification sentence.

The shape list, one plant at a time into copies, controls included:

| shape | round 10 | round 11 |
|---|---|---|
| `t = {"header": split_row(l)}; [squash(c) for c in t["header"]]` | ESCAPED | **CAUGHT** |
| `t = table_of(l); hdr = t["header"]; [squash(c) for c in hdr]` | ESCAPED | **CAUGHT** |
| `[squash(c) for c in tables_of(l)[0]["header"]]` | ESCAPED | **CAUGHT** |
| `for tbl in tables_of(ls): [squash(c) for c in tbl["header"]]` | ESCAPED | **CAUGHT** |
| `t = T(line); [squash(c) for c in t.header]` (attribute) | ESCAPED | **CAUGHT** |
| `[ops.norm(c) for c in t["header"]]` (the other spelling) | ESCAPED | **CAUGHT** |
| `squash(t["header"][0]) == "id"` (the scalar half) | ESCAPED | **CAUGHT** |
| the four-link append/tuple/index/unpack chain | ESCAPED | **CAUGHT** |
| a table handed over by `yield` | ESCAPED | **CAUGHT** |
| CONTROL `[squash(c) for c in split_row(l)]` | CAUGHT | CAUGHT |
| CONTROL a value normalizer over values | silent | **silent** |
| CONTROL `squash` of a dict of VALUES | silent | **silent** |
| CONTROL a generator yielding a dict of VALUES | silent | **silent** |

### 1.5 Ten branches DELETED because nothing measured them

**[review correction 3] The first draft of this section described a sweep of
eighteen HAND-CHOSEN probes. The review found two branches it never reached —
the `YieldFrom` step and `ast.Set` in the literal branch — and said the right
thing about it: a claim that a sweep found everything is a completeness claim.
So the sweep was rebuilt to take its candidates from `git diff` instead of from
me.** What follows is the hand sweep (which did real work and is kept, because
the ten deletions came out of it) and then the mechanical one that replaced it.

### The hand sweep — eighteen probes, ten deleted

Eighteen survival probes were run over the new machinery, each neutralised
alone. **Ten came back green** — the whole corpus stayed caught **and** the
live census stayed at 76 sites / 27 static-blind / no offenders — so they were
speculation and are deleted rather than carried:

`extend`/`update`, `insert` and `setdefault` container fills; an iterable
wrapper, `.copy()`, `.get("k")` and a `BoolOp` inside `_paths`; the slice
branch; the integer-subscript branch (the `elem` fallback already answers
`tables[0]`); and a parameter carrying a table's paths.

That is this row's own lesson applied to its own code: round 8 was failed for
keeping a half nothing measured, and an unmeasured half is a liability whichever
direction it errs in.

An eleventh probe came back green and was a **corpus gap** rather than dead
code — the loop-target binding, a LOOP over a list of tables rather than an
index into one, which is how `bin/perry_md_store.py:468` and `:543` and
`bin/perry_store.py:531` each read a header. `D42` plants it, and the probe
(R11-12) now reddens `D42` and only `D42`. The remaining seven probes were red
from the start and are R11-9, R11-10, R11-11, R11-13, R11-14, R11-16 and R11-17
in § 5 — seven red, ten deleted, one corpus entry, eighteen in all.

### The mechanical sweep — 128 candidates, taken from the diff

The candidate list is every `if`/`elif` test, every conditional expression and
every simple statement whose line `git diff -U0 4c2f07a..HEAD --
tests/header_rule.py` reports as new or changed: **337 lines, 128 candidates.**
Each mutant is built on the AST and written back with `ast.unparse`, so a
multi-line condition or a continuation line cannot break the syntax the way a
text-anchored edit can — and a **control run unparses the tree without mutating
anything** and stays green, so the round trip itself is not doing the work.

Each candidate is probed against the corpus, and every candidate that comes
back clean there is probed again against the **runtime** half, so *green* means
"the whole corpus is still caught AND
`test_the_uncovered_remainder_is_the_measured_one` is unmoved".

```
candidates                                        128
RED in the corpus                                  60
RED in the watch                                   26
UNNEUTRALISABLE (the module cannot run without it)  22
GREEN                                              20
```

The first run of it found **four more unpinned DETECTION branches** on top of
the review's two. Each is now planted with the live shape it is for, and each
is a single-entry mutation in § 5:

| entry | branch it pins | the live shape |
|---|---|---|
| `D43` | the `YieldFrom` step | `yield from` re-yields, so it must NOT add an element level |
| `D44` | `_rpaths_of` by ATTRIBUTE name | `Board.task_tables()`, minus the cross-module root |
| `D45` | `_bind_element` on a COMPREHENSION generator | the same list of tables walked by a comprehension |
| `D46` | the `cell()` half of the tuple unpack | `i, cells = row["line"], row["cells"]` |
| `D47` | the SUBSCRIPT half of the carried write | `spec["header"] = header`, `D24`'s sibling |

`ast.Set` was **deleted** rather than planted: a row is a list, a list is not
hashable, so a row cannot be an element of a set literal — it survived its own
deletion because it is unreachable.

**Twenty green mutants remain, and none of them is a detection branch.** They
are named here rather than counted, because "none is a detection branch" is a
claim and this is what it rests on:

| green | what it is | why a planting corpus cannot pin it |
|---|---|---|
| L418 L419 | `if self.of(node) is not f: continue` in the `yield` loop | an owner filter; only bites on a `yield` inside a nested function |
| L499 L500 | `if not isinstance(t, ast.Name): continue` | a target-shape guard |
| L506 L509 L512 L513 L514 | the `bound` flag and its `continue` | round 9's guard against the generic fall-through marking `_` a row |
| L584 | `_bind_element`'s target guard | same |
| L609 | `_rpaths_of`'s `isinstance(node, ast.Call)` guard | same |
| L694 L695 L696 | `source()`'s default-scope normalisation and its `_source_direct` short-circuit | `_paths` calls `_source_direct` itself, and the scalar half catches these bodies independently — defence in depth, the same reason R11-1 does not redden `D38` |
| L848 L852 L853 L856 | `header_sites`'s `Path(root)`, its two `warnings` filters and its `continue` on an unparseable file | plumbing copied from `offenders_by_symbol` |
| L877 L878 | the census's ATTRIBUTE half | dead on this tree: all seventeen live carried sites are subscripts. A stated limit of the MEASUREMENT (§ 7.14) |

Two of the twenty — L695 and L418 — were re-verified by hand with
text-anchored mutations rather than AST ones, because a sweep that disagrees
with a hand check is a broken sweep. Both agreed.

**What this sweep still does not claim.** It mutates whole `if` tests, not
individual conjuncts of an `and`; it does not mutate constants, operators or
f-string contents; and it covers `tests/header_rule.py` only —
`tests/test_header_index_is_the_only_fold.py`'s new code is probed by the six
targeted mutations R11-18…R11-23 and by nothing else.

---

## 2. The measured remainder — 8

### 2.1 The instrument

`tests/header_rule.py § header_sites(root)` enumerates every place a reader
holds a header row, in two kinds:

- **`convert`** — an argument of `header_index`/`header_keys`. Spelling-free:
  derived from the blessed call itself. **59 sites in 51 functions.**
- **`carried`** — a subscript or attribute read whose key is one of
  `CARRIED_KEYS = ("header", "headers", "hdr")`. **17 sites in 17 functions.**

Each carries a **static verdict**: does `_RowLocals` resolve that expression as
a row — which is exactly whether a `squash` planted on it in the same function
is reported by `offenders_by_symbol`.

`tests/test_header_index_is_the_only_fold.py § Reach` records, with
`sys.setprofile`, every function of this repository the watch's workload
ENTERS. A site is covered when the static half resolves it **or** the dynamic
half enters its function; the rest is the remainder.

`test_the_uncovered_remainder_is_the_measured_one` recomputes that difference
every run and asserts it equals `UNCOVERED`, **in both directions** — a
remainder that grows fails, and a remainder stated larger than it is fails too.

### 2.2 The numbers

All on `9d00f1b`, `sites=76`, `static-blind=27` in every row (the static half
does not move with the workload):

| | remainder |
|---|---|
| round 10's workload | **20** |
| round 11's workload | **8** |

Cross-checked with a **line-level** trace of the same workload rather than a
function-level one: the same 20 and the same 8, the same members
(`agree: True`). The coarser question is not hiding anything today.

Nine of the twelve functions the reviewer named are now DRIVEN rather than
named — `task_tables`, `_task_sections`, `find`, `ensure_columns`,
`ensure_section_columns`, `task_section_headings`, `replace_row`,
`refuse_foreign_risk_table` (on its refusal path, asserted with
`assertRaises`), plus `canonical_of` and `is_user_register_header`. The
write-side three edit the lines they are handed, so they run against
`WRITE_BOARD`, a fixture of their own.

### 2.3 The eight, by name

```
carried  bin/perry-task        _cmd_list_from_board
carried  bin/perry_md_store.py plan
carried  bin/perry_store.py    plan
convert  bin/perry-lint        check_cross_file
convert  bin/perry-lint        check_reviews
convert  bin/perry-lint        check_verification
convert  bin/perry-task        task_projection_row
convert  bin/perry_store.py    plan
```

**[review correction 1] They are open for TWO different reasons, and the first
draft of this section gave one reason for all eight. It was wrong for three.**

- **Five are rooted in a call into ANOTHER MODULE** — `_cmd_list_from_board`,
  `task_projection_row`, `perry_md_store § plan` and `perry_store § plan`
  (both its sites). Each reaches its row through `perry_store.markdown_tables`,
  `perry_store.intake_table` or a `Board` defined elsewhere.
  `tests/header_rule.py` is file-local by construction, so these need the
  interprocedural step the amendment rejects.
- **Three are NOT.** The `bin/perry-lint` sites reach their row through
  `tables()`, which is defined at `bin/perry-lint:194`, on top of
  `tables_with_lines()` at `:209` — **both in the same file**. What they
  escape through is that **`_paths` has no comprehension branch**:
  `tables()` is `[(h, [c for c, _ in r]) for h, r in tables_with_lines(...)]`,
  and a path does not travel through a comprehension's element expression.

  Reproduced here on a synthetic file with **no cross-module call anywhere**:
  the `bin/perry-lint` shape ESCAPED, and the identical file with the
  comprehension unrolled into an explicit loop was CAUGHT.

**The consequence, said plainly: the honest target for the next round is 5,
not 0.** Three of these eight are closable by the same file-local machinery
this round already built — one more `_paths` case for a comprehension, with
its own corpus entry and its own mutation — and the remaining five are the
cross-module limit.

This is the same species of error as round 10's, one rung smaller: *which*
sites and *how many* were right, *why* was wrong for three of them.

### 2.4 Reconciliation with the reviewer's twelve

The review reported *"17 live sites … 12 of them in functions the watch never
reaches"*. Measured here with a profiler rather than a capped stack, under
round 10's workload: **13 carried sites in 12 distinct function names** — the
reviewer's twelve names exactly, with `plan` standing for two files. The two
counts agree; they count different things (names versus sites). Under round
11's workload it is **7 sites in 6 names**.

---

## 3. `WATCHED` no longer survives its own deletion

Round 10's review:

> *"`WATCHED` is asserted in one direction only … removing `cmd_intake_write`
> from `WATCHED` leaves all 8 tests green, so nothing fails when a reader is
> absent from the list … the list is already short of the readers that
> matter."*

`test_watched_is_exactly_the_converted_readers_this_workload_folds_through`
asserts SET EQUALITY, and **the other side of the equality is not written in
this module**: it is `header_sites()`, walking the tree for every function that
calls `header_index`/`header_keys`. Frames are matched by FILE as well as by
name, so neither a unittest runner frame nor the `header_language` that exists
in two readers can answer for another.

Two failures follow from one assertion, and both are verified by mutation:

- **R11-18**, the reviewer's own deletion of `"cmd_intake_write"` → RED.
- **R11-19**, convert-and-forget: dropping `"is_intake_register_header"` → RED.

The second was not hypothetical. `WATCHED` was short by eight, and
`is_intake_register_header` was **already being driven and already missing from
the list** — the *"one unwatched conversion away"* that round 10 declared as a
future risk had already happened. `WATCHED` is 16 → 24.

---

## 4. The corpus

Round 10's review:

> *"No `DRIFT` entry carries a row through a dict or an attribute … That is the
> sentence round 9 wrote about `fold = squash`, with a different noun."*

Fourteen new `DRIFT` entries, each quoting the review line it comes from.
Nine answer round 10's charge:

| entry | shape |
|---|---|
| `D34` | a dict built in the SAME function |
| `D35` | a dict a file-local function RETURNED |
| `D36` | a LIST OF DICTS, indexed |
| `D42` | a LOOP over a list of tables |
| `D37` | an OBJECT ATTRIBUTE, set in `__init__` |
| `D38` | the FOUR-LINK chain `bin/perry_store.py` actually writes |
| `D39` | a table handed over by `yield` |
| `D40` | a dict-carried row, SCALAR on one cell |
| `D41` | a dict-carried row folded through `ops.norm` |

Five more came out of the mechanical sweep and the round 11 review (§ 1.5):

| entry | shape |
|---|---|
| `D43` | a table RE-YIELDED by `yield from` |
| `D44` | a table reached through a METHOD of a file-local class |
| `D45` | a table bound by a COMPREHENSION generator |
| `D46` | a tuple unpack whose element is one CELL |
| `D47` | a row written INTO a dict, then folded out of it |

Two new `CLEAN` controls, which are the reason the entries above are not a key-
name allowlist:

| entry | shape |
|---|---|
| `C13` | a dict of VALUES, folded by `squash` — silent |
| `C14` | a generator yielding a dict of VALUES — silent |

`D39` and `C14` differ only in whether what went into the dict came off a row.
That is the provenance the whole design is stated over, and it is now planted on
both sides.

**The three fractions, computed:**

```
DRIFT       caught  : 47 of 47
CLEAN       flagged : 0 of 14
SECOND_RULE caught  : 0 of 41 (+2 the reviews do not name)
```

`0 of 41` on `SECOND_RULE` is unchanged and is round 9's accepted ruling.

---

## 5. Mutations — twenty-seven, all red

Each anchored by LINE, asserted against the exact old text before replacing,
run in a **fresh interpreter**, with `__pycache__` cleared and the clock walked
past the next whole second on **both** sides, and restored from the WHOLE
original text with the md5 verified. Every restore printed `MATCHES`.

**[review correction 2] The first draft of this table was measured before
`D42` existed and omitted it from five rows — `R11-5` reddens `D38` AND `D42`,
not `D38` alone. That is the second time on this row that a mutation table has
been published against a corpus older than itself**: round 10's table predated
`D32`/`D33` and its reviewer found the same thing about `R10-2`. Both times the
error was safe-direction (the guard is broader than advertised) and both times
it was found by someone else. **The table below is re-measured in full against
the 47-entry corpus, in one run, after the last entry was added** — which is
the process change, not the numbers.

| # | mutation (anchor) | reddens |
|---|---|---|
| R11-1 | `header_rule.py:698` `source()` no longer consults `_paths` | D34 D35 D36 D37 D39 D40 D41 D42 D43 D44 D45 D46 D47 |
| R11-2 | `:631` a dict literal carries nothing | D34 D35 D36 D38 D39 D40 D41 D42 D43 D44 D45 D46 |
| R11-3 | `:659` an attribute carries nothing | **D37 only** |
| R11-4 | `:415` `yield` is not a producer | D39 D43 |
| R11-5 | `:470` `out.append(...)` fills nothing | D38 D42 D43 D44 D45 |
| R11-6 | `:501` a tuple UNPACK carries no paths | **D38 only** |
| R11-7 | `:575` a tuple LOOP target carries no paths | **D39 only** |
| R11-8 | `:327` the path fixpoint runs once | D37 D38 D42 D43 D44 D45 |
| R11-9 | `:530` a carried WRITE carries nothing | D37 D47 |
| R11-10 | `:532` `self.header = …` never reaches the class | **D37 only** |
| R11-11 | `:538` a plain name carries no paths | D34 D35 D37 D38 D40 D41 D46 |
| R11-12 | `:586` a loop target carries no paths | D42 D43 D44 D45 |
| R11-13 | `:639` a list/tuple literal carries nothing | D36 D38 D39 |
| R11-14 | `:643` no tuple POSITION on a literal | D38 D39 |
| R11-15 | `:654` an `elem` subscript yields nothing | D36 D38 |
| R11-16 | `:666` a call carries nothing from its callee | D35 D36 D37 D38 D39 D42 D43 D44 D45 |
| R11-17 | `:667` an IfExp carries nothing | **D38 only** |
| R11-24 | `:420` `yield from` adds an element level | **D43 only** |
| R11-25 | `:520` a SUBSCRIPT write carries nothing | **D47 only** |
| R11-26 | `:454` a comprehension generator binds no table | **D45 only** |
| R11-27 | `:504` a tuple unpack has no `cell()` half | **D46 only** |
| R11-18 | `…only_fold.py:100` delete `cmd_intake_write` from `WATCHED` | `test_watched_is_exactly_…` |
| R11-19 | `:84` convert-and-forget `is_intake_register_header` | `test_watched_is_exactly_…` |
| R11-20 | `:435` stop driving the carried-row readers | `…_the_measured_one`, `test_watched_is_exactly_…`, `…_actually_folds_one` |
| R11-21 | `:126` drop one entry from `UNCOVERED` | `test_the_uncovered_remainder_is_the_measured_one` |
| R11-22 | `:270` `Reach` records nothing | `test_the_uncovered_remainder_is_the_measured_one` |
| R11-23 | `header_rule.py:881` call every carried site static | `test_the_uncovered_remainder_is_the_measured_one` |

**Twenty-seven mutations, all red, nine of them single-entry.** **No mutation
flagged a `CLEAN` entry.** The anchor is given for every row so the next
reviewer can replay them: the round 11 reviewer could not verify 9 of the 23 in
the first draft of this table, because the table named the mutation and not the
line it was made at, and substituted an exhaustive plant sweep and a
twelve-branch hunt of its own. That substitution is what found corrections 1
and 3. The fixpoint keeps earning its place
(R11-8 → two entries). R11-1 does not redden `D38` because the tuple-unpack
branch writes into `self.scope` directly rather than through `source()`, which
is defence in depth and is reported rather than tidied.

R11-22 and R11-23 are the two that make § 2 readable: they neutralise the
DYNAMIC half of the measurement and the STATIC half of it in turn, and each
reddens the remainder test — so neither half of the number is vacuous.

The corpus probe used for the code mutations analyses only the planted file.
That is exactly what `_hits` already does (it filters offenders to the planted
path) and it keeps `readers_under`'s own `is_python`, which `D20` and `D21`
exist to discriminate. It was validated against the full `measure()` on the
unmutated tree: both report 0 escaped, 0 flagged.

---

## 6. Baselines — runner AND tree

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | `4c2f07a`, the merged tree this round started from | 102 | **3034** | 3 |
| `bash tests/run` | `9d00f1b`, this round's code tip | 102 | **3036** | 3 |
| `bash tests/run` | `9d00f1b`, a second run after restoring § 9's four files | 102 | **3036** | 3 |
| `bash tests/run` | `3210248`, the tip after the three review corrections | 102 | **3036** | 3 |
| `python3 -m unittest … test_header_index_is_the_only_fold.py` | `3210248` | — | 10 | 0 |
| `python3 -m unittest … test_one_header_rule.py` | `3210248` | — | 13 | 0 |
| `python3 -m unittest … test_row_integrity.py` | `3210248` | — | 33 | 0 |
| `python3 -m unittest … test_header_rule_harness.py` | `3210248` | — | 13 | 0 |

3034 → 3036 is this round's two new tests, both in
`test_header_index_is_the_only_fold.py` (8 → 10). The count on `4c2f07a`
matches the PMO's and the round 10 reviewer's measurement of that tree exactly.

The three failures are the same three names in all four runs, unchanged:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

Two of them are data-dependent on board state and one on a row's Next action
prose, so this count is stated for these two trees and not carried forward.

`offenders_by_symbol` on the live tree, best of three in one process:
**1.83s** against round 10's **1.48s**, best of three in one process each.
`test_header_rule_harness` is 152s against round 10's 156s.

---

## 7. What was NOT done, and what is not proven

Restated from scratch, because round 10's list was failed for the content of
one entry rather than its bookkeeping. Round 10's thirteen map onto these; the
one that changed is limit 1.

1. **A header row whose producing chain crosses a MODULE boundary is not
   resolved statically, and there are eleven such sites.** This replaces round
   10's limit 1, which said the uncovered set was empty and described the
   mechanism as a module boundary when the failing case had none. Measured: of
   the 17 carried sites, the **six** inside `bin/perry_store.py` resolve; the
   **eleven** in `bin/perry-task`, `bin/perry-tasks` and `bin/perry_md_store.py`
   are each rooted in a call into `perry_store` or into a `Board` defined in
   another module. `_RowLocals` is file-local by construction; cross-module
   dataflow is a type checker's job.
2. **`_paths` has no comprehension branch, and that is a FILE-LOCAL hole.** A
   path does not travel through a comprehension's element expression, so
   `tables()` at `bin/perry-lint:194` —
   `[(h, [c for c, _ in r]) for h, r in tables_with_lines(section)]`, both
   functions in that same file — hands its header row on invisibly. **Three of
   the eight uncovered sites are this and not limit 1**, and they are closable
   by the machinery this round already built. Found by the round 11 review;
   `_bind_element` IS called for a comprehension's generators (`D45`), so it is
   specifically `_paths` that stops at the element expression.
3. **The remainder neither half covers is 8**, listed by name in § 2.3 and
   recomputed by a named test. It is not zero and this round does not claim it
   is — and **five of the eight, not eight, are the cross-module limit.**
3. **The `carried` half of the census is a SPELLING**, `CARRIED_KEYS =
   ("header", "headers", "hdr")`. It is used only to COUNT, never by
   `offenders_by_symbol`, and it is documented as such at its definition — but
   a census that undercounts overstates coverage, so a row held under a fourth
   key name is uncounted. The `convert` half (59 of the 76 sites) is
   spelling-free.
4. **The dynamic half measures FUNCTION entry, not line execution.** A plant on
   a branch the workload does not take, inside a function it does enter, is
   counted as covered and would not be. A line-level trace of the same workload
   returns the same remainder today (§ 2.2), so nothing is hiding behind the
   coarser question — but that is a measurement, not a guarantee.
5. **A second RULE — a reader that invents its own fold — is invisible to the
   static net by construction.** That is `SECOND_RULE`, 41 planted shapes
   asserted to escape, covered by
   `test_every_decorated_header_cell_reached_header_index`. Round 9's ruling
   that `0 of 41` is acceptable under option C is carried, not re-litigated.
6. **A rebinding through a container (`FOLDS["k"] = squash`) and a function that
   RETURNS the rule (`def picker(): return squash`) are still not resolved as
   aliases.** Round 10's limit, unchanged; both are a second-rule shape by
   another road.
7. **`WATCHED` records bare function names.** `header_language` exists in both
   `bin/perry-goals` and `bin/perry-task`, so one entry can be satisfied by
   either. The converse check in § 3 matches by file as well as name, so the
   equality is not fooled — but the forward check
   (`test_every_reader_this_module_claims_to_watch_actually_folds_one`) still
   is. Recorded by the round 10 review; not load-bearing today.
8. **`viewer/parsers.py § parse_decisions`** is still a live instance of the
   scalar second-rule class and still dead code. Agreed out of scope.
9. **The write side, localized headers and non-Python readers are not audited.**
10. **Eleven branches were deleted for being unmeasured** (§ 1.5) — the ten the
    hand sweep found plus `ast.Set`. Each was dead on this tree; a future reader
    that writes `d.setdefault("header", row)` or `tables[1:]` would escape until
    someone plants it. That is a deliberate trade — an unmeasured half is what
    failed round 8 — and it is stated here so the next round can widen it *with*
    an entry rather than without one.
11. **`test_the_row_splitter_half_is_owned_by_criterion_3` still asserts half
    its docstring**: it checks `SPLIT_RE` and not that the scan covers `bin/`
    and `viewer/`. Carried from round 10.
12. **No reader was driven end-to-end from `argv`.** Round 8's four-CLI
    byte-identical differential is carried, not re-measured.
13. **`bash tests/run` writes Perry state into the repository it runs in**
    (§ 9). Observed, reproduced under control, confirmed independently by the
    round 11 reviewer in its own export, and filed as `TASK-249`. Not this row.
14. **The census's `carried` half has an ATTRIBUTE branch that is unexercised.**
    All seventeen live carried sites are subscripts, so neutralising the
    attribute branch of `header_sites` moves nothing (§ 1.5). It is kept so the
    census does not silently under-report the day one appears, and it is named
    here because an unexercised branch of the MEASUREMENT is exactly the kind of
    thing this row has been failed for leaving unsaid.
15. **The mechanical sweep is bounded and says so** (§ 1.5, last paragraph): it
    mutates whole `if` tests rather than individual conjuncts, does not mutate
    constants or operators, and covers `tests/header_rule.py` only.

---

## 7a. What the round 11 review verified independently

Recorded because it is stronger evidence than anything this document could
produce about itself, and because the next round should not re-run it:

- **The census's static verdict was validated EXHAUSTIVELY**, by planting at
  **all 76 sites one at a time**: `offenders_by_symbol` agreed with the
  `static` flag **76 of 76**.
- **The remainder reproduces on the reviewer's own `sys.settrace`** — 8 by
  function entry and 8 by line execution, the same eight members — and round
  10's **20** reproduces exactly.
- **The reconciliation with the round 10 reviewer's twelve was checked**: 13
  carried sites in 12 names.
- **"Provenance, not a key-name list" survived adversarial testing**: a dict
  keyed `zulu` holding a row is CAUGHT, a key literally named `header` holding
  non-row values is silent, and `CARRIED_KEYS` is never read by
  `offenders_by_symbol`.
- **Nine of the 23 mutations in this document's first draft could not be
  verified from it**, because the table named each mutation and not the line it
  was made at. The reviewer substituted the exhaustive plant sweep and a
  twelve-branch hunt of its own — which is what produced corrections 1 and 3.
  § 5 now carries the anchor for every row.

---

## 8. Corrections to round 10's result, and to this one

- **R10-2 reddens EIGHT corpus entries, not the six § 3.1 lists.** `D32` and
  `D33` are also alias-resolution dependents; the table predated them. The
  review is right and the correction is made here rather than in place, because
  this document supersedes that section.
- **§ 4.2's first row overstated the static half.** It claimed
  `offenders_by_symbol` sees *"the rule applied to a row a local dataflow
  reaches, under any alias"*. It did not: a dict-carried row is a local
  dataflow and was not seen. It is now, and § 7 limit 1 states what is left.
- **§ 7 limit 1 is withdrawn in full** and replaced by § 7 limits 1 and 2 above.
- **§ 7 limit 11** (*"this branch is not rebased on `main`"*) was already
  untrue of the tree the reviewer measured; the PMO's merge post-dates the
  document.

---

## 9. Findings this round produced

1. **`WATCHED` was short by eight, not by nothing**, and one of the eight —
   `is_intake_register_header` — was already being driven. The list claimed
   fewer readers than the module actually watched, which is the mirror image of
   round 8's finding that it claimed more.
2. **Eleven branches of this round's own first draft survived their own
   deletion** and are deleted, and **five more were unpinned detection branches
   that are now planted** (§ 1.5). The hand sweep found ten of the eleven; the
   round 11 review found `ast.Set` and the `YieldFrom` step that the hand sweep
   never reached, and the mechanical sweep built in answer to that found four
   more. The lesson is not "sweep harder" — it is that **a candidate list a
   human writes is a claim about their own code, and this row has been failed
   three times for claims wider than their measurement.** The candidate list now
   comes from `git diff`.
3. **`bash tests/run` writes Perry state into the repository it runs in, and
   it is reproducible.** After this session's baseline run, `git status` in the
   worktree showed four tracked files modified — `.perry/events.jsonl`,
   `perry/BOARD.md`, `perry/intake.jsonl` and
   `perry/journal/2026-08/2026-08-30.md` — all at the same second, carrying an
   `intake-sweep` event with `"actor": "agent"` that discharged one board row
   into the journal.

   A second run left them alone, so the write was checked properly rather than
   assumed: the four files were restored to their committed bytes (md5s
   recorded), `bash tests/run` was run again, and **the same four files moved
   again with the same one-row sweep and a new timestamp**. The no-op second
   run is the sweep being idempotent — after the first one there is nothing
   left to discharge — not the write being a one-off.

   **Independently confirmed by the round 11 reviewer**, which saw three
   tracked files move after `bash tests/run` in its own export — a third
   observation of the same behaviour. Filed as `TASK-249`.

   Restored again afterwards; the four md5s match their committed bytes and
   nothing from them is in this branch. Which test does it was not
   investigated: it is outside this row. Recorded because a reviewer who runs
   `bash tests/run` inside a worktree rather than on a `git archive` export
   will see these four files move and must not read them as the round's work —
   and because two of this suite's three carried failures are data-dependent on
   board state, which this write touches.
